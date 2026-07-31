import io
import datetime
import sqlite3
import requests
import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

st.set_page_config(
    page_title="RCM Compliance Intelligence Engine",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
    <style>
    .stApp, .main, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    h1, h2, h3, h4, h5, h6, p, label, span, .stMarkdown {
        color: #000000 !important;
    }

    span[data-baseweb="tag"] {
        background-color: #FF8200 !important;
        border: 1px solid #FF8200 !important;
        color: #FFFFFF !important;
    }

    span[data-baseweb="tag"] span,
    span[data-baseweb="tag"] svg {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
    }

    div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"],
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div,
    textarea, input {
        background-color: #FFFFFF !important;
        border: 2px solid #FF8200 !important;
        border-radius: 6px !important;
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
    }

    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea,
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] input {
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
        font-weight: 600 !important;
        background-color: #FFFFFF !important;
    }

    input::placeholder, textarea::placeholder {
        color: #666666 !important;
        -webkit-text-fill-color: #666666 !important;
    }

    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
        background-color: #FFFFFF !important;
        border: 1px solid #FF8200 !important;
    }
    li[role="option"] {
        color: #000000 !important;
        background-color: #FFFFFF !important;
    }
    li[role="option"]:hover, li[aria-selected="true"] {
        background-color: #FF8200 !important;
        color: #FFFFFF !important;
    }

    div[data-testid="stExpander"] {
        border: 1px solid #FF8200 !important;
        border-radius: 6px !important;
        overflow: hidden;
        background-color: #FFFFFF !important;
    }
    div[data-testid="stExpander"] details summary {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-bottom: 1px solid #FF8200 !important;
    }
    div[data-testid="stExpander"] details summary p {
        color: #000000 !important;
        font-weight: bold !important;
    }
    div[data-testid="stExpanderDetails"] {
        background-color: #FFFFFF !important;
        color: #111111 !important;
    }
    div[data-testid="stExpanderDetails"] p, 
    div[data-testid="stExpanderDetails"] li {
        color: #111111 !important;
    }

    /* Force all expander headers and containers to pure white background and dark text */
    details, summary, [data-testid="stExpander"] div, [data-testid="stExpanderDetails"] {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }

    .metric-card {
        background-color: #FFFFFF;
        border-left: 6px solid #FF8200;
        border-top: 1px solid #D0D0D0;
        border-right: 1px solid #D0D0D0;
        border-bottom: 1px solid #D0D0D0;
        padding: 16px;
        border-radius: 6px;
        margin-bottom: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .metric-title {
        color: #FF8200;
        font-size: 0.85rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #000000;
        margin-top: 4px;
        white-space: nowrap !important;
    }

    div.stButton > button, div.stDownloadButton > button {
        background-color: #FF8200 !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        border-radius: 6px !important;
        border: none !important;
        padding: 10px 18px !important;
        width: 100% !important;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background-color: #E67300 !important;
        color: #FFFFFF !important;
    }

    [data-testid="stDataFrame"], .stDataFrame, div[data-testid="stTable"] {
        border: 1px solid #FF8200 !important;
        border-radius: 6px !important;
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    [data-testid="stDataFrame"] th {
        background-color: #FF8200 !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
    }
    [data-testid="stDataFrame"] td {
        color: #111111 !important;
        background-color: #FFFFFF !important;
    }

    section[data-testid="stFileUploaderDropzone"],
    div[data-testid="stFileUploaderDropzone"] {
        background-color: #FF8200 !important;
        border: 2px dashed #FFFFFF !important;
        border-radius: 8px !important;
    }
    section[data-testid="stFileUploaderDropzone"] *,
    div[data-testid="stFileUploaderDropzone"] * {
        color: #FFFFFF !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

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

if "df_cases" not in st.session_state:
    st.session_state.df_cases = pd.DataFrame([
        {"Case_ID": "PAUTH-046", "Status": "Approved", "Risk_Level": "Moderate", "Days_Pending": 4, "Data_Quality_Flag": "Missing resolution date", "Claim_Value": 8500.00},
        {"Case_ID": "PAUTH-047", "Status": "Closed", "Risk_Level": "High", "Days_Pending": 9, "Data_Quality_Flag": "Missing closure evidence", "Claim_Value": 12000.00},
        {"Case_ID": "PAUTH-048", "Status": "Escalated", "Risk_Level": "Routine", "Days_Pending": 2, "Data_Quality_Flag": "Missing owner", "Claim_Value": 4500.00},
        {"Case_ID": "PAUTH-049", "Status": "Pending Review", "Risk_Level": "Critical", "Days_Pending": 6, "Data_Quality_Flag": "Missing human review evidence", "Claim_Value": 25000.00},
        {"Case_ID": "PAUTH-050", "Status": "Appeal Readiness", "Risk_Level": "Critical", "Days_Pending": 10, "Data_Quality_Flag": "Pass", "Claim_Value": 20000.00}
    ])

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
    
    meta_text = f"Generated Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>" \
                f"Reviewer Authority: {auditor_name}<br/>" \
                f"Governance Status: Official Executive Audit Sign-Off"
    story.append(Paragraph(meta_text, body_style))
    story.append(Spacer(1, 15))

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
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#FFFFFF")),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#FF8200")),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    story.append(Paragraph("Detailed Work Queue Audit Snapshot:", body_style))
    
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
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#FF8200")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#FF8200")),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]))
    story.append(t_cases)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

with st.sidebar:
    st.header("Governance & Data Controls")
    role = st.selectbox("Select Access Role", ["System Admin", "Compliance Manager", "Junior Auditor"])
    user_id = st.text_input("User Identifier", value="K. Pickle, BSHA Compliance")
    st.markdown("---")
    
    st.subheader("Data Ingestion & Controls")
    uploaded_file = st.file_uploader("Ingest Custom Claims (CSV)", type=["csv"])
    if uploaded_file is not None:
        try:
            custom_df = pd.read_csv(uploaded_file)
            st.session_state.df_cases = custom_df
            st.success("Custom dataset loaded successfully!")
        except Exception as e:
            st.error(f"Error loading CSV: {e}")

    st.markdown("---")
    
    st.write("Or Paste CSV Data Directly:")
    pasted_csv_text = st.text_area("Paste CSV rows here (Case_ID,Status,Risk_Level,Days_Pending,Data_Quality_Flag,Claim_Value)")
    
    if st.button("Parse and Load Pasted Data"):
        if pasted_csv_text:
            try:
                custom_df = pd.read_csv(io.StringIO(pasted_csv_text))
                st.session_state.df_cases = custom_df
                st.success("Pasted dataset parsed and loaded successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error parsing pasted text: {e}. Ensure format matches CSV headers.")
        else:
            st.warning("Please paste valid CSV text before parsing.")
            
    if st.button("Reset Queue to Default Sample Data"):
        st.session_state.df_cases = pd.DataFrame([
            {"Case_ID": "PAUTH-046", "Status": "Approved", "Risk_Level": "Moderate", "Days_Pending": 4, "Data_Quality_Flag": "Missing resolution date", "Claim_Value": 8500.00},
            {"Case_ID": "PAUTH-047", "Status": "Closed", "Risk_Level": "High", "Days_Pending": 9, "Data_Quality_Flag": "Missing closure evidence", "Claim_Value": 12000.00},
            {"Case_ID": "PAUTH-048", "Status": "Escalated", "Risk_Level": "Routine", "Days_Pending": 2, "Data_Quality_Flag": "Missing owner", "Claim_Value": 4500.00},
            {"Case_ID": "PAUTH-049", "Status": "Pending Review", "Risk_Level": "Critical", "Days_Pending": 6, "Data_Quality_Flag": "Missing human review evidence", "Claim_Value": 25000.00},
            {"Case_ID": "PAUTH-050", "Status": "Appeal Readiness", "Risk_Level": "Critical", "Days_Pending": 10, "Data_Quality_Flag": "Pass", "Claim_Value": 20000.00}
        ])
        st.rerun()

    st.markdown("---")
    st.markdown(f"Active Authority: {role}")

st.title("RCM Compliance & Work-Queue Intelligence Engine")
st.caption("Enterprise Portfolio Artifact: RBAC, SQLite Persistence, Webhook Alerting, and Historical Audit Search.")

with st.expander("Review & Attestation Standard Operating Guide", expanded=True):
    st.write("Compliance Review & Attestation Protocol")
    st.write("This intelligence engine provides real-time auditability and risk governance for Revenue Cycle Management (RCM) prior authorization queues and claims data quality.")
    
    st.write("1. Data Quality Exception Categories")
    st.write("Missing Resolution Date: Prior authorization case closed without timestamped clinical resolution.")
    st.write("Missing Closure Evidence: Lack of attached payer authorization notice or determination letter.")
    st.write("Missing Owner: Case assigned to an unallocated or terminated user ID in the EHR/RCM workflow.")
    st.write("Missing Human Review Evidence: High-dollar claim ($20,000+) processed via auto-adjudication without required compliance oversight.")
    st.write("Pass: Clean record meeting all corporate compliance criteria.")

    st.write("2. Standard Operating Procedures (SOP)")
    st.write("1. Filter Active Queue: Identify cases tagged with Critical or High financial exposure.")
    st.write("2. Inspect & Annotate: Select specific Case IDs in the Interactive Inspector to review details and log specific clinical annotations into SQLite.")
    st.write("3. Remediate Exceptions: Use the Bulk Remediation Hub or Single Sign-Off Panel to commit official compliance notes and update data flags to Pass.")
    st.write("4. Traceability: Verify sign-offs in the persistent SQLite Historical Audit Trail.")
    st.write("5. Executive Reporting: Dispatch real-time webhooks or export PDF audit certificates for governance reporting.")

st.markdown("---")

df = st.session_state.df_cases

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

passing_cases = len(df[df["Data_Quality_Flag"] == "Pass"])
total_cases = len(df)
compliance_index = int((passing_cases / total_cases) * 100) if total_cases > 0 else 0

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

st.subheader("Active Work Queue & Data Quality Exceptions")

f_col1, f_col2 = st.columns(2)
with f_col1:
    selected_risk = st.multiselect("Filter by Risk Level", options=df["Risk_Level"].unique(), default=df["Risk_Level"].unique())
with f_col2:
    selected_flag = st.multiselect("Filter by Data Quality Flag Status", options=df["Data_Quality_Flag"].unique(), default=df["Data_Quality_Flag"].unique())

filtered_df = df[(df["Risk_Level"].isin(selected_risk)) & (df["Data_Quality_Flag"].isin(selected_flag))]
st.dataframe(filtered_df, use_container_width=True)

ch1, ch2 = st.columns(2)
with ch1:
    fig_status = px.bar(
        filtered_df, x="Status", title="Status Distribution (Filtered Cases)",
        color_discrete_sequence=["#FF8200"]
    )
    fig_status.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font_color="#000000", margin=dict(t=30, b=10, l=10, r=10))
    st.plotly_chart(fig_status, use_container_width=True)

with ch2:
    fig_aging = px.bar(
        filtered_df, x="Case_ID", y="Days_Pending", title="Aging Breakdown (Filtered Cases)",
        color_discrete_sequence=["#FF8200"]
    )
    fig_aging.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font_color="#000000", margin=dict(t=30, b=10, l=10, r=10))
    st.plotly_chart(fig_aging, use_container_width=True)

st.markdown("---")

st.subheader("Interactive Case Detail Inspector & Annotation Log")
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

st.info(f"Data Quality Flag Status for {selected_case_id}: {case_row['Data_Quality_Flag']}")

n_col1, n_col2 = st.columns(2)
with n_col1:
    new_case_note = st.text_area(f"Add Audit Annotation Note for {selected_case_id}")
    if st.button(f"Save Annotation to SQLite for {selected_case_id}"):
        if new_case_note:
            conn = sqlite3.connect("rcm_audit_log.db")
            c = conn.cursor()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO case_notes (timestamp, case_id, author, note) VALUES (?, ?, ?, ?)",
                      (timestamp, selected_case_id, user_id, new_case_note))
            conn.commit()
            conn.close()
            st.success("Annotation logged!")
        else:
            st.warning("Please enter a note before saving.")

