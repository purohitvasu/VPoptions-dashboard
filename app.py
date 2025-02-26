import streamlit as st
import pandas as pd
import datetime
import os
import sqlite3

# Streamlit App Title
st.title("RDX Dashboard")

# Database file
db_file = "rdx_data.db"

# Clear SQLite database before processing new data
def clear_database():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS rdx_table")
    cursor.execute("DROP TABLE IF EXISTS merged_rdx_table")
    conn.commit()
    conn.close()
    st.sidebar.success("SQLite database cleared successfully")

if st.sidebar.button("Clear SQLite Database"):
    clear_database()

# Section 1: EOD Data
st.header("EOD Data")

# File Upload Section for EOD Data
cash_file = st.file_uploader("Upload Cash Market Bhavcopy", type=["csv"], key="cash_eod")
fo_file = st.file_uploader("Upload F&O Bhavcopy", type=["csv"], key="fo_eod")

if cash_file and fo_file:
    st.success("Files Uploaded Successfully!")
    
    def process_cash_data(cash_file):
        df_cash = pd.read_csv(cash_file)
        df_cash.columns = df_cash.columns.str.strip()
        df_cash = df_cash[["SYMBOL", "OPEN_PRICE", "HIGH_PRICE", "LOW_PRICE", "CLOSE_PRICE", "DELIV_PER"]]
        df_cash.rename(columns={
            "SYMBOL": "TckrSymb",
            "OPEN_PRICE": "Open",
            "HIGH_PRICE": "High",
            "LOW_PRICE": "Low",
            "CLOSE_PRICE": "Close",
            "DELIV_PER": "Delivery_Percentage"
        }, inplace=True)
        return df_cash
    
    def process_fo_data(fo_file):
        df_fo = pd.read_csv(fo_file)
        df_futures = df_fo[df_fo['FinInstrmTp'].isin(['STF', 'IDF'])]
        df_options = df_fo[df_fo['FinInstrmTp'].isin(['STO', 'IDO'])]
        
        df_futures_cumulative = df_futures.groupby(["TckrSymb"]).agg({
            "OpnIntrst": "sum",
            "ChngInOpnIntrst": "sum"
        }).reset_index()
        df_futures_cumulative.rename(columns={
            "OpnIntrst": "Future_COI",
            "ChngInOpnIntrst": "Cumulative_Change_OI"
        }, inplace=True)
        
        df_options_cumulative = df_options.groupby(["TckrSymb", "OptnTp"]).agg({"OpnIntrst": "sum"}).reset_index()
        df_options_pivot = df_options_cumulative.pivot(index=["TckrSymb"], columns="OptnTp", values="OpnIntrst").reset_index()
        df_options_pivot.rename(columns={"CE": "Cumulative_CE_OI", "PE": "Cumulative_PE_OI"}, inplace=True)
        df_options_pivot.fillna(0, inplace=True)
        df_options_pivot["PCR"] = df_options_pivot["Cumulative_PE_OI"] / df_options_pivot["Cumulative_CE_OI"]
        df_options_pivot.replace([float('inf'), -float('inf')], 0, inplace=True)
        
        df_rdx = df_futures_cumulative.merge(df_options_pivot, on="TckrSymb", how="outer")
        
        trade_date = df_fo["TradDt"].iloc[0] if "TradDt" in df_fo.columns else datetime.datetime.today().strftime('%Y-%m-%d')
        df_rdx.insert(0, "Date", trade_date)
        
        return df_rdx
    
    cash_data = process_cash_data(cash_file)
    fo_data = process_fo_data(fo_file)
    rdx_data = fo_data.merge(cash_data, on="TckrSymb", how="inner")
    
    # Display Filtered EOD Data
    st.subheader("Processed EOD Data")
    st.dataframe(rdx_data[["TckrSymb", "Future_COI", "Cumulative_Change_OI", "Cumulative_CE_OI", "Cumulative_PE_OI", "PCR", "Open", "High", "Low", "Close", "Delivery_Percentage"]])
    
    # Add Filters
    min_pcr, max_pcr = st.slider("Filter by PCR", min_value=0.0, max_value=5.0, value=(0.0, 5.0))
    min_deliv, max_deliv = st.slider("Filter by Delivery Percentage", min_value=0.0, max_value=100.0, value=(0.0, 100.0))
    
    filtered_rdx_data = rdx_data[(rdx_data["PCR"] >= min_pcr) & (rdx_data["PCR"] <= max_pcr) &
                                 (rdx_data["Delivery_Percentage"] >= min_deliv) & (rdx_data["Delivery_Percentage"] <= max_deliv)]
    
    st.dataframe(filtered_rdx_data)

# Section 2: Historical Data
st.header("Historical Data")

historical_file = st.file_uploader("Upload Historical Data", type=["csv"], key="historical")
if historical_file:
    historical_data = pd.read_csv(historical_file)
    st.subheader("Historical Data")
    st.dataframe(historical_data)
