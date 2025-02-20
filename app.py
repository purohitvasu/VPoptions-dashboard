import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# Streamlit UI
st.title("📈 Live Stock Market Dashboard")

# User Input for Stock Symbol
symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, TSLA, MSFT)", "AAPL")

if st.button("Get Stock Data"):
    stock = yf.Ticker(symbol)
    hist = stock.history(period="1mo")  # Fetch last 1 month data

    if not hist.empty:
        st.write(f"📊 Stock Data for {symbol}")
        st.dataframe(hist.tail(5))  # Show last 5 days' data

        # Plot Stock Price Chart
        fig = px.line(hist, x=hist.index, y="Close", title=f"{symbol} Stock Price")
        st.plotly_chart(fig)
    else:
        st.error("Invalid Stock Symbol or No Data Available")
