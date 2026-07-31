import io
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

tab1, tab2 = st.tabs(["Dashboard & Inspector", "Review & Attestation Guide"])

with tab1:
  @st.cache_data
  def load_default_data():
    data = {
        "Case_ID": [
            "PAUTH-046",
            "PAUTH-047",
            "PAUTH-048",
            "PAUTH-049",
            "PAUTH-050",
        ],
        "Status": [
            "Approved",
            "Closed",
            "Escalated",
            "Pending Review",
            "Appeal Readiness",
        ],
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

  st.sidebar.header("Data & Queue Controls")
  input_method = st.sidebar.radio(
      "Choose Data Input Method", ["Default Data", "Upload CSV", "Paste Data"]
  )

  df = None

  if input_method == "Upload CSV":
    uploaded_file = st.sidebar.file_uploader(
        "Upload Custom Fictional CSV Dataset", type=["csv", "txt"]
    )
    if uploaded_file is not None:
      try:
        df = pd.read_csv(uploaded_file)
      except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")

  elif input_method == "Paste Data":
    pasted_data = st.sidebar.text_area(
        "Paste CSV Data Here",
        placeholder=(
            "Case_ID,Status,Risk_Level,Days_Pending,Data_Quality_Flag\nTEST-101,Pending"
            " Review,Critical,12,Missing review"
        ),
        height=150,
    )
    if pasted_data:
      try:
        df = pd.read_csv(io.StringIO(pasted_data))
      except Exception as e:
        st.sidebar.error(f"Error parsing pasted text: {e}")

  if df is None:
    df = load_default_data()

  if "Risk_Level" in df.columns:
    risk_options = ["All"] + list(df["Risk_Level"].unique())
    selected_risk = st.sidebar.selectbox("Filter by Risk Level", risk_options)

    if selected_risk != "All":
      df_filtered = df[df["Risk_Level"] == selected_risk]
    else:
      df_filtered = df
  else:
    df_filtered = df

  col1, col2, col3, col4 = st.columns(4)
  col1.metric("Total Filtered Cases", len(df_filtered))
  if "Risk_Level" in df_filtered.columns:
    col2.metric(
        "Critical Risk Items",
        len(df_filtered[df_filtered["Risk_Level"] == "Critical"]),
    )
    col3.metric(
        "Open High/Critical",
        len(
            df_filtered[
                df_filtered["Risk_Level"].isin(["High", "Critical"])
                & (df_filtered["Status"] != "Closed")
            ]
        ),
    )
  else:
    col2.metric("Critical Risk Items", 0)
    col3.metric("Open High/Critical", 0)

  if "Data_Quality_Flag" in df_filtered.columns:
    col4.metric(
        "Data Quality Exceptions",
        len(df_filtered[df_filtered["Data_Quality_Flag"] != "Pass"]),
    )
  else:
    col4.metric("Data Quality Exceptions", 0)

  st.subheader("Active Work Queue & Data Quality Exceptions")
  st.dataframe(df_filtered, use_container_width=True)

  if not df_filtered.empty and "Status" in df_filtered.columns:
    st.subheader("Dashboard Visual Analytics")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
      st.markdown("**Status Breakdown**")
      status_counts = df_filtered["Status"].value_counts()
      st.bar_chart(status_counts)

    with chart_col2:
      if "Days_Pending" in df_filtered.columns:
        st.markdown("**Aging Breakdown (Days Pending)**")
        st.bar_chart(df_filtered.set_index("Case_ID")["Days_Pending"])

  if not df.empty and "Case_ID" in df.columns:
    st.subheader("Interactive Case Detail Inspector")
    selected_case = st.selectbox(
        "Select Case ID to Review", df["Case_ID"].tolist()
    )
    case_row = df[df["Case_ID"] == selected_case]
    if not case_row.empty:
      case_details = case_row.iloc[0]
      col_a, col_b, col_c = st.columns(3)
      col_a.metric("Current Status", case_details.get("Status", "N/A"))
      col_b.metric("Risk Level", case_details.get("Risk_Level", "N/A"))
      col_c.metric("Days Pending", case_details.get("Days_Pending", "N/A"))

      if "Data_Quality_Flag" in case_details:
        st.markdown(
            f"**Data Quality Flag Status for {selected_case}:**"
            f" `{case_details['Data_Quality_Flag']}`"
        )

with tab2:
  st.subheader("PA-004 Review Guide & Attestation Framework")
  st.markdown("### Scope Definitions")
  st.write(
      "This application serves as an educational simulation framework to"
      " evaluate administrative work-queue throughput, tracking logic, and data"
      " quality standards without exposing production or protected information."
  )

  st.markdown("### Personal Boundary Statements")
  st.info(
      "Strict No-PHI Boundary: This engine utilizes entirely fictional,"
      " synthesized dataset structures. It is intentionally decoupled from live"
      " clinical workflows or adjudication engines."
  )

  st.markdown("### Attestation Checklist")
  st.checkbox(
      "Verified structure contains zero Protected Health Information (PHI)."
  )
  st.checkbox("Validated exception flagging logic against administrative standard rules.")
  st.checkbox("Confirmed Vols brand identity requirements and layout responsiveness.")

st.info(
    "Boundary Notice: This tool is built strictly for educational workflow"
    " simulation and does not contain PHI or make clinical/payer"
    " determinations."
)

st.markdown("---")
st.subheader("Queue Health & Export Controls")

if "Data_Quality_Flag" in df_filtered.columns:
    passed_count = len(df_filtered[df_filtered["Data_Quality_Flag"] == "Pass"])
    total_count = len(df_filtered)
    health_score = int((passed_count / total_count) * 100) if total_count > 0 else 100
    st.metric(
        "Overall Queue Compliance Health",
        f"{health_score}%",
        delta=f"{passed_count} of {total_count} passing"
    )

@st.cache_data
def convert_df_to_csv(dataframe):
    return dataframe.to_csv(index=False).encode("utf-8")

csv_data = convert_df_to_csv(df_filtered)

st.download_button(
    label="📥 Download Filtered Dataset as CSV",
    data=csv_data,
    file_name="rcm_filtered_export.csv",
    mime="text/csv",
)

st.markdown("---")
st.subheader("Risk Level Breakdown & Audit Summary")

risk_summary = df_filtered["Risk_Level"].value_counts().reset_index()
risk_summary.columns = ["Risk_Level", "Count"]

st.dataframe(risk_summary, use_container_width=True)

st.download_button(
    label="📊 Download Risk Audit Summary",
    data=risk_summary.to_csv(index=False).encode("utf-8"),
    file_name="risk_audit_summary.csv",
    mime="text/csv",
)

st.markdown("---")
st.subheader("Aging Breakdown Summary")

aging_summary = df_filtered[["Case_ID", "Days_Pending", "Risk_Level"]].sort_values(by="Days_Pending", ascending=False).reset_index(drop=True)

st.dataframe(aging_summary, use_container_width=True)

st.download_button(
    label="⏱️ Download Aging Breakdown CSV",
    data=aging_summary.to_csv(index=False).encode("utf-8"),
    file_name="aging_breakdown_summary.csv",
    mime="text/csv",
)
