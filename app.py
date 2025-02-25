import streamlit as st
import pandas as pd
import os

# Define storage directory
STORAGE_DIR = "uploaded_data"
os.makedirs(STORAGE_DIR, exist_ok=True)

# Streamlit file uploader
st.title("NSE Bhavcopy Upload & Storage")
uploaded_file = st.file_uploader("Upload NSE Bhavcopy File", type=["csv"], accept_multiple_files=False)

if uploaded_file:
    file_path = os.path.join(STORAGE_DIR, uploaded_file.name)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success(f"File saved: {uploaded_file.name}")
    
    # Read and process file
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()  # Remove leading/trailing spaces
    
    # Identify Cash Market Bhavcopy
    if set(["TckrSymb", "LAST_PRICE", "DELIV_PER"]).issubset(df.columns):
        cash_market_df = df[["TckrSymb", "LAST_PRICE", "DELIV_PER"]]  # Select relevant columns
    else:
        # Process F&O Bhavcopy
        df_ce = df[df["OptnTp"] == "CE"].groupby("TckrSymb", as_index=False)["OpnIntrst"].sum()
        df_ce.rename(columns={"OpnIntrst": "CE_OI"}, inplace=True)
        
        df_pe = df[df["OptnTp"] == "PE"].groupby("TckrSymb", as_index=False)["OpnIntrst"].sum()
        df_pe.rename(columns={"OpnIntrst": "PE_OI"}, inplace=True)
        
        merged_df = pd.merge(df_ce, df_pe, on="TckrSymb", how="outer").fillna(0)
        merged_df["PCR"] = merged_df["PE_OI"] / merged_df["CE_OI"].replace(0, 1)
        
        # Merge with Cash Market Bhavcopy
        if 'cash_market_df' in locals():
            merged_df = merged_df.merge(cash_market_df, on="TckrSymb", how="left")
        
        # Display Pivot Table
        st.write("### Pivot Table View")
        st.write(merged_df)
        
        # Filters
        st.sidebar.header("Filters")
        if "DELIV_PER" in merged_df.columns:
            deliv_per_range = st.sidebar.slider("Delivery Percentage Range", float(merged_df["DELIV_PER"].min()), float(merged_df["DELIV_PER"].max()), (float(merged_df["DELIV_PER"].min()), float(merged_df["DELIV_PER"].max())))
            merged_df = merged_df[merged_df["DELIV_PER"].between(deliv_per_range[0], deliv_per_range[1])]
        
        st.write("### Filtered Data")
        st.write(merged_df)
else:
    st.warning("Please upload a CSV file.")
