"""
Pydantic v2 contracts for ResumeIQ.

The API response is a strict contract: the frontend renders exactly
what these models describe, and the evaluation harness asserts on them.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class SkillAssessment(BaseModel):
    skill: str
    requirement: Literal["required", "preferred"]
    status: Literal["matched", "partial", "missing"]
    # Direct line from the resume, verbatim. Empty when there is no evidence.
    # Never invented — absence of evidence is reported as missing/partial.
    evidence: str = ""
    note: str = ""


class DimensionScore(BaseModel):
    name: str
    # None = not applicable for this JD (weight redistributed, not zero-filled).
    score: Optional[float] = Field(default=None, ge=0, le=100)
    weight: float
    detail: str = ""


class Recommendation(BaseModel):
    type: Literal["surface", "rewrite", "learn", "clarify"]
    title: str
    detail: str
    # Grounded in the actual resume whenever possible. Empty when the
    # recommendation is about something the resume lacks entirely.
    evidence: str = ""


class JDProfile(BaseModel):
    job_title: str = ""
    seniority: str = ""
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    qualifications: List[str] = Field(default_factory=list)


class AnalysisMeta(BaseModel):
    request_id: str
    # How the JD/resume profile was produced: local LLM vs deterministic.
    # Surfaced honestly in the UI — users deserve to know.
    extraction_mode: Literal["llm", "deterministic"]
    model: Optional[str] = None
    latency_ms: int


class AnalysisResponse(BaseModel):
    filename: str
    overall_score: int = Field(ge=0, le=100)
    verdict: str
    # Explicit reminder: this is a decision-support signal, not a
    # probability of being hired. Carried in the payload, not just the UI.
    disclaimer: str
    dimensions: List[DimensionScore]
    skills: List[SkillAssessment]
    jd_profile: JDProfile
    gaps: dict = Field(default_factory=dict)  # critical / important / optional
    recommendations: List[Recommendation]
    meta: AnalysisMeta
