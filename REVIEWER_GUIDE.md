🛰 Triple Stack Radar — Reviewer & Judge Guide

Autonomous Multi-Agent Intelligence Platform 

Two ways to review this project.
Pick the one that suits your setup — both demonstrate the full system.

Option A — Live Demo (No Setup Required)

The full system is already deployed.

Frontend: Streamlit Cloud
Backend: Render (FastAPI)

🌐 Frontend — Streamlit Dashboard

Live URL

https://frontier-ai-radar-qtphyvfsuw7w9ngqsvaagh.streamlit.app/

Features available:

All 12 dashboard pages active

Trigger pipeline runs from UI

Real findings generated live

Observability metrics and run history

⚙ Backend — Render API

Render Project

https://dashboard.render.com/project/prj-d6ktmnchg0os73ceadbg

Capabilities:

FastAPI backend

22 REST endpoints

Swagger UI available at /docs

Persistent SQLite database

Deployment Architecture
Layer	Deployment
Frontend	Streamlit Cloud — auto deploy from GitHub
Backend	Render — FastAPI web service
Database	SQLite (persistent disk on Render)
LLM	OpenRouter / Anthropic
Email	SendGrid (optional)
Scheduler	APScheduler — daily run at 07:00 IST
Option B — Run Locally (Full System ~5 Minutes)
Step 1 — Prerequisites

Install Python 3.10+

Check version:

python --version

If not installed:

https://python.org/downloads
Step 2 — Download & Extract

Download the project ZIP

Extract it to any folder

Open a terminal inside the extracted folder

Step 3 — Configure API Key

Inside the backend/ folder:

Copy .env.example

Rename to .env

Open .env and fill one block only

Option A — OpenRouter (Easiest)
LLM_API_KEY=your-key-here
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=anthropic/claude-3.5-sonnet

Signup:

https://openrouter.ai
Option B — Anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here

Email configuration is optional and can be skipped.

Step 4 — Install & Run
Windows
pip install -r backend/requirements.txt
python start.py
Mac / Linux
pip install -r backend/requirements.txt
python start.py

start.py automatically:

Starts FastAPI backend (port 8000)

Starts Streamlit dashboard (port 8501)

Opens browser automatically

Runs system health checks

Step 5 — Access the System
Component	URL
Dashboard	http://localhost:8501

API Docs	http://localhost:8000/docs

Health Check	http://localhost:8000/health
Quick Test Flow (3 Minutes)

Open

http://localhost:8501

Navigate to ⚙ Sources

Verify sources are listed.

Click

🚀 Trigger Run

Wait ~90 seconds.

Navigate to 🔍 Findings Explorer

See ranked findings.

Navigate to 🔄 What Changed

See:

NEW

UPDATED

UNCHANGED signals

Navigate to 📁 Run History

Download the generated PDF digest.

Open API docs

http://localhost:8000/docs

Test endpoints directly from Swagger.

What Reviewers Should Evaluate
Functional Requirements
Requirement	Verification
FR1 — Configurable sources	⚙ Sources page → add/remove URLs
FR2 — Multi-format extraction	Run logs show HTML + RSS processed
FR3 — Structured summaries	Findings Explorer shows title, summary, why_matters, evidence
FR4 — Deduplication & clustering	Run log shows multi-layer dedup
FR5 — PDF digest	Run History → download PDF
FR6 — Email delivery	Schedule page shows email provider status
FR7 — Web UI	Full 12-page dashboard
Ranking Formula

Impact Score formula:

Impact =
0.35 × Relevance
+ 0.25 × Novelty
+ 0.20 × Credibility
+ 0.20 × Actionability

Visible on every finding in the Findings Explorer.

API — 22 Endpoints

Interactive Swagger UI:

Local

http://localhost:8000/docs

Render

https://dashboard.render.com/project/prj-d6ktmnchg0os73ceadbg

Endpoints can be tested directly in the browser.

Troubleshooting
Issue	Fix
No module named X	Run pip install -r backend/requirements.txt
Port already in use	Kill process using port 8000
API error in dashboard	Wait ~20 seconds for backend startup
Pipeline returns 0 findings	Ensure .env has valid LLM_API_KEY
Email not working	Expected on corporate networks — SMTP blocked
Architecture Summary
Layer	Details
Agents	Competitor Watcher · Model Provider · Research Scout · HF Benchmark
Pipeline	Dedup → Change Detection → Topic Clustering → Entity Trends
Output	SQLite DB · PDF Digest · Email · REST API · Dashboard
Stack	FastAPI · SQLAlchemy · SQLite · Streamlit · APScheduler
Extraction	httpx · BeautifulSoup
LLM	OpenRouter / Anthropic
Technology Stack

FastAPI

SQLAlchemy

SQLite

Streamlit

APScheduler

BeautifulSoup

ReportLab

OpenRouter / Anthropic

🛰 Triple Stack Radar 

Autonomous Multi-Agent Intelligence Platform

FastAPI · SQLAlchemy · SQLite · Streamlit · APScheduler · OpenRouter · Anthropic