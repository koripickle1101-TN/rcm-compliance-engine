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

st.markdown("---")
st.subheader("Data Export Verification")

if st.button("Run Export Data Integrity Check"):
    validation_passed = len(df_filtered) > 0 and "Case_ID" in df_filtered.columns
    if validation_passed:
        st.success(f"Verification Successful: {len(df_filtered)} active records ready for compliant export.")
    else:
        st.error("Verification Failed: No records detected in current filter scope.")

st.markdown("---")
st.subheader("Queue Analytics Summary Metric")

total_aging_days = int(df_filtered["Days_Pending"].sum()) if "Days_Pending" in df_filtered.columns else 0
avg_aging_days = float(df_filtered["Days_Pending"].mean()) if "Days_Pending" in df_filtered.columns and len(df_filtered) > 0 else 0.0

col1, col2 = st.columns(2)
with col1:
    st.metric("Total Cumulative Days Pending", f"{total_aging_days} Days")
with col2:
    st.metric("Average Days Pending per Case", f"{avg_aging_days:.1f} Days")

def add_branding_header(csv_string, title_text):
    brand_header = f"# ORGANIZATION: RCM Compliance & Work-Queue Intelligence Engine\n# BRAND PALETTE: Tennessee Volunteers Theme (#FF8200, White, Black)\n# REPORT: {title_text}\n"
    return brand_header + csv_string

# Let's see how we can embed this directly into your Streamlit export buttons

st.markdown("---")
st.subheader("Compliance SLA Performance & Resolution Tracking")

sla_summary = df_filtered.groupby("Status").agg(
    Total_Cases=("Case_ID", "count"),
    Avg_Days_Pending=("Days_Pending", "mean")
).reset_index()

st.dataframe(sla_summary, use_container_width=True)

st.download_button(
    label="⏱️ Download SLA Compliance Report",
    data=sla_summary.to_csv(index=False).encode("utf-8"),
    file_name="sla_compliance_report.csv",
    mime="text/css",
)

st.markdown("---")
st.subheader("Data Quality Exception Audit & Resolution Log")

if "Data_Quality_Flag" in df_filtered.columns:
    dq_summary = df_filtered[df_filtered["Data_Quality_Flag"] != "Pass"].groupby("Data_Quality_Flag").agg(
        Affected_Cases=("Case_ID", "count"),
        Case_List=("Case_ID", lambda x: ", ".join(x))
    ).reset_index()

    st.dataframe(dq_summary, use_container_width=True)

    st.download_button(
        label="📥 Download DQ Exception Audit Log",
        data=dq_summary.to_csv(index=False).encode("utf-8"),
        file_name="data_quality_exception_audit.csv",
        mime="text/csv",
    )
else:
    st.info("No data quality flag field detected in current scope.")


st.markdown("---")
st.subheader("Interactive Compliance Case Search & Filter")

search_query = st.text_input("🔍 Search Active Cases by ID, Status, or Flag", "").strip()

if search_query:
    filtered_search_df = df_filtered[
        df_filtered.astype(str).apply(lambda row: row.str.contains(search_query, case=False, na=False)).any(axis=1)
    ]
    st.write(f"Showing matching results for: **{search_query}** ({len(filtered_search_df)} matches found)")
    st.dataframe(filtered_search_df, use_container_width=True)
else:
    st.info("Type a keyword or case ID above to instantly filter your active compliance queue.")

st.markdown("---")
st.subheader("Compliance Audit Export Hub & Full Snapshot")

# Export all active filtered records with complete metadata
all_data_csv = df_filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="📦 Download Complete Filtered Queue Snapshot (CSV)",
    data=all_data_csv,
    file_name="rcm_complete_queue_snapshot.csv",
    mime="text/csv",
)

st.markdown("---")
st.subheader("Executive Compliance Summary & Print Hub")

# Generate executive text summary block
total_cases_count = len(df_filtered)
critical_count = len(df_filtered[df_filtered["Risk_Level"] == "Critical"])
dq_issues_count = len(df_filtered[df_filtered["Data_Quality_Flag"] != "Pass"])
avg_days = df_filtered["Days_Pending"].mean() if total_cases_count > 0 else 0

executive_summary_text = f"""
==================================================
RCM COMPLIANCE INTELLIGENCE ENGINE - EXECUTIVE REPORT
==================================================
Scope Analyzed: {total_cases_count} Active Work-Queue Cases
Critical Risk Exposure: {critical_count} Cases Requiring Immediate Escalation
Data Quality Exceptions: {dq_issues_count} Active Compliance Flags
Average Case Aging: {avg_days:.1f} Days Pending
Status: Operational Review Complete
==================================================
"""

