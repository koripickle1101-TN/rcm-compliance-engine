import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import datetime
import requests
import io

# Optional ReportLab import for PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ==========================================
# PAGE CONFIGURATION & VOLS COLOR SCHEME
# ==========================================
st.set_page_config(
    page_title="RCM Compliance Intelligence Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling: White Background (#FFFFFF), Black Text (#000000), Vols Orange Accent (#FF8200)
st.markdown("""
    <style>
        :root {
            --vols-orange: #FF8200;
            --vols-black: #000000;
            --vols-white: #FFFFFF;
        }
        
        /* Pure White Background for Main Body & App Area */
        .stApp, .main, [data-testid="stAppViewContainer"] {
            background-color: #FFFFFF !important;
            color: #000000 !important;
        }
        
        /* Black Typography for Headers, Text, and Labels */
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, div {
            color: #000000 !important;
        }

        /* Input Boxes & Dropdowns: Orange Accent Styling */
        div[data-baseweb="input"] > div, 
        div[data-baseweb="select"] > div,
        .stTextInput input, 
        .stSelectbox div, 
        .stMultiSelect div {
            border: 2px solid #FF8200 !important;
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border-radius: 6px !important;
        }
        
        /* Focus state for input boxes */
        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="select"]:focus-within {
            border-color: #000000 !important;
            box-shadow: 0 0 0 1px #FF8200 !important;
        }

        /* High-Contrast Action Buttons with Vols Orange */
        div.stButton > button:first-child {
            background-color: #FF8200 !important;
            color: #000000 !important;
            font-weight: bold !important;
            border-radius: 6px !important;
            border: 1px solid #000000 !important;
            width: 100%;
        }
        div.stButton > button:first-child:hover {
            background-color: #E67300 !important;
            color: #FFFFFF !important;
        }

        /* Pure White Metric Cards with Orange Borders */
        .metric-card {
            background-color: #FFFFFF;
            border-left: 6px solid #FF8200;
            border-top: 1px solid #E0E0E0;
            border-right: 1px solid #E0E0E0;
            border-bottom: 1px solid #E0E0E0;
            padding: 16px;
            border-radius: 6px;
            margin-bottom: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .metric-title {
            color: #FF8200;
            font-size: 0.85rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .metric-value {
            font-size: 1.7rem;
            font-weight: bold;
            color: #000000;
            margin-top: 4px;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# DATABASE INITIALIZATION
# ==========================================
def init_db():
    conn = sqlite3.connect("rcm_audit_log.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            case_id TEXT,
            exception TEXT,
            auditor TEXT,
            notes TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS case_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            case_id TEXT,
            author TEXT,
            note TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ==========================================
# INITIAL DATASET & SESSION STATE
# ==========================================
if "df_cases" not in st.session_state:
    st.session_state.df_cases = pd.DataFrame([
        {"Case_ID": "PAUTH-046", "Status": "Approved", "Risk_Level": "Moderate", "Days_Pending": 4, "Data_Quality_Flag": "Missing resolution date", "Claim_Value": 8500.00},
        {"Case_ID": "PAUTH-047", "Status": "Closed", "Risk_Level": "High", "Days_Pending": 9, "Data_Quality_Flag": "Missing closure evidence", "Claim_Value": 12000.00},
        {"Case_ID": "PAUTH-048", "Status": "Escalated", "Risk_Level": "Routine", "Days_Pending": 2, "Data_Quality_Flag": "Missing owner", "Claim_Value": 4500.00},
        {"Case_ID": "PAUTH-049", "Status": "Pending Review", "Risk_Level": "Critical", "Days_Pending": 6, "Data_Quality_Flag": "Missing human review evidence", "Claim_Value": 25000.00},
        {"Case_ID": "PAUTH-050", "Status": "Appeal Readiness", "Risk_Level": "Critical", "Days_Pending": 10, "Data_Quality_Flag": "Pass", "Claim_Value": 20000.00}
    ])

# ==========================================
# SIDEBAR CONTROL
# ==========================================
with st.sidebar:
    st.header("Enterprise Governance")
    role = st.selectbox("Select Access Role", ["System Admin", "Compliance Manager", "Junior Auditor"])
    user_id = st.text_input("User Identifier", value="K. Pickle, BSHA Compliance")
    st.markdown("---")
    st.markdown(f"**Active Session:** {role}")

# ==========================================
# MAIN DASHBOARD CONTENT
# ==========================================
st.title("RCM Compliance & Work-Queue Intelligence Engine")
st.caption("Enterprise Portfolio Artifact: RBAC, SQLite Persistence, Webhook Alerting, and Historical Audit Search.")

df = st.session_state.df_cases

# 1. Financial Exposure & Executive Metrics
total_portfolio_val = df["Claim_Value"].sum()
revenue_at_risk = df[df["Data_Quality_Flag"] != "Pass"]["Claim_Value"].sum()
critical_exposure = df[df["Risk_Level"] == "Critical"]["Claim_Value"].sum()
active_flags = len(df[df["Data_Quality_Flag"] != "Pass"])

st.subheader("Financial Exposure & Executive Metrics")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">TOTAL PORTFOLIO VALUE</div><div class="metric-value">${total_portfolio_val:,.2f}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><div class="metric-title">REVENUE AT RISK</div><div class="metric-value">${revenue_at_risk:,.2f}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><div class="metric-title">CRITICAL FINANCIAL RISK</div><div class="metric-value">${critical_exposure:,.2f}</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><div class="metric-title">ACTIVE EXCEPTION FLAGS</div><div class="metric-value">{active_flags}</div></div>', unsafe_allow_html=True)

# 2. Executive Portfolio Snapshot
passing_cases = len(df[df["Data_Quality_Flag"] == "Pass"])
total_cases = len(df)
compliance_index = int((passing_cases / total_cases) * 100)

st.subheader("Executive Portfolio Snapshot")
s1, s2, s3 = st.columns(3)
with s1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">OVERALL COMPLIANCE INDEX</div><div class="metric-value">{compliance_index}%</div></div>', unsafe_allow_html=True)
with s2:
    st.markdown(f'<div class="metric-card"><div class="metric-title">CRITICAL FINANCIAL RISK</div><div class="metric-value">${critical_exposure:,.2f}</div></div>', unsafe_allow_html=True)
with s3:
    grade = "Grade A" if compliance_index == 100 else ("Grade B" if compliance_index >= 60 else "Grade C")
    st.markdown(f'<div class="metric-card"><div class="metric-title">PORTFOLIO HEALTH STATUS</div><div class="metric-value">{grade}</div></div>', unsafe_allow_html=True)

st.markdown("---")

# 3. Active Work Queue & Data Quality Exceptions
st.subheader("Active Work Queue & Data Quality Exceptions")

f_col1, f_col2 = st.columns(2)
with f_col1:
    selected_risk = st.multiselect("Filter by Risk Level", options=df["Risk_Level"].unique(), default=df["Risk_Level"].unique())
with f_col2:
    selected_flag = st.multiselect("Filter by Data Quality Flag Status", options=df["Data_Quality_Flag"].unique(), default=df["Data_Quality_Flag"].unique())

filtered_df = df[(df["Risk_Level"].isin(selected_risk)) & (df["Data_Quality_Flag"].isin(selected_flag))]
st.dataframe(filtered_df, use_container_width=True)

# Visual Charts
import plotly.express as px
ch1, ch2 = st.columns(2)
with ch1:
    fig_status = px.bar(filtered_df, x="Status", title="Status Distribution (Filtered Cases)", color_discrete_sequence=["#FF8200"])
    fig_status.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font_color="#000000")
    st.plotly_chart(fig_status, use_container_width=True)
with ch2:
    fig_aging = px.bar(filtered_df, x="Case_ID", y="Days_Pending", title="Aging Breakdown (Filtered Cases)", color_discrete_sequence=["#FF8200"])
    fig_aging.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font_color="#000000")
    st.plotly_chart(fig_aging, use_container_width=True)

st.markdown("---")

# 4. Interactive Case Detail Inspector
st.subheader("Interactive Case Detail Inspector")
selected_case_id = st.selectbox("Select Case ID to Review", options=df["Case_ID"].tolist())
case_row = df[df["Case_ID"] == selected_case_id].iloc[0]

ic1, ic2, ic3, ic4 = st.columns(4)
with ic1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">CURRENT STATUS</div><div class="metric-value">{case_row["Status"]}</div></div>', unsafe_allow_html=True)
with ic2:
    st.markdown(f'<div class="metric-card"><div class="metric-title">RISK LEVEL</div><div class="metric-value">{case_row["Risk_Level"]}</div></div>', unsafe_allow_html=True)
with ic3:
    st.markdown(f'<div class="metric-card"><div class="metric-title">DAYS PENDING</div><div class="metric-value">{case_row["Days_Pending"]}</div></div>', unsafe_allow_html=True)
with ic4:
    st.markdown(f'<div class="metric-card"><div class="metric-title">CLAIM VALUE</div><div class="metric-value">${case_row["Claim_Value"]:,.2f}</div></div>', unsafe_allow_html=True)

st.info(f"Data Quality Flag Status for {selected_case_id}: **{case_row['Data_Quality_Flag']}**")

st.markdown("---")

# 5. Bulk Remediation Hub
st.subheader("Bulk Remediation Hub")
open_cases = df[df["Data_Quality_Flag"] != "Pass"]["Case_ID"].tolist()
if open_cases:
    selected_bulk_cases = st.multiselect("Select Case IDs for Bulk Audit Sign-Off", options=open_cases)
    bulk_note = st.text_input("Enter Bulk Remediation Note (Applied to ALL selected cases)", placeholder="e.g., Verified clearinghouse records and updated documentation across batch.")
    
    if st.button("Execute Bulk Remediation & Commit to SQLite"):
        if selected_bulk_cases and bulk_note:
            conn = sqlite3.connect("rcm_audit_log.db")
            c = conn.cursor()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for cid in selected_bulk_cases:
                st.session_state.df_cases.loc[st.session_state.df_cases["Case_ID"] == cid, "Data_Quality_Flag"] = "Pass"
                c.execute("INSERT INTO audit_logs (timestamp, case_id, exception, auditor, notes) VALUES (?, ?, ?, ?, ?)",
                          (timestamp, cid, "Pass", user_id, bulk_note))
            conn.commit()
            conn.close()
            st.success(f"Successfully executed bulk remediation for {len(selected_bulk_cases)} cases.")
            st.rerun()
        else:
            st.warning("Please select cases and enter a note.")
else:
    st.info("No options to select (All active cases are marked as Pass).")

st.markdown("---")

# 6. Persistent SQLite Audit & Remediation Logbook & Live State Update
st.subheader("Persistent SQLite Audit & Remediation Logbook & Live State Update")
rem_case_id = st.selectbox("Select Case ID for Persistent SQLite Audit Sign-Off", options=df["Case_ID"].tolist(), key="single_signoff_select")
target_row = df[df["Case_ID"] == rem_case_id].iloc[0]
st.write(f"Target Case Exception: **{target_row['Data_Quality_Flag']}**")

single_note = st.text_input("Enter Official Audit Remediation Note", placeholder="e.g., Verified missing documentation and closed loop.", key="single_note_input")
auditor_input = st.text_input("Compliance Auditor / Reviewer Name", value=user_id, key="auditor_name_input")

if st.button("Commit Remediation to Database & Update Queue State to 'Pass'"):
    if single_note:
        st.session_state.df_cases.loc[st.session_state.df_cases["Case_ID"] == rem_case_id, "Data_Quality_Flag"] = "Pass"
        conn = sqlite3.connect("rcm_audit_log.db")
        c = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO audit_logs (timestamp, case_id, exception, auditor, notes) VALUES (?, ?, ?, ?, ?)",
                  (timestamp, rem_case_id, "Pass", auditor_input, single_note))
        conn.commit()
        conn.close()
        st.success(f"Updated {rem_case_id} state to Pass and committed record to SQLite audit log.")
        st.rerun()
    else:
        st.warning("Please enter a remediation note.")

st.markdown("---")

# 7. Historical Audit Search & Traceability Panel
st.subheader("Historical Audit Search & Traceability Panel")
conn = sqlite3.connect("rcm_audit_log.db")
audit_logs_df = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY id DESC", conn)
conn.close()

search_query = st.text_input("Search Audit History (Case ID or Auditor)")
if search_query:
    audit_logs_df = audit_logs_df[audit_logs_df["case_id"].str.contains(search_query, case=False, na=False) |
                                  audit_logs_df["auditor"].str.contains(search_query, case=False, na=False)]

st.write("Official SQLite Audit Trail Records")
st.dataframe(audit_logs_df, use_container_width=True)

st.markdown("---")

# 8. Automated Compliance Alert & Webhook Dispatcher
st.subheader("Automated Compliance Alert & Webhook Dispatcher")

webhook_url = st.text_input("Webhook Endpoint URL (Slack / Teams / Custom)", value="https://httpbin.org/post")
email_recipient = st.text_input("Compliance Officer Email", value="koripickle1101@gmail.com")

w_col1, w_col2 = st.columns(2)
with w_col1:
    if st.button("Dispatch Webhook Executive Alert"):
        try:
            payload = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "compliance_index": f"{compliance_index}%",
                "auditor": user_id,
                "revenue_at_risk": f"${revenue_at_risk:,.2f}"
            }
            res = requests.post(webhook_url, json=payload, timeout=5)
            if res.status_code == 200:
                st.success(f"Webhook alert successfully dispatched! Response status code: {res.status_code}")
            else:
                st.warning(f"Webhook dispatched with status code: {res.status_code}")
        except Exception as e:
            st.error(f"Webhook dispatch failed: {e}")

with w_col2:
    if st.button("Simulate SMTP Email Dispatch"):
        st.success(f"Simulated email successfully transmitted to {email_recipient} with attached Executive Compliance Summary!")

st.markdown("---")

# 9. Executive Report Exports
st.subheader("Executive Report Exports")

summary_text = f"""==================================================
RCM COMPLIANCE INTELLIGENCE ENGINE - EXECUTIVE REPORT
==================================================
Generated Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Reviewer Authority: {user_id}
--------------------------------------------------
Scope Analyzed: {len(df)} Active Work-Queue Cases
Total Portfolio Value: ${total_portfolio_val:,.2f}
Revenue at Risk (Exceptions): ${revenue_at_risk:,.2f}
Critical Financial Exposure: ${critical_exposure:,.2f}
Data Quality Exceptions: {active_flags} Active Compliance Flags
Calculated Compliance Index: {compliance_index}%
=================================================="""

d_col1, d_col2 = st.columns(2)
with d_col1:
    st.download_button(
        label="Download Executive Summary (.txt)",
        data=summary_text,
        file_name="rcm_executive_summary.txt",
        mime="text/plain"
    )
with d_col2:
    if REPORTLAB_AVAILABLE:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor("#FF8200"))
        body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=10, textColor=colors.black)
        story = [
            Paragraph("RCM COMPLIANCE AUDIT CERTIFICATE", title_style),
            HRFlowable(width="100%", thickness=2, color=colors.HexColor("#FF8200"), spaceAfter=15),
            Paragraph(f"<b>Timestamp:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/><b>Auditor:</b> {user_id}<br/><b>Compliance Index:</b> {compliance_index}%", body_style),
            Spacer(1, 15)
        ]
        doc.build(story)
        buffer.seek(0)
        st.download_button(
            label="Download Official PDF Audit Certificate",
            data=buffer,
            file_name="rcm_audit_certificate.pdf",
            mime="application/pdf"
        )

st.caption("CREATED BY KORI PICKLE | BSHA Healthcare Operations & Compliance Engine")
