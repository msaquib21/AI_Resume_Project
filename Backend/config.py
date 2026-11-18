"""
Environment-driven configuration for ResumeIQ.

Everything tunable lives here so the demo is reproducible and the
scoring rubric can be calibrated without touching code.
"""

import os

# ---------------------------------------------------------------------------
# LLM (optional). Default: "auto" — use local Ollama if reachable, otherwise
# fall back to the deterministic extractor. The product works fully offline.
#   auto    -> try Ollama, fall back gracefully (default)
#   ollama  -> require Ollama; fail with a clear error if unavailable
#   offline -> never call an LLM; deterministic extraction only
# ---------------------------------------------------------------------------
LLM_MODE = os.getenv("RESUMEIQ_LLM", "auto").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("RESUMEIQ_OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("RESUMEIQ_OLLAMA_TIMEOUT", "120"))
OLLAMA_CONNECT_TIMEOUT_SECONDS = float(os.getenv("RESUMEIQ_OLLAMA_CONNECT_TIMEOUT", "4"))

# ---------------------------------------------------------------------------
# Upload limits
# ---------------------------------------------------------------------------
MAX_UPLOAD_BYTES = int(os.getenv("RESUMEIQ_MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
MAX_JD_CHARS = int(os.getenv("RESUMEIQ_MAX_JD_CHARS", "20000"))
MIN_JD_CHARS = int(os.getenv("RESUMEIQ_MIN_JD_CHARS", "80"))

# ---------------------------------------------------------------------------
# Scoring rubric — INITIAL PRODUCT HYPOTHESIS, not validated truth.
# Calibrate against the labeled set in evaluation/ before trusting the numbers.
# Weights are renormalized automatically when a dimension is not applicable
# (e.g. JD lists no preferred skills).
# ---------------------------------------------------------------------------
WEIGHTS = {
    "required_skills": float(os.getenv("RESUMEIQ_W_REQUIRED", "40")),
    "relevant_experience": float(os.getenv("RESUMEIQ_W_EXPERIENCE", "25")),
    "responsibilities": float(os.getenv("RESUMEIQ_W_RESPONSIBILITIES", "20")),
    "preferred_skills": float(os.getenv("RESUMEIQ_W_PREFERRED", "10")),
    "qualifications": float(os.getenv("RESUMEIQ_W_QUALIFICATIONS", "5")),
}

# Seniority keyword -> (minimum years expected, label)
SENIORITY_EXPECTATIONS = {
    "intern": (0, "Intern"),
    "entry": (0, "Entry-level"),
    "junior": (0, "Junior"),
    "associate": (1, "Associate"),
    "mid": (3, "Mid-level"),
    "senior": (5, "Senior"),
    "lead": (6, "Lead"),
    "staff": (7, "Staff"),
    "principal": (8, "Principal"),
}

DEFAULT_EXPECTED_YEARS = 2  # used when the JD gives no seniority signal
