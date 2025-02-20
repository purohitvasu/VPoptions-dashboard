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
    "OPEN_PRICE": "Open",
    "HIGH_PRICE": "High",
    "LOW_PRICE": "Low",
    "LAST_PRICE": "Close",
    "DELIV_PER": "Delivery %"
}

# Column Mapping for F&O Bhavcopy CSV
fo_column_mapping = {
    "TckrSymb": "Script Name",
    "OpnIntrst": "Open Interest",
    "ChngInOpnIntrst": "Future OI Change",
    "OptnTp": "Option Type",
    "XpryDt": "Expiry Date",
    "FinInstrmTp": "Instrument Type"
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
            df[col] = df[col].fillna(0)  # Replace NaN with 0
            df[col] = df[col].round(2)  # Round to 2 decimal places
    return df

# Processing Function for Cash Market Data
def process_cash_market(cash_file):
    try:
        # Load Cash Market Data
        cash_df = pd.read_csv(cash_file)
        cash_df = clean_columns(cash_df, cash_column_mapping)

        # Check required columns
        required_cash_cols = ["Script Name", "Open", "High", "Low", "Close", "Delivery %"]
        if not all(col in cash_df.columns for col in required_cash_cols):
            st.error(f"⚠️ Cash Market CSV is missing columns: {set(required_cash_cols) - set(cash_df.columns)}")
            return None

        # Clean numeric values
        cash_df = clean_numeric_data(cash_df, ["Open", "High", "Low", "Close", "Delivery %"])

        # Keep only required columns
        cash_df = cash_df[["Script Name", "Open", "High", "Low", "Close", "Delivery %"]]

        return cash_df

    except Exception as e:
        st.error(f"❌ Error processing Cash Market file: {str(e)}")
        return None

# Processing Function for F&O Bhavcopy Data
def process_fo_bhavcopy(fo_file):
    try:
        # Load F&O Bhavcopy Data
        fo_df = pd.read_csv(fo_file)
        fo_df = clean_columns(fo_df, fo_column_mapping)

        # Ignore StrkPric column if it exists
        if "StrkPric" in fo_df.columns:
            fo_df = fo_df.drop(columns=["StrkPric"])

        # Filter Stock Futures (STF), Index Futures (IDF), and **Stock Options (STO)**
        fo_df = fo_df[fo_df["Instrument Type"].isin(["STF", "IDF", "STO"])]

        # Check required columns
        required_fo_cols = ["Script Name", "Open Interest", "Future OI Change", "Expiry Date", "Option Type"]
        missing_cols = [col for col in required_fo_cols if col not in fo_df.columns]

        if missing_cols:
            st.error(f"⚠️ **F&O CSV is missing columns:** {missing_cols}")
            return None

        # Ensure 'Expiry Date' is of string type
        fo_df["Expiry Date"] = fo_df["Expiry Date"].astype(str)

        # Clean numeric values
        fo_df = clean_numeric_data(fo_df, ["Open Interest", "Future OI Change"])

        # **Calculate Total Call OI and Total Put OI for each Script Name and Expiry Date**
        call_oi = fo_df[fo_df["Option Type"] == "CE"].groupby(["Script Name", "Expiry Date"])["Open Interest"].sum().reset_index()
        put_oi = fo_df[fo_df["Option Type"] == "PE"].groupby(["Script Name", "Expiry Date"])["Open Interest"].sum().reset_index()

        call_oi.rename(columns={"Open Interest": "Total Call OI"}, inplace=True)
        put_oi.rename(columns={"Open Interest": "Total Put OI"}, inplace=True)

        # Merge F&O Data
        fo_final = fo_df.merge(call_oi, on=["Script Name", "Expiry Date"], how="left").merge(put_oi, on=["Script Name", "Expiry Date"], how="left")

        # Ensure all OI values are numeric and fill NaN with 0
        fo_final["Total Call OI"] = fo_final["Total Call OI"].fillna(0).round(2)
        fo_final["Total Put OI"] = fo_final["Total Put OI"].fillna(0).round(2)

        # Calculate PCR (Put-Call Ratio) and handle division errors
        fo_final["PCR"] = np.where(
            fo_final["Total Call OI"] > 0, 
            (fo_final["Total Put OI"] / fo_final["Total Call OI"]).round(2), 
            0
        )

        # Select required columns
        final_df = fo_final[["Script Name", "Expiry Date", "Future OI Change", "Total Call OI", "Total Put OI", "PCR"]]

        return final_df

    except Exception as e:
        st.error(f"❌ Error processing F&O Bhavcopy file: {str(e)}")
        return None

# Process files after upload
cash_df, fo_df = None, None

if cash_file:
    cash_df = process_cash_market(cash_file)

if fo_file:
    fo_df = process_fo_bhavcopy(fo_file)

if cash_df is not None:
    st.success("✅ Cash Market file processed successfully!")

    # Display Cash Market Data
    st.subheader("📊 Cash Market Data")
    st.dataframe(cash_df)

if fo_df is not None:
    st.success("✅ F&O Bhavcopy file processed successfully!")

    # Sidebar Filters for F&O Data
    st.sidebar.header("🔍 F&O Filters")

    # Expiry Date Filter
    expiry_dates = fo_df["Expiry Date"].dropna().unique()
    selected_expiry = st.sidebar.selectbox("📅 Select Expiry Date", ["All"] + list(expiry_dates))
    if selected_expiry != "All":
        fo_df = fo_df[fo_df["Expiry Date"] == selected_expiry]

    # Display F&O Data
    st.subheader("📊 F&O Stock Analysis")
    st.dataframe(fo_df)

else:
    st.warning("⚠️ Please upload both Cash Market & F&O Bhavcopy files.")
