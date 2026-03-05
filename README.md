# 🛰 Frontier AI Radar — v4.2

> **Daily multi-agent AI intelligence system.**  
> Tracks competitor releases, model launches, research publications, and benchmark updates.  
> Delivers structured findings, ranked intelligence signals, PDF digest, and email — fully automated.

---

## ⚡ Quickstart — One Command

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Configure environment
copy backend\.env.example backend\.env    # Windows
cp backend/.env.example backend/.env      # Mac/Linux
# → edit backend/.env with your API keys

# 3. Start everything
python start.py
```

**That's it.** Opens automatically:

| Service | URL |
|---|---|
| 🖥 UI Dashboard | http://localhost:8501 |
| 📡 API + Swagger | http://localhost:8000/docs |
| 🗄 DB Explorer | http://localhost:8000/admin/db |
| 📊 Metrics | http://localhost:8000/metrics |
| ❤ Health | http://localhost:8000/health |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│           APScheduler (daily 07:00 IST)                     │
│         + POST /api/runs/trigger (manual)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ asyncio.gather()
         ┌───────────────┼───────────────────┐
         ▼               ▼                   ▼                 ▼
  CompetitorAgent  ModelProviderAgent  ResearchAgent  HFBenchmarkAgent
  (4 URLs)         (7 URLs)            (arXiv feeds)  (HF leaderboard)
         │               │                   │                 │
         └───────────────┴───────────────────┘─────────────────┘
                         │
              ┌──────────▼──────────┐
              │  3-Layer Dedup      │  hash → title similarity → semantic overlap
              │  Change Detection   │  NEW / UPDATED / UNCHANGED
              │  Topic Clustering   │  8 clusters (safety, benchmarks, releases...)
              │  Ranking            │  0.35×impact + 0.25×novelty + 0.20×credibility + 0.20×actionability
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  SQLite Database    │  findings · runs · sources · snapshots
              │  Entity Trends      │  compare vs prior run
              │  SOTA Watch         │  benchmark score deltas
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  PDF Digest         │  ReportLab, always generated
              │  Email Delivery     │  Resend API (port 443) or SMTP
              │  Streamlit UI       │  8 pages
              │  REST API           │  22 endpoints + Swagger
              └─────────────────────┘
```

---

## 🗄 Database — For Reviewers & Stakeholders

No database tools required. Three ways to inspect the DB:

### 1. Browser DB Explorer (easiest)
```
http://localhost:8000/admin/db
```
Shows all tables with live data, row counts, and quick links.

### 2. REST API (JSON)
```bash
# All findings
GET http://localhost:8000/api/findings?limit=100

# Specific run
GET http://localhost:8000/api/runs

# Change detection (what's new vs updated)
GET http://localhost:8000/api/changes/{run_id}

# Entity trends vs prior run
GET http://localhost:8000/api/entity-trends/{run_id}

# Topic clusters
GET http://localhost:8000/api/clusters

# Full metrics
GET http://localhost:8000/metrics
```

### 3. CSV Export (for Excel/analysis)
```
http://localhost:8000/admin/db/export/findings
http://localhost:8000/admin/db/export/runs
http://localhost:8000/admin/db/export/sources
```

### 4. DB Schema
```
http://localhost:8000/admin/db/schema
```
Returns all table names, column names, and row counts as JSON.

---

## 📡 Full API Reference

