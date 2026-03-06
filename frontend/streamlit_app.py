"""
streamlit_app.py — Triple Stack Radar 
Enterprise Intelligence Platform — Production Grade
Aesthetic: Light, clean, navigable; pipeline + schedule in clear cards.
Fonts: Fraunces (display) + DM Mono (data) + Outfit (body)
"""

import os
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# ── Backend URL resolution ─────────────────────────────────────────────────────
for _env_path in [
    os.path.join(os.path.dirname(__file__), "..", "backend", ".env"),
    os.path.join(os.getcwd(), "backend", ".env"),
    ".env",
]:
    if os.path.isfile(_env_path):
        try:
            with open(_env_path) as _f:
                for _line in _f:
                    _line = _line.strip()
                    if _line and not _line.startswith("#") and "=" in _line:
                        _k, _, _v = _line.partition("=")
                        _k, _v = _k.strip(), _v.strip().strip('"').strip("'")
                        if _k and _v and _k not in os.environ:
                            os.environ[_k] = _v
        except Exception:
            pass
        break

def _get_backend_url():
    url = (
        (st.secrets.get("BACKEND_URL") if hasattr(st, "secrets") and st.secrets else None)
        or "http://localhost:8000"
    )
    return (url or "http://localhost:8000").rstrip("/")

API_URL = _get_backend_url()

st.set_page_config(
    page_title="Triple Stack Radar",
    page_icon="🛰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State ─────────────────────────────────────────────────────────────
for _k, _v in [
    ("pipeline_was_running", False),
    ("pipeline_just_finished", False),
    ("reset_confirm", False),
    ("reset_step", 0),
    ("reset_result", None),
    ("sidebar_compact", False),  # Sidebar compact mode: icons-only navigation
]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM — Deep Space Operations Terminal
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,600;0,9..144,700;1,9..144,300&family=DM+Mono:wght@300;400;500&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">

<style>
/* ═══════════════════════════════════════════════════
   DESIGN TOKENS — Deep Space Ops
═══════════════════════════════════════════════════ */
:root {
  /* Surfaces — light theme */
  --c-void:      #f8fafc;
  --c-base:      #ffffff;
  --c-surface:   #ffffff;
  --c-raised:    #f1f5f9;
  --c-float:     #e2e8f0;
  --c-hover:     #f1f5f9;

  /* Borders */
  --b-faint:     rgba(15,23,42,0.06);
  --b-subtle:    rgba(15,23,42,0.1);
  --b-default:   rgba(15,23,42,0.14);
  --b-active:    rgba(37,99,235,0.4);
  --b-glow:      rgba(37,99,235,0.15);

  /* Text */
  --t-primary:   #0f172a;
  --t-secondary: #475569;
  --t-muted:     #64748b;
  --t-accent:    #0ea5e9;
  --t-dim:       #94a3b8;

  /* Accents */
  --a-teal:      #0d9488;
  --a-blue:      #2563eb;
  --a-violet:    #7c3aed;
  --a-amber:     #d97706;
  --a-green:     #16a34a;
  --a-red:       #dc2626;
  --a-cyan:      #0891b2;
  /* Reference: CentificAI-style sidebar toggle */
  --sidebar-toggle-bg: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%);
  --sidebar-toggle-color: #ffffff;

  /* Shadows — light */
  --shadow-sm:   0 1px 3px rgba(0,0,0,0.06);
  --shadow-md:   0 4px 12px rgba(0,0,0,0.06), 0 2px 4px rgba(0,0,0,0.04);
  --shadow-lg:   0 8px 24px rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.04);

  /* Radii */
  --r-xs: 4px;
  --r-sm: 7px;
  --r-md: 11px;
  --r-lg: 16px;

  /* Motion */
  --ease: cubic-bezier(0.16, 1, 0.3, 1);
  --spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --fast: 140ms;
  --base: 210ms;
  --slow: 340ms;
}

/* ═══════════════════════════════════════════════════
   GLOBAL
═══════════════════════════════════════════════════ */
html, body, [class*="css"], .stApp {
  font-family: 'Outfit', system-ui, sans-serif !important;
  background: var(--c-void) !important;
  color: var(--t-primary) !important;
}

/* Atmospheric background mesh */
.stApp::after {
  content: '';
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 100% 60% at 15% 0%, rgba(77,124,254,0.05) 0%, transparent 55%),
    radial-gradient(ellipse 70% 50% at 85% 100%, rgba(0,229,200,0.04) 0%, transparent 55%),
    radial-gradient(ellipse 50% 40% at 50% 50%, rgba(139,109,255,0.02) 0%, transparent 60%);
}

/* Optional: very subtle texture (disabled for clean light theme) */
.stApp::before { content: none; }

.block-container {
  padding: 0 2.2rem 2.2rem !important;
  max-width: 1480px !important;
  position: relative; z-index: 1;
}

/* App header — reference: CentificAI top bar + gradient strip */
.app-header {
  background: var(--c-base);
  border-bottom: 1px solid var(--b-subtle);
  margin: -1rem -2.2rem 1rem -2.2rem !important;
  padding: 0.75rem 2.2rem;
  display: flex; align-items: center; gap: 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.app-header-brand { display: flex; align-items: center; gap: 10px; }
.app-header-logo { font-size: 1.5rem; }
.app-header-title { font-family: 'Fraunces', serif; font-weight: 600; font-size: 1.1rem; color: var(--t-primary); }
.app-header-sub { font-family: 'DM Mono', monospace; font-size: 9px; color: var(--t-muted); letter-spacing: .08em; }
.app-header-gradient {
  height: 4px;
  margin: -0.5rem -2.2rem 1.25rem -2.2rem !important;
  background: linear-gradient(90deg, #7c3aed 0%, #5b21b6 50%, #0d9488 100%);
  border-radius: 0 0 4px 4px;
}
/* Hero metric cards row (reference: purple banner cards) */
.hero-cards-row {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  align-items: stretch;
  margin-bottom: 1.25rem;
}
.hero-card {
  flex: 1;
  min-width: 140px;
  min-height: 104px;
  background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
  border: 1px solid rgba(124,58,237,0.2);
  border-radius: var(--r-md);
  padding: 0.95rem 1.15rem;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.hero-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(124,58,237,0.12); }
.hero-card-label { font-size: 10.5px; color: var(--t-muted); text-transform: uppercase; letter-spacing: .07em; margin-bottom: 6px; }
.hero-card-value { font-size: 1.35rem; font-weight: 700; color: var(--a-violet); line-height: 1.2; }
/* Table container for table-wise pages */
.table-section { margin-top: 1rem; }
.data-table-wrapper { border-radius: var(--r-md); overflow: hidden; border: 1px solid var(--b-subtle); box-shadow: var(--shadow-sm); }
.wrapped-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background: var(--c-raised);
  border: 1px solid var(--b-subtle);
  border-radius: var(--r-md);
  overflow: hidden;
  table-layout: fixed;
}
.wrapped-table-wrap {
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  margin: 0 0 14px 0;
}
.wrapped-table th {
  text-align: left;
  background: #f8fafc;
  color: var(--t-muted);
  font-family: 'DM Mono', monospace;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: .08em;
  padding: 10px 12px;
  border-bottom: 1px solid var(--b-subtle);
  white-space: nowrap;
}
.wrapped-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--b-faint);
  color: var(--t-secondary);
  font-size: 13px;
  line-height: 1.45;
  vertical-align: top;
  white-space: normal;
  word-break: break-word;
  overflow-wrap: anywhere;
}
.wrapped-table tr:last-child td { border-bottom: none; }
.wrapped-table .cell-scroll {
  max-height: 3.6em;
  overflow: auto;
  white-space: normal;
  line-height: 1.45;
  padding-right: 4px;
}
.wrapped-table .cell-scroll::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.wrapped-table .cell-scroll::-webkit-scrollbar-thumb {
  background: rgba(71, 94, 130, 0.35);
  border-radius: 6px;
}
.wrapped-table .col-impact {
  width: 72px;
  text-align: right;
  white-space: nowrap;
  font-family: 'DM Mono', monospace;
}
.wrapped-table .col-tight {
  width: 78px;
  white-space: nowrap;
  font-family: 'DM Mono', monospace;
}
.wrapped-table .col-medium {
  width: 130px;
  white-space: nowrap;
}
.wrapped-table .col-title {
  width: 42%;
  min-width: 360px;
}
.wrapped-table .col-summary {
  width: 48%;
  min-width: 420px;
}
.wrapped-table .col-link a {
  color: var(--a-teal);
  text-decoration: none;
  font-family: 'DM Mono', monospace;
  font-size: 11px;
}
.wrapped-table .col-link a:hover { text-decoration: underline; }
@media (max-width: 1200px) {
  .wrapped-table th, .wrapped-table td { padding: 8px 10px; }
  .wrapped-table td { font-size: 12px; }
  .wrapped-table .col-title { min-width: 300px; }
  .wrapped-table .col-summary { min-width: 260px; }
  .wrapped-table .col-medium { width: 110px; }
  .wrapped-table .col-tight { width: 68px; }
  .wrapped-table .col-impact { width: 64px; }
}

/* Kill all Streamlit chrome */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="manage-app-button"],
.st-emotion-cache-h5rgaw,
.viewerBadge_container__1QSob { display: none !important; }

/* ═══════════════════════════════════════════════════
   SIDEBAR — Obsidian panel with teal accents
═══════════════════════════════════════════════════ */
/* Sidebar toggle: custom in-header chevron only */
button[data-testid="baseButton-headerNoPadding"] { display: none !important; }
[data-testid="stHeader"] button[aria-label*="sidebar" i],
[data-testid="stHeader"] button[title*="sidebar" i],
[data-testid="stHeader"] [data-testid="collapsedControl"],
[data-testid="stHeader"] button[kind="header"] {
  display: none !important;
}
button[aria-label="Close sidebar"],
button[aria-label="Open sidebar"],
button[aria-label="Enable sidebar"],
button[aria-label="Collapse sidebar"],
button[aria-label*="close sidebar" i],
button[aria-label*="open sidebar" i],
button[aria-label*="collapse sidebar" i],
button[aria-label*="expand sidebar" i],
button[title*="close sidebar" i],
button[title*="open sidebar" i],
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarNavCollapseButton"],
section[data-testid="stSidebar"] > div[data-testid="collapsedControl"],
section[data-testid="stSidebar"] [data-testid="collapsedControl"],
[data-testid="collapsedControl"] {
  display: none !important;
  visibility: hidden !important;
  pointer-events: none !important;
}

section[data-testid="stSidebar"],
[data-testid="stSidebar"] {
    width: 260px !important;
    min-width: 260px !important;
  max-width: 260px !important;
  background: var(--c-surface) !important;
  border-right: 1px solid var(--b-subtle) !important;
  box-shadow: 1px 0 12px rgba(0,0,0,0.06) !important;
}
section[data-testid="stSidebar"] > div:first-child {
  width: 260px !important; min-width: 260px !important;
  padding: 0 !important; overflow-x: hidden !important;
  overflow-y: auto !important;
}
[data-testid="stSidebar"] * { color: var(--t-secondary) !important; }

