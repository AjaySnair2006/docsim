from fastapi import APIRouter
from app.config import settings
from app.models import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Simple liveness check used by the frontend and deployment platforms."""
    return HealthResponse(
        status="ok", app_name=settings.APP_NAME, version=settings.APP_VERSION
    )
