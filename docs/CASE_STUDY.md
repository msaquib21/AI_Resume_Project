# ResumeIQ — Case study (portfolio narrative)

> How to use this page: it’s the story you tell in interviews. Every bracketed
> **[FILL]** needs your real data — do not present estimates as findings.

## Context

Program manager at Reliance (2 YOE) building toward AI PM roles. Built ResumeIQ
to close the "can you evaluate and ship AI, not just manage around it" gap —
by shipping a small, honest, measured AI product.

## The one-line story

**I built a resume↔JD analyzer that doesn't let the model make things up — and that tells you the exact questions your interview will probe, anchored to your own resume line.**

## Why this problem

Applying to PM roles, I noticed the advice loop: candidates don’t know which
requirements matter, and “ATS score” tools keyword-count without evidence or
honesty. Two hypotheses drove v1:

1. Candidates act on feedback tied to *their own lines*, not generic advice.
2. A trustworthy tool beats a magic benchmark — because false confidence is worse than no score.

## What I decided to build (and what I cut)

Cut ruthlessly to prove product judgment: **no agents, no RAG/vector DB, no
streaming** — a ~1.2k-token corpus doesn’t benefit; complexity would have added
failure modes, not insight. [FILL: 1–2 sentences from your user interviews — e.g.
“6 of 12 job seekers said X, so I Y”].

Kept as the core bet: **evidence-cited matching + deterministic scoring**, with
the LLM (qwen2.5:3b, local) restricted to *locating and phrasing* requirements.

## The decision that mattered most

First LLM integration made analysis *worse*: the 3B model emitted free-text
phrases (“experience with adobe analytics”) that the evidence matcher couldn’t
verify — grounding broke. Fix: **“LLM proposes, lexicon verifies.”** Output is
canonicalised onto ~200 curated terms (+ alias/morphology handling); anything
unmappable is dropped rather than guessed. Result: 100% groundedness on the dev
set, disclosed extraction mode in the API response
(`extraction_mode: llm | deterministic`), and a deterministic offline mode that
needs no model at all.

## Evaluation (dev set)

Hand-labeled n=4 resume/JD pairs (strong / moderate / weak / career-switcher),
pinned offline:

| Metric | Result |
|---|---|
| Skill-status accuracy | **100%** (25/25 labeled) |
| Groundedness (verbatim evidence or explicit absence) | **100%** |
| Score ordering (strong > moderate > weak) | holds |

And what it does **not** show: production accuracy, calibration of the weights,
or generalization — n=4 is a dev set, stated as such everywhere it appears.
[FILL: after your 30-resume calibration study, replace with MAE/Spearman vs human scores.]

## Shipped vs roadmap

Shipped: end-to-end flow, local LLM + cloud free-tier + deterministic offline modes,
evidence-cited report, deterministic rubric, **Interview Evidence Map**, PII-free
metrics endpoint, layout-verified parser, tests, this documentation.
Roadmap: calibration study, richer lexicon from consented JDs, JD-corpus RAG, deployed demo with disclosed inference.

## What I’d tell my past self

- Measure the *parser* separately from the *model* — most “AI quality” bugs were extraction bugs.
- Evaluations you can’t defend are worse than none; small-and-honest > big-and-fuzzy.
- For employment-adjacent products, “assists a human, never decides” is a feature, not a limitation.

## Interview FAQ (rehearse from this)

- **Why not RAG?** Corpus fits in context 50× over; retrieval adds latency/cost/failure for zero accuracy gain. v2 trigger: JD-corpus at scale.
- **Why deterministic scoring?** Reproducibility + auditability; the model interprets, the engine computes.
- **How do you evaluate?** Labeled dev set → accuracy/groundedness; next: human MAE calibration; by `/api/metrics` in live use.
- **Privacy posture?** In-memory, local inference, aggregate-only metrics; disclaimer shipped in the payload itself.
- **What failed first?** LLM-phrase grounding (fixed via lexicon gate); header-parsing swallowing bullets (“- Roadmapping and requirement writing” was eaten as a section header); morphology misses (“experiment” vs “experimentation” — fixed with alias + stem matching).
- **What’s different vs the 400 other resume-analyzer portfolios?** Three things: (1) deterministic scoring where the model interprets and the engine computes; (2) an Interview Evidence Map — probes anchored to the exact resume line being probed, classified strong/thin/exposed — diagnosing the interview, not just the document; (3) verified two- and single-column PDF parsing with zero duplicate lines, measured, not claimed.
- **What’s honest about it?** n=4 dev set; unvalidated weights; English-only; lexicon bounded by curated coverage; skills-list heuristic defeated by column-wrapped lines (occasional generous "matched"); LLM mode varies run-to-run (mitigated by lexicon canonicalisation); hosted demo sends data to a third-party API (disclosed; local mode doesn't).
