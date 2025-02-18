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
    # Expiry Filter
    expiry_list = sorted(bhavcopy_df["Expiry"].dropna().unique())
    if expiry_list:
        selected_expiry = st.sidebar.selectbox("Select Expiry", expiry_list, format_func=lambda x: x.strftime('%Y-%m-%d'))
    else:
        st.warning("No valid expiry dates found in the uploaded file.")
        st.stop()
    
    # Stock Filter
    stock_list = sorted(bhavcopy_df[bhavcopy_df["Expiry"] == selected_expiry]["Stock"].dropna().unique())
    if stock_list:
        selected_stock = st.sidebar.selectbox("Select Stock", stock_list)
    else:
        st.warning("No valid stock data found for the selected expiry.")
        st.stop()
    
    bhavcopy_df = bhavcopy_df[bhavcopy_df["Expiry"] == selected_expiry]
    
    # Stock Details (Futures OHLC only)
    st.subheader(f"Stock Details: Futures Open, High, Low, Close (Expiry: {selected_expiry.date()})")
    stock_data = bhavcopy_df[(bhavcopy_df["Stock"] == selected_stock) & (bhavcopy_df["Option_Type"].isna())][["Date", "Open", "High", "Low", "Close"]]
    if stock_data.empty:
        st.warning("No futures data available for this stock.")
    else:
        st.dataframe(stock_data.style.format({"Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}"}))
    
    # Futures Data - Expiry Wise
    st.subheader("Futures Open Interest - Selected Expiry")
    futures_data = bhavcopy_df[(bhavcopy_df["Stock"] == selected_stock) & (bhavcopy_df["Option_Type"].isna())].groupby("Expiry")[["Total_OI", "Change_in_OI"]].sum().reset_index()
    if futures_data.empty:
        st.warning("No futures open interest data available.")
    else:
        st.dataframe(futures_data)
    
    # Options Data - Expiry Wise
    st.subheader("Options Open Interest - Selected Expiry")
    options_data = bhavcopy_df[(bhavcopy_df["Stock"] == selected_stock) & (~bhavcopy_df["Option_Type"].isna())].groupby(["Expiry", "Strike_Price", "Option_Type"])[["Total_OI", "Change_in_OI"]].sum().reset_index()
    if options_data.empty:
        st.warning("No options open interest data available.")
    else:
        st.dataframe(options_data)
    
    # Support & Resistance Based on OI
    st.subheader("Support & Resistance Levels")
    if not options_data.empty:
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
        st.warning("Options data is empty.")
else:
    st.warning("Please upload a valid NSE Bhavcopy file to proceed.")
