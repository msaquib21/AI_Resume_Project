import io

import fitz  # PyMuPDF
import pytest
from docx import Document

import Backend.analyzer as analyzer_module
from Backend.analyzer import analyze
from Backend.jd_parser import parse_jd
from Backend.resume_parser import extract_resume_text
from Backend.scoring import extract_years_experience, overall_from_dimensions

SAMPLE_RESUME = """
Ananya Sharma
ananya.sharma@example.com

SUMMARY
Product-minded program manager with 2 years of experience launching
analytics products at a large Indian conglomerate.

EXPERIENCE
- Led the roadmap for a weekly active users dashboard used by 40+ stakeholders
- Wrote SQL and Python pipelines powering cohort analysis across 18 months of CRM data
- Defined requirements and user stories for a self-serve reporting feature
- Partnered with engineering to ship a cohort analysis experiment improving
  retention by 12%
- Managed stakeholder alignment across 5 teams for a CRM migration

SKILLS
SQL, Python, Product discovery, User research, Agile, Roadmapping, Excel

EDUCATION
B.Tech, Computer Science, 2022
"""

SAMPLE_JD = """
Associate Product Manager, Growth

About the role
You will own analytics and experimentation for our consumer growth pod.

Responsibilities:
- Define product requirements and user stories with engineering
- Run A/B testing and experimentation to improve activation
- Partner with data science on cohort analysis and retention metrics
- Present findings to senior stakeholders

Required:
- SQL and Python
- Product discovery and user research
- A/B testing
- Roadmapping and requirement writing

Preferred:
- Experience with Adobe Analytics or similar product analytics tools
- Generative AI familiarity

Requirements:
- 2+ years of experience (internships count)
- Bachelor's degree in any field
"""


def test_extract_years_experience():
    assert extract_years_experience(SAMPLE_RESUME) == 2.0
    assert extract_years_experience("no numbers here") is None


def test_parse_jd_extracts_skills_and_sections():
    profile, expected_years = parse_jd(SAMPLE_JD)
    assert profile["job_title"]
    assert "sql" in profile["required_skills"]
    assert "a/b testing" in profile["required_skills"]
    assert "generative ai" in profile["preferred_skills"]
    assert profile["responsibilities"], "expected responsibility bullets"
    assert profile["qualifications"], "expected a degree qualification"


def test_analyze_end_to_end_offline(monkeypatch):
    # Tests must be deterministic and independent of a local Ollama service.
    monkeypatch.setattr(analyzer_module, "LLM_MODE", "offline")
    result = analyze(SAMPLE_RESUME, SAMPLE_JD, "sample.pdf")
    assert 0 <= result.overall_score <= 100
    assert result.disclaimer
    by_skill = {s.skill: s for s in result.skills}
    assert by_skill["sql"].status == "matched"
    assert by_skill["sql"].evidence  # evidence must be cited
    # generative ai is in preferred, not in resume -> missing preferred
    assert by_skill["generative ai"].status == "missing"
    # Deterministic and reproducible
    again = analyze(SAMPLE_RESUME, SAMPLE_JD, "sample.pdf")
    assert again.overall_score == result.overall_score


def test_pdf_roundtrip():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Resume test\nSQL and Python")
    data = doc.tobytes()
    text = extract_resume_text("r.pdf", data)
    assert "SQL" in text


def test_docx_roundtrip():
    buffer = io.BytesIO()
    doc = Document()
    doc.add_paragraph("Resume test")
    doc.add_paragraph("User research, roadmapping")
    doc.save(buffer)
    text = extract_resume_text("r.docx", buffer.getvalue())
    assert "User research" in text


def test_empty_pdf_rejected():
    with pytest.raises(ValueError):
        extract_resume_text("r.pdf", b"")

def test_interview_map_is_generated_and_grounded(monkeypatch):
    monkeypatch.setattr(analyzer_module, "LLM_MODE", "offline")
    from Backend.tests.test_backend import SAMPLE_RESUME, SAMPLE_JD
    result = analyze(SAMPLE_RESUME, SAMPLE_JD, "sample.pdf")
    assert result.interview_map, "expected interview probes"
    readiness = {p.readiness for p in result.interview_map}
    assert "exposed" in readiness  # a/b testing is missing -> must be flagged
    exposed = [p for p in result.interview_map if p.readiness == "exposed"]
    assert all(p.grounded_in == "" for p in exposed)  # honest: no fake evidence
    strong = [p for p in result.interview_map if p.readiness == "strong"]
    assert all(p.grounded_in for p in strong)  # strong probes anchored in resume

def test_ocr_extracts_text_from_scanned_pdf():
    rapidocr = pytest.importorskip("rapidocr_onnxruntime")
    # Build a synthetic image-only PDF containing known text.
    text_doc = fitz.open()
    page = text_doc.new_page()
    page.insert_text((72, 140), "RESUMEIQ OCR TEST PYTHON SQL", fontsize=32)
    pix = page.get_pixmap(dpi=200)
    img_doc = fitz.open()
    img_page = img_doc.new_page(width=page.rect.width, height=page.rect.height)
    img_page.insert_image(img_page.rect, pixmap=pix)
    image_bytes = img_doc.tobytes()

    text = extract_resume_text("scanned.pdf", image_bytes)
    lowered = text.lower()
    assert "ocr" in lowered or "resumeiq" in lowered
