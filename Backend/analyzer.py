"""
ResumeIQ analysis orchestrator.

Flow (deliberately boring, deliberately auditable):
  parse resume text (already done upstream)
    -> build JD profile      (LLM if available, else deterministic)
    -> match skills          (deterministic, evidence-cited)
    -> score dimensions      (deterministic)
    -> gaps + recommendations (grounded in actual resume lines)
"""

import re
import time
import uuid
from typing import List, Optional, Tuple

from Backend.config import LLM_MODE, OLLAMA_MODEL, OPENAI_MODEL
from Backend.jd_parser import parse_jd
from Backend.evidence import canonicalise_skills, find_line_with_term
from Backend.interview_map import build_interview_map
from Backend.llm import cloud_available, extract_jd_profile_llm, ollama_available
from Backend.scoring import (
    build_dimensions,
    experience_score,
    overall_from_dimensions,
    qualification_score,
    responsibilities_score,
    verdict_for,
)
from Backend.schemas import (
    AnalysisMeta,
    AnalysisResponse,
    JDProfile,
    Recommendation,
    SkillAssessment,
)
from Backend.skill_lexicon import SKILL_LEXICON

_SEPARATORS_RE = re.compile(r"[,|•;/]")
ACTION_VERB_RE = re.compile(
    r"\b(led|built|designed|launched|shipped|owned|delivered|created|developed|"
    r"improved|reduced|increased|grew|managed|drove|analysed|analyzed|measured|"
    r"partnered|negotiated|defined|scaled|automated)\b", re.I)
METRIC_RE = re.compile(r"(\d+%|\d+\s*(?:x\b|users|customers|teams|markets|cr|lakh|million|\$|₹))", re.I)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _evidence_line(resume_text: str, term: str) -> Optional[str]:
    line = find_line_with_term(term, resume_text)
    return line or None


def _is_skills_list_line(line: str) -> bool:
    """Heuristic: comma/pipe/bullet-dense short line = skills list, not evidence."""
    return len(_SEPARATORS_RE.findall(line)) >= 4 and len(line) < 200


def _assess_skill(resume_text: str, term: str, requirement: str) -> SkillAssessment:
    line = _evidence_line(resume_text, term)
    if line is None:
        return SkillAssessment(
            skill=term, requirement=requirement, status="missing",
            evidence="", note="No direct evidence found in the resume text.",
        )
    if _is_skills_list_line(line):
        return SkillAssessment(
            skill=term, requirement=requirement, status="partial",
            evidence=line,
            note="Listed among other skills; no demonstrated impact shown.",
        )
    note = "Demonstrated in context." if (ACTION_VERB_RE.search(line) or METRIC_RE.search(line)) else "Found in context."
    return SkillAssessment(skill=term, requirement=requirement, status="matched", evidence=line, note=note)


def _dedupe(items: List[str]) -> List[str]:
    seen, out = set(), []
    for item in items:
        key = _norm(item)
        if key and key not in seen:
            seen.add(key)
            out.append(item.strip())
    return out


def _skill_dimension(assessments: List[SkillAssessment], requirement: str):
    relevant = [a for a in assessments if a.requirement == requirement]
    if not relevant:
        return None, "Not stated in JD." if requirement == "preferred" else "None found in JD."
    credit = {"matched": 1.0, "partial": 0.5, "missing": 0.0}
    total = sum(credit[a.status] for a in relevant)
    score = 100.0 * total / len(relevant)
    matched = sum(1 for a in relevant if a.status == "matched")
    partial = sum(1 for a in relevant if a.status == "partial")
    return score, f"{matched} matched, {partial} partial, {len(relevant) - matched - partial} without evidence (of {len(relevant)} {requirement})."


