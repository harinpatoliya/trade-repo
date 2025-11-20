import streamlit as st
import pandas as pd
import datetime
from database import init_db, get_account, get_holdings, get_history, buy_stock, sell_stock, reset_account
from market_data import get_current_price, get_current_price_mock

st.set_page_config(page_title="VR Securities Limited", layout="wide", initial_sidebar_state="expanded")

# Initialize DB
init_db()

# Theme config handled by .streamlit/config.toml or system default.

st.title("VR Securities Limited")

# Sidebar
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Trade", "History", "Settings"])

# --- Helper to get price (Mock or Real) ---
def fetch_price(symbol, exchange):
    if st.session_state.get('use_real_api', False):
        return get_current_price(symbol, exchange)
    else:
        return get_current_price_mock(symbol, exchange)

# --- Dashboard Page ---
if page == "Dashboard":
    st.header("Dashboard")

    account = get_account()
    balance = account['balance']
    st.metric("Available Balance", f"₹ {balance:,.2f}")

    st.subheader("Current Holdings")
    holdings = get_holdings()

    if not holdings.empty:
        # Calculate Live P&L
        # We need to fetch current prices for each holding

        # Use a list to collect data instead of applying directly if we need robust error handling
        current_prices = []
        live_pnl = []
        live_pnl_pct = []

        for index, row in holdings.iterrows():
            cp = fetch_price(row['symbol'], row['exchange'])
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

        # Filter out rows where price fetch failed for display or handle NaN
        # We will display them but formatted carefully.

        display_holdings = holdings[['symbol', 'first_buy_date', 'average_price', 'quantity', 'Current Price', 'Live P&L', 'Live %P&L']].copy()
        display_holdings.columns = ['Security', 'Buying Date', 'Buying Price', 'Quantity', 'Current Price', 'Live P&L', 'Live %P&L']

        # Styling: We can't format NaNs with {:.2f}, so we might need to fillna or use a custom formatter
        # Simplest is to fillna with 0 or - for display purposes in a formatted string column,
        # but Styler works better with numbers.

        st.dataframe(display_holdings.style.format({
            "Buying Price": "₹ {:.2f}",
            "Current Price": "₹ {:.2f}",
            "Live P&L": "₹ {:.2f}",
            "Live %P&L": "{:.2f} %"
        }, na_rep="N/A"))

        # Calculate total P&L ignoring Nones
        total_pl = holdings['Live P&L'].sum()
        st.metric("Total Unrealized P&L", f"₹ {total_pl:,.2f}")

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

# --- Settings Page ---
elif page == "Settings":
    st.header("Settings")

    st.subheader("Fyres API Configuration")
    st.write("Enter your Fyres API credentials here to use live data. Otherwise, mock data will be used.")

    client_id = st.text_input("Client ID (App ID)", value=st.session_state.get('client_id', ''))
    access_token = st.text_input("Access Token", value=st.session_state.get('access_token', ''), type="password")

    if st.button("Save Credentials"):
        st.session_state['client_id'] = client_id
        st.session_state['access_token'] = access_token
        st.session_state['use_real_api'] = True
        st.success("Credentials saved!")

    st.markdown("---")
    if st.button("Reset Account (Restore 3 Lakhs)"):
        reset_account()
        st.success("Account reset to initial state.")
