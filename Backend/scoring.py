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


# --- Experience inferred from date ranges (no explicit "X years" needed) ---
_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}
_DATE_TOKEN = (
    r"(?:(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    r"\.?\s*\d{4}|\d{1,2}/\d{4}|\d{4})"
)
_END_TOKEN = _DATE_TOKEN + r"|present|current|now|today"
_RANGE_RE = re.compile(rf"({_DATE_TOKEN})\s*(?:–|—|−|-|\bto\b|\buntil\b)\s*({_END_TOKEN})", re.I)



def _parse_date(token: str):
    from datetime import date
    s = token.strip().lower().rstrip(".")
    if s in ("present", "current", "now", "today"):
        return date.today()
    m = re.fullmatch(r"(\d{1,2})/(\d{4})", s)
    if m:
        return date(int(m.group(2)), int(m.group(1)), 1)
    m = re.fullmatch(r"(\d{4})", s)
    if m:
        return date(int(m.group(1)), 7, 1)
    m = re.fullmatch(r"([a-z]+)\.?\s*(\d{4})", s)
    if m:
        month = _MONTHS.get(m.group(1))
        if month:
            return date(int(m.group(2)), month, 1)
    raise ValueError(f"unparsable date token: {token!r}")


def infer_experience_years_from_dates(resume_text: str) -> Optional[float]:
    """Career span from date ranges anywhere in the resume.

    Layout-agnostic: infographic/two-column PDFs often emit section headers
    AFTER their content, so we don't rely on section slicing. A range is
    treated as education when education keywords appear within the same
    neighbourhood; education spans are excluded. Overlapping ranges are
    merged (union) so concurrent jobs are not double-counted.
    """
    edu_keywords = (
        "b.tech", "b.e.", "btech", "be in", "m.tech", "m.e.", "mtech", "mba",
        "bsc", "msc", "bachelor", "master", "degree", "diploma", "cgpa",
        "percentage", "college", "university", "institute of technology",
        "school", "vidyalaya", "class x", "class xii", "ssc", "hsc",
    )

    intervals = []
    for match in _RANGE_RE.finditer(resume_text):
        try:
            start_d = _parse_date(match.group(1))
            end_d = _parse_date(match.group(2))
        except ValueError:
            continue
        if end_d < start_d:
            continue
        if (end_d - start_d).days > 15 * 366:  # sanity cap per range
            continue
        # Context window around the range decides employment vs education.
        window = resume_text[max(0, match.start() - 160): match.end() + 160].lower()
        if any(k in window for k in edu_keywords):
            continue
        intervals.append((start_d, end_d))
    if not intervals:
        return None

    intervals.sort()
    merged = [list(intervals[0])]
    for start_d, end_d in intervals[1:]:
        if start_d <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end_d)
        else:
            merged.append([start_d, end_d])
    total_days = sum((e - s).days for s, e in merged)
    years = total_days / 365.25
    return round(years, 1) if years >= 0.25 else None


def experience_score(resume_text: str, expected_years: Optional[float] = None) -> tuple[Optional[float], str]:
    years = extract_years_experience(resume_text)
    inferred = years is None
    if inferred:
        years = infer_experience_years_from_dates(resume_text)
    if years is None:
        return None, "No explicit years or parseable date ranges found; cannot assess."
    expected = float(expected_years) if expected_years else float(DEFAULT_EXPECTED_YEARS)
    score = _clamp(100.0 * min(years, expected) / expected)
    basis = "estimated from date ranges in the experience section" if inferred else "as stated on the resume"
    return score, f"Resume indicates ~{years:g} year(s) of experience ({basis}) vs ~{expected:g} expected by the JD."


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
