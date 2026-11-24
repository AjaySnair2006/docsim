"""
Pydantic models describing the shape of data moving between:
  PDF processing module -> AI similarity module -> report module -> API response

These schemas are the "contract" the 3 teammates' modules are expected to
fill. Keep this file as the single source of truth for data shape.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ---------- Internal data-flow models (between the 3 modules) ----------

class ExtractedPage(BaseModel):
    """Output expected from the PDF Processing teammate's module (per page)."""
    page_number: int
    text: str


class ExtractedDocument(BaseModel):
    """Full output expected from the PDF Processing module for one PDF."""
    filename: str
    total_pages: int
    pages: List[ExtractedPage]


class SimilarSection(BaseModel):
    """One matched/similar section between the two documents."""
    doc_a_page: int
    doc_b_page: int
    doc_a_excerpt: str
    doc_b_excerpt: str
    similarity_score: float = Field(..., ge=0, le=100)


class PageStat(BaseModel):
    """Page-wise similarity statistic."""
    page_number: int
    matched_page_in_other_doc: Optional[int] = None
    similarity_score: float = Field(..., ge=0, le=100)


# ---------- API response models ----------

class ComparisonResult(BaseModel):
    comparison_id: str
    document_a_name: str
    document_b_name: str
    overall_similarity: float = Field(..., ge=0, le=100)
    content_similarity: float = Field(..., ge=0, le=100)
    similar_sections: List[SimilarSection]
    page_wise_stats: List[PageStat]
    content_similar_sections: List[SimilarSection]
    content_page_wise_stats: List[PageStat]
    total_pages_a: int
    total_pages_b: int
    report_download_url: str


class ErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    message: str


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
