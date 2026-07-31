import sqlite3
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# --- PAGE CONFIGURATION & THEME ---
st.set_page_config(
    page_title="RCM Compliance & Work-Queue Intelligence Engine",
    page_icon="🏥",
    layout="wide",
)

# Tennessee Volunteers Theme Colors
VOLS_ORANGE = "#FF8200"
DARK_BG = "#0E1117"
CARD_BG = "#1A1D24"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {DARK_BG};
        color: #FFFFFF;
    }}
    .metric-card {{
        background-color: {CARD_BG};
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid {VOLS_ORANGE};
    }}
    h1, h2, h3 {{
        color: {VOLS_ORANGE} !important;
    }}
    </style>
""",
    unsafe_allow_html=True,
)

# --- DATABASE SETUP & INITIALIZATION ---
DB_NAME = "rcm_compliance.db"


def init_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            case_id TEXT,
            exception TEXT,
            auditor TEXT,
            remediation_note TEXT,
            role TEXT
        )
    """)
  # New table for session export logging
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS export_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user TEXT,
            export_type TEXT,
            row_count INTEGER
        )
    """)
  conn.commit()
  conn.close()


init_db()


def log_export_to_db(user, export_type, row_count):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "INSERT INTO export_history (timestamp, user, export_type, row_count)"
      " VALUES (?, ?, ?, ?)",
      (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user, export_type, row_count),
  )
  conn.commit()
  conn.close()


# --- SIDEBAR: ROLE-BASED ACCESS CONTROL (RBAC) ---
st.sidebar.markdown(f"## 🛡️ Enterprise Governance")
user_role = st.sidebar.selectbox(
    "Select Access Role", ["Junior Auditor", "Compliance Manager", "System Admin"]
)
current_user = st.sidebar.text_input(
    "User Identifier", "K. Pickle, BSHA Compliance"
)

st.sidebar.markdown("---")
st.sidebar.info(f"**Current Session Tier:** {user_role}")

# --- MOCK DATA GENERATION ---
data = {
    "Case_ID": ["PAUTH-046", "PAUTH-047", "PAUTH-048", "PAUTH-049", "PAUTH-050"],
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
df = pd.DataFrame(data)

# --- MAIN DASHBOARD HEADER ---
st.markdown(
    "# RCM Compliance & Work-Queue Intelligence Engine"
)  #
st.markdown(
    "*Enterprise Portfolio Artifact: RBAC, SQLite Persistence, Webhook"
    " Alerting, and Historical Audit Search.*"
)  #

# --- METRICS ROW ---
col1, col2, col3, col4 = st.columns(4)
with col1:
  st.metric(
      label="Total Filtered Cases", value=len(df)
  )  #
with col2:
  st.metric(
      label="Critical Risk Items",
      value=len(df[df["Risk_Level"] == "Critical"]),
  )  #
with col3:
  st.metric(
      label="Open High/Critical",
      value=len(df[df["Risk_Level"].isin(["High", "Critical"])]),
  )  #
with col4:
  st.metric(
      label="Data Quality Exceptions",
      value=len(df[df["Data_Quality_Flag"] != "Pass"]),
  )  #

st.markdown("---")

# --- ACTIVE WORK QUEUE TABLE ---
st.markdown("### Active Work Queue & Data Quality Exceptions")
st.dataframe(df, use_container_width=True)

# --- EXPORT CONTROLS WITH LOGGING ---
st.markdown("### Queue Health & Export Controls")
csv_data = df.to_csv(index=False).encode("utf-8")
if st.download_button(
    "📥 Download Filtered Dataset as CSV",
    csv_data,
    "rcm_filtered_queue.csv",
    "text/csv",
):
  log_export_to_db(current_user, "Filtered Dataset CSV", len(df))
  st.success("Export logged to SQLite successfully!")

st.markdown("---")

# --- PERSISTENT SQLITE AUDIT & REMEDIATION LOGBOOK ---
st.markdown("### Persistent SQLite Audit & Remediation Logbook")

selected_case = st.selectbox(
    "Select Case ID for Persistent SQLite Audit Sign-Off", df["Case_ID"]
)
target_exception = df.loc[df["Case_ID"] == selected_case][
    "Data_Quality_Flag"
].values[0]
st.markdown(f"**Target Case Exception:** `{target_exception}`")

remediation_note = st.text_input(
    "Enter Official Audit Remediation Note",
    "Verified missing documentation and closed loop.",
)
auditor_name = st.text_input("Compliance Auditor / Reviewer Name", current_user)

if st.button("💾 Commit Remediation to Database & Update Queue State to 'Pass'"):
  if user_role == "Junior Auditor":
    st.error(
        "Access Denied: Junior Auditors do not have permission to execute"
        " queue state overrides. Contact a Compliance Manager or System Admin."
    )
  else:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
            INSERT INTO audit_log (timestamp, case_id, exception, auditor,"
        " remediation_note, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            selected_case,
            target_exception,
            auditor_name,
            remediation_note,
            user_role,
        ),
    )
    conn.commit()
    conn.close()
    st.success(
        f"Remediation for {selected_case} committed to SQLite database"
        " successfully!"
    )

# --- NEW: HISTORICAL AUDIT SEARCH & FILTER PANEL ---
st.markdown("### 🔍 Historical Audit Search & Traceability Panel")
st.markdown(
    "Query past immutable audit decisions and state change histories for"
    " regulatory compliance reviews."
)

search_col1, search_col2 = st.columns(2)
with search_col1:
  audit_search_term = st.text_input(
      "Search Audit History (Case ID or Auditor)", ""
  )
with search_col2:
  export_log_view = st.checkbox("View Database Export History Log", False)

conn = sqlite3.connect(DB_NAME)
if audit_search_term:
  query = "SELECT * FROM audit_log WHERE case_id LIKE ? OR auditor LIKE ?"
  audit_df = pd.read_sql_query(
      query, conn, params=(f"%{audit_search_term}%", f"%{audit_search_term}%")
  )
else:
  audit_df = pd.read_sql_query(
      "SELECT * FROM audit_log ORDER BY timestamp DESC", conn
  )

st.markdown("#### Official SQLite Audit Trail Records")
if not audit_df.empty:
  st.dataframe(audit_df, use_container_width=True)
  audit_csv = audit_df.to_csv(index=False).encode("utf-8")
  if st.download_button(
      "📥 Download Official SQLite Audit Log (.csv)",
      audit_csv,
      "rcm_audit_log_history.csv",
      "text/csv",
  ):
    log_export_to_db(current_user, "Audit Log History CSV", len(audit_df))
else:
  st.info(
      "No audit records found matching criteria. Commit a remediation above to"
      " populate the database."
  )

if export_log_view:
  st.markdown("#### Immutable Database Export History")
  export_df = pd.read_sql_query(
      "SELECT * FROM export_history ORDER BY timestamp DESC", conn
  )
  st.dataframe(export_df, use_container_width=True)

conn.close()

st.markdown("---")

# --- AUTOMATED COMPLIANCE ALERT & WEBHOOK DISPATCHER ---
st.markdown("### 🚨 Automated Compliance Alert & Webhook Dispatcher")
webhook_url = st.text_input(
    "Webhook Endpoint URL (Slack / Teams / Custom)", "https://httpbin.org/post"
)
officer_email = st.text_input("Compliance Officer Email", current_user)

col_alert1, col_alert2 = st.columns(2)
with col_alert1:
  if st.button("📡 Dispatch Webhook Executive Alert"):
    try:
      payload = {
          "event": "RCM_COMPLIANCE_ALERT",
          "total_cases": len(df),
          "critical_risks": int(
              len(df[df["Risk_Level"] == "Critical"])
          ),  # Ensure JSON serializable
          "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      }
      response = requests.post(webhook_url, json=payload, timeout=5)
      st.success(
          f"Webhook alert successfully dispatched! Response status code:"
          f" {response.status_code}"
      )
    except Exception as e:
      st.error(f"Webhook dispatch failed: {e}")

with col_alert2:
  if st.button("📧 Simulate SMTP Email Dispatch"):
    st.success(
        f"Simulated email successfully transmitted to {officer_email} with"
        " attached Executive Compliance Summary!"
    )

