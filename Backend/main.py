"""
ResumeIQ API.

Endpoints:
  GET  /health              liveness probe
  GET  /api/metrics         in-memory product metrics (no PII, aggregate only)
  POST /api/resume/parse    extract text from a resume (kept for debugging)
  POST /api/analyze         full resume<->JD analysis
"""

import logging
import os
import time
import uuid
from typing import Dict

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import Backend.analyzer as analyzer
from Backend.config import LLM_MODE, MAX_JD_CHARS, MAX_UPLOAD_BYTES, MIN_JD_CHARS
from Backend.resume_parser import extract_resume_text
from Backend.schemas import AnalysisResponse

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("resumeiq")

app = FastAPI(
    title="ResumeIQ API",
    description="AI-powered, evidence-grounded resume-to-job-description analysis. "
                "Decision-support for candidates — never an automated hiring decision.",
    version="1.0.0",
)

_DEFAULT_ORIGINS = "http://localhost:5173,http://localhost:4173,http://127.0.0.1:5173,http://127.0.0.1:4173"
_ALLOWED_ORIGINS = [o.strip() for o in os.getenv("RESUMEIQ_CORS_ORIGINS", _DEFAULT_ORIGINS).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory, aggregate-only metrics. No resume content is ever stored or logged.
_METRICS: Dict[str, float] = {
    "analyses_total": 0,
    "analyses_failed": 0,
    "extraction_llm": 0,
    "extraction_deterministic": 0,
    "latency_ms_sum": 0,
}


@app.get("/health")
@app.get("/")
def health_check():
    return {"status": "healthy", "service": "resumeiq", "llm_mode": LLM_MODE}


@app.get("/api/metrics")
def metrics():
    total = _METRICS["analyses_total"]
    return {
        "analyses_total": int(total),
        "analyses_failed": int(_METRICS["analyses_failed"]),
        "extraction_mode_counts": {
            "llm": int(_METRICS["extraction_llm"]),
            "deterministic": int(_METRICS["extraction_deterministic"]),
        },
        "avg_latency_ms": round(_METRICS["latency_ms_sum"] / total, 1) if total else 0,
    }


async def _read_resume(file: UploadFile) -> str:
    filename = file.filename or ""
    if not filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Please upload a PDF or DOCX resume.")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 5 MB.")

    try:
        text = extract_resume_text(filename, file_bytes)
    except Exception:
        raise HTTPException(status_code=422, detail="Could not read this file. Please upload a valid, text-based PDF or DOCX.")

    if not text.strip():
        raise HTTPException(status_code=422, detail="No readable text found. Please upload a text-based resume.")
    return text


@app.post("/api/resume/parse")
async def parse_resume(file: UploadFile = File(...)):
    filename = file.filename or "resume"
    resume_text = await _read_resume(file)
    # Log only metadata — never the content.
    logger.info("parse filename=%s chars=%d", filename, len(resume_text))
    return {"filename": filename, "character_count": len(resume_text), "resume_text": resume_text}


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_resume(file: UploadFile = File(...), jd_text: str = Form(...)):
    filename = file.filename or "resume"
    request_id = uuid.uuid4().hex[:12]
    started = time.perf_counter()

    jd_text = jd_text.strip()
    if len(jd_text) < MIN_JD_CHARS:
        raise HTTPException(status_code=400, detail=f"Job description is too short (minimum {MIN_JD_CHARS} characters).")
    if len(jd_text) > MAX_JD_CHARS:
        raise HTTPException(status_code=400, detail=f"Job description is too long (maximum {MAX_JD_CHARS} characters).")

    resume_text = await _read_resume(file)

    try:
        result = analyzer.analyze(resume_text, jd_text, filename)
    except RuntimeError as exc:
        _METRICS["analyses_failed"] += 1
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        _METRICS["analyses_failed"] += 1
        logger.exception("analyze failed request_id=%s", request_id)
        raise HTTPException(status_code=500, detail="Analysis failed unexpectedly. Please try again.")

    latency = (time.perf_counter() - started) * 1000
    _METRICS["analyses_total"] += 1
    _METRICS["latency_ms_sum"] += latency
    _METRICS["extraction_llm" if result.meta.extraction_mode == "llm" else "extraction_deterministic"] += 1
    logger.info(
        "analyze request_id=%s mode=%s score=%d latency_ms=%.0f resume_chars=%d jd_chars=%d",
        request_id, result.meta.extraction_mode, result.overall_score, latency, len(resume_text), len(jd_text),
    )
    return result
