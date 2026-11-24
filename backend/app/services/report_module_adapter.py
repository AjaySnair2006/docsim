"""
=====================================================================
ADAPTER FOR: Comparison Analysis & PDF Report Generation module
(Teammate #3)
=====================================================================

INTEGRATION CONTRACT
---------------------
Teammate #3 must provide two things:

1. An analysis function that turns raw similarity scores into the
   structured "similar sections" and "page-wise stats" the frontend shows:

    def analyze_comparison(doc_a: dict, doc_b: dict, similarity_result: dict) -> dict:
        \"\"\"
        Returns:
        {
            "similar_sections": [
                {
                    "doc_a_page": 1, "doc_b_page": 1,
                    "doc_a_excerpt": "...", "doc_b_excerpt": "...",
                    "similarity_score": 91.2
                }, ...
            ],
            "page_wise_stats": [
                {"page_number": 1, "matched_page_in_other_doc": 1, "similarity_score": 91.2},
                ...
            ]
        }
        \"\"\"

2. A report generator:

    def generate_pdf_report(comparison_data: dict, output_path: str) -> str:
        \"\"\"Writes a PDF report to output_path and returns the path.\"\"\"

HOW TO CONNECT THE REAL MODULE
-------------------------------
1. Drop teammate #3's package into `backend/app/external/report/`.
2. Replace the imports inside `_call_real_*` functions below.
=====================================================================
"""

from pathlib import Path
import re

from app.config import settings
from app.services.similarity_module_adapter import (
    _maximum_weight_assignment,
    _token_shingles,
    _weighted_dice,
)


class ReportGenerationError(Exception):
    def __init__(self, message: str, code: str = "REPORT_GENERATION_FAILED"):
        self.message = message
        self.code = code
        super().__init__(message)


# ---------- Analysis (similar sections + page-wise stats) ----------

def _call_real_analysis_module(doc_a: dict, doc_b: dict, similarity_result: dict) -> dict:
    from app.external.report.analysis import analyze_comparison  # type: ignore

    return analyze_comparison(doc_a, doc_b, similarity_result)


def _stub_analysis_module(doc_a: dict, doc_b: dict, similarity_result: dict) -> dict:
    """Fallback: builds sections/stats directly from the similarity adapter's
    page_pair_scores using the configured threshold. Remove once teammate #3's
    real analysis module is integrated."""
    threshold = settings.SIMILARITY_THRESHOLD * 100
    pages_a = {p["page_number"]: p["text"] for p in doc_a["pages"]}
    pages_b = {p["page_number"]: p["text"] for p in doc_b["pages"]}

    similar_sections = []
    page_wise_stats = []

    for pair in similarity_result.get("page_pair_scores", []):
        score = pair["similarity_score"]
        page_wise_stats.append(
            {
                "page_number": pair["doc_a_page"],
                "matched_page_in_other_doc": pair["doc_b_page"],
                "similarity_score": score,
            }
        )
        page_b = pair["doc_b_page"]
        if page_b is None:
            continue

        sections = _matching_sentences(
            pages_a.get(pair["doc_a_page"], ""),
            pages_b.get(page_b, ""),
            threshold,
        )
        if sections:
            for excerpt_a, excerpt_b, section_score in sections:
                similar_sections.append(
                    {
                        "doc_a_page": pair["doc_a_page"],
                        "doc_b_page": page_b,
                        "doc_a_excerpt": excerpt_a[:200],
                        "doc_b_excerpt": excerpt_b[:200],
                        "similarity_score": section_score,
                    }
                )
        elif score >= threshold:
            similar_sections.append(
                {
                    "doc_a_page": pair["doc_a_page"],
                    "doc_b_page": page_b,
                    "doc_a_excerpt": (pages_a.get(pair["doc_a_page"], "") or "")[:200],
                    "doc_b_excerpt": (pages_b.get(page_b, "") or "")[:200],
                    "similarity_score": score,
                }
            )

    return {"similar_sections": similar_sections, "page_wise_stats": page_wise_stats}


def _matching_sentences(text_a: str, text_b: str, threshold: float) -> list[tuple[str, str, float]]:
    sentences_a = _split_sentences(text_a)
    sentences_b = _split_sentences(text_b)
    vectors_a = [_token_shingles(sentence) for sentence in sentences_a]
    vectors_b = [_token_shingles(sentence) for sentence in sentences_b]

    scores = []
    overlaps = []
    for vector_a in vectors_a:
        score_row = []
        overlap_row = []
        for vector_b in vectors_b:
            score, overlap = _weighted_dice(vector_a, vector_b)
            score_row.append(score)
            overlap_row.append(overlap)
        scores.append(score_row)
        overlaps.append(overlap_row)

    matches = []
    for index_a, index_b in enumerate(_maximum_weight_assignment(overlaps)):
        if index_b is None or index_b >= len(sentences_b):
            continue
        score = scores[index_a][index_b]
        if score >= threshold:
            matches.append(
                (sentences_a[index_a], sentences_b[index_b], round(score, 2))
            )
    return matches


