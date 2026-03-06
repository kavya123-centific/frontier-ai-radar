"""
summarizer.py
---------------------
LLM-powered structured intelligence extraction.

v4.0 CHANGES:
  - confidence_score normalization: maps any float → nearest of [1.0, 0.8, 0.6]
    (was previously clamping to [0.0,1.0] which allowed values like 0.7 that the
     spec does not define — now strictly enforces the three allowed tiers)
  - Provider-agnostic design retained from v3.2.

Supported providers (via .env):
  OpenRouter, Groq, Google AI, HuggingFace Inference, Ollama, Anthropic (native)
"""

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

MAX_RETRIES  = 3
RETRY_DELAYS = [2, 4, 8]

# ── Prompts ────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert AI industry intelligence analyst.
Extract structured intelligence from web content about AI, ML, and tech companies.
Return ONLY valid JSON with no markdown fences, no backticks, no explanation text.
If content has no relevant AI/ML intelligence, return the exact sentinel JSON specified."""

EXTRACTION_PROMPT = """Source: {url}
Category context: {category}

Analyze the content below and return EXACTLY this JSON structure:
{{
  "title": "concise headline under 15 words describing the key development",
  "summary": "2-3 sentences summarizing what changed or was announced",
  "why_matters": "1-2 sentences on business or technical impact for AI practitioners",
  "publisher": "company or organization name (string, not URL)",
  "impact_score": <integer 0-10, significance in AI landscape>,
  "novelty_score": <integer 0-10, how new or surprising vs prior knowledge>,
  "confidence_score": <MUST be exactly 1.0 for official source, 0.8 for blog/docs, 0.6 for third-party report>,
  "evidence": "1-2 verbatim sentences directly quoted from the source content that prove the finding",
  "tags": ["tag1", "tag2", "tag3"],
  "entities": ["company names", "model names", "dataset names mentioned"]
}}

Rules:
- impact_score and novelty_score MUST be integers between 0 and 10
- confidence_score MUST be EXACTLY 1.0, 0.8, or 0.6 — no other values allowed
- evidence MUST be a direct quote from the content, not a paraphrase
- tags should be 2-5 short lowercase keywords
- entities should be proper nouns only
- If no relevant AI/ML content exists, return:
  {{"title": "NO_RELEVANT_CONTENT", "summary": "", "why_matters": "", "publisher": "", "impact_score": 0, "novelty_score": 0, "confidence_score": 0.0, "evidence": "", "tags": [], "entities": []}}

