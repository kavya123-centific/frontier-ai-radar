"""
pipeline.py
------------------
Core intelligence pipeline.

ADDITIONS:
  1. Stale-run auto-recovery on startup:
     Any run stuck in 'running' state from a prior crash is automatically
     marked 'failed' before the new run starts. Eliminates the "perpetual 409"
     problem that appears in live server logs after restart.
  2. Entity trend tracking: compares entity mentions in current run vs prior run
     and stores delta as entity_trends JSON on the Run record.
  3. SOTA watch: compares impact_score of findings between runs to flag
     benchmark leaderboard movements.
  4. Per-category finding counts logged + stored on Run.
  5. Snapshot persist is now wrapped per-finding (never blocks on failure).

All features retained.
"""

import asyncio
import logging
import os
import time
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import yaml

from .database import SessionLocal
from .models import Finding, Run, Snapshot, Source
from .agents.competitor_agent import CompetitorAgent
from .agents.model_provider_agent import ModelProviderAgent
from .agents.research_agent import ResearchAgent
from .agents.hf_benchmark_agent import HFBenchmarkAgent
from .services.deduplicator import deduplicate_batch, assign_clusters
from .services.ranker import rank_findings
from .services.pdf_generator import generate_pdf
from .services.email_sender import send_digest_email

logger = logging.getLogger(__name__)

AGENT_TIMEOUT    = 120
STALE_RUN_CUTOFF = 30   # Minutes: runs older than this that are still 'running' are stale


# ── Config ─────────────────────────────────────────────────────────────────

