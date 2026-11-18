"""
Deterministic scoring engine.

The LLM (when used) interprets evidence; THIS module produces numbers.
That separation is the core AI-trust decision in ResumeIQ:
scores are reproducible, auditable and calibratable — not sampled
from a model's imagination.
"""

import re
from typing import Dict, List, Optional, Sequence

from Backend.config import DEFAULT_EXPECTED_YEARS, WEIGHTS
from Backend.schemas import DimensionScore

STATUS_CREDIT = {"matched": 1.0, "partial": 0.5, "missing": 0.0}


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


# ---------------------------------------------------------------------------
# Experience dimension
# ---------------------------------------------------------------------------

YEARS_RE = re.compile(
    r"(\d+)\s*\+?\s*(?:years|yrs|yr)(?:\s+of\s+experience)?"  # "2 years of experience"
    r"|(?:years|yrs|yr)(?:\s+of\s+experience)?\s*[:\-]?\s*(\d+)\s*\+?",  # "years of experience: 2"
    re.I,
)


def extract_years_experience(resume_text: str) -> Optional[float]:
    matches = [int(m.group(1) or m.group(2)) for m in YEARS_RE.finditer(resume_text)]
    return float(max(matches)) if matches else None


def experience_score(resume_text: str, expected_years: Optional[float] = None) -> tuple[Optional[float], str]:
    years = extract_years_experience(resume_text)
    if years is None:
        return None, "No explicit years of experience found; cannot assess."
    expected = float(expected_years) if expected_years else float(DEFAULT_EXPECTED_YEARS)
    score = _clamp(100.0 * min(years, expected) / expected)
    return score, f"Resume states ~{years:g} year(s) of experience vs ~{expected:g} expected by the JD."


# ---------------------------------------------------------------------------
# Responsibilities dimension — lexical coverage, not vibes
# ---------------------------------------------------------------------------

_STOPWORDS = {
    "with", "that", "this", "from", "will", "have", "your", "their", "they",
    "including", "across", "within", "into", "about", "over", "under", "other",
    "our", "you", "for", "and", "the", "are", "work", "role", "team", "build",
}


def responsibilities_score(jd_bullets: Sequence[str], resume_text: str) -> tuple[Optional[float], str]:
    if not jd_bullets:
        return None, "No responsibilities extracted from the JD."
    resume_lower = resume_text.lower()
    covered_salience = 0
    total_salience = 0
    for bullet in jd_bullets:
        tokens = [
            t for t in re.findall(r"[a-z][a-z/&+-]{4,}", bullet.lower())
            if t not in _STOPWORDS
        ]
        if not tokens:
            continue
        hits = sum(1 for t in set(tokens) if t in resume_lower)
        covered_salience += hits / len(set(tokens))
        total_salience += 1
    if total_salience == 0:
        return None, "Responsibilities could not be tokenized."
    coverage = covered_salience / total_salience
    score = _clamp(100.0 * coverage)
    return score, f"Resume covers, on average, {coverage:.0%} of salient terms per JD bullet."


# ---------------------------------------------------------------------------
# Qualifications dimension
# ---------------------------------------------------------------------------

_DEGREE_CLASSES = [
    {"bachelor", "bachelors", "b.tech", "b.e.", "bsc", "bba", "b.com", "b.a."},
    {"master", "masters", "mba", "m.tech", "msc", "m.com", "ms"},
    {"phd", "doctorate"},
]


def qualification_score(jd_qualifications: Sequence[str], resume_text: str) -> tuple[Optional[float], str]:
    if not jd_qualifications:
        return None, "JD states no formal qualification requirement."
    resume_lower = resume_text.lower()
    hits = 0
    for qual in jd_qualifications:
        qual_lower = qual.lower()
        classes = [c for c in _DEGREE_CLASSES if any(d in qual_lower for d in c)]
        if classes:
            # Degree class equivalence: a B.Tech satisfies a "Bachelor's" requirement.
            if any(any(d in resume_lower for d in c) for c in classes):
                hits += 1
        elif any(tok in resume_lower for tok in re.findall(r"[a-z.]{4,}", qual_lower)):
            hits += 1
    score = _clamp(100.0 * hits / len(jd_qualifications))
    return score, f"{hits}/{len(jd_qualifications)} qualification signal(s) found in resume."


# ---------------------------------------------------------------------------
# Weighted aggregation with renormalisation of not-applicable dimensions
# ---------------------------------------------------------------------------

def build_dimensions(
    skills_score: Optional[float],
    skills_detail: str,
    experience: tuple,
    responsibilities: tuple,
    preferred_skills_score: Optional[float],
    preferred_detail: str,
    qualifications: tuple,
) -> List[DimensionScore]:
    exp_score, exp_detail = experience
    resp_score, resp_detail = responsibilities
    qual_score, qual_detail = qualifications

    raw = [
        ("required_skills", skills_score, skills_detail),
        ("relevant_experience", exp_score, exp_detail),
        ("responsibilities", resp_score, resp_detail),
        ("preferred_skills", preferred_skills_score, preferred_detail),
        ("qualifications", qual_score, qual_detail),
    ]

    applicable = [(name, score, detail) for name, score, detail in raw if score is not None]
    total_weight = sum(WEIGHTS[name] for name, _, _ in applicable)

    dimensions: List[DimensionScore] = []
    labels = {
        "required_skills": "Required skills",
        "relevant_experience": "Relevant experience",
        "responsibilities": "Responsibilities alignment",
        "preferred_skills": "Preferred skills",
        "qualifications": "Qualifications",
    }
    for name, score, detail in raw:
        weight = WEIGHTS[name]
        renorm = (weight / total_weight * 100.0) if (score is not None and total_weight > 0) else 0.0
        dimensions.append(
            DimensionScore(
                name=labels[name],
                score=round(_clamp(score), 1) if score is not None else None,
                weight=round(renorm, 1),
                detail=detail,
            )
        )
    return dimensions


def overall_from_dimensions(dimensions: List[DimensionScore]) -> int:
    applicable = [d for d in dimensions if d.score is not None]
    total_weight = sum(d.weight for d in applicable)
    if not applicable or total_weight == 0:
        return 0
    weighted = sum((d.score or 0.0) * d.weight for d in applicable)
    return int(round(weighted / total_weight))


def verdict_for(score: int) -> str:
    if score >= 80:
        return "Strong alignment"
    if score >= 60:
        return "Moderate to strong alignment"
    if score >= 40:
        return "Partial alignment — targeted improvements recommended"
    return "Significant gaps — consider whether this role is the right target"
