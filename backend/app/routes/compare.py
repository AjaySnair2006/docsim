"""
POST /compare

Orchestrates the full pipeline:
  1. Validate both uploaded PDFs
  2. Save them to a temp location
  3. PDF processing module -> extract text per page
  4. AI similarity module -> compute similarity scores
  5. Comparison/report module -> build similar sections + page stats,
     then generate a downloadable PDF report
  6. Return structured JSON to the frontend
"""

import uuid
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.models import ComparisonResult
from app.utils.validators import validate_upload, FileValidationError
from app.utils.file_handler import save_temp_file, delete_file_silently
from app.services import (
    content_similarity_adapter,
    pdf_module_adapter,
    similarity_module_adapter,
    report_module_adapter,
)
from app.services.pdf_module_adapter import PdfProcessingError
from app.services.similarity_module_adapter import SimilarityComputationError
from app.services.report_module_adapter import ReportGenerationError
from app.services.content_similarity_adapter import ContentSimilarityError
from app.services.report_store import register_report

logger = logging.getLogger("docsim.compare")
router = APIRouter(tags=["Comparison"])


@router.post("/compare", response_model=ComparisonResult)
async def compare_documents(
    document_a: UploadFile = File(..., description="First PDF document"),
    document_b: UploadFile = File(..., description="Second PDF document"),
):
    saved_paths = []
    try:
        # ---- 1 & 2: validate + save ----
        content_a = await validate_upload(document_a)
        content_b = await validate_upload(document_b)

        path_a = save_temp_file(document_a.filename, content_a)
        path_b = save_temp_file(document_b.filename, content_b)
        saved_paths = [path_a, path_b]

        # ---- 3: PDF processing module ----
        doc_a = pdf_module_adapter.extract_document(str(path_a), document_a.filename)
        doc_b = pdf_module_adapter.extract_document(str(path_b), document_b.filename)

        doc_a_dict = doc_a.model_dump()
        doc_b_dict = doc_b.model_dump()

        # ---- 4: AI similarity module ----
        similarity_result = similarity_module_adapter.compute(doc_a_dict, doc_b_dict)
        content_result = content_similarity_adapter.compute(doc_a_dict, doc_b_dict)

        # ---- 5: Comparison analysis + report generation ----
        analysis = report_module_adapter.analyze(doc_a_dict, doc_b_dict, similarity_result)

        comparison_id = uuid.uuid4().hex

        comparison_data = {
            "comparison_id": comparison_id,
            "document_a_name": document_a.filename,
            "document_b_name": document_b.filename,
            "overall_similarity": similarity_result["overall_similarity"],
            "content_similarity": content_result["content_similarity"],
            "similar_sections": analysis["similar_sections"],
            "page_wise_stats": analysis["page_wise_stats"],
            "content_similar_sections": content_result["content_similar_sections"],
            "content_page_wise_stats": content_result["content_page_wise_stats"],
            "total_pages_a": doc_a.total_pages,
            "total_pages_b": doc_b.total_pages,
        }

        report_path = report_module_adapter.generate_report(comparison_data, comparison_id)
        register_report(comparison_id, report_path)

        # ---- 6: structured JSON response ----
        return ComparisonResult(
            **comparison_data,
            report_download_url=f"/download-report/{comparison_id}",
        )

    except FileValidationError as exc:
        raise HTTPException(status_code=400, detail={"error_code": exc.code, "message": exc.message})
    except PdfProcessingError as exc:
        raise HTTPException(status_code=422, detail={"error_code": exc.code, "message": exc.message})
    except SimilarityComputationError as exc:
        raise HTTPException(status_code=500, detail={"error_code": exc.code, "message": exc.message})
    except ContentSimilarityError as exc:
        raise HTTPException(status_code=500, detail={"error_code": exc.code, "message": exc.message})
    except ReportGenerationError as exc:
        raise HTTPException(status_code=500, detail={"error_code": exc.code, "message": exc.message})
    except Exception as exc:
        logger.exception("Unexpected error during /compare")
        raise HTTPException(
            status_code=500,
            detail={"error_code": "INTERNAL_ERROR", "message": f"Unexpected error: {exc}"},
        )
    finally:
        # Clean up the uploaded source PDFs — we only keep the generated report
        for p in saved_paths:
            delete_file_silently(p)
