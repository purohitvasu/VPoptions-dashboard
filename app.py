import streamlit as st
import pandas as pd
import datetime
import os

# Streamlit App Title
st.title("RDX Dashboard")

# Sidebar: EOD Data Uploads
st.sidebar.header("EOD Data Uploads")
cash_file = st.sidebar.file_uploader("Upload Cash Market Bhavcopy", type=["csv"], key="cash_eod")
fo_file = st.sidebar.file_uploader("Upload F&O Bhavcopy", type=["csv"], key="fo_eod")

# Sidebar: EOD Data Filters
st.sidebar.header("EOD Data Filters")
min_pcr, max_pcr = st.sidebar.slider("Filter by PCR", min_value=0.0, max_value=5.0, value=(0.0, 5.0))
min_deliv, max_deliv = st.sidebar.slider("Filter by Delivery Percentage", min_value=0.0, max_value=100.0, value=(0.0, 100.0))

# Section 1: EOD Data
st.header("EOD Data")

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
        df_cash["Delivery_Percentage"] = pd.to_numeric(df_cash["Delivery_Percentage"], errors='coerce')
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
        df_rdx["PCR"] = pd.to_numeric(df_rdx["PCR"], errors='coerce')
        return df_rdx
    
    cash_data = process_cash_data(cash_file)
    fo_data = process_fo_data(fo_file)
    rdx_data = fo_data.merge(cash_data, on="TckrSymb", how="inner")
    
    # Apply Filters
    filtered_rdx_data = rdx_data[(rdx_data["PCR"] >= min_pcr) & (rdx_data["PCR"] <= max_pcr) &
                                 (rdx_data["Delivery_Percentage"] >= min_deliv) & (rdx_data["Delivery_Percentage"] <= max_deliv)]
    
    # Display Processed EOD Data in a Single Table with Filters Applied
    st.subheader("Processed EOD Data")
    st.dataframe(filtered_rdx_data)
    
    # Save Processed Data for Download
    output_filename = f"Processed_RDX_{rdx_data['Date'].iloc[0]}.csv"
    rdx_data.to_csv(output_filename, index=False)
    
    # Provide Download Button
    with open(output_filename, "rb") as file:
        st.download_button(
            label="Download Processed RDX Data",
            data=file,
            file_name=output_filename,
            mime="text/csv"
        )

# Sidebar: Historical Data Upload
st.sidebar.header("Historical Data Upload")
historical_file = st.sidebar.file_uploader("Upload Historical Data", type=["csv"], key="historical")

# Section 2: Historical Data
st.header("Historical Data")
if historical_file:
    historical_data = pd.read_csv(historical_file)
    st.subheader("Historical Data")
    st.dataframe(historical_data)
