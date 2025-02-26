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
cursor = conn.cursor()

# List all tables in the database to debug missing table issue
tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
cursor.execute(tables_query)
available_tables = [table[0] for table in cursor.fetchall()]
st.sidebar.write("Available Tables in DB:", available_tables)

# Ensure tables exist
required_tables = {"cash_market_table", "rdx_table"}
missing_tables = required_tables - set(available_tables)
if missing_tables:
    st.error(f"Missing tables in database: {missing_tables}. Please ensure data is properly uploaded.")
    conn.close()
else:
    # Check if tables contain data
    cursor.execute("SELECT COUNT(*) FROM cash_market_table")
    cash_data_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM rdx_table")
    rdx_data_count = cursor.fetchone()[0]

    merged_rdx_cash_data = pd.DataFrame()

    if cash_data_count > 0 and rdx_data_count > 0:
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
    else:
        st.warning("Tables exist but contain no data. Please upload and process the required files.")

    conn.close()

    # Check if data exists before filtering
    if not merged_rdx_cash_data.empty:
        # Sidebar Filters
        st.sidebar.subheader("Filters")
        deliv_min, deliv_max = st.sidebar.slider("Delivery Percentage Range", 
            min_value=float(merged_rdx_cash_data["Delivery_Percentage"].min()), 
            max_value=float(merged_rdx_cash_data["Delivery_Percentage"].max()), 
            value=(float(merged_rdx_cash_data["Delivery_Percentage"].min()), float(merged_rdx_cash_data["Delivery_Percentage"].max())))
        
        pcr_min, pcr_max = st.sidebar.slider("PCR Range", 
            min_value=float(merged_rdx_cash_data["PCR"].min()), 
            max_value=float(merged_rdx_cash_data["PCR"].max()), 
            value=(float(merged_rdx_cash_data["PCR"].min()), float(merged_rdx_cash_data["PCR"].max())))

        # Apply Filters
        df_filtered = merged_rdx_cash_data[(merged_rdx_cash_data["Delivery_Percentage"] >= deliv_min) & (merged_rdx_cash_data["Delivery_Percentage"] <= deliv_max) &
                                            (merged_rdx_cash_data["PCR"] >= pcr_min) & (merged_rdx_cash_data["PCR"] <= pcr_max)]

        # Display Filtered Merged RDX Dataset
        st.subheader("Filtered Merged F&O and Cash Market Data")
        st.dataframe(df_filtered)
    else:
        st.warning("No data found in the database. Please upload the required files.")
