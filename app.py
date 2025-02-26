# RDX Ver 1.0 - Updated with Merged F&O and Cash Market Data

import streamlit as st
import pandas as pd
import sqlite3

# Streamlit App Title
st.title("RDX Dashboard - Futures & Options Analysis")

# File Upload Section
st.sidebar.header("Upload Files")
cash_file = st.sidebar.file_uploader("Upload Cash Market Bhavcopy", type=["csv"])
fo_file = st.sidebar.file_uploader("Upload F&O Bhavcopy", type=["csv"])

# Connect to SQLite database
db_file = "rdx_data.db"
conn = sqlite3.connect(db_file)

# Fetch Merged Data
query = """
    SELECT f.Date, f.TckrSymb, f.Future_COI, f.Cumulative_Change_OI, 
           f.Cumulative_CE_OI, f.Cumulative_PE_OI, f.PCR, 
           c.Open, c.High, c.Low, c.Close, c.Delivery_Percentage
    FROM rdx_table f
    INNER JOIN cash_market_table c 
    ON f.Date = c.Date AND f.TckrSymb = c.TckrSymb
"""
merged_rdx_cash_data = pd.read_sql(query, conn)
conn.close()

# Sidebar Filters
st.sidebar.subheader("Filters")
deliv_min, deliv_max = st.sidebar.slider("Delivery Percentage Range", min_value=float(merged_rdx_cash_data["Delivery_Percentage"].min()), max_value=float(merged_rdx_cash_data["Delivery_Percentage"].max()), value=(float(merged_rdx_cash_data["Delivery_Percentage"].min()), float(merged_rdx_cash_data["Delivery_Percentage"].max())))
pcr_min, pcr_max = st.sidebar.slider("PCR Range", min_value=float(merged_rdx_cash_data["PCR"].min()), max_value=float(merged_rdx_cash_data["PCR"].max()), value=(float(merged_rdx_cash_data["PCR"].min()), float(merged_rdx_cash_data["PCR"].max())))

# Apply Filters
df_filtered = merged_rdx_cash_data[(merged_rdx_cash_data["Delivery_Percentage"] >= deliv_min) & (merged_rdx_cash_data["Delivery_Percentage"] <= deliv_max) &
                                    (merged_rdx_cash_data["PCR"] >= pcr_min) & (merged_rdx_cash_data["PCR"] <= pcr_max)]

# Display Filtered Merged RDX Dataset
st.subheader("Filtered Merged F&O and Cash Market Data")
st.dataframe(df_filtered)
