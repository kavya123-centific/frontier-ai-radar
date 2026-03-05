# 🛰 Frontier AI Radar — Reviewer & Judge Guide

> **Two ways to review this project.**
> Pick the one that suits your setup — both show the full system.

---

## Option A — Run Locally (Full System, 5 Minutes)

### Step 1 — Prerequisites
You need Python 3.10+ installed. Check with:
```
python --version
```
If not installed → https://python.org/downloads

---

### Step 2 — Download & Extract
1. Download `frontier-ai-radar-v4.2.zip`
2. Extract it anywhere (e.g. Desktop)
3. You'll get a folder called `frontier-ai-radar-v4.1`

---

### Step 3 — Configure API Key
1. Go into the folder → open `backend/` folder
2. Copy `.env.example` → rename copy to `.env`
3. Open `.env` in Notepad and fill in ONE block:

**Easiest (OpenRouter — free signup at openrouter.ai):**
```
LLM_API_KEY=your-key-here
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=anthropic/claude-3.5-sonnet
```

**Already have Anthropic key:**
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Leave everything else as-is. Email is optional — skip it.

---

### Step 4 — Install & Run (ONE command)

Open a terminal in the extracted folder and run:

**Windows:**
```powershell
pip install -r backend/requirements.txt
python start.py
```

**Mac/Linux:**
```bash
pip install -r backend/requirements.txt
python start.py
```

`start.py` automatically:
- Starts the FastAPI backend (port 8000)
- Starts the Streamlit dashboard (port 8501)
- Opens both in your browser
- Shows you a health check

---

### Step 5 — Test the System

Once running, open these URLs:

| What | URL |
|---|---|
| 🖥 **Main Dashboard** | http://localhost:8501 |
| 📡 **API + Swagger** | http://localhost:8000/docs |
| 🗄 **DB Explorer** | http://localhost:8000/admin/db |
| ❤ **Health Check** | http://localhost:8000/health |

**Test flow (3 minutes):**
1. Open http://localhost:8501
2. Click **⚙️ Sources** in sidebar → verify sources are listed
3. Click **🚀 Trigger Manual Run** in sidebar
4. Wait ~90 seconds (watch terminal for progress logs)
5. Navigate to **🔍 Findings Explorer** → see ranked findings
6. Navigate to **🔄 What Changed** → see NEW/UPDATED/UNCHANGED
7. Navigate to **📁 Run History** → click **⬇️ Save PDF**
8. Open http://localhost:8000/admin/db → browse the live database
9. Open http://localhost:8000/docs → try any endpoint live

---

## Option B — View Live Demo (No Setup)

> **Live deployment on Streamlit Cloud:**
> 🔗 **https://frontier-ai-radar.streamlit.app**
>
> The live demo runs with a shared API key. All features are active.
> Trigger a run directly from the UI and see real findings appear.

---

## What to Evaluate

### Functional Requirements (per spec)
| Requirement | How to verify |
|---|---|
| FR1 — Configurable sources | ⚙️ Sources page → add/remove URLs live |
| FR2 — Multi-format extraction | Run logs show HTML + RSS feeds processed |
| FR3 — Structured summaries | 🔍 Findings Explorer → expand any finding → see title, summary, why_matters, evidence, confidence |
| FR4 — Dedup + clustering | Run log: `"Dedup: 9 input → 7 unique (2 removed across 3 layers)"` |
| FR5 — PDF digest | 📁 Run History → ⬇️ Save PDF |
| FR6 — Email delivery | Schedule page shows Resend status |
| FR7 — Web UI | Full 9-page dashboard |

### Ranking Formula (spec section 14)
```
Impact = 0.35 × Relevance + 0.25 × Novelty + 0.20 × Credibility + 0.20 × Actionability
```
Visible on every finding card in the Findings Explorer.

### Database (no tools needed)
- Browser view: http://localhost:8000/admin/db
- JSON export: http://localhost:8000/api/findings?limit=100
- CSV export: http://localhost:8000/admin/db/export/findings
- Schema: http://localhost:8000/admin/db/schema

### API (22 endpoints)
Full interactive Swagger UI: http://localhost:8000/docs
Try any endpoint directly from the browser — no Postman needed.

---

## Troubleshooting

**"No module named X"**
```
pip install -r backend/requirements.txt
```

**"Port already in use"**
```
# Kill whatever is using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <pid> /F
```

**"API error" in dashboard first 20 seconds**
Normal — backend is starting up. Disappears automatically.

**Pipeline shows 0 findings**
Check `.env` has a valid `LLM_API_KEY`. Without it, LLM extraction fails silently.

**Email not working**
Expected — SMTP blocked on most corporate networks.
Email is optional. PDF download works regardless.

---

## Architecture Summary

```
4 Agents (parallel)          Pipeline              Output
──────────────────    ─────────────────────    ──────────────
Competitor Watcher  ─┐
Model Provider      ─┤─→ 3-Layer Dedup ──→ Rank ──→ SQLite DB
Research Scout      ─┤─→ Change Detect         ──→ PDF Digest
HF Benchmark        ─┘─→ Topic Cluster         ──→ Email
                          Entity Trends         ──→ Dashboard
                          SOTA Watch            ──→ REST API
```

**Tech stack:** FastAPI · SQLAlchemy · SQLite · httpx · BeautifulSoup · ReportLab · Streamlit · APScheduler · OpenRouter/Anthropic
