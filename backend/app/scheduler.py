"""
scheduler.py
------------
Daily scheduled pipeline execution using APScheduler.

FIX: This was MISSING in all previous versions.
The spec says "daily multi-agent intelligence system" — but previous code
was manual-trigger only. This implements the actual daily schedule.

Integration:
  - Started on FastAPI app startup via lifespan
  - Stopped cleanly on app shutdown
  - Runs run_pipeline() as an async coroutine at configured time daily
  - Concurrent run guard in pipeline.py prevents scheduler + manual overlap

Configuration via config.yaml:
  global.run_time  : "07:00"  (24h format)
  global.timezone  : "Asia/Kolkata"
"""

import asyncio
from typing import Optional
import logging
import os

import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler = None


def load_schedule_config():
    """Load run_time and timezone from config.yaml."""
    config_path = os.getenv("CONFIG_PATH", "config.yaml")
    try:
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        global_cfg = cfg.get("global", {})
        run_time   = global_cfg.get("run_time", "07:00")
        timezone   = global_cfg.get("timezone", "UTC")
        hour, minute = map(int, run_time.split(":"))
        return hour, minute, timezone
    except Exception as e:
        logger.error(f"Failed to load schedule config: {e} — defaulting to 07:00 UTC")
        return 7, 0, "UTC"


async def _scheduled_run():
    """Wrapper called by APScheduler — imports pipeline here to avoid circular imports."""
    from .pipeline import run_pipeline
    logger.info("⏰ Scheduled daily run triggered")
    try:
        run_id = await run_pipeline()
        logger.info(f"⏰ Scheduled run completed: {run_id[:8]}")
    except RuntimeError as e:
        if "ALREADY_RUNNING" in str(e):
            logger.warning("⏰ Scheduled run skipped — pipeline already running")
        else:
            logger.error(f"⏰ Scheduled run failed: {e}")
    except Exception as e:
        logger.error(f"⏰ Scheduled run failed: {type(e).__name__}: {e}")


def start_scheduler():
    """
    Initialize and start APScheduler with daily cron trigger.
    Called on FastAPI app startup.
    """
    global _scheduler

    hour, minute, timezone = load_schedule_config()

    _scheduler = AsyncIOScheduler(timezone=timezone)
    _scheduler.add_job(
        _scheduled_run,
        trigger=CronTrigger(hour=hour, minute=minute, timezone=timezone),
        id="daily_radar_run",
        name="Daily Frontier AI Radar",
        replace_existing=True,
        misfire_grace_time=3600,   # 1 hour grace — catch up if server was down
    )
    _scheduler.start()

    logger.info(
        f"📅 Scheduler started — daily run at {hour:02d}:{minute:02d} {timezone}"
    )


def stop_scheduler():
    """Stop the scheduler cleanly on app shutdown."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("📅 Scheduler stopped")


def get_next_run_time():
    """Return the next scheduled run time as ISO string (for API/UI display)."""
    if _scheduler and _scheduler.running:
        job = _scheduler.get_job("daily_radar_run")
        if job and job.next_run_time:
            return job.next_run_time.isoformat()
    return None
