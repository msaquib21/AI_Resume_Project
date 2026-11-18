
import logging
import re
from io import BytesIO
from pathlib import Path
from typing import List

import fitz  # PyMuPDF
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


logger = logging.getLogger(__name__)


# ==========================================================
# 1. PDF EXTRACTION
# ==========================================================

def _norm_alnum(text: str) -> str:
    """Collapse everything except alphanumerics — used to detect that a
    table's cells re-state text already captured from blocks, even when
    whitespace differs ('Requirements Gathering' vs 'RequirementsGathering')."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract readable text from PDF resumes.

    Features:
    - Extracts text using PyMuPDF.
    - Handles multi-column resumes using positional blocks.
    - Attempts to preserve logical reading order.
    - Extracts tables when possible.
    - Avoids duplicate table content.
    - Handles extraction errors gracefully.
    """

    if not file_bytes:
        raise ValueError("The uploaded PDF file is empty.")

    extracted_pages: List[str] = []

    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as pdf:

            if pdf.page_count == 0:
                raise ValueError("The PDF contains no pages.")

            for page in pdf:

                page_width = page.rect.width
                page_height = page.rect.height

                # Extract text blocks with positional information.
                blocks = page.get_text("blocks", sort=False)

                left_column = []
                right_column = []
                full_width_blocks = []

                # Approximate column boundary.
                column_boundary = page_width / 2

                for block in blocks:

                    # PyMuPDF block format:
                    # (x0, y0, x1, y1, text, block_no, block_type)

                    if len(block) < 5:
                        continue

                    x0, y0, x1, y1, text = block[:5]

                    if not isinstance(text, str) or not text.strip():
                        continue

                    # Skip image metadata blocks.
                    if len(block) >= 7 and block[6] != 0:
                        continue

                    text = text.strip()

                    block_width = x1 - x0
                    block_center = (x0 + x1) / 2

                    # Blocks spanning most of the page are usually
                    # headers, summaries, or full-width sections.
                    if block_width > page_width * 0.55:

                        full_width_blocks.append(
                            (y0, x0, text)
                        )

                    elif block_center < column_boundary:

                        left_column.append(
                            (y0, x0, text)
                        )

                    else:

                        right_column.append(
                            (y0, x0, text)
                        )

                # Sort blocks top-to-bottom, then left-to-right.
                full_width_blocks.sort(
                    key=lambda item: (item[0], item[1])
                )

                left_column.sort(
                    key=lambda item: (item[0], item[1])
                )

                right_column.sort(
                    key=lambda item: (item[0], item[1])
                )

                page_text_parts = []

                # Preserve full-width content first.
                for _, _, text in full_width_blocks:
                    page_text_parts.append(text)

                # Then process left and right columns.
                for _, _, text in left_column:
                    page_text_parts.append(text)

                for _, _, text in right_column:
                    page_text_parts.append(text)

                page_text = "\n".join(page_text_parts).strip()

                # ==================================================
                # TABLE EXTRACTION
                # ==================================================

                try:

                    tables = page.find_tables()

                    for table in tables.tables:

                        table_data = table.extract()

                        if not table_data:
                            continue

                        table_rows = []

                        for row in table_data:

                            if not row:
                                continue

                            row_text = " | ".join(
                                str(cell).strip()
                                if cell is not None
                                else ""
                                for cell in row
                            )

                            if row_text.strip():
                                table_rows.append(row_text)

                        page_norm = _norm_alnum(page_text)

                        # Row-level check: a row only adds new information if
                        # at least one of its cells is absent from the block
                        # text (ignoring alphanumerics). Rows already covered
                        # by the reading-order pass are dropped entirely.
                        novel_rows = []
                        for row in table_rows:
                            cells = [c for c in row.split(" | ") if c.strip()]
                            novel = any(
                                len(_norm_alnum(cell)) >= 8 and _norm_alnum(cell) not in page_norm
                                for cell in cells
                            )
                            if novel:
                                novel_rows.append(row)

                        table_text = "\n".join(novel_rows).strip()
                        if table_text:
                            page_text += "\n" + table_text

                except Exception as table_error:

                    logger.warning(
                        "PDF table extraction failed on page %s: %s",
                        page.number + 1,
                        table_error,
                    )

                if page_text:
                    extracted_pages.append(page_text)

    except ValueError:
        raise

    except Exception as pdf_error:

        logger.exception("PDF extraction failed.")

        raise ValueError(
            "Unable to process this PDF file. "
            "Please upload a valid, readable PDF."
        ) from pdf_error

    extracted_text = "\n\n".join(extracted_pages).strip()

    # Detect empty or image-only documents.
    if not extracted_text:

        raise ValueError(
            "Could not extract readable text from this resume. "
            "It may be a scanned or image-only PDF. "
            "Please upload a text-based PDF or DOCX."
        )

    logger.info(
        "PDF extraction successful: %s characters extracted",
        len(extracted_text),
    )

    return extracted_text


