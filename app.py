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

# Read and merge all stored CSV files
def load_and_merge_data(directory):
    all_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".csv")]
    data_frames = []
    
    for file in all_files:
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip()  # Remove leading/trailing spaces
        
        # Extract date from filename (assuming format includes YYYYMMDD)
        date_str = "".join(filter(str.isdigit, os.path.basename(file)))  # Extract numbers from filename
        df["Date"] = pd.to_datetime(date_str, format="%Y%m%d", errors="coerce")
        data_frames.append(df)
    
    # Combine all files into a single DataFrame
    if data_frames:
        merged_df = pd.concat(data_frames, ignore_index=True)
        return merged_df
    else:
        return None

# Load merged data
merged_data = load_and_merge_data(STORAGE_DIR)
if merged_data is not None:
    st.write("### Merged Data Preview:")
    st.write(merged_data.head())
else:
    st.warning("No data available. Please upload CSV files.")

# Display list of stored files
stored_files = os.listdir(STORAGE_DIR)
if stored_files:
    st.write("### Stored Files:")
    st.write(stored_files)
