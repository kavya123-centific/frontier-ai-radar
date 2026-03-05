"""
ranker.py 
-----------------
Ranking formula from spec:
  final_score = 0.35*impact + 0.25*novelty + 0.20*credibility + 0.20*actionability

v4.0 CHANGES:
  - confidence_score from LLM now ALSO incorporated into credibility component
    (official announcement = 1.0 → boosts credibility beyond domain alone)
  - actionability_score gets extra weight for 'updated' change_status findings
    (changed content is inherently more actionable than static content)
  - Domain list expanded with more credible AI sources
"""

import logging
from typing import Any, Dict, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

CREDIBLE_DOMAINS = frozenset({
    "openai.com",
    "anthropic.com",
    "deepmind.google",
    "google.com",
    "arxiv.org",
    "huggingface.co",
    "mistral.ai",
    "cohere.com",
    "stability.ai",
    "meta.com",
    "microsoft.com",
    "research.google",
    "blogs.microsoft.com",
    "ai.google",
    "together.ai",
    "x.ai",
    "nvidia.com",
    "intel.com",
    "aws.amazon.com",
    "cloud.google.com",
    "azure.microsoft.com",
})

ACTIONABLE_KEYWORDS = [
    "api", "pricing", "price", "benchmark", "release", "launch",
    "latency", "context window", "tokens", "safety", "performance",
    "available", "deprecat", "update", "model", "cost", "speed",
    "fine-tun", "inference", "throughput", "accuracy", "eval",
    "breaking", "critical", "new", "improved", "faster", "cheaper",
]


def extract_domain(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc.split(":")[0]
    except Exception:
        return ""


def credibility_score(finding: Dict[str, Any]) -> float:
    """
    v4.0: Combines domain credibility with LLM-assigned confidence_score.
    Domain check: 10.0 if trusted, 5.0 otherwise.
    Confidence modifier: +0.5 if official source (1.0), -0.5 if third-party (0.6)
    Result clamped to [0, 10].
    """
    url    = finding.get("source_url", "")
    domain = extract_domain(url)
    conf   = float(finding.get("confidence_score", 0.8) or 0.8)

    base = 5.0
    if domain:
        for trusted in CREDIBLE_DOMAINS:
            if domain == trusted or domain.endswith(f".{trusted}"):
                base = 10.0
                break

    # Confidence modifier: official (1.0) → +0.5, third-party (0.6) → -0.5
    modifier = (conf - 0.8) * 5   # maps 0.6→-1.0, 0.8→0, 1.0→+1.0
    return max(0.0, min(10.0, base + modifier))


def actionability_score(finding: Dict[str, Any]) -> float:
    """
    Score based on actionable keywords in summary + why_matters.
    v4.0: 'updated' findings get a +1.0 bonus (changed content = more actionable).
    """
    text = (
        finding.get("summary", "") + " " +
        finding.get("why_matters", "")
    ).lower()

    hits   = sum(1 for kw in ACTIONABLE_KEYWORDS if kw in text)
    score  = min(9.0, hits * 1.2)

    # Updated findings are inherently actionable — something changed
    if finding.get("change_status") == "updated":
        score = min(10.0, score + 1.0)

    return score


def compute_final_score(finding: Dict[str, Any]) -> float:
    """
    Weighted multi-factor ranking score.
    formula: final = 0.35*impact + 0.25*novelty + 0.20*credibility + 0.20*actionability
    """
    impact      = max(0.0, min(10.0, float(finding.get("impact_score",  5))))
    novelty     = max(0.0, min(10.0, float(finding.get("novelty_score", 5))))
    cred        = credibility_score(finding)
    actionable  = actionability_score(finding)

    score = (
        0.35 * impact +
        0.25 * novelty +
        0.20 * cred +
        0.20 * actionable
    )
    return round(score, 2)


def rank_findings(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for f in findings:
        f["final_score"] = compute_final_score(f)
    ranked = sorted(findings, key=lambda x: x["final_score"], reverse=True)
    logger.info(
        f"Ranked {len(ranked)} findings. "
        f"Top score: {ranked[0]['final_score'] if ranked else 0}"
    )
    return ranked
