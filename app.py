import sqlite3
import pandas as pd
import requests
import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="RCM Compliance & Work-Queue Intelligence Engine",
    page_icon="🏥",
    layout="wide",
)

VOLS_ORANGE = "#FF8200"
WHITE = "#FFFFFF"
BLACK = "#000000"

# Unified Custom Styling Configuration
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    .stApp {{
        background-color: {WHITE};
        color: {BLACK};
        font-family: 'Inter', sans-serif !important;
    }}
    
    [data-testid="stSidebar"] {{
        background-color: {WHITE};
        border-right: 2px solid {VOLS_ORANGE};
        color: {BLACK};
        font-family: 'Inter', sans-serif !important;
    }}

    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] span {{
        color: {VOLS_ORANGE} !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
    }}

    h1, h2, h3, h4, h5, h6, .editorial-header {{
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        color: {BLACK} !important;
        letter-spacing: -0.01em;
    }}

    /* Streamlit Native Metric Cards & Responsive Mobile View */
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {{
        color: {VOLS_ORANGE} !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
    }}
    
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] div {{
        color: {BLACK} !important;
        font-weight: 800 !important;
        font-size: 1.35rem !important;
        white-space: nowrap !important;
    }}

    /* Form Fields & High-Contrast Labels */
    label, .stSelectbox label, .stTextInput label, .stTextArea label, .stCheckbox label {{
        color: {VOLS_ORANGE} !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        font-family: 'Inter', sans-serif !important;
    }}

    input, textarea, select, [data-baseweb="select"] div, [data-baseweb="input"] div {{
        background-color: {WHITE} !important;
        color: {BLACK} !important;
        border: 1px solid {VOLS_ORANGE} !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
    }}

    .stTextInput input:focus, .stTextArea textarea:focus {{
        border-color: {VOLS_ORANGE} !important;
        box-shadow: 0 0 0 1px {VOLS_ORANGE} !important;
    }}

    /* Tabs Styling */
    button[data-baseweb="tab"] p {{
        color: {BLACK} !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
    }}
    button[aria-selected="true"] p {{
        color: {VOLS_ORANGE} !important;
        font-weight: 700 !important;
    }}
    div[data-baseweb="tab-highlight"] {{
        background-color: {VOLS_ORANGE} !important;
    }}

    /* Code & Tag Badges */
    code, .stMarkdown code, span[data-baseweb="tag"] {{
        color: {VOLS_ORANGE} !important;
        background-color: {BLACK} !important;
        border: 1px solid {VOLS_ORANGE} !important;
        padding: 3px 8px !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
    }}

    /* Custom Metric Cards */
    .metric-card {{
        background-color: {WHITE};
        padding: 16px;
        border-radius: 6px;
        border: 1.5px solid {VOLS_ORANGE};
        border-left: 6px solid {VOLS_ORANGE};
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        margin-bottom: 10px;
    }}

    .metric-card small {{
        color: {VOLS_ORANGE} !important;
        font-weight: 700 !important;
        font-size: 0.8rem !important;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }}

    .metric-card h2, .metric-card h3 {{
        color: {BLACK} !important;
        font-weight: 800 !important;
        margin: 4px 0 0 0 !important;
    }}

    .sidebar-session-box {{
        background-color: {WHITE};
        border: 1px solid {VOLS_ORANGE};
        border-left: 4px solid {VOLS_ORANGE};
        padding: 12px;
        border-radius: 4px;
        color: {BLACK};
        margin-top: 10px;
        font-family: 'Inter', sans-serif !important;
    }}

    /* Buttons */
    .stButton button, .stDownloadButton button {{
        background-color: {WHITE} !important;
        border: 1.5px solid {VOLS_ORANGE} !important;
        color: {BLACK} !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        border-radius: 4px !important;
    }}
    
    .stButton button:hover, .stDownloadButton button:hover {{
        background-color: {VOLS_ORANGE} !important;
        color: {WHITE} !important;
        border-color: {VOLS_ORANGE} !important;
    }}

    /* Dataframes & Chart Container Overrides */
    [data-testid="stDataFrame"] {{
        border: 1px solid {VOLS_ORANGE} !important;
        border-radius: 6px;
    }}

    /* Suppress chart touch tooltip artifacts on touch devices */
    .svg-container .hoverlayer {{
        pointer-events: none !important;
    }}
    </style>
