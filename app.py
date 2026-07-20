import streamlit as st

# 1. Page Configuration & Theme Setup
st.set_page_config(
    page_title="DAZZY BUILD LAB - Blood Strike",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Dark Theme Custom CSS
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #0d0e12;
        color: #e2e8f0;
    }
    
    /* Premium Rounded Cards */
    .feature-card {
        background-color: #1a1c23;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #2d3139;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    }
    
    /* Accents & Headers */
    h1, h2, h3 {
        color: #ff4b4b !important;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #111318;
        border-right: 1px solid #2d3139;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Sidebar / Navigation
with st.sidebar:
    st.title("⚡ NAVIGATION")
    st.write("Welcome to the Blood Strike Community Hub.")
    st.markdown("---")
    menu = st.radio(
        "Select Phase Component:",
        ["Dashboard Home", "User System (Locked)", "Gun Loadouts (Locked)", "Community Features (Locked)"]
    )
    st.markdown("---")
    st.caption("Developed for the Blood Strike Community 🩸")

# 3. Main Dashboard Layout (Phase 1 UI)
st.title("🎮 DAZZY BUILD LAB")
st.subheader("Premium Interface Foundation")

st.markdown("""
<div class="feature-card">
    <h3>📢 Phase 1 Status: UI Core Operational</h3>
    <p>This single-file framework is successfully connected to Streamlit. It uses a custom structural grid layout designed to stay completely unbroken as we scale up to 1,000+ lines of code together.</p>
</div>
""", unsafe_allow_html=True)

# Grid Layout for Next Features
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>👤 User System</h3>
        <p><i>Status: Interface Placeholder Only</i></p>
        <p>Future update will add profile generation, rank trackers, and stats cards.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>🔫 Gun Attachments & Images</h3>
        <p><i>Status: Interface Placeholder Only</i></p>
        <p>Future update will showcase weapon cards, stats bars, and visual asset integrations.</p>
    </div>
    """, unsafe_allow_html=True)

st.success("✨ Phase 1 code generated successfully. Ready for GitHub deployment!")