/* Sidebar header — reference-style title + collapse hint */
.sidebar-header { padding: 18px 14px 14px; }
.sidebar-brand {
  display: flex; align-items: center; gap: 12px;
  flex-wrap: nowrap;
}
.sidebar-logo-only-wrap {
  display: flex; align-items: center; justify-content: center;
}
.sidebar-logo {
  width: 38px; height: 38px; border-radius: 10px; flex-shrink: 0;
  background: linear-gradient(135deg, rgba(13,148,136,0.12), rgba(37,99,235,0.1));
  border: 1px solid rgba(13,148,136,0.25);
  display: flex; align-items: center; justify-content: center; font-size: 18px;
}
.sidebar-title {
  font-family: 'Fraunces', serif; font-size: 16px; font-weight: 600;
  color: var(--t-primary) !important; letter-spacing: -0.02em; line-height: 1.2;
  flex: 1;
}
.sidebar-subtitle {
  font-family: 'DM Mono', monospace; font-size: 9px; color: var(--t-muted) !important;
  letter-spacing: .1em; margin-top: 2px;
}
.sidebar-collapse-hint {
  font-size: 10px; color: var(--t-dim); cursor: default;
  padding: 4px 6px; border-radius: 6px;
  transition: background var(--base) var(--ease), color var(--base) var(--ease);
}
.sidebar-collapse-hint:hover { color: var(--t-secondary); background: var(--c-hover); }
.sidebar-divider { height: 1px; background: var(--b-faint); margin: 0 10px 10px; }
.sidebar-nav-label {
  font-family: 'DM Mono', monospace; font-size: 9px; font-weight: 500;
  color: var(--t-dim); text-transform: uppercase; letter-spacing: .12em;
  padding: 0 12px 8px;
}

/* Radio: hide label + radio buttons */
/* Important: never hide label:first-child here, or the first nav page (Dashboard) disappears. */
[data-testid="stSidebar"] .stRadio > label,
[data-testid="stSidebar"] .stRadio > div > label { display: block !important; }
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] > div:first-child { display: none !important; }
[data-testid="stSidebar"] .stRadio > div {
  gap: 2px !important; padding: 0 10px !important;
  align-items: stretch !important;
}

/* Nav items — production list spacing and hover (reference: Claude sidebar) */
[data-testid="stSidebar"] .stRadio > div {
  flex-direction: column !important;
  gap: 2px !important;
}
[data-testid="stSidebar"] .stRadio label { 
  font-family: 'Outfit', sans-serif !important;
  font-size: 13px !important; font-weight: 500 !important;
  letter-spacing: 0.01em !important;
  padding: 10px 14px !important;
  border-radius: var(--r-sm) !important;
  transition: background var(--base) var(--ease), color var(--base) var(--ease), border-color var(--base) var(--ease) !important;
  display: block !important; cursor: pointer !important;
  margin: 0 !important; position: relative !important;
  width: 100% !important;
  box-sizing: border-box !important;
  border: 1px solid transparent !important;
  border-left: 3px solid transparent !important;
  line-height: 1.35 !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
  background: var(--c-hover) !important;
  color: var(--t-primary) !important;
  border-left-color: var(--b-default) !important;
}
[data-testid="stSidebar"] .stRadio label:has(input:checked) {
  background: rgba(13,148,136,0.08) !important;
  color: var(--a-teal) !important;
  border-left-color: var(--a-teal) !important;
  font-weight: 600 !important;
}

/* Sidebar buttons */
[data-testid="stSidebar"] .stButton > button {
  background: rgba(0,229,200,0.08) !important;
  border: 1px solid rgba(0,229,200,0.2) !important;
  color: var(--a-teal) !important;
  border-radius: var(--r-sm) !important;
  font-size: 12px !important; font-weight: 600 !important;
  letter-spacing: 0.02em !important;
  transition: all var(--base) var(--ease) !important;
  font-family: 'Outfit', sans-serif !important;
}
[data-testid="stSidebar"] .stButton > button[kind][aria-label*="sidebar_mode_toggle"] {
  background: var(--sidebar-toggle-bg) !important;
  border: none !important;
  color: var(--sidebar-toggle-color) !important;
  box-shadow: 0 2px 8px rgba(124,58,237,0.35) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(0,229,200,0.14) !important;
  border-color: rgba(0,229,200,0.4) !important;
  box-shadow: var(--glow-teal) !important;
  transform: translateY(-1px) !important;
}

/* Ops expander in sidebar */
[data-testid="stSidebar"] [data-testid="stExpander"] {
  background: transparent !important; border: 1px solid var(--b-faint) !important;
  border-radius: var(--r-sm) !important; box-shadow: none !important;
  margin: 0 8px !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
  font-family: 'DM Mono', monospace !important;
  font-size: 10.5px !important; color: var(--t-muted) !important;
  padding: 7px 10px !important; letter-spacing: 0.06em !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
  color: var(--t-secondary) !important; background: var(--c-hover) !important;
}

/* ═══════════════════════════════════════════════════
   METRIC CARDS
═══════════════════════════════════════════════════ */
[data-testid="metric-container"] {
  background: var(--c-raised) !important;
  border: 1px solid var(--b-subtle) !important;
  border-radius: var(--r-md) !important;
  padding: 18px 20px !important;
  transition: all var(--base) var(--ease) !important;
  position: relative !important; overflow: hidden !important;
}
[data-testid="metric-container"]::after {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, var(--a-teal), transparent);
  opacity: 0; transition: opacity var(--base);
}
[data-testid="metric-container"]:hover {
  border-color: var(--b-active) !important;
  background: var(--c-float) !important;
  transform: translateY(-3px) !important;
  box-shadow: var(--shadow-md), var(--glow-teal) !important;
}
[data-testid="metric-container"]:hover::after { opacity: 1; }
[data-testid="metric-container"] label {
  font-family: 'DM Mono', monospace !important;
  color: var(--t-muted) !important; font-size: 9.5px !important;
  font-weight: 500 !important; letter-spacing: 0.1em !important;
  text-transform: uppercase !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
  font-family: 'Fraunces', serif !important;
  color: var(--t-primary) !important; font-size: 28px !important;
  font-weight: 600 !important; letter-spacing: -0.02em !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
  font-family: 'DM Mono', monospace !important; font-size: 11px !important;
}

/* ═══════════════════════════════════════════════════
   EXPANDERS
═══════════════════════════════════════════════════ */
[data-testid="stExpander"] {
  background: var(--c-surface) !important;
  border: 1px solid var(--b-subtle) !important;
  border-radius: var(--r-md) !important;
  box-shadow: var(--shadow-sm) !important;
  margin-bottom: 7px !important;
  transition: all var(--base) var(--ease) !important;
  overflow: hidden !important;
}
[data-testid="stExpander"]:hover {
  border-color: var(--b-default) !important;
  background: var(--c-raised) !important;
  box-shadow: var(--shadow-md) !important;
  transform: translateY(-1px) !important;
}
[data-testid="stExpander"] details summary {
  font-family: 'Outfit', sans-serif !important;
  font-size: 13.5px !important; font-weight: 500 !important;
  color: var(--t-secondary) !important;
  padding: 14px 18px !important;
  transition: color var(--fast) !important;
}
[data-testid="stExpander"] details summary:hover { color: var(--t-primary) !important; }
[data-testid="stExpander"] details[open] summary {
  color: var(--a-teal) !important;
  border-bottom: 1px solid var(--b-faint) !important;
}
[data-testid="stExpander"] details > div { padding: 16px 18px !important; }

/* ═══════════════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════════════ */
.stButton > button {
  font-family: 'Outfit', sans-serif !important;
  font-size: 13px !important; font-weight: 600 !important;
  border-radius: var(--r-sm) !important;
  transition: all var(--base) var(--ease) !important;
  letter-spacing: 0.02em !important;
  min-height: 40px !important;
  padding: 0.48rem 0.92rem !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 0.35rem !important;
  line-height: 1.2 !important;
}
.stButton > button[kind="primary"], .stButton > button {
  background: linear-gradient(135deg, #00c9b1, #00e5c8) !important;
  color: #06080f !important;
    border: none !important;
  box-shadow: 0 2px 12px rgba(0,229,200,0.25) !important;
}
.stButton > button:hover {
  background: linear-gradient(135deg, #00e5c8, #22ffe8) !important;
  transform: translateY(-2px) !important;
  box-shadow: var(--glow-teal), 0 4px 20px rgba(0,229,200,0.3) !important;
}
.stButton > button:active { transform: translateY(0) scale(0.98) !important; }
.stButton > button[kind="secondary"] {
  background: transparent !important;
  border: 1px solid var(--b-default) !important;
  color: var(--t-secondary) !important;
}
.stButton > button[kind="secondary"]:hover {
  border-color: var(--a-teal) !important; color: var(--a-teal) !important;
  background: rgba(0,229,200,0.06) !important;
}

/* ═══════════════════════════════════════════════════
   INPUTS
═══════════════════════════════════════════════════ */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
  background: var(--c-raised) !important;
  border: 1px solid var(--b-subtle) !important;
  border-radius: var(--r-sm) !important;
  color: var(--t-primary) !important;
  font-family: 'Outfit', sans-serif !important;
    font-size: 13px !important;
  transition: border-color var(--fast), box-shadow var(--fast) !important;
  min-height: 40px !important;
  line-height: 1.25 !important;
}
.stSelectbox [data-baseweb="select"] > div {
  min-height: 40px !important;
  display: flex !important;
  align-items: center !important;
}
.stTextInput > div > div > input:focus {
  border-color: var(--a-teal) !important;
  box-shadow: 0 0 0 3px rgba(0,229,200,0.1) !important;
}
.stTextInput label, .stSelectbox label, .stNumberInput label {
  color: var(--t-muted) !important;
  font-family: 'DM Mono', monospace !important;
  font-size: 10px !important; letter-spacing: 0.08em !important;
  text-transform: uppercase !important; font-weight: 400 !important;
}

/* ═══════════════════════════════════════════════════
   DATA TABLE
═══════════════════════════════════════════════════ */
[data-testid="stDataFrame"] {
  background: var(--c-surface) !important;
  border: 1px solid var(--b-subtle) !important;
  border-radius: var(--r-md) !important; overflow: hidden !important;
}
[data-testid="stDataFrame"] th {
  background: var(--c-raised) !important;
  font-family: 'DM Mono', monospace !important;
  font-size: 10.5px !important; letter-spacing: 0.07em !important;
  text-transform: uppercase !important; color: var(--t-muted) !important;
}
[data-testid="stDataFrame"] td {
  font-family: 'Outfit', sans-serif !important; font-size: 13px !important;
  color: var(--t-secondary) !important;
}

/* ═══════════════════════════════════════════════════
   ALERTS
═══════════════════════════════════════════════════ */
.stAlert {
  background: var(--c-raised) !important;
  border-radius: var(--r-md) !important;
  border: 1px solid var(--b-subtle) !important;
  font-family: 'Outfit', sans-serif !important; font-size: 13px !important;
}

/* ═══════════════════════════════════════════════════
   TYPOGRAPHY
═══════════════════════════════════════════════════ */
h1 {
  font-family: 'Fraunces', serif !important; color: var(--t-primary) !important;
  font-size: 28px !important; font-weight: 700 !important; letter-spacing: -0.03em !important;
}
h2 {
  font-family: 'Outfit', sans-serif !important; color: var(--t-primary) !important;
  font-size: 17px !important; font-weight: 600 !important; letter-spacing: -0.01em !important;
  margin-top: 8px !important;
  margin-bottom: 8px !important;
}
h3 { font-family: 'Outfit', sans-serif !important; color: var(--t-secondary) !important;
  font-size: 14px !important; font-weight: 600 !important;
  margin-top: 8px !important;
  margin-bottom: 8px !important;
}
p, li { color: var(--t-secondary) !important; font-size: 13.5px !important; line-height: 1.65 !important; }
[data-testid="stCaptionContainer"] p {
  color: var(--t-muted) !important; font-family: 'DM Mono', monospace !important; font-size: 11px !important;
}
hr { border-color: var(--b-faint) !important; margin: 20px 0 !important; }

/* Charts */
[data-testid="stArrowVegaLiteChart"] {
  background: var(--c-surface) !important; border: 1px solid var(--b-subtle) !important;
  border-radius: var(--r-md) !important; overflow: hidden !important; padding: 8px !important;
}
.stProgress > div > div {
  background: linear-gradient(90deg, var(--a-teal), var(--a-cyan)) !important;
  border-radius: 3px !important; box-shadow: var(--glow-teal) !important;
}
select option { background: var(--c-raised) !important; }

/* ═══════════════════════════════════════════════════
   COMPONENT LIBRARY
═══════════════════════════════════════════════════ */

/* ── PAGE TOPBAR ── */
.pg-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 0 18px;
  border-bottom: 1px solid var(--b-faint);
  margin-bottom: 26px;
}
.pg-bar-l { display: flex; align-items: center; gap: 14px; }
.pg-icon {
  width: 38px; height: 38px;
  background: linear-gradient(135deg, rgba(0,229,200,0.12), rgba(77,124,254,0.12));
  border: 1px solid rgba(0,229,200,0.25); border-radius: var(--r-sm);
  display: flex; align-items: center; justify-content: center; font-size: 18px;
}
.pg-title {
  font-family: 'Fraunces', serif; font-size: 20px; font-weight: 600;
  color: var(--t-primary); letter-spacing: -0.02em;
}
.pg-sub {
  font-family: 'DM Mono', monospace; font-size: 10.5px;
  color: var(--t-muted); margin-top: 2px; letter-spacing: 0.04em;
}
.pg-badge {
  font-family: 'DM Mono', monospace; font-size: 10px; font-weight: 500;
  padding: 4px 12px; border-radius: 20px; letter-spacing: 0.06em; text-transform: uppercase;
}
.badge-idle { background: rgba(61,77,110,0.4); border: 1px solid rgba(61,77,110,0.6); color: var(--t-muted); }
.badge-running {
  background: rgba(0,229,200,0.1); border: 1px solid rgba(0,229,200,0.35); color: var(--a-teal);
  animation: pb-pulse 1.8s ease-in-out infinite;
}
@keyframes pb-pulse { 0%,100%{opacity:1} 50%{opacity:0.55} }

