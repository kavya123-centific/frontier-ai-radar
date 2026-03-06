"""
streamlit_app.py — Frontier AI Radar v4.3
Enterprise Intelligence Platform — Clean Design
"""

import os
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

API_URL = st.secrets.get("BACKEND_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(
    page_title="Frontier AI Radar",
    page_icon="🛰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Enterprise CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ---------- GLOBAL RESET ---------- */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.stApp { background: #F4F6FA !important; }
.block-container {
    padding: 28px 32px 32px 32px !important;
    max-width: 1380px !important;
}
#MainMenu, footer, header { visibility: hidden !important; }

/* ---------- HIDE SIDEBAR COLLAPSE ---------- */
[data-testid="collapsedControl"],
button[data-testid="baseButton-headerNoPadding"],
[data-testid="stSidebarCollapsedControl"] { display: none !important; }

/* ---------- SIDEBAR ---------- */
section[data-testid="stSidebar"],
[data-testid="stSidebar"] {
    width: 256px !important;
    min-width: 256px !important;
    max-width: 256px !important;
    background: linear-gradient(160deg, #1C2340 0%, #252D4A 100%) !important;
    border-right: none !important;
    box-shadow: 4px 0 24px rgba(0,0,0,0.12) !important;
}
section[data-testid="stSidebar"] > div:first-child {
    width: 256px !important;
    min-width: 256px !important;
    padding: 0 !important;
    overflow-x: hidden !important;
}

/* All sidebar text */
[data-testid="stSidebar"] * { color: #B0BAD4 !important; }
[data-testid="stSidebar"] .stRadio > label { display: none !important; }
[data-testid="stSidebar"] .stRadio > div { gap: 2px !important; }
[data-testid="stSidebar"] .stRadio label {
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 9px 16px 9px 20px !important;
    border-radius: 8px !important;
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    margin: 1px 8px !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.08) !important;
    color: #fff !important;
}
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] input:checked ~ div + span,
[data-testid="stSidebar"] .stRadio [aria-checked="true"] ~ div span {
    color: #fff !important;
}

/* ---------- KPI METRIC CARDS ---------- */
[data-testid="metric-container"] {
    background: white !important;
    border-radius: 14px !important;
    padding: 20px 22px !important;
    border: 1px solid #E8ECF4 !important;
    box-shadow: 0 2px 8px rgba(28,35,64,0.06) !important;
}
[data-testid="metric-container"] label {
    color: #8492A6 !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #1C2340 !important;
    font-size: 28px !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 12px !important;
    font-weight: 500 !important;
}

/* ---------- EXPANDERS (Signal Cards) ---------- */
[data-testid="stExpander"] {
    background: white !important;
    border-radius: 12px !important;
    border: 1px solid #E8ECF4 !important;
    box-shadow: 0 1px 4px rgba(28,35,64,0.05) !important;
    margin-bottom: 8px !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] > details > summary {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #1C2340 !important;
    padding: 14px 18px !important;
}
[data-testid="stExpander"] > details > summary:hover {
    background: #F8FAFD !important;
}
[data-testid="stExpander"] > details[open] > summary {
    border-bottom: 1px solid #F0F3F8 !important;
}

/* ---------- BUTTONS ---------- */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    border-radius: 9px !important;
    border: none !important;
    padding: 9px 18px !important;
    transition: all 0.15s ease !important;
    letter-spacing: 0.01em !important;
}
.stButton > button[kind="primary"],
.stButton > button {
    background: linear-gradient(135deg, #4F5BDB 0%, #6C47DB 100%) !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(79,91,219,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px rgba(79,91,219,0.4) !important;
}
.stButton > button[kind="secondary"] {
    background: white !important;
    color: #4F5BDB !important;
    border: 1.5px solid #4F5BDB !important;
    box-shadow: none !important;
}

/* ---------- INPUTS ---------- */
.stTextInput > div > div > input {
    background: white !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 9px !important;
    color: #1C2340 !important;
    font-size: 13px !important;
    font-family: 'Inter', sans-serif !important;
    padding: 9px 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #4F5BDB !important;
    box-shadow: 0 0 0 3px rgba(79,91,219,0.12) !important;
}
.stSelectbox > div > div {
    background: white !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 9px !important;
    font-size: 13px !important;
}

/* ---------- TYPOGRAPHY ---------- */
h1 {
    color: #1C2340 !important;
    font-weight: 700 !important;
    font-size: 22px !important;
    letter-spacing: -0.03em !important;
    margin-bottom: 4px !important;
}
h2 {
    color: #1C2340 !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    letter-spacing: -0.01em !important;
    margin: 0 !important;
}
h3 {
    color: #5A6478 !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
}
p, li { color: #5A6478 !important; font-size: 13px !important; line-height: 1.6 !important; }

/* ---------- ALERTS ---------- */
.stAlert { border-radius: 10px !important; font-size: 13px !important; }

/* ---------- PROGRESS BAR ---------- */
.stProgress > div > div {
    background: linear-gradient(90deg, #4F5BDB, #6C47DB) !important;
    border-radius: 4px !important;
}

/* ---------- DIVIDER ---------- */
hr { border-color: #EEF1F8 !important; margin: 20px 0 !important; }

/* ---------- DATA TABLE ---------- */
[data-testid="stDataFrame"] {
    background: white !important;
    border: 1px solid #E8ECF4 !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* ---------- CAPTION ---------- */
[data-testid="stCaptionContainer"] p {
    color: #8492A6 !important;
    font-size: 12px !important;
}

/* ---------- AREA/BAR CHARTS ---------- */
[data-testid="stArrowVegaLiteChart"],
[data-testid="stVegaLiteChart"] {
    background: white !important;
    border: 1px solid #E8ECF4 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    overflow: hidden !important;
}

/* ---------- FORM ---------- */
[data-testid="stForm"] {
    background: white !important;
    border: 1px solid #E8ECF4 !important;
    border-radius: 14px !important;
    padding: 20px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
_LIST = ["findings","runs","sources","entities","snapshots","clusters","changes","email-recipients"]
CAT_ICON  = {"competitors":"🏢","model_providers":"🤖","research":"📄","hf_benchmarks":"📊"}
CAT_LABEL = {"competitors":"Competitors","model_providers":"Model Providers",
             "research":"Research","hf_benchmarks":"HF Benchmarks"}
CAT_CLR   = {"competitors":"#EF4444","model_providers":"#4F5BDB","research":"#10B981","hf_benchmarks":"#F59E0B"}
PRI_CLR   = {"HIGH":"#EF4444","MEDIUM":"#F59E0B","LOW":"#10B981"}
PRI_BG    = {"HIGH":"#FEF2F2","MEDIUM":"#FFFBEB","LOW":"#ECFDF5"}

# ── Session State — pipeline cross-navigation tracking ────────────────────────
if "pipeline_running" not in st.session_state:
    st.session_state.pipeline_running  = False
if "pipeline_done_flag" not in st.session_state:
    st.session_state.pipeline_done_flag = False
if "last_known_run_id" not in st.session_state:
    st.session_state.last_known_run_id  = None

# ── API Helper ─────────────────────────────────────────────────────────────────
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_URL}{path}", params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.Timeout:
        return [] if any(x in path for x in _LIST) else {}
    except requests.ConnectionError:
        st.error("❌ Cannot reach API. Check BACKEND_URL in Streamlit secrets.")
        st.stop()
    except Exception as e:
        if "timed out" in str(e).lower():
            return [] if any(x in path for x in _LIST) else {}
        return [] if any(x in path for x in _LIST) else {}

# ── Score helpers ──────────────────────────────────────────────────────────────
def score_color(s):
    if s >= 7: return "#10B981"
    if s >= 4: return "#F59E0B"
    return "#EF4444"

def score_bg(s):
    if s >= 7: return "#ECFDF5"
    if s >= 4: return "#FFFBEB"
    return "#FEF2F2"

# ── Pipeline state — persisted across page navigations ────────────────────────
def sync_pipeline_state():
    """
    Call once per page render. Checks real API state and syncs session_state.
    Returns (status_dict, is_running).
    """
    status = api_get("/api/status")
    api_running = status.get("is_running", False)
    current_run_id = status.get("current_run_id")

    # Transition: was running → now idle = just completed
    if st.session_state.pipeline_running and not api_running:
        st.session_state.pipeline_running   = False
        st.session_state.pipeline_done_flag = True   # show banner once
        st.session_state.last_known_run_id  = None
    elif api_running:
        st.session_state.pipeline_running  = True
        st.session_state.last_known_run_id = current_run_id

    return status, api_running

# ── Pipeline progress bar ──────────────────────────────────────────────────────
def pipeline_banner():
    """Shows running bar OR completion banner, then clears. Returns True if was running."""
    is_running = st.session_state.pipeline_running

    if st.session_state.pipeline_done_flag:
        st.session_state.pipeline_done_flag = False
        st.markdown("""
        <div style='background:linear-gradient(135deg,#10B981,#059669);border-radius:12px;
            padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:12px;'>
            <span style='font-size:20px;'>✅</span>
            <div>
                <div style='color:white;font-weight:700;font-size:14px;'>Pipeline Completed!</div>
                <div style='color:rgba(255,255,255,0.8);font-size:12px;'>
                    New intelligence signals are now available below.</div>
            </div>
        </div>""", unsafe_allow_html=True)

    if is_running:
        ps       = api_get("/api/pipeline-status")
        stage    = ps.get("stage", "Initializing")
        progress = ps.get("progress", 0)
        detail   = ps.get("detail", "")
        st.markdown(f"""
        <div style='background:white;border:1px solid #E8ECF4;border-radius:12px;
            padding:16px 20px;margin-bottom:20px;box-shadow:0 2px 8px rgba(79,91,219,0.1);'>
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;'>
                <div style='display:flex;align-items:center;gap:10px;'>
                    <div style='width:9px;height:9px;border-radius:50%;background:#4F5BDB;
                        animation:radar-pulse 1.4s ease-in-out infinite;'></div>
                    <span style='font-size:13px;font-weight:600;color:#1C2340;'>
                        Pipeline Running — {stage}
                    </span>
                </div>
                <span style='font-size:13px;font-weight:700;color:#4F5BDB;'>{progress}%</span>
            </div>
            <div style='background:#F0F3F8;border-radius:6px;height:7px;overflow:hidden;'>
                <div style='background:linear-gradient(90deg,#4F5BDB,#6C47DB);height:7px;
                    border-radius:6px;width:{progress}%;transition:width .4s ease;'></div>
            </div>
            <div style='color:#8492A6;font-size:11px;margin-top:7px;font-style:italic;'>{detail}</div>
        </div>
        <style>
        @keyframes radar-pulse {{
            0%,100% {{ opacity:1; transform:scale(1); }}
            50% {{ opacity:0.4; transform:scale(1.3); }}
        }}
        </style>""", unsafe_allow_html=True)
        import time; time.sleep(2.5); st.rerun()

    return is_running

# ── Reusable: Section header ────────────────────────────────────────────────
def section_header(title, subtitle=None):
    sub = f"<div style='color:#8492A6;font-size:12px;margin-top:2px;'>{subtitle}</div>" if subtitle else ""
    st.markdown(f"""
    <div style='margin:20px 0 12px 0;'>
        <div style='font-size:16px;font-weight:700;color:#1C2340;letter-spacing:-0.01em;'>{title}</div>
        {sub}
    </div>""", unsafe_allow_html=True)

# ── Reusable: Signal card ────────────────────────────────────────────────────
def signal_card(f, expanded=False):
    score    = f.get("final_score", 0) or 0
    conf     = f.get("confidence_score", 0.8) or 0.8
    cat      = f.get("category", "")
    change   = f.get("change_status", "new")
    icon     = "🆕" if change == "new" else "🔄"
    sc       = score_color(score)
    sbg      = score_bg(score)
    priority = (f.get("priority") or "medium").upper()
    horizon  = f.get("impact_horizon") or "3-months"
    cat_c    = CAT_CLR.get(cat, "#8492A6")
    pc       = PRI_CLR.get(priority, "#8492A6")
    pbg      = PRI_BG.get(priority, "#F4F6FA")

    with st.expander(f"{icon} {f.get('title', '')}  ·  {score:.1f}/10", expanded=expanded):
        left, right = st.columns([3, 1])

        with left:
            # Summary
            st.markdown(f"<p style='color:#475569;font-size:13px;line-height:1.6;margin-bottom:10px;'>{f.get('summary','')}</p>", unsafe_allow_html=True)

            # Why it matters
            if f.get("why_matters"):
                st.markdown(f"""<div style='background:#EFF6FF;border-left:3px solid #4F5BDB;
                    padding:10px 14px;border-radius:0 8px 8px 0;margin:8px 0;'>
                    <span style='font-size:11px;font-weight:700;color:#4F5BDB;
                        text-transform:uppercase;letter-spacing:.06em;'>Why it matters</span>
                    <p style='font-size:13px;color:#1E3A8A;margin:4px 0 0;'>{f["why_matters"]}</p>
                </div>""", unsafe_allow_html=True)

            # Evidence
            if f.get("evidence"):
                st.markdown(f"""<div style='background:#F0FDF4;border-left:3px solid #10B981;
                    padding:10px 14px;border-radius:0 8px 8px 0;margin:8px 0;'>
                    <span style='font-size:11px;font-weight:700;color:#10B981;
                        text-transform:uppercase;letter-spacing:.06em;'>Evidence</span>
                    <p style='font-size:12px;color:#14532D;margin:4px 0 0;'>{f["evidence"]}</p>
                </div>""", unsafe_allow_html=True)

            # Strategic Recommendation
            if f.get("recommendation"):
                st.markdown(f"""<div style='background:#FAF5FF;border-left:3px solid #7C3AED;
                    padding:10px 14px;border-radius:0 8px 8px 0;margin:8px 0;'>
                    <span style='font-size:11px;font-weight:700;color:#7C3AED;
                        text-transform:uppercase;letter-spacing:.06em;'>🎯 Strategic Action</span>
                    <p style='font-size:13px;color:#3B0764;margin:5px 0 8px;'>{f["recommendation"]}</p>
                    <span style='background:{pc};color:white;padding:3px 10px;border-radius:20px;
                        font-size:11px;font-weight:700;'>Priority: {priority}</span>
                    <span style='background:{pbg};color:{pc};padding:3px 10px;border-radius:20px;
                        font-size:11px;font-weight:600;margin-left:6px;border:1px solid {pc}40;'>
                        ⏱ {horizon}</span>
                </div>""", unsafe_allow_html=True)

        with right:
            # Score ring
            st.markdown(f"""<div style='background:{sbg};border-radius:12px;padding:16px 12px;
                text-align:center;margin-bottom:10px;border:1px solid {sc}30;'>
                <div style='font-size:30px;font-weight:800;color:{sc};
                    letter-spacing:-0.03em;line-height:1;'>{score:.1f}</div>
                <div style='font-size:10px;color:#8492A6;font-weight:600;
                    text-transform:uppercase;letter-spacing:.08em;margin-top:2px;'>Score / 10</div>
            </div>""", unsafe_allow_html=True)

            # Meta pill card
            st.markdown(f"""<div style='background:#F8FAFD;border:1px solid #E8ECF4;
                border-radius:10px;padding:12px;font-size:12px;'>
                <div style='margin-bottom:8px;'>
                    <div style='color:#8492A6;font-size:10px;font-weight:600;
                        text-transform:uppercase;letter-spacing:.06em;margin-bottom:3px;'>Category</div>
                    <span style='background:{cat_c}18;color:{cat_c};padding:3px 10px;
                        border-radius:20px;font-size:11px;font-weight:700;'>{CAT_LABEL.get(cat,cat)}</span>
                </div>
                <div style='margin-bottom:8px;'>
                    <div style='color:#8492A6;font-size:10px;font-weight:600;
                        text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px;'>Confidence</div>
                    <div style='font-weight:700;color:#1C2340;font-size:13px;'>{conf:.0%}</div>
                </div>
                <div>
                    <div style='color:#8492A6;font-size:10px;font-weight:600;
                        text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px;'>Cluster</div>
                    <div style='font-weight:500;color:#5A6478;font-size:11px;'>
                        {f.get("topic_cluster","general")}</div>
                </div>
            </div>""", unsafe_allow_html=True)

            if f.get("source_url"):
                st.markdown(f"""<div style='margin-top:8px;text-align:center;'>
                    <a href='{f["source_url"]}' target='_blank'
                        style='font-size:12px;color:#4F5BDB;font-weight:600;text-decoration:none;'>
                        🔗 View Source →</a></div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo block
    st.markdown("""
    <div style='padding:22px 20px 16px;'>
        <div style='display:flex;align-items:center;gap:12px;'>
            <div style='background:linear-gradient(135deg,#4F5BDB 0%,#6C47DB 100%);
                border-radius:11px;width:38px;height:38px;flex-shrink:0;
                display:flex;align-items:center;justify-content:center;font-size:19px;'>
                🛰
            </div>
            <div>
                <div style='color:#FFFFFF;font-size:14px;font-weight:700;
                    letter-spacing:-0.01em;line-height:1.2;'>Frontier AI Radar</div>
                <div style='color:#5A6FA8;font-size:11px;margin-top:1px;'>
                    Intelligence Platform v4.3</div>
            </div>
        </div>
    </div>
    <div style='height:1px;background:rgba(255,255,255,0.07);margin:0 16px 12px;'></div>
    <div style='padding:0 8px;'>
        <div style='font-size:10px;font-weight:700;color:#3D4F72;
            text-transform:uppercase;letter-spacing:.1em;padding:4px 12px 8px;'>Navigation</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("nav", [
        "📊  Dashboard",
        "🔄  What Changed",
        "🎯  Impact Analysis",
        "📈  Observability",
        "🏷️  Entity Trends",
        "🔭  SOTA Watch",
        "🔍  Findings Explorer",
        "⚙️  Sources",
        "📁  Run History",
        "📚  Digest Archive",
        "📧  Email Recipients",
        "📅  Schedule",
    ], label_visibility="collapsed")

    # Divider + Run button
    st.markdown("""
    <div style='height:1px;background:rgba(255,255,255,0.07);margin:12px 16px;'></div>
    """, unsafe_allow_html=True)

    if st.button("🚀  Run Pipeline Now", type="primary", use_container_width=True):
        try:
            r = requests.post(f"{API_URL}/api/runs/trigger", timeout=5)
            if r.status_code == 200:
                st.session_state.pipeline_running   = True
                st.session_state.pipeline_done_flag = False
                st.success("✅ Run started!")
                st.rerun()
            elif r.status_code == 409:
                st.warning("⏳ Already running")
            else:
                st.error(f"Error {r.status_code}")
        except:
            st.error("API offline")

    with st.expander("🔧 Operations"):
        if st.button("Recover Stale Runs", use_container_width=True):
            try:
                r = requests.post(f"{API_URL}/api/runs/recover", timeout=5)
                st.success(r.json().get("message","Done") if r.ok else "Failed")
            except Exception as e:
                st.error(str(e))

    # Health dot
    try:
        h = requests.get(f"{API_URL}/health", timeout=3)
        dot, label = ("#10B981","API Online") if h.ok else ("#EF4444","API Degraded")
    except:
        dot, label = "#EF4444","API Offline"

    st.markdown(f"""
    <div style='padding:12px 20px 20px;display:flex;align-items:center;gap:8px;
        position:absolute;bottom:0;left:0;right:0;'>
        <div style='width:7px;height:7px;border-radius:50%;background:{dot};'></div>
        <span style='font-size:12px;color:#5A6FA8;'>{label}</span>
    </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
if page == "📊  Dashboard":
    status, is_running = sync_pipeline_state()
    findings = api_get("/api/findings", {"limit": 100})

    # Page header
    st.markdown("""
    <div style='margin-bottom:20px;'>
        <div style='font-size:22px;font-weight:800;color:#1C2340;letter-spacing:-0.03em;'>
            📊 Intelligence Dashboard
        </div>
        <div style='color:#8492A6;font-size:13px;margin-top:3px;'>
            Autonomous multi-agent surveillance · Real-time frontier AI monitoring
        </div>
    </div>""", unsafe_allow_html=True)

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🔍 Signals Detected",  status.get("total_findings", 0))
    k2.metric("✅ Runs Completed",    status.get("completed_runs", 0))
    k3.metric("📡 Sources Active",    len(api_get("/api/sources")))
    k4.metric("⚡ Pipeline",          "▶ Running" if is_running else "● Idle")

    # Pipeline banner (auto-reruns if running)
    pipeline_banner()

    if not findings:
        st.info("No intelligence signals yet. Click **🚀 Run Pipeline Now** in the sidebar to start.")
        st.stop()

    # Executive brief
    section_header("🧠 Executive Intelligence Brief", "Top 5 highest-impact signals from latest run")
    for f in findings[:5]:
        score    = f.get("final_score", 0) or 0
        sc       = score_color(score)
        icon     = "🆕" if f.get("change_status") == "new" else "🔄"
        cat      = f.get("category", "")
        cat_c    = CAT_CLR.get(cat, "#8492A6")
        priority = (f.get("priority") or "medium").upper()
        pc       = PRI_CLR.get(priority, "#8492A6")
        st.markdown(f"""
        <div style='background:white;border:1px solid #E8ECF4;border-radius:12px;
            padding:14px 18px;margin:6px 0;display:flex;align-items:flex-start;gap:16px;
            box-shadow:0 1px 4px rgba(28,35,64,0.05);'>
            <div style='flex:1;min-width:0;'>
                <div style='font-weight:600;color:#1C2340;font-size:14px;margin-bottom:5px;'>
                    {icon} {f.get("title","")}</div>
                <div style='color:#5A6478;font-size:13px;line-height:1.5;'>
                    {(f.get("why_matters") or f.get("summary",""))[:160]}</div>
                <div style='margin-top:9px;display:flex;align-items:center;gap:7px;flex-wrap:wrap;'>
                    <span style='background:{cat_c}18;color:{cat_c};padding:3px 10px;
                        border-radius:20px;font-size:11px;font-weight:700;'>
                        {CAT_LABEL.get(cat,cat)}</span>
                    <span style='background:{pc}18;color:{pc};padding:3px 10px;
                        border-radius:20px;font-size:11px;font-weight:700;'>⚡ {priority}</span>
                    <span style='color:#8492A6;font-size:11px;'>
                        🏷️ {f.get("topic_cluster","general")}</span>
                </div>
            </div>
            <div style='flex-shrink:0;text-align:center;min-width:52px;'>
                <div style='font-size:24px;font-weight:800;color:{sc};
                    letter-spacing:-0.02em;line-height:1;'>{score:.1f}</div>
                <div style='font-size:10px;color:#8492A6;font-weight:600;margin-top:1px;'>/10</div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # Top signals (expandable)
    section_header("🏆 Top Intelligence Signals", f"Showing top {min(6, len(findings))} by impact score")
    for i, f in enumerate(findings[:6], 1):
        signal_card(f, expanded=(i == 1))

    st.markdown("---")

    # Charts row
    ca, cb = st.columns(2)
    with ca:
        section_header("📈 Signal Momentum", "Findings per completed run")
        runs = api_get("/api/runs")
        if runs:
            data = [{"Date": str(r.get("started_at",""))[:10], "Signals": r.get("total_found",0)}
                    for r in runs if r.get("status") == "completed"]
            if data:
                st.area_chart(pd.DataFrame(data).set_index("Date"), use_container_width=True)
    with cb:
        section_header("📂 Category Breakdown", "Signals by agent category")
        cats = {}
        for f in findings:
            k = CAT_LABEL.get(f.get("category",""), f.get("category","other"))
            cats[k] = cats.get(k, 0) + 1
        if cats:
            st.bar_chart(pd.DataFrame(list(cats.items()), columns=["Category","Count"]).set_index("Category"))

    st.caption(f"Next scheduled run: {status.get('next_scheduled','N/A')} · v{status.get('version','4.3.0')}")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: WHAT CHANGED
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🔄  What Changed":
    status, is_running = sync_pipeline_state()
    pipeline_banner()

    st.markdown("""<div style='margin-bottom:20px;'>
        <div style='font-size:22px;font-weight:800;color:#1C2340;letter-spacing:-0.03em;'>🔄 What Changed</div>
        <div style='color:#8492A6;font-size:13px;margin-top:3px;'>Signal delta between runs — NEW / UPDATED / UNCHANGED</div>
    </div>""", unsafe_allow_html=True)

    runs = api_get("/api/runs", {"limit": 10})
    completed = [r for r in runs if r.get("status") == "completed"]
    if not completed:
        st.info("No completed runs yet. Trigger a run to start collecting signals.")
        st.stop()

    opts = {f"Run {r['run_id'][:8]}  ·  {str(r.get('started_at',''))[:16]}  ·  {r.get('total_found',0)} signals": r["run_id"]
            for r in completed}
    sel  = opts[st.selectbox("Select Run", list(opts.keys()))]
    chg  = api_get(f"/api/changes/{sel}")
    new_items = chg.get("new", [])
    upd_items = chg.get("updated", [])

    c1, c2, c3 = st.columns(3)
    c1.metric("🆕 New Signals",   len(new_items))
    c2.metric("🔄 Updated",       len(upd_items))
    c3.metric("⏸ Unchanged",      chg.get("unchanged", 0))
    st.markdown("---")

    for label, items, clr in [
        ("🆕 New Signals", new_items, "#4F5BDB"),
        ("🔄 Updated Signals", upd_items, "#10B981"),
    ]:
        if items:
            section_header(f"{label}", f"{len(items)} signal(s)")
            for f in items:
                signal_card(f)

    if not new_items and not upd_items:
        st.success("✅ No changes detected — all sources unchanged since last run.")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: IMPACT ANALYSIS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🎯  Impact Analysis":
    status, is_running = sync_pipeline_state()
    pipeline_banner()

    st.markdown("""<div style='margin-bottom:20px;'>
        <div style='font-size:22px;font-weight:800;color:#1C2340;letter-spacing:-0.03em;'>🎯 Impact Analysis</div>
        <div style='color:#8492A6;font-size:13px;margin-top:3px;'>Strategic scoring — Relevance · Novelty · Credibility · Actionability</div>
    </div>""", unsafe_allow_html=True)

    findings = api_get("/api/findings", {"limit": 20})
    if not findings:
        st.info("No findings yet. Trigger a run first.")
        st.stop()

    # Formula banner
    st.markdown("""
    <div style='background:white;border:1px solid #E8ECF4;border-radius:12px;
        padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:20px;
        flex-wrap:wrap;box-shadow:0 1px 4px rgba(28,35,64,0.05);'>
        <span style='font-size:12px;font-weight:700;color:#8492A6;
            text-transform:uppercase;letter-spacing:.06em;'>Impact Formula</span>
        <span style='font-size:13px;color:#1C2340;'>
            <span style='color:#4F5BDB;font-weight:700;'>0.35</span> × Relevance &nbsp;+&nbsp;
            <span style='color:#10B981;font-weight:700;'>0.25</span> × Novelty &nbsp;+&nbsp;
            <span style='color:#7C3AED;font-weight:700;'>0.20</span> × Credibility &nbsp;+&nbsp;
            <span style='color:#F59E0B;font-weight:700;'>0.20</span> × Actionability
        </span>
    </div>""", unsafe_allow_html=True)

    try:
        import plotly.graph_objects as go
        PLOTLY = True
    except:
        PLOTLY = False

    top = findings[:6]
    section_header("📊 Multi-Dimensional Signal Scoring")

    if PLOTLY:
        cols = st.columns(2)
        for i, f in enumerate(top):
            score   = f.get("final_score",0) or 0
            conf    = f.get("confidence_score",0.8) or 0.8
            impact  = f.get("impact_score",0) or 0
            novelty = f.get("novelty_score",0) or 0
            rel     = min(score/10, 1.0)
            action  = min((impact/10)*1.2, 1.0)

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=[rel, novelty, conf, action, rel],
                theta=["Relevance","Novelty","Credibility","Actionability","Relevance"],
                fill='toself',
                fillcolor='rgba(79,91,219,0.10)',
                line=dict(color='#4F5BDB', width=2.5),
            ))
            fig.update_layout(
                polar=dict(bgcolor='white',
                    radialaxis=dict(visible=True, range=[0,1], gridcolor='#EEF1F8',
                        tickfont=dict(color='#8492A6', size=9), tickvals=[0.25,0.5,0.75,1]),
                    angularaxis=dict(gridcolor='#EEF1F8',
                        tickfont=dict(color='#1C2340', size=11, family='Inter'))),
                paper_bgcolor='white', plot_bgcolor='white',
                font=dict(family='Inter', color='#1C2340', size=11),
                margin=dict(l=40,r=40,t=48,b=16), height=265,
                title=dict(text=f.get("title","")[:42],
                    font=dict(size=11, color='#1C2340', family='Inter')),
                showlegend=False,
            )
            cols[i%2].plotly_chart(fig, use_container_width=True)
    else:
        rows = [{"Title":f.get("title","")[:60],"Score":f.get("final_score",0),
                 "Conf":f"{(f.get('confidence_score',0.8) or 0.8):.0%}",
                 "Cluster":f.get("topic_cluster","general")} for f in top]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    section_header("💼 Strategic Implications", "Why each signal matters")
    for f in findings[:5]:
        why = f.get("why_matters", "")
        if why:
            score = f.get("final_score", 0) or 0
            sc    = score_color(score)
            st.markdown(f"""
            <div style='background:white;border:1px solid #E8ECF4;border-radius:12px;
                padding:14px 18px;margin:6px 0;display:flex;gap:14px;
                box-shadow:0 1px 4px rgba(28,35,64,0.05);'>
                <div style='flex:1;'>
                    <div style='font-weight:600;color:#1C2340;font-size:13px;margin-bottom:5px;'>
                        {f.get("title","")[:70]}</div>
                    <div style='color:#5A6478;font-size:13px;line-height:1.5;'>{why}</div>
                </div>
                <div style='font-size:20px;font-weight:800;color:{sc};flex-shrink:0;
                    letter-spacing:-0.02em;'>{score:.1f}</div>
            </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: OBSERVABILITY
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📈  Observability":
    status, is_running = sync_pipeline_state()
    pipeline_banner()

    st.markdown("""<div style='margin-bottom:20px;'>
        <div style='font-size:22px;font-weight:800;color:#1C2340;letter-spacing:-0.03em;'>📈 Observability</div>
        <div style='color:#8492A6;font-size:13px;margin-top:3px;'>Agent performance · run trends · signal distributions</div>
    </div>""", unsafe_allow_html=True)

    metrics = api_get("/metrics")
    if not metrics or metrics.get("total_runs", 0) == 0:
        st.info("No completed runs yet.")
        st.stop()

    k1,k2,k3,k4,k5,k6 = st.columns(6)
    k1.metric("Runs",           metrics.get("total_runs",0))
    k2.metric("Completed",      metrics.get("completed_runs",0))
    k3.metric("Failed",         metrics.get("failed_runs",0))
    k4.metric("Total Signals",  metrics.get("total_findings",0))
    k5.metric("Avg Time (s)",   metrics.get("avg_elapsed_sec",0))
    k6.metric("Avg Signals",    metrics.get("avg_findings_per_run",0))

    st.markdown("---")

    rot = metrics.get("runs_over_time", [])
    if rot:
        section_header("📅 Signals Per Run Over Time")
        st.bar_chart(pd.DataFrame(rot).set_index("date")["count"], use_container_width=True)

    st.markdown("---")
    ca, cb = st.columns(2)
    with ca:
        section_header("🤖 Per-Agent Performance")
        agents = metrics.get("agent_metrics", [])
        if agents:
            st.dataframe(pd.DataFrame(agents).rename(columns={
                "name":"Agent","total_found":"Signals","success_runs":"OK",
                "error_runs":"Errors","avg_elapsed":"Avg (s)"}),
                use_container_width=True, hide_index=True)
    with cb:
        section_header("🔄 Change Detection Stats")
        cs = metrics.get("change_stats", {})
        if cs:
            st.bar_chart(pd.DataFrame(list(cs.items()),columns=["Status","Count"]).set_index("Status"))

    st.markdown("---")
    cc, cd = st.columns(2)
    with cc:
        section_header("📂 By Category")
        cd2 = metrics.get("findings_by_category", {})
        if cd2: st.bar_chart(pd.DataFrame(list(cd2.items()),columns=["Category","Count"]).set_index("Category"))
    with cd:
        section_header("🗂️ By Topic Cluster")
        cl2 = metrics.get("findings_by_cluster", {})
        if cl2: st.bar_chart(pd.DataFrame(list(cl2.items()),columns=["Cluster","Count"]).set_index("Cluster"))

    st.markdown("---")
    section_header("🏢 Top Entities by Mention")
    te = metrics.get("top_entities", [])
    if te: st.bar_chart(pd.DataFrame(te[:15]).set_index("entity")["count"])


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: ENTITY TRENDS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🏷️  Entity Trends":
    status, is_running = sync_pipeline_state()
    pipeline_banner()

    st.markdown("""<div style='margin-bottom:20px;'>
        <div style='font-size:22px;font-weight:800;color:#1C2340;letter-spacing:-0.03em;'>🏷️ Entity Trends</div>
        <div style='color:#8492A6;font-size:13px;margin-top:3px;'>Mindshare tracking — entity mention deltas vs prior run</div>
    </div>""", unsafe_allow_html=True)

    runs      = api_get("/api/runs", {"limit": 10})
    completed = [r for r in runs if r.get("status") == "completed"]
    if not completed:
        st.info("No completed runs yet.")
        st.stop()

    opts = {f"Run {r['run_id'][:8]}  ·  {str(r.get('started_at',''))[:16]}": r["run_id"] for r in completed}
    sel  = opts[st.selectbox("Select Run", list(opts.keys()))]
    trends_data = api_get(f"/api/entity-trends/{sel}")
    trends      = trends_data.get("entity_trends", {})

    if trends:
        section_header("📊 Entity Mention Trends vs Prior Run")
        rows = []
        for entity, info in trends.items():
            trend = info.get("trend", "stable")
            icon  = {"up":"⬆️","down":"⬇️","new":"🆕","stable":"➡️"}.get(trend,"")
            rows.append({"Entity":entity.title(),"Trend":f"{icon} {trend}",
                         "Now":info.get("current",0),"Before":info.get("previous",0),
                         "Δ":info.get("delta",0)})
        rows.sort(key=lambda x: abs(x["Δ"]), reverse=True)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.markdown("---")
        t1, t2, t3 = st.columns(3)
        risers  = [r for r in rows if r["Δ"] > 0]
        fallers = [r for r in rows if r["Δ"] < 0]
        new_ent = [r for r in rows if "🆕" in r["Trend"]]

        with t1:
            st.markdown("""<div style='background:#ECFDF5;border-radius:10px;padding:14px 16px;'>
                <div style='font-size:12px;font-weight:700;color:#10B981;
                    text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px;'>⬆️ Rising</div>""",
                unsafe_allow_html=True)
            for r in risers[:5]:
                st.markdown(f"<div style='font-size:13px;font-weight:600;color:#14532D;"
                            f"margin-bottom:4px;'>+{r['Δ']} · {r['Entity']}</div>",
                            unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with t2:
            st.markdown("""<div style='background:#FEF2F2;border-radius:10px;padding:14px 16px;'>
                <div style='font-size:12px;font-weight:700;color:#EF4444;
                    text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px;'>⬇️ Falling</div>""",
                unsafe_allow_html=True)
            for r in fallers[:5]:
                st.markdown(f"<div style='font-size:13px;font-weight:600;color:#7F1D1D;"
                            f"margin-bottom:4px;'>{r['Δ']} · {r['Entity']}</div>",
                            unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with t3:
            st.markdown("""<div style='background:#EFF6FF;border-radius:10px;padding:14px 16px;'>
                <div style='font-size:12px;font-weight:700;color:#4F5BDB;
                    text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px;'>🆕 New This Run</div>""",
                unsafe_allow_html=True)
            for r in new_ent[:5]:
                st.markdown(f"<div style='font-size:13px;font-weight:600;color:#1E3A8A;"
                            f"margin-bottom:4px;'>{r['Entity']}</div>",
                            unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    sc1, sc2 = st.columns([2,1])
    scope = sc1.radio("Scope", ["All Time", "Latest Run"], horizontal=True)
    top_n = sc2.selectbox("Show top", [10, 20, 30], index=1)
    params = {"limit": top_n}
    if scope == "Latest Run": params["run_id"] = sel
    entities = api_get("/api/entities", params)
    if entities:
        section_header("Top Entities by Mention Count")
        st.bar_chart(pd.DataFrame(entities).set_index("entity")["count"])


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: SOTA WATCH
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🔭  SOTA Watch":
    status, is_running = sync_pipeline_state()
    pipeline_banner()

    st.markdown("""<div style='margin-bottom:20px;'>
        <div style='font-size:22px;font-weight:800;color:#1C2340;letter-spacing:-0.03em;'>🔭 SOTA Watch</div>
        <div style='color:#8492A6;font-size:13px;margin-top:3px;'>Benchmark leaderboard movements — who moved up or down</div>
    </div>""", unsafe_allow_html=True)

    runs      = api_get("/api/runs", {"limit": 10})
    completed = [r for r in runs if r.get("status") == "completed"]
    if not completed:
        st.info("No completed runs yet.")
        st.stop()

    opts   = {f"Run {r['run_id'][:8]}  ·  {str(r.get('started_at',''))[:16]}": r["run_id"] for r in completed}
    sel    = opts[st.selectbox("Select Run", list(opts.keys()))]
    sota   = api_get(f"/api/sota-watch/{sel}")
    events = sota.get("sota_watch", [])

    if not events:
        st.info("No leaderboard movements this run. SOTA Watch activates when HF Benchmark findings appear across multiple runs.")
        st.markdown("---")
        section_header("📊 HF Benchmark Findings")
        for f in api_get("/api/findings", {"category":"hf_benchmarks","limit":20}):
            signal_card(f)
    else:
        section_header(f"📊 {len(events)} Leaderboard Movement(s)")
        for event in events:
            delta    = event.get("delta", 0)
            movement = event.get("movement", "")
            icon     = "⬆️" if movement == "up" else "⬇️"
            with st.expander(f"{icon} {event.get('title','')}  ·  ({'+' if delta > 0 else ''}{delta:.1f} pts)"):
                c1, c2 = st.columns(2)
                c1.metric("Current Score",  f"{event.get('current_score',0):.1f}")
                c2.metric("Previous Score", f"{event.get('previous_score',0):.1f}", delta=f"{delta:.1f}")
                st.caption(f"Source: {event.get('source_url','')}")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: FINDINGS EXPLORER
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🔍  Findings Explorer":
    status, is_running = sync_pipeline_state()
    pipeline_banner()

    st.markdown("""<div style='margin-bottom:20px;'>
        <div style='font-size:22px;font-weight:800;color:#1C2340;letter-spacing:-0.03em;'>🔍 Findings Explorer</div>
        <div style='color:#8492A6;font-size:13px;margin-top:3px;'>Search, filter, and deep-dive into every signal</div>
    </div>""", unsafe_allow_html=True)

    # Filters
    fc1, fc2, fc3, fc4 = st.columns([2,3,2,1])
    cat_f   = fc1.selectbox("Category", ["All","competitors","model_providers","research","hf_benchmarks"],
                format_func=lambda x: CAT_LABEL.get(x,x) if x!="All" else "All")
    search  = fc2.text_input("Search", placeholder="GPT-5 · benchmark · pricing…")
    clust_f = fc3.selectbox("Cluster", ["All","model releases","benchmarks & evals",
                "safety & alignment","agents & reasoning","multimodal",
                "infrastructure","research","open source","general"])
    limit   = fc4.selectbox("Show", [25,50,100,200], index=1)

    params: dict = {"limit": limit}
    if cat_f   != "All": params["category"] = cat_f
    if search:           params["search"]   = search
    if clust_f != "All": params["cluster"]  = clust_f

    findings = api_get("/api/findings", params)
    st.caption(f"{len(findings)} signals match your filters")

    if findings:
        df = pd.DataFrame([{
            "Score":     f.get("final_score",0),
            "Priority":  (f.get("priority") or "medium").upper(),
            "Status":    f.get("change_status","new"),
            "Title":     f.get("title","")[:80],
            "Category":  CAT_LABEL.get(f.get("category",""),f.get("category","")),
            "Cluster":   f.get("topic_cluster","general"),
            "Publisher": f.get("publisher","—"),
            "URL":       f.get("source_url",""),
        } for f in findings])

        st.dataframe(df, use_container_width=True, hide_index=True,
            column_config={
                "Score":    st.column_config.NumberColumn(format="%.2f", width="small"),
                "URL":      st.column_config.LinkColumn("Source", width="medium"),
                "Title":    st.column_config.TextColumn("Title",  width="large"),
                "Priority": st.column_config.TextColumn("Priority", width="small"),
            })

        st.markdown("---")
        section_header("📄 Signal Detail View")
        titles  = [f.get("title","")[:80] for f in findings]
        sel_t   = st.selectbox("Select a signal to inspect", titles)
        finding = next((f for f in findings if f.get("title","").startswith(sel_t[:30])), None)
        if finding:
            signal_card(finding, expanded=True)
    else:
        st.info("No signals match your filters.")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: SOURCES
# ═════════════════════════════════════════════════════════════════════════════
elif page == "⚙️  Sources":
    st.markdown("""<div style='margin-bottom:20px;'>
        <div style='font-size:22px;font-weight:800;color:#1C2340;letter-spacing:-0.03em;'>⚙️ Source Management</div>
        <div style='color:#8492A6;font-size:13px;margin-top:3px;'>Configure crawl sources per agent — changes take effect next run</div>
    </div>""", unsafe_allow_html=True)

    with st.form("add_source", clear_on_submit=True):
        section_header("➕ Add New Source")
        c1, c2, c3 = st.columns([2,4,2])
        name       = c1.text_input("Name *", placeholder="Mistral Blog")
        url        = c2.text_input("URL *",  placeholder="https://mistral.ai/news")
        agent_type = c3.selectbox("Agent *", ["competitors","model_providers","research","hf_benchmarks"],
                        format_func=lambda x: CAT_LABEL.get(x,x))
        if st.form_submit_button("Add Source", type="primary"):
            if not name.strip():             st.error("Name is required")
            elif not url.startswith("http"): st.error("URL must start with http://")
            else:
                try:
                    r = requests.post(f"{API_URL}/api/sources",
                        json={"name":name.strip(),"url":url.strip(),"agent_type":agent_type}, timeout=5)
                    if r.ok:                   st.success(f"✅ Added: {name}"); st.rerun()
                    elif r.status_code == 400: st.warning("URL already exists.")
                    else:                      st.error(f"Failed: {r.text}")
                except Exception as e: st.error(str(e))

    st.markdown("---")
    section_header("📡 Active Sources")
    sources = api_get("/api/sources")
    if sources:
        for src in sources:
            c1,c2,c3,c4,c5,c6 = st.columns([2,4,2,2,1,1])
            c1.write(f"**{src.get('name','')}**")
            c2.caption(src.get("url",""))
            c3.caption(CAT_LABEL.get(src.get("agent_type",""), src.get("agent_type","")))
            ls = src.get("last_seen_at")
            c4.caption(f"Last: {str(ls)[:16] if ls else 'Never'}")
            c5.caption(f"#{src['id']}")
            if c6.button("🗑", key=f"del_{src['id']}", help="Remove source"):
                try:
                    r = requests.delete(f"{API_URL}/api/sources/{src['id']}", timeout=5)
                    if r.ok: st.success("Removed"); st.rerun()
                except Exception as e: st.error(str(e))
    else:
        st.info("No sources configured. Add one above or trigger a run to auto-seed from config.yaml.")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: RUN HISTORY
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📁  Run History":
    status, is_running = sync_pipeline_state()
    pipeline_banner()

    st.markdown("""<div style='margin-bottom:20px;'>
        <div style='font-size:22px;font-weight:800;color:#1C2340;letter-spacing:-0.03em;'>📁 Run History</div>
        <div style='color:#8492A6;font-size:13px;margin-top:3px;'>All pipeline runs with agent breakdowns and PDF downloads</div>
    </div>""", unsafe_allow_html=True)

    runs = api_get("/api/runs")
    if not runs:
        st.info("No runs yet.")
        st.stop()

    STATUS_ICON = {"completed":"✅","failed":"❌","running":"⏳"}
    STATUS_CLR  = {"completed":"#10B981","failed":"#EF4444","running":"#4F5BDB"}

    for run in runs:
        run_status = run.get("status","unknown")
        run_id     = run.get("run_id","")
        found      = run.get("total_found",0)
        elapsed    = run.get("elapsed_sec")
        icon       = STATUS_ICON.get(run_status, "❓")
        label      = f"{icon}  {str(run.get('started_at',''))[:16]}  ·  {run_status.upper()}  ·  {found} signals"
        if elapsed: label += f"  ·  {elapsed:.0f}s"

        with st.expander(label, expanded=(run_status == "running")):
            r1, r2, r3 = st.columns(3)
            r1.write(f"**Run ID:** `{run_id[:8]}...`")
            r1.write(f"**Status:** {run_status}")
            r2.write(f"**Started:** {str(run.get('started_at',''))[:19]}")
            r2.write(f"**Finished:** {str(run.get('finished_at',''))[:19] or 'In progress...'}")
            r3.write(f"**Signals:** {found}")
            if elapsed: r3.write(f"**Elapsed:** {elapsed:.0f}s")

            fbc = run.get("findings_by_category", {})
            if fbc:
                st.markdown("**By Category:**")
                cc = st.columns(len(fbc))
                for i,(cat,count) in enumerate(fbc.items()):
                    cc[i].metric(f"{CAT_ICON.get(cat,'📌')} {cat}", count)

            ast2 = run.get("agent_status", {})
            if ast2:
                st.markdown("**Per-Agent:**")
                ac = st.columns(len(ast2))
                for i,(name,info) in enumerate(ast2.items()):
                    ic  = "✅" if info.get("status")=="ok" else ("⏱️" if info.get("status")=="timeout" else "❌")
                    lbl = f"{info.get('found',0)} signals"
                    if info.get("elapsed_sec"): lbl += f" · {info['elapsed_sec']}s"
                    ac[i].metric(f"{ic} {name}", lbl)

            if run.get("pdf_path"):
                st.markdown(f"[📥 Download PDF]({API_URL}/api/digest/{run_id}/pdf)")

            if run_status == "failed" and run.get("error_log"):
                with st.expander("❌ Error Log"):
                    st.code(run["error_log"], language="text")

            if st.button("📋 View Top Findings", key=f"view_{run_id}"):
                for f in api_get(f"/api/findings/{run_id}")[:5]:
                    score = f.get("final_score", 0)
                    badge = "🆕" if f.get("change_status") == "new" else "🔄"
                    st.write(f"• {badge} [{score:.1f}] **{f.get('title','')}**")
                    st.caption(f.get("summary","")[:100] + "...")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: DIGEST ARCHIVE
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📚  Digest Archive":
    st.markdown("""<div style='margin-bottom:20px;'>
        <div style='font-size:22px;font-weight:800;color:#1C2340;letter-spacing:-0.03em;'>📚 Digest Archive</div>
        <div style='color:#8492A6;font-size:13px;margin-top:3px;'>All past PDF digests — browse, search, download</div>
    </div>""", unsafe_allow_html=True)

    runs      = api_get("/api/runs")
    completed = [r for r in runs if r.get("status") == "completed" and r.get("pdf_path")]
    if not completed:
        st.info("No digests yet. Run the pipeline to generate your first digest.")
        st.stop()

    search = st.text_input("🔍 Search by date or run ID", placeholder="2026-03-05 or b6d68b8f")
    if search:
        completed = [r for r in completed if
                     search.lower() in str(r.get("started_at","")).lower() or
                     search.lower() in r.get("run_id","").lower()]

    st.caption(f"**{len(completed)} digest(s)** available")
    st.markdown("---")

    for run in completed:
        run_id  = run.get("run_id","")
        started = str(run.get("started_at",""))[:16]
        found   = run.get("total_found", 0)
        elapsed = run.get("elapsed_sec")
        fbc     = run.get("findings_by_category", {})

        with st.expander(f"📄  {started}  ·  {found} signals", expanded=False):
            c1, c2 = st.columns(2)
            c1.write(f"**Run:** `{run_id[:8]}...`")
            c1.write(f"**Date:** {started}")
            c2.write(f"**Signals:** {found}")
            if elapsed: c2.write(f"**Elapsed:** {elapsed:.0f}s")
            if fbc:
                st.caption("  ·  ".join(f"{CAT_ICON.get(k,'📌')} {k}: {v}" for k,v in fbc.items()))
            st.markdown(f"[📥 Open PDF in browser]({API_URL}/api/digest/{run_id}/pdf)")
            if st.button("👁 Preview signals", key=f"prev_{run_id}"):
                for f in api_get(f"/api/findings/{run_id}")[:5]:
                    score = f.get("final_score",0) or 0
                    st.write(f"**[{score:.1f}]** {f.get('title','')}")
                    st.caption(f.get("summary","")[:120] + "...")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: EMAIL RECIPIENTS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📧  Email Recipients":
    st.markdown("""<div style='margin-bottom:20px;'>
        <div style='font-size:22px;font-weight:800;color:#1C2340;letter-spacing:-0.03em;'>📧 Email Recipients</div>
        <div style='color:#8492A6;font-size:13px;margin-top:3px;'>Manage distribution list — configurable recipients for daily digest</div>
    </div>""", unsafe_allow_html=True)

    st.info("📬 Uses **SendGrid API** — sends to any email address with no domain verification required.")

    section_header("📋 Current Recipients")
    recipients = api_get("/api/email-recipients") or []

    if not recipients:
        st.warning("No recipients yet. Add one below.")
    else:
        active_list   = [r for r in recipients if r.get("is_active",1)]
        inactive_list = [r for r in recipients if not r.get("is_active",1)]
        st.caption(f"{len(active_list)} active · {len(inactive_list)} paused · {len(recipients)} total")

        for rec in recipients:
            rid    = rec.get("id")
            email  = rec.get("email","")
            name   = rec.get("name") or ""
            note   = rec.get("note") or ""
            active = rec.get("is_active",1)
            label  = f"{'✅' if active else '⏸'} **{email}**" + (f"  ·  {name}" if name else "")
            with st.expander(label, expanded=False):
                c1,c2,c3,c4 = st.columns([3,2,1,1])
                c1.write(f"**Email:** {email}")
                c2.write(f"**Name:** {name or '—'}")
                if note: st.caption(f"Note: {note}")
                if c3.button("⏸ Pause" if active else "▶️ Resume", key=f"tog_{rid}"):
                    try:
                        r = requests.patch(f"{API_URL}/api/email-recipients/{rid}/toggle", timeout=5)
                        if r.ok: st.rerun()
                        else: st.error(r.json().get("detail","Failed"))
                    except Exception as e: st.error(str(e))
                if c4.button("🗑 Remove", key=f"del_r_{rid}"):
                    try:
                        r = requests.delete(f"{API_URL}/api/email-recipients/{rid}", timeout=5)
                        if r.ok: st.success(f"Removed: {email}"); st.rerun()
                        else: st.error(r.json().get("detail","Failed"))
                    except Exception as e: st.error(str(e))

    st.markdown("---")
    section_header("➕ Add Recipient")
    a1, a2, a3 = st.columns([3,2,2])
    new_email = a1.text_input("Email *", placeholder="researcher@company.com", key="new_email")
    new_name  = a2.text_input("Name",    placeholder="Dr. Smith",              key="new_name")
    new_note  = a3.text_input("Note",    placeholder="Research team lead",     key="new_note")
    if st.button("➕ Add Recipient", type="primary"):
        if not new_email or "@" not in new_email:
            st.error("Please enter a valid email address")
        else:
            try:
                r = requests.post(f"{API_URL}/api/email-recipients",
                    json={"email":new_email,"name":new_name or None,"note":new_note or None}, timeout=5)
                if r.status_code == 200:   st.success(f"✅ Added: {new_email}"); st.rerun()
                elif r.status_code == 409: st.warning("This email is already in the list")
                else:                      st.error(r.json().get("detail","Failed"))
            except Exception as e: st.error(str(e))

    st.markdown("---")
    section_header("🧪 Test Email Delivery", "Sends immediately — no pipeline run needed")
    t1, t2 = st.columns([4,1])
    test_addr = t1.text_input("Send test to", placeholder="your@email.com", key="test_email")
    if t2.button("📤 Send Test", type="secondary"):
        if not test_addr or "@" not in test_addr:
            st.error("Valid email required")
        else:
            with st.spinner("Sending…"):
                try:
                    r = requests.post(f"{API_URL}/api/email-recipients/test",
                        json={"email":test_addr}, timeout=15)
                    if r.ok:
                        st.success(f"✅ Sent to **{test_addr}** via {r.json().get('provider','SendGrid')}")
                        st.caption("Check inbox + spam — arrives within 30s")
                    else:
                        st.error(f"Failed: {r.json().get('detail','Unknown error')}")
                except Exception as e: st.error(str(e))


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: SCHEDULE
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📅  Schedule":
    status, is_running = sync_pipeline_state()
    pipeline_banner()

    st.markdown("""<div style='margin-bottom:20px;'>
        <div style='font-size:22px;font-weight:800;color:#1C2340;letter-spacing:-0.03em;'>📅 Schedule & System Status</div>
        <div style='color:#8492A6;font-size:13px;margin-top:3px;'>Scheduling, configuration, and system health</div>
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        section_header("⏰ Next Scheduled Run")
        next_run = status.get("next_scheduled")
        if next_run:
            try:
                next_dt = datetime.fromisoformat(next_run)
                st.metric("Next Run", next_dt.strftime("%Y-%m-%d %H:%M %Z"))
                delta = next_dt.replace(tzinfo=None) - datetime.utcnow()
                h = int(delta.total_seconds() // 3600)
                m = int((delta.total_seconds() % 3600) // 60)
                st.caption(f"Runs in approximately {h}h {m}m")
            except:
                st.write(next_run)
        else:
            st.warning("Scheduler not active")

    with c2:
        section_header("📊 System Stats")
        st.metric("Total Signals", status.get("total_findings",0))
        st.metric("Total Runs",    status.get("total_runs",0))
        st.metric("Completed",     status.get("completed_runs",0))

    st.markdown("---")
    section_header("🔑 Configuration Status")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**🤖 LLM Provider**")
        st.write(status.get("llm_status","❌ Not configured"))
        st.markdown("**📧 Email Provider**")
        st.write(status.get("email_status","❌ Not configured"))
    with col_b:
        st.markdown("**👥 Active Recipients**")
        active_recipients = status.get("active_recipients", 0)
        if active_recipients > 0:
            st.success(f"✅ {active_recipients} recipient(s) configured")
        else:
            st.warning("⚠️ No recipients — add them in 📧 Email Recipients")

    st.markdown("---")
    section_header("⚙️ Schedule Configuration")
    st.info("Edit `backend/config.yaml` to change schedule:\n```yaml\nglobal:\n  run_time: '07:00'\n  timezone: 'Asia/Kolkata'\n```\nRestart the API to apply.")

    st.markdown("---")
    section_header("🔗 Quick Links")
    q1, q2, q3, q4 = st.columns(4)
    q1.markdown(f"[📡 API Docs]({API_URL}/docs)")
    q2.markdown(f"[🗄 DB Explorer]({API_URL}/admin/db)")
    q3.markdown(f"[📊 Metrics JSON]({API_URL}/metrics)")
    q4.markdown(f"[❤ Health Check]({API_URL}/health)")