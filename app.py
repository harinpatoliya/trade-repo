import streamlit as st
import pandas as pd
import datetime
from database import init_db, get_account, get_holdings, get_history, buy_stock, sell_stock, reset_account
from market_data import get_current_price, get_current_price_mock

st.set_page_config(page_title="VR Securities Limited", layout="wide", initial_sidebar_state="expanded")

# Initialize DB
init_db()

# --- Theme Logic ---
# Config sets base="dark". We offer a toggle to force Light Mode CSS.
st.sidebar.header("Theme")
dark_mode = st.sidebar.toggle("Dark Mode", value=True)

if not dark_mode:
    # Inject CSS to force light mode styles over the dark base
    st.markdown("""
        <style>
            [data-testid="stAppViewContainer"] {
                background-color: #ffffff;
                color: #31333F;
            }
            [data-testid="stSidebar"] {
                background-color: #f0f2f6;
                color: #31333F;
            }
            [data-testid="stHeader"] {
                background-color: rgba(255, 255, 255, 0);
            }
            .stMarkdown, .stText, h1, h2, h3, h4, h5, h6 {
                color: #31333F !important;
            }
            /* Adjust metric values */
            [data-testid="stMetricValue"] {
                color: #31333F !important;
            }
            /* Adjust tables - this is tricky as they use specific classes, but basic text might work */
            .stDataFrame {
                color: #31333F;
            }
        </style>
    """, unsafe_allow_html=True)

st.title("VR Securities Limited")

# Sidebar Navigation
st.sidebar.header("Navigation")
# Reordered: Log in is first, so it is the default on start.
page = st.sidebar.radio("Go to", ["Log in", "Dashboard", "Trade", "History"])

# --- Helper to get price (Mock or Real) ---
def fetch_price(symbol, exchange):
    if st.session_state.get('use_real_api', False):
        return get_current_price(symbol, exchange)
    else:
        return get_current_price_mock(symbol, exchange)

# --- Log in Page (Formerly Settings) ---
if page == "Log in":
    st.header("Log in / Settings")

    st.subheader("Fyres API Configuration")
    st.write("Enter your Fyres API credentials here to use live data. Otherwise, mock data will be used.")

    client_id = st.text_input("Client ID (App ID)", value=st.session_state.get('client_id', ''))

    st.write("---")
    st.write("**Generate Access Token** (Optional Helper)")

    secret_key = st.text_input("Secret Key (for token generation)", type="password")
    redirect_uri = st.text_input("Redirect URI", value="https://www.google.com")

    if st.button("Generate Login Link"):
        if not client_id or not secret_key or not redirect_uri:
            st.error("Please fill Client ID, Secret Key and Redirect URI")
        else:
            from fyers_apiv3 import fyersModel
            session = fyersModel.SessionModel(
                client_id=client_id,
                secret_key=secret_key,
                redirect_uri=redirect_uri,
                response_type='code',
                grant_type='authorization_code'
            )
            auth_link = session.generate_authcode()
            st.info(f"Click [here]({auth_link}) to login. After login, copy the 'auth_code' from the URL and paste below.")

    auth_code = st.text_input("Auth Code (Paste here)")

    if st.button("Get Access Token"):
        if not auth_code or not client_id or not secret_key or not redirect_uri:
             st.error("Missing details for token generation.")
        else:
            try:
                from fyers_apiv3 import fyersModel
                session = fyersModel.SessionModel(
                    client_id=client_id,
                    secret_key=secret_key,
                    redirect_uri=redirect_uri,
                    response_type='code',
                    grant_type='authorization_code'
                )
                session.set_token(auth_code)
                response = session.generate_token()
                if response.get('s') == 'ok' or 'access_token' in response:
                    token = response['access_token']
                    st.session_state['generated_token'] = token
                    st.success("Token Generated! It is auto-filled below.")
                else:
                    st.error(f"Failed to generate token: {response}")
            except Exception as e:
                st.error(f"Error: {e}")

    access_token_val = st.session_state.get('generated_token', st.session_state.get('access_token', ''))
    access_token = st.text_input("Access Token", value=access_token_val, type="password")

    if st.button("Save Credentials"):
        st.session_state['client_id'] = client_id
        st.session_state['access_token'] = access_token
        st.session_state['use_real_api'] = True
        st.success("Credentials saved!")

    st.markdown("---")
    if st.button("Reset Account (Restore 3 Lakhs)"):
        reset_account()
        st.success("Account reset to initial state.")


