from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import json, time, threading, pyotp, requests
from logzero import logger
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
API_KEY = os.getenv("API_KEY")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
TOTP_SECRET = os.getenv("TOTP_SECRET")

# Target Expiry: December 2, 2025 (a Tuesday, a valid weekly expiry day)
# We will convert this date object to the required Angel One format (e.g., 02DEC2025)
TARGET_EXPIRY_DATE = datetime(2025, 12, 2)
# --- END CONFIGURATION ---

##############################################
# STEP 1: LOGIN (Requires API_KEY, USERNAME, PASSWORD, TOTP_SECRET in .env)
##############################################
try:
    smart = SmartConnect(API_KEY)
    totp = pyotp.TOTP(TOTP_SECRET).now()
    session = smart.generateSession(USERNAME, PASSWORD, totp)
except Exception as e:
    print(f"Login failed. Check your API credentials and TOTP: {e}")
    exit()

AUTH_TOKEN  = session["data"]["jwtToken"]
FEED_TOKEN  = smart.getfeedToken()
print("Login successful. Starting instrument download...")


##############################################
# STEP 2: DOWNLOAD INSTRUMENT LIST (SmartAPI)
##############################################
url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
try:
    data = requests.get(url).json()
    df = pd.DataFrame(data)
except Exception as e:
    print(f"Failed to download or parse instrument master: {e}")
    exit()

# Convert target date to the likely required format (e.g., '02DEC2025')
EXPIRY = TARGET_EXPIRY_DATE.strftime('%d%b%Y').upper()
print(f"Attempting to find NIFTY instruments for Expiry: {EXPIRY}")

# Filter NIFTY options for your expiry
nifty_df = df[
    (df["name"] == "NIFTY") &
    (df["expiry"] == EXPIRY) &
    (df["instrumenttype"] == "OPTIDX")
].copy()

if nifty_df.empty:
    print("\n" + "="*80)
    print(f"ERROR: No instruments found for the expiry date: {EXPIRY}!")
    print("This means the contract is either not listed yet, or the expiry format is incorrect.")
    
    # --- DEBUGGING HELP ---
    # Print the unique expiry dates actually available for NIFTY options for debugging the format
    available_expiries = df[
        (df["name"] == "NIFTY") &
        (df["instrumenttype"] == "OPTIDX")
    ]["expiry"].unique()
    
    if len(available_expiries) > 0:
        print("\nAvailable NIFTY Option Expiry Dates in the Master File:")
        for exp in sorted(available_expiries):
            print(f"- {exp}")
    # --- END DEBUGGING HELP ---

    print("Please check the dates above and update the TARGET_EXPIRY_DATE in the script.")
    print("="*80 + "\n")
    exit()

print(f"Found {len(nifty_df)} instruments for expiry {EXPIRY}.")


##############################################
# STEP 3: FIND ATM STRIKE
##############################################
# Note: Using the Nifty Index token (26009) to get the latest spot price
try:
    spot_data = smart.ltpData("NSE", "NIFTY", "26009")
    if spot_data.get("status") is False:
        print(f"Could not fetch LTP for NIFTY index (Token 26009). Exiting. Error: {spot_data.get('message')}")
        exit()
    spot = spot_data["data"]["ltp"]
    print(f"Current NIFTY Spot Price: {spot}")
    
    # Add a sanity check for the spot price based on typical NIFTY values (~20,000-25,000)
    if spot < 10000 or spot > 30000:
        print("WARNING: The fetched NIFTY Spot Price is outside the expected range (10,000-30,000).")
        print("This may indicate a data scaling issue (e.g., multiplied by 100) or an incorrect instrument token.")
        # If the spot price is extremely high, we should assume it's scaled by 100 to calculate ATM correctly.
        # However, for 59697.75, dividing by 100 gives 596.97, which is too low.
        # Since we cannot be sure of the scaling factor, we will use the raw spot for ATM calculation,
        # but the unexpected value is likely the root cause of high strike prices.

except Exception as e:
    print(f"Error fetching NIFTY spot price: {e}")
    exit()


# closest strike to spot → ATM
nifty_df["strike"] = nifty_df["strike"].astype(float)
atm_strike = nifty_df.iloc[(nifty_df["strike"] - spot).abs().argsort()].iloc[0]["strike"]
print(f"Calculated ATM Strike: {atm_strike}")