""",
    unsafe_allow_html=True,
)


def vols_alert(message, icon="🟠"):
    st.markdown(
        f"""
        <div style="background-color: {WHITE}; border: 1px solid {VOLS_ORANGE}; border-left: 5px solid {VOLS_ORANGE}; color: {BLACK}; padding: 14px; border-radius: 4px; margin-bottom: 16px; font-family: 'Inter', sans-serif; font-size: 0.95rem; font-weight: 500;">
            {icon} {message}
        </div>
        """,
        unsafe_allow_html=True,
    )


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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS export_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user TEXT,
            export_type TEXT,
            row_count INTEGER
        )
    """)
    cursor.execute("""
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


st.sidebar.markdown("Enterprise Governance")
user_role = st.sidebar.selectbox(
    "Select Access Role", ["Junior Auditor", "Compliance Manager", "System Admin"]
)
current_user = st.sidebar.text_input(
    "User Identifier", "K. Pickle, BSHA Compliance"
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"""
    <div class="sidebar-session-box">
        <small style="color: {VOLS_ORANGE}; font-weight: 700;">ACTIVE SESSION</small><br>
        <strong>Tier:</strong> {user_role}
    </div>
""",
    unsafe_allow_html=True,
)

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
    "Claim_Value": [8500.00, 12000.00, 4500.00, 25000.00, 20000.00],
}
df = pd.DataFrame(data)

conn = sqlite3.connect(DB_NAME)
audit_history_df = pd.read_sql_query("SELECT * FROM audit_log", conn)
conn.close()

if not audit_history_df.empty:
    passed_cases = audit_history_df["case_id"].unique()
    df.loc[df["Case_ID"].isin(passed_cases), "Data_Quality_Flag"] = "Pass"

# Calculate dynamic financial metrics
total_financial_exposure = df["Claim_Value"].sum()
revenue_at_risk = df[df["Data_Quality_Flag"] != "Pass"]["Claim_Value"].sum()
critical_revenue_risk = df[df["Risk_Level"] == "Critical"]["Claim_Value"].sum()
exceptions_count = len(df[df["Data_Quality_Flag"] != "Pass"])
passed_count = len(df[df["Data_Quality_Flag"] == "Pass"])
compliance_index = int((passed_count / len(df)) * 100) if len(df) > 0 else 0


tab1, tab2, tab3 = st.tabs(
    ["Dashboard & Inspector", "Case Notes Stream", "Review & Attestation Guide"]
)

with tab1:
    st.markdown(
        "<h1 style='font-size: 2.5rem; margin-bottom: 0px;'>RCM Compliance &"
        " Work-Queue Intelligence Engine</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='font-size: 1.05rem; color: {BLACK}; margin-top: 8px;"
        " margin-bottom: 30px;'>Enterprise Portfolio Artifact: RBAC, SQLite"
        " Persistence, Webhook Alerting, and Historical Audit Search.</p>",
        unsafe_allow_html=True,
    )

    st.subheader("Financial Exposure & Executive Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Portfolio Value",
            value=f"${total_financial_exposure:,.2f}",
            help="Total claim value of all active cases in queue.",
        )

    with col2:
        st.metric(
            label="Revenue at Risk (Exceptions)",
            value=f"${revenue_at_risk:,.2f}",
            delta=f"{exceptions_count} Open Flags",
            delta_color="inverse",
            help="Dollar value tied up in cases with un-remediated compliance flags.",
        )

    with col3:
        st.metric(
            label="Critical Financial Risk",
            value=f"${critical_revenue_risk:,.2f}",
            help="Total dollar value tied up in Critical risk level cases.",
        )

    with col4:
        st.metric(
            label="Active Exception Flags",
            value=exceptions_count,
        )

    st.divider()
    # Executive Portfolio Snapshot integrated properly
    st.markdown("### Executive Portfolio Snapshot")
    snap_col1, snap_col2, snap_col3 = st.columns(3)

    with snap_col1:
        st.metric(
            label="Overall Compliance Index",
            value=f"{compliance_index}%",
            delta=f"{compliance_index - 80}% from Goal (80%)",
            help="Target index for 'Grade A' status is 80% or higher.",
        )

    with snap_col2:
        st.metric(
            label="Critical Financial Risk",
            value=f"${critical_revenue_risk:,.2f}",
            delta=f"{len(df[df['Risk_Level'] == 'Critical'])} Critical Cases",
            delta_color="inverse",
            help="Dollar value tied specifically to Critical risk cases.",
        )

    with snap_col3:
        st.metric(
            label="Portfolio Health Status",
            value="Grade: C",
            help="Immediate remediation required to clear flags.",
        )

    st.markdown("---")

    st.markdown("### Active Work Queue & Data Quality Exceptions")
    
    df_display = df.copy()
    df_display["Claim_Value"] = df_display["Claim_Value"].apply(
        lambda x: f"${x:,.2f}"
    )
    st.dataframe(df_display, use_container_width=True)

    # Dashboard Visual Analytics using base df (fixed logic inside)
    st.markdown("### Dashboard Visual Analytics (Filtered Data)")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("Status Distribution (Filtered Cases)")
        # In a real sync scenario, you would filter 'df' based on inputs before this. 
        # For now, using base df for charts to load until filters are implemented later in script.
        status_counts = df["Status"].value_counts()
        st.bar_chart(status_counts, color=VOLS_ORANGE)

    with chart_col2:
        st.markdown("Aging Breakdown (Filtered Cases)")
        st.bar_chart(
            df.set_index("Case_ID")["Days_Pending"], color=VOLS_ORANGE
        )

    st.markdown("---")

    st.markdown("### Interactive Case Detail Inspector")
    selected_inspect_case = st.selectbox(
        "Select Case ID to Review", df["Case_ID"], key="inspector_select"
    )
    inspect_row = df.loc[df["Case_ID"] == selected_inspect_case].iloc[0]

    insp_col1, insp_col2, insp_col3, insp_col4 = st.columns(4)
    with insp_col1:
        st.markdown(
            f"<div class='metric-card'><small>CURRENT STATUS</small>"
            f"<h3 style='color:{BLACK}!important; margin:4px 0 0 0;'>{inspect_row['Status']}</h3></div>",
            unsafe_allow_html=True,
        )
    with insp_col2:
        st.markdown(
            f"<div class='metric-card'><small>RISK LEVEL</small>"
            f"<h3 style='color:{BLACK}!important; margin:4px 0 0 0;'>{inspect_row['Risk_Level']}</h3></div>",
            unsafe_allow_html=True,
        )
    with insp_col3:
        st.markdown(
            f"<div class='metric-card'><small>DAYS PENDING</small>"
            f"<h3 style='color:{BLACK}!important; margin:4px 0 0 0;'>{inspect_row['Days_Pending']}</h3></div>",
            unsafe_allow_html=True,
        )
    with insp_col4:
        st.markdown(
            f"<div class='metric-card'><small>CLAIM VALUE</small>"
            f"<h3 style='color:{BLACK}!important; margin:4px 0 0 0;'>${inspect_row['Claim_Value']:,.2f}</h3></div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"Data Quality Flag Status for {selected_inspect_case}:"
        f" `{inspect_row['Data_Quality_Flag']}`"
    )

    vols_alert("Boundary Notice: This tool is built strictly for educational workflow simulation and does not contain PHI.")

    st.markdown("---")

    st.markdown("### Queue Health & Export Controls")
    csv_data = df_display.to_csv(index=False).encode("utf-8")

    col_qh1, col_qh2 = st.columns(2)
    with col_qh1:
        st.markdown(
            f"<div class='metric-card'><small>OVERALL QUEUE COMPLIANCE HEALTH</small>"
            f"<h2 style='color:{BLACK}!important; margin:4px 0 0 0;'>{compliance_index}%</h2>"
            f"<p style='color:{VOLS_ORANGE}; margin:5px 0 0 0; font-weight:600; font-size:0.85rem;'>🟠 {passed_count} of {len(df)} passing</p></div>",
            unsafe_allow_html=True,
        )
    with col_qh2:
        if user_role in ["Compliance Manager", "System Admin"]:
            if st.download_button(
                "Download Filtered Dataset as CSV",
                csv_data,
                "rcm_filtered_queue.csv",
                "text/csv",
            ):
                log_export_to_db(current_user, "Filtered Dataset CSV", len(df))
                vols_alert("Export logged to SQLite successfully!")
        else:
            vols_alert("Export controls restricted to Compliance Managers and System Admins.")

    st.markdown("---")

    st.markdown("### Risk Level Breakdown & Audit Summary")
    risk_summary_df = (
        df["Risk_Level"]
        .value_counts()
        .reset_index(name="Count")
        .rename(columns={"index": "Risk_Level"})
    )
    st.dataframe(risk_summary_df, use_container_width=True)
    risk_csv = risk_summary_df.to_csv(index=False).encode("utf-8")
    if st.download_button(
        "Download Risk Audit Summary",
        risk_csv,
        "rcm_risk_audit_summary.csv",
        "text/csv",
    ):
        log_export_to_db(current_user, "Risk Audit Summary CSV", len(risk_summary_df))

    st.markdown("---")

    st.markdown("### Aging Breakdown Summary")
    aging_df = (
        df_display[["Case_ID", "Days_Pending", "Risk_Level", "Claim_Value"]]
        .sort_values(by="Days_Pending", ascending=False)
        .reset_index(drop=True)
    )
    st.dataframe(aging_df, use_container_width=True)
    aging_csv = aging_df.to_csv(index=False).encode("utf-8")
    if st.download_button(
        "Download Aging Breakdown CSV",
        aging_csv,
        "rcm_aging_breakdown.csv",
        "text/csv",
    ):
        log_export_to_db(current_user, "Aging Breakdown CSV", len(aging_df))

    st.markdown("---")

    st.markdown("### Queue Analytics Summary Metric")
    tot_days = int(df["Days_Pending"].sum())
    avg_days = round(float(df["Days_Pending"].mean()), 1)
    qmetric_col1, qmetric_col2 = st.columns(2)
    with qmetric_col1:
        st.markdown(
            f"<div class='metric-card'><small>TOTAL CUMULATIVE DAYS PENDING</small>"
            f"<h2 style='color:{BLACK}!important; margin:4px 0 0 0;'>{tot_days} Days</h2></div>",
            unsafe_allow_html=True,
        )
    with qmetric_col2:
        st.markdown(
            f"<div class='metric-card'><small>AVERAGE DAYS PENDING PER CASE</small>"
            f"<h2 style='color:{BLACK}!important; margin:4px 0 0 0;'>{avg_days} Days</h2></div>",
            unsafe_allow_html=True,
        )

    st.markdown("### Compliance SLA Performance & Resolution Tracking")
    sla_df = (
        df.groupby("Status")
        .agg(
            Total_Cases=("Case_ID", "count"),
            Avg_Days_Pending=("Days_Pending", "mean"),
            Total_Claim_Value=("Claim_Value", "sum")
        )
        .reset_index()
    )
    sla_df_display = sla_df.copy()
    sla_df_display["Total_Claim_Value"] = sla_df_display["Total_Claim_Value"].apply(lambda x: f"${x:,.2f}")
    st.dataframe(sla_df_display, use_container_width=True)
    sla_csv = sla_df_display.to_csv(index=False).encode("utf-8")
    if st.download_button(
        "Download SLA Compliance Report",
        sla_csv,
        "rcm_sla_compliance_report.csv",
        "text/csv",
    ):
        log_export_to_db(current_user, "SLA Compliance Report CSV", len(sla_df))

    st.markdown("---")

    st.markdown("### Data Quality Exception Audit & Resolution Log")
    dq_summary = (
        df[df["Data_Quality_Flag"] != "Pass"]
        .groupby("Data_Quality_Flag")
        .agg(
            Affected_Cases=("Case_ID", "count"),
            Total_Value_At_Risk=("Claim_Value", "sum"),
            Case_List=("Case_ID", lambda x: ", ".join(x)),
        )
        .reset_index()
    )
    dq_summary_display = dq_summary.copy()
    dq_summary_display["Total_Value_At_Risk"] = dq_summary_display["Total_Value_At_Risk"].apply(lambda x: f"${x:,.2f}")
    st.dataframe(dq_summary_display, use_container_width=True)
    dq_csv = dq_summary_display.to_csv(index=False).encode("utf-8")
    if st.download_button(
        "Download DQ Exception Audit Log",
        dq_csv,
        "rcm_dq_exception_audit.csv",
        "text/csv",
    ):
        log_export_to_db(current_user, "DQ Exception Audit Log CSV", len(dq_summary))

    st.markdown("---")

    # Interactive Queue Filter Panel integrated properly
    st.markdown("### Interactive Queue Filter Panel")

    # 1. Create a row of multiselect filters
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        selected_statuses = st.multiselect(
            "Filter by Status",
            options=df["Status"].unique(),
            default=df["Status"].unique(),
        )

    with filter_col2:
        selected_risks = st.multiselect(
            "Filter by Risk Level",
            options=df["Risk_Level"].unique(),
            default=df["Risk_Level"].unique(),
        )

    with filter_col3:
        selected_flags = st.multiselect(
            "Filter by Data Quality Flag",
            options=df["Data_Quality_Flag"].unique(),
            default=df["Data_Quality_Flag"].unique(),
        )

    # 2. Apply all filters to the DataFrame
    filtered_results_df = df[
        (df["Status"].isin(selected_statuses))
        & (df["Risk_Level"].isin(selected_risks))
        & (df["Data_Quality_Flag"].isin(selected_flags))
    ]
    
    # Pre-format the display DF for currency
    filtered_results_display_df = filtered_results_df.copy()
    filtered_results_display_df["Claim_Value"] = filtered_results_display_df["Claim_Value"].apply(lambda x: f"${x:,.2f}")

    # 3. Show dynamic results alert
    if len(filtered_results_display_df) == 0:
        vols_alert(
            "No active cases match your selected filter criteria.", icon="🔍"
        )
    else:
        st.dataframe(filtered_results_display_df, use_container_width=True)
        vols_alert(
            f"Displaying {len(filtered_results_display_df)} active compliance cases based on selected filters."
        )

    st.markdown("---")

    st.markdown("### Compliance Audit Export Hub & Full Snapshot")
    full_snapshot_csv = df_display.to_csv(index=False).encode("utf-8")
    if st.download_button(
        "Download Complete Filtered Queue Snapshot (CSV)",
        full_snapshot_csv,
        "rcm_complete_queue_snapshot.csv",
        "text/csv",
    ):
        log_export_to_db(current_user, "Complete Queue Snapshot CSV", len(df))

    st.markdown("---")

    st.markdown("### Executive Compliance Summary & Print Hub")
    exec_summary_text = f"""
==================================================
RCM COMPLIANCE INTELLIGENCE ENGINE - EXECUTIVE REPORT
==================================================
Generated Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Reviewer Authority: {current_user} ({user_role})
--------------------------------------------------
Scope Analyzed: {len(df)} Active Work-Queue Cases
Total Portfolio Value: ${total_financial_exposure:,.2f}
Revenue at Risk (Exceptions): ${revenue_at_risk:,.2f}
Critical Financial Exposure: ${critical_revenue_risk:,.2f}
Critical Risk Exposure: {len(df[df['Risk_Level'] == 'Critical'])} Cases Requiring Immediate Escalation
Data Quality Exceptions: {len(df[df['Data_Quality_Flag'] != 'Pass'])} Active Compliance Flags
Average Case Aging: {avg_days} Days Pending
Calculated Compliance Index: {compliance_index}%
==================================================
"""
    st.text_area(
        "Copy Executive Summary Report", exec_summary_text.strip(), height=200
    )
    if st.download_button(
        "Download Executive Summary (.txt)",
        exec_summary_text.strip(),
        "rcm_executive_summary.txt",
        "text/plain",
    ):
        log_export_to_db(current_user, "Executive Summary TXT", 1)

    st.markdown("---")

    # Bulk Remediation Hub integrated properly before Persistent Logbook
    st.markdown("### Bulk Remediation Hub")
    vols_alert(
        "Select multiple cases from the table below to resolve repetitive flags simultaneously."
    )

    # Use multiselect specifically designed for bulk actions
    bulk_choices = df[df["Data_Quality_Flag"] != "Pass"]["Case_ID"].tolist()
    selected_bulk_cases = st.multiselect(
        "Select Case IDs for Bulk Audit Sign-Off",
        bulk_choices,
        help="Select multiple cases flagged with Missing Resolution Date/Missing closure evidence.",
    )

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        bulk_remediation_note = st.text_input(
            "Enter Bulk Remediation Note (Applied to ALL selected cases)"
        )

    with col_b2:
        target_data_quality_state = st.selectbox(
            "Set Final Data Quality State to:", ["Pass"], key="bulk_state_select"
        )

    if st.button("Execute Bulk Remediation & Commit to SQLite"):
        if user_role not in ["Compliance Manager", "System Admin"]:
            vols_alert(
                "Access Denied: Bulk Remediation requiere permisos de Compliance Manager o System Admin."
            )
        elif not selected_bulk_cases:
            vols_alert("Error: No se han seleccionado casos para la remediación en masa.")
        elif not bulk_remediation_note:
            vols_alert("Error: La nota de remediación en masa no puede estar vacía.")
        else:
            # Commit each selected case one at a time within a SQLite transaction
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            for case in selected_bulk_cases:
                # Need to find the target exception for logging
                target_exception_row = df.loc[df["Case_ID"] == case]
                if not target_exception_row.empty:
                    target_exception = target_exception_row["Data_Quality_Flag"].values[0]
                    cursor.execute(
                        """
                        INSERT INTO audit_log (timestamp, case_id, exception, auditor, remediation_note, role)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            case,
                            target_exception,
                            current_user,
                            f"BULK ACTION: {bulk_remediation_note}",
                            user_role,
                        ),
                    )
            conn.commit()
            conn.close()
            vols_alert(
                f"Successfully executed bulk remediation for {len(selected_bulk_cases)} cases. Database updated."
            )
            st.rerun()

    st.markdown("---")

    st.markdown(
        "### Persistent SQLite Audit & Remediation Logbook & Live State Update"
    )

    selected_case = st.selectbox(
        "Select Case ID for Persistent SQLite Audit Sign-Off",
        df["Case_ID"],
        key="remediation_case_select",
    )
    target_exception = df.loc[df["Case_ID"] == selected_case][
        "Data_Quality_Flag"
    ].values[0]
    st.markdown(f"Target Case Exception: `{target_exception}`")

    remediation_note = st.text_input(
        "Enter Official Audit Remediation Note",
        "e.g., Verified missing documentation and closed loop.",
    )
    auditor_name = st.text_input(
        "Compliance Auditor / Reviewer Name",
        current_user,
        key="remediation_auditor",
    )

    if st.button("Commit Remediation to Database & Update Queue State to 'Pass'"):
        if user_role == "Junior Auditor":
            vols_alert("Access Denied: Junior Auditors do not have permission to execute queue state overrides. Contact a Compliance Manager or System Admin.")
        elif not remediation_note:
             vols_alert("Error: Remediation note cannot be empty.")
        else:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_log (timestamp, case_id, exception, auditor, remediation_note, role)
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
            vols_alert(f"Remediation for {selected_case} committed to SQLite database successfully!")
            st.rerun()

    st.markdown("---")

    st.markdown("### Historical Audit Search & Traceability Panel")
    st.markdown(
        "Query past immutable audit decisions and state change histories for regulatory compliance reviews."
    )

    search_col1, search_col2 = st.columns(2)
    with search_col1:
        audit_search_term = st.text_input(
            "Search Audit History (Case ID or Auditor)",
            "",
            key="audit_history_search",
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

    st.markdown("Official SQLite Audit Trail Records")
    if not audit_df.empty:
        st.dataframe(audit_df, use_container_width=True)
        audit_csv = audit_df.to_csv(index=False).encode("utf-8")
        if st.download_button(
            "Download Official SQLite Audit Log (.csv)",
            audit_csv,
            "rcm_audit_log_history.csv",
            "text/csv",
        ):
            log_export_to_db(current_user, "Audit Log History CSV", len(audit_df))
    else:
        vols_alert("No audit records found matching criteria. Commit a remediation above to populate the database.")

    if export_log_view:
        st.markdown("Immutable Database Export History")
        export_df = pd.read_sql_query(
            "SELECT * FROM export_history ORDER BY timestamp DESC", conn
        )
        st.dataframe(export_df, use_container_width=True)

    conn.close()

    st.markdown("---")

    st.markdown("### Automated Compliance Alert & Webhook Dispatcher")
    st.markdown(
        "Instantly transmit executive summaries and critical exception flags via webhook simulation or SMTP notification."
    )

    if user_role in ["Compliance Manager", "System Admin"]:
        webhook_url = st.text_input(
            "Webhook Endpoint URL (Slack / Teams / Custom)",
            "https://webhook.site/your-unique-endpoint",
        )
        officer_email = st.text_input(
            "Compliance Officer Email",
            "koripickle1101@gmail.com",
            key="webhook_email",
        )

        col_alert1, col_alert2 = st.columns(2)
        with col_alert1:
            if st.button("Dispatch Webhook Executive Alert"):
                try:
                    payload = {
                        "event": "RCM_COMPLIANCE_ALERT",
                        "total_cases": len(df),
                        "total_portfolio_value": total_financial_exposure,
                        "revenue_at_risk": revenue_at_risk,
                        "critical_risks": int(len(df[df["Risk_Level"] == "Critical"])),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    response = requests.post(webhook_url, json=payload, timeout=5)
                    vols_alert(f"Webhook alert successfully dispatched! Response status code: {response.status_code}")
                except Exception as e:
                    vols_alert(f"Webhook dispatch failed: {e}")

        with col_alert2:
            if st.button("Simulate SMTP Email Dispatch"):
                vols_alert(f"Simulated email successfully transmitted to {officer_email} with attached Executive Compliance Summary!")
    else:
        vols_alert("Webhook and alerting functions are restricted to Compliance Managers and System Admins.")

    st.markdown("---")

    st.markdown("### Automated Compliance Scoring & Executive Badge")
    score_col1, score_col2 = st.columns(2)

    with score_col1:
        grade_text = "Grade: A (Fully Compliant)" if compliance_index >= 80 else "Grade: C (Action Required)"
        st.markdown(
            f"<div class='metric-card'><small>CALCULATED COMPLIANCE INDEX</small>"
            f"<h2 style='color:{BLACK}!important; margin:4px 0 0 0;'>{compliance_index}%</h2>"
            f"<p style='color:{BLACK}; margin:5px 0 0 0; font-weight:600;'>{grade_text}</p></div>",
            unsafe_allow_html=True
        )

    with score_col2:
        st.markdown("Executive Governance Status:")
        if compliance_index >= 80:
            vols_alert("Work queue is fully compliant with internal data standards.")
        else:
            vols_alert("Immediate remediation required to clear high-risk compliance flags.")

with tab2:
    st.subheader("📝 Case Notes Stream")
    st.write("Live operational notes and audit documentation stream.")

    note_case = st.selectbox(
        "Select Case ID for Annotation", df["Case_ID"], key="note_case_select"
    )
    new_note = st.text_area("Add Case Annotation / Note")

    if st.button("Save Note to Database"):
        if not new_note.strip():
            vols_alert("Note content cannot be empty.")
        else:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO case_notes (timestamp, case_id, author, note)
                VALUES (?, ?, ?, ?)
            """,
                (
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    note_case,
                    current_user,
                    new_note,
                ),
            )
            conn.commit()
            conn.close()
            vols_alert("Case note saved successfully!")
            st.rerun()

    st.markdown("### Existing Case Notes Timeline")
    conn = sqlite3.connect(DB_NAME)
    notes_df = pd.read_sql_query(
        "SELECT * FROM case_notes ORDER BY timestamp DESC", conn
    )
    conn.close()

    if not notes_df.empty:
        st.dataframe(notes_df, use_container_width=True)
    else:
        vols_alert("No case notes recorded yet.")

with tab3:
    st.subheader("📋 Review & Attestation Guide")
    st.write(
        "Standard Operating Procedures (SOP) and operational definitions for data quality exception flags and compliance attestations."
    )
    st.divider()

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown(
            f"""
            <div class="metric-card" style="margin-bottom: 15px;">
                <h4 style="color:{BLACK}!important; margin:0 0 8px 0;">Missing Resolution Date</h4>
                <p style="margin:0 0 8px 0; font-size:0.95rem;"><strong>Definition:</strong> Case resolution status is marked closed or approved without a validated timestamp.</p>
                <p style="margin:0; font-size:0.85rem; color:{VOLS_ORANGE};"><strong>Remediation Protocol:</strong> Cross-reference clearinghouse logs and record the exact final adjudication date.</p>
            </div>
            <div class="metric-card" style="margin-bottom: 15px;">
                <h4 style="color:{BLACK}!important; margin:0 0 8px 0;">Missing Closure Evidence</h4>
                <p style="margin:0 0 8px 0; font-size:0.95rem;"><strong>Definition:</strong> Supporting documentation, payor EOB, or written authorization is absent from the file.</p>
                <p style="margin:0; font-size:0.85rem; color:{VOLS_ORANGE};"><strong>Remediation Protocol:</strong> Attach proof of payment or final appeal decision before committing state change to 'Pass'.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_g2:
        st.markdown(
            f"""
            <div class="metric-card" style="margin-bottom: 15px;">
                <h4 style="color:{BLACK}!important; margin:0 0 8px 0;">Missing Owner</h4>
                <p style="margin:0 0 8px 0; font-size:0.95rem;"><strong>Definition:</strong> No primary analyst or compliance specialist is assigned accountability for the work item.</p>
                <p style="margin:0; font-size:0.85rem; color:{VOLS_ORANGE};"><strong>Remediation Protocol:</strong> Assign an active staff member in the work-queue manager.</p>
            </div>
            <div class="metric-card" style="margin-bottom: 15px;">
                <h4 style="color:{BLACK}!important; margin:0 0 8px 0;">Missing Human Review Evidence</h4>
                <p style="margin:0 0 8px 0; font-size:0.95rem;"><strong>Definition:</strong> Automated claim/authorization decision lacks required secondary sign-off.</p>
                <p style="margin:0; font-size:0.85rem; color:{VOLS_ORANGE};"><strong>Remediation Protocol:</strong> Require Senior Auditor or Compliance Manager verification.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    st.subheader("🛡️ Enterprise Governance & Regulatory Attestation")
    vols_alert(
        "Attestation Clause: All remediation logs committed to the persistent database constitute an immutable audit trail subject to internal quality management system (QMS) standards.",
        icon="📜",
    )

st.divider()

st.markdown(
    "<h4 style='text-align: center;'>CREATED BY KORI PICKLE</h4>",
    unsafe_allow_html=True,
)

