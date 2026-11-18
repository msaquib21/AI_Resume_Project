"""
Interview Evidence Map — the step every template resume analyzer skips.

Scores tell a candidate where they stand; this tells them what an
interviewer will actually probe, anchored to the exact resume line that
will be probed, and where the candidate is exposed (JD-critical, no
evidence). Deterministic by design — no model required, fully reproducible.
"""

import re
from typing import List

from Backend.schemas import InterviewProbe, SkillAssessment

_MARKER_RE = re.compile(r"(\d+%|\d+\s*(?:x\b|users|customers|teams|markets))", re.I)


def _clip(text: str, limit: int = 140) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _probe_for_skill(a: SkillAssessment) -> InterviewProbe:
    if a.status == "matched":
        anchored = _clip(a.evidence, 110)
        metric = bool(_MARKER_RE.search(a.evidence))
        question = (
            f"Walk me through “{anchored}” — how did you work with {a.skill} day to day, "
            f"what trade-offs did you make, and what broke?"
            if not metric else
            f"“{anchored}” claims measurable impact. What was the baseline, what did you change, and how did you verify {a.skill} moved the number?"
        )
        return InterviewProbe(
            question=question,
            targets=a.skill,
            grounded_in=a.evidence,
            readiness="strong",
            why="The JD requires this and your resume anchors it — expect deep probing on exactly this claim.",
        )
    if a.status == "partial":
        return InterviewProbe(
            question=(
                f"You list {a.skill}, but I don't see it demonstrated in context — "
                f"give me one specific project with scope, your role, and the outcome."
            ),
            targets=a.skill,
            grounded_in=a.evidence,
            readiness="thin",
            why="Skills-list-only claims collapse under the first follow-up. Prepare a STAR story with numbers.",
        )
    # missing
    severity = "required" if a.requirement == "required" else "preferred"
    return InterviewProbe(
        question=(
            f"The JD makes {a.skill} a hard requirement and your resume shows no evidence. "
            f"What's your honest level — and what have you shipped or learned that counts?"
        ),
        targets=a.skill,
        grounded_in="",
        readiness="exposed",
        why=f"This is a {severity} gap. If unaddressed, it is the first thing an interviewer drills.",
    )


def _star_probe(responsibility: str) -> InterviewProbe:
    return InterviewProbe(
        question=(
            f"The JD expects you to “{_clip(responsibility)}” — "
            f"give me a STAR story showing exactly this: situation, your specific actions, result."
        ),
        targets="JD responsibility",
        grounded_in="",
        readiness="thin",
        why="Responsibilities are the interview's anchor — map each one to a story now, not in the hallway.",
    )


def build_interview_map(
    skills: List[SkillAssessment],
    responsibilities: List[str],
    limit: int = 8,
) -> List[InterviewProbe]:
    probes: List[InterviewProbe] = []

    # Exposed first — these lose interviews.
    exposed = [a for a in skills if a.status == "missing" and a.requirement == "required"]
    thin = [a for a in skills if a.status == "partial"]
    strong = [a for a in skills if a.status == "matched" and a.requirement == "required"]

    probes += [_probe_for_skill(a) for a in exposed]
    probes += [_probe_for_skill(a) for a in thin]
    # Strong probes: the 2 strongest anchors — claim-defense practice.
    probes += [_probe_for_skill(a) for a in strong[:2]]
    # Up to 2 STAR probes on JD responsibilities with no clear anchor.
    for resp in responsibilities[:2]:
        probes.append(_star_probe(resp))

    return probes[:limit]
