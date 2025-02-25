import streamlit as st
import pandas as pd
import os
import datetime

# Define storage directory
STORAGE_DIR = "uploaded_data"
os.makedirs(STORAGE_DIR, exist_ok=True)

# Streamlit file uploader
st.title("NSE Bhavcopy Upload & Storage")

st.header("Upload Cash Market Bhavcopy")
cash_market_file = st.file_uploader("Upload Cash Market File", type=["csv"], key="cash")

st.header("Upload F&O Bhavcopy")
fo_bhavcopy_file = st.file_uploader("Upload F&O Bhavcopy File", type=["csv"], key="fo")

if cash_market_file and fo_bhavcopy_file:
    # Save files
    cash_market_path = os.path.join(STORAGE_DIR, cash_market_file.name)
    fo_bhavcopy_path = os.path.join(STORAGE_DIR, fo_bhavcopy_file.name)
    
    with open(cash_market_path, "wb") as f:
        f.write(cash_market_file.getbuffer())
    with open(fo_bhavcopy_path, "wb") as f:
        f.write(fo_bhavcopy_file.getbuffer())
    
    st.success("Files uploaded successfully!")
    
    # Read and process Cash Market Bhavcopy
    cash_df = pd.read_csv(cash_market_path)
    cash_df.columns = cash_df.columns.str.strip()
    if "SYMBOL" in cash_df.columns:
        cash_df.rename(columns={"SYMBOL": "TckrSymb"}, inplace=True)
        cash_df["LAST_PRICE"] = pd.to_numeric(cash_df["LAST_PRICE"], errors="coerce")
        cash_df["DELIV_PER"] = pd.to_numeric(cash_df["DELIV_PER"], errors="coerce")
        cash_df = cash_df[["TckrSymb", "LAST_PRICE", "DELIV_PER"]]
    else:
        st.warning("Column 'SYMBOL' not found in Cash Market Bhavcopy. Please check the file.")
        cash_df = None
    
    # Read and process F&O Bhavcopy
    fo_df = pd.read_csv(fo_bhavcopy_path)
    fo_df.columns = fo_df.columns.str.strip()
    
    if "TckrSymb" in fo_df.columns and "OptnTp" in fo_df.columns:
        fo_df["OpnIntrst"] = pd.to_numeric(fo_df["OpnIntrst"], errors="coerce")
        
        fo_ce = fo_df[fo_df["OptnTp"] == "CE"].groupby("TckrSymb", as_index=False)["OpnIntrst"].sum()
        fo_ce.rename(columns={"OpnIntrst": "CE_OI"}, inplace=True)
        
        fo_pe = fo_df[fo_df["OptnTp"] == "PE"].groupby("TckrSymb", as_index=False)["OpnIntrst"].sum()
        fo_pe.rename(columns={"OpnIntrst": "PE_OI"}, inplace=True)
        
        merged_df = pd.merge(fo_ce, fo_pe, on="TckrSymb", how="outer").fillna(0)
        merged_df["PCR"] = merged_df["PE_OI"] / merged_df["CE_OI"].replace(0, 1)
        
        # Merge with Cash Market Bhavcopy if available
        if cash_df is not None:
            merged_df = merged_df.merge(cash_df, on="TckrSymb", how="inner")
        
        # Save merged data with today's date
        today_date = datetime.datetime.today().strftime('%Y%m%d')
        merged_filename = f"Day_Data_{today_date}.csv"
        merged_filepath = os.path.join(STORAGE_DIR, merged_filename)
        merged_df.to_csv(merged_filepath, index=False)
        
        st.success(f"Merged data saved as {merged_filename}")
        
        # Filters
        st.sidebar.header("Filters")
        if "DELIV_PER" in merged_df.columns and "PCR" in merged_df.columns:
            deliv_per_range = st.sidebar.slider("Delivery Percentage Range", float(merged_df["DELIV_PER"].min(skipna=True)), float(merged_df["DELIV_PER"].max(skipna=True)), (float(merged_df["DELIV_PER"].min(skipna=True)), float(merged_df["DELIV_PER"].max(skipna=True))))
            pcr_range = st.sidebar.slider("PCR Range", float(merged_df["PCR"].min(skipna=True)), float(merged_df["PCR"].max(skipna=True)), (float(merged_df["PCR"].min(skipna=True)), float(merged_df["PCR"].max(skipna=True))))
            
            filtered_df = merged_df[(merged_df["DELIV_PER"].between(deliv_per_range[0], deliv_per_range[1])) & (merged_df["PCR"].between(pcr_range[0], pcr_range[1]))]
            
            st.write("### F&O Stock Data for Today")
            st.write(filtered_df)
    else:
        st.warning("Required columns 'TckrSymb' or 'OptnTp' missing in the F&O Bhavcopy. Please check the file.")
else:
    st.warning("Please upload both Cash Market and F&O Bhavcopy files.")
