import streamlit as st
import pandas as pd
import datetime
import os
import sqlite3

# Streamlit App Title
st.title("RDX Dashboard - Single Day Data Upload")

# File Upload Section
st.sidebar.header("Upload Files")
cash_file = st.sidebar.file_uploader("Upload Cash Market Bhavcopy", type=["csv"])
fo_file = st.sidebar.file_uploader("Upload F&O Bhavcopy", type=["csv"])
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

# Function to process Cash Market Data
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

# Function to process F&O Bhavcopy Data
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
    
    # Extract Trade Date from F&O Bhavcopy
    trade_date = df_fo["TradDt"].iloc[0] if "TradDt" in df_fo.columns else datetime.datetime.today().strftime('%Y-%m-%d')
    df_rdx.insert(0, "Date", trade_date)
    
    return df_rdx

if cash_file and fo_file:
    st.success("Files Uploaded Successfully!")
    
    cash_data = process_cash_data(cash_file)
    fo_data = process_fo_data(fo_file)
    
    # Merge Processed Data
    rdx_data = fo_data.merge(cash_data, on="TckrSymb", how="inner")
    
    # Display Processed Data
    st.subheader("Processed RDX Dataset")
    st.dataframe(rdx_data)
    
    # Save to CSV
    filename = f"RDX_Data_{rdx_data['Date'].iloc[0]}.csv"
    rdx_data.to_csv(filename, index=False)
    st.success(f"RDX dataset saved as {filename}")
    
    # Store data in SQLite
    conn = sqlite3.connect(db_file)
    rdx_data.to_sql("rdx_table", conn, if_exists="append", index=False)
    conn.close()
    st.success("RDX dataset saved to SQLite database")

# Section to display SQLite stored data
st.sidebar.subheader("View Merged Data from SQLite")
if st.sidebar.button("Load Merged RDX Data"):
    conn = sqlite3.connect(db_file)
    query = "SELECT * FROM merged_rdx_table"
    stored_merged_rdx_data = pd.read_sql(query, conn)
    conn.close()
    st.subheader("Stored Merged RDX Data from SQLite")
    st.dataframe(stored_merged_rdx_data)