Interactive Swagger UI: **http://localhost:8000/docs**

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/runs/trigger` | Trigger a pipeline run |
| `GET` | `/api/runs` | List all runs |
| `GET` | `/api/runs/{run_id}` | Single run details |
| `GET` | `/api/findings` | All findings (filterable) |
| `GET` | `/api/findings/{run_id}` | Findings for a run |
| `GET` | `/api/digest/{run_id}/pdf` | Download PDF digest |
| `GET` | `/api/changes/{run_id}` | NEW/UPDATED/UNCHANGED breakdown |
| `GET` | `/api/entity-trends/{run_id}` | Entity mention deltas vs prior run |
| `GET` | `/api/sota-watch/{run_id}` | Benchmark leaderboard movements |
| `GET` | `/api/entities` | Top entities (with run filter) |
| `GET` | `/api/clusters` | Findings by topic cluster |
| `GET` | `/api/sources` | All configured sources |
| `POST` | `/api/sources` | Add a new source |
| `DELETE` | `/api/sources/{id}` | Remove a source |
| `GET` | `/api/sources/{id}/history` | Per-source snapshot history |
| `GET` | `/api/snapshots` | Raw page snapshots |
| `GET` | `/api/status` | System status + next scheduled run |
| `GET` | `/metrics` | Full observability metrics |
| `GET` | `/admin/db` | Browser DB explorer (HTML) |
| `GET` | `/admin/db/export/{table}` | Download table as CSV |
| `GET` | `/admin/db/schema` | Table schemas + row counts |
| `POST` | `/api/runs/recover` | Recover stuck runs |
| `GET` | `/health` | Health check |

---

## 🖥 UI Dashboard Pages

| Page | Description |
|---|---|
| 📊 Dashboard | KPIs, top signals, category breakdown |
| 🔄 What Changed | NEW / UPDATED / UNCHANGED since last run |
| 📈 Observability | Per-agent metrics, run history charts |
| 🏷️ Entity Dashboard | Entity trends, topic clusters, risers/fallers |
| 🔭 SOTA Watch | Benchmark leaderboard movements |
| 🔍 Findings Explorer | Filterable table + full finding detail |
| ⚙️ Sources | Add/remove/manage crawl sources |
| 📁 Run History | Past runs, PDF download, agent status |
| 📅 Schedule | Scheduler config, email status |

---

## ⚙️ Configuration

### LLM Provider (`backend/.env`)
```dotenv
# OpenRouter (recommended — supports Claude, GPT, Llama, etc.)
LLM_API_KEY=your-openrouter-key
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=anthropic/claude-3.5-sonnet
```

### Email (`backend/.env`)
```dotenv
# Resend (recommended — works on all networks including corporate)
RESEND_API_KEY=re_your_key
RESEND_FROM=AI Radar <onboarding@resend.dev>
```

### Sources (`backend/config.yaml`)
```yaml
agents:
  competitors:
    - name: "Google DeepMind"
      release_urls:
        - "https://deepmind.google/blog/"
```
Or add sources live via the UI or `POST /api/sources`.

---

## 🐳 Docker Deployment

```bash
# Build and run everything
docker-compose up --build

# Services start at same URLs
# Data persists in Docker volumes
```

---

## 🧪 Tests

```bash
cd backend
pytest ../tests/ -v
```

---

## 📁 Project Structure

```
frontier-ai-radar/
├── start.py                    ← One-command launcher
├── docker-compose.yml
├── Dockerfile
├── README.md
├── backend/
│   ├── .env.example            ← Copy to .env
│   ├── config.yaml             ← Sources + schedule
│   ├── requirements.txt
│   └── app/
│       ├── main.py             ← FastAPI (22 endpoints)
│       ├── pipeline.py         ← Core intelligence pipeline
│       ├── models.py           ← SQLAlchemy ORM (4 tables)
│       ├── schemas.py          ← Pydantic response models
│       ├── scheduler.py        ← APScheduler daily trigger
│       ├── database.py         ← SQLite session factory
│       ├── agents/
│       │   ├── base_agent.py
│       │   ├── competitor_agent.py
│       │   ├── model_provider_agent.py
│       │   ├── research_agent.py
│       │   └── hf_benchmark_agent.py
│       └── services/
│           ├── summarizer.py   ← LLM extraction (provider-agnostic)
│           ├── deduplicator.py ← 3-layer dedup + clustering
│           ├── ranker.py       ← Weighted scoring formula
│           ├── pdf_generator.py
│           └── email_sender.py ← Resend + SMTP fallback
├── frontend/
│   └── streamlit_app.py        ← 9-page dashboard
└── tests/
    ├── test_ranker.py
    ├── test_deduplicator.py
    └── test_summarizer.py
```
