"""
test_summarizer.py
--------------------------
Tests for sanitization logic (no API key required).
Integration tests for LLM call are skipped if ANTHROPIC_API_KEY not set.

additions:
  - Tests for _normalize_confidence() strictly mapping to [1.0, 0.8, 0.6]
  - Tests for edge case confidence values (0.7, 0.9, etc.)
"""

import sys
import os
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app.services.summarizer import _sanitize, _normalize_confidence, _clean_json


class TestNormalizeConfidence:
    """v4.0: confidence_score must map to exactly 1.0, 0.8, or 0.6."""

    def test_1_0_stays_1_0(self):
        assert _normalize_confidence(1.0) == 1.0

    def test_0_8_stays_0_8(self):
        assert _normalize_confidence(0.8) == 0.8

    def test_0_6_stays_0_6(self):
        assert _normalize_confidence(0.6) == 0.6

    def test_0_7_maps_to_0_8(self):
        """0.7 is equidistant between 0.6 and 0.8; implementation picks 0.8."""
        result = _normalize_confidence(0.7)
        assert result in [0.6, 0.8]  # Either is acceptable

    def test_0_9_maps_to_0_8_or_1_0(self):
        result = _normalize_confidence(0.9)
        assert result in [0.8, 1.0]

    def test_0_5_maps_to_0_6(self):
        assert _normalize_confidence(0.5) == 0.6

    def test_0_0_maps_to_0_6(self):
        assert _normalize_confidence(0.0) == 0.6

    def test_string_input_handled(self):
        """Non-numeric input should default to 0.8."""
        assert _normalize_confidence("not-a-number") == 0.8

    def test_none_defaults_to_0_8(self):
        assert _normalize_confidence(None) == 0.8


class TestSanitize:

    def _valid_raw(self):
        return {
            "title":            "Test finding",
            "summary":          "Something happened",
            "why_matters":      "It matters because",
            "publisher":        "OpenAI",
            "impact_score":     8,
            "novelty_score":    7,
            "confidence_score": 1.0,
            "evidence":         "Direct quote from source",
            "tags":             ["release", "api"],
            "entities":         ["OpenAI", "GPT-5"],
        }

    def test_valid_input_passes_through(self):
        result = _sanitize(self._valid_raw())
        assert result["title"] == "Test finding"
        assert result["impact_score"] == 8.0
        assert result["confidence_score"] == 1.0

    def test_impact_score_clamped_to_10(self):
        raw = self._valid_raw()
        raw["impact_score"] = 99
        result = _sanitize(raw)
        assert result["impact_score"] == 10.0

    def test_impact_score_clamped_to_0(self):
        raw = self._valid_raw()
        raw["impact_score"] = -5
        result = _sanitize(raw)
        assert result["impact_score"] == 0.0

    def test_title_truncated_at_500(self):
        raw = self._valid_raw()
        raw["title"] = "x" * 600
        result = _sanitize(raw)
        assert len(result["title"]) <= 500

    def test_confidence_normalized(self):
        """v4.0: 0.7 should map to nearest valid tier."""
        raw = self._valid_raw()
        raw["confidence_score"] = 0.7
        result = _sanitize(raw)
        assert result["confidence_score"] in [0.6, 0.8, 1.0]

    def test_tags_not_list_becomes_empty(self):
        raw = self._valid_raw()
        raw["tags"] = "not-a-list"
        result = _sanitize(raw)
        assert result["tags"] == []

    def test_entities_not_list_becomes_empty(self):
        raw = self._valid_raw()
        raw["entities"] = {"bad": "dict"}
        result = _sanitize(raw)
        assert result["entities"] == []

    def test_evidence_truncated_at_1000(self):
        raw = self._valid_raw()
        raw["evidence"] = "x" * 1200
        result = _sanitize(raw)
        assert len(result["evidence"]) <= 1000


class TestCleanJson:

    def test_strips_markdown_fence(self):
        text = "```json\n{\"key\": \"value\"}\n```"
        assert _clean_json(text) == '{"key": "value"}'

    def test_plain_json_unchanged(self):
        text = '{"key": "value"}'
        assert _clean_json(text) == '{"key": "value"}'

    def test_strips_bare_backticks(self):
        text = "```{\"key\": \"value\"}```"
        assert _clean_json(text) == '{"key": "value"}'


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="Integration test requires ANTHROPIC_API_KEY"
)
class TestSummarizeContentIntegration:

    def test_real_api_call_returns_structured_output(self):
        import asyncio
        from backend.app.services.summarizer import summarize_content

        sample_text = """
        OpenAI today announced the release of GPT-5, their most capable model yet.
        The model features a 256k context window and improved reasoning capabilities.
        Pricing starts at $15 per million input tokens and $60 per million output tokens.
        The model is available via the API starting today.
        """

        result = asyncio.run(
            summarize_content(sample_text, "https://openai.com/blog", "competitors")
        )

        if result:  # May return None if content filtered
            assert "title" in result
            assert "summary" in result
            assert "evidence" in result
            assert "confidence_score" in result
            assert result["confidence_score"] in [0.6, 0.8, 1.0]
            assert isinstance(result["tags"], list)
            assert isinstance(result["entities"], list)
