import streamlit as st
import pandas as pd
import numpy as np

# Streamlit UI
st.title("NSE EOD Data Upload & Analysis")

# File upload widgets
st.sidebar.header("Upload Bhavcopy Files")
cash_file = st.sidebar.file_uploader("Upload Cash Market Bhavcopy (CSV)", type=["csv"])
fo_file = st.sidebar.file_uploader("Upload F&O Bhavcopy (CSV)", type=["csv"])

# Column Mapping for Cash Market CSV
cash_column_mapping = {
    "SYMBOL": "Script Name",
    "LAST_PRICE": "Last Traded Price",
    "DELIV_PER": "Delivery Percentage"
}

# Column Mapping for F&O Bhavcopy CSV
fo_column_mapping = {
    "TckrSymb": "Script Name",
    "OpnIntrst": "Total Future OI",
    "ChngInOpnIntrst": "Change in Future OI",
    "OptnTp": "Option Type",
    "XpryDt": "Expiry Date"
}

# Function to clean and rename columns
def clean_columns(df, column_mapping):
    df.columns = df.columns.str.strip()  # Remove leading/trailing spaces
    df.rename(columns={col: column_mapping[col] for col in df.columns if col in column_mapping}, inplace=True)
    return df

# Function to handle missing or invalid numeric values
def clean_numeric_data(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = df[col].replace(' -', np.nan)  # Replace invalid values with NaN
            df[col] = pd.to_numeric(df[col], errors="coerce")  # Convert to float (NaN for errors)
            df[col] = df[col].fillna(0)  # Replace NaN with 0 or another fallback value
    return df

# Processing Function
def process_files(cash_file, fo_file):
    try:
        # Load Cash Market Data
        cash_df = pd.read_csv(cash_file)
        cash_df = clean_columns(cash_df, cash_column_mapping)

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
        fo_df = clean_columns(fo_df, fo_column_mapping)

        # Debugging: Print actual column names
        st.write("✅ **Columns in uploaded F&O CSV:**", list(fo_df.columns))

        # Check required columns in F&O Bhavcopy Data
        required_fo_cols = ["Script Name", "Total Future OI", "Change in Future OI", "Expiry Date", "Option Type"]
        missing_cols = [col for col in required_fo_cols if col not in fo_df.columns]

        if missing_cols:
            st.error(f"⚠️ **F&O CSV is missing columns:** {missing_cols}")
            return None

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