with n_col2:
    conn = sqlite3.connect("rcm_audit_log.db")
    notes_df = pd.read_sql_query("SELECT timestamp, author, note FROM case_notes WHERE case_id = ? ORDER BY id DESC", conn, params=(selected_case_id,))
    conn.close()
    st.write(f"Existing Case Notes ({len(notes_df)})")
    st.dataframe(notes_df, use_container_width=True)

st.markdown("---")

with st.expander("Add New Case / Claim Entry to Queue"):
    with st.form("add_case_form"):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            new_cid = st.text_input("New Case ID", value=f"PAUTH-0{len(df)+46}")
            new_status = st.selectbox("Status", ["Approved", "Closed", "Escalated", "Pending Review", "Appeal Readiness"])
        with fc2:
            new_risk = st.selectbox("Risk Level", ["Routine", "Moderate", "High", "Critical"])
            new_days = st.number_input("Days Pending", min_value=0, value=1)
        with fc3:
            new_flag = st.selectbox("Data Quality Flag", ["Pass", "Missing resolution date", "Missing closure evidence", "Missing owner", "Missing human review evidence"])
            new_val = st.number_input("Claim Value ($)", min_value=0.0, value=5000.0, step=500.0)
            
        submit_new_case = st.form_submit_button("Add Claim to Active Work Queue")
        if submit_new_case:
            new_row = pd.DataFrame([{"Case_ID": new_cid, "Status": new_status, "Risk_Level": new_risk, "Days_Pending": new_days, "Data_Quality_Flag": new_flag, "Claim_Value": new_val}])
            st.session_state.df_cases = pd.concat([st.session_state.df_cases, new_row], ignore_index=True)
            st.success(f"Case {new_cid} successfully added!")
            st.rerun()

