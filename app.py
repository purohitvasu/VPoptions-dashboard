import streamlit as st
import pandas as pd
import requests
import json
import os

# Streamlit UI - Must be first command
st.set_page_config(layout="wide", page_title="Options & Futures Dashboard")

# Fyers API Credentials
client_id = "your_client_id"
secret_key = "your_secret_key"
redirect_uri = "your_redirect_url"
token_file = "fyers_token.json"
access_token = None

# Function to check and load stored token
def load_access_token():
    global access_token
    if os.path.exists(token_file):
        with open(token_file, "r") as f:
            data = json.load(f)
            access_token = data.get("access_token")

# Function to save token
def save_access_token(token):
    with open(token_file, "w") as f:
        json.dump({"access_token": token}, f)

# Function to authenticate and get access token
def authenticate_fyers():
    global access_token
    auth_url = f"https://api.fyers.in/api/v2/generate-authcode?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
    st.sidebar.write("[Click here to authenticate Fyers](%s)" % auth_url)
    auth_code = st.sidebar.text_input("Enter Authorization Code after authentication:")
    
    if auth_code:
        token_url = "https://api.fyers.in/api/v2/token"
        payload = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "secret_key": secret_key,
            "redirect_uri": redirect_uri,
            "code": auth_code
        }
        response = requests.post(token_url, json=payload)
        if response.status_code == 200:
            access_token = response.json().get("access_token")
            save_access_token(access_token)
            st.sidebar.success("Authentication Successful!")
        else:
            st.sidebar.error("Failed to authenticate. Please check your credentials.")

# Load existing token
load_access_token()
if not access_token:
    authenticate_fyers()

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
    else:
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
