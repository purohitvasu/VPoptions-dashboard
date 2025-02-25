import streamlit as st
import pandas as pd
import os

# Define storage directory
STORAGE_DIR = "uploaded_data"
os.makedirs(STORAGE_DIR, exist_ok=True)

# Streamlit file uploader
st.title("NSE Bhavcopy Upload & Storage")
uploaded_files = st.file_uploader("Upload NSE Bhavcopy Files", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        file_path = os.path.join(STORAGE_DIR, uploaded_file.name)
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"File saved: {uploaded_file.name}")

# Read and merge all stored CSV files based on TckrSymb and Expiry Date
def load_and_merge_data(directory):
    all_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".csv")]
    data_frames = []
    cash_market_df = None  # Placeholder for Cash Market Bhavcopy
    
    for file in all_files:
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip()  # Remove leading/trailing spaces
        
        # Extract date from filename (assuming format includes YYYYMMDD)
        date_str = "".join(filter(str.isdigit, os.path.basename(file)))  # Extract numbers from filename
        df["Date"] = pd.to_datetime(date_str, format="%Y%m%d", errors="coerce")
        
        # Identify Cash Market Bhavcopy based on known structure
        if set(["TckrSymb", "LAST_PRICE", "DELIV_PER"]).issubset(df.columns):
            cash_market_df = df[["TckrSymb", "LAST_PRICE", "DELIV_PER"]]  # Select relevant columns
        else:
            data_frames.append(df)
    
    # Combine all F&O files based on TckrSymb and Expiry Date
    if data_frames:
        merged_df = pd.concat(data_frames, ignore_index=True)
        
        # Separate CE and PE Open Interest into different columns
        merged_df_ce = merged_df[merged_df["OptnTp"] == "CE"].groupby(["TckrSymb", "XpryDt"], as_index=False)["OpnIntrst"].sum()
        merged_df_ce.rename(columns={"OpnIntrst": "CE_OpnIntrst"}, inplace=True)
        
        merged_df_pe = merged_df[merged_df["OptnTp"] == "PE"].groupby(["TckrSymb", "XpryDt"], as_index=False)["OpnIntrst"].sum()
        merged_df_pe.rename(columns={"OpnIntrst": "PE_OpnIntrst"}, inplace=True)
        
        # Merge CE and PE Open Interest
        merged_df = pd.merge(merged_df_ce, merged_df_pe, on=["TckrSymb", "XpryDt"], how="outer").fillna(0)
        
        # Compute PCR (Put-Call Ratio)
        merged_df["PCR"] = merged_df["PE_OpnIntrst"] / merged_df["CE_OpnIntrst"].replace(0, 1)
        
        # Merge with Cash Market Bhavcopy if available
        if cash_market_df is not None:
            merged_df = merged_df.merge(cash_market_df, on="TckrSymb", how="left")
        
        return merged_df
    else:
        return None

# Load merged data
merged_data = load_and_merge_data(STORAGE_DIR)
if merged_data is not None:
    # Filters for user selection
    st.sidebar.header("Filters")
    expiry_dates = merged_data["XpryDt"].dropna().unique()
    selected_expiry = st.sidebar.selectbox("Select Expiry Date", expiry_dates)
    
    if "DELIV_PER" in merged_data.columns:
        deliv_per_range = st.sidebar.slider("Delivery Percentage Range", float(merged_data["DELIV_PER"].min()), float(merged_data["DELIV_PER"].max()), (float(merged_data["DELIV_PER"].min()), float(merged_data["DELIV_PER"].max())))
        filtered_data = merged_data[(merged_data["XpryDt"] == selected_expiry) & (merged_data["DELIV_PER"].between(deliv_per_range[0], deliv_per_range[1]))]
    else:
        filtered_data = merged_data[merged_data["XpryDt"] == selected_expiry]
    
    # Display pivot-style table
    pivot_columns = ["CE_OpnIntrst", "PE_OpnIntrst", "PCR"]
    if "LAST_PRICE" in merged_data.columns:
        pivot_columns.append("LAST_PRICE")
    if "DELIV_PER" in merged_data.columns:
        pivot_columns.append("DELIV_PER")
    
    pivot_table = filtered_data.pivot_table(index="TckrSymb", values=pivot_columns, aggfunc="sum")
    st.write("### Pivot Table View")
    st.write(pivot_table)
else:
    st.warning("No data available. Please upload CSV files.")

# Display list of stored files
stored_files = os.listdir(STORAGE_DIR)
if stored_files:
    st.write("### Stored Files:")
    st.write(stored_files)