st.markdown("---")

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
                st.session_state.df_cases.loc[st.session_state.df_cases["Case_ID"] == cid, "Data_Quality_Flag"] = "Pass"
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

st.subheader("Persistent SQLite Audit & Remediation Logbook & Live State Update")
rem_case_id = st.selectbox("Select Case ID for Persistent SQLite Audit Sign-Off", options=df["Case_ID"].tolist(), key="single_signoff_select")
target_row = df[df["Case_ID"] == rem_case_id].iloc[0]
st.write(f"Target Case Exception: {target_row['Data_Quality_Flag']}")

single_note = st.text_input("Enter Official Audit Remediation Note", placeholder="e.g., Verified missing documentation and closed loop.", key="single_note_input")
auditor_input = st.text_input("Compliance Auditor / Reviewer Name", value=user_id, key="auditor_name_input")

if st.button("Commit Remediation to Database & Update Queue State to Pass"):
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

st.subheader("Historical Audit Search & Traceability Panel")
conn = sqlite3.connect("rcm_audit_log.db")
audit_trail_df = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY id DESC", conn)
conn.close()

search_term = st.text_input("Search Audit History (Case ID or Auditor)")
if search_term:
    audit_display_df = audit_trail_df[audit_trail_df["case_id"].str.contains(search_term, case=False, na=False) | 
                                      audit_trail_df["auditor"].str.contains(search_term, case=False, na=False)]
