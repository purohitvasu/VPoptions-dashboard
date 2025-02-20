import streamlit as st
import pandas as pd

def load_data(fo_file, cash_file):
    # Load F&O Bhavcopy
    fo_df = pd.read_csv(fo_file)
    
    # Process Futures Data
    futures_data = fo_df[fo_df["FinInstrmTp"] == "FUTSTK"].groupby(["TckrSymb", "XpryDt"]).agg(
        Future_OI=("OpnIntrst", "sum"),
        Future_OI_Change=("ChngInOpnIntrst", "sum")
    ).reset_index()
    
    # Process Options Data (Aggregate Call & Put OI)
    options_data = fo_df[fo_df["FinInstrmTp"] == "STO"].groupby(["TckrSymb", "XpryDt", "OptnTp"]) \
        ["OpnIntrst"].sum().unstack().fillna(0)
    options_data = options_data.rename(columns={"CE": "Total_Call_OI", "PE": "Total_Put_OI"})
    options_data["PCR"] = options_data["Total_Put_OI"] / options_data["Total_Call_OI"]
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
        st.dataframe(processed_data)
        
        # Filters
        stock_filter = st.selectbox("Select Stock", ["All"] + list(processed_data["TckrSymb"].unique()))
        expiry_filter = st.selectbox("Select Expiry Date", ["All"] + list(processed_data["XpryDt"].unique()))
        
        if stock_filter != "All":
            processed_data = processed_data[processed_data["TckrSymb"] == stock_filter]
        if expiry_filter != "All":
            processed_data = processed_data[processed_data["XpryDt"] == expiry_filter]
        
        st.dataframe(processed_data)

if __name__ == "__main__":
    main()
