"""
deduplicator.py
-----------------------
Three-layer deduplication + topic clustering.

Layer 1 — Exact hash match (O(1))
  Catches identical pages fetched from two URLs.

Layer 2 — Title similarity via SequenceMatcher (threshold 0.85)
  Catches same announcement reworded across sources.

Layer 3 — Entity + keyword overlap (NEW v4.1)
  Catches semantic duplicates where titles differ but core content
  is the same announcement (e.g. "OpenAI launches GPT-5" vs
  "GPT-5 is now available from OpenAI"). Requires ≥2 shared entities
  AND ≥3 shared keywords to flag as duplicate.
  No external dependencies — pure Python set intersection.

Cross-run dedup:
  pipeline.py queries DB by content_hash before inserting.

Topic clusters (8):
  Maps findings to one of 8 predefined topic areas.
"""

import logging
from difflib import SequenceMatcher
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)

TITLE_SIMILARITY_THRESHOLD  = 0.85
ENTITY_OVERLAP_MIN          = 2    # Shared entities to flag semantic dup
KEYWORD_OVERLAP_MIN         = 3    # Shared content keywords to flag semantic dup

TOPIC_CLUSTERS = {
    "safety & alignment":  ["safety", "alignment", "rlhf", "harmful", "bias",
                            "fairness", "red team", "redteam", "guardrail"],
    "benchmarks & evals":  ["benchmark", "eval", "leaderboard", "mmlu", "score",
                            "accuracy", "sota", "hellaswag", "human eval"],
    "model releases":      ["release", "launch", "available", "ga", "version",
                            "model", "weights", "checkpoint", "preview", "early access"],
    "agents & reasoning":  ["agent", "reasoning", "chain-of-thought", "planning",
                            "tool use", "react", "agentic", "function call"],
    "multimodal":          ["multimodal", "vision", "image", "audio", "video",
                            "speech", "ocr", "omni"],
    "infrastructure":      ["api", "latency", "throughput", "inference", "cost",
                            "pricing", "tokens", "quota", "rate limit", "context window"],
    "research":            ["paper", "arxiv", "training", "architecture",
                            "attention", "transformer", "pretraining", "dataset"],
    "open source":         ["open source", "open-source", "weights", "hugging face",
                            "community", "mit license", "apache", "llama", "mistral"],
}


# ── Helpers ────────────────────────────────────────────────────────────────

def title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _entity_set(finding: Dict[str, Any]) -> Set[str]:
    return {e.lower().strip() for e in (finding.get("entities") or [])}


def _keyword_set(finding: Dict[str, Any]) -> Set[str]:
    """Extract meaningful words (len>4) from title + summary."""
    text  = f"{finding.get('title','')} {finding.get('summary','')}".lower()
    words = {w.strip(".,!?;:\"'()[]") for w in text.split() if len(w) > 4}
    return words


def _is_semantic_duplicate(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    """
    Layer 3: entity + keyword overlap check.
    Two findings are semantic duplicates if they share enough entities AND keywords.
    Uses pure Python set intersection — no embeddings required.
    """
    entity_overlap   = _entity_set(a) & _entity_set(b)
    keyword_overlap  = _keyword_set(a) & _keyword_set(b)
    return (len(entity_overlap) >= ENTITY_OVERLAP_MIN and
            len(keyword_overlap) >= KEYWORD_OVERLAP_MIN)


# ── Main dedup function ────────────────────────────────────────────────────

def deduplicate_batch(
    findings: List[Dict[str, Any]],
    threshold: float = TITLE_SIMILARITY_THRESHOLD,
) -> List[Dict[str, Any]]:
    """
    Remove within-batch duplicates using three layers:
      1. Exact content hash
      2. Title string similarity (SequenceMatcher ≥ threshold)
      3. Entity + keyword overlap (semantic near-duplicate)

    Preserves first occurrence of each unique finding.
    """
    unique: List[Dict[str, Any]] = []
    seen_hashes: Set[str] = set()
    removed = 0

    for finding in findings:
        content_hash = finding.get("content_hash", "")
        title        = finding.get("title", "")

        # Layer 1: exact hash
        if content_hash and content_hash in seen_hashes:
            logger.debug(f"[Dedup L1-hash] removed: '{title[:60]}'")
            removed += 1
            continue

        # Layer 2 + 3: compare against accepted findings
        is_dup = False
        for accepted in unique:
            # Title similarity
            if title_similarity(title, accepted.get("title", "")) >= threshold:
                logger.debug(f"[Dedup L2-title] removed: '{title[:50]}'")
                is_dup = True
                removed += 1
                break
            # Semantic overlap
            if _is_semantic_duplicate(finding, accepted):
                logger.debug(f"[Dedup L3-semantic] removed: '{title[:50]}'")
                is_dup = True
                removed += 1
                break

        if not is_dup:
            if content_hash:
                seen_hashes.add(content_hash)
            unique.append(finding)

    logger.info(
        f"Dedup: {len(findings)} input → {len(unique)} unique "
        f"({removed} removed across 3 layers)"
    )
    return unique


# ── Topic clustering ───────────────────────────────────────────────────────

def assign_topic_cluster(finding: dict) -> str:
    text = " ".join([
        " ".join(finding.get("tags", [])),
        finding.get("title", ""),
        finding.get("summary", ""),
        finding.get("why_matters", ""),
    ]).lower()

    best_cluster = "general"
    best_hits    = 0

    for cluster, keywords in TOPIC_CLUSTERS.items():
        hits = sum(1 for kw in keywords if kw in text)
        if hits > best_hits:
            best_hits    = hits
            best_cluster = cluster

    return best_cluster


def assign_clusters(findings: list) -> list:
    for f in findings:
        f["topic_cluster"] = assign_topic_cluster(f)
    return findings
