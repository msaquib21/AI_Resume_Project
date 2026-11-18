# ResumeIQ — Product Requirements Document (v1, as-built)

**Author:** project owner (program manager → AI PM) · **Status:** v1 built, v2 planned
**Last updated:** Nov 2026

## 1. Problem & opportunity

Job seekers can’t reverse-engineer what a specific JD wants from their resume.
Existing tools either keyword-count (ATS scores) without evidence, or give generic
advice with no lineage. Opportunity: an **evidence-grounded, local-first** analysis
that shows *what* matched, *where*, and *what to do next* — useful and privacy-safe.

Non-goals: hiring decisions, employer-side ranking, salary negotiation, auto-apply,
any claim that a score = chance of getting hired.

## 2. Users (prioritized — decision-support, not a democratic list)

1. **Early-career/APM-aspirant in India (0–3 YOE)** — primary. Tech-adjacent applications, highest JD ambiguity, most sensitive to false confidence.
2. **Career switchers** — secondary. Need translation of experience across domains.
3. Job seekers in general — out of scope for v1 positioning (dilutes calibration).

## 3. User stories (P0)

Upload resume → paste JD → get a report where every requirement is mapped to
status (matched / partial / no-evidence) with a verbatim quote, an explained
weighted score, and prioritised, truthful actions (surface / rewrite / learn).
Privacy: local processing; no resume storage; metrics are aggregate-only.

## 4. Functional requirements (as built)

| ID | Requirement | Status |
|----|-------------|--------|
| FR-01 | PDF/DOCX upload, 5MB cap, text extraction incl. multi-column + tables + OCR fallback for scanned PDFs | ✅ built + tested |
| FR-02 | JD input validation (min 80 / max 20k chars) | ✅ |
| FR-03 | Structured JD profile (title, seniority, required/preferred skills, responsibilities, qualifications) — LLM or deterministic | ✅ both paths |
| FR-04 | LLM proposes → lexicon verifies (unmappable skills dropped) | ✅ built |
| FR-05 | Evidence-cited skill matching (aliases + morphology) | ✅ |
| FR-06 | Deterministic weighted score, renormalised for N/A dimensions | ✅ |
| FR-07 | Explicit disclaimer in payload + UI | ✅ |
| FR-08 | Grounded recommendations (learn/surface/rewrite), never fabricated achievements | ✅ |
| FR-09 | Aggregate metrics endpoint, PII-free logging | ✅ |
| FR-10 | Streaming progress (SSE) | ❌ cut — a <10s operation; restart complexity not justified in v1 |
| FR-11 | Accounts / history | ❌ cut — no persistence by design (privacy) |
| FR-12 | OCR for scanned PDFs | ✅ RapidOCR offline (free, ONNX); image-only PDFs now parse |
| FR-13 | Reproducible scoring (same input → same output) | ✅ temp 0 + seed + JD-profile cache; union with deterministic extraction |
| FR-14 | Experience inferred when "X years" is absent | ✅ date-range union across resume (education excluded) |
| FR-15 | PM telemetry surface for reviewers (groundedness, abstention, routing, cost) | ✅ in-app drawer in results view |

## 5. Decision log (the interview-relevant part)

- **Deterministic scoring, not LLM-invented score.** Reproducible, auditable, calibratable. The LLM locates/phrases requirements; it never produces the number.
- **LLM output through a lexicon gate.** Observed: qwen2.5:3b emits free-text phrases (“experience with adobe analytics”) that break verbatim evidence matching and inflate misses. Canonicalising onto ~200 curated terms (with observed-phrasing aliases, e.g. “user interviews” → `user research`) restored grounding. *This is the single best AI-judgment story in the project.*
- **No RAG / agents / vector store.** Corpus is ~1.2k tokens; complexity had negative ROI. Deferred to v2 with a stated trigger: JDs fetched per-company at scale (retrieval over a JD corpus), where RAG earns its keep.
- **“No evidence found” ≠ “candidate lacks skill.”** Reported explicitly; recommendations differentiate *learn* from *surface*.
- **Scoring weights are hypotheses** (40/25/20/10/5), configurable via env, to be calibrated against human-labeled resumes (MAE + rank correlation) before any external claim.
- **Local-first inference** (Ollama qwen2.5:3b) as the privacy default; “auto” mode falls back to deterministic extraction with disclosed `extraction_mode` in the response meta.

## 6. Metrics

North star (as a product): **time-to-actionable-insight** (upload → user acts on ≥1 recommendation).
Instrumentation shipped: `analyses_total`, `analyses_failed`, `extraction_mode_counts`, `avg_latency_ms` at `/api/metrics` (aggregate, no PII).
To add with users: recommendation acceptance rate, re-upload-after-edit rate, score calibration (MAE vs human), complaint/appeal rate.

## 7. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Score misread as hire probability | Disclaimer in payload+UI; candidate-facing positioning; no employer features |
| Small-model hallucinated JD extraction | Lexicon gate; deterministic fallback; mode disclosed in response |
| Scoring unfairness (prestige proxies) | No name/school/employer-prestige features in rubric; employment-domain caveats documented |
| Extraction garbage → garbage analysis | Parser isolated + tested separately from scorer; empty/image PDFs rejected with actionable errors |
| Overclaiming in portfolio | Eval section uses labeled dev set n=4, reported transparently as such |

## 8. Roadmap

**v1 (done):** end-to-end analysis, local + offline modes, eval harness, honest UI.
**v2:** calibration study (n≥30, human MAE), richer lexicon from consented JDs, optional LLM rewriting assist with strict no-fabrication constraints, RAG over JD corpus, deployed demo with disclosed inference.
**v3:** longitudinal mode — track a resume across applications; integrate with application tracker (Reliance PM background fits).

## 9. Interview Evidence Map (v1 differentiator)

Resume analyzers stop at the score. For every JD requirement and responsibility,
ResumeIQ emits the probe an interviewer will most plausibly ask, anchored to the
verbatim resume line being probed (or flagged as having no anchor), classified:

- **strong** — evidence exists; coach the candidate to defend it with depth (and metrics, if claimed).
- **thin** — listed/partial evidence; the first follow-up collapses it; prepare a STAR story with numbers.
- **exposed** — JD-critical, zero evidence; the interview’s opening target.

Deterministic templates (no model needed); generated from the same evidence-cited
assessments the score uses. Shipped in API (`interview_map`), UI (per-probe cards),
and tests. This is the piece that makes the project a *workflow* tool, not a
*document* tool — and a concrete answer to "what makes this different?".

## 10. Deployment reality (free)

Profile A local Ollama (privacy) · Profile B hosted + free cloud LLM (Groq /
Gemini / GitHub Models, OpenAI-compatible — one env var swap, `DEPLOYMENT.md`)
· Profile C hosted deterministic mode (no third party at all). Privacy disclosed
in-app and in docs; cold-start caveat documented. Recorded local demo (Loom)
as the always-on portfolio artifact.

## 11. Open questions

- Weight calibration: is responsibilities-alignment worth 20% vs experience? Needs human labels.
- Should “partial-only-in-skills-list” be capped harder? (Currently 0.5 credit.)
- India-specific JD phrasing coverage — needs 50 real JDs.
