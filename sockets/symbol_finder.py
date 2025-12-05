import requests
import json
from logzero import logger
from datetime import datetime

# URL for the Angel One Scrip Master JSON file
SCRIP_MASTER_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

def get_nfo_option_token(
    symbol_name: str, 
    expiry_date: str, 
    strike_price: int, 
    option_type: str
) -> dict or None:
    """
    Downloads the Scrip Master file and searches for a specific NFO option token.

    Args:
        symbol_name: The underlying index/stock name (e.g., "NIFTY", "BANKNIFTY").
        expiry_date: The exact expiry date string (e.g., "30JAN2025").
        strike_price: The strike price as an integer (e.g., 26200).
        option_type: The option type ("CE" for Call, "PE" for Put).

    Returns:
        A dictionary containing the full instrument details if found, otherwise None.
    """
    
    logger.info(f"Attempting to download Scrip Master from: {SCRIP_MASTER_URL}")
    try:
        # 1. Download the JSON file
        response = requests.get(SCRIP_MASTER_URL)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        instruments = response.json()
        logger.info(f"Successfully downloaded {len(instruments)} instruments.")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading Scrip Master file: {e}")
        return None
    except json.JSONDecodeError:
        logger.error("Error decoding JSON from Scrip Master file.")
        return None

    # 2. Calculate the required strike format for the search
    # Strike must be multiplied by 100 and formatted as a string for an exact match
    target_strike_str = f"{strike_price * 100}.000000"
    
    # 3. Define the filter criteria
    search_criteria = {
        "name": symbol_name.upper(),
        "expiry": expiry_date.upper(),
        "instrumenttype": "OPTIDX", # For Index Options like NIFTY/BANKNIFTY
        "exch_seg": "NFO",         # Futures and Options segment
        "strike": target_strike_str,
        # The option type is usually part of the full 'symbol' string in the file.
        # However, for an exact match, we rely on filtering the list.
    }
    
    # 4. Search the instrument list
    logger.info(f"Searching for {symbol_name} {strike_price} {option_type} expiring on {expiry_date}...")

    # We iterate through the list and check all criteria
    found_instrument = next((
        inst for inst in instruments 
        if inst.get("name") == search_criteria["name"] and
           inst.get("expiry") == search_criteria["expiry"] and
           inst.get("instrumenttype") == search_criteria["instrumenttype"] and
           inst.get("exch_seg") == search_criteria["exch_seg"] and
           inst.get("strike") == search_criteria["strike"] and
           inst.get("symbol", "").upper().endswith(option_type.upper()) # Check if symbol ends with CE or PE
    ), None)

    if found_instrument:
        logger.info(f"Found Token: {found_instrument['token']} for {found_instrument['symbol']}")
        return found_instrument
    else:
        logger.warning(f"No matching instrument found for strike {strike_price}, expiry {expiry_date}, type {option_type}.")
        return None

# --- EXAMPLE USAGE ---
if __name__ == "__main__":
    # Example 1: Search for the 26200 CALL option for a hypothetical January 2026 expiry
    # NOTE: This expiry is chosen to be far in the future where 26200 might exist.
    # If this fails, it means the exchange has not listed this specific contract yet.
    target_token_data = get_nfo_option_token(
        symbol_name="NIFTY",
        expiry_date="30JAN2026", # Use a plausible expiry date for deep OTM
        strike_price=26200, 
        option_type="CE"
    )

    if target_token_data:
        print("\n--- Found Instrument ---")
        for key, value in target_token_data.items():
            print(f"{key}: {value}")
    else:
        print("\n--- Search Result ---")
        print("Token not found for the specified criteria. The contract might not be listed by the exchange yet.")

    print("\n--- Another Example (If Nifty is 22000 spot, checking nearest monthly expiry PE) ---")
    # Example 2: Check for a more likely, near-the-money contract (adjust parameters to current market reality)
    # If the current date is Nov 2025, the Dec 2025 expiry might be the near month.
    # Let's check for a 24500 PE on the 02DEC2025 expiry (using a known expiry format).
    likely_token_data = get_nfo_option_token(
        symbol_name="NIFTY",
        expiry_date="02DEC2025", 
        strike_price=26250, 
        option_type="CE"
    )

    if likely_token_data:
        print("\n--- Found Likely Instrument ---")
        print(f"Token: {likely_token_data['token']}, Symbol: {likely_token_data['symbol']}")
    else:
        print("\n--- Likely Instrument Search Result ---")
        print("Could not find the 24500 PE for 02DEC2025. Check the URL for the full list of active expiries.")