def _split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    return [sentence for sentence in re.split(r"(?<=[.!?])\s+", normalized) if sentence]


def analyze(doc_a: dict, doc_b: dict, similarity_result: dict) -> dict:
    try:
        try:
            return _call_real_analysis_module(doc_a, doc_b, similarity_result)
        except ModuleNotFoundError:
            return _stub_analysis_module(doc_a, doc_b, similarity_result)
    except Exception as exc:
        raise ReportGenerationError(f"Comparison analysis failed: {exc}")


# ---------- PDF report generation ----------

def _call_real_report_module(comparison_data: dict, output_path: str) -> str:
    from app.external.report.generator import generate_pdf_report  # type: ignore

    return generate_pdf_report(comparison_data, output_path)


def _stub_report_module(comparison_data: dict, output_path: str) -> str:
    """Create a paginated PDF with the matched excerpts, not just their scores."""
    from xml.sax.saxutils import escape

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportBody", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=9, leading=13, alignment=TA_LEFT, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="ReportMatch", parent=styles["Heading3"], fontSize=10,
        leading=14, textColor=colors.HexColor("#68152d"), spaceBefore=8,
        spaceAfter=4,
    ))

    document = SimpleDocTemplate(
        output_path, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
    )
    story = [
        Paragraph("Document Similarity Report", styles["Title"]),
        Spacer(1, 8),
        Paragraph(f"Document A: {escape(str(comparison_data['document_a_name']))}", styles["ReportBody"]),
        Paragraph(f"Document B: {escape(str(comparison_data['document_b_name']))}", styles["ReportBody"]),
        Paragraph(f"Text Overlap: {comparison_data['overall_similarity']}%", styles["ReportBody"]),
        Paragraph(f"Semantic Content Similarity: {comparison_data['content_similarity']}%", styles["ReportBody"]),
        Spacer(1, 10),
        Paragraph("Similar Sections", styles["Heading2"]),
    ]

    text_sections = comparison_data["similar_sections"]
    if not text_sections:
        story.append(Paragraph("No text-overlap sections were found.", styles["ReportBody"]))
    for index, section in enumerate(text_sections, start=1):
        story.extend([
            Paragraph(
                f"Text match {index} | Doc A p{section['doc_a_page']} "
                f"to Doc B p{section['doc_b_page']} | Score: "
                f"{section['similarity_score']}%",
                styles["ReportMatch"],
            ),
            Paragraph(f"<b>Document A:</b> {escape(str(section['doc_a_excerpt']))}", styles["ReportBody"]),
            Paragraph(f"<b>Document B:</b> {escape(str(section['doc_b_excerpt']))}", styles["ReportBody"]),
        ])

    story.extend([Spacer(1, 10), Paragraph("Semantic Content Matches", styles["Heading2"])])
    content_sections = comparison_data["content_similar_sections"]
    if not content_sections:
        story.append(Paragraph("No semantic page matches were found.", styles["ReportBody"]))
    for index, section in enumerate(content_sections, start=1):
        story.extend([
            Paragraph(
                f"Content match {index} | Doc A p{section['doc_a_page']} "
                f"to Doc B p{section['doc_b_page']} | Meaning score: "
                f"{section['similarity_score']}%",
                styles["ReportMatch"],
            ),
            Paragraph(f"<b>Document A:</b> {escape(str(section['doc_a_excerpt']))}", styles["ReportBody"]),
            Paragraph(f"<b>Document B:</b> {escape(str(section['doc_b_excerpt']))}", styles["ReportBody"]),
        ])

    document.build(story)
    return output_path


def generate_report(comparison_data: dict, comparison_id: str) -> Path:
    output_path = settings.REPORT_DIR / f"{comparison_id}.pdf"
    try:
        try:
            path = _call_real_report_module(comparison_data, str(output_path))
        except ModuleNotFoundError:
            path = _stub_report_module(comparison_data, str(output_path))
        return Path(path)
    except Exception as exc:
        raise ReportGenerationError(f"Failed to generate PDF report: {exc}")
