"""
test_ranker.py 
---------------------
Unit tests for ranker.py

additions:
  - Tests for confidence_score incorporation into credibility
  - Tests for updated change_status actionability bonus
  - Tests for expanded CREDIBLE_DOMAINS list

Run: pytest tests/test_ranker.py -v
No API key required — pure logic tests.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app.services.ranker import (
    credibility_score,
    actionability_score,
    compute_final_score,
    rank_findings,
    extract_domain,
)


class TestExtractDomain:

    def test_standard_url(self):
        assert extract_domain("https://openai.com/blog") == "openai.com"

    def test_subdomain_url(self):
        assert extract_domain("https://api.openai.com/v1") == "api.openai.com"

    def test_fake_openai_not_trusted(self):
        assert extract_domain("https://fake-openai.com") == "fake-openai.com"

    def test_port_stripped(self):
        assert extract_domain("http://localhost:8000") == "localhost"


class TestCredibilityScore:

    def test_official_openai_gets_max(self):
        f = {"source_url": "https://openai.com/blog/gpt-5", "confidence_score": 1.0}
        assert credibility_score(f) >= 10.0

    def test_fake_openai_does_not_get_credit(self):
        f = {"source_url": "https://fake-openai.com/post", "confidence_score": 0.8}
        score = credibility_score(f)
        assert score < 9.0   # Should NOT get trusted-domain score

    def test_arxiv_is_credible(self):
        f = {"source_url": "https://arxiv.org/abs/2401.12345", "confidence_score": 0.8}
        assert credibility_score(f) >= 9.0

    def test_subdomain_of_credible_domain(self):
        f = {"source_url": "https://research.anthropic.com/paper", "confidence_score": 1.0}
        assert credibility_score(f) >= 9.0

    def test_unknown_domain_mid_score(self):
        f = {"source_url": "https://someblog.example.com/post", "confidence_score": 0.6}
        score = credibility_score(f)
        assert 2.0 <= score <= 7.0

    def test_high_confidence_boosts_score(self):
        """v4.0: official (1.0) should score higher than blog (0.8) for same domain."""
        f_official = {"source_url": "https://openai.com/blog", "confidence_score": 1.0}
        f_blog     = {"source_url": "https://openai.com/blog", "confidence_score": 0.6}
        assert credibility_score(f_official) > credibility_score(f_blog)

    def test_nvidia_is_credible(self):
        """v4.0: nvidia.com added to CREDIBLE_DOMAINS."""
        f = {"source_url": "https://blogs.nvidia.com/blog/ai", "confidence_score": 0.8}
        assert credibility_score(f) >= 8.0


class TestActionabilityScore:

    def test_api_pricing_keywords_score_high(self):
        f = {
            "summary": "OpenAI released new API pricing with reduced cost per token",
            "why_matters": "Lower inference cost improves ROI for enterprise workloads",
            "change_status": "new",
        }
        score = actionability_score(f)
        assert score >= 3.0

    def test_vague_announcement_scores_low(self):
        f = {
            "summary": "A company announced something interesting",
            "why_matters": "This is notable",
            "change_status": "new",
        }
        score = actionability_score(f)
        assert score < 3.0

    def test_updated_finding_gets_bonus(self):
        """v4.0: 'updated' change_status adds +1.0 bonus."""
        f_new = {
            "summary": "API pricing update announced",
            "why_matters": "Cost change affects budgets",
            "change_status": "new",
        }
        f_updated = {**f_new, "change_status": "updated"}
        assert actionability_score(f_updated) > actionability_score(f_new)

    def test_score_capped_at_10(self):
        f = {
            "summary": "api pricing release update launch model benchmark eval accuracy performance cost tokens latency",
            "why_matters": "critical update available faster cheaper inference throughput",
            "change_status": "updated",
        }
        assert actionability_score(f) <= 10.0


class TestComputeFinalScore:

    def test_score_in_valid_range(self):
        f = {
            "impact_score": 8,
            "novelty_score": 7,
            "source_url": "https://openai.com/blog",
            "confidence_score": 1.0,
            "summary": "GPT-5 API release with new pricing",
            "why_matters": "major update for enterprise customers",
            "change_status": "new",
        }
        score = compute_final_score(f)
        assert 0.0 <= score <= 10.0

    def test_official_source_ranks_higher_than_unknown(self):
        f_official = {
            "impact_score": 7, "novelty_score": 7,
            "source_url": "https://anthropic.com/news",
            "confidence_score": 1.0,
            "summary": "API update with performance improvements",
            "why_matters": "faster inference",
            "change_status": "new",
        }
        f_unknown = {
            "impact_score": 7, "novelty_score": 7,
            "source_url": "https://random-blog.io/post",
            "confidence_score": 0.6,
            "summary": "API update with performance improvements",
            "why_matters": "faster inference",
            "change_status": "new",
        }
        assert compute_final_score(f_official) > compute_final_score(f_unknown)

    def test_high_impact_drives_score(self):
        f_high = {"impact_score": 10, "novelty_score": 10, "source_url": "https://openai.com", "confidence_score": 1.0, "summary": "major release", "why_matters": "big change", "change_status": "new"}
        f_low  = {"impact_score": 1,  "novelty_score": 1,  "source_url": "https://openai.com", "confidence_score": 0.6, "summary": "minor note",  "why_matters": "small change", "change_status": "new"}
        assert compute_final_score(f_high) > compute_final_score(f_low)


class TestRankFindings:

    def test_sorted_descending(self):
        findings = [
            {"impact_score": 3, "novelty_score": 3, "source_url": "https://a.com", "confidence_score": 0.6, "summary": "low", "why_matters": "low", "change_status": "new"},
            {"impact_score": 9, "novelty_score": 9, "source_url": "https://openai.com", "confidence_score": 1.0, "summary": "new api release benchmark", "why_matters": "major update cost", "change_status": "new"},
            {"impact_score": 6, "novelty_score": 6, "source_url": "https://arxiv.org", "confidence_score": 0.8, "summary": "paper eval benchmark", "why_matters": "research update", "change_status": "new"},
        ]
        ranked = rank_findings(findings)
        scores = [f["final_score"] for f in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_final_score_added_to_finding(self):
        findings = [{"impact_score": 5, "novelty_score": 5, "source_url": "https://openai.com", "confidence_score": 0.8, "summary": "test", "why_matters": "test", "change_status": "new"}]
        ranked = rank_findings(findings)
        assert "final_score" in ranked[0]

    def test_empty_list(self):
        assert rank_findings([]) == []
