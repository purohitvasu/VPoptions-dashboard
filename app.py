import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
                                "OpnIntrst": "Total_OI", "ChngInOpnIntrst": "Change_in_OI", "OptnTp": "Option_Type", "StrkPric": "Strike_Price", "FinInstrmTp": "Instrument_Type"}
            
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
    
    # Filter data based on selected expiry
    expiry_data = bhavcopy_df[bhavcopy_df["Expiry"] == selected_expiry]
    
    # Aggregate Data for Table
    summary_table = expiry_data.groupby("Stock").agg(
        LTP=("Close", lambda x: x[expiry_data["Instrument_Type"] == "STF"].iloc[-1] if not x[expiry_data["Instrument_Type"] == "STF"].empty else x.iloc[-1]),
        Future_OI=("Total_OI", "sum"),
        Change_in_Future_OI=("Change_in_OI", "sum"),
        Total_Call_OI=("Total_OI", lambda x: x[expiry_data["Option_Type"] == "CE"].sum()),
        Total_Put_OI=("Total_OI", lambda x: x[expiry_data["Option_Type"] == "PE"].sum()),
    ).reset_index()
    
    # Calculate PCR with 2 decimal places
    summary_table["PCR"] = (summary_table["Total_Put_OI"] / summary_table["Total_Call_OI"]).round(2)
    
    # Support & Resistance Based on OI
    def get_max_oi_strike(data, option_type):
        filtered_data = data[data["Option_Type"] == option_type]
        if not filtered_data.empty:
            return filtered_data.loc[filtered_data["Total_OI"].idxmax(), "Strike_Price"]
        return None
    
    summary_table["Support"] = summary_table["Stock"].apply(lambda x: get_max_oi_strike(expiry_data[expiry_data["Stock"] == x], "PE"))
    summary_table["Resistance"] = summary_table["Stock"].apply(lambda x: get_max_oi_strike(expiry_data[expiry_data["Stock"] == x], "CE"))
    
    # Add Future OI Change Filter
    future_oi_change_filter = st.sidebar.slider("Select Change in Future OI Range", int(summary_table["Change_in_Future_OI"].min()), int(summary_table["Change_in_Future_OI"].max()), (int(summary_table["Change_in_Future_OI"].min()), int(summary_table["Change_in_Future_OI"].max())))
    summary_table = summary_table[(summary_table["Change_in_Future_OI"] >= future_oi_change_filter[0]) & (summary_table["Change_in_Future_OI"] <= future_oi_change_filter[1])]
    
    # Display Enhanced Table with Visualization
    st.subheader(f"Stock Data for Expiry: {selected_expiry.date()}")
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
    st.warning("Please upload a valid NSE Bhavcopy file to proceed.")
