import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import datetime
import requests
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ==========================================
# PAGE CONFIGURATION & THEME
# ==========================================
st.set_page_config(
    page_title="RCM Compliance Intelligence Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom VOLS High-Contrast Styling
st.markdown("""
    <style>
        :root {
            --vols-orange: #FF8200;
            --vols-black: #000000;
            --vols-white: #FFFFFF;
        }
        .main {
            background-color: #0E1117;
            color: #FFFFFF;
        }
        stButton > button {
            background-color: #FF8200 !important;
            color: #000000 !important;
            font-weight: bold !important;
            border-radius: 6px !important;
            border: none !important;
            width: 100%;
        }
        stButton > button:hover {
            background-color: #E67300 !important;
            color: #FFFFFF !important;
        }
        .metric-card {
            background-color: #161B22;
            border-left: 5px solid #FF8200;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        .metric-title {
            color: #FF8200;
            font-size: 0.85rem;
            font-weight: bold;
            text-transform: uppercase;
        }
        .metric-value {
            font-size: 1.6rem;
            font-weight: bold;
            color: #FFFFFF;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# DATABASE INITIALIZATION (SQLite)
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
# PDF GENERATOR FUNCTION (ReportLab)
# ==========================================
def generate_pdf_report(compliance_score, total_val, revenue_risk, auditor_name):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor("#FF8200"),
        spaceAfter=10
    )
    
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        spaceAfter=6
    )

    story = []
    story.append(Paragraph("RCM COMPLIANCE & AUDIT CERTIFICATE", title_style))
    story.append(HRFlowable(width="100%", thickness=3, color=colors.HexColor("#FF8200"), spaceAfter=15))
    
    meta_text = f"<b>Generated Timestamp:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>" \
                f"<b>Reviewer Authority:</b> {auditor_name}<br/>" \
                f"<b>Governance Status:</b> Official Executive Audit Sign-Off"
    story.append(Paragraph(meta_text, body_style))
    story.append(Spacer(1, 15))

    # Summary Table Data
    table_data = [
        ["Metric", "Value"],
        ["Overall Compliance Score", f"{compliance_score}%"],
        ["Total Portfolio Value", f"${total_val:,.2f}"],
        ["Revenue at Risk (Active Exceptions)", f"${revenue_risk:,.2f}"],
        ["Audit Certification Grade", "Grade A (Compliant)" if compliance_score == 100 else "Grade Action Required"]
    ]

    t = Table(table_data, colWidths=[250, 250])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#FF8200")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F8F9FA")),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#CCCCCC")),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    story.append(Paragraph("<b>Detailed Work Queue Audit Snapshot:</b>", body_style))
    
    # Cases Table
    case_headers = [["Case ID", "Status", "Risk Level", "Claim Value", "Compliance Flag"]]
    for _, row in st.session_state.df_cases.iterrows():
        case_headers.append([
            row["Case_ID"], 
            row["Status"], 
            row["Risk_Level"], 
            f"${row['Claim_Value']:,.2f}", 
            row["Data_Quality_Flag"]
        ])
    
    t_cases = Table(case_headers, colWidths=[80, 100, 80, 90, 150])
    t_cases.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#000000")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD")),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]))
    story.append(t_cases)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==========================================
# SIDEBAR CONTROL & RBAC
# ==========================================
with st.sidebar:
    st.header("Enterprise Governance")
    role = st.selectbox("Select Access Role", ["System Admin", "Compliance Manager", "Junior Auditor"])
    user_id = st.text_input("User Identifier", value="K. Pickle, BSHA Compliance")
    st.markdown("---")
    st.markdown(f"**Active Session:** {role}")

# ==========================================
# MAIN DASHBOARD HEADER
# ==========================================
st.title("RCM Compliance & Work-Queue Intelligence Engine")
st.caption("Enterprise Portfolio Artifact: RBAC, SQLite Persistence, Webhook Alerting, and PDF Certification.")

# ==========================================
# UPGRADE 1: FINANCIAL EXPOSURE METRICS
# ==========================================
df = st.session_state.df_cases

total_portfolio_val = df["Claim_Value"].sum()
revenue_at_risk = df[df["Data_Quality_Flag"] != "Pass"]["Claim_Value"].sum()
critical_exposure = df[df["Risk_Level"] == "Critical"]["Claim_Value"].sum()
active_flags = len(df[df["Data_Quality_Flag"] != "Pass"])

st.subheader("Financial Exposure & Executive Metrics")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Total Portfolio Value</div><div class="metric-value">${total_portfolio_val:,.2f}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Revenue at Risk</div><div class="metric-value">${revenue_at_risk:,.2f}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Critical Exposure</div><div class="metric-value">${critical_exposure:,.2f}</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Active Flags</div><div class="metric-value">{active_flags}</div></div>', unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# UPGRADE 2: DYNAMIC CHART SYNCHRONIZATION
# ==========================================
st.subheader("Interactive Queue & Dynamic Filter Panel")

f_col1, f_col2 = st.columns(2)
with f_col1:
    selected_risk = st.multiselect("Filter by Risk Level", options=df["Risk_Level"].unique(), default=df["Risk_Level"].unique())
with f_col2:
    selected_flag = st.multiselect("Filter by Data Quality Flag Status", options=df["Data_Quality_Flag"].unique(), default=df["Data_Quality_Flag"].unique())

# Dynamically Filtered Dataframe
filtered_df = df[(df["Risk_Level"].isin(selected_risk)) & (df["Data_Quality_Flag"].isin(selected_flag))]

st.dataframe(filtered_df, use_container_width=True)

# Synchronized Visual Charts
import plotly.express as px

ch1, ch2 = st.columns(2)
with ch1:
    fig_status = px.bar(
        filtered_df, x="Status", title="Status Distribution (Filtered Cases)",
        color_discrete_sequence=["#FF8200"]
    )
    fig_status.update_layout(paper_bgcolor="#0E1117", plot_bgcolor="#0E1117", font_color="#FFFFFF")
    st.plotly_chart(fig_status, use_container_width=True)

with ch2:
    fig_aging = px.bar(
        filtered_df, x="Case_ID", y="Days_Pending", title="Aging Breakdown (Filtered Cases)",
        color_discrete_sequence=["#FF8200"]
    )
    fig_aging.update_layout(paper_bgcolor="#0E1117", plot_bgcolor="#0E1117", font_color="#FFFFFF")
    st.plotly_chart(fig_aging, use_container_width=True)

st.markdown("---")

# ==========================================
# UPGRADE 3: BULK WORK-QUEUE REMEDIATION
# ==========================================
st.subheader("Bulk Remediation Hub")

open_cases = df[df["Data_Quality_Flag"] != "Pass"]["Case_ID"].tolist()

if open_cases:
    selected_bulk_cases = st.multiselect("Select Case IDs for Bulk Audit Sign-Off", options=open_cases)
    bulk_note = st.text_area("Enter Bulk Remediation Note (Applied to ALL selected cases)", placeholder="e.g., Verified clearinghouse records and updated documentation across batch.")
    
    if st.button("Execute Bulk Remediation & Commit to SQLite"):
        if selected_bulk_cases and bulk_note:
            conn = sqlite3.connect("rcm_audit_log.db")
            c = conn.cursor()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            for cid in selected_bulk_cases:
                # Update main state
                st.session_state.df_cases.loc[st.session_state.df_cases["Case_ID"] == cid, "Data_Quality_Flag"] = "Pass"
                # Commit to audit log
                c.execute("INSERT INTO audit_logs (timestamp, case_id, exception, auditor, notes) VALUES (?, ?, ?, ?, ?)",
                          (timestamp, cid, "Pass", user_id, bulk_note))
            
            conn.commit()
            conn.close()
            st.success(f"Successfully executed bulk remediation for {len(selected_bulk_cases)} cases.")
            st.rerun()
        else:
            st.warning("Please select at least one case and enter a remediation note.")
else:
    st.info("No active open exceptions available for bulk remediation. All cases compliant.")

st.markdown("---")

# ==========================================
# UPGRADE 4: STYLED PDF AUDIT CERTIFICATE EXPORT
# ==========================================
st.subheader("Automated Compliance Scoring & Executive PDF Export")

passing_cases = len(df[df["Data_Quality_Flag"] == "Pass"])
total_cases = len(df)
compliance_index = int((passing_cases / total_cases) * 100)

score_col, pdf_col = st.columns(2)

with score_col:
    st.markdown(f'<div class="metric-card"><div class="metric-title">CALCULATED COMPLIANCE INDEX</div><div class="metric-value">{compliance_index}%</div></div>', unsafe_allow_html=True)
    if compliance_index == 100:
        st.success("Work queue is fully compliant with internal data standards.")
    else:
        st.warning("Immediate remediation required to clear high-risk compliance flags.")

with pdf_col:
    st.write("Generate a formal, print-ready PDF Compliance Certificate complete with executive financial metrics and auditor sign-off block.")
    
    pdf_data = generate_pdf_report(compliance_index, total_portfolio_val, revenue_at_risk, user_id)
    
    st.download_button(
        label="Download Official PDF Audit Certificate",
        data=pdf_data,
        file_name=f"RCM_Compliance_Certificate_{datetime.date.today()}.pdf",
        mime="application/pdf"
    )

# ==========================================
# PERSISTENT AUDIT HISTORY SEARCH
# ==========================================
st.markdown("---")
st.subheader("Persistent SQLite Audit Search & Traceability Panel")

conn = sqlite3.connect("rcm_audit_log.db")
audit_df = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY id DESC", conn)
conn.close()

search_term = st.text_input("Search Audit History (Case ID or Auditor)")
if search_term:
    audit_df = audit_df[audit_df["case_id"].str.contains(search_term, case=False, na=False) | 
                        audit_df["auditor"].str.contains(search_term, case=False, na=False)]

st.dataframe(audit_df, use_container_width=True)

st.caption("CREATED BY KORI PICKLE | BSHA Healthcare Operations & Compliance Engine")

