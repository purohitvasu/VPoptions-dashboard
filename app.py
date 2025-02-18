import streamlit as st
import pandas as pd

# Streamlit UI - Must be first command
st.set_page_config(layout="wide", page_title="Options & Futures Dashboard")

# File Upload Section
st.sidebar.subheader("Upload CSV Files")
fo_file = st.sidebar.file_uploader("Upload Futures Data (fo170225.csv)", type=["csv"])
op_file = st.sidebar.file_uploader("Upload Options Data (op170225.csv)", type=["csv"])

@st.cache_data
def load_data(fo_file, op_file):
    if fo_file is not None and op_file is not None:
        fo_df = pd.read_csv(fo_file)
        op_df = pd.read_csv(op_file)
        
        # Data Cleaning
        fo_df = fo_df.rename(columns=str.strip)
        op_df = op_df.rename(columns=str.strip)
        
        fo_df["STOCK"] = fo_df["CONTRACT_D"].str.extract(r'FUTSTK(\w+)')
        op_df["STOCK"] = op_df["CONTRACT_D"].str.extract(r'OPTSTK(\w+)')
        
        # Ensure correct Open Interest Calculation
        op_df["TOTAL_OI"] = op_df["OI_NO_CON"].sum()
        op_df["CHANGE_IN_OI"] = op_df["NET_CHANGE"].sum()
        
        return fo_df, op_df
    else:
        return None, None

fo_df, op_df = load_data(fo_file, op_file)

st.title("📊 Options & Futures Market Dashboard")

if fo_df is not None and op_df is not None:
    # Merge Data for a Single Filter
    common_stocks = set(fo_df["STOCK"].dropna()).intersection(set(op_df["STOCK"].dropna()))
    selected_stock = st.sidebar.selectbox("Select Stock", sorted(common_stocks))
    
    st.subheader("Futures Open Interest")
    filtered_fo = fo_df[fo_df["STOCK"] == selected_stock]
    if not filtered_fo.empty:
        st.write(f"Total Open Interest: {filtered_fo['OI_NO_CON'].sum()}")
        st.write(f"Change in Open Interest: {filtered_fo['OI_NO_CON'].diff().iloc[-1]}")
    else:
        st.warning("No data available for the selected stock.")
    
    st.subheader("Options Open Interest")
    filtered_op = op_df[op_df["STOCK"] == selected_stock]
    if not filtered_op.empty:
        st.write(f"Total Open Interest: {filtered_op['TOTAL_OI'].iloc[0]}")
        st.write(f"Change in Open Interest: {filtered_op['CHANGE_IN_OI'].iloc[0]}")
    else:
        st.warning("No options data available.")
else:
    st.warning("Please upload both Futures and Options CSV files to proceed.")
