import streamlit as st
import pandas as pd
import io

# Streamlit UI
st.title("NSE EOD Data Upload & Analysis")

# File upload widgets
st.sidebar.header("Upload Bhavcopy Files")
cash_file = st.sidebar.file_uploader("Upload Cash Market Bhavcopy (CSV)", type=["csv"])
fo_file = st.sidebar.file_uploader("Upload F&O Bhavcopy (CSV)", type=["csv"])

# Processing Function
def process_files(cash_file, fo_file):
    # Load cash market data
    cash_df = pd.read_csv(cash_file)
    cash_df = cash_df[['SYMBOL', 'CLOSE', 'DELIV_PER']]
    cash_df.rename(columns={'SYMBOL': 'Script Name', 'CLOSE': 'Last Traded Price', 'DELIV_PER': 'Delivery Percentage'}, inplace=True)
    cash_df['Delivery Percentage'] = cash_df['Delivery Percentage'].astype(float)

    # Load F&O data
    fo_df = pd.read_csv(fo_file)
    fo_df = fo_df[['SYMBOL', 'EXPIRY_DT', 'OPEN_INT', 'CHG_IN_OI', 'OPTION_TYP', 'STRIKE_PR']]
    fo_df.rename(columns={'SYMBOL': 'Script Name', 'OPEN_INT': 'Total Future OI', 'CHG_IN_OI': 'Change in Future OI'}, inplace=True)

    # Separate futures and options data
    futures_df = fo_df[fo_df['OPTION_TYP'].isna()][['Script Name', 'Total Future OI', 'Change in Future OI']]
    options_df = fo_df[fo_df['OPTION_TYP'].notna()]

    # Aggregate OI for Calls & Puts
    call_oi = options_df[options_df['OPTION_TYP'] == 'CE'].groupby("Script Name")["Total Future OI"].sum().reset_index()
    put_oi = options_df[options_df['OPTION_TYP'] == 'PE'].groupby("Script Name")["Total Future OI"].sum().reset_index()

    call_oi.rename(columns={"Total Future OI": "Total Call OI"}, inplace=True)
    put_oi.rename(columns={"Total Future OI": "Total Put OI"}, inplace=True)

    # Merge F&O Data
    fo_final = futures_df.merge(call_oi, on="Script Name", how="left").merge(put_oi, on="Script Name", how="left")
    fo_final["PCR"] = fo_final["Total Put OI"] / fo_final["Total Call OI"]

    # Merge with cash market data
    final_df = cash_df.merge(fo_final, on="Script Name", how="left")

    return final_df

# Process files after upload
if cash_file and fo_file:
    df = process_files(cash_file, fo_file)
    st.success("Files uploaded & processed successfully!")
    
    # Display merged data
    st.subheader("Processed Data")
    st.dataframe(df)

    # Allow user to download processed data
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Processed Data", csv, "processed_data.csv", "text/csv")
else:
    st.warning("Please upload both Cash Market & F&O Bhavcopy files.")

