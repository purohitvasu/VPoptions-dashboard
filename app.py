import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
    
    tab1, tab2, tab3, tab4 = st.tabs(["Futures Data", "Options Chain", "Open Interest", "Market Insights"])
    
    with tab1:
        st.subheader("Futures Data")
        filtered_fo = fo_df[fo_df["CONTRACT_D"] == selected_contract]
        if not filtered_fo.empty:
            fig_futures = go.Figure()
            fig_futures.add_trace(go.Candlestick(
                x=filtered_fo.index,
                open=filtered_fo["OPEN_PRICE"],
                high=filtered_fo["HIGH_PRICE"],
                low=filtered_fo["LOW_PRICE"],
                close=filtered_fo["CLOSE_PRIC"],
                name="Candlestick"
            ))
            fig_futures.update_layout(title=f"Futures Price Movement - {selected_contract}")
            st.plotly_chart(fig_futures, use_container_width=True)
        else:
            st.warning("No data available for the selected contract.")
    
    with tab2:
        st.subheader("Options Chain")
        try:
            selected_stock = selected_contract.split("FUTSTK")[1].split("-")[0]
            filtered_op = op_df[op_df["CONTRACT_D"].str.contains(selected_stock, na=False)]
            st.dataframe(filtered_op[["CONTRACT_D", "OPEN_PRICE", "HIGH_PRICE", "LOW_PRICE", "CLOSE_PRIC", "OI_NO_CON"]])
        except IndexError:
            st.warning("Could not extract stock name from contract. Please check data format.")
    
    with tab3:
        st.subheader("Open Interest Analysis")
        if not filtered_op.empty:
            oi_chart = px.bar(filtered_op, x="CONTRACT_D", y="OI_NO_CON", title="Open Interest by Strike Price")
            st.plotly_chart(oi_chart, use_container_width=True)
        else:
            st.warning("No options data available for Open Interest analysis.")
    
    with tab4:
        st.subheader("Market Insights")
        if not filtered_op.empty:
            summary_metrics = {
                "Total Contracts": len(filtered_op),
                "Highest OI": filtered_op["OI_NO_CON"].max(),
                "Most Traded": filtered_op["TRADED_QUA"].max() if "TRADED_QUA" in filtered_op.columns else "N/A"
            }
            st.write(summary_metrics)
        else:
            st.warning("No market insights available due to lack of data.")
else:
    st.warning("Please upload both Futures and Options CSV files to proceed.")
