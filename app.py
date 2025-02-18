import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Streamlit UI - Must be first command
st.set_page_config(layout="wide", page_title="Options & Futures Dashboard")

# File Upload Section
st.sidebar.subheader("Upload NSE Bhavcopy Data")
fo_bhavcopy_file = st.sidebar.file_uploader("Upload NSE FO Bhavcopy Data", type=["csv"])
cm_bhavcopy_file = st.sidebar.file_uploader("Upload NSE CM Bhavcopy Data", type=["csv"])

@st.cache_data
def load_data(file):
    if file is not None:
        try:
            df = pd.read_csv(file)
            df = df.rename(columns=str.strip)
            return df
        except Exception as e:
            st.error(f"Error processing file: {e}")
            return None
    return None

fo_bhavcopy_df = load_data(fo_bhavcopy_file)
cm_bhavcopy_df = load_data(cm_bhavcopy_file)

st.title("📊 Options & Futures Market Dashboard")

if fo_bhavcopy_df is not None and cm_bhavcopy_df is not None:
    # Expiry Filter
    expiry_list = sorted(fo_bhavcopy_df["XpryDt"].dropna().unique())
    if expiry_list:
        selected_expiry = st.sidebar.selectbox("Select Expiry", expiry_list, format_func=lambda x: pd.to_datetime(x).strftime('%Y-%m-%d'))
    else:
        st.warning("No valid expiry dates found in the uploaded FO Bhavcopy file.")
        st.stop()
    
    # Filter FO data based on selected expiry
    fo_expiry_data = fo_bhavcopy_df[fo_bhavcopy_df["XpryDt"] == selected_expiry]
    
    # Merge FO and CM Data on Stock Name
    cm_bhavcopy_df = cm_bhavcopy_df.rename(columns={"SYMBOL": "Stock", "DELIV_PER": "Delivery_Percentage"})
    summary_table = fo_expiry_data.groupby("TckrSymb").agg(
        LTP=("ClsPric", "last"),
        Future_OI=("OpnIntrst", "sum"),
        Change_in_Future_OI=("ChngInOpnIntrst", "sum"),
        Total_Call_OI=("OpnIntrst", lambda x: x[fo_expiry_data["OptnTp"] == "CE"].sum()),
        Total_Put_OI=("OpnIntrst", lambda x: x[fo_expiry_data["OptnTp"] == "PE"].sum()),
    ).reset_index()
    
    # Merge with Delivery Data
    summary_table = summary_table.merge(cm_bhavcopy_df[["Stock", "Delivery_Percentage"]], left_on="TckrSymb", right_on="Stock", how="left").drop(columns=["Stock"])
    
    # Calculate PCR with 2 decimal places
    summary_table["PCR"] = (summary_table["Total_Put_OI"] / summary_table["Total_Call_OI"]).round(2)
    
    # Add Delivery Percentage Filter
    delivery_filter = st.sidebar.slider("Select Delivery Percentage Range", 0, 100, (0, 100))
    summary_table = summary_table[(summary_table["Delivery_Percentage"] >= delivery_filter[0]) & (summary_table["Delivery_Percentage"] <= delivery_filter[1])]
    
    # Display Enhanced Table with Visualization
    st.subheader(f"Stock Data for Expiry: {pd.to_datetime(selected_expiry).date()}")
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(summary_table.columns),
                    fill_color='#1f77b4',
                    font=dict(color='white', size=14),
                    align='center'),
        cells=dict(values=[summary_table[col] for col in summary_table.columns],
                   fill_color=['#f5f5f5', '#ffffff'],
                   align='center'))
    ])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Please upload both FO and CM Bhavcopy files to proceed.")
