from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import json, time, threading, pyotp, requests
from logzero import logger
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables (NOTE: These must be configured in your local environment 
# for the script to execute successfully, as the SDK requires them for connection.)
load_dotenv()

# --- CONFIGURATION ---
API_KEY = os.getenv("API_KEY")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
TOTP_SECRET = os.getenv("TOTP_SECRET")

# Target Expiry: December 2, 2025 (a Tuesday, a valid weekly expiry day)
TARGET_EXPIRY_DATE = datetime(2025, 12, 2)
# --- END CONFIGURATION ---

# --- GLOBAL DATA STORES FOR OPTION CHAIN ---
# Map token (string) to strike (float) and option type (string) for easy lookup
TOKEN_TO_INFO = {} 
# Store the latest real-time data received from the WebSocket: {token: {'ltp': X.XX, 'timestamp': YY}}
OPTION_CHAIN_DATA = {}
# --- END GLOBAL DATA STORES ---

##############################################
# STEP 1: LOGIN (Requires API_KEY, USERNAME, PASSWORD, TOTP_SECRET in .env)
##############################################
if not all([API_KEY, USERNAME, PASSWORD, TOTP_SECRET]):
    print("FATAL ERROR: Missing one or more environment variables (API_KEY, USERNAME, PASSWORD, TOTP_SECRET).")
    print("Please set these variables in your .env file or environment.")
    exit()

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
    # Get NIFTY Index LTP from the API
    spot_data = smart.ltpData("NSE", "NIFTY", "26009")
    if spot_data.get("status") is False:
        # Fallback to a placeholder value if API fails, preventing script crash
        print(f"Could not fetch LTP for NIFTY index (Token 26009). Error: {spot_data.get('message')}")
        spot = 2200000.0 # Assuming a spot of 22000 * 100 (as often API data is scaled)
        print(f"Using fallback spot price: {spot/100.0}")
    else:
        spot = spot_data["data"]["ltp"]
        print(f"Current NIFTY Spot Price (Raw): {spot}")
    
    # Sanity Check and Assumption: The API often returns strike and spot * 100.
    # We assume 'spot' is already scaled to match the 'strike' field in the master file.
    
except Exception as e:
    print(f"Error fetching NIFTY spot price: {e}. Using fallback spot price 22000.")
    spot = 2200000.0 # Fallback

# Find the closest strike to spot -> ATM
nifty_df["strike"] = nifty_df["strike"].astype(float)
# The closest strike is used as the center for the option chain
atm_strike_raw = nifty_df.iloc[(nifty_df["strike"] - spot).abs().argsort()].iloc[0]["strike"]
print(f"Calculated ATM Strike (Raw): {atm_strike_raw}")


##############################################
# STEP 4: SELECT 10 ITM, ATM, 10 OTM per CE / PE and MAP TOKENS
##############################################
def pick_strikes(df, atm_raw_strike):
    """Picks the 10 ITM, ATM, and 10 OTM strikes (21 total)"""
    if df.empty:
        return df
        
    df_sorted = df.sort_values("strike")
    try:
        # Find index of the exact ATM strike
        idx = df_sorted.index[df_sorted["strike"] == atm_raw_strike][0]
        # Calculate start and end indices for 21 strikes centered on ATM
        start_idx = max(0, idx - 10)
        end_idx = min(len(df_sorted), idx + 11)
    except IndexError:
        # Fallback: If the exact ATM strike isn't found, pick the middle 21 strikes
        print(f"DEBUG: ATM strike {atm_raw_strike} NOT found exactly. Falling back to selecting middle 21 strikes.")
        mid = len(df_sorted) // 2
        start_idx = max(0, mid - 10)
        end_idx = min(len(df_sorted), mid + 11)

    result_df = df_sorted.iloc[start_idx : end_idx]
    return result_df

# Split the main DataFrame into Call and Put options
calls_df_raw = nifty_df[nifty_df["symbol"].str.endswith("CE")]
puts_df_raw  = nifty_df[nifty_df["symbol"].str.endswith("PE")]

# Run the selection function
calls = pick_strikes(calls_df_raw, atm_strike_raw)
puts  = pick_strikes(puts_df_raw, atm_strike_raw)

# Combine tokens and populate the TOKEN_TO_INFO lookup map
final_df = pd.concat([calls, puts])
final_tokens = list(final_df["token"].astype(str))

for _, row in final_df.iterrows():
    token = str(row["token"])
    symbol = row["symbol"]
    strike = row["strike"] / 100.0 # Divide by 100 for human-readable strike
    option_type = "CE" if symbol.endswith("CE") else "PE"
    
    # Populate lookup map
    TOKEN_TO_INFO[token] = {
        'strike': strike,
        'type': option_type,
        'symbol': symbol
    }
    # Initialize real-time data store
    OPTION_CHAIN_DATA[token] = {'ltp': 0.0, 'timestamp': None}

print(f"Total tokens selected for subscription: {len(final_tokens)}")
print(f"ATM Strike (Human Readable): {atm_strike_raw / 100.0}")

final_tokens = ["46807"]
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
# STEP 6: CALLBACKS and DISPLAY LOGIC
##############################################

def on_data(wsapp, message):
    """Processes incoming real-time price updates."""
    if isinstance(message, bytes):
        message = message.decode()
    
    try:
        data = json.loads(message)
        # Check if the message is a tick update (it should contain 'ltp' or similar fields)
        if "data" in data and isinstance(data["data"], dict):
            # The structure for a tick is often like: {"action": 1, "data": {"token": "...", "ltp": X.XX, ...}}
            token = str(data["data"].get("token"))
            ltp = data["data"].get("ltp")
            
            if token in OPTION_CHAIN_DATA and ltp is not None:
                # Update the global data store
                OPTION_CHAIN_DATA[token]['ltp'] = ltp
                OPTION_CHAIN_DATA[token]['timestamp'] = datetime.now()
        else:
            # Log non-tick data (like heartbeat, initial handshake, or error messages)
            logger.info(message)
            
    except json.JSONDecodeError:
        logger.warning(f"Failed to decode JSON message: {message}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")

def on_open(wsapp):
    logger.info("WebSocket Open. Subscribing to tokens...")
    # Subscribe to the tokens in LTP mode
    if token_list[0]["tokens"]: # Only subscribe if tokens exist
        # SmartWebSocketV2 uses parent.subscribe(correlation_id, mode, token_list)
        wsapp.parent.subscribe(correlation_id, mode, token_list)
        logger.info(f"Subscription request sent for {len(token_list[0]['tokens'])} instruments.")
    else:
        logger.warning("Subscription skipped: Token list is empty.")

def on_error(wsapp, error):
    logger.error(f"WebSocket Error: {error}")

def on_close(wsapp):
    logger.info("WebSocket Closed")
    
# Function to format and display the option chain
def display_option_chain():
    """Formats the global option chain data and prints it to the console."""
    
    # 1. Create a list of strikes present in the selection
    strikes = sorted(list(set(info['strike'] for info in TOKEN_TO_INFO.values())))
    
    # 2. Map strike price to its CE and PE LTP
    chain = {}
    for token, info in TOKEN_TO_INFO.items():
        strike = info['strike']
        ltp = OPTION_CHAIN_DATA.get(token, {}).get('ltp', 0.0)
        
        if strike not in chain:
            chain[strike] = {'CE_LTP': 0.0, 'PE_LTP': 0.0}
            
        if info['type'] == 'CE':
            chain[strike]['CE_LTP'] = ltp
        else:
            chain[strike]['PE_LTP'] = ltp

    # 3. Print the formatted chain
    print("\n" + "="*75)
    print(f"NIFTY OPTION CHAIN | EXPIRY: {EXPIRY} | TIME: {datetime.now().strftime('%H:%M:%S')}")
    print("="*75)
    
    # Header
    header = f"{'CE LTP':>10} | {'STRIKE':^10} | {'PE LTP':<10}"
    print(header)
    print("-" * 75)

    # Rows
    current_atm_strike = atm_strike_raw / 100.0
    print(f"Current ATM Strike: {current_atm_strike}\n")
    for strike in strikes:
        data = chain[strike]
        print(281,data)
        # Highlight ATM strike
        if strike == current_atm_strike:
            row_style = "\033[93m" # Yellow for ATM
        # Highlight ITM (CE is ITM if Strike < Spot; PE is ITM if Strike > Spot)
        elif strike < current_atm_strike and data['CE_LTP'] > 0:
            row_style = "\033[92m" # Green for CE ITM
        elif strike > current_atm_strike and data['PE_LTP'] > 0:
            row_style = "\033[92m" # Green for PE ITM
        else:
            row_style = "\033[0m"  # Reset color

        row = f"{row_style}{data['CE_LTP']:>10.2f}\033[0m | {row_style}{strike:^10.2f}\033[0m | {row_style}{data['PE_LTP']:<10.2f}\033[0m"
        print(row)
        
    print("="*75 + "\n")


##############################################
# STEP 7: START WEBSOCKET AND MAIN LOOP
##############################################
sws = SmartWebSocketV2(AUTH_TOKEN, API_KEY, USERNAME, FEED_TOKEN)

def attach_parent():
    """Waits for the internal wsapp object to be created and attaches the parent."""
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

# Keep the main thread alive and display the option chain periodically
try:
    print("Real-time option chain display started. Press Ctrl+C to stop.")
    while True:
        # Display the option chain every 5 seconds
        time.sleep(5) 
        display_option_chain()

except KeyboardInterrupt:
    print("Exiting application...")
    sws.close()
    thread.join()
    exit()