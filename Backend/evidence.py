"""
Evidence matching helpers: canonicalise LLM output against the lexicon
and match skills in text despite aliases and simple morphology.
"""

import re
from typing import List

from Backend.skill_lexicon import SKILL_ALIASES, SKILL_CANONICAL, SKILL_LEXICON

_DELIMIT = r"(?<![a-z0-9])"
_DELIMIT_END = r"(?![a-z0-9])"


def canonical_skill(term: str) -> str:
    """Merge surface variants onto one canonical skill (idempotent)."""
    return SKILL_CANONICAL.get((term or "").lower(), (term or "").lower())


def _variants(term: str) -> List[str]:
    return [term] + SKILL_ALIASES.get(term.lower(), [])


def canonicalise_skills(raw_skills: List[str]) -> List[str]:
    """Map free-text LLM skills onto known lexicon terms.

    LLM proposes, lexicon verifies: anything we cannot map is dropped,
    because we cannot cite evidence for it downstream. Order preserved,
    duplicates removed.
    """
    out: List[str] = []
    seen = set()
    for raw in raw_skills:
        lowered = (raw or "").lower()
        for term in SKILL_LEXICON:
            canonical = canonical_skill(term)
            if canonical in seen:
                continue
            for variant in _variants(term):
                if re.search(f"{_DELIMIT}{re.escape(variant)}{_DELIMIT_END}", lowered):
                    out.append(canonical)
                    seen.add(canonical)
                    break
    return out


def _stem(term: str) -> str:
    for suf in ("ation", "tion", "ing", "es", "s"):
        if term.endswith(suf) and len(term) - len(suf) >= 5:
            return term[: -len(suf)]
    return term


def _variant_pattern(variant: str) -> str:
    stem = _stem(variant.lower())
    if stem == variant.lower():
        return re.escape(variant)
    return re.escape(stem) + r"[a-z]*"


def _union_pattern(term: str) -> str:
    parts = [_variant_pattern(v) for v in _variants(term)]
    return "(?:" + "|".join(parts) + ")"


def term_in_text(term: str, text_lower: str) -> bool:
    return re.search(f"{_DELIMIT}{_union_pattern(term)}{_DELIMIT_END}", text_lower) is not None


def find_line_with_term(term: str, resume_text: str) -> str:
    """First resume line containing the term/alias (morphology-tolerant), else ''."""
    pattern = re.compile(f"{_DELIMIT}{_union_pattern(term)}{_DELIMIT_END}", re.I)
    for line in resume_text.splitlines():
        if pattern.search(line):
            cleaned = re.sub(r"\s+", " ", line).strip().strip("|•- ")
            if len(cleaned) <= 220:
                return cleaned
            cut = cleaned[:220].rsplit(" ", 1)[0].rstrip(",;:- ")
            return cut + "…"
    return ""
