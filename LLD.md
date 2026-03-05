# Low-Level Design — Frontier AI Radar v3.0

## 1. All Issues Fixed (Audit Trail)

| Audit Finding | Severity | Fix Applied | File |
|---|---|---|---|
| `asyncio.sleep` ≠ concurrency control | Medium | `asyncio.Semaphore(max_concurrent)` | `base_agent.py` |
| No timeout on agent tasks | High | `asyncio.wait_for(agent.run(), timeout=120)` | `pipeline.py` |
| No retry on LLM rate limits | Medium | Exponential backoff, 3 attempts | `summarizer.py` |
| Concurrent runs corrupt SQLite | High | `is_run_in_progress()` → 409 | `main.py`, `pipeline.py` |
| Scheduler not implemented | High | APScheduler with cron trigger | `scheduler.py` |
| PDF broken when no findings | Low | Always generate (empty state template) | `pdf_generator.py` |
| Credibility: `"openai.com" in url` | High | `urlparse().netloc.endswith(trusted)` | `ranker.py` |
| DB session passed to background task | Critical | Pipeline creates own session | `pipeline.py` |
| Config vs DB source inconsistency | Medium | Seed + DB authoritative | `pipeline.py` |

---

## 2. Module Dependency Graph

```
main.py
  ├── pipeline.py
  │     ├── agents/base_agent.py
  │     │     ├── services/summarizer.py   (Claude API)
  │     │     └── httpx + BeautifulSoup
  │     ├── agents/competitor_agent.py     (extends base)
  │     ├── agents/model_provider_agent.py (extends base)
  │     ├── agents/research_agent.py       (overrides run())
  │     ├── agents/hf_benchmark_agent.py   (extends base)
  │     ├── services/deduplicator.py
  │     ├── services/ranker.py
  │     ├── services/pdf_generator.py      (Jinja2 + WeasyPrint)
  │     └── services/email_sender.py       (SMTP SSL)
  ├── scheduler.py                         (APScheduler)
  ├── database.py
  ├── models.py
  └── schemas.py
```

---

## 3. DB Session Lifecycle (Critical Fix)

**Problem (v1/v2):**
```
HTTP Request → get_db() yields session
  → background_tasks.add_task(run_pipeline, run_id, db)
  → Response returned → FastAPI closes session ← DANGER
  
Background Task (later):
  run_pipeline(run_id, db)
    db.query(...)  ← DetachedInstanceError! Session is closed!
```

**Fix (v3):**
```
HTTP Request → get_db() yields session
  → background_tasks.add_task(run_pipeline)  ← NO session
  → Response returned → session closed safely

Background Task:
  run_pipeline()
    db = SessionLocal()   ← fresh session, owned here
    try:
      ... all DB operations ...
    finally:
      db.close()          ← always closed, even on exception
```

---

## 4. Concurrency Model (3 Levels)

```
Level 1: Pipeline (macro)
  asyncio.gather(
    competitor_agent.run(run_id),    ← 4 agents in parallel
    provider_agent.run(run_id),
    research_agent.run(run_id),
    hf_agent.run(run_id),
  )

Level 2: Per-Agent (meso)
  asyncio.gather(
    process_url(url1),               ← N URLs in parallel
    process_url(url2),
    ...process_url(urlN),
  )

Level 3: HTTP (micro) — CONTROLLED
  async with asyncio.Semaphore(max_concurrent=3):
    await httpx.AsyncClient.get(url) ← max 3 concurrent per agent
```

**Rate limiting:**
- `asyncio.sleep(rate_limit)` before each URL = polite delay
- `asyncio.Semaphore(3)` = max 3 concurrent TCP connections per agent
- NOT burst-requesting (fixed from v2)

---

## 5. Fault Isolation Model

```
Pipeline exception handling:
  Agent failure    → returns [] → pipeline continues
  URL timeout      → asyncio.TimeoutError caught → skip URL
  LLM rate limit   → retry 3x with backoff → return None
  LLM JSON error   → retry 3x → return None
  Insert collision → skip (content_hash unique constraint)
  Email failure    → log and return False → never raises
  PDF failure      → log → run marked failed
```

No single URL or agent failure can abort the pipeline.

