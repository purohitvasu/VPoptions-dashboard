import streamlit as st

# Google Drive Public URL (Corrected)
file_id = "1Fq_swEdR0dSg0UJpsb-JLpourvU7kWVy"
report_url = f"https://drive.google.com/uc?id={file_id}"

# Display Download Button in Streamlit
st.markdown(
    f'<a href="{report_url}" target="_blank" style="text-decoration:none;">'
    f'<button style="padding:10px 20px; font-size:16px;">📥 Download Latest Report</button>'
    f'</a>',
    unsafe_allow_html=True
)
