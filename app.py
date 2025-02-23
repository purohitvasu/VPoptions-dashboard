import streamlit as st
import pandas as pd
import os
import datetime

# 🚀 Step 1: Define Google Drive Path
gdrive_base_url = "https://drive.google.com/uc?id="

# **Manual File Upload as a Backup Option**
st.sidebar.header("📤 Upload New Bhavcopy")
uploaded_cash_file = st.sidebar.file_uploader("Upload Cash Market Bhavcopy (CSV)", type=["csv"])
uploaded_fo_file = st.sidebar.file_uploader("Upload F&O Bhavcopy (CSV)", type=["csv"])

# **Latest Available File IDs (Manually Update)**
cash_market_file_id = "1-93x9MZw2SGRcxRcZ6jQqxiivdlHi_LK"
fo_bhavcopy_file_id = "1-CBLBJMuFByy1_8bUdsOV-QfBZfl4dII"

# 🚀 Step 2: Load Latest Bhavcopy Files
def load_csv_from_drive(file_id):
    file_url = f"{gdrive_base_url}{file_id}"
    return pd.read_csv(file_url)

st.title("📊 NSE Options Analysis Dashboard")

# 📌 Display Cash Market Data
if uploaded_cash_file is not None:
    cash_market_df = pd.read_csv(uploaded_cash_file)
    st.subheader("📌 Latest Cash Market Bhavcopy (Uploaded)")
    st.dataframe(cash_market_df)
elif cash_market_file_id:
    try:
        cash_market_df = load_csv_from_drive(cash_market_file_id)
        st.subheader("📌 Latest Cash Market Bhavcopy (From Drive)")
        st.dataframe(cash_market_df)
    except Exception as e:
        st.error(f"❌ Error loading Cash Market Bhavcopy: {e}")

# 📌 Display F&O Bhavcopy Data
if uploaded_fo_file is not None:
    fo_bhavcopy_df = pd.read_csv(uploaded_fo_file)
    st.subheader("📌 Latest F&O Bhavcopy (Uploaded)")
    st.dataframe(fo_bhavcopy_df)
elif fo_bhavcopy_file_id:
    try:
        fo_bhavcopy_df = load_csv_from_drive(fo_bhavcopy_file_id)
        st.subheader("📌 Latest F&O Bhavcopy (From Drive)")
        st.dataframe(fo_bhavcopy_df)
    except Exception as e:
        st.error(f"❌ Error loading F&O Bhavcopy: {e}")

# 📥 Download Report Buttons
st.subheader("📥 Download Latest Report")
if cash_market_file_id:
    st.markdown(f"[Download Cash Market Bhavcopy](https://drive.google.com/uc?id={cash_market_file_id})")
if fo_bhavcopy_file_id:
    st.markdown(f"[Download F&O Bhavcopy](https://drive.google.com/uc?id={fo_bhavcopy_file_id})")