---

## 6. Deduplication Pipeline

```
Raw findings (N items)
     │
     ▼ deduplicate_batch()
     ├── Layer 1: content_hash in seen_hashes set
     │     O(1) lookup — exact page content match
     │
     └── Layer 2: title_similarity() >= 0.85
           SequenceMatcher — same announcement reworded
           O(M) per finding, M = accepted count
     │
     ▼ filter_already_seen()  [cross-run]
       DB query by content_hash
       Skips pages unchanged since last run
     │
     ▼ New findings (K ≤ M ≤ N)
```

---

## 7. Ranking Formula

```
final_score = 0.35 * impact
            + 0.25 * novelty
            + 0.20 * credibility
            + 0.20 * actionability

Components:
  impact      ∈ [0,10]  LLM-assigned, clamped
  novelty     ∈ [0,10]  LLM-assigned, clamped
  credibility = 10 if urlparse(url).netloc == trusted
                   or netloc.endswith(f".{trusted}")
              = 5  otherwise
  actionability = min(10, keyword_hits * 1.2)
                  keywords: api, pricing, benchmark, release, ...

Output: float ∈ [0, 10], rounded to 2 decimal places
```

---

## 8. Config ↔ DB Relationship

```
config.yaml (static seed)
     │
     ▼ seed_sources_from_config(db) — idempotent
       Inserts only if url not in DB (unique constraint)
     │
  sources table (DB) ← authoritative after seeding
     │                    ← new URLs via POST /api/sources
     ▼
  get_urls_for_agent(db, "competitors")
     │
  agent.urls list → fetch → summarize → findings
```

After first run, sources table is the single source of truth.
Config YAML is only consulted once per source per run (idempotent).

---

## 9. Scheduler Design

```
FastAPI Lifespan (startup):
  start_scheduler()
    APScheduler AsyncIOScheduler
    CronTrigger(hour=7, minute=0, timezone="Asia/Kolkata")
    misfire_grace_time=3600  ← catch up if server was down <1h

On trigger:
  _scheduled_run()
    await run_pipeline()
    ├── If ALREADY_RUNNING: log warning, skip
    └── Normal pipeline execution

FastAPI Lifespan (shutdown):
  stop_scheduler()
```

---

## 10. Data Flow Per URL

```
URL
 │
 ▼ asyncio.Semaphore (max 3 concurrent)
 │
 ▼ asyncio.wait_for(90s timeout)
 │
 ▼ httpx.AsyncClient.get() + retry(3x, backoff 2/4/8s)
 │
 ▼ BeautifulSoup (lxml parser)
   → strip [script, style, nav, footer, header, aside, iframe, form]
   → get_text()[:6000]
 │
 ▼ hashlib.sha256(text) → content_hash
 │
 ▼ Claude API (claude-sonnet-4-20250514)
   System: strict JSON-only
   + retry on 429/5xx (3x, backoff 2/4/8s)
 │
 ▼ json.loads() → _sanitize() → score clamping
 │
 ▼ finding dict {title, summary, why_matters, publisher,
                  impact_score, novelty_score, tags, entities,
                  content_hash, run_id, category, source_url}
```

---

## 11. Security Notes

| Area | Implementation | Gap |
|---|---|---|
| Secrets | `.env` file + `python-dotenv` | Not vault-backed |
| Auth | None | Suitable for hackathon only |
| CORS | Localhost only (`8501`) | Not production-hardened |
| Input validation | Pydantic schemas | SQL injection protected via ORM |
| Rate limiting | Semaphore per agent | No API-level rate limiting |
| robots.txt | Not implemented | Should add for production |

---

## 12. Hackathon vs Production Readiness

| Feature | Hackathon (v3) | Production Needs |
|---|---|---|
| DB | SQLite | PostgreSQL |
| Auth | None | OAuth2/JWT |
| Queue | BackgroundTasks | Celery + Redis |
| Scheduler | APScheduler in-process | Airflow/Dagster |
| Monitoring | Logs | Prometheus + Grafana |
| Dedup | SequenceMatcher | Vector similarity embeddings |
| Secrets | .env | HashiCorp Vault |
| Rate limiting | Per-agent semaphore | API gateway |
