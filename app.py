import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# List of NIFTY 50 Stocks
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
}

# Streamlit UI
st.title("📈 NIFTY 50 Stock Market Dashboard")

# Dropdown for Stock Selection
stock_name = st.selectbox("Select a NIFTY 50 Stock", list(nifty50_stocks.keys()))

# Convert selected stock to Yahoo Finance symbol
nse_symbol = nifty50_stocks[stock_name]

if st.button("Get Stock Data"):
    stock = yf.Ticker(nse_symbol)
    hist = stock.history(period="1mo")  # Fetch last 1 month data

    if not hist.empty:
        st.write(f"📊 Stock Data for {stock_name} (NSE)")
        st.dataframe(hist.tail(5))  # Show last 5 days' data

        # Plot Stock Price Chart
        fig = px.line(hist, x=hist.index, y="Close", title=f"{stock_name} Stock Price (NSE)")
        st.plotly_chart(fig)
    else:
        st.error("No Data Available for Selected Stock")
