#!/usr/bin/env python3
"""
start.py — Frontier AI Radar One-Command Launcher
===================================================
Starts both the FastAPI backend and Streamlit frontend
in a single command. No terminal expertise required.

Usage:
    python start.py

Opens:
    API Dashboard:  http://localhost:8000/docs   (Swagger UI)
    UI Dashboard:   http://localhost:8501
    DB Explorer:    http://localhost:8000/admin/db
    Health:         http://localhost:8000/health
"""

import os
import sys
import time
import signal
import subprocess
import webbrowser
import threading
from pathlib import Path

BASE     = Path(__file__).parent
BACKEND  = BASE / "backend"
FRONTEND = BASE / "frontend"
ENV_FILE = BACKEND / ".env"

# ── Colour helpers (Windows-safe) ─────────────────────────────────────────
def _c(code, text): return f"\033[{code}m{text}\033[0m"
def green(t):  return _c("92", t)
def yellow(t): return _c("93", t)
def red(t):    return _c("91", t)
def bold(t):   return _c("1",  t)
def cyan(t):   return _c("96", t)

# ── Pre-flight checks ──────────────────────────────────────────────────────
def check_env():
    if not ENV_FILE.exists():
        print(red("✗ backend/.env not found."))
        print(yellow("  Copy backend/.env.example → backend/.env and fill in your keys."))
        sys.exit(1)

    # Load .env manually (no dotenv dependency at launch time)
    env = {}
    for line in ENV_FILE.read_text(encoding='utf-8', errors='ignore').splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()

    llm_ok = bool(env.get("LLM_API_KEY") or env.get("ANTHROPIC_API_KEY"))
    if not llm_ok:
        print(yellow("⚠  No LLM API key found in .env (LLM_API_KEY or ANTHROPIC_API_KEY)."))
        print(yellow("   Pipeline will run but LLM extraction will fail."))

    return env

def check_deps():
    missing = []
    for pkg in ["fastapi", "uvicorn", "streamlit", "sqlalchemy", "httpx"]:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)
    if missing:
        print(red(f"✗ Missing packages: {', '.join(missing)}"))
        print(yellow("  Run: pip install -r backend/requirements.txt"))
        sys.exit(1)

# ── Process management ─────────────────────────────────────────────────────
procs = []

def start_backend():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND)
    # Load .env into environment
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding='utf-8', errors='ignore').splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    p = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=str(BACKEND),
        env=env,
    )
    procs.append(p)
    return p

def start_frontend():
    env = os.environ.copy()
    env["API_URL"] = "http://localhost:8000"
    p = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run",
         str(FRONTEND / "streamlit_app.py"),
         "--server.port", "8501",
         "--server.address", "0.0.0.0",
         "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        env=env,
    )
    procs.append(p)
    return p

def wait_for_api(timeout=30):
    import urllib.request, urllib.error
    for _ in range(timeout):
        try:
            urllib.request.urlopen("http://localhost:8000/health", timeout=1)
            return True
        except Exception:
            time.sleep(1)
    return False

def shutdown(sig=None, frame=None):
    print(f"\n{yellow('Shutting down...')}")
    for p in procs:
        try: p.terminate()
        except Exception: pass
    time.sleep(1)
    for p in procs:
        try: p.kill()
        except Exception: pass
    print(green("✓ All services stopped."))
    sys.exit(0)

# ── Main ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print(bold(cyan("""
╔══════════════════════════════════════════════╗
║     🛰  Frontier AI Radar  — Starting...     ║
╚══════════════════════════════════════════════╝""")))

    print(f"\n{bold('Pre-flight checks...')}")
    check_env()
    check_deps()
    print(green("✓ Environment OK"))

    print(f"\n{bold('Starting API backend...')}")
    start_backend()

    print(f"{bold('Waiting for API to be ready...')}", end="", flush=True)
    if wait_for_api():
        print(f" {green('✓ Ready')}")
    else:
        print(f" {yellow('⚠  slow to start, continuing anyway')}")

    print(f"\n{bold('Starting Streamlit frontend...')}")
    start_frontend()
    time.sleep(2)

    print(f"""
{bold(green('✅ All services running!'))}

{bold('Access points:')}
  🖥  UI Dashboard     →  {cyan('http://localhost:8501')}
  📡  API (Swagger)    →  {cyan('http://localhost:8000/docs')}
  🗄  DB Explorer      →  {cyan('http://localhost:8000/admin/db')}
  📊  Metrics          →  {cyan('http://localhost:8000/metrics')}
  ❤   Health check     →  {cyan('http://localhost:8000/health')}

{bold('Quick actions:')}
  Trigger a run    →  POST http://localhost:8000/api/runs/trigger
  View findings    →  GET  http://localhost:8000/api/findings
  Download PDF     →  GET  http://localhost:8000/api/digest/{{run_id}}/pdf

{yellow('Press Ctrl+C to stop all services.')}
""")

    # Open browser after short delay
    def _open():
        time.sleep(2)
        webbrowser.open("http://localhost:8501")
        webbrowser.open("http://localhost:8000/docs")
    threading.Thread(target=_open, daemon=True).start()

    # Keep alive
    try:
        while True:
            for p in procs:
                if p.poll() is not None:
                    print(red(f"\n⚠  A service exited (code {p.returncode}). Shutting down."))
                    shutdown()
            time.sleep(3)
    except KeyboardInterrupt:
        shutdown()
