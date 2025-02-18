import streamlit as st
import pandas as pd
import requests
import json
from fyers_api import fyersModel

# Streamlit UI - Must be first command
st.set_page_config(layout="wide", page_title="Options & Futures Dashboard")

# Load credentials from Streamlit Secrets
client_id = st.secrets["client_id"]
secret_key = st.secrets["secret_key"]
redirect_uri = st.secrets["redirect_uri"]
access_token = None

# Function to authenticate using Fyers SDK
def authenticate_fyers():
    session = fyersModel.FyersModel(client_id=client_id, is_async=False)
    auth_url = session.generate_authcode(redirect_uri=redirect_uri)
    st.sidebar.write(f"[Click here to Authenticate Fyers]({auth_url})")
    auth_code = st.sidebar.text_input("Enter the Authorization Code after authentication:")
    
    if auth_code:
        session.set_access_token(auth_code)
        access_token = session.get_access_token()
        return access_token
    return None

# Automate Authentication
access_token = authenticate_fyers()
if access_token:
    st.sidebar.success("Authentication Successful!")
else:
    st.sidebar.error("Authentication failed. Ensure that the auth code is correct and try again.")

headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}

# Function to fetch real-time data from Fyers API
def fetch_fyers_data(symbol):
    if not access_token:
        return {}
    url = f"https://api.fyers.in/api/v2/market-data?symbols={symbol}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data["d"].get(symbol, {})
    return {}

# Function to fetch real-time delivery data from Fyers API
def fetch_delivery_data(symbol):
    if not access_token:
        return "N/A"
    url = f"https://api.fyers.in/api/v2/market-depth?symbol={symbol}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        total_volume = data["d"][symbol].get("volume", 0)
        delivery_quantity = data["d"][symbol].get("delivery_quantity", 0)
        delivery_percentage = (delivery_quantity / total_volume * 100) if total_volume else 0
        return round(delivery_percentage, 2)
    return "N/A"

st.title("📊 Options & Futures Market Dashboard")

# Fetch real-time data for selected stock
selected_stock = st.sidebar.text_input("Enter Stock Symbol (e.g., NSE:RELIANCE-EQ)")
if selected_stock and access_token:
    fyers_data = fetch_fyers_data(selected_stock)
    delivery_percentage = fetch_delivery_data(selected_stock)
    if fyers_data:
        st.sidebar.subheader("Real-time Data from Fyers API")
        st.sidebar.write(f"LTP: {fyers_data.get('ltp', 'N/A')}")
        st.sidebar.write(f"20-SMA: {fyers_data.get('sma_20', 'N/A')}")
        st.sidebar.write(f"RSI (14): {fyers_data.get('rsi_14', 'N/A')}")
        st.sidebar.write(f"Delivery Percentage: {delivery_percentage}%")

# Function to fetch options chain data from Fyers API
def fetch_options_data(symbol):
    if not access_token:
        return {}
    url = f"https://api.fyers.in/api/v2/options-chain?symbol={symbol}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return {}

if selected_stock and access_token:
    options_data = fetch_options_data(selected_stock)
    if options_data:
        st.subheader("Live Options Chain Data")
        call_oi = options_data["CE"].get("open_interest", "N/A")
        put_oi = options_data["PE"].get("open_interest", "N/A")
        change_in_oi = options_data["CE"].get("change_oi", "N/A")
        pcr = round(put_oi / call_oi, 2) if call_oi and put_oi else "N/A"

        # Display Options Data
        options_df = pd.DataFrame({
            "Stock": [selected_stock],
            "LTP": [fyers_data.get("ltp", "N/A")],
            "Delivery %": [delivery_percentage],
            "20-SMA": [fyers_data.get("sma_20", "N/A")],
            "RSI": [fyers_data.get("rsi_14", "N/A")],
            "PCR": [pcr],
            "Change in Future OI": [change_in_oi],
            "Total Call OI": [call_oi],
            "Total Put OI": [put_oi]
        })

        # Format data and display
        options_df = options_df.round(2)
        st.dataframe(options_df.style.set_properties(**{"font-size": "16px"}))
