"""
Generate ResumeIQ — AI PM Case Study (Word document, print-ready).

Run: .venv\\Scripts\\python.exe docs\\generate_portfolio_doc.py
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime

ACCENT = "0E6B52"       # deep green
ACCENT_DEEP_RGB = RGBColor(0x0A, 0x53, 0x40)
PAPER = "FFFFFF"
TINT = "EAF3EE"         # light green tint
AMBER = "FAF1E3"
INK = RGBColor(0x21, 0x1F, 0x1C)
MUTED = RGBColor(0x6F, 0x6D, 0x63)
ACCENT_RGB = RGBColor(0x0E, 0x6B, 0x52)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

SEIF = "Georgia"
SANS = "Calibri"


def set_cell_bg(cell, hex_fill: str) -> None:
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), hex_fill)
    shading.set(qn("w:val"), "clear")
    cell._tc.get_or_add_tcPr().append(shading)


def set_cell_margins(cell, top=100, bottom=100, left=140, right=140) -> None:
    tcMar = OxmlElement("w:tcMar")
    for tag, value in (("top", top), ("bottom", bottom), ("start", left), ("end", right)):
        element = OxmlElement(f"w:{tag}")
        element.set(qn("w:w"), str(value))
        element.set(qn("w:type"), "dxa")
        tcMar.append(element)
    cell._tc.get_or_add_tcPr().append(tcMar)


def set_repeat_table_header(row) -> None:
    trPr = row._tr.get_or_add_trPr()
    tblHeader = OxmlElement("w:tblHeader")
    trPr.append(tblHeader)


def set_repeat_cant_split(row) -> None:
    trPr = row._tr.get_or_add_trPr()
    cantSplit = OxmlElement("w:cantSplit")
    trPr.append(cantSplit)


def style_base(doc: Document) -> None:
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = SANS
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = INK
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.15

    def _style(name, font, size, bold=True, color=ACCENT_RGB, before=18, after=7, line=1.15):
        style = styles[name]
        style.font.name = font
        style.font.size = Pt(size)
        style.font.bold = bold
        style.font.color.rgb = color
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.line_spacing = line
        style.paragraph_format.keep_with_next = True

    _style("Title", SEIF, 40, True, INK, before=6, after=10)
    _style("Heading 1", SEIF, 22, True, RGBColor(0x21, 0x1F, 0x1C), before=26, after=10)
    _style("Heading 2", SEIF, 14.5, True, ACCENT_RGB, before=16, after=6)
    _style("Heading 3", SANS, 11.5, True, INK, before=12, after=4)


def add_page_field(paragraph) -> None:
    fldChar_begin = OxmlElement("w:fldChar")
    fldChar_begin.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.set(qn("xml:space"), "preserve")
    instrText.text = "PAGE"
    fldChar_end = OxmlElement("w:fldChar")
    fldChar_end.set(qn("w:fldCharType"), "end")
    run = paragraph.add_run()
    run._r.append(fldChar_begin)
    run._r.append(instrText)
    run._r.append(fldChar_end)


def set_header_footer(doc: Document) -> None:
    section = doc.sections[0]
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)

    header_p = section.header.paragraphs[0]
    header_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = header_p.add_run("RESUMEIQ  ·  AN AI PRODUCT MANAGEMENT CASE STUDY")
    run.font.name = SANS
    run.font.size = Pt(7.5)
    run.font.color.rgb = MUTED
    run.font.bold = True

    footer_p = section.footer.paragraphs[0]
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer_p.add_run("Mohammad Saquib  ·  ResumeIQ  ·  Decision support, not a hiring probability  ·  Page ")
    run.font.name = SANS
    run.font.size = Pt(7.5)
    run.font.color.rgb = MUTED
    add_page_field(footer_p)


def hr(doc: Document) -> None:
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(2)
    paragraph.paragraph_format.space_after = Pt(10)
    pPr = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "8")
    bottom.set(qn("w:space"), "2")
    bottom.set(qn("w:color"), ACCENT)
    borders.append(bottom)
    pPr.append(borders)


def callout(doc: Document, text: str, tint: str = TINT) -> None:
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_bg(cell, tint)
    set_cell_margins(cell, top=120, bottom=120, left=200, right=200)
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.add_run(text)
    run.font.name = SEIF
    run.font.italic = True
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0x14, 0x44, 0x36)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def make_table(doc: Document, headers, rows, widths, header_fill: str = ACCENT) -> None:
    table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for i, (header, width) in enumerate(zip(headers, widths)):
        cell = table.cell(0, i)
        cell.width = Inches(width)
        set_cell_bg(cell, header_fill)
        set_cell_margins(cell)
        paragraph = cell.paragraphs[0]
        paragraph.paragraph_format.space_after = Pt(0)
        run = paragraph.add_run(header)
        run.font.name = SANS
        run.font.bold = True
        run.font.size = Pt(9)
        run.font.color.rgb = WHITE
    for r, row in enumerate(rows):
        tr = table.rows[r + 1]
        set_repeat_cant_split(tr)
        for c, (value, width) in enumerate(zip(row, widths)):
            cell = table.cell(r + 1, c)
            cell.width = Inches(width)
            set_cell_margins(cell)
            if r % 2 == 1:
                set_cell_bg(cell, "F7F6F1")
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(0)
            is_lead = c == 0
            run = paragraph.add_run(value)
            run.font.name = SANS
            run.font.size = Pt(8.5)
            run.font.bold = is_lead
            run.font.color.rgb = INK
    set_repeat_table_header(table.rows[0])
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def bullets(doc: Document, items) -> None:
    for item in items:
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.left_indent = Inches(0.18)
        paragraph.paragraph_format.space_after = Pt(3)
        paragraph.paragraph_format.line_spacing = 1.15
        run = paragraph.add_run("—  ")
        run.font.color.rgb = ACCENT_RGB
        run.font.bold = True
        if isinstance(item, tuple):
            lead, rest = item
            lead_run = paragraph.add_run(lead)
            lead_run.font.bold = True
            lead_run.font.name = SANS
            lead_run.font.size = Pt(10)
            paragraph.add_run(rest)
        else:
            paragraph.add_run(item)


def ask(doc: Document, number: int, question: str, answer: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(10)
    paragraph.paragraph_format.space_after = Pt(3)
    paragraph.paragraph_format.keep_with_next = True
    run = paragraph.add_run(f"Q{number:02d}.  {question}")
    run.font.name = SEIF
    run.font.bold = True
    run.font.size = Pt(11.5)
    run.font.color.rgb = ACCENT_DEEP_RGB
    answer_paragraph = doc.add_paragraph()
    answer_paragraph.paragraph_format.left_indent = Inches(0.28)
    answer_paragraph.paragraph_format.space_after = Pt(8)
    answer_paragraph.paragraph_format.line_spacing = 1.18
    body = answer_paragraph.add_run(answer)
    body.font.size = Pt(9.5)


doc = Document()
style_base(doc)
set_header_footer(doc)
hr_none = True

# ================= COVER =================
for _ in range(2):
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(2)
run = p.add_run("AN AI PRODUCT MANAGEMENT CASE STUDY")
run.font.name = SANS
run.font.bold = True
run.font.size = Pt(9)
run.font.color.rgb = ACCENT_RGB

title = doc.add_paragraph()
title.style = doc.styles["Title"]
title.add_run("ResumeIQ")

sub = doc.add_paragraph()
sub.paragraph_format.space_after = Pt(16)
run = sub.add_run("Evidence-grounded resume-to-job-description intelligence — a product built like it has an owner.")
run.font.name = SEIF
run.font.italic = True
run.font.size = Pt(15.5)
run.font.color.rgb = MUTED

hr(doc)

tags = doc.add_paragraph()
tags.paragraph_format.space_after = Pt(2)
run = tags.add_run("EVIDENCE-GROUNDED  ·  DETERMINISTIC RUBRIC  ·  LOCAL-FIRST  ·  FREE-TIER CLOUD  ·  $0 RUN COST")
run.font.name = SANS
run.font.bold = True
run.font.size = Pt(8.5)
run.font.color.rgb = ACCENT_RGB

details = [
    ("Author", "Mohammad Saquib — Program Manager, Reliance; targeting AI PM roles (Adobe India)"),
    ("Product type", "Decision-support candidate tool (not a hiring system; not an ATS)"),
    ("Repository", "AI_Resume_Project — v1, evaluated, documented, deployed (Vercel + Render, free tier)"),
    ("Live profiles", "Local privacy mode (Ollama qwen2.5:3b) · free-tier hosted demo (Groq openai/gpt-oss-120b) · deterministic-only mode"),
    ("Snapshot date", datetime.date(2026, 11, 18).strftime("%d %B %Y")),
]
for label, value in details:
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(3)
    lead = paragraph.add_run(f"{label:14}")
    lead.font.name = SANS
    lead.font.bold = True
    lead.font.size = Pt(9)
    lead.font.color.rgb = ACCENT_RGB
    body = paragraph.add_run("  " + value)
    body.font.size = Pt(9.5)
    body.font.name = SANS

for _ in range(2):
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
callout(doc, "The one-line story — I built a resume analyzer that refuses to make things up, then measured, proved, disclosed and deployed exactly where it works and where it doesn’t.", TINT)

doc.add_page_break()

# ================= CONTENTS =================
doc.add_heading("Contents", level=1)
contents = [
    ("Part 1", "What this is, in simple words"),
    ("Part 2", "How it works — the six-stage pipeline"),
    ("Part 3", "Tech stack, deep dive — every component and why it exists"),
    ("Part 4", "What we deliberately did NOT build — and why"),
    ("Part 5", "Is this legitimately an “AI project”? (The honest inventory)"),
    ("Part 6", "The honesty ledger — measured, not claimed"),
    ("Part 7", "25 questions a senior PM will ask — with real answers"),
    ("Part 8", "Limitations, risks and the roadmap I would defend"),
    ("Appendix", "How to reproduce every number in this document"),
]
for part, desc in contents:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    lead = p.add_run(f"{part:9}  ")
    lead.font.name = SANS
    lead.font.bold = True
    lead.font.size = Pt(10)
    lead.font.color.rgb = ACCENT_RGB
    body = p.add_run(desc)
    body.font.name = SEIF
    body.font.size = Pt(10)
hr(doc)
p = doc.add_paragraph()
run = p.add_run("Reading time: ~25 minutes. If you only read Part 5 and Part 7, you have the whole argument.")
run.font.italic = True
run.font.size = Pt(9)
run.font.color.rgb = MUTED

# ================= PART 1 =================
doc.add_heading("Part 1 — What this is, in simple words", level=1)

callout(doc, "ResumeIQ reads your resume and the job description you are targeting, then tells you — with the exact resume line as proof — what matches, what does not, and the questions you will be asked in the interview.")

doc.add_heading("The problem, stated like a PM", level=2)
p = doc.add_paragraph()
p.add_run("Every candidate targeting an AI-era role hits the same wall. Paste your resume into a generic analyzer and you get one of two useless outputs: a vague compliment (“great experience!”) or an unexplained percentage (64% match — of what, against what, judged how?). Applicant tracking systems hide their logic. LLM-based tools confidently invent skills you never had. Neither tells you the only thing that matters after you apply: what an interviewer will actually probe, and where your resume does not yet answer it.")

doc.add_heading("What ResumeIQ does about it — 30 seconds", level=2)
bullets(doc, [
    ("You upload a resume (PDF or DOCX).", " Two-column, single-column, or a scanned image — all three are parsed locally, including tables and OCR."),
    ("You paste the job description.", " Any length, formatting allowed — the system splits must-haves from nice-to-haves."),
    ("It returns five things:", " (1) a deterministic match score with the weight of every dimension disclosed; (2) a skills-versus-requirements panel where every claim carries a verbatim line from your own resume — or the honest words “no evidence found”; (3) concrete actions (learn it, or surface it), never empty advice; (4) an Interview Evidence Map — the exact probes an interviewer will ask, anchored to the exact resume line being probed, tagged strong / thin / exposed; (5) a telemetry strip showing how the machine ran — groundedness, abstention, inference routing, cost — because a trustworthy AI product shows its working."),
])

doc.add_heading("The one-sentence positioning", level=2)
callout(doc, "ResumeIQ is decision support for candidates — not a hiring system, not an ATS, and it never emits a probability of getting the job. A score here is an explanation you can audit, not a verdict you must obey.", AMBER)

doc.add_heading("Where it wins and where it refuses", level=2)
make_table(
    doc,
    ["What users hate", "ResumeIQ’s answer"],
    [
        ("“64% match — of what?”", "Every sub-score is itemised with weights: required skills 44%, experience 28%, responsibilities 22%, qualifications 6%. Change the weights and the score moves — it is a rubric, not a mood."),
        ("Drenched in adjectives, no proof", "Every assessment cites the verbatim resume line it is based on. No line exists? It says so — it does not improvise."),
        ("Useless “improve your resume” advice", "Actions reference your lines: “prove X with impact — this bullet lists it, add the outcome”. No blank-page endings."),
        ("“Am I even interviewable for this?”", "The Interview Evidence Map shows which gaps are first-round killers (exposed), which fold under one follow-up (thin), and which you can defend cold (strong)."),
        ("One-size scoring for every role", "Rubric weights are documented, configurable, and explicitly labelled an unvalidated hypothesis — calibration is the roadmap, not a marketing claim."),
    ],
    [2.6, 4.1],
)

# ================= PART 2 =================
doc.add_heading("Part 2 — How it works, stage by stage", level=1)
p = doc.add_paragraph()
p.add_run("The pipeline is deliberately boring. Boring is how you get a product you can explain in an interview without hand-waving. Six stages, one direction, no loops, no agents pretending to be a committee:")

make_table(
    doc,
    ["#", "Stage", "What happens", "Is AI involved?"],
    [
        ("1", "Parse the resume", "PyMuPDF extracts text while preserving multi-column reading order and table content (row-level de-duplication against the block pass); python-docx preserves DOCX paragraph/table order. If the PDF is image-only (a scan), RapidOCR — an offline ONNX neural-net — reads it at 200 DPI.", "Yes — OCR (ONNX), only for scans"),
        ("2", "Build the JD profile", "Sections are split heuristically. An LLM (local Ollama qwen2.5:3b, or hosted Groq openai/gpt-oss-120b) proposes job title, seniority, required/preferred skills, responsibilities, qualifications. Output is validated against a Pydantic schema and canonicalised onto a ~200-term curated skill lexicon — anything unmappable is dropped, never guessed.", "Yes — LLM, constrained"),
        ("3", "Match skills to evidence", "Pure Python: alias-aware, morphology-tolerant term matching (“user interviews” counts as user research). Every hit is classified matched (demonstrated in context) / partial (skills-list only) / missing (no evidence found — reported, not invented).", "No"),
        ("4", "Score the rubric", "Weighted dimensions, renormalised when a dimension is N/A (e.g. no experience signal found). The LLM does not touch this stage. Same input, same number — forever.", "No — determinism is the feature"),
        ("5", "Find gaps and ground actions", "Missing/partial required skills become a grouped hard-gaps triage card and targeted rewrite actions — each grounded in your lines, not in generic advice.", "No"),
        ("6", "Generate the interview map", "From the same evidence-cited assessments, derive the probes an interviewer will most plausibly ask — strong / thin / exposed — anchored to the exact resume line being probed (or flagged as unanchored).", "No"),
    ],
    [0.35, 1.15, 4.35, 1.35],
)
p = doc.add_paragraph()
run = p.add_run("Notice where AI is and is not: the model may interpret language (stage 2) and read pixels (stage 1, scans only). It may not score, may not invent evidence, may not decide your worth. That boundary is the product.")
run.font.bold = True
run.font.color.rgb = ACCENT_RGB

# ================= PART 3 =================
doc.add_heading("Part 3 — Tech stack, deep dive", level=1)

doc.add_heading("3.1  The moving parts, and why each exists", level=2)
make_table(
    doc,
    ["Layer", "Technology", "Why it, and what it replaced"],
    [
        ("Frontend", "React 19 + TypeScript + Vite", "Typed client mirrors backend schemas 1:1 — the API contract is the UI contract. Vite: sub-second dev, instant HMR. No framework bloat, no CSS-in-JS runtime."),
        ("API", "FastAPI + Pydantic v2", "Typed request/response contracts, validation at the boundary, clean 422s, automatic docs. Alternatives (Django REST, Flask + manual validation) add weight or remove guarantees."),
        ("Resume parsing (PDF)", "PyMuPDF (fitz)", "Only reliable way to recover multi-column reading order and table geometry from PDFs. pdfplumber and naive text extraction mangle the two-column layouts most Indian resume templates use."),
        ("Resume parsing (DOCX)", "python-docx", "Preserves paragraph/table order — the same layouts exported to Word."),
        ("OCR (scanned PDFs)", "RapidOCR on onnxruntime", "Scanned resumes are a large, unglamorous segment of the target market. RapidOCR runs fully offline on CPU — no Tesseract system binary, no cloud OCR bill, free forever."),
        ("JD understanding", "LLM, constrained", "Local default: Ollama qwen2.5:3b (privacy, free). Hosted demo: Groq openai/gpt-oss-120b (free tier, JSON mode, ~1.7 s). Chosen for: structured-output reliability, cost ($0), acceptable latency. Rejected: GPT-4-class endpoints (cost), embeddings-only approaches (no phrasing ability), prompt-only without schema (hallucination)."),
        ("Evidence matching", "Custom lexicon + aliases + morphology", "~200 curated tech/PM terms with observed-phrasing aliases (“user interviews” → user research). Deterministic, explainable, measurable. A missing term surfaces as no-evidence — never as a crash or a guess."),
        ("Weighted scoring", "Pure Python", "40/25/20/10/5 initial weighting (skills / experience / responsibilities / preferred / qualifications), renormalised for N/A dimensions. Integer output, stable across runs, exposed in the payload with weights. The LLM is constitutionally barred from this stage."),
        ("JD profile cache", "sha256 of normalised JD text", "Same JD → same profile → same score, bit-for-bit. Also collapses latency from seconds to ~0 ms on repeats. Stores JD-derived fields only — never resume text."),
        ("Evaluation", "pytest + labeled dev set", "4 synthetic-but-realistic cases, 25 hand-labelled skill statuses. Deterministic, offline, reproducible. Publishable numbers: 100% skill-status accuracy (25/25), 100% groundedness."),
        ("Deployment", "Vercel (frontend) + Render (API, free)", "The honest free path: no credit card, no always-on container costs. Cold starts (~30 s) documented on the demo page itself."),
        ("Privacy", "In-memory processing only", "No DB, no accounts, no resume content logged — even local mode. /api/metrics exposes aggregates only. The one artefact that could leak (resume) is never persisted."),
    ],
    [1.05, 1.5, 4.15],
)

doc.add_heading("3.2  The folder map (for the technically curious interviewer)", level=2)
make_table(
    doc,
    ["Path", "Responsibility"],
    [
        ("Backend/main.py", "HTTP surface: /health, /api/metrics, /api/resume/parse, /api/analyze. CORS, upload limits, error mediation, nothing else."),
        ("Backend/resume_parser.py", "PDF/DOCX → clean text. Column-aware ordering, table de-duplication, OCR fallback, duplicate-line removal."),
        ("Backend/jd_parser.py", "Deterministic section splitting + lexicon extraction — the always-available fallback the LLM can never silently override."),
        ("Backend/llm.py", "Provider-agnostic LLM call (Ollama or any OpenAI-compatible endpoint). Temperature 0, fixed seed, JD-profile cache, browser-UA hardening (Groq/Cloudflare block naive clients), never raises into the user path."),
        ("Backend/evidence.py", "Canonicalisation (“node.js” ≡ node) and morphology-tolerant evidence search with verbatim line return."),
        ("Backend/scoring.py", "The rubric. Renormalisation, date-range experience inference, verdict labels."),
        ("Backend/analyzer.py", "Orchestrator: parse → profile (LLM with deterministic fallback) → match → score → gaps → grounded recommendations → interview map."),
        ("Backend/interview_map.py", "Probe generation: exposed first (they lose interviews), then thin, then strong anchors."),
        ("frontend/src/App.tsx", "The entire UX: hero → analyzer → verdict strip → skills strips → swipeable decks → telemetry drawer."),
        ("evaluation/", "cases.py, evaluate.py, report.md — the labeled set and its published results."),
        ("docs/", "PRD (decision log), CASE_STUDY (interview narrative), PRD vs. reality."),
        ("DEPLOYMENT.md", "€0 deployment guides for Groq, Gemini, GitHub Models, OpenRouter + local-privacy mode + cold-start disclosure copy."),
    ],
    [1.7, 5.0],
)

# ================= PART 4 =================
doc.add_heading("Part 4 — What we deliberately did NOT build, and why", level=1)
p = doc.add_paragraph()
p.add_run("Every AI PM is asked: “why not RAG? why not agents? why not fine-tune?” Here are the real answers, in the order they come up:")
make_table(
    doc,
    ["The obvious ask", "Why we said no — the senior answer"],
    [
        ("RAG / vector database over JDs", "The retrieval corpus is a single JD and a single resume — ~1,200 tokens. Retrieval adds latency, a failure mode (bad chunks, bad ranking), and an operating burden, in exchange for exactly nothing in accuracy. The hard problem here is trust, not search. If/when ResumeIQ grows a corpus (thousands of JDs), JD-corpus RAG becomes interesting — it is on the roadmap, labelled as such, not bolted on for résumé-bullet value."),
        ("LangGraph / multi-agent orchestration", "A linear pipeline dressed up as a committee is still a linear pipeline — with extra failure modes and latency. Five stages, one direction, each stage inspectable. “Agentic” is not a virtue when the task is deterministic most of the way."),
        ("Fine-tuning on “resume data”", "Needs a labeled corpus we do not have, money we do not want to spend, and it would make the system less auditable — the opposite of the product thesis. The lexicon gate gets us most of the precision fine-tuning would, at zero cost."),
        ("SSE / streaming LLM output", "Perceived-performance problem, different solution: the loading screen (5 staged steps, elapsed timer) plus a JD-profile cache (repeat analyses ~0 ms). Streaming raw JSON tokens would leak implementation detail for no user benefit."),
        ("Accounts, cloud DB, auth", "Resume PII is radioactive. Storing it creates breach surface, DPDPA/GDPR obligations, and user anxiety — with zero product benefit in v1. Nothing stored means nothing to leak, ever. A deletion policy you can state in one sentence is the privacy architecture."),
        ("GPT-4/Claude-class frontier models", "Cost per 1000 analyses would 100x for a JSON-extraction task a constrained OSS model handles in 1.7 s for $0. Free tier + deterministic fallback is the correct trade at portfolio-project economics — and the routing logic is provider-agnostic by design."),
        ("Microservices / Kubernetes", "One FastAPI process. Splitting it would be cargo-cult scaling — Résumé-Driven Architecture, literally."),
        ("LangChain", "Not needed. There is no chain/retriever/tool-use composition to abstract. Our lexicon + Pydantic validation is 200 lines we can read and test — LangChain would be 40 MB of someone else’s opinions."),
        ("A “match percentage” everywhere in the UI", "One honest 0–100 number, labeled decision-support, with the disclaimer in the payload and UI, and dimension weights disclosed. Scattering percentages would be dishonest anchoring."),
    ],
    [1.9, 4.8],
)

# ================= PART 5 =================
doc.add_heading("Part 5 — Is this legitimately an “AI project”? Yes — precisely, and here is the inventory", level=1)
p = doc.add_paragraph()
p.add_run("Interviews will probe whether the “AI” is real. Here is the exact ledger — what is AI, what is ML, and what is deliberately not:")

doc.add_heading("5.1  Where AI and ML genuinely run", level=2)
make_table(
    doc,
    ["Component", "What it is", "Type"],
    [
        ("JD profile extraction", "Large language model (Ollama qwen2.5:3b locally / Groq openai/gpt-oss-120b hosted) constrained by schema validation and a lexicon gate. Temperature 0, fixed seed, deterministic on repeats via cache.", "Generative LLM, constrained"),
        ("OCR for scanned resumes", "RapidOCR — a neural detection+recognition stack on onnxruntime. Reads pixels, not text layers, on the exact hardware you own.", "Computer vision ML (ONNX)"),
        ("Evidence matching", "Rule-based with alias dictionaries and morphology tolerance — NOT ML. Included here because interviewers ask where the model ends.", "Deterministic NLP heuristics"),
        ("Scoring engine", "Weighted arithmetic. NOT ML — intentionally. Reproducibility is the moat.", "Deterministic logic"),
    ],
    [1.35, 4.6, 1.3],
)

doc.add_heading("5.2  How to claim this honestly in one sentence", level=2)
callout(doc, "“ResumeIQ uses LLMs and neural OCR to interpret language and pixels, a deterministic rubric to produce numbers, and an evaluation harness to prove both work — every number you see in the product is either verbatim evidence or a labeled hypothesis. The AI is confined, verifiable, and disclosed.”")

doc.add_heading("5.3  Why this is a BETTER AI story than another RAG chatbot", level=2)
bullets(doc, [
    ("The intelligence is inspectable.", "We can point at every LLM output and show the exact line we dropped it, because the lexicon gate either maps it or rejects it. Most “AI” resume tools cannot show their working."),
    ("The AI is bounded by a non-AI core.", "The verdict does not depend on a model’s temperature, mood, or vendor. That is not a compromise — it is the trust architecture."),
    ("We measured what the AI does wrong.", "We observed qwen2.5:3b emit unmappable free text — and fixed it with the lexicon gate instead of “better prompting”. That observation-fix loop is the MLPM job description."),
    ("We know when the AI is off.", "llama-3.3-70b-versatile silently vanished from Groq’s free tier. The product noticed (deterministic fallback) instead of crashing. Model risk management, in production, for free."),
])

# ================= PART 6 =================
doc.add_heading("Part 6 — The honesty ledger: what is measured, what is claimed", level=1)
make_table(
    doc,
    ["Claim", "Status", "Evidence"],
    [
        ("Skill-status accuracy 100% (25/25)", "Measured — on 4 synthetic-but-realistic labeled cases", "evaluation/evaluate.py → evaluation/report.md. Dev set, not a held-out benchmark. Treat as a smoke test, not a generalisation claim."),
        ("Groundedness 100%", "Measured — structurally true", "Every matched/partial assessment carries a verbatim span; every missing one is reported, never guessed. Verified by the eval harness."),
        ("Determinism — same input, same output", "Verified", "temp 0 + seed 42 + content-hash JD-profile cache; three consecutive runs byte-identical."),
        ("Cost per analysis $0.00", "True and disclosed", "Local mode: zero marginal cost. Hosted demo: free tier. Hosted usage is on the friend’s/demo balance — disclosed in DEPLOYMENT.md."),
        ("Weights 40/25/20/10/5", "HYPOTHESIS, labelled as such", "No calibration data yet. The UI copy and docs say so. Path: 30-resume calibration study, MAE + Spearman vs human raters, then re-weight."),
        ("Partial credit 0.5 for skills-list-only mentions", "HYPOTHESIS", "Defensive against keyword stuffing. Side effect: punishes table-heavy resumes (observed: 24/31 partials on one resume). Revisit with calibration data."),
        ("Cognitive/ATS compatibility", "NOT CLAIMED", "No empirical basis. The score is decision-support for humans — never a filter."),
        ("“Better than competitors”", "NOT CLAIMED", "No head-to-head study exists. Say it in interviews as architecture judgment, not as a result."),
        ("OCR text quality on scans", "Known-limited", "iLovePDF-style scans parse at usable accuracy with noise (emails/phones garble — irrelevant here; skill terms survive). Prefer Export-to-PDF advice in docs."),
        ("English only; no PDF fonts weirdness", "Known-limited", "Ligatures, hyphenation across line breaks, infographic layouts all degrade extraction gracefully; none of it fabricates."),
    ],
    [1.9, 1.35, 3.45],
)

# ================= PART 7 =================
doc.add_heading("Part 7 — 25 questions a senior PM will ask (and the real answers)", level=1)
p = doc.add_paragraph()
p.add_run("Each answer is written to be said out loud in an interview, not read silently from a script. Lengths are deliberate: a senior answer is 40–60 seconds of structured speech.")

ask(doc, 1, "Who is the user, exactly? Not “job seekers” — narrow it.",
    "Early-career and 2–4 YOE candidates — Indian-market tech talent — who are strong enough to be shortlisted but get silently rejected on resume–JD fit they never see. Specifically: engineers and PMs targeting generative-AI roles where JD language has drifted far ahead of what HR screens actually probe. Beachhead: IIT/NIT grads with 1–3 years, targeting AI/PM roles at GCC and Indian product companies."),

ask(doc, 2, "Why would they use this instead of reading the JD carefully?",
    "Everyone reads the JD. Nobody reads it the way an interviewer will probe it. The gap between “I read it” and “I know which six questions they’ll ask” is the product. We sell calibrated self-knowledge, not reading comprehension — and the tool shows its receipts line by line."),

ask(doc, 3, "What is the North Star metric?",
    "Percent of exposed/thin claims in a user's resume converted into evidence-backed bullets within 7 days of first analysis. It captures the only outcome that matters — changed behaviour — not vanity engagement. It is deliberately not measured yet because instrumenting it honestly requires opt-in follow-up; a fake number would be worse than none, and the UI says 0/N until it exists."),

ask(doc, 4, "What guardrail metrics would you add on day one?",
    "Groundedness (always 100% — verbatim span per claim), abstention rate (how often we say “no evidence” — should rise, not fall, if the model gets bolder), fallback-invocation rate (LLM→deterministic switch count — early warning for model/provider drift), and time-to-first-insight. All four are already visible in the product telemetry drawer."),

ask(doc, 5, "Why is the matching deterministic instead of embedding-based?",
    "Embeddings would bridge semantics we don't need yet — the JD and resume are both short, lexically rich documents where the hard cases (“did they show RAG in context?”) require evidence classification, not vector proximity. Deterministic matching is inspectable, debuggable, and unit-testable; embeddings would add a dependency and a failure mode for accuracy we have not yet measured as missing. When calibration shows lexical matching losing real hits, embeddings become a measured bet, not a fashionable one."),

ask(doc, 6, "How do you stop the LLM hallucinating skills or evidence?",
    "Four layers, in order of precedence. One: the LLM never writes evidence — Python does the matching against the actual file. Two: LLM skill output is canonicalised onto a curated lexicon; anything unmappable is dropped silently or falls back whole. Three: output is schema-validated (Pydantic) before use. Four: every response carries an extraction_mode field — if we fell back, the UI says so. The model proposes; the lexicon verifies; Python computes."),

ask(doc, 7, "Why is there no RAG anywhere in the pipeline?",
    "Same reason there's no vector DB for search here: corpus size ≈ one document pair (~1.2k tokens). Retrieval would add failure modes (chunking, ranking regressions, index staleness) and latency for zero measurable accuracy gain. The failure class we were actually fighting — ungrounded generation — is handled by the lexicon gate and verbatim citations, which is where grounding belongs for single-document reasoning."),

ask(doc, 8, "Why not agents — isn’t planning with LangGraph “the 2025 way”?",
    "Agents earn their complexity when the task graph is unknown at design time. Ours is fully known: parse, profile, match, score, recommend, map — six stages, fixed order, each individually testable. I'd add agents the day a user flow requires a variable sub-graph (e.g. cross-resume career analysis or a multi-round interview simulator). Until then, orchestration theater adds failure modes, not value."),

ask(doc, 9, "What does “evidence-grounded” mean mechanically?",
    "Every skill assessment returns a SkillAssessment(status, evidence, note). Evidence is the verbatim line(s) from the resume that contain the term or its aliases (“user interviews” for user research), clipped on word boundaries. If no line contains it, status is missing and evidence is empty — displayed as “no direct evidence found”, not softened. The split matched vs partial is decided by a deterministic skills-list heuristic (comma-dense short lines = listed, not demonstrated)."),

ask(doc, 10, "Why not let the LLM compute the score?",
    "Because then the score would be unreproducible, un-auditable, un-calibratable and unexplainable to the candidate whose life it influenced. The rubric has known weights, printed in the UI, configurable via environment, and identical across every run of the same input. When a PM asks “why did S get 58 on required skills?”, the answer is arithmetic, not “temperature 0.7 and vibes”."),

ask(doc, 11, "How do you know the scoring works at all?",
    "We built a labeled development set — four realistic resume/JD pairs hand-annotated with expected skill statuses and outcomes — and measure two things on every change: status accuracy (25/25 today) and groundedness (100%). It's honest about scope: four cases is a smoke test, not a benchmark. The validation that matters for shipping is the calibration study on ~30 resumes against human raters — that's v1.5, with MAE and Spearman correlation reported publicly."),

ask(doc, 12, "Couldn’t your 100% be inflated by hand-picked cases?",
    "Yes — that's why the doc, the README and the UI all label it as a dev set, n=4, hypothesis-grade. The claim we defend is not “95% accurate in the wild”, it's “our regression suite passes and every verdict is inspectable”. Any number we can't defend in public, we don't print."),

ask(doc, 13, "How would you calibrate weights 40/25/20/10/5?",
    "Recruit 30 resume/JD pairs across match strengths, get three human raters to score alignment 0–100 with a written rubric, then grid-search weight vectors minimising MAE and maximising Spearman against consensus, with a holdout split. Publish the process and the numbers in the repo regardless of outcome — including if the result is “weights stay as hypotheses”. Calibration is iterative: re-run after every material parser or UI change."),

ask(doc, 14, "What result would shut the project down?",
    "Three. If human-vs-system Spearman landed under ~0.5 after calibration — we're not measuring hiring fit, we're generating noise with good typography. If users can't state back the one thing the tool taught them, our UX failed — rewrite, don't ship. If groundedness ever dipped below 100% — a single fabricated evidence line is a trust-killer in a tool whose entire thesis is honesty. That's the kill-switch because it is non-negotiable."),

ask(doc, 15, "Aren’t you building a tool that discriminates in hiring?",
    "Deliberately not. ResumeIQ never outputs a hire/no-hire signal, never touches employers, and disclaims in every payload that it's decision support with no probability calibration. Scope creep into employer tooling changes the regulatory posture entirely (EU AI Act employment-risk category) and the product identity. The day we serve employers, we need audits, bias testing, and legal review — none of which a portfolio demo pretends to satisfy, so we don't."),

ask(doc, 16, "What about privacy? Does the hosted demo leak resumes?",
    "Honest answer: in the hosted demo, resume text transits a free-tier third-party inference API (Groq). We process in memory, store nothing, log nothing — but it is not your-machine-private. Local mode is; we ship a one-env-var switch and disclose the distinction in the UI pill (“Free-tier demo · not stored” vs “Local-first · nothing stored”), the README, DEPLOYMENT.md and this document. No resume content is ever persisted server-side in any mode. Request IDs exist; payloads don't."),

ask(doc, 17, "Who gets hurt when this is wrong?",
    "The candidate — falsely reassured (applies nowhere else, leans on inflated 80) or falsely discouraged (drops a role they'd have landed on interview presence). Both harms are soft and reversible — this tool advises the individual; it gates nobody. Compare that to the same model inside an ATS: then a wrong answer becomes an employment decision at scale. Same model, radically different blast radius — scope is our safety case, and our disclaimer is repeated, not decorative."),

ask(doc, 18, "What happens when Groq deprecates your model overnight?",
    "Already happened, in production, to this exact class of risk: llama-3.3-70b-versatile vanished from the free catalog mid-development, and Groq's WAF blocks non-browser clients (error 1010). Design response: provider-agnostic client (any OpenAI-compatible endpoint), fixed seed and temperature where supported, schema-validated fallback to the deterministic parser, and a health/telemetry surface showing exactly which engine produced the analysis. The user never sees a stack trace; they see a disclaimer and still get a result."),

ask(doc, 19, "Can it survive a Product Hunt / demo day spike?",
    "Render free tier: one instance, sleeps on idle, ~30 s cold start, 512 MB RAM — fine for tens of analyses a day, wrong for a spike. Burst path: Groq free tier has per-minute token/request caps; beyond them we 429 — and degrade gracefully to deterministic scoring (slightly less nuanced, fully working, no errors). What we must not do is hide this: the demo page carries the cold-start notice, and the README documents it. For real traffic: one paid instance of the API (~$7/mo) removes the problem entirely."),

ask(doc, 20, "What’s the moat? Resume parsing seems commoditised.",
    "Not moats — honest bets. (1) The lexicon-gated trust architecture is inspectable and testable; copying it is feasible, operating it is judgment. (2) The evaluation harness and calibration data are the real assets over time. (3) Distribution: candidates who fixed their resumes with it tell others — evidence beats ads. (4) The interview map is a workflow no PDF scanner has shipped. If a big ATS copies all four, we still lose — which is why this is designed as a portfolio product with a community, not as a venture-scale moat."),

ask(doc, 21, "How would you get the first 100 users without budget?",
    "Three channels, zero spend. (1) Personal network at Reliance and GCC peers — 40 warm sends with a 2-minute Loom, asking for 15 minutes of feedback, not reviews. (2) Community posts in AI-career Discords/Reddit r/india, r/cscareerquestions — ship the tool with one honest demo, answer every comment. (3) The case study itself — every interview loop is a distribution event for the product. First 100 users is a conversation problem, not an ads problem."),

ask(doc, 22, "What’s explicitly on the v2 roadmap — and what was cut?",
    "Kept in v2: calibration study (the only legitimate reason to touch the weights), JD-corpus RAG once volume justifies it, the “Fix with Context” co-authoring loop (turns exposed claims into evidence-backed bullets using the user's own raw input — the blank-page killer), role-archetype rubric lenses, privacy-preserving feedback telemetry. Cut deliberately: employer-side anything (regulatory + identity), batch analysis, multi-resume comparison, ATS integrations, mobile app, internationalization. Every cut protects the trust thesis and the $0 run cost."),

ask(doc, 23, "What would you A/B test first?",
    "Exposed → action-card flow, not the score. Hypothesis: candidates who complete one "
    "“surface it” rewrite within 24 h are measurably more likely to report a follow-up interview invite — the causal chain the North Star wants. Primary: 7-day conversion to evidence-backed bullet (self-reported + before/after diff). Guardrails: score-comprehension quiz pass rate, disclaimer recall rate, abstention-rate drift. We A/B the behaviour, never the ethical framing."),

ask(doc, 24, "Build vs buy the whole thing — be honest.",
    "Resume parsing: build (two months of edge cases no vendor sells). JD extraction: buy the tokens, build the gate. Scoring: build — it is the IP and the trust plane. Interview map: build — it's the differentiator. Telemetry: assemble from existing primitives. Buying ATS APIs (Greenhouse etc.) would add data-sharing risk and zero learning. The rule: rent commodity compute, own the trust layer."),

ask(doc, 25, "If you were interviewing you for AI PM, what are you hoping we ask?",
    "The uncomfortable one: “Show me something you got wrong.” Because the honest answer is the product: my first parser duplicated every table cell, my first scorer re-weighted itself silently on N/A dimensions, the 3B model invented skills until I added the lexicon gate, and llama-3.3-70b disappeared from Groq mid-build — four failures, four permanent fixes, all in the git history, all visible. I don't ship AI products — I ship AI products that survive their first contact with reality, and I have the scars catalogued to prove it.")

# ================= PART 8 =================
doc.add_heading("Part 8 — Limitations, risks and the roadmap I would defend", level=1)

doc.add_heading("8.1  Known limits — and what they teach", level=2)
bullets(doc, [
    ("Skills declared ≠ skills demonstrated.", "A dense skills table reads as “partial” everywhere — 24 of 31 skills on one resume scored partial, dragging required skills to 58. The rubric is honest but stern; the fix is bullets with outcomes, not a softer heuristic."),
    ("Semantics beyond the lexicon are invisible.", "“Led a GenAI pitch-generation layer” doesn’t contain the literal term “rag” — lexical matching reports no evidence. Capturing that requires true semantic retrieval — roadmap, not denial."),
    ("OCR quality varies with scan quality.", "A printed iLovePDF scan parses usably; a phone photo of a creased printout is a gamble we take openly, with guidance to re-export instead."),
    ("Ranking is ordinal-ish, not cardinal.", "Scores band alignment; they don’t rank candidates against each other. We removed the temptation to imply a leaderboard."),
    ("Weights are priors, not posteriors.", "40/25/20/10/5 encodes judgment, not evidence. Calibration study is the fix — and we say so on the page."),
])

doc.add_heading("8.2  Risk register (the honest rows)", level=2)
make_table(
    doc,
    ["Risk", "Severity", "Mitigation already shipped"],
    [
        ("Judge/interviewer assumes score = hiring probability", "High", "Disclaimer in payload + UI, verbatim; decision-support framing in every touchpoint; no employer surface exists."),
        ("User uploads and walks away with an inflated verdict", "Medium", "Score is holistic (experience + responsibilities + quals), conservative by construction, and every claim is verifiable."),
        ("Cloud model silently deprecates / 403s / 429s", "Medium", "Provider-agnostic client, deterministic fallback, visible routing in telemetry, cold-start disclosure."),
        ("Lexicon misses a niche-but-real skill", "Low–Medium", "Miss = no-evidence reported honestly; no hallucinated match. Lexicon grows per-pull-request with evidence, not by dumping keyword dumps."),
        ("PII leak via logging", "Low", "Zero payload logging anywhere; metrics are aggregates only; request IDs are random hex."),
        ("User expects OCR miracles from a photo-scan", "Low", "README states Export→PDF > Print→PDF; known-noise disclosure; errors are explicit, not silent garbage-in."),
    ],
    [2.35, 0.8, 3.55],
)

doc.add_heading("8.3  Roadmap — 90 days, in order", level=2)
bullets(doc, [
    ("Days 1–30", "Calibration study with 30 resume/JD pairs and 2–3 raters. Publish MAE + Spearman in the repo. Re-weight or admit the weights stay hypotheses (both outcomes are publishable)."),
    ("Days 31–60", "JD-corpus RAG behind a feature flag, only if calibration shows semantic-miss dominance. “Fix with Context” co-authoring: two questions → evidence-backed bullet, score delta preview."),
    ("Days 61–90", "Closed-loop habit: email-free nudges (“you have 3 exposed gaps — want the interview map again?”); opt-in feedback telemetry; role-archetype rubric lenses (IC vs PM vs platform)."),
])

# ================= APPENDIX =================
doc.add_heading("Appendix — Reproduce everything in this document", level=1)
make_table(
    doc,
    ["Claim", "Command / artefact"],
    [
        ("Unit + integration tests (8)", ".venv\\Scripts\\python.exe -m pytest Backend/tests -q"),
        ("Eval harness (25 labeled cases)", "$env:RESUMEIQ_LLM='offline'; .venv\\Scripts\\python.exe evaluation\\evaluate.py  →  evaluation\\report.md"),
        ("Two-column + single-column parsing", "0 duplicate lines on both layouts; row-level table dedup; see Backend/resume_parser.py"),
        ("Scanned-PDF OCR round trip", "test_ocr_extracts_text_from_scanned_pdf (synthetic image-only PDF)"),
        ("Determinism (3 identical runs)", "RESUMEIQ_LLM=ollama; analyze same file thrice; latency drops to ~0 ms via cache"),
        ("Hosted demo model", "GET /health → llm_mode=cloud; POST /api/analyze → model: openai/gpt-oss-120b, ~1.7 s (cold) / ~36 ms (cache)"),
        ("Local privacy mode", "RESUMEIQ_LLM=ollama or ollama; health → llm_mode=ollama/auto; nothing leaves the machine"),
        ("Free deterministic mode", "RESUMEIQ_LLM=offline — zero network calls, always works, full product minus LLM phrasing"),
    ],
    [2.7, 4.0],
)
p = doc.add_paragraph()
run = p.add_run("Every number in this document is reproducible from the repository alone. That is the difference between a case study and a press release.")
run.font.italic = True
run.font.color.rgb = ACCENT_RGB

callout(doc, "ResumeIQ — decision support, not a hiring probability. Built, measured, disclosed.", TINT)

out = r"docs\ResumeIQ_AI_PM_Case_Study.docx"
doc.save(out)
print(f"Saved {out}")
