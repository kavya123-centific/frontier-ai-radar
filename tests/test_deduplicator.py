"""
test_deduplicator.py 
----------------------------
Tests for all three deduplication layers.

additions:
  - Layer 3 semantic dedup tests (_is_semantic_duplicate)
  - Entity overlap threshold tests
  - Keyword overlap threshold tests

Run: pytest tests/test_deduplicator.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app.services.deduplicator import (
    title_similarity,
    deduplicate_batch,
    _is_semantic_duplicate,
    _entity_set,
    _keyword_set,
    assign_topic_cluster,
    TITLE_SIMILARITY_THRESHOLD,
)


class TestTitleSimilarity:

    def test_identical_returns_one(self):
        assert title_similarity("Claude 3 Released", "Claude 3 Released") == 1.0

    def test_empty_strings(self):
        assert title_similarity("", "") == 1.0

    def test_completely_different(self):
        assert title_similarity("GPT-4 pricing update", "ArXiv paper on RLHF") < 0.4

    def test_case_insensitive(self):
        assert title_similarity("CLAUDE 3 RELEASED", "claude 3 released") == 1.0

    def test_near_duplicate_above_threshold(self):
        sim = title_similarity(
            "Claude 3 Haiku is now available via API",
            "Claude 3 Haiku now available via API",
        )
        assert sim >= TITLE_SIMILARITY_THRESHOLD

    def test_different_models_not_duplicates(self):
        assert title_similarity("GPT-4 Turbo pricing", "GPT-3.5 Turbo pricing") < TITLE_SIMILARITY_THRESHOLD


class TestSemanticDedup:
    """v4.1: Layer 3 — entity + keyword overlap."""

    def _make(self, title, summary="", entities=None):
        return {"title": title, "summary": summary, "entities": entities or []}

    def test_shared_entities_and_keywords_flagged(self):
        a = self._make(
            "OpenAI launches GPT-5 with new reasoning",
            "The new model features chain-of-thought capabilities",
            entities=["OpenAI", "GPT-5"],
        )
        b = self._make(
            "GPT-5 is available from OpenAI today",
            "OpenAI announces the release of their latest model",
            entities=["OpenAI", "GPT-5"],
        )
        assert _is_semantic_duplicate(a, b)

    def test_different_entities_not_flagged(self):
        a = self._make("Anthropic Claude update", "New safety features", entities=["Anthropic","Claude"])
        b = self._make("Google Gemini launch", "New multimodal model from Google", entities=["Google","Gemini"])
        assert not _is_semantic_duplicate(a, b)

    def test_no_entities_not_flagged(self):
        a = self._make("Some announcement", "An update was released")
        b = self._make("Another announcement", "Another update was released")
        # No entities → entity overlap is 0 → not flagged
        assert not _is_semantic_duplicate(a, b)

    def test_entity_overlap_below_threshold_not_flagged(self):
        # Only 1 shared entity (below ENTITY_OVERLAP_MIN=2)
        a = self._make("OpenAI API update", "The API changed", entities=["OpenAI"])
        b = self._make("Anthropic API update", "The API changed", entities=["OpenAI"])
        # 1 shared entity, not enough
        assert not _is_semantic_duplicate(a, b)


class TestDeduplicateBatch:

    def _f(self, title, hash_=None, entities=None, summary=""):
        return {
            "title": title,
            "content_hash": hash_ or hash(title),
            "entities": entities or [],
            "summary": summary,
        }

    def test_empty_list(self):
        assert deduplicate_batch([]) == []

    def test_single_finding_unchanged(self):
        assert len(deduplicate_batch([self._f("OpenAI GPT-5")])) == 1

    def test_exact_hash_duplicate_removed(self):
        findings = [self._f("Same", "hash_abc"), self._f("Same", "hash_abc")]
        assert len(deduplicate_batch(findings)) == 1

    def test_title_near_duplicate_removed(self):
        findings = [
            self._f("Claude 3.5 Haiku available via API", "h1"),
            self._f("Claude 3.5 Haiku now available via Anthropic API", "h2"),
        ]
        assert len(deduplicate_batch(findings)) == 1

    def test_semantic_duplicate_removed(self):
        """v4.1 Layer 3: same entities + similar keywords."""
        findings = [
            {
                "title": "OpenAI launches GPT-5 today",
                "content_hash": "h_a",
                "entities": ["OpenAI", "GPT-5"],
                "summary": "The model features advanced reasoning capabilities",
            },
            {
                "title": "GPT-5 now available from OpenAI",
                "content_hash": "h_b",
                "entities": ["OpenAI", "GPT-5"],
                "summary": "OpenAI releases their latest model with reasoning features",
            },
        ]
        result = deduplicate_batch(findings)
        assert len(result) == 1

    def test_distinct_findings_all_kept(self):
        findings = [
            self._f("OpenAI GPT-5 pricing", "h1", ["OpenAI","GPT-5"]),
            self._f("Google Gemini benchmark results", "h2", ["Google","Gemini"]),
            self._f("ArXiv safety alignment paper", "h3", ["ArXiv"]),
            self._f("HuggingFace leaderboard SOTA", "h4", ["HuggingFace"]),
        ]
        assert len(deduplicate_batch(findings)) == 4

    def test_preserves_first_occurrence(self):
        findings = [
            self._f("Title A original", "h1"),
            self._f("Title A copy", "h2"),
        ]
        result = deduplicate_batch(findings)
        assert result[0]["content_hash"] == "h1"


class TestTopicClustering:

    def test_benchmark_finding_clustered(self):
        f = {"title": "New SOTA on MMLU benchmark", "summary": "Eval results show accuracy improvement", "tags": ["benchmark"], "why_matters": ""}
        assert assign_topic_cluster(f) == "benchmarks & evals"

    def test_model_release_clustered(self):
        f = {"title": "GPT-5 launch available now", "summary": "Model release with new weights", "tags": ["release","model"], "why_matters": ""}
        assert assign_topic_cluster(f) == "model releases"

    def test_safety_finding_clustered(self):
        f = {"title": "Safety alignment research", "summary": "RLHF and red team evaluation", "tags": ["safety","alignment"], "why_matters": ""}
        assert assign_topic_cluster(f) == "safety & alignment"

    def test_unknown_defaults_to_general(self):
        f = {"title": "Something unrelated", "summary": "Content without keywords", "tags": [], "why_matters": ""}
        assert assign_topic_cluster(f) == "general"