##############################################
# STEP 4: SELECT 10 ITM, ATM, 10 OTM per CE / PE
##############################################
def pick_strikes(df, atm):
    """Picks the 10 ITM, ATM, and 10 OTM strikes (21 total)"""
    # Debug Print: Check if input DF is empty
    if df.empty:
        print("DEBUG: pick_strikes received an EMPTY DataFrame. Returning empty set.")
        return df
        
    df_sorted = df.sort_values("strike")
    try:
        # Tries to find the exact ATM strike index
        idx = df_sorted.index[df_sorted["strike"] == atm][0]
        # Calculate start and end indices for 21 strikes centered on ATM
        start_idx = max(0, idx - 10)
        end_idx = min(len(df_sorted), idx + 11)
        print(f"DEBUG: ATM strike {atm} found. Selecting index range {start_idx}:{end_idx}.")
    except IndexError:
        # Fallback: If the exact ATM strike isn't found, pick the middle 21 strikes
        print(f"DEBUG: ATM strike {atm} NOT found exactly. Falling back to selecting middle 21 strikes.")
        mid = len(df_sorted) // 2
        start_idx = max(0, mid - 10)
        end_idx = min(len(df_sorted), mid + 11)

    result_df = df_sorted.iloc[start_idx : end_idx]
    print(f"DEBUG: pick_strikes returning {len(result_df)} tokens.")
    return result_df

# Split the main DataFrame into Call and Put options
calls_df_raw = nifty_df[nifty_df["symbol"].str.endswith("CE")]
puts_df_raw  = nifty_df[nifty_df["symbol"].str.endswith("PE")]

# New Debug Prints to isolate the 0-token issue
print(f"\n--- DEBUGGING TOKEN SELECTION ---")
print(f"Total NIFTY instruments available: {len(nifty_df)}")
print(f"Instruments ending with 'CE' found: {len(calls_df_raw)}")
print(f"Instruments ending with 'PE' found: {len(puts_df_raw)}")
print(f"Sample Symbols (first 5): {list(nifty_df['symbol'].head())}")
print(f"---------------------------------")


# Run the selection function
calls = pick_strikes(calls_df_raw, atm_strike)
puts  = pick_strikes(puts_df_raw, atm_strike)

final_tokens = list(calls["token"].astype(str)) + list(puts["token"].astype(str))
print(f"Total tokens selected for subscription: {len(final_tokens)}")


##############################################
# STEP 5: BUILD WEBSOCKET TOKEN STRUCTURE
##############################################
token_list = [
    {
        "exchangeType": 1,          # NFO
        "tokens": final_tokens
    }
]

correlation_id = "nifty_chain"
mode = 1   # LTP mode


##############################################
# STEP 6: CALLBACKS
##############################################
def on_data(wsapp, message):
    if isinstance(message, bytes):
        message = message.decode()
    # The real-time data comes in as a large JSON object or a series of updates.
    # We are using logger.info to print it, which is good for debugging.
    # In a real application, you would parse and update a data structure here.
    logger.info(message)

def on_open(wsapp):
    logger.info("WebSocket Open. Subscribing to tokens...")
    # Subscribe to the tokens in LTP mode
    if token_list[0]["tokens"]: # Only subscribe if tokens exist
        wsapp.parent.subscribe(correlation_id, mode, token_list)
        logger.info(f"Subscription request sent for {len(token_list[0]['tokens'])} instruments.")
    else:
        logger.warning("Subscription skipped: Token list is empty.")

def on_error(wsapp, error):
    logger.error(f"WebSocket Error: {error}")

def on_close(wsapp):
    logger.info("WebSocket Closed")


##############################################
# STEP 7: START WEBSOCKET
##############################################
sws = SmartWebSocketV2(AUTH_TOKEN, API_KEY, USERNAME, FEED_TOKEN)

def attach_parent():
    """Waits for the internal wsapp object to be created and attaches the parent."""
    # This is a necessary boilerplate for the SmartAPI SDK structure
    while sws.wsapp is None:
        time.sleep(0.05)
    sws.wsapp.parent = sws

print("\nConnecting to WebSocket for real-time data...")

sws.on_open  = on_open
sws.on_data  = on_data
sws.on_error = on_error
sws.on_close = on_close

# Start the connection in a separate thread
thread = threading.Thread(target=sws.connect, daemon=True)
thread.start()

# Wait for the WebSocket object to be ready and attach parent
attach_parent()

# Keep the main thread alive to allow the WebSocket thread to run
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting application...")
    sws.close()
    thread.join()
    exit()