def load_config() -> Dict:
    config_path = os.getenv("CONFIG_PATH", "config.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)


# ── Stale run recovery (v4.1 NEW) ──────────────────────────────────────────

def recover_stale_runs(db) -> int:
    """
    Auto-recover runs stuck in 'running' state after a server crash/restart.
    A run is considered stale if started_at is older than STALE_RUN_CUTOFF minutes.

    This directly fixes the perpetual 409 seen in live server logs:
      POST /api/runs/trigger HTTP/1.1 409 Conflict (repeated)

    Returns number of runs recovered.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=STALE_RUN_CUTOFF)
    stale_runs = (
        db.query(Run)
        .filter(Run.status == "running", Run.started_at < cutoff)
        .all()
    )
    if not stale_runs:
        return 0

    for run in stale_runs:
        run.status      = "failed"
        run.finished_at = datetime.utcnow()
        run.error_log   = (
            f"Auto-recovered: run was stuck in 'running' state since "
            f"{run.started_at}. Likely caused by server restart or crash."
        )
        logger.warning(
            f"Stale run recovered: {run.run_id[:8]} "
            f"(started {run.started_at}, {STALE_RUN_CUTOFF}min cutoff)"
        )

    db.commit()
    logger.info(f"Recovered {len(stale_runs)} stale run(s)")
    return len(stale_runs)


def is_run_in_progress(db) -> bool:
    return db.query(Run).filter(Run.status == "running").first() is not None


# ── Source seeding ─────────────────────────────────────────────────────────

def seed_sources_from_config(db, config: Dict) -> None:
    """
    Idempotent source seeding — safe to call on every run.

    FIX v4.2: Each URL is committed individually with try/except + rollback.
    Prevents a single duplicate URL from rolling back the entire session and
    crashing the pipeline with PendingRollbackError.
    Also deduplicates within the config itself (same URL in competitors + providers).
    """
    seeded  = 0
    skipped = 0
    seen_urls: set = set()  # deduplicate within config

    def _try_add(name: str, url: str, agent_type: str) -> None:
        nonlocal seeded, skipped
        url = url.strip()
        if not url or url in seen_urls:
            return
        seen_urls.add(url)
        if db.query(Source).filter_by(url=url).first():
            skipped += 1
            return
        try:
            db.add(Source(name=name, url=url, agent_type=agent_type))
            db.flush()   # detect constraint violation NOW, not at commit
            seeded += 1
        except Exception:
            db.rollback()
            logger.debug(f"Source already exists (skipped): {url}")
            skipped += 1

    for comp in config.get("agents", {}).get("competitors", []):
        for url in comp.get("release_urls", []):
            _try_add(comp["name"], url, "competitors")

    for mp in config.get("agents", {}).get("model_providers", []):
        for url in mp.get("urls", []):
            _try_add(mp["name"], url, "model_providers")

    for url in config.get("agents", {}).get("hf_benchmarks", {}).get("leaderboards", []):
        _try_add("HuggingFace", url, "hf_benchmarks")

    try:
        db.commit()
    except Exception:
        db.rollback()

    if seeded:
        logger.info(f"Seeded {seeded} new sources from config.yaml ({skipped} already existed)")
    else:
        logger.debug(f"Source seeding: all {skipped} URLs already in DB")


def get_urls_for_agent(db, agent_type: str) -> List[str]:
    return [
        s.url for s in
        db.query(Source)
        .filter(Source.agent_type == agent_type, Source.is_active == 1)
        .all()
    ]


# ── Snapshot + source metadata ─────────────────────────────────────────────

def _try_persist_snapshot(db, finding: Dict, run_id: str) -> None:
    try:
        db.add(Snapshot(
            url          = finding.get("source_url", ""),
            run_id       = run_id,
            content_hash = finding.get("content_hash", ""),
            text_excerpt = finding.get("_raw_text_excerpt", ""),
            agent_type   = finding.get("category", ""),
        ))
    except Exception as e:
        logger.debug(f"Snapshot persist skipped: {e}")


def _try_update_source_meta(db, finding: Dict) -> None:
    try:
        src = db.query(Source).filter(Source.url == finding.get("source_url")).first()
        if src:
            src.last_seen_at = datetime.utcnow()
            src.last_hash    = finding.get("content_hash", "")
    except Exception as e:
        logger.debug(f"Source meta update skipped: {e}")


# ── Change detection ───────────────────────────────────────────────────────

def detect_changes(db, findings: List[Dict]) -> List[Dict]:
    result = []
    for f in findings:
        hash_   = f.get("content_hash", "")
        src_url = f.get("source_url", "")

        if hash_ and db.query(Finding).filter_by(content_hash=hash_).first():
            logger.debug(f"UNCHANGED: {f.get('title','')[:60]}")
            continue

        prev = (
            db.query(Finding)
            .filter(Finding.source_url == src_url)
            .order_by(Finding.created_at.desc())
            .first()
        )
        if prev:
            f["change_status"] = "updated"
            f["previous_hash"] = prev.content_hash
            logger.info(f"UPDATED: {f.get('title','')[:60]}")
        else:
            f["change_status"] = "new"
            f["previous_hash"] = None
            logger.info(f"NEW: {f.get('title','')[:60]}")

        result.append(f)
    return result


# ── Entity trend analysis (v4.1 NEW) ───────────────────────────────────────

def compute_entity_trends(db, current_findings: List[Dict], run_id: str) -> Dict:
    """
    Compare entity mentions in the current run vs. the previous run.
    Returns dict: {entity: {"current": N, "previous": M, "delta": N-M, "trend": "up"/"down"/"new"}}

    This powers the 'Entity Heatmap' and 'SOTA Watch' judging checkpoint.
    """
    # Current run entities
    current_counts: Counter = Counter()
    for f in current_findings:
        for e in (f.get("entities") or []):
            current_counts[e.lower()] += 1

    # Previous run entities (most recent completed run before this one)
    prev_run = (
        db.query(Run)
        .filter(Run.status == "completed", Run.run_id != run_id)
        .order_by(Run.started_at.desc())
        .first()
    )

    prev_counts: Counter = Counter()
    if prev_run:
        prev_findings = db.query(Finding).filter(Finding.run_id == prev_run.run_id).all()
        for f in prev_findings:
            for e in (f.entities or []):
                prev_counts[e.lower()] += 1

    # Compute delta
    all_entities = set(current_counts.keys()) | set(prev_counts.keys())
    trends = {}
    for entity in all_entities:
        curr = current_counts.get(entity, 0)
        prev = prev_counts.get(entity, 0)
        delta = curr - prev
        if prev == 0 and curr > 0:
            trend = "new"
        elif delta > 0:
            trend = "up"
        elif delta < 0:
            trend = "down"
        else:
            trend = "stable"
        if curr > 0:   # Only include entities present in current run
            trends[entity] = {"current": curr, "previous": prev, "delta": delta, "trend": trend}

    # Return top 30 by current count
    top = dict(sorted(trends.items(), key=lambda x: x[1]["current"], reverse=True)[:30])
    return top


# ── SOTA watch (v4.1 NEW) ──────────────────────────────────────────────────

def compute_sota_watch(db, current_findings: List[Dict]) -> List[Dict]:
    """
    Identify benchmark leaderboard movements by comparing current run's
    high-impact benchmark findings vs prior runs on same source URL.

    Returns list of {title, source_url, current_score, previous_score, movement}
    for benchmark-category findings where impact_score changed.
    """
    sota_events = []
    benchmark_findings = [
        f for f in current_findings
        if f.get("category") == "hf_benchmarks" or "benchmark" in f.get("topic_cluster", "")
    ]

    for f in benchmark_findings:
        src_url = f.get("source_url", "")
        if not src_url:
            continue

        prev = (
            db.query(Finding)
            .filter(Finding.source_url == src_url)
            .order_by(Finding.created_at.desc())
            .first()
        )
        if prev and prev.impact_score is not None:
            curr_score = f.get("impact_score", 0)
            prev_score = prev.impact_score
            delta      = curr_score - prev_score
            if abs(delta) >= 1.0:   # Only report significant movements
                sota_events.append({
                    "title":          f.get("title", ""),
                    "source_url":     src_url,
                    "current_score":  curr_score,
                    "previous_score": prev_score,
                    "delta":          round(delta, 1),
                    "movement":       "up" if delta > 0 else "down",
                })

    return sota_events


# ── Main pipeline ──────────────────────────────────────────────────────────

async def run_pipeline() -> str:
    db     = SessionLocal()
    run_id = str(uuid.uuid4())

    # v4.1: Auto-recover stale runs before guard check
    recovered = recover_stale_runs(db)
    if recovered:
        logger.info(f"Auto-recovered {recovered} stale run(s) before starting new run")

    if is_run_in_progress(db):
        db.close()
        logger.warning("Pipeline already running — new run rejected (409)")
        raise RuntimeError("ALREADY_RUNNING")

    run = Run(run_id=run_id, status="running")
    db.add(run)
    db.commit()
    logger.info(f"Pipeline started: run_id={run_id[:8]}")

    start_time = datetime.utcnow()

    try:
        config       = load_config()
        global_cfg   = config.get("global", {})
        research_cfg = config.get("agents", {}).get("research", {})

        seed_sources_from_config(db, config)

        competitor_urls = get_urls_for_agent(db, "competitors")
        provider_urls   = get_urls_for_agent(db, "model_providers")
        hf_urls         = get_urls_for_agent(db, "hf_benchmarks")

        agents = [
            CompetitorAgent("Competitors",   competitor_urls, global_cfg),
            ModelProviderAgent("Providers",  provider_urls,   global_cfg),
            ResearchAgent("Research",        [],              research_cfg),
            HFBenchmarkAgent("HFBenchmarks", hf_urls,         global_cfg),
        ]

        logger.info(
            f"Launching {len(agents)} agents in parallel "
            f"(competitor:{len(competitor_urls)}, providers:{len(provider_urls)}, "
            f"hf:{len(hf_urls)} URLs)"
        )

        agent_start_times: Dict[str, float] = {}

        async def run_with_timeout(agent):
            agent_start_times[agent.name] = time.monotonic()
            try:
                return await asyncio.wait_for(agent.run(run_id), timeout=AGENT_TIMEOUT)
            except asyncio.TimeoutError:
                logger.error(f"Agent {agent.name} timed out after {AGENT_TIMEOUT}s")
                return []

        results = await asyncio.gather(
            *[run_with_timeout(a) for a in agents],
            return_exceptions=True,
        )

        elapsed_agents = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"All agents completed in {elapsed_agents:.1f}s")

        all_findings: List[Dict[str, Any]] = []
        agent_status_map: Dict = {}

        for agent, result in zip(agents, results):
            agent_elapsed = round(time.monotonic() - agent_start_times.get(agent.name, 0), 1)
            if isinstance(result, Exception):
                logger.error(f"Agent {agent.name}: {type(result).__name__}: {result}")
                agent_status_map[agent.name] = {"found": 0, "status": "error", "elapsed_sec": agent_elapsed}
            elif isinstance(result, list):
                logger.info(f"  {agent.name}: {len(result)} findings in {agent_elapsed}s")
                all_findings.extend(result)
                agent_status_map[agent.name] = {"found": len(result), "status": "ok", "elapsed_sec": agent_elapsed}
            else:
                agent_status_map[agent.name] = {"found": 0, "status": "timeout", "elapsed_sec": agent_elapsed}

        logger.info(f"Total raw findings: {len(all_findings)}")

        # ── Three-layer dedup + change detection + clustering ──────────────
        unique       = deduplicate_batch(all_findings)
        new_findings = detect_changes(db, unique)
        assign_clusters(new_findings)

        logger.info(
            f"Pipeline: {len(all_findings)} raw → {len(unique)} deduped → "
            f"{len(new_findings)} new/updated"
        )

        # ── Analytics (v4.1) ───────────────────────────────────────────────
        entity_trends = compute_entity_trends(db, new_findings, run_id)
        sota_watch    = compute_sota_watch(db, new_findings)

        if sota_watch:
            logger.info(f"SOTA Watch: {len(sota_watch)} benchmark movements detected")

        # ── Rank ───────────────────────────────────────────────────────────
        ranked = rank_findings(new_findings)

        # ── Persist ────────────────────────────────────────────────────────
        inserted = 0
        findings_by_cat: Counter = Counter()

        for f in ranked:
            try:
                db.add(Finding(
                    title            = f.get("title", "")[:500],
                    summary          = f.get("summary", ""),
                    why_matters      = f.get("why_matters", ""),
                    source_url       = f.get("source_url", ""),
                    publisher        = f.get("publisher", ""),
                    category         = f.get("category", ""),
                    content_hash     = f.get("content_hash", ""),
                    impact_score     = f.get("impact_score", 0),
                    novelty_score    = f.get("novelty_score", 0),
                    final_score      = f.get("final_score", 0),
                    tags             = f.get("tags", []),
                    entities         = f.get("entities", []),
                    run_id           = run_id,
                    confidence_score = f.get("confidence_score", 0.8),
                    evidence         = f.get("evidence", ""),
                    change_status    = f.get("change_status", "new"),
                    previous_hash    = f.get("previous_hash"),
                    topic_cluster    = f.get("topic_cluster", "general"),
                ))
                _try_persist_snapshot(db, f, run_id)
                _try_update_source_meta(db, f)
                inserted += 1
                findings_by_cat[f.get("category", "other")] += 1
            except Exception as e:
                logger.warning(f"Failed to insert finding: {e}")

        db.commit()
        logger.info(f"Persisted {inserted} findings")

        # ── PDF ────────────────────────────────────────────────────────────
        os.makedirs("digests", exist_ok=True)
        pdf_path = f"digests/digest_{run_id[:8]}.pdf"
        generate_pdf(ranked, pdf_path)

        # ── Email ──────────────────────────────────────────────────────────
        # FR6: Recipients from DB (UI-managed) take priority over config.yaml
        from .models import EmailRecipient as _ER
        db_recipients = [
            r.email for r in db.query(_ER).filter(_ER.is_active == 1).all()
        ]
        # Fallback to config.yaml if DB has none
        config_recipients = global_cfg.get("email_recipients", [])
        recipients = db_recipients if db_recipients else config_recipients
        # Seed config.yaml recipients into DB on first run
        if config_recipients and not db_recipients:
            for email in config_recipients:
                exists = db.query(_ER).filter_by(email=email).first()
                if not exists:
                    db.add(_ER(email=email, name="From config.yaml", note="Auto-seeded"))
            try:
                db.commit()
                logger.info(f"Seeded {len(config_recipients)} recipients from config.yaml into DB")
            except Exception:
                db.rollback()
        if recipients:
            send_digest_email(pdf_path, ranked[:5], recipients)
            logger.info(f"Email sent to {len(recipients)} recipient(s): {recipients}")
        else:
            logger.info("No email recipients configured — skipped")

        # ── Finalise run record ────────────────────────────────────────────
        total_elapsed = (datetime.utcnow() - start_time).total_seconds()
        run.status               = "completed"
        run.finished_at          = datetime.utcnow()
        run.pdf_path             = pdf_path
        run.total_found          = inserted
        run.elapsed_sec          = round(total_elapsed, 1)
        run.agent_status         = agent_status_map
        run.findings_by_category = dict(findings_by_cat)
        # Store analytics for UI use
        run.entity_trends        = entity_trends
        run.sota_watch           = sota_watch
        db.commit()

        logger.info(
            f"✅ Run {run_id[:8]} completed | {inserted} findings | "
            f"{total_elapsed:.1f}s | cats: {dict(findings_by_cat)}"
        )
        return run_id

    except RuntimeError:
        raise

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {type(e).__name__}: {e}", exc_info=True)
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        run.status      = "failed"
        run.error_log   = f"{type(e).__name__}: {str(e)}"
        run.finished_at = datetime.utcnow()
        run.elapsed_sec = round(elapsed, 1)
        db.commit()
        return run_id

    finally:
        db.close()
        logger.debug(f"DB session closed for run {run_id[:8]}")
