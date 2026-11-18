"""
Optional local-LLM extraction via Ollama (stdlib only — no SDK dependency).

Design rule: the LLM may *locate and phrase* requirements; it may not
invent them. Output is validated against JDProfile and merged with the
deterministic baseline; any failure falls back to deterministic mode.
"""

import json
import logging
import re
import urllib.request
from typing import Optional

from Backend.config import (
    OLLAMA_BASE_URL,
    OLLAMA_CONNECT_TIMEOUT_SECONDS,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SECONDS,
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
        "options": {"temperature": 0.1},
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


def extract_jd_profile_llm(jd_text: str) -> Optional[dict]:
    """Return a JD-profile dict, or None if the LLM path fails for any reason."""
    try:
        raw = _generate(JD_EXTRACTION_PROMPT % jd_text[:12000])
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
        return profile
    except Exception as exc:  # never let the LLM path take down the product
        logger.warning("LLM JD extraction failed (%s); using deterministic parser.", exc)
        return None
