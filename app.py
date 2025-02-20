import streamlit as st
import pandas as pd
import numpy as np
import sqlite3

def init_db():
    conn = sqlite3.connect("market_data.db")
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_data (
            TckrSymb TEXT,
            XpryDt TEXT,
            Future_OI REAL,
            Future_OI_Change REAL,
            Total_Call_OI REAL,
            Total_Put_OI REAL,
            PCR REAL,
            CLOSE_PRICE REAL,
            DELIV_PER REAL,
            Sentiment TEXT
        )
    ''')
    conn.commit()
    conn.close()

def classify_sentiment(row):
    if row["PCR"] < 0.7 and row["Future_OI_Change"] > 0 and row["DELIV_PER"] > 50:
        return "Bullish"
    elif row["PCR"] > 1.0 and row["Future_OI_Change"] < 0 and row["DELIV_PER"] < 30:
        return "Bearish"
    else:
        return "Neutral"

def save_to_db(data):
    conn = sqlite3.connect("market_data.db")
    data.to_sql("market_data", conn, if_exists="replace", index=False)
    conn.close()

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
    
    # Classify Market Sentiment
    final_summary["Sentiment"] = final_summary.apply(classify_sentiment, axis=1)
    
    final_summary = final_summary.round(2)
    
    # Save to Database
    save_to_db(final_summary)
    
    return final_summary

def query_db():
    conn = sqlite3.connect("market_data.db")
    df = pd.read_sql("SELECT * FROM market_data", conn)
    conn.close()
    return df

def main():
    st.title("NSE F&O and Cash Market Data Analysis")
    
    init_db()
    
    with st.sidebar:
        fo_file = st.file_uploader("Upload F&O Bhavcopy CSV", type=["csv"])
        cash_file = st.file_uploader("Upload Cash Market Bhavcopy CSV", type=["csv"])
    
    if fo_file and cash_file:
        processed_data = load_data(fo_file, cash_file)
    else:
        processed_data = query_db()
    
    # Filters in Sidebar
    with st.sidebar:
        expiry_filter = st.selectbox("Select Expiry Date", ["All"] + list(processed_data["XpryDt"].dropna().unique()))
        sentiment_filter = st.selectbox("Select Sentiment", ["All"] + list(processed_data["Sentiment"].unique()))
        pcr_filter = st.slider("Select PCR Range", min_value=0.0, max_value=1.5, value=(0.0, 1.5))
        deliv_min, deliv_max = processed_data["DELIV_PER"].dropna().min(), processed_data["DELIV_PER"].dropna().max()
        delivery_filter = st.slider("Select Delivery Percentage Range", min_value=float(deliv_min), max_value=float(deliv_max), value=(max(10.0, deliv_min), min(90.0, deliv_max)))
    
    if expiry_filter != "All":
        processed_data = processed_data[processed_data["XpryDt"] == expiry_filter]
    if sentiment_filter != "All":
        processed_data = processed_data[processed_data["Sentiment"] == sentiment_filter]
    processed_data = processed_data[(processed_data["PCR"] >= pcr_filter[0]) & (processed_data["PCR"] <= pcr_filter[1])]
    processed_data = processed_data[(processed_data["DELIV_PER"] >= delivery_filter[0]) & (processed_data["DELIV_PER"] <= delivery_filter[1])]
    
    # Display table only
    st.dataframe(processed_data)

if __name__ == "__main__":
    main()
