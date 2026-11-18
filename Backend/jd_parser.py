"""
Deterministic JD parser.

Splits a job description into sections (required / preferred /
responsibilities / qualifications), extracts lexicon-known skills per
section, and captures seniority and degree signals. No LLM involved —
fully reproducible, which is what makes the offline demo and the eval
harness meaningful.
"""

import re
from typing import List, Tuple

from Backend.config import SENIORITY_EXPECTATIONS
from Backend.evidence import canonical_skill, term_in_text
from Backend.skill_lexicon import DEGREE_KEYWORDS, SKILL_LEXICON

_BULLET_RE = re.compile(r"^\s*[-*•▪◦]\s+|^\s*\d+[.)]\s+")
_REQUIRED_RE = re.compile(r"(required|must[- ]have|requirements?|what you.?ll need|you have|qualifications? you)", re.I)
_PREFERRED_RE = re.compile(r"(preferred|nice[- ]to[- ]have|bonus|plus|desired|good to have|advantage)", re.I)
_RESPONSIBILITY_RE = re.compile(r"(responsibilit|what you.?ll do|the role|about the (role|job)|day[- ]to[- ]day|you will|what you.?ll be)", re.I)

TITLE_KEYWORDS_RE = re.compile(
    r"\b(product manager|associate product manager|apm|program manager|project manager|"
    r"senior product manager|data analyst|business analyst|product analyst|"
    r"product owner|growth manager|strategy manager|consultant|engineer)\b", re.I)


def _clean(line: str) -> str:
    return _BULLET_RE.sub("", line).strip(" \t-•*").strip()


def _is_bullet(line: str) -> bool:
    return bool(_BULLET_RE.match(line))


def split_sections(jd_text: str) -> List[Tuple[str, str]]:
    """Return (section, line) for each non-empty line.

    Section is one of: required | preferred | responsibilities | other.
    """
    section = "other"
    tagged: List[Tuple[str, str]] = []
    for raw in jd_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        is_headerish = len(line) < 60 and not _is_bullet(line) and line.rstrip().endswith((":",))
        # Standalone label line (e.g. "Requirements") — the keyword accounts
        # for most of the line. Bullets can never be headers.
        def _label(regex, max_len):
            m = regex.search(line.lower())
            return bool(m) and not _is_bullet(line) and len(line) <= max_len and len(m.group(0)) >= 0.5 * len(line.strip())

        if _PREFERRED_RE.search(line.lower()) and (is_headerish or _label(_PREFERRED_RE, 40)):
            section = "preferred"
            continue
        if _REQUIRED_RE.search(line.lower()) and (is_headerish or _label(_REQUIRED_RE, 40)):
            section = "required"
            continue
        if _RESPONSIBILITY_RE.search(line.lower()) and (is_headerish or _label(_RESPONSIBILITY_RE, 80)):
            section = "responsibilities"
            continue
        tagged.append((section, line))
    return tagged


def extract_title(jd_text: str) -> str:
    m = TITLE_KEYWORDS_RE.search(jd_text)
    if m:
        return m.group(0).strip().title().replace("Apm", "APM")
    for raw in jd_text.splitlines():
        line = raw.strip()
        if 3 < len(line) <= 80:
            return line.rstrip(".:")
    return ""


def detect_seniority(jd_text: str) -> str:
    lowered = jd_text.lower()
    for keyword, (_, label) in SENIORITY_EXPECTATIONS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", lowered):
            return label
    m = re.search(r"(\d+)\s*\+?\s*(?:years|yrs|yr)", lowered)
    if m:
        return f"{m.group(1)}+ years"
    return "Not stated"


def parse_jd(jd_text: str):
    """Return (JDProfile dict, expected_seniority_years_or_None)."""
    tagged = split_sections(jd_text)

    required, preferred = set(), set()
    responsibilities: List[str] = []
    qualifications: List[str] = []

    for section, line in tagged:
        lowered = line.lower()

        if any(deg in lowered for deg in DEGREE_KEYWORDS):
            cleaned = _clean(line)
            if cleaned and cleaned not in qualifications:
                qualifications.append(cleaned)
            continue

        if section == "responsibilities":
            cleaned = _clean(line)
            if len(cleaned) > 25:
                responsibilities.append(cleaned)

        for term in SKILL_LEXICON:
            if term_in_text(term, lowered):
                canonical = canonical_skill(term)
                if section == "preferred":
                    preferred.add(canonical)
                else:  # required + untagged default to mandatory
                    required.add(canonical)

    # A skill seen in both sections is treated as required (mandatory wins).
    preferred -= required

    # If we found no responsibility bullets, fall back to bullet lines
    # that look like duties (start with a verb-ish token, reasonably long).
    if not responsibilities:
        for _, line in tagged:
            cleaned = _clean(line)
            if _is_bullet(line) and len(cleaned) > 40:
                responsibilities.append(cleaned)
    responsibilities = responsibilities[:12]

    seniority_label = detect_seniority(jd_text)
    years_match = re.search(r"(\d+)\s*\+?\s*(?:years|yrs|yr)", jd_text.lower())
    expected_years = float(years_match.group(1)) if years_match else None
    if expected_years is None:
        for keyword, (years, label) in SENIORITY_EXPECTATIONS.items():
            if label == seniority_label:
                expected_years = float(years)
                break

    profile = {
        "job_title": extract_title(jd_text),
        "seniority": seniority_label,
        "required_skills": sorted(required),
        "preferred_skills": sorted(preferred),
        "responsibilities": responsibilities,
        "qualifications": qualifications,
    }
    return profile, expected_years
