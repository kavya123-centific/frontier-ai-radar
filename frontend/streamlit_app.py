"""
streamlit_app.py — Frontier AI Radar v4.2
Enterprise Intelligence Platform
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

# ── Sidebar: always open, correct width, no collapse arrow ───────────────────
st.markdown("""
<style>
/* Hide every collapse/expand button variant */
[data-testid="collapsedControl"],
button[data-testid="baseButton-headerNoPadding"],
[data-testid="stSidebarCollapsedControl"] { display: none !important; }

/* Sidebar container — always 260px, never slides away */
section[data-testid="stSidebar"],
[data-testid="stSidebar"] {
    width: 260px !important;
    min-width: 260px !important;
    max-width: 260px !important;
    transform: none !important;
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* Inner div that Streamlit sometimes shrinks */
section[data-testid="stSidebar"] > div:first-child {
    width: 260px !important;
    min-width: 260px !important;
    padding-top: 1rem !important;
}
</style>
""", unsafe_allow_html=True)

# ── Light Intelligence Dashboard CSS ─────────────────────────────────────────
st.markdown("""
<style>

/* ---------- GLOBAL ---------- */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
.stApp { background-color: #f8fafc; }
.block-container { padding: 1.5rem 2rem; max-width: 1400px; }

/* Remove Streamlit chrome */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }

/* ---------- SIDEBAR ---------- */
[data-testid="stSidebar"] {
    background: white !important;
    border-right: 1px solid #e5e7eb !important;
}
[data-testid="stSidebar"] * { color: #374151 !important; }
[data-testid="stSidebar"] .stRadio label { 
    font-size: 13px !important; 
    font-weight: 500 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}

/* ---------- METRIC CARDS ---------- */
[data-testid="metric-container"] {
    background: white;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    border: 1px solid #e5e7eb;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
[data-testid="metric-container"] label {
    color: #6b7280 !important;
    font-size: 11px !important;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-weight: 600 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #111827 !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}

/* ---------- EXPANDERS ---------- */
[data-testid="stExpander"] {
    background: white;
    border-radius: 10px;
    border: 1px solid #e5e7eb !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    margin-bottom: 8px;
}

/* ---------- DATA TABLE ---------- */
[data-testid="stDataFrame"] {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
}

/* ---------- BUTTONS ---------- */
.stButton button {
    background: #2563eb;
    color: white;
    border-radius: 8px;
    border: none;
    font-weight: 500;
    font-size: 13px;
}
.stButton button:hover { background: #1d4ed8; color: white; }
button[kind="primary"] {
    background: #2563eb !important;
    color: white !important;
    border: none !important;
}

/* ---------- INPUTS ---------- */
.stTextInput input, .stSelectbox select {
    background: white !important;
    border-color: #d1d5db !important;
    color: #111827 !important;
    font-size: 13px !important;
    border-radius: 8px !important;
}

/* ---------- HEADINGS ---------- */
h1 { color: #111827 !important; font-weight: 700 !important; font-size: 1.75rem !important; letter-spacing: -0.02em; }
h2 { color: #374151 !important; font-weight: 600 !important; font-size: 1.1rem !important; }
h3 { color: #6b7280 !important; font-size: 0.95rem !important; font-weight: 600 !important; }
p, li { color: #4b5563; }

/* ---------- SCORE COLORS ---------- */
.score-hi  { color: #16a34a; font-weight: 700; }
.score-mid { color: #d97706; font-weight: 700; }
.score-lo  { color: #ef4444; font-weight: 700; }

/* ---------- BADGES ---------- */
.badge-new { background: #dbeafe; color: #1d4ed8; padding: 3px 9px; border-radius: 6px; font-size: 11px; font-weight: 600; }
.badge-upd { background: #dcfce7; color: #15803d; padding: 3px 9px; border-radius: 6px; font-size: 11px; font-weight: 600; }
.badge-unc { background: #f3f4f6; color: #6b7280; padding: 3px 9px; border-radius: 6px; font-size: 11px; font-weight: 600; }

/* ---------- STATUS DOTS ---------- */
.status-ok   { color: #16a34a; font-weight: 600; }
.status-fail { color: #ef4444; font-weight: 600; }

/* ---------- TREND COLORS ---------- */
.trend-up { color: #16a34a; font-weight: 700; }
.trend-dn { color: #ef4444; font-weight: 700; }
.mono     { font-family: 'SF Mono', monospace; font-size: 12px; color: #6b7280; }

/* ---------- PROGRESS BAR ---------- */
.stProgress > div > div { background: #2563eb !important; }

/* ---------- HORIZONTAL RULE ---------- */
hr { border-color: #e5e7eb !important; }

/* ---------- ALERT / INFO BOX ---------- */
.stAlert { border-radius: 8px !important; }

/* ---------- SIDEBAR NAV ACTIVE ---------- */
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] input:checked + div {
    border-color: #2563eb !important;
}

</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
_LIST = ["findings","runs","sources","entities","snapshots","clusters","changes","email-recipients"]

CAT_ICON   = {"competitors":"🏢","model_providers":"🤖","research":"📄","hf_benchmarks":"📊"}
CAT_LABEL  = {"competitors":"Competitors","model_providers":"Model Providers",
              "research":"Research","hf_benchmarks":"HF Benchmarks"}
CAT_COLOR  = {"competitors":"🔴","model_providers":"🔵","research":"🟢","hf_benchmarks":"🟡"}
CONF_LABEL = {1.0:"Official Source",0.8:"Lab Blog / Docs",0.6:"Third-party"}

# ── Helpers ───────────────────────────────────────────────────────────────────
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_URL}{path}", params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.Timeout:
        if any(x in path for x in ["status","runs"]):
            st.info("⏳ Pipeline running — refresh in ~60s")
        return [] if any(x in path for x in _LIST) else {}
    except requests.ConnectionError:
        st.error("❌ Cannot reach API. Check BACKEND_URL in Streamlit secrets.")
        st.stop()
    except Exception as e:
        if "timed out" in str(e).lower():
            return [] if any(x in path for x in _LIST) else {}
        st.error(f"API error: {e}")
        return [] if any(x in path for x in _LIST) else {}

def score_color(s):
    if s >= 7: return "score-hi"
    if s >= 4: return "score-mid"
    return "score-lo"

def change_badge(status):
    if status == "new":     return '<span class="badge-new">NEW</span>'
    if status == "updated": return '<span class="badge-upd">UPDATED</span>'
    return '<span class="badge-unc">UNCHANGED</span>'

def impact_bar(score):
    """Colored impact label for expanders."""
    if score >= 7:   st.success("🟢 High strategic impact")
    elif score >= 4: st.warning("🟡 Medium impact")
    else:            st.info("🔵 Informational signal")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:1rem 0 0.5rem;display:flex;align-items:center;gap:10px;'>
        <span style='font-size:26px;'>🛰</span>
        <div>
            <div style='font-size:17px;color:#111827;font-weight:700;letter-spacing:-0.01em;'>
                Frontier AI Radar
            </div>
            <div style='font-size:11px;color:#9ca3af;margin-top:1px;'>
                v4.2 · Intelligence Platform
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<hr style="border-color:#e5e7eb;margin:0.5rem 0;">', unsafe_allow_html=True)

    page = st.radio("Navigation", [
        "📊 Dashboard",
        "🔄 What Changed",
        "🎯 Impact Analysis",
        "📈 Observability",
        "🏷️ Entity Dashboard",
        "🔭 SOTA Watch",
        "🔍 Findings Explorer",
        "⚙️ Sources",
        "📁 Run History",
        "📚 Digest Archive",
        "📧 Email Recipients",
        "📅 Schedule",
    ], label_visibility="collapsed")

    st.markdown('<hr style="border-color:#e5e7eb;margin:0.5rem 0;">', unsafe_allow_html=True)

    if st.button("🚀 Trigger Run", type="primary", use_container_width=True):
        try:
            r = requests.post(f"{API_URL}/api/runs/trigger", timeout=5)
            if r.status_code == 200:
                st.success("Run started — ~90s")
            elif r.status_code == 409:
                st.warning("Already running")
            else:
                st.error(f"Error {r.status_code}")
        except requests.ConnectionError:
            st.error("API offline")

    with st.expander("⚙️ Ops"):
        if st.button("Recover Stale Runs", key="recover"):
            try:
                r = requests.post(f"{API_URL}/api/runs/recover", timeout=5)
                st.success(r.json().get("message","Done") if r.ok else f"Failed: {r.status_code}")
            except Exception as e:
                st.error(str(e))

        # ── Internal reset (not labelled obviously) ──────────────────────────
        st.markdown("""
        <div style='margin-top:8px;border-top:1px solid #f3f4f6;padding-top:6px;'>
        </div>""", unsafe_allow_html=True)
        if "reset_confirm" not in st.session_state:
            st.session_state.reset_confirm = False

        if not st.session_state.reset_confirm:
            if st.button("🗑 reset db", key="reset_db_init",
                         help="Wipe all data",
                         use_container_width=True):
                st.session_state.reset_confirm = True
                st.rerun()
        else:
            st.caption("⚠️ This will delete ALL runs, findings, sources.")
            col_y, col_n = st.columns(2)
            if col_y.button("Yes, wipe", key="reset_yes", type="primary"):
                try:
                    r = requests.post(f"{API_URL}/api/admin/reset-db", timeout=10)
                    if r.ok:
                        st.session_state.reset_confirm = False
                        st.success("DB wiped ✓")
                    else:
                        st.error(f"Failed: {r.status_code}")
                except Exception as e:
                    st.error(str(e))
            if col_n.button("Cancel", key="reset_no"):
                st.session_state.reset_confirm = False
                st.rerun()

    st.markdown('<hr style="border-color:#e5e7eb;margin:0.5rem 0;">', unsafe_allow_html=True)

    try:
        h = requests.get(f"{API_URL}/health", timeout=3)
        if h.ok:
            st.markdown('<span class="status-ok">● API Online</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-fail">● API Degraded</span>', unsafe_allow_html=True)
    except:
        st.markdown('<span class="status-fail">● API Offline</span>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "📊 Dashboard":

    # Header
    col_logo, col_title = st.columns([1, 11])
    with col_logo:
        st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=52)
    with col_title:
        st.title("Frontier AI Radar")
        st.caption("Autonomous Multi-Agent Intelligence · Tracking frontier AI developments daily")

    status   = api_get("/api/status")
    findings = api_get("/api/findings", {"limit": 100})

    # KPI cards
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Signals Detected",   status.get("total_findings", 0))
    c2.metric("Runs Completed",     status.get("completed_runs", 0))
    c3.metric("Sources Monitored",  len(api_get("/api/sources")))
    c4.metric("Pipeline Status",    "▶ Running" if status.get("is_running") else "● Idle")

    # Live pipeline progress
    if status.get("is_running"):
        ps       = api_get("/api/pipeline-status")
        stage    = ps.get("stage","Running")
        progress = ps.get("progress", 0)
        detail   = ps.get("detail","")
        st.markdown(f"""
        <div style='background:white;border:1px solid #e5e7eb;border-radius:10px;
                    padding:1rem 1.5rem;margin:1rem 0;box-shadow:0 2px 6px rgba(0,0,0,0.04);'>
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>
                <span style='color:#2563eb;font-size:13px;font-weight:600;'>
                    ⚡ PIPELINE RUNNING — {stage}
                </span>
                <span style='color:#9ca3af;font-size:12px;'>{progress}%</span>
            </div>
            <div style='background:#f3f4f6;border-radius:4px;height:6px;'>
                <div style='background:#2563eb;height:6px;border-radius:4px;width:{progress}%;'></div>
            </div>
            <div style='color:#9ca3af;font-size:11px;margin-top:6px;'>{detail}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    if not findings:
        st.info("No intelligence signals yet. Click **🚀 Trigger Run** to start.")
        st.stop()

    # Executive Intelligence Brief
    st.subheader("🧠 Executive Intelligence Brief")
    for f in findings[:5]:
        score = f.get("final_score", 0) or 0
        icon  = "🆕" if f.get("change_status") == "new" else "🔄"
        st.markdown(f"""
        <div style='background:white;border:1px solid #e5e7eb;border-radius:10px;
                    padding:1rem 1.25rem;margin:6px 0;box-shadow:0 1px 4px rgba(0,0,0,0.04);'>
            <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
                <div style='flex:1;'>
                    <div style='font-weight:600;color:#111827;font-size:14px;'>
                        {icon} {f.get('title','')}
                    </div>
                    <div style='color:#6b7280;font-size:13px;margin-top:4px;'>
                        {f.get('why_matters','') or f.get('summary','')[:120]}
                    </div>
                </div>
                <div style='margin-left:1rem;text-align:right;flex-shrink:0;'>
                    <div style='font-size:20px;font-weight:700;color:{"#16a34a" if score>=7 else "#d97706" if score>=4 else "#ef4444"};'>
                        {score:.1f}
                    </div>
                    <div style='font-size:10px;color:#9ca3af;'>/ 10</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Top Signals
    st.subheader("🏆 Top Intelligence Signals")
    for i, f in enumerate(findings[:6], 1):
        score  = f.get("final_score",0) or 0
        conf   = f.get("confidence_score",0.8) or 0.8
        change = f.get("change_status","new")
        cat    = f.get("category","")
        icon   = "🆕" if change == "new" else "🔄"

        with st.expander(
            f"{icon} {f.get('title','')} — Score: {score:.1f}/10",
            expanded=(i==1)
        ):
            impact_bar(score)
            col1, col2 = st.columns([3,1])
            with col1:
                st.write(f.get("summary",""))
                if f.get("why_matters"):
                    st.markdown(f"""
                    <div style='background:#eff6ff;border-left:3px solid #2563eb;
                                padding:0.6rem 1rem;border-radius:0 8px 8px 0;margin:0.5rem 0;
                                color:#1e40af;font-size:13px;'>
                        💡 {f['why_matters']}
                    </div>
                    """, unsafe_allow_html=True)
                if f.get("evidence"):
                    st.markdown(f"""
                    <div style='background:#f0fdf4;border-left:3px solid #16a34a;
                                padding:0.6rem 1rem;border-radius:0 8px 8px 0;margin:0.5rem 0;
                                color:#15803d;font-size:12px;'>
                        📎 {f['evidence']}
                    </div>
                    """, unsafe_allow_html=True)
            with col2:
                st.metric("Impact Score", f"{score:.1f}/10")
                st.metric("Confidence",   f"{conf:.0%}")
                st.caption(f"{CAT_COLOR.get(cat,'')} {CAT_LABEL.get(cat,cat)}")
                st.caption(f"🏷️ {f.get('topic_cluster','general')}")
                if f.get("source_url"):
                    st.markdown(f"[🔗 Source]({f['source_url']})")

    st.markdown("---")

    # Charts
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📈 Signal Momentum")
        runs = api_get("/api/runs")
        if runs:
            data = [{"Date":str(r.get("started_at",""))[:10],"Signals":r.get("total_found",0)}
                    for r in runs if r.get("status")=="completed"]
            if data:
                st.area_chart(pd.DataFrame(data).set_index("Date"))
    with col_b:
        st.subheader("📂 By Category")
        cats = {}
        for f in findings:
            k = CAT_LABEL.get(f.get("category",""), f.get("category",""))
            cats[k] = cats.get(k,0) + 1
        if cats:
            st.bar_chart(pd.DataFrame(list(cats.items()),columns=["Category","Count"]).set_index("Category"))

    st.caption(f"Next run: {status.get('next_scheduled','N/A')} · v{status.get('version','')}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: WHAT CHANGED
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔄 What Changed":
    st.title("🔄 What Changed")
    st.caption("Signal delta between runs — NEW / UPDATED / UNCHANGED")

    runs      = api_get("/api/runs",{"limit":10})
    completed = [r for r in runs if r.get("status")=="completed"]
    if not completed:
        st.info("No completed runs yet.")
        st.stop()

    opts = {f"Run {r['run_id'][:8]} · {str(r.get('started_at',''))[:16]} · {r.get('total_found',0)} signals": r["run_id"]
            for r in completed}
    sel  = opts[st.selectbox("Select Run", list(opts.keys()))]
    chg  = api_get(f"/api/changes/{sel}")

    new_items = chg.get("new",[])
    upd_items = chg.get("updated",[])

    c1,c2,c3 = st.columns(3)
    c1.metric("🆕 New",      len(new_items))
    c2.metric("🔄 Updated",  len(upd_items))
    c3.metric("⏸ Unchanged", chg.get("unchanged",0))
    st.markdown("---")

    for label, items in [("🆕 New Signals", new_items), ("🔄 Updated Signals", upd_items)]:
        if items:
            st.subheader(f"{label} ({len(items)})")
            for f in items:
                score = f.get("final_score",0) or 0
                conf  = f.get("confidence_score",0.8) or 0.8
                with st.expander(f"[{score:.1f}] {f.get('title','')}"):
                    impact_bar(score)
                    c1,c2 = st.columns([3,1])
                    c1.write(f.get("summary",""))
                    if f.get("why_matters"): st.info(f"💡 {f['why_matters']}")
                    if f.get("evidence"):    st.success("📎 " + f["evidence"])
                    c2.metric("Confidence", f"{conf:.0%}")
                    c2.caption(f"🏷️ {f.get('topic_cluster','general')}")
                    if f.get("source_url"): c2.markdown(f"[🔗]({f['source_url']})")

    if not new_items and not upd_items:
        st.success("✅ All sources unchanged since last run.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: IMPACT ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎯 Impact Analysis":
    st.title("🎯 Impact Analysis")
    st.caption("Strategic scoring breakdown — Relevance · Novelty · Credibility · Actionability")

    findings = api_get("/api/findings", {"limit":20})
    if not findings:
        st.info("No findings yet. Trigger a run first.")
        st.stop()

    try:
        import plotly.graph_objects as go
        PLOTLY = True
    except ImportError:
        PLOTLY = False

    st.markdown("""
    <div style='background:white;border:1px solid #e5e7eb;border-radius:10px;
                padding:1rem 1.5rem;margin-bottom:1rem;box-shadow:0 1px 4px rgba(0,0,0,0.04);
                font-size:14px;color:#374151;'>
        <strong>Impact Formula:</strong>
        &nbsp; <span style='color:#2563eb;font-weight:600;'>0.35</span> × Relevance
        + <span style='color:#16a34a;font-weight:600;'>0.25</span> × Novelty
        + <span style='color:#7c3aed;font-weight:600;'>0.20</span> × Credibility
        + <span style='color:#d97706;font-weight:600;'>0.20</span> × Actionability
    </div>
    """, unsafe_allow_html=True)

    st.subheader("🎯 Signal Scoring Breakdown")
    top = findings[:6]

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
                fillcolor='rgba(37,99,235,0.10)',
                line=dict(color='#2563eb', width=2),
            ))
            fig.update_layout(
                polar=dict(
                    bgcolor='white',
                    radialaxis=dict(visible=True, range=[0,1], gridcolor='#e5e7eb',
                                   tickfont=dict(color='#9ca3af', size=9), tickvals=[0.25,0.5,0.75,1]),
                    angularaxis=dict(gridcolor='#e5e7eb', tickfont=dict(color='#374151', size=11)),
                ),
                paper_bgcolor='white',
                plot_bgcolor='white',
                font=dict(family='-apple-system,BlinkMacSystemFont,"Segoe UI"', color='#374151', size=11),
                margin=dict(l=40,r=40,t=50,b=20),
                height=280,
                title=dict(text=f.get("title","")[:45], font=dict(size=11, color='#111827')),
                showlegend=False,
            )
            cols[i%2].plotly_chart(fig, use_container_width=True)
    else:
        rows = []
        for f in top:
            score = f.get("final_score",0) or 0
            conf  = f.get("confidence_score",0.8) or 0.8
            rows.append({"Title":f.get("title","")[:60],"Score":score,"Confidence":f"{conf:.0%}","Cluster":f.get("topic_cluster","general")})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("💼 Strategic Implications")
    for f in findings[:4]:
        why = f.get("why_matters","")
        if why:
            st.markdown(f"""
            <div style='background:white;border:1px solid #e5e7eb;border-radius:10px;
                        padding:0.8rem 1.2rem;margin:6px 0;box-shadow:0 1px 4px rgba(0,0,0,0.04);'>
                <div style='font-weight:600;color:#111827;font-size:13px;margin-bottom:4px;'>
                    {f.get("title","")[:70]}
                </div>
                <div style='color:#6b7280;font-size:13px;'>{why}</div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: OBSERVABILITY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Observability":
    st.title("📈 Observability")
    st.caption("Agent performance · run history · signal distributions")

    metrics = api_get("/metrics")
    if not metrics or metrics.get("total_runs",0) == 0:
        st.info("No completed runs yet.")
        st.stop()

    k1,k2,k3,k4,k5,k6 = st.columns(6)
    k1.metric("Total Runs",      metrics.get("total_runs",0))
    k2.metric("Completed",       metrics.get("completed_runs",0))
    k3.metric("Failed",          metrics.get("failed_runs",0))
    k4.metric("Total Signals",   metrics.get("total_findings",0))
    k5.metric("Avg Elapsed (s)", metrics.get("avg_elapsed_sec",0))
    k6.metric("Avg Signals/Run", metrics.get("avg_findings_per_run",0))

    st.markdown("---")
    rot = metrics.get("runs_over_time",[])
    if rot:
        st.subheader("📅 Signals Per Run")
        st.bar_chart(pd.DataFrame(rot).set_index("date")["count"])

    st.markdown("---")
    ca,cb = st.columns(2)
    with ca:
        st.subheader("🤖 Per-Agent Performance")
        agents = metrics.get("agent_metrics",[])
        if agents:
            st.dataframe(
                pd.DataFrame(agents).rename(columns={
                    "name":"Agent","total_found":"Signals",
                    "success_runs":"OK","error_runs":"Errors","avg_elapsed":"Avg (s)"}),
                use_container_width=True, hide_index=True)
    with cb:
        st.subheader("🔄 Change Detection")
        cs = metrics.get("change_stats",{})
        if cs:
            st.bar_chart(pd.DataFrame(list(cs.items()),columns=["Status","Count"]).set_index("Status"))

    st.markdown("---")
    cc,cd = st.columns(2)
    with cc:
        st.subheader("📂 By Category")
        cd2 = metrics.get("findings_by_category",{})
        if cd2:
            st.bar_chart(pd.DataFrame(list(cd2.items()),columns=["Category","Count"]).set_index("Category"))
    with cd:
        st.subheader("🗂️ By Cluster")
        cl2 = metrics.get("findings_by_cluster",{})
        if cl2:
            st.bar_chart(pd.DataFrame(list(cl2.items()),columns=["Cluster","Count"]).set_index("Cluster"))

    st.markdown("---")
    st.subheader("🏢 Top Entities")
    te = metrics.get("top_entities",[])
    if te:
        st.bar_chart(pd.DataFrame(te[:15]).set_index("entity")["count"])


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ENTITY DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏷️ Entity Dashboard":
    st.title("🏷️ Entity Dashboard")
    st.caption("Entity mention trends vs prior run — mindshare tracking")

    runs      = api_get("/api/runs",{"limit":10})
    completed = [r for r in runs if r.get("status")=="completed"]
    if not completed:
        st.info("No completed runs yet.")
        st.stop()

    opts = {f"Run {r['run_id'][:8]} · {str(r.get('started_at',''))[:16]}": r["run_id"] for r in completed}
    sel  = opts[st.selectbox("Select Run", list(opts.keys()))]

    trends_data = api_get(f"/api/entity-trends/{sel}")
    trends      = trends_data.get("entity_trends",{})

    if trends:
        st.subheader("📈 Entity Mention Trends vs Prior Run")
        rows = []
        for entity, info in trends.items():
            trend = info.get("trend","stable")
            icon  = {"up":"⬆️","down":"⬇️","new":"🆕","stable":"➡️"}.get(trend,"")
            rows.append({
                "Entity":  entity.title(),
                "Trend":   f"{icon} {trend}",
                "Now":     info.get("current",0),
                "Before":  info.get("previous",0),
                "Δ":       info.get("delta",0),
            })
        rows.sort(key=lambda x: abs(x["Δ"]), reverse=True)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.markdown("---")
        t1,t2,t3 = st.columns(3)
        risers  = [r for r in rows if r["Δ"]>0]
        fallers = [r for r in rows if r["Δ"]<0]
        new_ent = [r for r in rows if "🆕" in r["Trend"]]
        with t1:
            st.markdown("**⬆️ Rising**")
            for r in risers[:5]:
                st.markdown(f'<span class="trend-up">+{r["Δ"]} {r["Entity"]}</span>', unsafe_allow_html=True)
        with t2:
            st.markdown("**⬇️ Falling**")
            for r in fallers[:5]:
                st.markdown(f'<span class="trend-dn">{r["Δ"]} {r["Entity"]}</span>', unsafe_allow_html=True)
        with t3:
            st.markdown("**🆕 New This Run**")
            for r in new_ent[:5]:
                st.markdown(f'<span style="color:#2563eb;font-weight:600;">{r["Entity"]}</span>', unsafe_allow_html=True)

    st.markdown("---")
    sc1,sc2 = st.columns([2,1])
    scope = sc1.radio("Scope",["All Time","Latest Run"],horizontal=True)
    top_n = sc2.selectbox("Show top",[10,20,30],index=1)
    params = {"limit":top_n}
    if scope == "Latest Run": params["run_id"] = sel
    entities = api_get("/api/entities", params)
    if entities:
        st.subheader(f"Top {len(entities)} Entities")
        st.bar_chart(pd.DataFrame(entities).set_index("entity")["count"])

    st.markdown("---")
    st.subheader("🗂️ Topic Clusters")
    clusters = api_get("/api/clusters",{"run_id":sel})
    if clusters:
        cols = st.columns(min(3,len(clusters)))
        for i,(name,items) in enumerate(clusters.items()):
            col = cols[i%3]
            col.markdown(f"**{name.title()}** ({len(items)})")
            for item in items[:4]:
                score = item.get("final_score",0) or 0
                badge = "🆕" if item.get("change_status")=="new" else "🔄"
                col.caption(f"{badge} [{score:.1f}] {item.get('title','')[:45]}...")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SOTA WATCH
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔭 SOTA Watch":
    st.title("🔭 SOTA Watch")
    st.caption("Benchmark leaderboard movements — who moved up or down")

    runs      = api_get("/api/runs",{"limit":10})
    completed = [r for r in runs if r.get("status")=="completed"]
    if not completed:
        st.info("No completed runs yet.")
        st.stop()

    opts = {f"Run {r['run_id'][:8]} · {str(r.get('started_at',''))[:16]}": r["run_id"] for r in completed}
    sel  = opts[st.selectbox("Select Run", list(opts.keys()))]
    sota = api_get(f"/api/sota-watch/{sel}")
    events = sota.get("sota_watch",[])

    if not events:
        st.info("No leaderboard movements this run. SOTA Watch activates when HF Benchmark findings appear across multiple runs.")
        st.markdown("---")
        st.subheader("📊 HF Benchmark Findings This Run")
        hf = api_get("/api/findings",{"category":"hf_benchmarks","limit":20})
        for f in hf:
            score = f.get("final_score",0) or 0
            with st.expander(f"[{score:.1f}] {f.get('title','')}"):
                impact_bar(score)
                st.write(f.get("summary",""))
                if f.get("evidence"): st.success("📎 "+f["evidence"])
    else:
        st.subheader(f"{len(events)} Leaderboard Movement(s)")
        for event in events:
            delta    = event.get("delta",0)
            movement = event.get("movement","")
            icon     = "⬆️" if movement=="up" else "⬇️"
            with st.expander(f"{icon} {event.get('title','')} ({'+' if delta>0 else ''}{delta:.1f} pts)"):
                c1,c2 = st.columns(2)
                c1.metric("Current Score",  f"{event.get('current_score',0):.1f}")
                c2.metric("Previous Score", f"{event.get('previous_score',0):.1f}", delta=f"{delta:.1f}")
                st.caption(f"Source: {event.get('source_url','')}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: FINDINGS EXPLORER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Findings Explorer":
    st.title("🔍 Findings Explorer")

    fc1,fc2,fc3,fc4 = st.columns([2,3,2,1])
    cat_f = fc1.selectbox("Category",
        ["All","competitors","model_providers","research","hf_benchmarks"],
        format_func=lambda x: CAT_LABEL.get(x,x) if x!="All" else "All")
    search  = fc2.text_input("Search", placeholder="GPT-5 · benchmark · pricing…")
    clust_f = fc3.selectbox("Cluster",
        ["All","model releases","benchmarks & evals","safety & alignment",
         "agents & reasoning","multimodal","infrastructure","research","open source","general"])
    limit = fc4.selectbox("Show",[25,50,100,200],index=1)

    params: dict = {"limit":limit}
    if cat_f   != "All": params["category"] = cat_f
    if search:           params["search"]   = search
    if clust_f != "All": params["cluster"]  = clust_f

    findings = api_get("/api/findings", params)
    st.caption(f"{len(findings)} signals matching filters")

    if findings:
        df = pd.DataFrame([{
            "Score":     f.get("final_score",0),
            "Conf":      f"{(f.get('confidence_score',0.8) or 0.8):.0%}",
            "Status":    f.get("change_status","new"),
            "Title":     f.get("title","")[:80],
            "Category":  CAT_LABEL.get(f.get("category",""),f.get("category","")),
            "Cluster":   f.get("topic_cluster","general"),
            "Publisher": f.get("publisher","—"),
            "URL":       f.get("source_url",""),
        } for f in findings])

        st.dataframe(df, use_container_width=True, hide_index=True,
            column_config={
                "Score": st.column_config.NumberColumn(format="%.2f", width="small"),
                "URL":   st.column_config.LinkColumn("Source", width="medium"),
                "Title": st.column_config.TextColumn("Title", width="large"),
            })

        st.markdown("---")
        st.subheader("📄 Signal Detail")
        titles  = [f.get("title","")[:80] for f in findings]
        sel_t   = st.selectbox("Select signal", titles)
        finding = next((f for f in findings if f.get("title","").startswith(sel_t[:30])), None)
        if finding:
            score  = finding.get("final_score",0) or 0
            conf   = finding.get("confidence_score",0.8) or 0.8
            change = finding.get("change_status","new")
            c1,c2  = st.columns([3,1])
            c1.markdown(f"### {finding.get('title')}")
            impact_bar(score)
            c2.metric("Score",      f"{score:.1f}/10")
            c2.metric("Confidence", f"{conf:.0%}")
            c2.caption({"new":"🆕 New","updated":"🔄 Updated","unchanged":"⏸ Unchanged"}.get(change,change))
            st.write(finding.get("summary",""))
            if finding.get("why_matters"): st.info(f"💡 {finding['why_matters']}")
            if finding.get("evidence"):    st.success("📎 **Evidence:** "+finding["evidence"])
            ca2,cb2 = st.columns(2)
            ca2.write(f"**Publisher:** {finding.get('publisher','—')}")
            ca2.write(f"**Cluster:** {finding.get('topic_cluster','general')}")
            if finding.get("source_url"):
                cb2.markdown(f"**Source:** [{finding.get('source_url','')[:50]}]({finding.get('source_url','')})")
            if finding.get("tags"):
                st.write("**Tags:** "+" ".join(f"`{t}`" for t in finding["tags"]))
            if finding.get("entities"):
                st.write("**Entities:** "+" · ".join(f"**{e}**" for e in finding["entities"]))
    else:
        st.info("No signals match filters.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SOURCES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Sources":
    st.title("⚙️ Source Management")
    st.caption("Configure crawl sources per agent — changes take effect next run")

    with st.form("add_source", clear_on_submit=True):
        st.subheader("➕ Add Source")
        c1,c2,c3 = st.columns([2,4,2])
        name       = c1.text_input("Name *", placeholder="Mistral Blog")
        url        = c2.text_input("URL *",  placeholder="https://mistral.ai/news")
        agent_type = c3.selectbox("Agent *",
            ["competitors","model_providers","research","hf_benchmarks"],
            format_func=lambda x: CAT_LABEL.get(x,x))
        if st.form_submit_button("Add Source", type="primary"):
            if not name.strip():                st.error("Name required")
            elif not url.startswith("http"):    st.error("URL must start with http://")
            else:
                try:
                    r = requests.post(f"{API_URL}/api/sources",
                        json={"name":name.strip(),"url":url.strip(),"agent_type":agent_type},timeout=5)
                    if r.ok:                st.success(f"✅ Added: {name}"); st.rerun()
                    elif r.status_code==400: st.warning("URL already exists.")
                    else:                   st.error(f"Failed: {r.text}")
                except Exception as e: st.error(str(e))

    st.markdown("---")
    st.subheader("📡 Active Sources")
    sources = api_get("/api/sources")
    if sources:
        for src in sources:
            c1,c2,c3,c4,c5,c6 = st.columns([2,4,2,2,1,1])
            c1.write(f"**{src.get('name','')}**")
            c2.caption(src.get("url",""))
            c3.caption(CAT_LABEL.get(src.get("agent_type",""),src.get("agent_type","")))
            ls = src.get("last_seen_at")
            c4.caption(f"Last: {str(ls)[:16] if ls else 'Never'}")
            c5.caption(f"#{src['id']}")
            if c6.button("🗑", key=f"del_{src['id']}"):
                try:
                    r = requests.delete(f"{API_URL}/api/sources/{src['id']}",timeout=5)
                    if r.ok: st.success("Removed"); st.rerun()
                except Exception as e: st.error(str(e))
    else:
        st.info("No sources. Add above or trigger a run to auto-seed from config.yaml.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: RUN HISTORY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📁 Run History":
    st.title("📁 Run History")

    runs = api_get("/api/runs")
    if not runs: st.info("No runs yet."); st.stop()

    icons = {"completed":"✅","failed":"❌","running":"⏳"}
    for run in runs:
        status  = run.get("status","unknown")
        run_id  = run.get("run_id","")
        found   = run.get("total_found",0)
        elapsed = run.get("elapsed_sec")
        label   = f"{icons.get(status,'❓')} {str(run.get('started_at',''))[:16]} · {status.upper()} · {found} signals"
        if elapsed: label += f" · {elapsed:.0f}s"

        with st.expander(label, expanded=(status=="running")):
            r1,r2,r3 = st.columns(3)
            r1.write(f"**ID:** `{run_id[:8]}...`")
            r1.write(f"**Status:** {status}")
            r2.write(f"**Started:** {str(run.get('started_at',''))[:19]}")
            r2.write(f"**Finished:** {str(run.get('finished_at',''))[:19] or 'In progress'}")
            r3.write(f"**Signals:** {found}")
            if elapsed: r3.write(f"**Elapsed:** {elapsed:.0f}s")

            fbc = run.get("findings_by_category",{})
            if fbc:
                st.markdown("**By Category:**")
                cc = st.columns(len(fbc))
                for i,(cat,count) in enumerate(fbc.items()):
                    cc[i].metric(f"{CAT_ICON.get(cat,'📌')} {cat}", count)

            ast2 = run.get("agent_status",{})
            if ast2:
                st.markdown("**Per-Agent:**")
                ac = st.columns(len(ast2))
                for i,(name,info) in enumerate(ast2.items()):
                    ic  = "✅" if info.get("status")=="ok" else ("⏱️" if info.get("status")=="timeout" else "❌")
                    lbl = f"{info.get('found',0)} signals"
                    if info.get("elapsed_sec"): lbl += f" · {info['elapsed_sec']}s"
                    ac[i].metric(f"{ic} {name}", lbl)

            if run.get("pdf_path"):
                d1,d2 = st.columns(2)
                d1.markdown(f"[📥 Open PDF]({API_URL}/api/digest/{run_id}/pdf)")
                try:
                    import os as _os
                    for base in ["backend",".","",""]:
                        pdf_abs = _os.path.join(base, run["pdf_path"]) if base else run["pdf_path"]
                        if _os.path.exists(pdf_abs):
                            with open(pdf_abs,"rb") as fh:
                                d2.download_button("⬇️ Save PDF", fh.read(),
                                    file_name=f"radar_{run_id[:8]}.pdf",
                                    mime="application/pdf", key=f"dl_{run_id}")
                            break
                except: pass

            if status=="failed" and run.get("error_log"):
                with st.expander("❌ Error Log"):
                    st.code(run["error_log"], language="text")

            if st.button("📋 Top Findings", key=f"view_{run_id}"):
                for f in api_get(f"/api/findings/{run_id}")[:8]:
                    score = f.get("final_score",0)
                    badge = "🆕" if f.get("change_status")=="new" else "🔄"
                    st.write(f"• {badge} [{score:.1f}] **{f.get('title','')}**")
                    st.caption(f.get("summary","")[:100]+"...")

            if status=="running" and st.button("🔄 Refresh", key=f"ref_{run_id}"):
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DIGEST ARCHIVE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📚 Digest Archive":
    st.title("📚 Digest Archive")
    st.caption("All past PDF digests — browse, search, download")

    runs      = api_get("/api/runs")
    completed = [r for r in runs if r.get("status")=="completed" and r.get("pdf_path")]
    if not completed: st.info("No digests yet."); st.stop()

    search = st.text_input("🔍 Search by date or run ID", placeholder="2026-03-05 or b6d68b8f")
    if search:
        completed = [r for r in completed if
                     search.lower() in str(r.get("started_at","")).lower() or
                     search.lower() in r.get("run_id","").lower()]

    st.caption(f"**{len(completed)} digest(s)**")
    st.markdown("---")

    for run in completed:
        run_id  = run.get("run_id","")
        started = str(run.get("started_at",""))[:16]
        found   = run.get("total_found",0)
        elapsed = run.get("elapsed_sec")
        fbc     = run.get("findings_by_category",{})

        with st.expander(f"📄 {started} · {found} signals", expanded=False):
            c1,c2,c3 = st.columns([2,2,1])
            c1.write(f"**Run:** `{run_id[:8]}...`")
            c1.write(f"**Date:** {started}")
            c2.write(f"**Signals:** {found}")
            if elapsed: c2.write(f"**Elapsed:** {elapsed:.0f}s")
            if fbc:
                st.caption("  ·  ".join(f"{CAT_ICON.get(k,'📌')} {k}: {v}" for k,v in fbc.items()))

            d1,d2 = st.columns(2)
            d1.markdown(f"[📥 Open in browser]({API_URL}/api/digest/{run_id}/pdf)")
            try:
                import os as _os
                for base in ["backend",".","",""]:
                    pdf_abs = _os.path.join(base, run["pdf_path"]) if base else run["pdf_path"]
                    if _os.path.exists(pdf_abs):
                        with open(pdf_abs,"rb") as fh:
                            d2.download_button("⬇️ Save PDF", fh.read(),
                                file_name=f"radar_{started[:10]}.pdf",
                                mime="application/pdf", key=f"arch_{run_id}")
                        break
            except: pass

            if st.button("👁 Preview signals", key=f"prev_{run_id}"):
                for f in api_get(f"/api/findings/{run_id}")[:5]:
                    score = f.get("final_score",0) or 0
                    st.write(f"**[{score:.1f}]** {f.get('title','')}")
                    st.caption(f.get("summary","")[:120]+"...")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: EMAIL RECIPIENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📧 Email Recipients":
    st.title("📧 Email Recipients")
    st.caption("Manage distribution list — configurable recipients")

    st.info("📬 **No DNS required.** Uses Resend's shared domain `onboarding@resend.dev` — works on any network including corporate firewalls.")

    st.subheader("📋 Current Recipients")
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
            label  = f"{'✅' if active else '⏸'} **{email}**" + (f" · {name}" if name else "")
            with st.expander(label, expanded=False):
                c1,c2,c3,c4 = st.columns([3,2,1,1])
                c1.write(f"**Email:** {email}")
                c2.write(f"**Name:** {name or '—'}")
                if note: st.caption(f"Note: {note}")
                if c3.button("⏸ Pause" if active else "▶️ Activate", key=f"tog_{rid}"):
                    try:
                        r = requests.patch(f"{API_URL}/api/email-recipients/{rid}/toggle",timeout=5)
                        if r.ok: st.rerun()
                        else: st.error(r.json().get("detail","Failed"))
                    except Exception as e: st.error(str(e))
                if c4.button("🗑 Remove", key=f"del_r_{rid}"):
                    try:
                        r = requests.delete(f"{API_URL}/api/email-recipients/{rid}",timeout=5)
                        if r.ok: st.success(f"Removed: {email}"); st.rerun()
                        else: st.error(r.json().get("detail","Failed"))
                    except Exception as e: st.error(str(e))

    st.markdown("---")
    st.subheader("➕ Add Recipient")
    a1,a2,a3 = st.columns([3,2,2])
    new_email = a1.text_input("Email *", placeholder="researcher@company.com", key="new_email")
    new_name  = a2.text_input("Name",    placeholder="Dr. Smith",              key="new_name")
    new_note  = a3.text_input("Note",    placeholder="Research team lead",     key="new_note")
    if st.button("➕ Add", type="primary"):
        if not new_email or "@" not in new_email:
            st.error("Valid email required")
        else:
            try:
                r = requests.post(f"{API_URL}/api/email-recipients",
                    json={"email":new_email,"name":new_name or None,"note":new_note or None},timeout=5)
                if r.status_code==200: st.success(f"✅ Added: {new_email}"); st.rerun()
                elif r.status_code==409: st.warning("Already in list")
                else: st.error(r.json().get("detail","Failed"))
            except Exception as e: st.error(str(e))

    st.markdown("---")
    st.subheader("🧪 Test Email Delivery")
    st.caption("Sends immediately — no pipeline run needed")
    t1,t2 = st.columns([4,1])
    test_addr = t1.text_input("Send test to", placeholder="your@gmail.com", key="test_email")
    if t2.button("📤 Send", type="secondary"):
        if not test_addr or "@" not in test_addr:
            st.error("Valid email required")
        else:
            with st.spinner("Sending…"):
                try:
                    r = requests.post(f"{API_URL}/api/email-recipients/test",
                        json={"email":test_addr},timeout=15)
                    if r.ok:
                        st.success(f"✅ Sent to **{test_addr}** via {r.json().get('provider','Resend')}")
                        st.caption("Check inbox + spam — arrives within 30s")
                    else:
                        st.error(f"Failed: {r.json().get('detail','Unknown')}")
                except Exception as e: st.error(str(e))

    with st.expander("ℹ️ Setup guide"):
        st.markdown("""
**1.** Go to [resend.com](https://resend.com) → Sign up (30 seconds)
**2.** Dashboard → API Keys → Create key
**3.** Add to `backend/.env`:
```
RESEND_API_KEY=re_your_key_here
```
**4.** Use Send Test above to verify · Free tier: 100 emails/day
        """)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SCHEDULE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📅 Schedule":
    st.title("📅 Schedule & System Status")

    status = api_get("/api/status")

    c1,c2 = st.columns(2)
    with c1:
        st.subheader("⏰ Next Scheduled Run")
        next_run = status.get("next_scheduled")
        if next_run:
            try:
                next_dt = datetime.fromisoformat(next_run)
                st.metric("Next Run", next_dt.strftime("%Y-%m-%d %H:%M %Z"))
                delta = next_dt.replace(tzinfo=None) - datetime.utcnow()
                h = int(delta.total_seconds()//3600)
                m = int((delta.total_seconds()%3600)//60)
                st.caption(f"In approximately {h}h {m}m")
            except: st.write(next_run)
        else:
            st.warning("Scheduler not running")
    with c2:
        st.subheader("📊 Stats")
        st.metric("Total Signals", status.get("total_findings",0))
        st.metric("Total Runs",    status.get("total_runs",0))
        st.metric("Completed",     status.get("completed_runs",0))

    st.markdown("---")
    st.subheader("⚙️ Schedule Config")
    st.info("Edit `backend/config.yaml` to change schedule:\n```yaml\nglobal:\n  run_time: '07:00'\n  timezone: 'Asia/Kolkata'\n```\nRestart API to apply.")

    st.markdown("---")
    st.subheader("🔑 Configuration Status")
    st.caption("Read from backend — accurate regardless of where keys are stored")

    llm_status        = status.get("llm_status","❌ Not configured")
    email_status      = status.get("email_status","❌ Not configured")
    active_recipients = status.get("active_recipients",0)

    col_a,col_b = st.columns(2)
    with col_a:
        st.markdown("**🤖 LLM Provider**"); st.write(llm_status)
        st.markdown("**📧 Email Provider**"); st.write(email_status)
    with col_b:
        st.markdown("**👥 Active Recipients**")
        if active_recipients > 0:
            st.success(f"✅ {active_recipients} recipient(s)")
            st.caption("Manage in 📧 Email Recipients page")
        else:
            st.warning("⚠️ No recipients — add in 📧 Email Recipients")

    st.markdown("---")
    st.subheader("🔗 Quick Links")
    q1,q2,q3,q4 = st.columns(4)
    q1.markdown(f"[📡 API Docs]({API_URL}/docs)")
    q2.markdown(f"[🗄 DB Explorer]({API_URL}/admin/db)")
    q3.markdown(f"[📊 Metrics JSON]({API_URL}/metrics)")
    q4.markdown(f"[❤ Health]({API_URL}/health)")

    st.markdown("---")

    # ── Danger Zone: Reset Database ──────────────────────────────────────────
    st.markdown("""
    <div style='border:1px solid #fca5a5;border-radius:10px;padding:1.2rem 1.5rem;
                background:#fff5f5;margin-top:0.5rem;'>
        <div style='font-size:14px;font-weight:700;color:#b91c1c;margin-bottom:4px;'>
            ⚠️ Danger Zone
        </div>
        <div style='font-size:13px;color:#6b7280;margin-bottom:12px;'>
            Wipe all findings, runs, snapshots and sources from the database.
            Email recipients are preserved. Sources will be re-seeded on next run.
            This action <strong>cannot be undone</strong>.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Two-step confirmation using session state
    if "reset_step" not in st.session_state:
        st.session_state.reset_step = 0
    if "reset_result" not in st.session_state:
        st.session_state.reset_result = None

    if st.session_state.reset_result:
        r = st.session_state.reset_result
        st.success(
            f"✅ Database wiped — deleted "
            f"{r['deleted']['findings']} findings, "
            f"{r['deleted']['runs']} runs, "
            f"{r['deleted']['snapshots']} snapshots, "
            f"{r['deleted']['sources']} sources."
        )
        st.caption("Email recipients preserved. Sources re-seed automatically on next pipeline run.")
        if st.button("Dismiss", key="reset_dismiss"):
            st.session_state.reset_result = None
            st.session_state.reset_step   = 0
            st.rerun()

    elif st.session_state.reset_step == 0:
        if st.button("🗑 Reset All Data", type="primary", key="reset_btn_1"):
            st.session_state.reset_step = 1
            st.rerun()

    elif st.session_state.reset_step == 1:
        st.warning("⚠️ Are you sure? This will permanently delete ALL findings, runs, and sources.")
        col_yes, col_no = st.columns([1, 3])
        with col_yes:
            if st.button("Yes, wipe everything", type="primary", key="reset_confirm"):
                try:
                    r = requests.post(
                        f"{API_URL}/api/admin/reset-db",
                        params={"confirm": "RESET"},
                        timeout=15,
                    )
                    if r.ok:
                        st.session_state.reset_result = r.json()
                        st.session_state.reset_step   = 0
                        st.rerun()
                    elif r.status_code == 409:
                        st.error("❌ Pipeline is currently running. Wait for it to finish first.")
                        st.session_state.reset_step = 0
                    else:
                        st.error(f"Failed: {r.json().get('detail', r.text)}")
                        st.session_state.reset_step = 0
                except Exception as e:
                    st.error(str(e))
                    st.session_state.reset_step = 0
        with col_no:
            if st.button("Cancel", key="reset_cancel"):
                st.session_state.reset_step = 0
                st.rerun()