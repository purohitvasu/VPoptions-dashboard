import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Streamlit UI - Must be first command
st.set_page_config(layout="wide", page_title="Options & Futures Dashboard")

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
    # Ensure required columns exist dynamically
    required_columns_fo = {"XpryDt", "TckrSymb", "ClsPric", "OpnIntrst", "ChngInOpnIntrst", "OptnTp"}
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
    numeric_columns = ["ClsPric", "OpnIntrst", "ChngInOpnIntrst", "DELIV_PER", "LAST_PRICE"]
    for col in numeric_columns:
        if col in fo_bhavcopy_df.columns:
            fo_bhavcopy_df[col] = pd.to_numeric(fo_bhavcopy_df[col], errors='coerce')
        if col in cm_bhavcopy_df.columns:
            cm_bhavcopy_df[col] = pd.to_numeric(cm_bhavcopy_df[col], errors='coerce')
    
    # Calculate 20 SMA for Price if LAST_PRICE exists
    if "LAST_PRICE" in cm_bhavcopy_df.columns:
        cm_bhavcopy_df["20_SMA"] = cm_bhavcopy_df["LAST_PRICE"].rolling(window=20).mean()
    
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
    
    # Ensure Option Type is handled correctly to avoid errors
    fo_expiry_data = fo_expiry_data.assign(OptnTp=fo_expiry_data["OptnTp"].fillna(""))
    
    summary_table = fo_expiry_data.groupby("TckrSymb").agg(
        Future_OI=("OpnIntrst", "sum"),
        Change_in_Future_OI=("ChngInOpnIntrst", "sum"),
        Total_Call_OI=("OpnIntrst", lambda x: x[fo_expiry_data["OptnTp"] == "CE"].sum() if "CE" in fo_expiry_data["OptnTp"].values else 0),
        Total_Put_OI=("OpnIntrst", lambda x: x[fo_expiry_data["OptnTp"] == "PE"].sum() if "PE" in fo_expiry_data["OptnTp"].values else 0),
    ).reset_index()
    
    # Merge with Delivery, LTP, SMA Data
    merge_columns = ["Stock", "Delivery_Percentage", "LTP"]
    if "20_SMA" in cm_bhavcopy_df.columns:
        merge_columns.append("20_SMA")
    
    summary_table = summary_table.merge(cm_bhavcopy_df[merge_columns], left_on="TckrSymb", right_on="Stock", how="left").drop(columns=["Stock"])
    
    # Calculate PCR with 2 decimal places, handle division by zero
    summary_table["PCR"] = summary_table.apply(lambda row: round(row["Total_Put_OI"] / row["Total_Call_OI"], 2) if row["Total_Call_OI"] > 0 else 0, axis=1)
    
    # Display Enhanced Table
    st.subheader(f"Stock Data for Expiry: {selected_expiry.date()}")
    st.dataframe(summary_table.style.set_properties(**{"font-size": "16px"}))
else:
    st.warning("Please upload both FO and CM Bhavcopy files to proceed.")
