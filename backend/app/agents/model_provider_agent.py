"""
model_provider_agent.py
-----------------------
Agent #2 — Foundation Model Provider Release Watcher

Tracks foundation model providers for:
- Model releases (name, version, modalities, context length)
- API changes (new endpoints, deprecations, rate limits)
- Pricing changes
- Safety policy updates
- Benchmark claims (cross-references with Agent #4)

Sources: Anthropic, Cohere, Together AI, etc.
"""

from .base_agent import BaseAgent


class ModelProviderAgent(BaseAgent):
    """
    Monitors model provider release notes, blogs, and docs.
    """

    @property
    def category(self) -> str:
        return "model_providers"
