import streamlit as st
import pandas as pd
import requests
import os

# Load API credentials
DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")

# Streamlit UI - Must be first command
st.set_page_config(layout="wide", page_title="Options & Futures Dashboard")

st.title("📊 Options & Futures Market Dashboard")

# Dhan API Base URL
DHAN_BASE_URL = "https://api.dhan.co"

# Function to fetch market data
def fetch_market_data(symbol):
    formatted_symbol = f"NSE:{symbol}"  # Ensuring correct format for Dhan API
    url = f"{DHAN_BASE_URL}/market/v1/quotes/{formatted_symbol}"
    headers = {"Authorization": f"Bearer {DHAN_ACCESS_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching market data for {symbol}: {response.status_code} - {response.text}")
        return None

# Function to fetch option chain data
def fetch_option_chain(symbol):
    formatted_symbol = f"NSE:{symbol}"  # Ensuring correct format for Dhan API
    url = f"{DHAN_BASE_URL}/market/v1/instruments/option-chain/{formatted_symbol}"
    headers = {"Authorization": f"Bearer {DHAN_ACCESS_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching option chain for {symbol}: {response.status_code} - {response.text}")
        return None

# User input for stock symbol
symbol = st.sidebar.text_input("Enter Stock Symbol (e.g., NIFTY_50)", value="NIFTY_50")

if symbol:
    # Fetch Market Data
    market_data = fetch_market_data(symbol)
    if market_data:
        st.subheader(f"Market Data for {symbol}")
        st.write(market_data)
    
    # Fetch Option Chain Data
    option_chain = fetch_option_chain(symbol)
    if option_chain:
        st.subheader(f"Option Chain for {symbol}")
        df_option_chain = pd.DataFrame(option_chain.get("data", []))
        
        if not df_option_chain.empty:
            # Filter expiry dates
            expiry_dates = df_option_chain["expiryDate"].unique()
            selected_expiry = st.sidebar.selectbox("Select Expiry", expiry_dates)
            df_filtered = df_option_chain[df_option_chain["expiryDate"] == selected_expiry]
            
            # Calculate Total Call OI & Put OI
            total_call_oi = df_filtered[df_filtered["optionType"] == "CE"]["openInterest"].sum()
            total_put_oi = df_filtered[df_filtered["optionType"] == "PE"]["openInterest"].sum()
            
            # Calculate PCR
            pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else 0
            
            # Display Calculated Data
            st.metric(label="Total Call OI", value=total_call_oi)
            st.metric(label="Total Put OI", value=total_put_oi)
            st.metric(label="PCR (Put/Call Ratio)", value=pcr)
            
            # Display Option Chain Data
            st.dataframe(df_filtered.style.set_properties(**{"font-size": "16px"}))
        else:
            st.warning("No option chain data available for the selected symbol.")