else:
    audit_display_df = audit_trail_df

st.write("Official SQLite Audit Trail Records")
st.dataframe(audit_display_df, use_container_width=True)

if not audit_trail_df.empty:
    csv_data = audit_trail_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Full Audit Log (CSV)",
        data=csv_data,
        file_name="sqlite_audit_log_export.csv",
        mime="text/csv",
        key="download_audit_csv"
    )
else:
    st.info("No audit logs available for export.")

st.markdown("---")

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
                st.success(f"Webhook alert successfully dispatched! Status code: {res.status_code}")
            else:
                st.warning(f"Webhook dispatched with status code: {res.status_code}")
        except Exception as e:
            st.error(f"Webhook dispatch failed: {e}")

with w_col2:
    if st.button("Simulate SMTP Email Dispatch"):
        st.success(f"Simulated email successfully transmitted to {email_recipient} with attached Executive Compliance Summary!")

st.markdown("---")

st.subheader("Automated Compliance Scoring & Executive PDF Export")

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

score_col, pdf_col = st.columns(2)

with score_col:
    st.markdown(f'<div class="metric-card"><div class="metric-title">CALCULATED COMPLIANCE INDEX</div><div class="metric-value">{compliance_index}%</div></div>', unsafe_allow_html=True)
    if compliance_index == 100:
        st.success("Work queue is fully compliant with internal data standards.")
    else:
        st.warning("Immediate remediation required to clear high-risk compliance flags.")
    
    st.download_button(
        label="Download Executive Summary (.txt)",
        data=summary_text,
        file_name="rcm_executive_summary.txt",
        mime="text/plain"
    )

with pdf_col:
    st.write("Generate a formal, print-ready PDF Compliance Certificate complete with executive financial metrics and auditor sign-off block.")
    
    if REPORTLAB_AVAILABLE:
        pdf_data = generate_pdf_report(compliance_index, total_portfolio_val, revenue_at_risk, user_id)
        
        st.download_button(
            label="Download Official PDF Audit Certificate",
            data=pdf_data,
            file_name=f"RCM_Compliance_Certificate_{datetime.date.today()}.pdf",
            mime="application/pdf"
        )
    else:
        st.error("ReportLab library is not installed. Please add reportlab to requirements.txt.")

st.caption("CREATED BY KORI PICKLE | BSHA Healthcare Operations & Compliance Engine")

