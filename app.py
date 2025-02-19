import streamlit as st
import os
from dhanhq import DhanHQ

# Fetch API credentials from Streamlit secrets
ACCESS_TOKEN = st.secrets["DHAN_ACCESS_TOKEN"]

# Initialize Dhan API client
dhan = DhanHQ(ACCESS_TOKEN)

# Test API Connection
st.write("Dhan API Connected ✅")
