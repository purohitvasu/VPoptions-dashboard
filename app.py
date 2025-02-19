import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Streamlit App Configuration
st.set_page_config(page_title="NSE F&O Dashboard", layout="wide")
st.title("Real-Time NIFTY Option Chain Dashboard")

# NSE API Endpoint
NSE_OPTION_CHAIN_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"

# Headers to Bypass NSE Bot Protection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.nseindia.com/",
}

# Function to Fetch NSE Data
def fetch_nse_data():
    session = requests.Session()
    session.headers.update(HEADERS)
    response = session.get(NSE_OPTION_CHAIN_URL)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Fetch Data
data = fetch_nse_data()

if data:
    option_chain = data["records"]["data"]
    strike_prices, call_oi, put_oi = [], [], []

    for item in option_chain:
        if "CE" in item and "PE" in item:
            strike_prices.append(item["strikePrice"])
            call_oi.append(item["CE"]["openInterest"])
            put_oi.append(item["PE"]["openInterest"])

    df = pd.DataFrame({"Strike Price": strike_prices, "Call OI": call_oi, "Put OI": put_oi})
    df["PCR"] = df["Put OI"] / df["Call OI"]
    
    # Display Data
    st.metric(label="Total Call OI", value=df["Call OI"].sum())
    st.metric(label="Total Put OI", value=df["Put OI"].sum())
    st.metric(label="Put-Call Ratio (PCR)", value=round(df["PCR"].mean(), 2))
    
    # Data Visualization
    fig = px.bar(df, x="Strike Price", y=["Call OI", "Put OI"], barmode="group", title="Option Chain Analysis")
    st.plotly_chart(fig)
else:
    st.error("Failed to fetch data from NSE API.")