/* ── SECTION DIVIDER ── */
.sd {
  display: flex; align-items: center; gap: 14px;
  margin: 30px 0 18px;
}
.sd-label {
  font-family: 'DM Mono', monospace; font-size: 9.5px; font-weight: 500;
  letter-spacing: 0.14em; text-transform: uppercase; color: var(--t-muted); white-space: nowrap;
}
.sd-line { flex: 1; height: 1px; background: linear-gradient(90deg, var(--b-subtle), transparent); }

/* ── STAT GRID ── */
.sg { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; margin: 14px 0; }
.sc {
  background: var(--c-raised); border: 1px solid var(--b-faint);
  border-radius: var(--r-sm); padding: 14px 16px;
  transition: all var(--base) var(--ease); cursor: default;
}
.sc:hover {
  border-color: var(--b-default); background: var(--c-float);
  transform: translateY(-2px); box-shadow: var(--shadow-sm);
}
.sl { font-family: 'DM Mono', monospace; font-size: 9px; color: var(--t-muted); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 6px; }
.sv { font-family: 'Fraunces', serif; font-size: 22px; font-weight: 600; color: var(--t-primary); letter-spacing: -0.02em; line-height: 1; }

/* ── SIGNAL ROW (Executive Brief) ── */
.sr {
  background: var(--c-surface); border: 1px solid var(--b-subtle);
  border-radius: var(--r-md); padding: 14px 18px; margin: 5px 0;
  display: flex; align-items: flex-start; gap: 16px;
  transition: all var(--base) var(--ease); cursor: pointer; position: relative; overflow: hidden;
}
.sr::before {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 2px;
  background: var(--a-teal); opacity: 0; transition: opacity var(--base);
}
.sr:hover { border-color: var(--b-active); background: var(--c-raised); transform: translateX(4px); box-shadow: var(--shadow-md); }
.sr:hover::before { opacity: 1; }
.sr-body { flex: 1; min-width: 0; }
.sr-title { font-family: 'Outfit', sans-serif; font-weight: 600; font-size: 13.5px; color: var(--t-primary); margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sr-desc { font-size: 12.5px; color: var(--t-secondary); line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.sr-meta { display: flex; align-items: center; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
.sr-score { flex-shrink: 0; text-align: right; min-width: 50px; }
.snum { font-family: 'Fraunces', serif; font-size: 24px; font-weight: 600; line-height: 1; letter-spacing: -0.02em; }
.sdenom { font-family: 'DM Mono', monospace; font-size: 9.5px; color: var(--t-muted); margin-top: 2px; }

/* ── INFO BLOCKS ── */
.ib {
  padding: 11px 15px; border-radius: var(--r-xs); margin: 8px 0;
  font-family: 'Outfit', sans-serif; font-size: 13px; line-height: 1.55;
  border-left: 3px solid;
}
.ib-label {
  font-family: 'DM Mono', monospace; font-size: 9.5px; font-weight: 500;
  letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 5px; display: block;
}
.ib-hi  { background: rgba(0,214,143,0.07);  border-color: var(--a-green);  color: #6ee7c0; }
.ib-mid { background: rgba(245,166,35,0.07); border-color: var(--a-amber);  color: #fcd68a; }
.ib-lo  { background: rgba(255,77,109,0.07); border-color: var(--a-red);    color: #ff9ab0; }
.ib-teal  { background: rgba(0,229,200,0.06); border-color: var(--a-teal);  color: #67e8e0; }
.ib-blue  { background: rgba(77,124,254,0.07); border-color: var(--a-blue); color: #93b4fd; }
.ib-warn  { background: rgba(245,166,35,0.07); border-color: var(--a-amber);color: #fcd68a; }
.ib-red   { background: rgba(255,77,109,0.07); border-color: var(--a-red);  color: #ff9ab0; }

/* ── PILLS ── */
.pill {
  display: inline-flex; align-items: center; padding: 2px 9px; border-radius: 20px;
  font-family: 'DM Mono', monospace; font-size: 9.5px; font-weight: 500;
  letter-spacing: 0.05em; text-transform: uppercase; border: 1px solid transparent; white-space: nowrap;
}
.p-teal   { background: rgba(0,229,200,0.1);  border-color: rgba(0,229,200,0.25);  color: var(--a-teal); }
.p-blue   { background: rgba(77,124,254,0.1); border-color: rgba(77,124,254,0.25); color: #7b9ffe; }
.p-green  { background: rgba(0,214,143,0.1);  border-color: rgba(0,214,143,0.25);  color: #34d399; }
.p-amber  { background: rgba(245,166,35,0.1); border-color: rgba(245,166,35,0.25); color: #fcd34d; }
.p-red    { background: rgba(255,77,109,0.1); border-color: rgba(255,77,109,0.25); color: #fca5b5; }
.p-violet { background: rgba(139,109,255,0.1);border-color: rgba(139,109,255,0.25);color: #c4b5fd; }
.p-grey   { background: rgba(61,77,110,0.3);  border-color: rgba(61,77,110,0.5);   color: var(--t-secondary); }

/* ── SCORE COLORS ── */
.score-hi  { color: var(--a-green) !important; }
.score-mid { color: var(--a-amber) !important; }
.score-lo  { color: var(--a-red)   !important; }

/* ── BADGES ── */
.badge-new { background: rgba(77,124,254,0.12); border: 1px solid rgba(77,124,254,0.3); color: #7b9ffe; padding: 2px 8px; border-radius: 4px; font-family:'DM Mono',monospace; font-size: 9.5px; font-weight:500; letter-spacing:.05em; }
.badge-upd { background: rgba(0,214,143,0.12);  border: 1px solid rgba(0,214,143,0.3);  color: #34d399; padding: 2px 8px; border-radius: 4px; font-family:'DM Mono',monospace; font-size: 9.5px; font-weight:500; letter-spacing:.05em; }
.badge-unc { background: rgba(61,77,110,0.3);   border: 1px solid rgba(61,77,110,0.5);  color: var(--t-muted); padding: 2px 8px; border-radius: 4px; font-family:'DM Mono',monospace; font-size: 9.5px; font-weight:500; letter-spacing:.05em; }

/* ── STATUS DOTS ── */
.sdot { display: inline-flex; align-items: center; gap: 8px; font-family:'DM Mono',monospace; font-size:11px; letter-spacing:.04em; }
.dot { width:6px; height:6px; border-radius:50%; }
.dot-teal  { background: var(--a-teal);  box-shadow: 0 0 8px var(--a-teal); }
.dot-red   { background: var(--a-red);   box-shadow: 0 0 8px var(--a-red); }
.dot-amber { background: var(--a-amber); box-shadow: 0 0 8px var(--a-amber); }

/* ── PIPELINE PROGRESS ── */
.pipe-wrap {
  background: var(--c-surface); border: 1px solid var(--b-active);
  border-radius: var(--r-md); padding: 16px 20px; margin: 14px 0;
  position: relative; overflow: hidden;
}
.pipe-wrap::before {
  content: ''; position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(90deg, rgba(0,229,200,0.03), transparent);
  animation: pipe-sweep 2.2s ease-in-out infinite;
}
@keyframes pipe-sweep { 0%{opacity:0;transform:translateX(-100%)} 50%{opacity:1} 100%{opacity:0;transform:translateX(100%)} }
.pipe-hd { display: flex; justify-content: space-between; align-items: center; margin-bottom: 11px; }
.pipe-stage {
  font-family: 'DM Mono', monospace; font-size: 11px; color: var(--a-teal);
  letter-spacing: 0.05em; display: flex; align-items: center; gap: 9px;
}
.pipe-dot {
  width: 7px; height: 7px; border-radius: 50%; background: var(--a-teal);
  animation: dp 1.3s ease-in-out infinite; box-shadow: 0 0 10px var(--a-teal);
}
@keyframes dp { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.5);opacity:0.4} }
.pipe-pct { font-family: 'Fraunces', serif; font-size: 16px; font-weight: 600; color: var(--t-primary); }
.pipe-track { background: var(--c-void); border-radius: 3px; height: 4px; overflow: hidden; }
.pipe-fill {
  height: 100%; border-radius: 3px;
  background: linear-gradient(90deg, var(--a-teal), var(--a-cyan));
  box-shadow: 0 0 14px rgba(0,229,200,0.5); transition: width 0.5s var(--ease);
}
.pipe-detail { font-family: 'DM Mono', monospace; font-size: 10px; color: var(--t-muted); margin-top: 8px; }

/* ── DONE BANNER ── */
.done-banner {
  background: linear-gradient(135deg, rgba(0,214,143,0.1), rgba(0,214,143,0.05));
  border: 1px solid rgba(0,214,143,0.3); border-radius: var(--r-md);
  padding: 14px 18px; margin: 12px 0; display: flex; align-items: center; gap: 14px;
  animation: slide-in var(--slow) var(--ease);
}
@keyframes slide-in { from{opacity:0;transform:translateY(-10px)} to{opacity:1;transform:translateY(0)} }
.done-title { font-family: 'Fraunces', serif; font-weight: 600; font-size: 15px; color: var(--a-green); }
.done-sub { font-size: 11.5px; color: var(--t-muted); font-family: 'DM Mono', monospace; margin-top: 2px; }

/* ── DANGER ZONE ── */
.danger-wrap {
  background: rgba(255,77,109,0.04); border: 1px solid rgba(255,77,109,0.18);
  border-radius: var(--r-md); padding: 18px 22px; margin-top: 14px;
}
.danger-title { font-family: 'Outfit', sans-serif; font-size: 13px; font-weight: 700; color: var(--a-red); margin-bottom: 5px; }
.danger-desc { font-size: 12.5px; color: var(--t-muted); line-height: 1.55; }

/* ── TREND ── */
.trend-up { color: var(--a-green) !important; font-weight: 700; }
.trend-dn { color: var(--a-red) !important; font-weight: 700; }
.mono { font-family: 'DM Mono', monospace; font-size: 11px; color: var(--t-muted); }

/* ── FORMULA CARD ── */
.formula-card {
  background: var(--c-raised); border: 1px solid var(--b-subtle);
  border-radius: var(--r-md); padding: 16px 22px; margin: 14px 0;
  display: flex; align-items: center; gap: 18px; flex-wrap: wrap;
}
.formula-label {
  font-family: 'DM Mono', monospace; font-size: 9.5px; color: var(--t-muted);
  text-transform: uppercase; letter-spacing: 0.1em; white-space: nowrap;
}

/* Pipeline + Schedule cards (Dashboard) — production-grade card grid like reference UIs */
.pipe-schedule-card {
  background: linear-gradient(135deg, var(--c-surface) 0%, var(--c-raised) 100%);
  border: 1px solid var(--b-subtle);
  border-radius: var(--r-md); padding: 16px 18px; margin-bottom: 12px;
  transition: box-shadow var(--base) var(--ease), border-color var(--base) var(--ease), transform var(--base) var(--ease);
}
.pipe-schedule-card:hover {
  box-shadow: var(--shadow-md); border-color: var(--b-default);
  transform: translateY(-1px);
}
.ps-label {
  font-family: 'DM Mono', monospace; font-size: 9px; color: var(--t-muted);
  text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px;
}
.ps-value {
  font-family: 'Fraunces', serif; font-size: 20px; font-weight: 600;
  color: var(--t-primary); letter-spacing: -0.02em; line-height: 1.2;
}
.ps-hint {
  font-size: 11px; color: var(--t-dim); margin-top: 8px; line-height: 1.4;
}

/* Loading — keep default spinner layout to avoid text clipping/wrapping regressions */

/* KPI / metric row — status card grid like reference UIs */
[data-testid="metric-container"] {
  border-radius: var(--r-md) !important;
  transition: transform var(--base) var(--ease), box-shadow var(--base) var(--ease);
}
[data-testid="metric-container"]:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

/* Data table consistency — classic enterprise style across pages */
[data-testid="stDataFrame"] {
  font-size: 13px !important;
  border: 1px solid var(--b-subtle) !important;
  border-radius: var(--r-md) !important;
  box-shadow: var(--shadow-sm) !important;
  overflow: hidden !important;
  margin-bottom: 14px !important;
}
[data-testid="stDataFrame"] th {
  background: var(--c-raised) !important;
  color: var(--t-muted) !important;
  font-family: 'DM Mono', monospace !important;
  font-size: 10px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
  font-weight: 600 !important;
  border-bottom: 1px solid var(--b-subtle) !important;
}
[data-testid="stDataFrame"] td,
[data-testid="stDataFrame"] th {
  padding: 10px 12px !important;
}
[data-testid="stDataFrame"] td {
  border-bottom: 1px solid var(--b-faint) !important;
}
[data-testid="stDataFrame"] [role="gridcell"] > div {
  max-height: 3.6em !important;
  overflow: auto !important;
  white-space: normal !important;
  line-height: 1.4 !important;
  padding-right: 3px !important;
}
[data-testid="stDataFrame"] [role="gridcell"] > div::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
[data-testid="stDataFrame"] [role="gridcell"] > div::-webkit-scrollbar-thumb {
  background: rgba(71, 94, 130, 0.35);
  border-radius: 6px;
}

/* Selectbox dropdown */
[data-baseweb="select"] { background: var(--c-raised) !important; }
[data-baseweb="popover"] { background: var(--c-raised) !important; border: 1px solid var(--b-default) !important; }
</style>
""", unsafe_allow_html=True)

# Sidebar mode CSS (expanded vs compact icon-only)
if st.session_state.sidebar_compact:
    st.markdown("""
    <style>
    section[data-testid="stSidebar"], [data-testid="stSidebar"] {
      width: 92px !important; min-width: 92px !important; max-width: 92px !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
      width: 92px !important; min-width: 92px !important;
    }
    .sidebar-title, .sidebar-subtitle, .sidebar-nav-label, .sidebar-divider,
    [data-testid="stSidebar"] [data-testid="stExpander"], [data-testid="stSidebar"] .sdot span,
    .sidebar-right-label {
      display: none !important;
    }
    .sidebar-header { padding: 8px 6px 4px !important; }
    .sidebar-brand { justify-content: center !important; gap: 0 !important; }
    .sidebar-logo { width: 34px !important; height: 34px !important; }
    [data-testid="stSidebar"] .stButton {
      display: flex !important;
      justify-content: center !important;
      align-items: center !important;
      margin: 6px 0 10px !important;
    }
    [data-testid="stSidebar"] .stButton > button {
      width: 44px !important;
      min-width: 44px !important;
      max-width: 44px !important;
      height: 44px !important;
      min-height: 44px !important;
      padding: 0 !important;
      border-radius: 12px !important;
      background: #f8fbff !important;
      border: 1px solid #5d88ff !important;
      color: #475e82 !important;
      box-shadow: none !important;
      font-size: 20px !important;
      line-height: 1 !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
      background: #eef4ff !important;
      border-color: #4476ff !important;
      transform: none !important;
    }
    [data-testid="stSidebar"] .stRadio > div { padding: 0 10px !important; }
    [data-testid="stSidebar"] .stRadio label {
      font-size: 20px !important;
      line-height: 1 !important;
      font-weight: 500 !important;
      padding: 11px 0 !important;
      border: 1px solid transparent !important;
      border-left: none !important;
      text-align: center !important;
      border-radius: 9px !important;
      white-space: nowrap !important;
      overflow: hidden !important;
      text-overflow: clip !important;
      width: 44px !important;
      min-width: 44px !important;
      max-width: 44px !important;
      margin: 0 auto !important;
      box-sizing: border-box !important;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
      transform: none !important;
      background: rgba(13,148,136,0.12) !important;
      border: 1px solid rgba(13,148,136,0.35) !important;
      color: var(--a-teal) !important;
    }
    [data-testid="stSidebar"] .stRadio label:has(input:checked) {
      background: rgba(13,148,136,0.14) !important;
      border: 1px solid rgba(13,148,136,0.45) !important;
      color: var(--a-teal) !important;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    section[data-testid="stSidebar"], [data-testid="stSidebar"] {
      width: 260px !important; min-width: 260px !important; max-width: 260px !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
      width: 260px !important; min-width: 260px !important;
    }
    /* Hard reset in expanded mode so compact icon-only rules never leak during reruns */
    [data-testid="stSidebar"] .stRadio label {
      font-size: 13px !important;
      line-height: 1.35 !important;
      font-weight: 500 !important;
      white-space: normal !important;
      overflow: visible !important;
      text-overflow: unset !important;
      padding: 10px 14px !important;
      text-align: left !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
_LIST = ["findings","runs","sources","entities","snapshots","clusters","changes","email-recipients"]
NAV_PAGES = [
    "📊  Dashboard",
    "🔄  What Changed",
    "🎯  Impact Analysis",
    "📈  Observability",
    "🏷️  Entity Dashboard",
    "🔭  SOTA Watch",
    "🔍  Findings Explorer",
    "⚙️  Sources",
    "📁  Run History",
    "📚  Digest Archive",
    "📧  Email Recipients",
    "📅  Schedule",
]
NAV_ICONS = ["📊", "🔄", "🎯", "📈", "🏷️", "🔭", "🔍", "⚙️", "📁", "📚", "📧", "📅"]
CAT_ICON  = {"competitors":"🏢","model_providers":"🤖","research":"📄","hf_benchmarks":"📊"}
CAT_LABEL = {"competitors":"Competitors","model_providers":"Model Providers",
              "research":"Research","hf_benchmarks":"HF Benchmarks"}
CAT_PILL  = {"competitors":"p-red","model_providers":"p-blue","research":"p-green","hf_benchmarks":"p-amber"}
CAT_COLOR = {"competitors":"🔴","model_providers":"🔵","research":"🟢","hf_benchmarks":"🟡"}
CONF_LABEL = {1.0:"Official Source",0.8:"Lab Blog / Docs",0.6:"Third-party"}

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def _http_session():
    s = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=16, pool_maxsize=16, max_retries=0)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s

def _params_key(params):
    if not params:
        return tuple()
    return tuple(sorted((str(k), str(v)) for k, v in params.items()))

@st.cache_data(show_spinner=False, ttl=8)
def _api_get_cached(path, params_key):
    params = {k: v for k, v in params_key} if params_key else None
    r = _http_session().get(f"{API_URL}{path}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def _api_get_uncached(path, params=None):
    r = _http_session().get(f"{API_URL}{path}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def clear_ui_cache():
    _api_get_cached.clear()

def api_get(path, params=None, use_cache=True):
    try:
        if use_cache:
            return _api_get_cached(path, _params_key(params))
        return _api_get_uncached(path, params=params)
    except requests.exceptions.Timeout:
        if any(x in path for x in ["status","runs"]):
            st.info("⏳ Pipeline running — refresh in ~60s")
        return [] if any(x in path for x in _LIST) else {}
    except requests.ConnectionError:
        st.error("❌ Cannot reach API — check BACKEND_URL in Streamlit secrets.")
        st.stop()
    except Exception as e:
        if "timed out" in str(e).lower():
            return [] if any(x in path for x in _LIST) else {}
        return [] if any(x in path for x in _LIST) else {}

def score_color(s):
    if s >= 7: return "score-hi"
    if s >= 4: return "score-mid"
    return "score-lo"

def change_badge(status):
    if status == "new":     return '<span class="badge-new">NEW</span>'
    if status == "updated": return '<span class="badge-upd">UPD</span>'
    return '<span class="badge-unc">—</span>'

def impact_bar(score):
    if score >= 7:
        st.markdown('<div class="ib ib-hi"><span class="ib-label">▲ High Impact</span></div>', unsafe_allow_html=True)
    elif score >= 4:
        st.markdown('<div class="ib ib-mid"><span class="ib-label">◆ Medium Impact</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ib ib-lo"><span class="ib-label">▼ Low Impact</span></div>', unsafe_allow_html=True)

def cat_pill(cat):
    cls = CAT_PILL.get(cat, "p-grey")
    lbl = CAT_LABEL.get(cat, cat)
    return f'<span class="pill {cls}">{lbl}</span>'

def topbar(icon, title, sub, badge_html=""):
    st.markdown(f"""
    <div class="pg-bar">
      <div class="pg-bar-l">
        <div class="pg-icon">{icon}</div>
        <div><div class="pg-title">{title}</div><div class="pg-sub">{sub}</div></div>
      </div>
      <div>{badge_html}</div>
    </div>""", unsafe_allow_html=True)

def section_div(label):
    st.markdown(f'<div class="sd"><div class="sd-label">{label}</div><div class="sd-line"></div></div>', unsafe_allow_html=True)

def stat_grid(items):
    cells = "".join(
        f'<div class="sc"><div class="sl">{it[0]}</div><div class="sv">{it[1]}</div></div>'
        for it in items
    )
    st.markdown(f'<div class="sg">{cells}</div>', unsafe_allow_html=True)

def pipeline_check(status):
    is_running = status.get("is_running", False)
    if is_running:
        st.session_state.pipeline_was_running   = True
        st.session_state.pipeline_just_finished = False
    elif st.session_state.pipeline_was_running and not is_running:
        st.session_state.pipeline_was_running   = False
        st.session_state.pipeline_just_finished = True
    if st.session_state.pipeline_just_finished:
        st.session_state.pipeline_just_finished = False
        st.markdown("""<div class="done-banner">
          <div style="font-size:22px">✅</div>
          <div><div class="done-title">Pipeline Complete</div>
          <div class="done-sub">Intelligence signals updated — latest data shown below</div></div>
        </div>""", unsafe_allow_html=True)
    if is_running:
        ps = api_get("/api/pipeline-status", use_cache=False)
        stage = ps.get("stage", "Initializing")
        pct   = ps.get("progress", 0)
        detail= ps.get("detail", "")
        updated_at = datetime.now().strftime("%H:%M:%S")
        st.markdown(f"""<div class="pipe-wrap">
          <div class="pipe-hd">
            <div class="pipe-stage"><div class="pipe-dot"></div>PIPELINE ACTIVE — {stage}</div>
            <div class="pipe-pct">{pct}%</div>
          </div>
          <div class="pipe-track"><div class="pipe-fill" style="width:{pct}%"></div></div>
          <div class="pipe-detail">{detail} · Last updated: {updated_at}</div>
        </div>""", unsafe_allow_html=True)
        import time; time.sleep(2.5); st.rerun()
    return is_running

def signal_detail(f, show_rec=True):
    score = f.get("final_score", 0) or 0
    conf  = f.get("confidence_score", 0.8) or 0.8
    cat   = f.get("category", "")
    cluster = f.get("topic_cluster", "general")
    priority = (f.get("priority") or "medium").upper()
    horizon  = f.get("impact_horizon") or "—"
    pri_cls  = {"HIGH":"p-red","MEDIUM":"p-amber","LOW":"p-green"}.get(priority,"p-grey")
    sc = score_color(score)

    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"<p style='color:var(--t-secondary);font-size:13.5px;line-height:1.65;margin-bottom:10px;'>{f.get('summary','')}</p>", unsafe_allow_html=True)
        if f.get("why_matters"):
            st.markdown(f'<div class="ib ib-teal"><span class="ib-label">💡 Why it matters</span>{f["why_matters"]}</div>', unsafe_allow_html=True)
        if f.get("evidence"):
            st.markdown(f'<div class="ib ib-blue"><span class="ib-label">📎 Evidence</span>{f["evidence"]}</div>', unsafe_allow_html=True)
        if show_rec and f.get("recommendation"):
            st.markdown(f'<div class="ib ib-warn"><span class="ib-label">🎯 Strategic Action</span>{f["recommendation"]}<div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap;"><span class="pill {pri_cls}">⚡ {priority}</span><span class="pill p-teal">⏱ {horizon}</span></div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style='background:var(--c-raised);border:1px solid var(--b-subtle);border-radius:10px;padding:16px 14px;text-align:center;margin-bottom:10px;'>
          <div class="snum {sc}">{score:.1f}</div>
          <div class="sdenom">/ 10.0</div>
        </div>
        <div style='background:var(--c-raised);border:1px solid var(--b-faint);border-radius:8px;padding:12px;'>
          <div class="mono" style='margin-bottom:5px;'>CATEGORY</div>{cat_pill(cat)}
          <div class="mono" style='margin-top:10px;margin-bottom:4px;'>CONFIDENCE</div>
          <div style='font-family:"Fraunces",serif;font-weight:600;color:var(--t-primary);font-size:17px;'>{conf:.0%}</div>
          <div class="mono" style='margin-top:10px;margin-bottom:4px;'>CLUSTER</div>
          <div style='font-size:11.5px;color:var(--t-secondary);'>{cluster}</div>
        </div>""", unsafe_allow_html=True)
        if f.get("source_url"):
            st.markdown(f"<div style='margin-top:8px;text-align:center;'><a href='{f['source_url']}' target='_blank' style='font-family:\"DM Mono\",monospace;font-size:10.5px;color:var(--a-teal);text-decoration:none;letter-spacing:.05em;'>↗ SOURCE</a></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    if "active_page" not in st.session_state:
        st.session_state.active_page = NAV_PAGES[0]
    if st.session_state.active_page not in NAV_PAGES:
        st.session_state.active_page = NAV_PAGES[0]

    if st.session_state.sidebar_compact:
        st.markdown("""
        <div class="sidebar-header">
          <div class="sidebar-logo-only-wrap">
            <div class="sidebar-logo">🛰</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("▶", key="sidebar_mode_toggle", help="Enable sidebar"):
            st.session_state.sidebar_compact = False
            st.rerun()
    else:
        h_left, h_right = st.columns([4, 1], gap="small")
        with h_left:
            st.markdown("""
            <div class="sidebar-header">
              <div class="sidebar-brand">
                <div class="sidebar-logo">🛰</div>
                <div class="sidebar-right-label">
                  <div class="sidebar-title">Triple Stack Radar</div>
                  <div class="sidebar-subtitle">RADAR v1.0</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        with h_right:
            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            if st.button("◀", use_container_width=True, key="sidebar_mode_toggle", help="Hide sidebar (icons only)"):
                st.session_state.sidebar_compact = True
                st.rerun()

    if not st.session_state.sidebar_compact:
        st.markdown('<div class="sidebar-divider"></div><div class="sidebar-nav-label">Navigation</div>', unsafe_allow_html=True)

    current_idx = NAV_PAGES.index(st.session_state.active_page)
    if st.session_state.sidebar_compact:
        icon_to_full = dict(zip(NAV_ICONS, NAV_PAGES))
        icon_sel = st.radio("nav", NAV_ICONS, index=current_idx, label_visibility="hidden", key="nav_compact")
        page = icon_to_full[icon_sel]
    else:
        page = st.radio("nav", NAV_PAGES, index=current_idx, label_visibility="hidden", key="nav_full")
    st.session_state.active_page = page

    if not st.session_state.sidebar_compact:
        st.markdown("""
        <div class="sidebar-divider" style="margin-top:12px;"></div>
        <div class="sidebar-nav-label">Settings</div>
        """, unsafe_allow_html=True)

        with st.expander("⚙ ops"):
            if st.button("↩ Recover Stale", use_container_width=True, key="recover"):
                try:
                    r = _http_session().post(f"{API_URL}/api/runs/recover", timeout=5)
                    if r.ok:
                        clear_ui_cache()
                    st.success(r.json().get("message","Done") if r.ok else "Failed")
                except Exception as e: st.error(str(e))
            st.markdown('<div style="height:1px;background:var(--b-faint);margin:6px 0;"></div>', unsafe_allow_html=True)
            if not st.session_state.reset_confirm:
                if st.button("🗑 reset db", key="reset_db_init", use_container_width=True):
                    st.session_state.reset_confirm = True; st.rerun()
            else:
                st.markdown('<div style="font-family:\'DM Mono\',monospace;font-size:9.5px;color:var(--a-red);margin-bottom:6px;">⚠ DELETE ALL DATA?</div>', unsafe_allow_html=True)
                cy, cn = st.columns(2)
                if cy.button("wipe", key="reset_yes", type="primary"):
                    try:
                        r = _http_session().post(f"{API_URL}/api/admin/reset-db", params={"confirm":"RESET"}, timeout=10)
                        st.session_state.reset_confirm = False
                        if r.ok:
                            clear_ui_cache()
                        st.success("Wiped ✓") if r.ok else st.error(f"{r.status_code}")
                    except Exception as e: st.error(str(e))
                if cn.button("cancel", key="reset_no"):
                    st.session_state.reset_confirm = False; st.rerun()

        st.markdown('<div style="height:1px;background:var(--b-faint);margin:8px 10px 6px;"></div>', unsafe_allow_html=True)
        try:
            h = _http_session().get(f"{API_URL}/health", timeout=3)
            dot_cls = "dot-teal" if h.ok else "dot-red"
            lbl = "api online" if h.ok else "api offline"
        except Exception:
            dot_cls = "dot-red"; lbl = "api offline"
        st.markdown(f"""
        <div style='padding:0 14px 18px;'>
          <div class="sdot"><div class="dot {dot_cls}"></div>
          <span style='color:var(--t-muted);'>{lbl}</span></div>
        </div>""", unsafe_allow_html=True)



# ══════════════════════════════════════
# APP HEADER (production-grade top bar + gradient)
# ══════════════════════════════════════
def render_app_header():
    st.markdown("""
    <div class="app-header">
      <div class="app-header-brand">
        <span class="app-header-logo">🛰</span>
        <div>
          <div class="app-header-title">Triple Stack Radar</div>
          <div class="app-header-sub">Frontier AI Intelligence</div>
        </div>
      </div>
    </div>
    <div class="app-header-gradient"></div>
    """, unsafe_allow_html=True)

render_app_header()

# ══════════════════════════════════════
# PAGES
# ══════════════════════════════════════
if page == "📊  Dashboard":

    with st.spinner("Loading dashboard…"):
        status   = api_get("/api/status", use_cache=False)
        findings = api_get("/api/findings", {"limit": 100})
    next_run = status.get("next_scheduled")
    is_running = status.get("is_running", False)

    # Top row: title left, Run Pipeline top right
    col_title, col_actions = st.columns([3, 1])
    with col_title:
        col_logo, col_t = st.columns([0.15, 1])
        with col_logo:
            st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=48)
        with col_t:
            st.title("Frontier AI Radar")
            st.caption("Autonomous Multi-Agent Intelligence · Tracking frontier AI developments daily")
    with col_actions:
        st.markdown("<div style='margin-top:0.6rem;'></div>", unsafe_allow_html=True)
        run_btn = st.button("⚡ Run Pipeline", type="primary", use_container_width=True, key="dashboard_trigger_run")
        if run_btn:
            try:
                r = _http_session().post(f"{API_URL}/api/runs/trigger", timeout=5)
                if r.status_code == 200:
                    clear_ui_cache()
                    st.session_state.pipeline_was_running = True
                    st.session_state.pipeline_just_finished = False
                    st.success("Pipeline started"); st.rerun()
                elif r.status_code == 409:
                    clear_ui_cache()
                    st.warning("Already running"); st.rerun()
                else:
                    st.error(f"Error {r.status_code}")
            except Exception:
                st.error("API offline")

    with st.container():
        # Pipeline + Schedule cards (aggregated)
        st.markdown("---")
        card1, card2, card3 = st.columns(3)
        with card1:
            pipe_label = "▶ Running" if is_running else "● Idle"
            st.markdown(f"""
            <div class="pipe-schedule-card">
                <div class="ps-label">Pipeline</div>
                <div class="ps-value" style="{'color:var(--a-teal);' if is_running else ''}">{pipe_label}</div>
                <div class="ps-hint">Use Run Pipeline above to start</div>
            </div>
            """, unsafe_allow_html=True)
        with card2:
            next_str = "—"
            try:
                if next_run:
                    next_dt = datetime.fromisoformat(next_run.replace("Z", "+00:00"))
                    next_str = next_dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
            st.markdown(f"""
            <div class="pipe-schedule-card">
                <div class="ps-label">Next scheduled run</div>
                <div class="ps-value">{next_str}</div>
                <div class="ps-hint">Set in Schedule page</div>
            </div>
            """, unsafe_allow_html=True)
        with card3:
            st.markdown(f"""
            <div class="pipe-schedule-card">
                <div class="ps-label">Last run</div>
                <div class="ps-value">{status.get("completed_runs", 0)} completed</div>
                <div class="ps-hint">{status.get("total_findings", 0)} signals total</div>
            </div>
            """, unsafe_allow_html=True)

        # KPI row
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Signals Detected",   status.get("total_findings", 0))
        c2.metric("Runs Completed",     status.get("completed_runs", 0))
        c3.metric("Sources Monitored",  len(api_get("/api/sources")))
        c4.metric("Pipeline Status",    "▶ Running" if is_running else "● Idle")

    # Live pipeline progress
    if status.get("is_running"):
        ps       = api_get("/api/pipeline-status", use_cache=False)
        stage    = ps.get("stage","Running")
        progress = ps.get("progress", 0)
        detail   = ps.get("detail","")
        updated_at = datetime.now().strftime("%H:%M:%S")
        st.markdown(f"""
            <div style='background:var(--c-surface);border:1px solid var(--b-subtle);border-radius:10px;
                    padding:1rem 1.5rem;margin:1rem 0;box-shadow:0 2px 6px rgba(0,0,0,0.04);'>
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>
                    <span style='color:var(--a-teal);font-size:13px;font-weight:600;'>
                    ⚡ PIPELINE RUNNING — {stage}
                </span>
                    <span style='color:var(--t-muted);font-size:12px;'>{progress}%</span>
            </div>
                <div style='background:var(--c-raised);border-radius:4px;height:6px;'>
                <div style='background:#2563eb;height:6px;border-radius:4px;width:{progress}%;'></div>
            </div>
                <div style='color:var(--t-muted);font-size:11px;margin-top:6px;'>{detail} · Last updated: {updated_at}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    if not findings:
        st.info("No intelligence signals yet. Click **⚡ Run Pipeline** above to start.")
    else:
        # Executive Intelligence Brief
        st.subheader("🧠 Executive Intelligence Brief")
        for f in findings[:5]:
            score = f.get("final_score", 0) or 0
            icon  = "🆕" if f.get("change_status") == "new" else "🔄"
            st.markdown(f"""
                <div style='background:var(--c-surface);border:1px solid var(--b-subtle);border-radius:10px;
                    padding:1rem 1.25rem;margin:6px 0;box-shadow:0 1px 4px rgba(0,0,0,0.04);'>
            <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
                <div style='flex:1;'>
                            <div style='font-weight:600;color:var(--t-primary);font-size:14px;'>
                        {icon} {f.get('title','')}
                    </div>
                            <div style='color:var(--t-secondary);font-size:13px;margin-top:4px;'>
                        {f.get('why_matters','') or f.get('summary','')[:120]}
                    </div>
                </div>
                <div style='margin-left:1rem;text-align:right;flex-shrink:0;'>
                    <div style='font-size:20px;font-weight:700;color:{"#16a34a" if score>=7 else "#d97706" if score>=4 else "#ef4444"};'>
                        {score:.1f}
                    </div>
                            <div style='font-size:10px;color:var(--t-muted);'>/ 10</div>
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
                            <div style='background:rgba(77,124,254,0.07);border-left:3px solid #2563eb;
                                padding:0.6rem 1rem;border-radius:0 8px 8px 0;margin:0.5rem 0;
                                        color:var(--a-blue);font-size:13px;'>
                        💡 {f['why_matters']}
                    </div>
                    """, unsafe_allow_html=True)
                if f.get("evidence"):
                    st.markdown(f"""
                            <div style='background:rgba(0,214,143,0.07);border-left:3px solid #16a34a;
                                padding:0.6rem 1rem;border-radius:0 8px 8px 0;margin:0.5rem 0;
                                        color:var(--a-green);font-size:12px;'>
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

    st.caption(f"Next run: {status.get('next_scheduled','N/A')}")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: WHAT CHANGED
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔄  What Changed":
    st.title("🔄  What Changed")
    st.caption("Signal delta between runs — NEW / UPDATED / UNCHANGED (table-wise)")
    st.caption("Primary: Changes table · Action: Select run, then expand details as needed.")

    runs      = api_get("/api/runs",{"limit":10})
    completed = [r for r in runs if r.get("status")=="completed"]
    if not completed:
        st.info("No completed runs yet.")
        st.stop()

    opts = {f"Run {r['run_id'][:8]} · {str(r.get('started_at',''))[:16]} · {r.get('total_found',0)} signals": r["run_id"]
            for r in completed}
    sel  = opts[st.selectbox("Select Run", list(opts.keys()), key="what_changed_run")]
    chg  = api_get(f"/api/changes/{sel}")

    new_items = chg.get("new",[])
    upd_items = chg.get("updated",[])
    unchanged = chg.get("unchanged",0)

    # Summary row — hero-style metric cards (table-wise)
    st.markdown("""
    <div class="hero-cards-row">
      <div class="hero-card"><div class="hero-card-label">🆕 New</div><div class="hero-card-value">""" + str(len(new_items)) + """</div></div>
      <div class="hero-card"><div class="hero-card-label">🔄 Updated</div><div class="hero-card-value">""" + str(len(upd_items)) + """</div></div>
      <div class="hero-card"><div class="hero-card-label">⏸ Unchanged</div><div class="hero-card-value">""" + str(unchanged) + """</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Table-wise: all new + updated in one table (Title, Score, Status, Summary, Cluster)
    all_changed = [("New", f) for f in new_items] + [("Updated", f) for f in upd_items]
    if all_changed:
        st.subheader("Changes table")
        rows = []
        for status_label, f in all_changed:
            rows.append({
                "Status": status_label,
                "Score": round((f.get("final_score") or 0), 1),
                "Title": (f.get("title") or ""),
                "Summary": (f.get("summary") or ""),
                "Cluster": f.get("topic_cluster") or "general",
                "Confidence": f"{(f.get('confidence_score') or 0.8):.0%}",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, column_config={
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Score": st.column_config.NumberColumn("Score", width="small"),
            "Title": st.column_config.TextColumn("Title", width="large"),
            "Summary": st.column_config.TextColumn("Summary", width="large"),
            "Cluster": st.column_config.TextColumn("Cluster", width="small"),
            "Confidence": st.column_config.TextColumn("Confidence", width="small"),
        })
        st.markdown("---")
        st.subheader("Detail (expand for full content)")
        for label, items in [("🆕 New Signals", new_items), ("🔄 Updated Signals", upd_items)]:
            if items:
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
    else:
        st.success("✅ All sources unchanged since last run.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: IMPACT ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎯  Impact Analysis":
    st.title("🎯  Impact Analysis")
    st.caption("Strategic scoring breakdown — Relevance · Novelty · Credibility · Actionability (table-wise)")
    st.caption("Primary: Signals overview table · Action: Use radar charts for top signals.")

    findings = api_get("/api/findings", {"limit":20})
    if not findings:
        st.info("No findings yet. Trigger a run first.")
        st.stop()

    # KPI strip for fast executive scan
    avg_score = round(sum((f.get("final_score", 0) or 0) for f in findings) / max(1, len(findings)), 2)
    high_impact = len([f for f in findings if (f.get("final_score", 0) or 0) >= 7])
    avg_conf = round(sum((f.get("confidence_score", 0.8) or 0.8) for f in findings) / max(1, len(findings)) * 100)
    st.markdown(f"""
    <div class="hero-cards-row">
      <div class="hero-card"><div class="hero-card-label">Signals Reviewed</div><div class="hero-card-value">{len(findings)}</div></div>
      <div class="hero-card"><div class="hero-card-label">Avg Impact Score</div><div class="hero-card-value">{avg_score}</div></div>
      <div class="hero-card"><div class="hero-card-label">High Impact (≥7)</div><div class="hero-card-value">{high_impact}</div></div>
      <div class="hero-card"><div class="hero-card-label">Avg Confidence</div><div class="hero-card-value">{avg_conf}%</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Summary table first (table-wise)
    st.subheader("Signals overview")
    score_rows = [{
        "Title": f.get("title",""),
        "Score": round((f.get("final_score") or 0), 1),
        "Confidence": f"{(f.get('confidence_score') or 0.8):.0%}",
        "Cluster": f.get("topic_cluster","general"),
        "Category": CAT_LABEL.get(f.get("category",""), f.get("category",""))
    } for f in findings[:20]]
    st.dataframe(pd.DataFrame(score_rows), use_container_width=True, hide_index=True)

    st.markdown("""
    <div style='background:var(--c-surface);border:1px solid var(--b-subtle);border-radius:10px;
                padding:1rem 1.5rem;margin:1rem 0;box-shadow:0 1px 4px rgba(0,0,0,0.04);
                font-size:14px;color:#374151;'>
        <strong>Impact Formula:</strong>
        &nbsp; <span style='color:var(--a-teal);font-weight:600;'>0.35</span> × Relevance
        + <span style='color:#16a34a;font-weight:600;'>0.25</span> × Novelty
        + <span style='color:#7c3aed;font-weight:600;'>0.20</span> × Credibility
        + <span style='color:#d97706;font-weight:600;'>0.20</span> × Actionability
    </div>
    """, unsafe_allow_html=True)

    try:
        import plotly.graph_objects as go
        PLOTLY = True
    except ImportError:
        PLOTLY = False

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
            rows.append({"Title":f.get("title",""),"Score":score,"Confidence":f"{conf:.0%}","Cluster":f.get("topic_cluster","general")})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("💼 Strategic implications table")
    why_rows = []
    for f in findings[:12]:
        why = f.get("why_matters", "")
        if why:
            why_rows.append({
                "Title": (f.get("title", "") or ""),
                "Impact": round((f.get("final_score", 0) or 0), 1),
                "Why it matters": why,
            })
    if why_rows:
        st.dataframe(
            pd.DataFrame(why_rows),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Title": st.column_config.TextColumn("Title", width="large"),
                "Impact": st.column_config.NumberColumn("Impact", width="small"),
                "Why it matters": st.column_config.TextColumn("Why it matters", width="large"),
            },
        )
    else:
        st.info("No strategic implications available yet.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: OBSERVABILITY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈  Observability":
    st.title("📈  Observability")
    st.caption("Agent performance · run history · signal distributions (table-wise)")
    st.caption("Primary: Per-agent performance table · Action: Validate stability and trend movement.")

    metrics = api_get("/metrics")
    if not metrics or metrics.get("total_runs",0) == 0:
        st.info("No completed runs yet.")
        st.stop()

    tr = metrics.get("total_runs",0)
    cr = metrics.get("completed_runs",0)
    fr = metrics.get("failed_runs",0)
    tf = metrics.get("total_findings",0)
    ae = metrics.get("avg_elapsed_sec",0)
    af = metrics.get("avg_findings_per_run",0)
    st.markdown(f"""
    <div class="hero-cards-row">
      <div class="hero-card"><div class="hero-card-label">Total Runs</div><div class="hero-card-value">{tr}</div></div>
      <div class="hero-card"><div class="hero-card-label">Completed</div><div class="hero-card-value">{cr}</div></div>
      <div class="hero-card"><div class="hero-card-label">Failed</div><div class="hero-card-value">{fr}</div></div>
      <div class="hero-card"><div class="hero-card-label">Total Signals</div><div class="hero-card-value">{tf}</div></div>
      <div class="hero-card"><div class="hero-card-label">Avg Elapsed (s)</div><div class="hero-card-value">{ae}</div></div>
      <div class="hero-card"><div class="hero-card-label">Avg Signals/Run</div><div class="hero-card-value">{af}</div></div>
    </div>
    """, unsafe_allow_html=True)

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
elif page == "🏷️  Entity Dashboard":
    st.title("🏷️  Entity Dashboard")
    st.caption("Entity mention trends vs prior run — mindshare tracking")
    st.caption("Primary: Entity trends table · Action: Track risers/fallers and topic clusters.")

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
        t1, t2, t3 = st.columns(3)
        risers = [r for r in rows if r["Δ"] > 0]
        fallers = [r for r in rows if r["Δ"] < 0]
        new_ent = [r for r in rows if "🆕" in r["Trend"]]
        with t1:
            st.markdown("**⬆️ Rising**")
            rising_rows = [{"Entity": r["Entity"], "Δ": f"+{r['Δ']}"} for r in risers[:5]] or [{"Entity": "—", "Δ": "0"}]
            st.dataframe(pd.DataFrame(rising_rows), use_container_width=True, hide_index=True)
        with t2:
            st.markdown("**⬇️ Falling**")
            falling_rows = [{"Entity": r["Entity"], "Δ": str(r["Δ"])} for r in fallers[:5]] or [{"Entity": "—", "Δ": "0"}]
            st.dataframe(pd.DataFrame(falling_rows), use_container_width=True, hide_index=True)
        with t3:
            st.markdown("**🆕 New This Run**")
            new_rows = [{"Entity": r["Entity"]} for r in new_ent[:5]] or [{"Entity": "—"}]
            st.dataframe(pd.DataFrame(new_rows), use_container_width=True, hide_index=True)

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
elif page == "🔭  SOTA Watch":
    st.title("🔭  SOTA Watch")
    st.caption("Benchmark leaderboard movements — who moved up or down")
    st.caption("Primary: Movement table · Action: Open details for score deltas and sources.")

    runs      = api_get("/api/runs",{"limit":10})
    completed = [r for r in runs if r.get("status")=="completed"]
    if not completed:
        st.info("No completed runs yet.")
        st.stop()

    opts = {f"Run {r['run_id'][:8]} · {str(r.get('started_at',''))[:16]}": r["run_id"] for r in completed}
    sel  = opts[st.selectbox("Select Run", list(opts.keys()), key="sota_run_sel")]
    sota = api_get(f"/api/sota-watch/{sel}")
    events = sota.get("sota_watch",[])

    if not events:
        st.info("No leaderboard movements this run. SOTA Watch activates when HF Benchmark findings appear across multiple runs.")
        st.markdown("---")
        st.subheader("📊 HF Benchmark Findings This Run (table)")
        hf = api_get("/api/findings",{"category":"hf_benchmarks","limit":20})
        if hf:
            hf_rows = [{
                "Title": (f.get("title", "") or ""),
                "Score": round((f.get("final_score") or 0), 1),
                "Summary": (f.get("summary", "") or ""),
            } for f in hf]
            st.dataframe(
                pd.DataFrame(hf_rows),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Title": st.column_config.TextColumn("Title", width="large"),
                    "Score": st.column_config.NumberColumn("Score", width="small"),
                    "Summary": st.column_config.TextColumn("Summary", width="large"),
                },
            )
        for f in hf:
            score = f.get("final_score",0) or 0
            with st.expander(f"[{score:.1f}] {f.get('title','')}"):
                impact_bar(score)
                st.write(f.get("summary",""))
                if f.get("evidence"): st.success("📎 "+f["evidence"])
    else:
        st.subheader(f"{len(events)} Leaderboard Movement(s) — table")
        sota_rows = []
        for event in events:
            delta = event.get("delta", 0) or 0
            movement = event.get("movement", "")
            icon = "⬆️" if movement == "up" else "⬇️"
            sota_rows.append({
                "Movement": f"{icon} {movement}",
                "Title": (event.get("title") or ""),
                "Δ": round(delta, 1),
                "Current": round((event.get("current_score", 0) or 0), 1),
                "Previous": round((event.get("previous_score", 0) or 0), 1),
            })
        st.dataframe(
            pd.DataFrame(sota_rows),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Movement": st.column_config.TextColumn("Movement", width="small"),
                "Title": st.column_config.TextColumn("Title", width="large"),
                "Δ": st.column_config.NumberColumn("Δ", width="small"),
                "Current": st.column_config.NumberColumn("Current", width="small"),
                "Previous": st.column_config.NumberColumn("Previous", width="small"),
            },
        )
        st.markdown("---")
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
elif page == "🔍  Findings Explorer":
    st.title("🔍  Findings Explorer")
    st.caption("Filter and browse signals — table-wise content below")
    st.caption("Primary: Filtered findings table · Action: Select one signal for deep detail.")

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
        avg_score = round(sum((f.get("final_score", 0) or 0) for f in findings) / max(1, len(findings)), 2)
        new_count = len([f for f in findings if f.get("change_status") == "new"])
        upd_count = len([f for f in findings if f.get("change_status") == "updated"])
        st.markdown(f"""
        <div class="hero-cards-row">
          <div class="hero-card"><div class="hero-card-label">Filtered Signals</div><div class="hero-card-value">{len(findings)}</div></div>
          <div class="hero-card"><div class="hero-card-label">Average Score</div><div class="hero-card-value">{avg_score}</div></div>
          <div class="hero-card"><div class="hero-card-label">New</div><div class="hero-card-value">{new_count}</div></div>
          <div class="hero-card"><div class="hero-card-label">Updated</div><div class="hero-card-value">{upd_count}</div></div>
        </div>
        """, unsafe_allow_html=True)

        findings_rows = []
        for i, f in enumerate(findings):
            score = (f.get("final_score", 0) or 0)
            conf = f"{(f.get('confidence_score', 0.8) or 0.8):.0%}"
            status = f.get("change_status", "new")
            title = f.get("title", "") or ""
            category = CAT_LABEL.get(f.get("category", ""), f.get("category", ""))
            cluster = f.get("topic_cluster", "general") or "general"
            publisher = f.get("publisher", "—") or "—"
            src = (f.get("source_url", "") or "").strip()
            findings_rows.append({
                "No.": i + 1,
                "Score": round(score, 1),
                "Conf": conf,
                "Status": status,
                "Title": title,
                "Category": category,
                "Cluster": cluster,
                "Publisher": publisher,
                "Source": src,
            })
        st.dataframe(
            pd.DataFrame(findings_rows),
            use_container_width=True,
            hide_index=True,
            column_config={
                "No.": st.column_config.NumberColumn("No.", width="small"),
                "Score": st.column_config.NumberColumn("Score", width="small"),
                "Conf": st.column_config.TextColumn("Conf", width="small"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Title": st.column_config.TextColumn("Title", width="large"),
                "Category": st.column_config.TextColumn("Category", width="small"),
                "Cluster": st.column_config.TextColumn("Cluster", width="medium"),
                "Publisher": st.column_config.TextColumn("Publisher", width="small"),
                "Source": st.column_config.LinkColumn("Source", width="small"),
            },
        )

        st.markdown("---")
        st.subheader("📄 Signal Detail")
        options = [
            f"{i+1}. {(f.get('title','') or '')[:65]} · {(f.get('final_score',0) or 0):.1f}"
            for i, f in enumerate(findings)
        ]
        selected = st.selectbox("Select signal", options, key="findings_detail_select")
        sel_idx = options.index(selected)
        finding = findings[sel_idx] if 0 <= sel_idx < len(findings) else None
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
elif page == "⚙️  Sources":
    st.title("⚙️ Source Management")
    st.caption("Configure crawl sources per agent — changes take effect next run")
    st.caption("Primary: Active sources table · Action: Search/filter and manage source lifecycle.")

    with st.form("add_source", clear_on_submit=True):
        st.subheader("➕ Add Source")
        c1, c2, c3 = st.columns([2, 4, 2])
        name = c1.text_input("Name *", placeholder="Mistral Blog")
        url = c2.text_input("URL *", placeholder="https://mistral.ai/news")
        agent_type = c3.selectbox(
            "Agent *",
            ["competitors", "model_providers", "research", "hf_benchmarks"],
            format_func=lambda x: CAT_LABEL.get(x, x),
        )
        if st.form_submit_button("Add Source", type="primary"):
            if not name.strip():
                st.error("Name required")
            elif not url.startswith("http"):
                st.error("URL must start with http:// or https://")
            else:
                try:
                    r = _http_session().post(
                        f"{API_URL}/api/sources",
                        json={"name": name.strip(), "url": url.strip(), "agent_type": agent_type},
                        timeout=5,
                    )
                    if r.ok:
                        clear_ui_cache()
                        st.success(f"✅ Added: {name}")
                        st.rerun()
                    elif r.status_code == 400:
                        st.warning("URL already exists.")
                    else:
                        st.error(f"Failed: {r.text}")
                except Exception as e:
                    st.error(str(e))

    st.markdown("---")
    st.subheader("📡 Active Sources")
    sources = api_get("/api/sources")
    if not sources:
        st.info("No sources. Add above or trigger a run to auto-seed from config.yaml.")
        st.stop()

    # Table-first management
    search_col, filter_col = st.columns([3, 2])
    src_search = search_col.text_input("Search source name or URL", placeholder="openai, huggingface, benchmark...")
    src_filter = filter_col.selectbox(
        "Filter agent",
        ["All", "competitors", "model_providers", "research", "hf_benchmarks"],
        format_func=lambda x: "All agents" if x == "All" else CAT_LABEL.get(x, x),
        key="sources_filter_agent",
    )

    filtered = sources
    if src_search.strip():
        q = src_search.strip().lower()
        filtered = [s for s in filtered if q in str(s.get("name", "")).lower() or q in str(s.get("url", "")).lower()]
    if src_filter != "All":
        filtered = [s for s in filtered if s.get("agent_type") == src_filter]

    total = len(filtered)
    seen = len([s for s in filtered if s.get("last_seen_at")])
    never = total - seen
    k1, k2, k3 = st.columns(3)
    k1.metric("Visible Sources", total)
    k2.metric("Seen At Least Once", seen)
    k3.metric("Never Crawled", never)

    src_rows = []
    for src in filtered:
        ls = src.get("last_seen_at")
        src_rows.append({
            "ID": src.get("id"),
            "Name": src.get("name", ""),
            "URL": src.get("url", ""),
            "Agent": CAT_LABEL.get(src.get("agent_type", ""), src.get("agent_type", "")),
            "Last Seen": str(ls)[:19] if ls else "Never",
            "Status": "Seen" if ls else "Pending",
        })
    st.dataframe(pd.DataFrame(src_rows), use_container_width=True, hide_index=True)

    action_col, btn_col = st.columns([5, 1])
    selected_source_id = action_col.selectbox(
        "Select source to delete",
        [r["ID"] for r in src_rows],
        format_func=lambda sid: f"#{sid} · {next((x['Name'] for x in src_rows if x['ID'] == sid), sid)}",
        key="sources_delete_sel",
    )
    btn_col.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    if btn_col.button("🗑 Delete", type="secondary", use_container_width=True, key="sources_delete_btn"):
        try:
            r = _http_session().delete(f"{API_URL}/api/sources/{selected_source_id}", timeout=5)
            if r.ok:
                clear_ui_cache()
                st.success(f"Removed source #{selected_source_id}")
                st.rerun()
            else:
                st.error(f"Failed: {r.status_code}")
        except Exception as e:
            st.error(str(e))


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: RUN HISTORY — table view (production-grade) + detail on selection
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📁  Run History":
    st.title("📁  Run History")
    st.caption("Runs in table view; select a run below for details, PDF, and per-agent breakdown.")
    st.caption("Primary: Run list table · Action: Select run and download digest or inspect agents.")

    runs = api_get("/api/runs")
    if not runs:
        st.info("No runs yet.")
        st.stop()

    icons = {"completed": "✅", "failed": "❌", "running": "⏳"}
    rows = []
    for run in runs:
        status = run.get("status", "unknown")
        run_id = run.get("run_id", "")
        started = str(run.get("started_at", ""))[:19]
        finished = str(run.get("finished_at") or "")[:19] or "—"
        found = run.get("total_found", 0)
        elapsed = run.get("elapsed_sec")
        elapsed_s = f"{elapsed:.0f}s" if elapsed is not None else "—"
        rows.append({
            "Status": f"{icons.get(status, '❓')} {status.upper()}",
            "Started": started,
            "Finished": finished,
            "Signals": found,
            "Elapsed": elapsed_s,
            "ID": run_id[:8] + "…",
            "Run ID": run_id,
        })

    df = pd.DataFrame(rows)
    df_display = df[["Status", "Started", "Finished", "Signals", "Elapsed", "ID"]].copy()
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Started": st.column_config.TextColumn("Started", width="medium"),
            "Finished": st.column_config.TextColumn("Finished", width="medium"),
            "Signals": st.column_config.NumberColumn("Signals", width="small"),
            "Elapsed": st.column_config.TextColumn("Elapsed", width="small"),
            "ID": st.column_config.TextColumn("ID", width="small"),
        },
    )

    st.markdown("---")
    st.subheader("Run details")
    opts = [f"{r['Status']} · {r['Started']} · {r['Signals']} signals" for r in rows]
    sel_idx = st.selectbox(
        "Select a run for details, PDF, and per-agent breakdown",
        range(len(opts)),
        format_func=lambda i: opts[i],
        key="run_history_sel",
    )
    if sel_idx is not None and 0 <= sel_idx < len(runs):
        run = runs[sel_idx]
        run_id = run.get("run_id", "")
        status = run.get("status", "unknown")
        found = run.get("total_found", 0)
        elapsed = run.get("elapsed_sec")

        r1, r2, r3 = st.columns(3)
        r1.metric("ID", run_id[:8] + "…")
        r1.caption(f"Status: {status}")
        r2.metric("Started", str(run.get("started_at", ""))[:16])
        r2.metric("Finished", str(run.get("finished_at") or "")[:16] or "In progress")
        r3.metric("Signals", found)
        if elapsed is not None:
            r3.metric("Elapsed", f"{elapsed:.0f}s")

        fbc = run.get("findings_by_category", {})
        if fbc:
            st.markdown("**By category**")
            cat_rows = [{"Category": f"{CAT_ICON.get(cat, '📌')} {cat}", "Count": count} for cat, count in fbc.items()]
            st.dataframe(pd.DataFrame(cat_rows), use_container_width=True, hide_index=True)

        ast2 = run.get("agent_status", {})
        if ast2:
            st.markdown("**Per-agent**")
            agent_rows = []
            for name, info in ast2.items():
                status_icon = "✅" if info.get("status") == "ok" else ("⏱️" if info.get("status") == "timeout" else "❌")
                elapsed_label = f"{info.get('elapsed_sec', 0):.1f}s" if info.get("elapsed_sec") else "—"
                agent_rows.append({
                    "Agent": name,
                    "Status": f"{status_icon} {info.get('status', 'unknown')}",
                    "Signals": info.get("found", 0),
                    "Elapsed": elapsed_label,
                })
            st.dataframe(pd.DataFrame(agent_rows), use_container_width=True, hide_index=True)

        a1, a2, a3 = st.columns([1.2, 1, 1])
        if run.get("pdf_path"):
            a1.markdown(f"[📥 Open PDF]({API_URL}/api/digest/{run_id}/pdf)")
            try:
                import os as _os
                for base in ["backend", ".", "", ""]:
                    pdf_abs = _os.path.join(base, run["pdf_path"]) if base else run["pdf_path"]
                    if _os.path.exists(pdf_abs):
                        with open(pdf_abs, "rb") as fh:
                            a2.download_button(
                                "⬇️ Save PDF",
                                fh.read(),
                                file_name=f"radar_{run_id[:8]}.pdf",
                                mime="application/pdf",
                                key=f"dl_{run_id}",
                                use_container_width=True,
                            )
                        break
            except Exception:
                pass

        if status == "failed" and run.get("error_log"):
            with st.expander("❌ Error log"):
                st.code(run["error_log"], language="text")

        preview_findings = a3.button("👁 Preview signals", key=f"view_{run_id}", use_container_width=True)
        if preview_findings:
            findings_rows = []
            for f in api_get(f"/api/findings/{run_id}")[:8]:
                score = f.get("final_score", 0) or 0
                badge = "🆕" if f.get("change_status") == "new" else "🔄"
                findings_rows.append({
                    "Score": round(score, 1),
                    "Status": badge,
                    "Title": (f.get("title", "") or ""),
                    "Summary": (f.get("summary", "") or ""),
                })
            if findings_rows:
                st.dataframe(pd.DataFrame(findings_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No findings captured for this run.")

        if status == "running" and st.button("🔄 Refresh", key=f"ref_{run_id}"):
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DIGEST ARCHIVE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📚  Digest Archive":
    st.title("📚  Digest Archive")
    st.caption("All past PDF digests — browse, search, download")
    st.caption("Primary: Digest archive table · Action: Select one run and preview attached signals.")

    runs = api_get("/api/runs")
    completed = [r for r in runs if r.get("status")=="completed" and r.get("pdf_path")]
    if not completed:
        st.info("No digests yet.")
        st.stop()

    search = st.text_input("🔍 Search by date or run ID", placeholder="2026-03-05 or b6d68b8f")
    if search:
        q = search.lower()
        completed = [
            r for r in completed
            if q in str(r.get("started_at", "")).lower() or q in r.get("run_id", "").lower()
        ]

    st.caption(f"**{len(completed)} digest(s)**")

    dig_rows = []
    for run in completed:
        run_id = run.get("run_id", "")
        started = str(run.get("started_at", ""))[:16]
        found = run.get("total_found", 0)
        elapsed = run.get("elapsed_sec")
        fbc = run.get("findings_by_category", {})
        cat_summary = " · ".join(f"{CAT_ICON.get(k, '📌')} {k}: {v}" for k, v in fbc.items()) if fbc else "—"
        dig_rows.append({
            "Run ID": run_id[:8] + "…",
            "Date": started,
            "Signals": found,
            "Elapsed": f"{elapsed:.0f}s" if elapsed else "—",
            "Categories": cat_summary,
            "_run_id": run_id,
        })

    st.dataframe(
        pd.DataFrame([{k: v for k, v in row.items() if k != "_run_id"} for row in dig_rows]),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.subheader("Digest details")
    selected_digest = st.selectbox(
        "Select digest run",
        [row["_run_id"] for row in dig_rows],
        format_func=lambda rid: next((f"{r['Date']} · {r['Signals']} signals · {r['Run ID']}" for r in dig_rows if r["_run_id"] == rid), rid),
        key="digest_sel",
    )
    run = next((r for r in completed if r.get("run_id") == selected_digest), None)
    if run:
        run_id = run.get("run_id", "")
        started = str(run.get("started_at", ""))[:16]
        d1, d2, d3 = st.columns([1.2, 1, 1])
        d1.markdown(f"[📥 Open in browser]({API_URL}/api/digest/{run_id}/pdf)")
        try:
            import os as _os
            for base in ["backend", ".", "", ""]:
                pdf_abs = _os.path.join(base, run["pdf_path"]) if base else run["pdf_path"]
                if _os.path.exists(pdf_abs):
                    with open(pdf_abs, "rb") as fh:
                        d2.download_button(
                            "⬇️ Save PDF",
                            fh.read(),
                            file_name=f"radar_{started[:10]}.pdf",
                            mime="application/pdf",
                            key=f"arch_{run_id}",
                            use_container_width=True,
                        )
                    break
        except Exception:
            pass

        if d3.button("👁 Preview signals", key=f"prev_{run_id}", use_container_width=True):
            previews = []
            for f in api_get(f"/api/findings/{run_id}")[:8]:
                score = f.get("final_score", 0) or 0
                previews.append({
                    "Score": round(score, 1),
                    "Title": (f.get("title", "") or ""),
                    "Summary": (f.get("summary", "") or ""),
                })
            if previews:
                st.dataframe(pd.DataFrame(previews), use_container_width=True, hide_index=True)
            else:
                st.info("No findings available for this digest.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: EMAIL RECIPIENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📧  Email Recipients":
    st.title("📧  Email Recipients")
    st.caption("Manage distribution list — configurable recipients")
    st.caption("Primary: Recipients table · Action: Toggle status, remove, add, and send test.")

    st.info("📬 **No DNS required.** Uses Resend's shared domain `onboarding@resend.dev` — works on any network including corporate firewalls.")

    st.subheader("📋 Current Recipients")
    recipients = api_get("/api/email-recipients") or []

    if not recipients:
        st.warning("No recipients yet. Add one below.")
    else:
        active_list = [r for r in recipients if r.get("is_active", 1)]
        inactive_list = [r for r in recipients if not r.get("is_active", 1)]
        st.caption(f"{len(active_list)} active · {len(inactive_list)} paused · {len(recipients)} total")

        rec_rows = []
        for rec in recipients:
            rec_rows.append({
                "ID": rec.get("id"),
                "Status": "✅ Active" if rec.get("is_active", 1) else "⏸ Paused",
                "Email": rec.get("email", ""),
                "Name": rec.get("name") or "—",
                "Note": rec.get("note") or "—",
                "Source": "config.yaml" if rec.get("from_config") else "UI",
            })
        st.dataframe(
            pd.DataFrame([{k: v for k, v in row.items() if k != "ID"} for row in rec_rows]),
            use_container_width=True,
            hide_index=True,
        )

        act_col, toggle_col, del_col = st.columns([4, 1, 1])
        selected_rec_id = act_col.selectbox(
            "Select recipient",
            [r["ID"] for r in rec_rows],
            format_func=lambda rid: next((f"#{rid} · {x['Email']} ({x['Status']})" for x in rec_rows if x["ID"] == rid), str(rid)),
            key="recipient_sel",
        )
        selected_rec = next((r for r in recipients if r.get("id") == selected_rec_id), None)
        is_active = bool(selected_rec.get("is_active", 1)) if selected_rec else True

        if toggle_col.button("⏸ Pause" if is_active else "▶️ Activate", use_container_width=True, key="recipient_toggle_btn"):
            try:
                r = _http_session().patch(f"{API_URL}/api/email-recipients/{selected_rec_id}/toggle", timeout=5)
                if r.ok:
                    clear_ui_cache()
                    st.rerun()
                else:
                    st.error(r.json().get("detail", "Failed"))
            except Exception as e:
                st.error(str(e))
        if del_col.button("🗑 Remove", use_container_width=True, key="recipient_delete_btn"):
            try:
                r = _http_session().delete(f"{API_URL}/api/email-recipients/{selected_rec_id}", timeout=5)
                if r.ok:
                    clear_ui_cache()
                    st.success("Recipient removed")
                    st.rerun()
                else:
                    st.error(r.json().get("detail", "Failed"))
            except Exception as e:
                st.error(str(e))

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
                r = _http_session().post(f"{API_URL}/api/email-recipients",
                    json={"email":new_email,"name":new_name or None,"note":new_note or None},timeout=5)
                if r.status_code==200:
                    clear_ui_cache()
                    st.success(f"✅ Added: {new_email}")
                    st.rerun()
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
                    r = _http_session().post(f"{API_URL}/api/email-recipients/test",
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
elif page == "📅  Schedule":
    st.title("📅 Schedule & System Status")
    st.caption("Primary: Schedule/status tables · Action: verify providers and operational readiness.")

    status = api_get("/api/status")

    next_run = status.get("next_scheduled")
    next_run_str = "—"
    next_eta = "Scheduler not running"
    if next_run:
        try:
            next_dt = datetime.fromisoformat(next_run)
            next_run_str = next_dt.strftime("%Y-%m-%d %H:%M %Z")
            delta = next_dt.replace(tzinfo=None) - datetime.now()
            h = int(delta.total_seconds() // 3600)
            m = int((delta.total_seconds() % 3600) // 60)
            next_eta = f"In approximately {h}h {m}m"
        except Exception:
            next_run_str = str(next_run)
            next_eta = "Parsed from API"

    st.markdown(f"""
    <div class="hero-cards-row">
      <div class="hero-card"><div class="hero-card-label">Next Scheduled Run</div><div class="hero-card-value" style="font-size:1.05rem;">{next_run_str}</div></div>
      <div class="hero-card"><div class="hero-card-label">ETA</div><div class="hero-card-value" style="font-size:1.05rem;">{next_eta}</div></div>
      <div class="hero-card"><div class="hero-card-label">Total Signals</div><div class="hero-card-value">{status.get("total_findings",0)}</div></div>
      <div class="hero-card"><div class="hero-card-label">Total Runs</div><div class="hero-card-value">{status.get("total_runs",0)}</div></div>
      <div class="hero-card"><div class="hero-card-label">Completed</div><div class="hero-card-value">{status.get("completed_runs",0)}</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("⚙️ Schedule Config")
    st.dataframe(
        pd.DataFrame([
            {"Key": "global.run_time", "Value": "07:00", "Notes": "Daily schedule"},
            {"Key": "global.timezone", "Value": "Asia/Kolkata", "Notes": "Local timezone"},
            {"Key": "Apply", "Value": "Restart API", "Notes": "Required after config changes"},
        ]),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.subheader("🔑 Configuration Status")
    st.caption("Read from backend — accurate regardless of where keys are stored")

    llm_status = status.get("llm_status", "❌ Not configured")
    email_status = status.get("email_status", "❌ Not configured")
    active_recipients = status.get("active_recipients", 0)
    status_rows = [
        {"Component": "🤖 LLM Provider", "Status": llm_status},
        {"Component": "📧 Email Provider", "Status": email_status},
        {"Component": "👥 Active Recipients", "Status": f"✅ {active_recipients}" if active_recipients > 0 else "⚠️ 0"},
    ]
    st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🔗 Quick Links")
    links = pd.DataFrame([
        {"Link": "📡 API Docs", "URL": f"{API_URL}/docs"},
        {"Link": "🗄 DB Explorer", "URL": f"{API_URL}/admin/db"},
        {"Link": "📊 Metrics JSON", "URL": f"{API_URL}/metrics"},
        {"Link": "❤ Health", "URL": f"{API_URL}/health"},
    ])
    st.dataframe(
        links,
        use_container_width=True,
        hide_index=True,
        column_config={"URL": st.column_config.LinkColumn("URL")},
    )