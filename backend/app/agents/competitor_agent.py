"""
competitor_agent.py
-------------------
Agent #1 — Competitor Release Watcher

Tracks competitor product blogs, changelogs, and release notes.
Sources: OpenAI, Google DeepMind, Mistral, Meta AI, etc.

Inherits all concurrency + retry logic from BaseAgent.
Only defines its category label.
"""

from .base_agent import BaseAgent


class CompetitorAgent(BaseAgent):
    """
    Monitors competitor sites for:
    - Product launches and feature releases
    - API updates and deprecations
    - Pricing changes
    - Strategic announcements
    """

    @property
    def category(self) -> str:
        return "competitors"
