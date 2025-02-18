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
        return fo_df, op_df
    else:
        return None, None

fo_df, op_df = load_data(fo_file, op_file)

st.title("📊 Options & Futures Market Dashboard")

if fo_df is not None and op_df is not None:
    # Sidebar Filters
    st.sidebar.header("Filters")
    selected_contract = st.sidebar.selectbox("Select Contract", fo_df["CONTRACT_D"].unique())
    
    st.subheader("Futures Open Interest")
    filtered_fo = fo_df[fo_df["CONTRACT_D"] == selected_contract]
    if not filtered_fo.empty:
        st.write(f"Total Open Interest: {filtered_fo['OI_NO_CON'].sum()}")
        st.write(f"Change in Open Interest: {filtered_fo['OI_NO_CON'].diff().iloc[-1]}")
    else:
        st.warning("No data available for the selected contract.")
    
    st.subheader("Options Open Interest")
    try:
        selected_stock = selected_contract.split("FUTSTK")[1].split("-")[0]
        filtered_op = op_df[op_df["CONTRACT_D"].str.contains(selected_stock, na=False)]
        if not filtered_op.empty:
            st.write(f"Total Open Interest: {filtered_op['OI_NO_CON'].sum()}")
            st.write(f"Change in Open Interest: {filtered_op['OI_NO_CON'].diff().iloc[-1]}")
        else:
            st.warning("No options data available.")
    except IndexError:
        st.warning("Could not extract stock name from contract. Please check data format.")
else:
    st.warning("Please upload both Futures and Options CSV files to proceed.")
