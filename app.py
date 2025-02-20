import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# List of NIFTY 50 Stocks and their Yahoo Finance Symbols
nifty50_stocks = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "HDFC BANK": "HDFCBANK.NS",
    "ICICI BANK": "ICICIBANK.NS",
    "HUL": "HINDUNILVR.NS",
    "SBI": "SBIN.NS",
    "TATA MOTORS": "TATAMOTORS.NS",
    "BAJAJ FINANCE": "BAJFINANCE.NS",
    "ASIAN PAINTS": "ASIANPAINT.NS",
    "WIPRO": "WIPRO.NS",
    "BHARTI AIRTEL": "BHARTIARTL.NS",
    "SUN PHARMA": "SUNPHARMA.NS",
    "KOTAK MAHINDRA BANK": "KOTAKBANK.NS",
    "MARUTI SUZUKI": "MARUTI.NS",
    "HCL TECHNOLOGIES": "HCLTECH.NS",
    "TITAN COMPANY": "TITAN.NS",
    "ULTRATECH CEMENT": "ULTRACEMCO.NS",
    "TECH MAHINDRA": "TECHM.NS",
    "NTPC": "NTPC.NS",
    "GRASIM INDUSTRIES": "GRASIM.NS",
    "POWER GRID CORP": "POWERGRID.NS",
    "BAJAJ AUTO": "BAJAJ-AUTO.NS",
    "LARSEN & TOUBRO": "LT.NS",
    "DR REDDY'S LABS": "DRREDDY.NS",
    "ADANI ENTERPRISES": "ADANIENT.NS",
    "JSW STEEL": "JSWSTEEL.NS",
    "AXIS BANK": "AXISBANK.NS",
    "INDUSIND BANK": "INDUSINDBK.NS",
    "HERO MOTOCORP": "HEROMOTOCO.NS",
    "COAL INDIA": "COALINDIA.NS",
    "BPCL": "BPCL.NS",
    "ONGC": "ONGC.NS",
    "HINDALCO": "HINDALCO.NS",
    "TATA STEEL": "TATASTEEL.NS",
    "CIPLA": "CIPLA.NS",
    "EICHER MOTORS": "EICHERMOT.NS",
    "DIVIS LABORATORIES": "DIVISLAB.NS",
    "BRITANNIA": "BRITANNIA.NS",
    "BAJAJ FINSERV": "BAJAJFINSV.NS",
    "TATA CONSUMER": "TATACONSUM.NS",
    "M&M": "M&M.NS",
    "UPL": "UPL.NS",
    "SHREE CEMENT": "SHREECEM.NS",
    "SIEMENS": "SIEMENS.NS",
    "PIDILITE": "PIDILITIND.NS",
    "SRF LTD": "SRF.NS",
}

# Function to fetch stock data
def get_stock_data(symbol):
    stock = yf.Ticker(symbol)
    hist = stock.history(period="5d")  # Fetch last 5 days of data
    if hist.empty:
        return None

    # Compute Indicators
    hist["SMA_5"] = hist["Close"].rolling(window=5).mean()  # 5-day Simple Moving Average
    hist["VWAP"] = (hist["Close"] * hist["Volume"]).cumsum() / hist["Volume"].cumsum()
    delta = hist["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    hist["RSI"] = 100 - (100 / (1 + rs))

    latest_data = hist.iloc[-1]  # Get the latest data
    return {
        "Symbol": symbol,
        "Open": round(latest_data["Open"], 2),
        "High": round(latest_data["High"], 2),
        "Low": round(latest_data["Low"], 2),
        "Close": round(latest_data["Close"], 2),
        "LTP": round(latest_data["Close"], 2),
        "SMA_5": round(latest_data["SMA_5"], 2),
        "VWAP": round(latest_data["VWAP"], 2),
        "RSI": round(latest_data["RSI"], 2),
    }

# Streamlit UI
st.title("📊 NIFTY 50 Live Stock Dashboard")

# Fetch all stock data
st.write("Fetching live stock data, please wait...")
data_list = []
for stock_name, symbol in nifty50_stocks.items():
    stock_data = get_stock_data(symbol)
    if stock_data:
        data_list.append(stock_data)

# Convert to DataFrame
if data_list:
    df = pd.DataFrame(data_list)
    st.dataframe(df)
else:
    st.error("Failed to fetch stock data. Please try again later.")
