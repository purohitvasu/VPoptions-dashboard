import streamlit as st
import pandas as pd
import numpy as np

def load_data(fo_file, cash_file):
    # Load F&O Bhavcopy
    fo_df = pd.read_csv(fo_file)
    
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
    
    # Load Cash Market Bhavcopy
    cash_df = pd.read_csv(cash_file)
    cash_df = cash_df.rename(columns=lambda x: x.strip())
    cash_df = cash_df[["SYMBOL", "CLOSE_PRICE", "DELIV_PER"]]
    cash_df = cash_df[cash_df["DELIV_PER"] != "-"]
    cash_df["DELIV_PER"] = pd.to_numeric(cash_df["DELIV_PER"], errors="coerce")
    
    # Merge Cash Market Data
    final_summary = fo_summary.merge(cash_df, left_on="TckrSymb", right_on="SYMBOL", how="left").drop(columns=["SYMBOL"])
    final_summary = final_summary.round(2)
    
    return final_summary

def main():
    st.title("NSE F&O and Cash Market Data Analysis")
    
    fo_file = st.file_uploader("Upload F&O Bhavcopy CSV", type=["csv"])
    cash_file = st.file_uploader("Upload Cash Market Bhavcopy CSV", type=["csv"])
    
    if fo_file and cash_file:
        processed_data = load_data(fo_file, cash_file)
        
        # Filters
        expiry_filter = st.selectbox("Select Expiry Date", ["All"] + list(processed_data["XpryDt"].dropna().unique()))
        pcr_min, pcr_max = processed_data["PCR"].dropna().min(), processed_data["PCR"].dropna().max()
        pcr_filter = st.slider("Select PCR Range", min_value=float(pcr_min), max_value=float(pcr_max), value=(max(0.0, pcr_min), min(1.5, pcr_max)))
        deliv_min, deliv_max = processed_data["DELIV_PER"].dropna().min(), processed_data["DELIV_PER"].dropna().max()
        delivery_filter = st.slider("Select Delivery Percentage Range", min_value=float(deliv_min), max_value=float(deliv_max), value=(max(10.0, deliv_min), min(90.0, deliv_max)))
        
        if expiry_filter != "All":
            processed_data = processed_data[processed_data["XpryDt"] == expiry_filter]
        processed_data = processed_data[(processed_data["PCR"] >= pcr_filter[0]) & (processed_data["PCR"] <= pcr_filter[1])]
        processed_data = processed_data[(processed_data["DELIV_PER"] >= delivery_filter[0]) & (processed_data["DELIV_PER"] <= delivery_filter[1])]
        
        st.dataframe(processed_data)

if __name__ == "__main__":
    main()