# ==========================================================
# 2. DOCX EXTRACTION
# ==========================================================

def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract text from DOCX resumes.

    Features:
    - Extracts paragraphs.
    - Extracts tables.
    - Preserves original document order of paragraphs and tables.
    - Supports mixed content documents.
    """

    if not file_bytes:
        raise ValueError("The uploaded DOCX file is empty.")

    extracted_content = []

    try:

        document = Document(BytesIO(file_bytes))

        # Iterate through paragraphs and tables in original order.
        for element in document.element.body.iterchildren():

            # ==================================================
            # PARAGRAPH EXTRACTION
            # ==================================================

            if element.tag.endswith("}p"):

                paragraph = Paragraph(
                    element,
                    document
                )

                paragraph_text = paragraph.text.strip()

                if paragraph_text:

                    extracted_content.append(
                        paragraph_text
                    )

            # ==================================================
            # TABLE EXTRACTION
            # ==================================================

            elif element.tag.endswith("}tbl"):

                table = Table(
                    element,
                    document
                )

                for row in table.rows:

                    row_text = " | ".join(
                        cell.text.strip()
                        for cell in row.cells
                    )

                    if row_text.strip():

                        extracted_content.append(
                            row_text
                        )

    except Exception as docx_error:

        logger.exception("DOCX extraction failed.")

        raise ValueError(
            "Unable to process this DOCX file. "
            "Please upload a valid Word document."
        ) from docx_error

    extracted_text = "\n".join(
        extracted_content
    ).strip()

    if not extracted_text:

        raise ValueError(
            "Could not extract readable text from this DOCX. "
            "Please upload a document containing readable text."
        )

    logger.info(
        "DOCX extraction successful: %s characters extracted",
        len(extracted_text),
    )

    return extracted_text


def _dedupe_lines(text: str) -> str:
    """Drop repeated lines and page furniture from a multi-page document.

    Compares on alphanumerics only. Exact repeats in a resume are almost
    always extraction artifacts (page footers, overlay/shadow text), so we
    keep the first occurrence and drop the rest.
    """
    seen = set()
    out = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if out and out[-1] != "":
                out.append("")
            continue
        key = _norm_alnum(stripped)
        if re.fullmatch(r"page\d+of\d+", key):  # "Page 1 of 2"
            continue
        # Short full-width banners like "Candidate — Resume" repeat per page
        if key in seen:
            continue
        seen.add(key)
        out.append(stripped)
    return "\n".join(out).strip()


# ==========================================================
# 3. MAIN RESUME EXTRACTION FUNCTION
# ==========================================================

def extract_resume_text(
    filename: str,
    file_bytes: bytes
) -> str:
    """
    Identify the uploaded file type and extract resume text.

    Supported formats:
    - PDF
    - DOCX

    Called directly from the FastAPI resume parsing endpoint.
    """

    if not filename:

        raise ValueError(
            "Filename is missing."
        )

    if not file_bytes:

        raise ValueError(
            "Uploaded file is empty."
        )

    extension = Path(filename).suffix.lower()

    # ======================================================
    # PDF
    # ======================================================

    if extension == ".pdf":

        extracted_text = extract_text_from_pdf(
            file_bytes
        )

    # ======================================================
    # DOCX
    # ======================================================

    elif extension == ".docx":

        extracted_text = extract_text_from_docx(
            file_bytes
        )

    # ======================================================
    # UNSUPPORTED FORMAT
    # ======================================================

    else:

        raise ValueError(
            "Unsupported file format. "
            "Please upload a PDF or DOCX file."
        )

    # ======================================================
    # FINAL CLEANUP & VALIDATION
    # ======================================================

    extracted_text = extracted_text.strip()
    extracted_text = _dedupe_lines(extracted_text)

    if not extracted_text:

        raise ValueError(
            "Could not extract readable text from this resume."
        )

    logger.info(
        "Resume extraction successful: "
        "%s characters extracted from %s",
        len(extracted_text),
        filename,
    )

    return extracted_text
