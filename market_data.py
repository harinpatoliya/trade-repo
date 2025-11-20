import random
from fyers_apiv3 import fyersModel
import streamlit as st

# Since we might not have keys, we need a way to run.
# If keys are present in session state, we use them.

def get_current_price(symbol, exchange):
    """
    Fetches the current price from Fyres API.
    Expects 'symbol' in the format required by Fyres (e.g., NSE:SBIN-EQ).
    The user input symbol/exchange needs to be converted to Fyres format.
    Fyres format: Exchange:Symbol (e.g., NSE:SBIN-EQ, MCX:CRUDEOIL20OCTFUT)
    """

    client_id = st.session_state.get('client_id')
    access_token = st.session_state.get('access_token')

    if not client_id or not access_token:
        return None

    try:
        fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="")

        # Construct symbol
        # If user puts "SBIN-EQ" and selects "NSE", we make "NSE:SBIN-EQ"
        full_symbol = f"{exchange}:{symbol}"

        data = {"symbols": full_symbol}
        response = fyers.quotes(data=data)

        # Response structure: {'s': 'ok', 'd': [{'n': 'NSE:SBIN-EQ', 's': 'ok', 'v': {'ch': -1.55, 'chp': -0.26, 'lp': 589.45, ...}}]}
        if response.get('s') == 'ok' and response.get('d'):
            return response['d'][0]['v']['lp'] # lp = Last Traded Price
        else:
            return None

    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

def get_current_price_mock(symbol, exchange):
    """
    Mock price generator for testing without API keys.
    Generates a somewhat realistic looking price based on a hash of the symbol
    so it stays consistent-ish, or randomizes slightly.
    """
    # Base price based on characters
    base = sum(ord(c) for c in symbol)
    # Add some randomness
    noise = random.uniform(-5, 5)
    return abs(base + noise)
