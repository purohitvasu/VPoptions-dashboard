import streamlit as st
import pandas as pd
import os

# Define storage directory
STORAGE_DIR = "uploaded_data"
os.makedirs(STORAGE_DIR, exist_ok=True)

# Streamlit file uploader
st.title("NSE Bhavcopy Upload & Storage")
uploaded_files = st.file_uploader("Upload NSE Bhavcopy Files", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        file_path = os.path.join(STORAGE_DIR, uploaded_file.name)
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"File saved: {uploaded_file.name}")
        
        # Read CSV and clean column names
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()  # Remove leading/trailing spaces
        
        # Display columns to check missing ones
        st.write("Columns in uploaded file:", df.columns.tolist())
        
        # Proceed without checking for specific columns
        st.success("File successfully loaded!")

# Display list of stored files
stored_files = os.listdir(STORAGE_DIR)
if stored_files:
    st.write("### Stored Files:")
    st.write(stored_files)
