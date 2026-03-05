#!/usr/bin/env python3
"""
fix_stuck_runs.py
-----------------
Quick fix for the "persistent 409 Conflict" problem.

Run this from the backend/ directory when POST /api/runs/trigger keeps
returning 409 after a server restart or crash.

Usage:
    cd backend
    python ../fix_stuck_runs.py

Or if running from the project root:
    python fix_stuck_runs.py
"""

import os
import sys
from datetime import datetime

# Try to find radar.db in common locations
db_paths = [
    "radar.db",
    "backend/radar.db",
    os.path.expanduser("~/radar.db"),
]

db_path = None
for p in db_paths:
    if os.path.exists(p):
        db_path = p
        break

if db_path is None:
    print("❌ Could not find radar.db")
    print("   Looked in:", db_paths)
    print("   Try: python fix_stuck_runs.py from the backend/ directory")
    sys.exit(1)

print(f"📂 Found database: {db_path}")

try:
    import sqlite3
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    # Find stuck runs
    cur.execute("SELECT run_id, started_at FROM runs WHERE status = 'running'")
    stuck = cur.fetchall()

    if not stuck:
        print("✅ No stuck runs found — database is already in a clean state.")
        print("   If you're still seeing 409, the run may be genuinely in progress.")
        conn.close()
        sys.exit(0)

    print(f"\n⚠️  Found {len(stuck)} stuck run(s):")
    for run_id, started_at in stuck:
        print(f"   run_id={run_id[:8]}... started_at={started_at}")

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        """
        UPDATE runs
        SET status = 'failed',
            finished_at = ?,
            error_log = 'Run interrupted by server restart/crash. Manually recovered via fix_stuck_runs.py.'
        WHERE status = 'running'
        """,
        (now,)
    )
    conn.commit()
    conn.close()

    print(f"\n✅ Recovered {len(stuck)} stuck run(s) successfully!")
    print("   You can now trigger a new run.")
    print("   Restart uvicorn and click 🚀 Trigger Manual Run in the dashboard.")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
