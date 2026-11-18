# ResumeIQ — Evidence-grounded AI resume ↔ job-description analysis

> A local-first, explainable AI product that tells a job seeker **how well their
> resume matches a specific job description, why, and what to fix** — with every
> claim tied to verbatim evidence from their own document.

ResumeIQ is a portfolio project built as an **AI Product Manager case study**:
it was scoped, evaluated and documented like a real product, not shipped as a
demo. It is deliberately *not* an LLM wrapper.

---

## The problem

Early-career job seekers in India apply to roles blindly. Two failure modes
dominate: (1) they can't tell **which resume gaps actually matter** for a given
JD, and (2) they get generic feedback ("make it ATS-friendly") with no evidence.
ResumeIQ turns a resume + JD into an **auditable alignment report**.

## What it does

Paste a job description, upload a resume (PDF/DOCX). ResumeIQ:

1. **Parses** the resume — layout-aware PDF extraction (multi-column + tables) and order-preserving DOCX extraction.
2. **Extracts structured requirements** from the JD — title, seniority, required vs preferred skills, responsibilities, qualifications (local LLM via Ollama with a deterministic fallback, or offline mode).
3. **Matches against the resume with cited evidence** — every matched/partial skill quotes the exact resume line; absences are reported as “no evidence found”, never invented.
4. **Scores deterministically** — a transparent, configurable rubric (skills 40%, experience 25%, responsibilities 20%, preferred 10%, qualifications 5%). The model never invents the score.
5. **Recommends grounded actions** — learn it / surface it / rewrite it — each tied to the resume line it references.
6. **Explains itself** — dimension breakdown with weights, extraction mode, latency, request ID, and an explicit “this is decision support, not a hiring probability” disclaimer in the payload.

## Architecture (deliberately simple)

```
React/Vite frontend  ──►  FastAPI  ──►  resume_parser (PyMuPDF / python-docx)
        │                                    │
        │                                    ▼
        │                              jd_parser / llm (qwen2.5:3b via Ollama)
        │                                    │  LLM proposes requirements;
        │                                    │  lexicon verifies — unmappable
        │                                    ▼  skills are dropped, not guessed
        │                              evidence matcher (morphology + aliases)
        │                                    │
        │                                    ▼
        │                              scoring engine (deterministic, weighted)
        │                                    │
        ◄──  JSON report  ◄─────────  analyzer (gaps + grounded recommendations)
```

**Why no RAG / no agents / no vector DB?** The corpus is one resume (~1.2k tokens)
and one JD. Retrieval would add latency, cost and failure modes for zero accuracy
gain. The interesting problem here is **trust**: evidence citation, honest
absence reporting, deterministic scoring, and reproducible evaluation — which is
what we built and measure instead. The v2 path (RAG over a corpus of JDs,
multi-document candidate memory) is sketched in `docs/PRD.md`.

## Quickstart

Prereqs: Python 3.12+, Node 20+, optional Ollama with `qwen2.5:3b`.

```powershell
# backend (from repo root)
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\uvicorn Backend.main:app --port 8000

# frontend (separate terminal)
cd frontend
npm install
npm run dev          # http://localhost:5173
```

Offline / no-LLM mode: set `RESUMEIQ_LLM=offline` (backend). Fully deterministic.

Useful scripts: `.venv\Scripts\python.exe -m pytest Backend/tests -q` and
`$env:RESUMEIQ_LLM="offline"; .venv\Scripts\python.exe evaluation\evaluate.py`
(see `evaluation/report.md`).

## API

| Endpoint | Purpose |
|---|---|
| `GET /health` | liveness + LLM mode |
| `GET /api/metrics` | aggregate, PII-free product metrics (counts, avg latency, extraction-mode split) |
| `POST /api/resume/parse` | raw text extraction (debug) |
| `POST /api/analyze` | full analysis (multipart: `file` + `jd_text`) → typed JSON report |

## Evaluation

Hand-labeled dev set (`evaluation/cases.py`, 4 synthetic-but-realistic resume/JD
pairs across match strengths). Deterministic, pinned offline:

| Metric | Result |
|---|---|
| Skill-status accuracy vs hand labels | **100%** (25/25) |
| Groundedness (claim → verbatim evidence or explicit absence) | **100%** |
| Unit/integration tests | 6 passed |

Reproduce: `.venv\Scripts\python.exe evaluation\evaluate.py` → `evaluation/report.md`.

**Known limitations (honest list):** lexical matching with aliases + light
morphology misses paraphrases; the 3B model’s JD extraction varies run-to-run
(temperature 0.1 but small models drift — we canonicalise its output through the
lexicon to protect grounding); scoring weights are an unvalidated hypothesis
(calibration plan in `docs/PRD.md`); hand-labeled n=4 is a dev set, not a
benchmark claim; India-market bias untested at scale; English resumes only.

## Privacy & trust stance

- Processing is in-memory; nothing is persisted or logged beyond lengths and metadata.
- Local inference by default — resumes never leave the machine.
- Aggregate metrics only; no PII.
- Candidate-facing by design: never used to rank or auto-reject people.
- The report payload itself carries the “not a hiring probability” disclaimer.

## Repository map

```
Backend/            FastAPI app: parser, jd_parser, llm, evidence, scoring, analyzer, main
  tests/            pytest suite (parsing round-trips, JD parsing, end-to-end analysis)
frontend/           React + Vite + TS — upload → JD → live report (typed API client)
evaluation/         Labeled cases + evaluate.py → report.md; sample resume/JD/PDF
docs/               PRD.md (product requirements, decisions, roadmap) · CASE_STUDY.md
```

## Status & roadmap

Working end-to-end: upload → LLM/deterministic JD extraction → evidence-cited
analysis → weighted score → gaps → grounded recommendations → local privacy mode.
Next: user calibration study on the scoring rubric (n≥30 resumes, human-vs-score
MAE), consented anonymized eval set, deployed demo with disclosed inference mode.
