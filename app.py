import pandas as pd
import streamlit as st
st.set_page_config(
page_title="RCM Compliance Intelligence Engine", page_icon="📊", layout="wide"
)
st.markdown(
"""
<style>
.main {
background-color: #000000;
color: #FFFFFF;
}
h1, h2, h3 {
color: #FF8200 !important;
}
.stMetric {
background-color: #111111;
padding: 15px;
border-radius: 5px;
border-left: 5px solid #FF8200;
}
</style>
""",
unsafe_allow_html=True,
)
st.title("RCM Compliance & Work-Queue Intelligence Engine")
st.markdown(
"Educational Portfolio Artifact: No-PHI administrative workflow and data quality simulation."
)
@st.cache_data
def load_data():
data = {
"Case_ID": ["PAUTH-046", "PAUTH-047", "PAUTH-048", "PAUTH-049", "PAUTH-050"],
"Status": ["Approved", "Closed", "Escalated", "Pending Review", "Appeal Readiness"],
"Risk_Level": ["Moderate", "High", "Routine", "Critical", "Critical"],
"Days_Pending": [4, 9, 2, 6, 10],
"Data_Quality_Flag": [
"Missing resolution date",
"Missing closure evidence",
"Missing owner",
"Missing human review evidence",
"Pass",
],
}
return pd.DataFrame(data)
df = load_data()
st.sidebar.header("Queue Filters")
selected_risk = st.sidebar.selectbox(
"Filter by Risk Level", ["All", "Routine", "Moderate", "High", "Critical"]
)
if selected_risk != "All":
df = df[df["Risk_Level"] == selected_risk]
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Filtered Cases", len(df))
col2.metric("Critical Risk Items", len(df[df["Risk_Level"] == "Critical"]))
col3.metric("Open High/Critical", len(df[df["Risk_Level"].isin(["High", "Critical"]) & (df["Status"] != "Closed")]))
col4.metric("Data Quality Exceptions", len(df[df["Data_Quality_Flag"] != "Pass"]))
st.subheader("Active Work Queue & Data Quality Exceptions")
st.dataframe(df, use_container_width=True)
st.info(
"Boundary Notice: This tool is built strictly for educational workflow simulation and does not contain PHI or make clinical/payer determinations."
)