Content (first 5000 chars):
{content}"""


# ── Config resolution ──────────────────────────────────────────────────────

def _resolve_config():
    base_url = os.getenv("LLM_BASE_URL", "").strip()
    api_key  = os.getenv("LLM_API_KEY",  "").strip()
    model    = os.getenv("LLM_MODEL",    "").strip()

    if base_url:
        if not api_key:
            raise EnvironmentError(
                "LLM_BASE_URL is set but LLM_API_KEY is missing. "
                "Add LLM_API_KEY to your .env file."
            )
        if not model:
            raise EnvironmentError(
                "LLM_BASE_URL is set but LLM_MODEL is missing. "
                "Add LLM_MODEL to your .env (e.g. deepseek/deepseek-r1:free)."
            )
        return "openai_compat", api_key, base_url, model

    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not anthropic_key:
        raise EnvironmentError(
            "No LLM provider configured. Add ONE of these blocks to your .env:\n\n"
            "--- OpenRouter (free, recommended) ---\n"
            "LLM_API_KEY=<key from openrouter.ai>\n"
            "LLM_BASE_URL=https://openrouter.ai/api/v1\n"
            "LLM_MODEL=deepseek/deepseek-r1:free\n\n"
            "--- Groq (free tier, very fast) ---\n"
            "LLM_API_KEY=<key from console.groq.com>\n"
            "LLM_BASE_URL=https://api.groq.com/openai/v1\n"
            "LLM_MODEL=llama-3.3-70b-versatile\n\n"
            "--- Anthropic (requires credits) ---\n"
            "ANTHROPIC_API_KEY=<key>\n"
        )
    return "anthropic", anthropic_key, "", model or "claude-haiku-4-5-20251001"


# ── Sanitization ───────────────────────────────────────────────────────────

# v4.0: Only these three values are valid per spec
VALID_CONFIDENCE_TIERS = [1.0, 0.8, 0.6]


def _normalize_confidence(val: Any) -> float:
    """
    v4.0: Map any float to the nearest allowed confidence tier.
    Valid tiers: 1.0 (official), 0.8 (blog/docs), 0.6 (third-party)
    This enforces the spec strictly — no 0.7, 0.9, etc.
    """
    try:
        v = float(val)
        v = max(0.0, min(1.0, v))
        return min(VALID_CONFIDENCE_TIERS, key=lambda c: abs(c - v))
    except (TypeError, ValueError):
        return 0.8


def _safe_score(val: Any, default: float = 5.0) -> float:
    try:
        return max(0.0, min(10.0, float(val)))
    except (TypeError, ValueError):
        return default


def _sanitize(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title":            str(raw.get("title", "Untitled"))[:500],
        "summary":          str(raw.get("summary", "")),
        "why_matters":      str(raw.get("why_matters", "")),
        "publisher":        str(raw.get("publisher", "Unknown")),
        "impact_score":     _safe_score(raw.get("impact_score"),  default=5.0),
        "novelty_score":    _safe_score(raw.get("novelty_score"), default=5.0),
        "confidence_score": _normalize_confidence(raw.get("confidence_score", 0.8)),
        "evidence":         str(raw.get("evidence", ""))[:1000],
        "tags":     raw.get("tags", [])     if isinstance(raw.get("tags"),     list) else [],
        "entities": raw.get("entities", []) if isinstance(raw.get("entities"), list) else [],
    }


def _clean_json(text: str) -> str:
    return text.replace("```json", "").replace("```", "").strip()


# ── Provider calls ─────────────────────────────────────────────────────────

class _RateLimitError(Exception): pass
class _ServerError(Exception):
    def __init__(self, code): self.status_code = code
class _PermanentError(Exception):
    def __init__(self, code, body): self.status_code = code; self.body = body


async def _call_openai_compat(api_key, base_url, model, prompt):
    import httpx
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/frontier-ai-radar",
        "X-Title": "Frontier AI Radar",
    }
    payload = {
        "model": model,
        "max_tokens": 1000,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers=headers, json=payload,
        )
    if resp.status_code == 429:
        raise _RateLimitError()
    if resp.status_code >= 500:
        raise _ServerError(resp.status_code)
    if resp.status_code >= 400:
        raise _PermanentError(resp.status_code, resp.json())
    return resp.json()["choices"][0]["message"]["content"]


async def _call_anthropic(api_key, model, prompt):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model, max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


# ── Core entry point ───────────────────────────────────────────────────────

async def summarize_content(
    text: str, url: str, category: str,
) -> Optional[Dict[str, Any]]:
    """
    Extract structured intelligence from page text.
    Auto-selects provider from .env — no code changes needed to switch.
    """
    try:
        mode, api_key, base_url, model = _resolve_config()
    except EnvironmentError as e:
        logger.error(f"Config error: {e}")
        raise

    prompt   = EXTRACTION_PROMPT.format(url=url, category=category, content=text[:5000])
    provider = base_url.split("/")[2] if base_url else "anthropic"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if mode == "openai_compat":
                raw = await _call_openai_compat(api_key, base_url, model, prompt)
            else:
                raw = await _call_anthropic(api_key, model, prompt)

            parsed = json.loads(_clean_json(raw))

            if parsed.get("title") == "NO_RELEVANT_CONTENT":
                logger.debug(f"No relevant AI content at: {url}")
                return None

            return _sanitize(parsed)

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error (attempt {attempt}/{MAX_RETRIES}) for {url}: {e}")
            if attempt < MAX_RETRIES:
                await _async_sleep(RETRY_DELAYS[attempt - 1])

        except _RateLimitError:
            logger.warning(f"Rate limited by {provider} (attempt {attempt}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES:
                await _async_sleep(RETRY_DELAYS[attempt - 1])

        except _ServerError as e:
            logger.warning(f"{provider} server error {e.status_code} (attempt {attempt}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES:
                await _async_sleep(RETRY_DELAYS[attempt - 1])

        except _PermanentError as e:
            logger.error(f"{provider} permanent error {e.status_code} for {url}: {e.body}")
            if e.status_code == 401 and "openrouter" in (base_url or "").lower():
                logger.error(
                    "OpenRouter 401: check LLM_API_KEY in backend/.env — get a valid key at https://openrouter.ai/keys"
                )
            return None

        except EnvironmentError:
            raise

        except Exception as e:
            cls = type(e).__name__
            if cls == "RateLimitError":
                logger.warning(f"Rate limited (attempt {attempt}/{MAX_RETRIES})")
                if attempt < MAX_RETRIES:
                    await _async_sleep(RETRY_DELAYS[attempt - 1])
            elif cls == "APIStatusError":
                status = getattr(e, "status_code", 0)
                if status >= 500:
                    logger.warning(f"Server error {status} (attempt {attempt}/{MAX_RETRIES})")
                    if attempt < MAX_RETRIES:
                        await _async_sleep(RETRY_DELAYS[attempt - 1])
                else:
                    logger.error(f"Permanent error {status} for {url}: {e}")
                    return None
            else:
                logger.error(f"Summarization error for {url}: {cls}: {e}")
                return None

    logger.error(f"Summarization failed after {MAX_RETRIES} attempts: {url}")
    return None


async def _async_sleep(seconds: float) -> None:
    import asyncio
    await asyncio.sleep(seconds)