# --- Dashboard Page ---
elif page == "Dashboard":
    st.header("Dashboard")

    # Fetch Data
    account = get_account()
    balance = account['balance']

    holdings = get_holdings()

    total_pl = 0.0

    # Prepare Holdings Data and Calculate Total P&L first for the top metrics
    if not holdings.empty:
        current_prices = []
        live_pnl = []
        live_pnl_pct = []
        invested_amts = []

        for index, row in holdings.iterrows():
            cp = fetch_price(row['symbol'], row['exchange'])
            invested = row['quantity'] * row['average_price']
            invested_amts.append(invested)

            if cp is not None:
                pnl = (cp - row['average_price']) * row['quantity']
                if row['average_price'] != 0:
                    pnl_pct = ((cp - row['average_price']) / row['average_price']) * 100
                else:
                    pnl_pct = 0.0
                current_prices.append(cp)
                live_pnl.append(pnl)
                live_pnl_pct.append(pnl_pct)
            else:
                current_prices.append(None)
                live_pnl.append(None)
                live_pnl_pct.append(None)

        holdings['Current Price'] = current_prices
        holdings['Live P&L'] = live_pnl
        holdings['Live %P&L'] = live_pnl_pct
        holdings['Invested'] = invested_amts

        total_pl = holdings['Live P&L'].sum()

    # Metrics Display: Balance and Total P&L side-by-side
    col1, col2 = st.columns(2)
    col1.metric("Available Balance", f"₹ {balance:,.2f}")
    col2.metric("Total Unrealized P&L", f"₹ {total_pl:,.2f}")

    st.subheader("Current Holdings")

    if not holdings.empty:
        # Columns: Security, Buying Date, Buying Price, Quantity, Invested, Current Price, Live P&L, Live %P&L

        display_holdings = holdings[['symbol', 'first_buy_date', 'average_price', 'quantity', 'Invested', 'Current Price', 'Live P&L', 'Live %P&L']].copy()
        display_holdings.columns = ['Security', 'Buying Date', 'Buying Price', 'Quantity', 'Invested', 'Current Price', 'Live P&L', 'Live %P&L']

        st.dataframe(display_holdings.style.format({
            "Buying Price": "₹ {:.2f}",
            "Invested": "₹ {:.2f}",
            "Current Price": "₹ {:.2f}",
            "Live P&L": "₹ {:.2f}",
            "Live %P&L": "{:.2f} %"
        }, na_rep="N/A"))

    else:
        st.info("No current holdings.")

# --- Trade Page ---
elif page == "Trade":
    st.header("Place Order")

    col1, col2 = st.columns(2)

    with col1:
        symbol = st.text_input("Symbol (e.g., SBIN-EQ, TCS)", value="SBIN-EQ")
        exchange = st.selectbox("Exchange", ["NSE", "BSE", "MCX"])
        order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"])

    with col2:
        transaction_type = st.selectbox("Transaction", ["BUY", "SELL"])
        quantity = st.number_input("Quantity", min_value=1, value=1)
        price = st.number_input("Price (for LIMIT order)", min_value=0.0, value=0.0, disabled=(order_type=="MARKET"))

    if st.button("Submit Order"):
        # If Market Order, fetch price first
        trade_price = price
        if order_type == "MARKET":
            current_price = fetch_price(symbol, exchange)
            if current_price is None:
                st.error("Could not fetch price. Please check symbol.")
                # We cannot proceed without a price for market order
            else:
                trade_price = current_price
                st.info(f"Market Price fetched: {trade_price}")

                if trade_price <= 0:
                    st.error("Price must be greater than 0")
                else:
                    if transaction_type == "BUY":
                        success, msg = buy_stock(symbol, exchange, quantity, trade_price, order_type)
                    else:
                        success, msg = sell_stock(symbol, exchange, quantity, trade_price, order_type)

                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
        else:
             # Limit Order
            if trade_price <= 0:
                st.error("Price must be greater than 0")
            else:
                if transaction_type == "BUY":
                    success, msg = buy_stock(symbol, exchange, quantity, trade_price, order_type)
                else:
                    success, msg = sell_stock(symbol, exchange, quantity, trade_price, order_type)

                if success:
                    st.success(msg)
                else:
                    st.error(msg)

# --- History Page ---
elif page == "History":
    st.header("History")
    history = get_history()

    if not history.empty:
        display_history = history[['symbol', 'buy_date', 'buy_price', 'buy_quantity', 'sell_date', 'sell_quantity', 'pnl', 'pnl_percent']].copy()
        display_history.columns = ['Security', 'Date of Buying', 'Buying Price', 'Buying Quantity', 'Selling Date', 'Selling Quantity', 'P&L', '% P&L']

        st.dataframe(display_history.style.format({
            "Buying Price": "₹ {:.2f}",
            "P&L": "₹ {:.2f}",
            "% P&L": "{:.2f} %"
        }))
    else:
        st.info("No trade history found.")
