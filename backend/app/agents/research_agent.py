"""
research_agent.py
-----------------
Agent #3 — Research Publication Scout

Overrides run() to build arXiv RSS feed URLs from configured categories
instead of using explicit URLs.

arXiv RSS format: https://rss.arxiv.org/rss/{category}
Categories: cs.CL (NLP), cs.AI (AI), cs.LG (ML)

Relevance scoring prioritizes:
- New benchmarks / evaluation methodology
- Safety, alignment, red-teaming
- Agentic workflows, tool use, memory
- Multimodal reasoning
- Data-centric techniques
"""

import asyncio
import logging
from typing import Any, Dict, List

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """
    Monitors arXiv RSS feeds for latest AI/ML research.
    Config provides arxiv_categories list — URLs are built dynamically.
    """

    @property
    def category(self) -> str:
        return "research"

    async def run(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Build arXiv RSS URLs from config.arxiv_categories,
        then process each feed concurrently (inherits semaphore + timeout).
        """
        categories = self.config.get("arxiv_categories", ["cs.CL", "cs.AI"])
        arxiv_urls = [
            f"https://rss.arxiv.org/rss/{cat}"
            for cat in categories
        ]

        logger.info(
            f"[ResearchAgent] Fetching {len(arxiv_urls)} arXiv feeds: "
            f"{categories}"
        )

        # Temporarily set urls so base gather logic works
        self.urls = arxiv_urls

        tasks = [self.process_url(url, run_id) for url in arxiv_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        findings = []
        for url, result in zip(arxiv_urls, results):
            if isinstance(result, Exception):
                logger.error(f"[ResearchAgent] Feed error for {url}: {result}")
            elif result is not None:
                findings.append(result)

        logger.info(f"[ResearchAgent] {len(findings)}/{len(arxiv_urls)} feeds yielded findings")
        return findings
