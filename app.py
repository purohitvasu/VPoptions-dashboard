import streamlit as st
import pandas as pd
import plotly.express as px

# Streamlit UI - Must be first command
st.set_page_config(layout="wide", page_title="Options & Futures Dashboard")

# File Upload Section
st.sidebar.subheader("Upload NSE Bhavcopy Data")
bhavcopy_file = st.sidebar.file_uploader("Upload NSE Bhavcopy Data", type=["csv"])

@st.cache_data
def load_data(bhavcopy_file):
    if bhavcopy_file is not None:
        bhavcopy_df = pd.read_csv(bhavcopy_file)
        
        # Data Cleaning
        bhavcopy_df = bhavcopy_df.rename(columns=str.strip)
        
        # Processing Bhavcopy Data
        bhavcopy_df = bhavcopy_df[["TradDt", "TckrSymb", "XpryDt", "OpnPric", "HghPric", "LwPric", "ClsPric", "OpnIntrst", "ChngInOpnIntrst"]]
        bhavcopy_df = bhavcopy_df.rename(columns={
            "TradDt": "Date", "TckrSymb": "Stock", "XpryDt": "Expiry",
            "OpnPric": "Open", "HghPric": "High", "LwPric": "Low", "ClsPric": "Close",
            "OpnIntrst": "Total_OI", "ChngInOpnIntrst": "Change_in_OI"
        })
        bhavcopy_df["Date"] = pd.to_datetime(bhavcopy_df["Date"])
        bhavcopy_df["Expiry"] = pd.to_datetime(bhavcopy_df["Expiry"])
        
        return bhavcopy_df
    else:
        return None

bhavcopy_df = load_data(bhavcopy_file)

st.title("📊 Options & Futures Market Dashboard")

if bhavcopy_df is not None:
    # Stock Filter
    stock_list = sorted(bhavcopy_df["Stock"].unique())
    selected_stock = st.sidebar.selectbox("Select Stock", stock_list)
    
    # Stock Details
    st.subheader("Stock Details: Open, High, Low, Close")
    stock_data = bhavcopy_df[bhavcopy_df["Stock"] == selected_stock][["Date", "Open", "High", "Low", "Close"]]
    st.dataframe(stock_data)
    
    # Futures Data - Expiry Wise
    st.subheader("Futures Open Interest - Expiry Wise")
    futures_data = bhavcopy_df[(bhavcopy_df["Stock"] == selected_stock)].groupby("Expiry")["Total_OI", "Change_in_OI"].sum().reset_index()
    st.dataframe(futures_data)
    
    # Options Data - Expiry Wise
    st.subheader("Options Open Interest - Expiry Wise")
    options_data = bhavcopy_df[(bhavcopy_df["Stock"] == selected_stock)].groupby(["Expiry", "Stock"])["Total_OI", "Change_in_OI"].sum().reset_index()
    st.dataframe(options_data)
    
    # Support & Resistance Based on OI
    st.subheader("Support & Resistance Levels")
    ce_data = bhavcopy_df[(bhavcopy_df["Stock"] == selected_stock) & (bhavcopy_df["Total_OI"] > 0)]
    pe_data = bhavcopy_df[(bhavcopy_df["Stock"] == selected_stock) & (bhavcopy_df["Total_OI"] > 0)]
    
    if not ce_data.empty and not pe_data.empty:
        max_ce_oi = ce_data.loc[ce_data["Total_OI"].idxmax(), "Close"]
        max_pe_oi = pe_data.loc[pe_data["Total_OI"].idxmax(), "Close"]
        st.write(f"🔹 Resistance Level (Max CE OI): {max_ce_oi}")
        st.write(f"🔹 Support Level (Max PE OI): {max_pe_oi}")
    else:
        st.warning("Not enough OI data to determine Support & Resistance levels.")
else:
    st.warning("Please upload NSE Bhavcopy data to proceed.")
