import streamlit as st
import pandas as pd
import os

# Define storage file for maintaining the rolling dataset
DATA_FILE = "historical_data.csv"

# Load hardcoded initial 13 days of data (Replace with your actual dataset)
def load_initial_data():
    data = pd.DataFrame({
        "Date": pd.date_range(start="2024-02-01", periods=13, freq='D'),
        "TckrSymb": ["STOCK1", "STOCK2", "STOCK3"] * 13,
        "LTP": [100 + i for i in range(39)],
        "Delivery_Percentage": [30 + (i % 5) for i in range(39)],
        "Future_OI": [5000 + i*10 for i in range(39)],
        "Future_OI_Change": [50 + i for i in range(39)],
        "Total_Call_OI": [2000 + i*5 for i in range(39)],
        "Total_Put_OI": [2500 + i*7 for i in range(39)],
    })
    data["PCR"] = data["Total_Put_OI"] / data["Total_Call_OI"]
    return data

# Load or initialize data
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, parse_dates=["Date"])
    else:
        initial_data = load_initial_data()
        initial_data.to_csv(DATA_FILE, index=False)
        return initial_data

# Store new data while maintaining a rolling 15-day limit
def update_data(new_data):
    existing_data = load_data()
    combined_data = pd.concat([existing_data, new_data]).drop_duplicates()
    combined_data = combined_data.sort_values(by="Date", ascending=False).head(15)  # Keep last 15 days
    combined_data.to_csv(DATA_FILE, index=False)
    return combined_data

# Streamlit UI
st.title("NSE F&O and Cash Market Analysis")

data = load_data()

# Date selection filter
date_selection = st.selectbox("Select Date", sorted(data["Date"].unique(), reverse=True))
filtered_data = data[data["Date"] == date_selection]
st.dataframe(filtered_data)

# File uploader for daily data updates
uploaded_file = st.file_uploader("Upload daily data CSV", type=["csv"])
if uploaded_file:
    new_data = pd.read_csv(uploaded_file, parse_dates=["Date"])
    data = update_data(new_data)
    st.success("Data updated successfully!")
    st.experimental_rerun()