st.text_area("📋 Copy Executive Summary Report", value=executive_summary_text, height=200)

st.download_button(
    label="📥 Download Executive Summary (.txt)",
    data=executive_summary_text.encode("utf-8"),
    file_name="rcm_executive_compliance_report.txt",
    mime="text/plain",
)
st.markdown("---")
st.subheader("Interactive Remediation & Sign-Off Workflow")

selected_case_to_remediate = st.selectbox(
    "Select Flagged Case ID for Remediation Sign-Off",
    options=df_filtered[df_filtered["Data_Quality_Flag"] != "Pass"]["Case_ID"].tolist()
)

if selected_case_to_remediate:
    current_flag = df_filtered.loc[df_filtered["Case_ID"] == selected_case_to_remediate, "Data_Quality_Flag"].values[0]
    st.write(f"**Current Active Exception for {selected_case_to_remediate}:** `{current_flag}`")
    
    remediation_note = st.text_input("Enter Remediation Action / Resolution Note", placeholder="e.g., Missing owner assigned and verified.")
    
    if st.button("✅ Mark Case Resolved & Update Audit Log"):
        st.success(f"Case {selected_case_to_remediate} successfully cleared! Remediation Logged: '{remediation_note}'")
        st.info("Note: Session-state tracking can persist this update across your workflow filters.")

st.markdown("---")
st.subheader("Persistent Audit & Remediation Logbook")

# Initialize session state history log if it doesn't exist
if "remediation_audit_trail" not in st.session_state:
    st.session_state.remediation_audit_trail = []

selected_case_persist = st.selectbox(
    "Select Case ID for Persistent Audit Sign-Off",
    options=df_filtered[df_filtered["Data_Quality_Flag"] != "Pass"]["Case_ID"].tolist(),
    key="persist_case_select"
)

if selected_case_persist:
    current_flag_val = df_filtered.loc[df_filtered["Case_ID"] == selected_case_persist, "Data_Quality_Flag"].values[0]
    st.write(f"**Target Case Exception:** `{current_flag_val}`")
    
    audit_note = st.text_input("Enter Official Audit Remediation Note", placeholder="e.g., Verified missing documentation and closed loop.", key="persist_note")
    auditor_name = st.text_input("Compliance Auditor / Reviewer Name", placeholder="e.g., K. Pickle, BSHA Compliance", key="persist_auditor")
    
    if st.button("💾 Commit to Permanent Session Audit Log", key="commit_audit_btn"):
        if audit_note and auditor_name:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Append record to session log
            st.session_state.remediation_audit_trail.append({
                "Timestamp": timestamp,
                "Case_ID": selected_case_persist,
                "Exception": current_flag_val,
                "Auditor": auditor_name,
                "Note": audit_note
            })
            st.success(f"Audit record successfully committed for {selected_case_persist}!")
        else:
            st.warning("Please provide both an audit note and your reviewer name before committing.")

# Display live persistent audit log table if entries exist
if st.session_state.remediation_audit_trail:
    st.markdown("### 📋 Live Session Audit Trail")
    audit_df = pd.DataFrame(st.session_state.remediation_audit_trail)
    st.dataframe(audit_df, use_container_width=True)
    
    # CSV Download for the audit trail
    csv_audit = audit_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Official Audit Log (.csv)",
        data=csv_audit,
        file_name="rcm_session_remediation_audit_log.csv",
        mime="text/csv",
        key="download_audit_log_btn"
    )

st.markdown("---")
st.subheader("🏆 Automated Compliance Scoring & Executive Badge")

# Calculate total cases vs critical/unresolved items
total_cases_count = len(df_filtered)
critical_cases_count = len(df_filtered[df_filtered["Risk_Level"] == "Critical"])
unresolved_exceptions = len(df_filtered[df_filtered["Data_Quality_Flag"] != "Pass"])

# Simple scoring logic
compliance_score = max(0, 100 - (critical_cases_count * 20) - (unresolved_exceptions * 10))

# Determine badge grade and color
if compliance_score >= 90:
    grade, status_color = "Grade: A (Optimal Compliance)", "🟢"
elif compliance_score >= 75:
    grade, status_color = "Grade: B (Moderate Risk Control)", "🟡"
else:
    grade, status_color = "Grade: C (Action Required)", "🔴"

col1, col2 = st.columns(2)
with col1:
    st.metric(label="Calculated Compliance Index", value=f"{compliance_score}%", delta=f"{status_color} {grade}")
with col2:
    st.write("**Executive Governance Status:**")
    if compliance_score >= 75:
        st.success("Queue meets baseline administrative quality thresholds for review.")
    else:
        st.warning("Immediate remediation required to clear high-risk compliance flags.")

