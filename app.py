import streamlit as st
import pandas as pd

# Streamlit UI - Must be first command
st.set_page_config(layout="wide", page_title="Options & Futures Dashboard")

st.title("📊 Options & Futures Market Dashboard")

# File Uploads for CM Bhav Copy and FO Bhav Copy
st.sidebar.subheader("Upload Files")
cm_bhavcopy = st.sidebar.file_uploader("Upload CM Bhav Copy", type=["csv"])
fo_bhavcopy = st.sidebar.file_uploader("Upload FO Bhav Copy", type=["csv"])

# Process the uploaded files
def process_cm_bhavcopy(file):
    df = pd.read_csv(file)
    required_columns = {"SYMBOL": "Ticker", "DELIV_PER": "Delivery_Percentage", "LAST_PRICE": "LTP"}
    
    # Rename available columns
    df = df.rename(columns={k: v for k, v in required_columns.items() if k in df.columns})
    
    # Convert available numeric columns
    if "Delivery_Percentage" in df.columns:
        df["Delivery_Percentage"] = pd.to_numeric(df["Delivery_Percentage"], errors='coerce').round(2)
    else:
        df["Delivery_Percentage"] = None  # Fill with NaN if missing
    
    if "LTP" in df.columns:
        df["LTP"] = pd.to_numeric(df["LTP"], errors='coerce').round(2)
    else:
        df["LTP"] = None  # Fill with NaN if missing
    
    return df[[col for col in ["Ticker", "LTP", "Delivery_Percentage"] if col in df.columns]]

def process_fo_bhavcopy(file):
    df = pd.read_csv(file)
    required_columns = {"TckrSymb": "Ticker", "ChngInOpnIntrst": "Change_in_Future_OI", "OpnIntrst": "Future_OI", "XpryDt": "Expiry", "OptnTp": "Option_Type"}
    
    # Rename available columns
    df = df.rename(columns={k: v for k, v in required_columns.items() if k in df.columns})
    
    # Convert available numeric columns
    if "Change_in_Future_OI" in df.columns:
        df["Change_in_Future_OI"] = pd.to_numeric(df["Change_in_Future_OI"], errors='coerce').round(2)
    
    if "Future_OI" in df.columns:
        df["Future_OI"] = pd.to_numeric(df["Future_OI"], errors='coerce').round(2)
    
    if "Expiry" in df.columns:
        df["Expiry"] = pd.to_datetime(df["Expiry"], errors='coerce')
    
    # Calculate total call OI and total put OI
    if "Option_Type" in df.columns:
        total_call_oi = df[df["Option_Type"] == "CE"].groupby("Ticker")["Future_OI"].sum().rename("Total_Call_OI")
        total_put_oi = df[df["Option_Type"] == "PE"].groupby("Ticker")["Future_OI"].sum().rename("Total_Put_OI")
        df = df.merge(total_call_oi, on="Ticker", how="left").merge(total_put_oi, on="Ticker", how="left")
        df["PCR"] = (df["Total_Put_OI"] / df["Total_Call_OI"]).round(2)
    
    return df[[col for col in ["Ticker", "Expiry", "Change_in_Future_OI", "Future_OI", "Total_Call_OI", "Total_Put_OI", "PCR"] if col in df.columns]]

if cm_bhavcopy and fo_bhavcopy:
    cm_data = process_cm_bhavcopy(cm_bhavcopy)
    fo_data = process_fo_bhavcopy(fo_bhavcopy)
    
    if cm_data is not None and fo_data is not None:
        # Expiry Filter
        expiry_list = sorted(fo_data["Expiry"].dropna().unique()) if "Expiry" in fo_data.columns else []
        selected_expiry = st.sidebar.selectbox("Select Expiry", expiry_list, format_func=lambda x: x.strftime('%Y-%m-%d')) if expiry_list else None
        
        if selected_expiry is not None:
            fo_data = fo_data[fo_data["Expiry"] == selected_expiry]
        
        # Merge CM and FO Data on Ticker
        merged_data = cm_data.merge(fo_data, on="Ticker", how="left")
        
        # Handle missing values after merging
        merged_data = merged_data.fillna(0)
        
        # Filters for PCR and Delivery Percentage
        pcr_filter = st.sidebar.slider("Select PCR Range", 0.0, 5.0, (0.0, 5.0))
        delivery_filter = st.sidebar.slider("Select Delivery Percentage Range", 0, 100, (0, 100))
        
        if "PCR" in merged_data.columns:
            filtered_data = merged_data[(merged_data["PCR"] >= pcr_filter[0]) & (merged_data["PCR"] <= pcr_filter[1])]
        else:
            filtered_data = merged_data.copy()
        
        if "Delivery_Percentage" in filtered_data.columns:
            filtered_data = filtered_data[(filtered_data["Delivery_Percentage"] >= delivery_filter[0]) & (filtered_data["Delivery_Percentage"] <= delivery_filter[1])]
        
        # Display Processed Data in Table Format
        st.subheader("Filtered Data")
        st.dataframe(filtered_data.style.set_properties(**{"font-size": "16px"}))
    else:
        st.warning("One or both uploaded files have missing required columns. Processing available data.")

