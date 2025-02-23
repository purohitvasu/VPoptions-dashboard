import streamlit as st
import pandas as pd
import os
import datetime
from google.colab import drive

# 🚀 Step 1: Mount Google Drive
st.write("📂 Mounting Google Drive...")
drive.mount('/content/drive')

# Define Paths
nse_drive_path = "/content/drive/MyDrive/NSE_Data/"
cash_market_path = os.path.join(nse_drive_path, "Cash_Market")
fo_bhavcopy_path = os.path.join(nse_drive_path, "F&O_Bhavcopy")

# Ensure directories exist before accessing them
if not os.path.exists(cash_market_path):
    st.error(f"❌ Cash Market directory not found: {cash_market_path}")
    st.stop()

if not os.path.exists(fo_bhavcopy_path):
    st.error(f"❌ F&O Bhavcopy directory not found: {fo_bhavcopy_path}")
    st.stop()

# Function to Get the Latest File
def get_latest_file(directory, prefix):
    files = [f for f in os.listdir(directory) if f.startswith(prefix) and f.endswith(".csv")]
    if files:
        latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(directory, x)))
        return os.path.join(directory, latest_file)
    return None

# 🚀 Step 2: Load the Latest Bhavcopy Files
latest_cash_market_file = get_latest_file(cash_market_path, "sec_bhavdata_full_")
latest_fo_bhavcopy_file = get_latest_file(fo_bhavcopy_path, "fo_bhavcopy_")

st.title("📊 NSE Options Analysis Dashboard")

# 📌 Display Cash Market Data
if latest_cash_market_file and os.path.exists(latest_cash_market_file):
    cash_market_df = pd.read_csv(latest_cash_market_file)
    st.subheader("📌 Latest Cash Market Bhavcopy")
    st.dataframe(cash_market_df)
else:
    st.error("❌ No Cash Market Data Found!")

# 📌 Display F&O Bhavcopy Data
if latest_fo_bhavcopy_file and os.path.exists(latest_fo_bhavcopy_file):
    fo_bhavcopy_df = pd.read_csv(latest_fo_bhavcopy_file)
    st.subheader("📌 Latest F&O Bhavcopy")
    st.dataframe(fo_bhavcopy_df)
else:
    st.error("❌ No F&O Bhavcopy Data Found!")

# 📥 Download Report Button
st.subheader("📥 Download Latest Report")
if latest_cash_market_file:
    st.markdown(f"[Download Cash Market Bhavcopy](file://{latest_cash_market_file})")
if latest_fo_bhavcopy_file:
    st.markdown(f"[Download F&O Bhavcopy](file://{latest_fo_bhavcopy_file})")
