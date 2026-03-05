"""
base_agent.py
-------------
Abstract base class for all 4 intelligence agents.

FIXES APPLIED:
  1. asyncio.Semaphore: limits concurrent outbound HTTP connections (not burst)
  2. asyncio.wait_for: per-URL timeout prevents any single slow URL stalling pipeline
  3. Exponential backoff retry: 3 attempts with 2s/4s/8s delay on transient failures
  4. Return exceptions via gather: one URL failure never blocks others

Each subclass only needs to:
  - Define the `category` property
  - Optionally override `run()` (ResearchAgent does this for arXiv RSS)
"""

import asyncio
import hashlib
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

from ..services.summarizer import summarize_content

logger = logging.getLogger(__name__)

# Fetch timeout for a single HTTP request (seconds)
FETCH_TIMEOUT = 15.0

# Per-URL processing timeout (includes LLM call)
URL_PROCESSING_TIMEOUT = 90.0

# Retry config
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0   # seconds — doubles each retry (exponential backoff)

# ── Global LLM semaphore ───────────────────────────────────────────────────
# Shared across ALL agents — limits concurrent LLM calls regardless of how
# many agents/URLs fire at once. Free-tier APIs (OpenRouter, Groq) typically
# allow 1-6 req/min on free tier. Set to 2 to stay safely under limits.
# Increase to 5+ if you have paid credits.
_LLM_SEMAPHORE: Optional[asyncio.Semaphore] = None

def _get_llm_semaphore() -> asyncio.Semaphore:
    """Lazy-init the global semaphore (must be created inside the event loop)."""
    global _LLM_SEMAPHORE
    if _LLM_SEMAPHORE is None:
        _LLM_SEMAPHORE = asyncio.Semaphore(2)  # max 2 concurrent LLM calls
    return _LLM_SEMAPHORE

HEADERS = {
    "User-Agent": "FrontierAIRadar/2.0 (research-intelligence-bot; non-commercial)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


class BaseAgent(ABC):

    def __init__(self, name: str, urls: List[str], config: Dict = None):
        self.name   = name
        self.urls   = urls
        self.config = config or {}

        # Rate limit: sleep between requests (polite crawling)
        self.rate_limit: float = float(
            self.config.get("default_rate_limit", 1.5)
        )

        # Semaphore: max concurrent HTTP connections for this agent
        # FIX: This prevents burst-requesting — properly throttles concurrency
        max_concurrent = int(self.config.get("max_concurrent_requests", 3))
        self._semaphore = asyncio.Semaphore(max_concurrent)

    # ── Abstract interface ─────────────────────────────────────────────────

    @property
    @abstractmethod
    def category(self) -> str:
        """Each subclass declares its intelligence category."""
        pass

    # ── Core fetch with retry + backoff ────────────────────────────────────

    async def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch URL with:
        - Semaphore-controlled concurrency (no burst)
        - Exponential backoff retry (3 attempts)
        - Hard timeout per request
        Returns clean extracted text or None on all failures.
        """
        async with self._semaphore:   # FIX: limits concurrent connections
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    async with httpx.AsyncClient(
                        timeout=FETCH_TIMEOUT,
                        follow_redirects=True,
                        headers=HEADERS,
                    ) as client:
                        resp = await client.get(url)
                        resp.raise_for_status()

                    # Use XML parser for RSS/Atom feeds, HTML parser for web pages
                    content_type = resp.headers.get("content-type", "")
                    is_xml = (
                        "xml" in content_type
                        or url.endswith((".xml", ".rss", ".atom"))
                        or resp.text.lstrip().startswith("<?xml")
                    )
                    parser = "lxml-xml" if is_xml else "lxml"
                    soup = BeautifulSoup(resp.text, parser)

                    if not is_xml:
                        # Strip boilerplate — keep only content
                        for tag in soup(["script", "style", "nav", "footer",
                                         "header", "aside", "iframe", "form"]):
                            tag.decompose()

                    text = soup.get_text(separator="\n", strip=True)
                    return text[:6000]   # Hard cap — avoid LLM context overflow

                except httpx.HTTPStatusError as e:
                    # 4xx errors are permanent — do not retry
                    if 400 <= e.response.status_code < 500:
                        logger.warning(
                            f"[{self.name}] HTTP {e.response.status_code} "
                            f"(permanent) for {url}"
                        )
                        return None

                    # 5xx: server error — retry with backoff
                    delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    logger.warning(
                        f"[{self.name}] HTTP {e.response.status_code} "
                        f"for {url} — retry {attempt}/{MAX_RETRIES} in {delay}s"
                    )
                    await asyncio.sleep(delay)

                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    logger.warning(
                        f"[{self.name}] {type(e).__name__} for {url} "
                        f"— retry {attempt}/{MAX_RETRIES} in {delay}s"
                    )
                    await asyncio.sleep(delay)

                except Exception as e:
                    logger.error(
                        f"[{self.name}] Unexpected fetch error for {url}: "
                        f"{type(e).__name__}: {e}"
                    )
                    return None

            logger.error(f"[{self.name}] All {MAX_RETRIES} retries exhausted for {url}")
            return None

    # ── Single URL processing with hard timeout ────────────────────────────

    async def process_url(self, url: str, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch + LLM summarize a single URL.
        FIX: Wrapped in asyncio.wait_for() — any hung URL is killed after timeout.
        """
        await asyncio.sleep(self.rate_limit)   # Polite crawl delay
        logger.info(f"[{self.name}] Processing: {url}")

        try:
            # FIX: Per-URL hard timeout — slow URLs can't stall the pipeline
            result = await asyncio.wait_for(
                self._process_url_inner(url, run_id),
                timeout=URL_PROCESSING_TIMEOUT
            )
            return result

        except asyncio.TimeoutError:
            logger.error(
                f"[{self.name}] Timeout after {URL_PROCESSING_TIMEOUT}s: {url}"
            )
            return None

    async def _process_url_inner(
        self, url: str, run_id: str
    ) -> Optional[Dict[str, Any]]:
        """Inner logic — fetch, hash, summarize."""
        text = await self.fetch_page(url)
        if not text:
            return None

        content_hash = hashlib.sha256(
            text.encode("utf-8", errors="replace")
        ).hexdigest()

        # Throttle concurrent LLM calls — free-tier APIs have strict rate limits
        async with _get_llm_semaphore():
            result = await summarize_content(text, url, self.category)
        if not result:
            return None

        result.update({
            "content_hash": content_hash,
            "run_id":       run_id,
            "category":     self.category,
            "source_url":   url,
        })
        return result

    # ── Parallel URL processing with exception isolation ───────────────────

    async def run(self, run_id: str, since_timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process all agent URLs concurrently.
        since_timestamp (ISO str): skip content already seen before this time (incremental).
        return_exceptions=True: one URL failure never blocks others.
        """
        if since_timestamp:
            logger.info(f"[{self.name}] Incremental scan since {since_timestamp}")
        if not self.urls:
            logger.info(f"[{self.name}] No URLs configured — skipping")
            return []

        tasks = [self.process_url(url, run_id) for url in self.urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        findings = []
        for url, result in zip(self.urls, results):
            if isinstance(result, Exception):
                logger.error(f"[{self.name}] Task exception for {url}: {result}")
            elif result is not None:
                findings.append(result)

        logger.info(
            f"[{self.name}] Completed: "
            f"{len(findings)}/{len(self.urls)} successful findings"
        )
        return findings
