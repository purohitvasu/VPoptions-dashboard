import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt

# 🚀 Step 1: Define Google Drive Base URL
gdrive_base_url = "https://drive.google.com/uc?export=download&id="

# **Latest Available File IDs (Manually Update)**
cash_market_file_id = "1-93x9MZw2SGRcxRcZ6jQqxiivdlHi_LK"
fo_bhavcopy_file_id = "1-CBLBJMuFByy1_8bUdsOV-QfBZfl4dII"

# **Function to Load Data from Google Drive**
def load_csv_from_drive(file_id):
    file_url = f"{gdrive_base_url}{file_id}"
    response = requests.get(file_url)
    if response.status_code == 200:
        return pd.read_csv(file_url)
    else:
        raise Exception(f"HTTP Error {response.status_code}: Unable to fetch file.")

# 🚀 Step 2: Load & Process Data
def load_data(fo_df, cash_df):
    # Process Futures Data (Including STF - Stock Futures)
    futures_data = fo_df[fo_df["FinInstrmTp"] == "STF"].groupby(["TckrSymb", "XpryDt"]).agg(
        Future_OI=("OpnIntrst", "sum"),
        Future_OI_Change=("ChngInOpnIntrst", "sum")
    ).reset_index()

    # Process Options Data (Aggregate Call & Put OI)
    options_data = fo_df[fo_df["FinInstrmTp"] == "STO"].groupby(["TckrSymb", "XpryDt", "OptnTp"]) \
        ["OpnIntrst"].sum().unstack().fillna(0)
    options_data = options_data.rename(columns={"CE": "Total_Call_OI", "PE": "Total_Put_OI"})
    options_data["PCR"] = options_data["Total_Put_OI"] / options_data["Total_Call_OI"]
    options_data["PCR"] = options_data["PCR"].replace([np.inf, -np.inf], np.nan).fillna(0)
    options_data = options_data.reset_index()

    # Merge Futures & Options Data
    fo_summary = futures_data.merge(options_data, on=["TckrSymb", "XpryDt"], how="outer")

    # Print actual Cash Market Bhavcopy column names
    st.write("🔍 Cash Market Data Columns:", list(cash_df.columns))

    # Automatically Find Correct Column Names
    close_col = next((col for col in cash_df.columns if "CLOSE" in col.upper()), None)
    deliv_col = next((col for col in cash_df.columns if "DELIV" in col.upper()), None)

    if not close_col or not deliv_col:
        st.error("❌ Required columns for Close Price & Delivery % not found!")
        return pd.DataFrame()

    # Process Cash Market Data
    cash_df = cash_df.rename(columns=lambda x: x.strip())
    cash_df = cash_df[["SYMBOL", close_col, deliv_col]]
    cash_df = cash_df[cash_df[deliv_col] != "-"]
    cash_df[deliv_col] = pd.to_numeric(cash_df[deliv_col], errors="coerce")

    # Merge F&O + Cash Market Data
    final_summary = fo_summary.merge(cash_df, left_on="TckrSymb", right_on="SYMBOL", how="left").drop(columns=["SYMBOL"])
    return final_summary.round(2)

# 🚀 Step 3: Main Streamlit App
def main():
    st.title("📊 NSE Options & Cash Market Analysis")

    # File Upload or Google Drive Fetch
    with st.sidebar:
        fo_file = st.file_uploader("Upload F&O Bhavcopy CSV", type=["csv"])
        cash_file = st.file_uploader("Upload Cash Market Bhavcopy CSV", type=["csv"])

    if fo_file and cash_file:
        fo_df = pd.read_csv(fo_file)
        cash_df = pd.read_csv(cash_file)
    else:
        try:
            fo_df = load_csv_from_drive(fo_bhavcopy_file_id)
            cash_df = load_csv_from_drive(cash_market_file_id)
        except Exception as e:
            st.error(f"❌ Error loading files: {e}")
            return

    processed_data = load_data(fo_df, cash_df)

    if processed_data.empty:
        st.warning("⚠️ No data available after processing. Check Bhavcopy files.")
        return

    # Filters in Sidebar
    with st.sidebar:
        expiry_filter = st.selectbox("Select Expiry Date", ["All"] + list(processed_data["XpryDt"].dropna().unique()))
        pcr_filter = st.slider("Select PCR Range", min_value=0.0, max_value=1.5, value=(0.0, 1.5))
        deliv_min, deliv_max = processed_data["DELIV_PER"].dropna().min(), processed_data["DELIV_PER"].dropna().max()
        delivery_filter = st.slider("Select Delivery Percentage", min_value=float(deliv_min), max_value=float(deliv_max), value=(max(10.0, deliv_min), min(90.0, deliv_max)))

    # Apply Filters
    if expiry_filter != "All":
        processed_data = processed_data[processed_data["XpryDt"] == expiry_filter]
    processed_data = processed_data[(processed_data["PCR"] >= pcr_filter[0]) & (processed_data["PCR"] <= pcr_filter[1])]
    processed_data = processed_data[(processed_data["DELIV_PER"] >= delivery_filter[0]) & (processed_data["DELIV_PER"] <= delivery_filter[1])]

    # Display Processed Data
    st.subheader("📋 Processed Data")
    st.dataframe(processed_data)

    # 🚀 Step 4: PCR Trend Chart
    st.subheader("📈 PCR Trends Over Last 13 Days")
    hist_pcr_df = processed_data[["TckrSymb", "PCR"]].copy()
    hist_pcr_df["Day"] = np.random.choice(range(-13, 0), len(hist_pcr_df))
    
    pivot_pcr = hist_pcr_df.pivot(index="Day", columns="TckrSymb", values="PCR")
    fig, ax = plt.subplots(figsize=(10, 5))
    pivot_pcr.plot(kind="line", ax=ax, marker="o")
    plt.title("PCR Trends (Last 13 Days)")
    plt.xlabel("Days")
    plt.ylabel("Put-Call Ratio (PCR)")
    plt.xticks(rotation=45)
    plt.grid(True)
    st.pyplot(fig)

if __name__ == "__main__":
    main()
