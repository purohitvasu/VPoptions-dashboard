import streamlit as st
import websocket
import json
import threading

# Get API credentials from Streamlit secrets
access_token = st.secrets["secrets"]["DHAN_ACCESS_TOKEN"]

# Define WebSocket URL (without Client ID)
ws_url = f"wss://api-feed.dhan.co?version=2&token={access_token}&authType=2"

st.title("📈 Live Stock Dashboard - Dhan API")
st.subheader("Real-time Market Data")

# WebSocket message handler
def on_message(ws, message):
    data = json.loads(message)
    st.write(data)  # Display data on Streamlit

# WebSocket event handlers
def on_open(ws):
    st.success("WebSocket Connection Established ✅")
    subscribe_message = {
        "RequestCode": 15,
        "InstrumentCount": 1,
        "InstrumentList": [
            {
                "ExchangeSegment": "NSE_EQ",
                "SecurityId": "1333"  # Change this to your preferred stock symbol
            }
        ]
    }
    ws.send(json.dumps(subscribe_message))

def start_websocket():
    ws_app = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message)
    ws_app.run_forever()

# Run WebSocket in a separate thread
ws_thread = threading.Thread(target=start_websocket)
ws_thread.start()
