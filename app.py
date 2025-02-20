import streamlit as st
import pandas as pd
import numpy as np

# Streamlit UI
st.title("NSE EOD Data Upload & Analysis")

# File upload widgets
st.sidebar.header("Upload Bhavcopy Files")
cash_file = st.sidebar.file_uploader("Upload Cash Market Bhavcopy (CSV)", type=["csv"])
fo_file = st.sidebar.file_uploader("Upload F&O Bhavcopy (CSV)", type=["csv"])

# Expected column mapping
column_mapping = {
    "symbol": "Script Name",
    "last_price": "Last Traded Price",
    "deliv_per": "Delivery Percentage",
    "open_int": "Total Future OI",
    "chg_in_oi": "Change in Future OI",
    "expiry_dt": "Expiry Date",
    "option_typ": "Option Type",
    "strike_pr": "Strike Price"
}

# Function to clean and rename columns
def clean_columns(df):
    df.columns = df.columns.str.strip().str.lower()  # Remove spaces & convert to lowercase
    df.rename(columns={col: column_mapping[col] for col in df.columns if col in column_mapping}, inplace=True)
    return df

# Function to handle missing or invalid numeric values
def clean_numeric_data(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = df[col].replace(' -', np.nan)  # Replace invalid values with NaN
            df[col] = pd.to_numeric(df[col], errors="coerce")  # Convert to float (NaN for errors)
            df[col] = df[col].fillna(0)  # Replace NaN with 0 or other fallback value
    return df

# Processing Function
def process_files(cash_file, fo_file):
    try:
        # Load Cash Market Data
        cash_df = pd.read_csv(cash_file)
        cash_df = clean_columns(cash_df)

        # Check required columns in Cash Market Data
        required_cash_cols = ["Script Name", "Last Traded Price", "Delivery Percentage"]
        if not all(col in cash_df.columns for col in required_cash_cols):
            st.error(f"⚠️ Cash Market CSV is missing columns: {set(required_cash_cols) - set(cash_df.columns)}")
            st.write("🔍 **Columns found in uploaded file:**", list(cash_df.columns))
            return None

        # Clean numeric values
        cash_df = clean_numeric_data(cash_df, ["Last Traded Price", "Delivery Percentage"])

        # Load F&O Bhavcopy Data
        fo_df = pd.read_csv(fo_file)
        fo_df = clean_columns(fo_df)

        # Check required columns in F&O Bhavcopy Data
        required_fo_cols = ["Script Name", "Total Future OI", "Change in Future OI", "Expiry Date", "Option Type"]
        if not all(col in fo_df.columns for col in required_fo_cols):
            st.error(f"⚠️ F&O CSV is missing columns: {set(required_fo_cols) - set(fo_df.columns)}")
            st.write("🔍 **Columns found in uploaded file:**", list(fo_df.columns))
            return None

        # Clean numeric values
        fo_df = clean_numeric_data(fo_df, ["Total Future OI", "Change in Future OI"])

        # Separate futures and options data
        futures_df = fo_df[fo_df["Option Type"].isna()][["Script Name", "Total Future OI", "Change in Future OI"]]
        options_df = fo_df[fo_df["Option Type"].notna()]

        # Aggregate OI for Calls & Puts
        call_oi = options_df[options_df["Option Type"] == "CE"].groupby("Script Name")["Total Future OI"].sum().reset_index()
        put_oi = options_df[options_df["Option Type"] == "PE"].groupby("Script Name")["Total Future OI"].sum().reset_index()

        call_oi.rename(columns={"Total Future OI": "Total Call OI"}, inplace=True)
        put_oi.rename(columns={"Total Future OI": "Total Put OI"}, inplace=True)

        # Merge F&O Data
        fo_final = futures_df.merge(call_oi, on="Script Name", how="left").merge(put_oi, on="Script Name", how="left")
        fo_final["PCR"] = fo_final["Total Put OI"] / fo_final["Total Call OI"]

        # Merge with Cash Market Data
        final_df = cash_df.merge(fo_final, on="Script Name", how="left")

        return final_df

    except Exception as e:
        st.error(f"❌ Error processing files: {str(e)}")
        return None

# Process files after upload
if cash_file and fo_file:
    df = process_files(cash_file, fo_file)
    if df is not None:
        st.success("✅ Files uploaded & processed successfully!")
        
        # Display merged data
        st.subheader("📊 Processed Data")
        st.dataframe(df)

        # Allow user to download the processed dataset
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Processed Data", csv, "processed_data.csv", "text/csv")
else:
    st.warning("⚠️ Please upload both Cash Market & F&O Bhavcopy files.")
