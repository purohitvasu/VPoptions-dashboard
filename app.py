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
        try:
            bhavcopy_df = pd.read_csv(bhavcopy_file)
            
            # Data Cleaning
            bhavcopy_df = bhavcopy_df.rename(columns=str.strip)
            
            # Ensure required columns exist
            required_columns = {"TradDt": "Date", "TckrSymb": "Stock", "XpryDt": "Expiry",
                                "OpnPric": "Open", "HghPric": "High", "LwPric": "Low", "ClsPric": "Close",
                                "OpnIntrst": "Total_OI", "ChngInOpnIntrst": "Change_in_OI", "OptnTp": "Option_Type", "StrkPric": "Strike_Price"}
            
            missing_columns = [col for col in required_columns.keys() if col not in bhavcopy_df.columns]
            if missing_columns:
                st.error(f"Missing required columns: {', '.join(missing_columns)}")
                return None
            
            bhavcopy_df = bhavcopy_df.rename(columns=required_columns)
            bhavcopy_df["Date"] = pd.to_datetime(bhavcopy_df["Date"], errors='coerce')
            bhavcopy_df["Expiry"] = pd.to_datetime(bhavcopy_df["Expiry"], errors='coerce')
            
            # Filter valid data
            bhavcopy_df = bhavcopy_df.dropna(subset=["Stock", "Expiry", "Total_OI", "Change_in_OI"])
            
            return bhavcopy_df
        except Exception as e:
            st.error(f"Error processing file: {e}")
            return None
    else:
        return None

bhavcopy_df = load_data(bhavcopy_file)

st.title("📊 Options & Futures Market Dashboard")

if bhavcopy_df is not None and not bhavcopy_df.empty:
    # Stock Filter
    stock_list = sorted(bhavcopy_df["Stock"].dropna().unique())
    if stock_list:
        selected_stock = st.sidebar.selectbox("Select Stock", stock_list)
    else:
        st.warning("No valid stock data found in the uploaded file.")
        st.stop()
    
    # Stock Details
    st.subheader("Stock Details: Open, High, Low, Close")
    stock_data = bhavcopy_df[bhavcopy_df["Stock"] == selected_stock][["Date", "Open", "High", "Low", "Close"]]
    st.dataframe(stock_data)
    
    # Futures Data - Expiry Wise
    st.subheader("Futures Open Interest - Expiry Wise")
    futures_data = bhavcopy_df[(bhavcopy_df["Stock"] == selected_stock) & (bhavcopy_df["Option_Type"].isna())].groupby("Expiry")["Total_OI", "Change_in_OI"].sum().reset_index()
    st.dataframe(futures_data)
    
    # Options Data - Expiry Wise
    st.subheader("Options Open Interest - Expiry Wise")
    options_data = bhavcopy_df[(bhavcopy_df["Stock"] == selected_stock) & (~bhavcopy_df["Option_Type"].isna())].groupby(["Expiry", "Strike_Price", "Option_Type"])["Total_OI", "Change_in_OI"].sum().reset_index()
    st.dataframe(options_data)
    
    # Support & Resistance Based on OI
    st.subheader("Support & Resistance Levels")
    ce_data = options_data[options_data["Option_Type"] == "CE"]
    pe_data = options_data[options_data["Option_Type"] == "PE"]
    
    if not ce_data.empty and not pe_data.empty:
        max_ce_oi = ce_data.loc[ce_data["Total_OI"].idxmax(), "Strike_Price"]
        max_pe_oi = pe_data.loc[pe_data["Total_OI"].idxmax(), "Strike_Price"]
        st.write(f"🔹 Resistance Level (Max CE OI): {max_ce_oi}")
        st.write(f"🔹 Support Level (Max PE OI): {max_pe_oi}")
    else:
        st.warning("Not enough OI data to determine Support & Resistance levels.")
else:
    st.warning("Please upload a valid NSE Bhavcopy file to proceed.")
