# GitHub + Streamlit Cloud Deployment Guide

## Step 1 — Create GitHub Repository

1. Go to **github.com** → click **New repository**
2. Name it: `frontier-ai-radar`
3. Set to **Public** (required for free Streamlit Cloud)
4. Do NOT add README (we have one)
5. Click **Create repository**

---

## Step 2 — Push Code to GitHub

Open terminal in your project folder and run these commands **one by one:**

```bash
# Initialize git (only first time)
git init

# Add all files
git add .

# First commit
git commit -m "Frontier AI Radar v4.2 - Multi-agent AI intelligence system"

# Connect to your GitHub repo (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/frontier-ai-radar.git

# Push to GitHub
git branch -M main
git push -u origin main
```

If it asks for username/password → use your GitHub username and a Personal Access Token (not your password).
Get a token: GitHub → Settings → Developer Settings → Personal Access Tokens → Generate new token (classic) → check "repo" scope.

---

## Step 3 — Deploy on Streamlit Cloud

1. Go to **share.streamlit.io** → Sign in with GitHub
2. Click **New app**
3. Fill in:
   - **Repository:** `YOUR_USERNAME/frontier-ai-radar`
   - **Branch:** `main`
   - **Main file path:** `frontend/streamlit_app.py`
4. Click **Advanced settings** → set Python version to `3.11`
5. Click **Deploy**

---

## Step 4 — Add API Keys on Streamlit Cloud

> **IMPORTANT:** Never put API keys in GitHub. Use Streamlit's secrets manager.

1. In your deployed app → click **⋮ (three dots)** → **Settings**
2. Click **Secrets** tab
3. Paste this (fill in your real keys):

```toml
API_URL = "http://localhost:8000"

LLM_API_KEY = "your-openrouter-key"
LLM_BASE_URL = "https://openrouter.ai/api/v1"
LLM_MODEL = "anthropic/claude-3.5-sonnet"

RESEND_API_KEY = "re_your_key"
```

4. Click **Save** → app restarts automatically

---

## Step 5 — Verify Deployment

Your app will be live at:
```
https://YOUR_USERNAME-frontier-ai-radar-frontend-streamlit-app-XXXXX.streamlit.app
```

Or set a custom subdomain in App Settings.

---

## Important Notes for Streamlit Cloud

**Streamlit Cloud runs only the frontend** (streamlit_app.py).
The FastAPI backend runs separately (locally or on a cloud server).

For a full cloud deployment where the pipeline also runs:

| Option | Cost | Difficulty |
|---|---|---|
| Streamlit Cloud (UI only) | Free | ⭐ Easy |
| Railway.app (full stack) | Free tier | ⭐⭐ Medium |
| Render.com (full stack) | Free tier | ⭐⭐ Medium |
| Docker on any VPS | ~$5/mo | ⭐⭐⭐ Advanced |

**For the hackathon submission**, Streamlit Cloud for the UI + a note that the backend runs locally is perfectly acceptable.

---

## Updating the Code

After making changes locally:

```bash
git add .
git commit -m "describe your change"
git push
```

Streamlit Cloud auto-redeploys on every push to `main`.
