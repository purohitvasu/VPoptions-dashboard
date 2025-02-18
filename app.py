import streamlit as st
import pandas as pd
import requests

# Streamlit UI - Must be first command
st.set_page_config(layout="wide", page_title="Options & Futures Dashboard")

# Fyers API Credentials
client_id = "your_client_id"
access_token = "your_access_token"
headers = {"Authorization": f"Bearer {access_token}"}

# Function to fetch real-time data from Fyers API
def fetch_fyers_data(symbol):
    url = f"https://api.fyers.in/api/v2/market-data?symbols={symbol}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data["d"].get(symbol, {})
    else:
        return {}

# File Upload Section
st.sidebar.subheader("Upload NSE Bhavcopy Data")
fo_bhavcopy_file = st.sidebar.file_uploader("Upload NSE FO Bhavcopy Data", type=["csv"])
cm_bhavcopy_file = st.sidebar.file_uploader("Upload NSE CM Bhavcopy Data", type=["csv"])

@st.cache_data
def load_data(file):
    if file is not None:
        try:
            df = pd.read_csv(file, dtype=str)  # Ensure all data is read as string to prevent parsing errors
            df = df.rename(columns=str.strip)
            return df
        except Exception as e:
            st.error(f"Error processing file: {e}")
            return None
    return None

fo_bhavcopy_df = load_data(fo_bhavcopy_file)
cm_bhavcopy_df = load_data(cm_bhavcopy_file)

st.title("📊 Options & Futures Market Dashboard")

if fo_bhavcopy_df is not None and cm_bhavcopy_df is not None:
    required_columns_fo = {"XpryDt", "TckrSymb", "ChngInOpnIntrst", "OpnIntrst", "OptnTp"}
    required_columns_cm = {"SYMBOL", "DELIV_PER", "LAST_PRICE"}
    
    missing_columns_fo = required_columns_fo - set(fo_bhavcopy_df.columns)
    missing_columns_cm = required_columns_cm - set(cm_bhavcopy_df.columns)
    
    if missing_columns_fo:
        st.error(f"FO Bhavcopy file is missing required columns: {', '.join(missing_columns_fo)}")
        st.stop()
    
    if missing_columns_cm:
        st.error(f"CM Bhavcopy file is missing required columns: {', '.join(missing_columns_cm)}")
        st.stop()
    
    # Convert necessary columns to correct data types
    numeric_columns = ["ChngInOpnIntrst", "OpnIntrst", "DELIV_PER", "LAST_PRICE"]
    for col in numeric_columns:
        if col in fo_bhavcopy_df.columns:
            fo_bhavcopy_df[col] = pd.to_numeric(fo_bhavcopy_df[col], errors='coerce')
        if col in cm_bhavcopy_df.columns:
            cm_bhavcopy_df[col] = pd.to_numeric(cm_bhavcopy_df[col], errors='coerce')
    
    # Fetch real-time data for selected stock
    selected_stock = st.sidebar.text_input("Enter Stock Symbol (e.g., NSE:RELIANCE-EQ)")
    if selected_stock:
        fyers_data = fetch_fyers_data(selected_stock)
        if fyers_data:
            st.sidebar.subheader("Real-time Data from Fyers API")
            st.sidebar.write(f"LTP: {fyers_data.get('ltp', 'N/A')}")
            st.sidebar.write(f"20-SMA: {fyers_data.get('sma_20', 'N/A')}")
            st.sidebar.write(f"RSI (14): {fyers_data.get('rsi_14', 'N/A')}")
    
    # Expiry Filter
    fo_bhavcopy_df["XpryDt"] = pd.to_datetime(fo_bhavcopy_df["XpryDt"], errors='coerce')
    expiry_list = sorted(fo_bhavcopy_df["XpryDt"].dropna().unique())
    if expiry_list:
        selected_expiry = st.sidebar.selectbox("Select Expiry", expiry_list, format_func=lambda x: x.strftime('%Y-%m-%d'))
    else:
        st.warning("No valid expiry dates found in the uploaded FO Bhavcopy file.")
        st.stop()
    
    # Filter FO data based on selected expiry
    fo_expiry_data = fo_bhavcopy_df[fo_bhavcopy_df["XpryDt"] == selected_expiry]
    
    # Merge FO and CM Data on Stock Name
    cm_bhavcopy_df = cm_bhavcopy_df.rename(columns={"SYMBOL": "Stock", "DELIV_PER": "Delivery_Percentage", "LAST_PRICE": "LTP"})
    
    # Aggregate FO data
    summary_table = fo_expiry_data.groupby("TckrSymb").agg(
        Change_in_Future_OI=("ChngInOpnIntrst", "sum"),
        Future_OI=("OpnIntrst", "sum"),
        Total_Call_OI=("OpnIntrst", lambda x: x[fo_expiry_data["OptnTp"] == "CE"].sum() if "CE" in fo_expiry_data["OptnTp"].values else 0),
        Total_Put_OI=("OpnIntrst", lambda x: x[fo_expiry_data["OptnTp"] == "PE"].sum() if "PE" in fo_expiry_data["OptnTp"].values else 0),
    ).reset_index()
    
    # Merge with Delivery, LTP, SMA, and RSI Data
    merge_columns = ["Stock", "Delivery_Percentage", "LTP"]
    summary_table = summary_table.merge(cm_bhavcopy_df[merge_columns], left_on="TckrSymb", right_on="Stock", how="left").drop(columns=["Stock"])
    
    # Calculate PCR with 2 decimal places, handle division by zero
    summary_table["PCR"] = summary_table.apply(lambda row: round(row["Total_Put_OI"] / row["Total_Call_OI"], 2) if row["Total_Call_OI"] > 0 else 0, axis=1)
    
    # Format all numeric columns to two decimal places
    summary_table = summary_table.round(2)
    
    # Display Enhanced Table
    st.subheader(f"Stock Data for Expiry: {selected_expiry.date()}")
    st.dataframe(summary_table[["TckrSymb", "LTP", "Delivery_Percentage", "PCR", "Change_in_Future_OI", "Future_OI", "Total_Call_OI", "Total_Put_OI"]].style.set_properties(**{"font-size": "16px"}))
else:
    st.warning("Please upload both FO and CM Bhavcopy files to proceed.")
