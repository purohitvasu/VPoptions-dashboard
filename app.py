import streamlit as st
import pandas as pd
import datetime
import sqlite3

# Streamlit App Title
st.title("RDX-F&O Analysis")

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
    
    # Sidebar Filters
    st.sidebar.subheader("Filters")
    deliv_min, deliv_max = st.sidebar.slider("Delivery Percentage Range", min_value=float(df_rdx["Delivery_Percentage"].min()), max_value=float(df_rdx["Delivery_Percentage"].max()), value=(float(df_rdx["Delivery_Percentage"].min()), float(df_rdx["Delivery_Percentage"].max())))
    pcr_min, pcr_max = st.sidebar.slider("PCR Range", min_value=float(df_rdx["PCR"].min()), max_value=float(df_rdx["PCR"].max()), value=(float(df_rdx["PCR"].min()), float(df_rdx["PCR"].max())))
    
    # Apply Filters
    df_filtered = df_rdx[(df_rdx["Delivery_Percentage"] >= deliv_min) & (df_rdx["Delivery_Percentage"] <= deliv_max) &
                          (df_rdx["PCR"] >= pcr_min) & (df_rdx["PCR"] <= pcr_max)]
    
    # Display Filtered RDX Dataset
    st.subheader("Filtered RDX Dataset")
    st.dataframe(df_filtered)
    
    # Save to SQLite Database
    conn = sqlite3.connect("rdx_data.db")
    df_filtered.to_sql("rdx_table", conn, if_exists="replace", index=False)
    conn.close()
    st.success("Filtered RDX dataset saved to SQLite database")
