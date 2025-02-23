import streamlit as st

# Google Drive Public URL for the HTML report
report_url = "https://drive.google.com/uc?id="1Fq_swEdR0dSg0UJpsb-JLpourvU7kWVy"

st.markdown(
    f'<a href="{report_url}" target="_blank" style="text-decoration:none;">'
    f'<button style="padding:10px 20px; font-size:16px;">📥 Download Latest Report</button>'
    f'</a>',
    unsafe_allow_html=True
)