def analyze(resume_text: str, jd_text: str, filename: str) -> AnalysisResponse:
    started = time.perf_counter()
    request_id = uuid.uuid4().hex[:12]

    # --- JD profile: LLM (if usable) with deterministic fallback ----------
    extraction_mode = "deterministic"
    model = None
    llm_profile = None
    if LLM_MODE in ("auto", "ollama") and ollama_available():
        llm_profile = extract_jd_profile_llm(jd_text, "ollama")
        if llm_profile:
            model = OLLAMA_MODEL
    elif LLM_MODE in ("auto", "cloud") and cloud_available():
        llm_profile = extract_jd_profile_llm(jd_text, "cloud")
        if llm_profile:
            model = OPENAI_MODEL
    elif LLM_MODE == "cloud":
        raise RuntimeError(
            "RESUMEIQ_LLM=cloud but OPENAI_API_KEY is not set. "
            "Configure OPENAI_BASE_URL / OPENAI_API_KEY / OPENAI_MODEL (see DEPLOYMENT.md)."
        )

    det_profile, expected_years = parse_jd(jd_text)

    if llm_profile:
        extraction_mode = "llm"
        # LLM proposes, lexicon verifies: canonicalise free-text skills onto
        # terms we can evidence. Unmappable skills are dropped, not guessed.
        req = _dedupe(canonicalise_skills(llm_profile["required_skills"]))
        pref = _dedupe(canonicalise_skills(llm_profile["preferred_skills"]))
        jd_profile = JDProfile(
            job_title=llm_profile["job_title"] or det_profile["job_title"],
            seniority=llm_profile["seniority"] or det_profile["seniority"],
            required_skills=req or det_profile["required_skills"],
            preferred_skills=pref or det_profile["preferred_skills"],
            responsibilities=_dedupe(llm_profile["responsibilities"]) or det_profile["responsibilities"],
            qualifications=_dedupe(llm_profile["qualifications"]) or det_profile["qualifications"],
        )
    else:
        if LLM_MODE == "ollama":
            raise RuntimeError("RESUMEIQ_LLM=ollama but the local Ollama service is unavailable.")
        jd_profile = JDProfile(**det_profile)

    # --- Skill matching (always deterministic, always evidence-cited) ------
    assessments = [
        _assess_skill(resume_text, term, "required") for term in jd_profile.required_skills
    ] + [
        _assess_skill(resume_text, term, "preferred") for term in jd_profile.preferred_skills
    ]

    required_score, required_detail = _skill_dimension(assessments, "required")
    preferred_score, preferred_detail = _skill_dimension(assessments, "preferred")

    # --- Dimension scoring -------------------------------------------------
    exp = experience_score(resume_text, expected_years)
    resp = responsibilities_score(jd_profile.responsibilities, resume_text)
    qual = qualification_score(jd_profile.qualifications, resume_text)

    dimensions = build_dimensions(
        skills_score=required_score,
        skills_detail=required_detail,
        experience=exp,
        responsibilities=resp,
        preferred_skills_score=preferred_score,
        preferred_detail=preferred_detail,
        qualifications=qual,
    )
    overall = overall_from_dimensions(dimensions)

    # --- Gaps ---------------------------------------------------------------
    critical = [a.skill for a in assessments if a.requirement == "required" and a.status == "missing"]
    important = [a.skill for a in assessments if a.requirement == "required" and a.status == "partial"]
    optional = [a.skill for a in assessments if a.requirement == "preferred" and a.status == "missing"]

    # --- Grounded recommendations -------------------------------------------
    recommendations: List[Recommendation] = []

    for a in assessments:
        if a.requirement == "required" and a.status == "partial":
            recommendations.append(Recommendation(
                type="rewrite",
                title=f"Prove {a.skill} with impact, not a list entry",
                detail=("This skill appears only in a skills list. Add one bullet showing the "
                        "outcome it drove — scope, action, measurable result."),
                evidence=a.evidence,
            ))
    for a in assessments:
        if a.requirement == "required" and a.status == "missing":
            recommendations.append(Recommendation(
                type="learn",
                title=f"No evidence of {a.skill} — decide: learn it or surface it",
                detail=("If you genuinely have this skill, add a concrete example with context. "
                        "If not, it is a real gap to close — not a wording problem."),
                evidence="",
            ))

    # Presentation improvements grounded in weak bullets (no invented content).
    weak_bullets = [
        ln.strip() for ln in resume_text.splitlines()
        if ln.strip().startswith(("-", "•")) and ln.strip() and not METRIC_RE.search(ln) and len(ln) > 40
    ][:3]
    for bullet in weak_bullets:
        recommendations.append(Recommendation(
            type="rewrite",
            title="Quantify an outcome",
            detail="This bullet describes activity but no result. Add the scale or outcome you drove.",
            evidence=bullet[:220],
        ))

    recommendations = recommendations[:8]

    meta = AnalysisMeta(
        request_id=request_id,
        extraction_mode=extraction_mode,
        model=model,
        latency_ms=int((time.perf_counter() - started) * 1000),
    )

    return AnalysisResponse(
        filename=filename,
        overall_score=overall,
        verdict=verdict_for(overall),
        disclaimer=("This match score is a decision-support signal about alignment between your "
                    "resume and this job description. It is not a probability of being hired and "
                    "must not be used as an automated hiring decision."),
        dimensions=dimensions,
        skills=assessments,
        jd_profile=jd_profile,
        gaps={
            "critical": critical,
            "important": important,
            "optional": optional,
            "presentation": [a.skill for a in assessments if a.status == "partial"],
        },
        recommendations=recommendations,
        interview_map=build_interview_map(assessments, jd_profile.responsibilities),
        meta=meta,
    )
