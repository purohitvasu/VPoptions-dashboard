import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Set up Streamlit app
st.set_page_config(page_title="F&O Dashboard", layout="wide")
st.title("Real-Time F&O Market Dashboard")

# API Configuration
DHAN_API_KEY = "your_dhan_api_key"
BASE_URL = "https://api.dhan.co"

# Function to fetch data
def fetch_dhan_data(endpoint, params={}):
    headers = {"Authorization": f"Bearer {DHAN_API_KEY}"}
    response = requests.get(f"{BASE_URL}/{endpoint}", headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    return None

# Fetch Market Data & Option Chain
def get_market_data(symbol):
    return fetch_dhan_data(f"marketdata/{symbol}")

def get_option_chain(symbol, expiry):
    return fetch_dhan_data(f"options/{symbol}/expiry/{expiry}")

# Sidebar Filters
symbol = st.sidebar.selectbox("Select Stock Symbol", ["NIFTY", "RELIANCE", "TCS", "INFY", "HDFCBANK"])
expiry = st.sidebar.selectbox("Select Expiry Date", ["2024-02-29", "2024-03-07", "2024-03-14"])  # Example dates

# Fetch Data
market_data = get_market_data(symbol)
option_chain = get_option_chain(symbol, expiry)

if market_data:
    ltp = market_data.get("ltp", "N/A")
    delivery_percentage = market_data.get("delivery_percentage", "N/A")
    total_oi = market_data.get("total_open_interest", "N/A")
    change_in_oi = market_data.get("change_in_oi", "N/A")

    # Display Metrics
    st.metric(label="LTP (Last Traded Price)", value=ltp)
    st.metric(label="Delivery Percentage", value=delivery_percentage)
    st.metric(label="Total Open Interest (OI)", value=total_oi)
    st.metric(label="Change in Future OI", value=change_in_oi)

if option_chain:
    call_oi = sum([item["call_oi"] for item in option_chain if "call_oi" in item])
    put_oi = sum([item["put_oi"] for item in option_chain if "put_oi" in item])
    pcr = round(put_oi / call_oi, 2) if call_oi else "N/A"

    st.metric(label="Total Call OI", value=call_oi)
    st.metric(label="Total Put OI", value=put_oi)
    st.metric(label="Put-Call Ratio (PCR)", value=pcr)

    # Data Visualization
    df = pd.DataFrame(option_chain)
    fig = px.bar(df, x='strike_price', y=['call_oi', 'put_oi'], barmode='group', title='Option Chain Analysis')
    st.plotly_chart(fig)
