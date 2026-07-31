import streamlit as st

# --- PAGE CONFIGURATION & THEME ---
st.set_page_config(
    page_title="RCM Compliance & Work-Queue Intelligence Engine",
    page_icon="🏥",
    layout="wide",
)

# Brand Color Palette: Tennessee Volunteers Theme
VOLS_ORANGE = "#FF8200"
WHITE = "#FFFFFF"
BLACK = "#000000"
WARM_GRAY = "#F4F5F7"
DARK_GRAY = "#222222"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@400;500;600&family=Great+Vibes&display=swap');

    .stApp {{
        background-color: {WHITE};
        color: {BLACK};
        font-family: 'Plus Jakarta Sans', sans-serif;
    }}
    
    h1, h2, h3, .editorial-header {{
        font-family: 'Playfair Display', serif !important;
        color: {BLACK} !important;
        letter-spacing: -0.02em;
    }}

    .metric-card {{
        background-color: {WARM_GRAY};
        padding: 24px;
        border-radius: 4px;
        border-left: 4px solid {VOLS_ORANGE};
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
    }}

    /* Editorial Footer Styling */
    .editorial-footer {{
        margin-top: 80px;
        padding: 40px 0;
        border-top: 1px solid #E5E7EB;
        text-align: center;
        background-color: {WHITE};
    }}

    .footer-name {{
        font-family: 'Playfair Display', serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: {BLACK};
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 12px;
    }}

    .cursive-signature {{
        font-family: 'Great Vibes', cursive;
        font-size: 2.5rem;
        color: {DARK_GRAY};
        transform: rotate(-3deg);
        margin: 10px 0 20px 0;
        text-shadow: 0.5px 0.5px 1px rgba(0,0,0,0.1);
    }}

    .social-icons {{
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-top: 15px;
    }}

    .social-icons a {{
        color: {BLACK};
        text-decoration: none;
        font-weight: 500;
        font-size: 0.9rem;
        padding: 6px 12px;
        border: 1px solid {BLACK};
        border-radius: 20px;
        transition: all 0.3s ease;
    }}

    .social-icons a:hover {{
        background-color: {VOLS_ORANGE};
        border-color: {VOLS_ORANGE};
        color: {WHITE};
    }}
    </style>
""",
    unsafe_allow_html=True,
)

# --- HEADER SECTION ---
st.markdown(
    "<h1 style='font-size: 2.8rem; margin-bottom: 0px;'>RCM Compliance & Work-Queue Intelligence Engine</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='font-size: 1.1rem; color: #555555; margin-top: 8px; margin-bottom:"
    " 40px;'>Enterprise Portfolio Artifact: RBAC, SQLite Persistence, Webhook"
    " Alerting, and Historical Audit Search.</p>",
    unsafe_allow_html=True,
)

# --- METRICS ROW (Structured Grid with Asymmetry) ---
col1, col2, col3, col4 = st.columns(4)
with col1:
  st.markdown(
      f"<div class='metric-card'><small>TOTAL CASES</small><h2"
      f" style='color:{VOLS_ORANGE}!important; margin:0;'>5</h2></div>",
      unsafe_allow_html=True,
  )
with col2:
  st.markdown(
      f"<div class='metric-card'><small>CRITICAL RISKS</small><h2"
      f" style='color:{VOLS_ORANGE}!important; margin:0;'>2</h2></div>",
      unsafe_allow_html=True,
  )
with col3:
  st.markdown(
      f"<div class='metric-card'><small>OPEN HIGH</small><h2"
      f" style='color:{VOLS_ORANGE}!important; margin:0;'>3</h2></div>",
      unsafe_allow_html=True,
  )
with col4:
  st.markdown(
      f"<div class='metric-card'><small>EXCEPTIONS</small><h2"
      f" style='color:{VOLS_ORANGE}!important; margin:0;'>4</h2></div>",
      unsafe_allow_html=True,
  )

st.markdown("<br><br>", unsafe_allow_html=True)

# --- FOOTER SECTION ---
st.markdown(
    f"""
    <div class="editorial-footer">
        <div class="footer-name">Created by Kori Pickle</div>
        <div class="cursive-signature">Kori Pickle</div>
        <div class="social-icons">
            <a href="https://linkedin.com" target="_blank">LinkedIn</a>
            <a href="https://github.com" target="_blank">GitHub</a>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

