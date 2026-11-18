"""
Optional local-LLM extraction via Ollama (stdlib only — no SDK dependency).

Design rule: the LLM may *locate and phrase* requirements; it may not
invent them. Output is validated against JDProfile and merged with the
deterministic baseline; any failure falls back to deterministic mode.
"""

import hashlib
import json
import logging
import os
import re
import urllib.request
from pathlib import Path
from typing import Optional

from Backend.config import (
    OLLAMA_BASE_URL,
    OLLAMA_CONNECT_TIMEOUT_SECONDS,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SECONDS,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    OPENAI_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)

JD_EXTRACTION_PROMPT = """You extract structured requirements from a job description.
Return ONLY a JSON object with exactly these keys:
job_title (string), seniority (string),
required_skills (array of short skill strings),
preferred_skills (array of short skill strings),
responsibilities (array of short duty strings),
qualifications (array of degree/certification strings).
Rules: copy requirements from the text; do not invent skills that are not implied;
keep each list under 20 items; empty array if absent.

JOB DESCRIPTION:
%s
"""


def _generate(prompt: str) -> str:
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0, "seed": 42},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    # urllib has no separate connect timeout; use a short total timeout for
    # the availability probe and the real timeout for the generation call.
    with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT_SECONDS) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body.get("response", "")


def _generate_openai_compatible(prompt: str) -> str:
    payload = json.dumps({
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
    )
    with urllib.request.urlopen(req, timeout=OPENAI_TIMEOUT_SECONDS) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]


def cloud_available() -> bool:
    return bool(OPENAI_API_KEY)


def ollama_available() -> bool:
    try:
        with urllib.request.urlopen(f"{OLLAMA_BASE_URL}/api/tags", timeout=OLLAMA_CONNECT_TIMEOUT_SECONDS):
            return True
    except Exception:
        return False


def _parse_json_object(text: str) -> Optional[dict]:
    text = text.strip()
    text = re.sub(r"^```(json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return None
        try:
            obj = json.loads(match.group(0))
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            return None


# --- Determinism: a given JD always yields the SAME profile ---------------
# Raw LLM sampling made identical inputs drift across runs (11 vs 13 vs 16
# "required" skills -> different scores). Two guards, both opt-out via
# RESUMEIQ_LLM_CACHE=0:
#   1. temperature 0 + fixed seed on every provider call (above).
#   2. a cache keyed by sha256(provider | model | normalised JD text).
#      The cache stores ONLY JD-derived fields — never resume text, never PII.
_LLM_CACHE_ENABLED = os.getenv("RESUMEIQ_LLM_CACHE", "1").lower() not in ("0", "off", "false")
_LLM_CACHE_PATH = Path(os.getenv("RESUMEIQ_CACHE_DIR", ".cache")) / "jd_profiles.json"
_MEM_CACHE: dict = {}
_MEM_LOADED = False


def _cache_key(jd_text: str, provider: str) -> str:
    model = OLLAMA_MODEL if provider == "ollama" else OPENAI_MODEL
    norm = re.sub(r"\s+", " ", jd_text.lower()).strip()
    return hashlib.sha256(f"{provider}|{model}|{norm}".encode("utf-8")).hexdigest()


def _cache_lookup(key: str):
    global _MEM_LOADED
    if not _MEM_LOADED:
        try:
            data = json.loads(_LLM_CACHE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                _MEM_CACHE.update(data)
        except Exception:
            pass
        _MEM_LOADED = True
    cached = _MEM_CACHE.get(key)
    return dict(cached) if isinstance(cached, dict) else None


def _cache_store(key: str, profile: dict) -> None:
    _MEM_CACHE[key] = profile
    try:
        _LLM_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _LLM_CACHE_PATH.write_text(json.dumps(_MEM_CACHE), encoding="utf-8")
    except OSError as exc:
        logger.warning("JD profile cache write failed (%s); continuing without it.", exc)


def extract_jd_profile_llm(jd_text: str, provider: str = "ollama") -> Optional[dict]:
    """Return a JD-profile dict, or None if the LLM path fails for any reason.

    provider: "ollama" (local, default) or "cloud" (OpenAI-compatible endpoint).
    Results are cached by hash of the JD text so identical inputs are
    bit-for-bit reproducible (and re-analysis takes ~0ms).
    """
    key = _cache_key(jd_text, provider) if _LLM_CACHE_ENABLED else None
    if key:
        cached = _cache_lookup(key)
        if cached is not None:
            logger.info("JD profile cache hit (%s); skipping LLM call.", key[:12])
            return cached
    try:
        generate = _generate_openai_compatible if provider == "cloud" else _generate
        raw = generate(JD_EXTRACTION_PROMPT % jd_text[:12000])
        parsed = _parse_json_object(raw)
        if not parsed:
            logger.warning("LLM JD extraction returned unparseable output; using deterministic parser.")
            return None
        # Normalise shape defensively.
        profile = {
            "job_title": str(parsed.get("job_title") or ""),
            "seniority": str(parsed.get("seniority") or ""),
            "required_skills": [str(s).lower() for s in parsed.get("required_skills", []) if s],
            "preferred_skills": [str(s).lower() for s in parsed.get("preferred_skills", []) if s],
            "responsibilities": [str(s) for s in parsed.get("responsibilities", []) if s],
            "qualifications": [str(s) for s in parsed.get("qualifications", []) if s],
        }
        if not profile["required_skills"] and not profile["preferred_skills"]:
            logger.warning("LLM JD extraction found no skills; using deterministic parser.")
            return None
        if key:
            _cache_store(key, profile)
        return profile
    except Exception as exc:  # never let the LLM path take down the product
        logger.warning("LLM JD extraction failed (%s); using deterministic parser.", exc)
        return None
