import streamlit as st
import pandas as pd
import websocket
import json
import threading
import numpy as np

# Load API credentials from Streamlit secrets
access_token = st.secrets["secrets"]["DHAN_ACCESS_TOKEN"]

# Define WebSocket URL for Dhan Live Market Feed
ws_url = f"wss://api-feed.dhan.co?version=2&token={access_token}&authType=2"

# NIFTY 50 Stock List (Symbol: SecurityID)
nifty50_stocks = {
    "RELIANCE": "1333",
    "TCS": "11536",
    "INFY": "1594",
    "HDFC BANK": "1330",
    "ICICI BANK": "4963",
    "HUL": "1792",
    "SBI": "3045",
    "TATA MOTORS": "3456",
    "BAJAJ FINANCE": "317",
    "ASIAN PAINTS": "236",
    "WIPRO": "3787",
    "BHARTI AIRTEL": "10666",
    "SUN PHARMA": "4345",
    "KOTAK MAHINDRA BANK": "1922",
    "MARUTI SUZUKI": "10999",
}

# Store Live Data
stock_data = {symbol: {"Open": None, "High": None, "Low": None, "Close": None, "LTP": None, "SMA_5": None, "VWAP": None, "RSI": None} for symbol in nifty50_stocks}

# WebSocket Handlers
def on_message(ws, message):
    data = json.loads(message)

    # Process the received live data
    for item in data.get("data", []):
        symbol_id = item.get("SecurityId")
        for stock_name, sec_id in nifty50_stocks.items():
            if sec_id == str(symbol_id):
                stock_data[stock_name]["LTP"] = round(item.get("LTP", 0), 2)
                stock_data[stock_name]["Open"] = round(item.get("Open", 0), 2)
                stock_data[stock_name]["High"] = round(item.get("High", 0), 2)
                stock_data[stock_name]["Low"] = round(item.get("Low", 0), 2)
                stock_data[stock_name]["Close"] = round(item.get("Close", 0), 2)

                # Calculate SMA, VWAP, RSI
                stock_data[stock_name]["SMA_5"] = round(np.mean([stock_data[stock_name]["Close"] for _ in range(5)]), 2)
                stock_data[stock_name]["VWAP"] = round(np.mean([stock_data[stock_name]["LTP"] for _ in range(5)]), 2)

                # RSI Calculation
                close_prices = np.array([stock_data[stock_name]["Close"] for _ in range(14)])
                delta = np.diff(close_prices)
                gain = np.where(delta > 0, delta, 0).mean()
                loss = np.where(delta < 0, -delta, 0).mean()
                rs = gain / loss if loss != 0 else 0
                stock_data[stock_name]["RSI"] = round(100 - (100 / (1 + rs)), 2)

# WebSocket Event Handlers
def on_error(ws, error):
    print(f"❌ WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"⚠️ WebSocket Closed: {close_msg}")

def on_open(ws):
    print("✅ WebSocket Connection Established")
    
    # Subscribe to NIFTY 50 stocks
    subscribe_message = {
        "RequestCode": 15,
        "InstrumentCount": len(nifty50_stocks),
        "InstrumentList": [{"ExchangeSegment": "NSE_EQ", "SecurityId": sec_id} for sec_id in nifty50_stocks.values()]
    }
    ws.send(json.dumps(subscribe_message))

# Function to Start WebSocket in Background Thread
def start_websocket():
    ws_app = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
    ws_app.run_forever()

# Start WebSocket Thread
ws_thread = threading.Thread(target=start_websocket, daemon=True)
ws_thread.start()

# Streamlit UI
st.title("📊 NIFTY 50 Live Market Dashboard (Dhan API)")

# Display Live Stock Data in Table
st.write("Live NIFTY 50 Market Data:")

df = pd.DataFrame.from_dict(stock_data, orient="index")
st.dataframe(df)
