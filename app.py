import streamlit as st

try:
    from dhanhq import DhanHQ
    st.write("DhanHQ Import Successful ✅")
except ImportError:
    st.write("❌ DhanHQ Import Failed. Trying manual install...")

    import os
    os.system("pip install dhanhq")

    try:
        from dhanhq import DhanHQ
        st.write("DhanHQ Import Successful After Manual Install ✅")
    except ImportError:
        st.write("❌ DhanHQ Still Not Working. Check Logs.")
