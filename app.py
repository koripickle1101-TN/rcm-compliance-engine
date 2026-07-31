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
    df_filtered = df[df["Risk_Level"] == selected_risk]
else:
    df_filtered = df

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Filtered Cases", len(df_filtered))
col2.metric("Critical Risk Items", len(df_filtered[df_filtered["Risk_Level"] == "Critical"]))
col3.metric("Open High/Critical", len(df_filtered[df_filtered["Risk_Level"].isin(["High", "Critical"]) & (df_filtered["Status"] != "Closed")]))
col4.metric("Data Quality Exceptions", len(df_filtered[df_filtered["Data_Quality_Flag"] != "Pass"]))

st.subheader("Active Work Queue & Data Quality Exceptions")
st.dataframe(df_filtered, use_container_width=True)

st.subheader("Interactive Case Detail Inspector")
selected_case = st.selectbox("Select Case ID to Review", df["Case_ID"].tolist())
case_details = df[df["Case_ID"] == selected_case].iloc[0]

col_a, col_b, col_c = st.columns(3)
col_a.metric("Current Status", case_details["Status"])
col_b.metric("Risk Level", case_details["Risk_Level"])
col_c.metric("Days Pending", case_details["Days_Pending"])

st.markdown(f"**Data Quality Flag Status for {selected_case}:** `{case_details['Data_Quality_Flag']}`")

st.info(
    "Boundary Notice: This tool is built strictly for educational workflow simulation and does not contain PHI or make clinical/payer determinations."
)
