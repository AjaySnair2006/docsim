"""
=====================================================================
ADAPTER FOR: PDF Processing & Text Extraction module (Teammate #1)
=====================================================================

INTEGRATION CONTRACT
---------------------
Teammate #1 must provide a Python package/module that exposes a function
with (roughly) this signature:

    def extract_text_from_pdf(file_path: str) -> dict:
        \"\"\"
        Returns:
        {
            "filename": "documentA.pdf",
            "total_pages": 5,
            "pages": [
                {"page_number": 1, "text": "..."},
                {"page_number": 2, "text": "..."},
                ...
            ]
        }
        \"\"\"

HOW TO CONNECT THE REAL MODULE
-------------------------------
1. Drop teammate #1's package into `backend/app/external/pdf_processing/`
   (create that folder) OR install it as a local pip package.
2. Replace the `_call_real_pdf_module()` import below with the real import,
   e.g.:
       from app.external.pdf_processing.extractor import extract_text_from_pdf
3. Delete/ignore the stub fallback once the real module is wired in.

This file is the ONLY place that should need to change once teammate #1's
code is ready — nothing else in the backend imports the PDF module directly.
=====================================================================
"""

from pathlib import Path
from app.models import ExtractedDocument, ExtractedPage


class PdfProcessingError(Exception):
    """Raised when text extraction fails for any reason."""

    def __init__(self, message: str, code: str = "PDF_PROCESSING_FAILED"):
        self.message = message
        self.code = code
        super().__init__(message)


def _call_real_pdf_module(file_path: str) -> dict:
    """
    Try to import and call teammate #1's real module.
    Update the import path below once their code is added to the project.
    """
    from app.external.pdf_processing.extractor import extract_text_from_pdf  # type: ignore

    return extract_text_from_pdf(file_path)


def _stub_pdf_module(file_path: str) -> dict:
    """
    Temporary fallback so the API layer is fully runnable/demo-able before
    teammate #1's module is plugged in. Uses PyPDF2 for a basic extraction.
    Remove this once the real module is integrated.
    """
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append({"page_number": i, "text": text})

    return {
        "filename": Path(file_path).name,
        "total_pages": len(reader.pages),
        "pages": pages,
    }


def extract_document(file_path: str, original_filename: str) -> ExtractedDocument:
    """
    Public function used by the /compare route.
    Calls the real teammate module if available, otherwise falls back to
    the local stub so the rest of the app keeps working during development.
    """
    try:
        try:
            raw = _call_real_pdf_module(file_path)
        except ModuleNotFoundError:
            raw = _stub_pdf_module(file_path)

        raw["filename"] = original_filename
        return ExtractedDocument(
            filename=raw["filename"],
            total_pages=raw["total_pages"],
            pages=[ExtractedPage(**p) for p in raw["pages"]],
        )
    except PdfProcessingError:
        raise
    except Exception as exc:
        raise PdfProcessingError(
            f"Failed to extract text from '{original_filename}': {exc}"
        )
