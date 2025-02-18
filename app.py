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
    required_columns = {"SYMBOL": "Ticker"}
    
    # Check for missing columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        st.error(f"CM Bhavcopy file is missing columns: {', '.join(missing_cols)}")
        return None
    
    # Detect columns for delivery percentage calculation
    delivery_qty_col = next((col for col in ["DELIV_QTY", "DELIVERABLE_QTY"] if col in df.columns), None)
    total_qty_col = next((col for col in ["TTL_TRD_QNTY", "TOTAL_TRD_QTY"] if col in df.columns), None)
    
    if "DELIV_PER" not in df.columns and delivery_qty_col and total_qty_col:
        df["DELIV_PER"] = (df[delivery_qty_col].astype(float) / df[total_qty_col].astype(float)) * 100
    elif "DELIV_PER" not in df.columns:
        st.warning("CM Bhavcopy is missing required columns to calculate Delivery Percentage. Skipping calculation.")
        df["DELIV_PER"] = None  # Fill with NaN to allow merging
    
    # Use CLOSE_PRICE as LTP if LAST_PRICE is missing
    if "LAST_PRICE" not in df.columns:
        if "CLOSE_PRICE" in df.columns:
            df["LAST_PRICE"] = df["CLOSE_PRICE"]
        else:
            st.warning("CM Bhavcopy is missing LAST_PRICE and CLOSE_PRICE columns. Skipping LTP calculation.")
            df["LAST_PRICE"] = None
    
    df = df.rename(columns={"SYMBOL": "Ticker", "DELIV_PER": "Delivery_Percentage", "LAST_PRICE": "LTP"})
    df["Delivery_Percentage"] = pd.to_numeric(df["Delivery_Percentage"], errors='coerce').round(2)
    df["LTP"] = pd.to_numeric(df["LTP"], errors='coerce').round(2)
    return df[["Ticker", "LTP", "Delivery_Percentage"]]

def process_fo_bhavcopy(file):
    df = pd.read_csv(file)
    required_columns = {"TckrSymb": "Ticker", "ChngInOpnIntrst": "Change_in_Future_OI", "OpnIntrst": "Future_OI"}
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        st.error(f"FO Bhavcopy file is missing columns: {', '.join(missing_cols)}")
        return None
    df = df.rename(columns=required_columns)
    df["Change_in_Future_OI"] = pd.to_numeric(df["Change_in_Future_OI"], errors='coerce').round(2)
    df["Future_OI"] = pd.to_numeric(df["Future_OI"], errors='coerce').round(2)
    df["PCR"] = df.apply(lambda row: round(row["Future_OI"] / row["Change_in_Future_OI"], 2) if row["Change_in_Future_OI"] > 0 else 0, axis=1)
    return df[["Ticker", "Change_in_Future_OI", "Future_OI", "PCR"]]

if cm_bhavcopy and fo_bhavcopy:
    cm_data = process_cm_bhavcopy(cm_bhavcopy)
    fo_data = process_fo_bhavcopy(fo_bhavcopy)
    
    if cm_data is not None and fo_data is not None:
        # Merge CM and FO Data on Ticker
        merged_data = cm_data.merge(fo_data, on="Ticker", how="left")
        
        # Handle missing values after merging
        merged_data = merged_data.fillna(0)
        
        # Filters for PCR and Delivery Percentage
        pcr_filter = st.sidebar.slider("Select PCR Range", 0.0, 5.0, (0.0, 5.0))
        delivery_filter = st.sidebar.slider("Select Delivery Percentage Range", 0, 100, (0, 100))
        
        filtered_data = merged_data[(merged_data["PCR"] >= pcr_filter[0]) & (merged_data["PCR"] <= pcr_filter[1])]
        filtered_data = filtered_data[(filtered_data["Delivery_Percentage"] >= delivery_filter[0]) & (filtered_data["Delivery_Percentage"] <= delivery_filter[1])]
        
        # Display Processed Data in Table Format
        st.subheader("Filtered Data")
        st.dataframe(filtered_data.style.set_properties(**{"font-size": "16px"}))
    else:
        st.warning("One or both uploaded files have missing required columns. Please check and re-upload.")

