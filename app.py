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
    return df

def process_fo_bhavcopy(file):
    df = pd.read_csv(file)
    return df

if cm_bhavcopy and fo_bhavcopy:
    cm_data = process_cm_bhavcopy(cm_bhavcopy)
    fo_data = process_fo_bhavcopy(fo_bhavcopy)
    
    st.subheader("CM Bhav Copy Data Preview")
    st.dataframe(cm_data.head())
    
    st.subheader("FO Bhav Copy Data Preview")
    st.dataframe(fo_data.head())

    # Merge CM and FO Data on Symbol
    merged_data = cm_data.merge(fo_data, on="SYMBOL", how="left")
    
    # Display Processed Data
    st.subheader("Merged Data Preview")
    st.dataframe(merged_data.head())

