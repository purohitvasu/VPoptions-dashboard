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
    cash_df = cash_df[["TckrSymb", "LAST_PRICE", "DELIV_PER"]]
    
    # Read and process F&O Bhavcopy
    fo_df = pd.read_csv(fo_bhavcopy_path)
    fo_df.columns = fo_df.columns.str.strip()
    
    if "OptnTp" in fo_df.columns:
        fo_ce = fo_df[fo_df["OptnTp"] == "CE"].groupby("TckrSymb", as_index=False)["OpnIntrst"].sum()
        fo_ce.rename(columns={"OpnIntrst": "CE_OI"}, inplace=True)
        
        fo_pe = fo_df[fo_df["OptnTp"] == "PE"].groupby("TckrSymb", as_index=False)["OpnIntrst"].sum()
        fo_pe.rename(columns={"OpnIntrst": "PE_OI"}, inplace=True)
        
        merged_df = pd.merge(fo_ce, fo_pe, on="TckrSymb", how="outer").fillna(0)
        merged_df["PCR"] = merged_df["PE_OI"] / merged_df["CE_OI"].replace(0, 1)
        
        # Merge with Cash Market Bhavcopy
        merged_df = merged_df.merge(cash_df, on="TckrSymb", how="left")
        
        # Ensure Last Price and Delivery Percentage are in the table
        if "LAST_PRICE" not in merged_df.columns:
            merged_df["LAST_PRICE"] = None
        if "DELIV_PER" not in merged_df.columns:
            merged_df["DELIV_PER"] = None
        
        # Save merged data with today's date
        today_date = datetime.datetime.today().strftime('%Y%m%d')
        merged_filename = f"Day_Data_{today_date}.csv"
        merged_filepath = os.path.join(STORAGE_DIR, merged_filename)
        merged_df.to_csv(merged_filepath, index=False)
        
        st.success(f"Merged data saved as {merged_filename}")
        
        # Display Pivot Table
        pivot_table = merged_df[["TckrSymb", "LAST_PRICE", "DELIV_PER", "CE_OI", "PE_OI", "PCR"]]
        st.write("### Mapped Stock Data")
        st.write(pivot_table)
        
        # Filters
        st.sidebar.header("Filters")
        deliv_per_range = st.sidebar.slider("Delivery Percentage Range", float(merged_df["DELIV_PER"].min(skipna=True)), float(merged_df["DELIV_PER"].max(skipna=True)), (float(merged_df["DELIV_PER"].min(skipna=True)), float(merged_df["DELIV_PER"].max(skipna=True))))
        pcr_range = st.sidebar.slider("PCR Range", float(merged_df["PCR"].min(skipna=True)), float(merged_df["PCR"].max(skipna=True)), (float(merged_df["PCR"].min(skipna=True)), float(merged_df["PCR"].max(skipna=True))))
        
        filtered_df = merged_df[(merged_df["DELIV_PER"].between(deliv_per_range[0], deliv_per_range[1])) & (merged_df["PCR"].between(pcr_range[0], pcr_range[1]))]
        
        st.write("### Filtered Data")
        st.write(filtered_df)
    else:
        st.warning("Column 'OptnTp' is missing in the F&O Bhavcopy. Unable to process CE and PE Open Interest.")
else:
    st.warning("Please upload both Cash Market and F&O Bhavcopy files.")
