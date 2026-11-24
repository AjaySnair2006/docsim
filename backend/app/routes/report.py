from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services.report_store import get_report_path

router = APIRouter(tags=["Report"])


@router.get("/download-report/{comparison_id}")
async def download_report(comparison_id: str):
    """Downloads the PDF report generated for a given comparison_id
    (returned as `report_download_url` by POST /compare)."""
    report_path = get_report_path(comparison_id)

    if report_path is None or not report_path.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "REPORT_NOT_FOUND",
                "message": f"No report found for comparison_id '{comparison_id}'. "
                           f"It may have expired or the ID is incorrect.",
            },
        )

    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename=f"similarity_report_{comparison_id}.pdf",
    )
