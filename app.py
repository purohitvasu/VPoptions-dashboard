import streamlit as st
import pandas as pd
import datetime
import gspread
import json
from google.oauth2.service_account import Credentials

# Streamlit App Title
st.title("RDX Dashboard - Futures & Options Analysis")

# File Upload Section
st.sidebar.header("Upload Files")
cash_file = st.sidebar.file_uploader("Upload Cash Market Bhavcopy", type=["csv"])
fo_file = st.sidebar.file_uploader("Upload F&O Bhavcopy", type=["csv"])

if cash_file and fo_file:
    # Load Cash Market Data
    df_cash = pd.read_csv(cash_file)
    df_cash.columns = df_cash.columns.str.strip()
    df_cash["DELIV_PER"] = pd.to_numeric(df_cash["DELIV_PER"], errors="coerce")
    df_cash_filtered = df_cash[["SYMBOL", "DELIV_PER"]]
    df_cash_filtered.rename(columns={"SYMBOL": "TckrSymb"}, inplace=True)
    
    # Load F&O Data
    df_fo = pd.read_csv(fo_file)
    df_futures = df_fo[df_fo['FinInstrmTp'].isin(['STF', 'IDF'])]
    df_options = df_fo[df_fo['FinInstrmTp'].isin(['STO', 'IDO'])]
    
    # Process Futures Data
    df_futures_cumulative = df_futures.groupby(["TckrSymb"]).agg({
        "OpnIntrst": "sum",
        "ChngInOpnIntrst": "sum",
        "OpnPric": "first",
        "HghPric": "max",
        "LwPric": "min",
        "ClsPric": "last"
    }).reset_index()
    df_futures_cumulative.rename(columns={
        "OpnIntrst": "Future_COI",
        "ChngInOpnIntrst": "Cumulative_Change_OI",
        "OpnPric": "Open_Price",
        "HghPric": "High_Price",
        "LwPric": "Low_Price",
        "ClsPric": "Close_Price"
    }, inplace=True)
    
    # Process Options Data
    df_options_cumulative = df_options.groupby(["TckrSymb", "OptnTp"]).agg({"OpnIntrst": "sum"}).reset_index()
    df_options_pivot = df_options_cumulative.pivot(index=["TckrSymb"], columns="OptnTp", values="OpnIntrst").reset_index()
    df_options_pivot.rename(columns={"CE": "Cumulative_CE_OI", "PE": "Cumulative_PE_OI"}, inplace=True)
    df_options_pivot.fillna(0, inplace=True)
    df_options_pivot["PCR"] = df_options_pivot["Cumulative_PE_OI"] / df_options_pivot["Cumulative_CE_OI"]
    df_options_pivot.replace([float('inf'), -float('inf')], 0, inplace=True)
    
    # Merge Data
    df_rdx = df_futures_cumulative.merge(df_options_pivot, on="TckrSymb", how="outer")
    df_rdx = df_rdx.merge(df_cash_filtered, on="TckrSymb", how="left")
    df_rdx.rename(columns={"DELIV_PER": "Delivery_Percentage"}, inplace=True)
    
    # Display RDX Dataset
    st.subheader("RDX Merged Dataset")
    st.dataframe(df_rdx)
    
    # Load Google Sheets credentials from Streamlit secrets
    creds_dict = json.loads(json.dumps(st.secrets["gcp_service_account"]))
    creds = Credentials.from_service_account_info(creds_dict)
    client = gspread.authorize(creds)
    
    # Save to Google Sheets
    sheet = client.open("RDX_Data").sheet1
    sheet.clear()
    sheet.update([df_rdx.columns.values.tolist()] + df_rdx.values.tolist())
    st.success("RDX dataset saved to Google Sheets")
