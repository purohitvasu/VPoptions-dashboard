import streamlit as st
import websocket
import json
import threading

st.title("📈 Live Stock Dashboard - Dhan API")
st.subheader("Real-time Market Data")

# UI placeholder for live data updates
live_data_box = st.empty()

# Load API Token
try:
    access_token = st.secrets["secrets"]["DHAN_ACCESS_TOKEN"]
    st.success("✅ Access Token Loaded Successfully")
except Exception as e:
    st.error("❌ Error Loading Access Token")
    st.write(e)

# Define WebSocket URL
ws_url = f"wss://api-feed.dhan.co?version=2&token={access_token}&authType=2"

# WebSocket event handlers
def on_message(ws, message):
    data = json.loads(message)

    # Update UI inside Streamlit session
    with st.session_state_lock:
        live_data_box.write(f"📊 **Live Data:** {data}")

def on_error(ws, error):
    with st.session_state_lock:
        live_data_box.error(f"❌ WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    with st.session_state_lock:
        live_data_box.warning(f"⚠️ WebSocket Closed: {close_msg}")

def on_open(ws):
    with st.session_state_lock:
        live_data_box.success("✅ WebSocket Connection Established")
    
    subscribe_message = {
        "RequestCode": 15,
        "InstrumentCount": 1,
        "InstrumentList": [
            {
                "ExchangeSegment": "NSE_EQ",
                "SecurityId": "1333"  # Change this to your stock
            }
        ]
    }
    ws.send(json.dumps(subscribe_message))

# Function to start WebSocket in a thread
def start_websocket():
    ws_app = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
    ws_app.run_forever()

# Start WebSocket in a separate thread
ws_thread = threading.Thread(target=start_websocket, daemon=True)
ws_thread.start()
