"""
Entry point for the FastAPI backend.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routes import health, compare, report

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Application layer (API) for the AI-Based Document "
                 "Similarity Detection System mini project.",
)

# ---- CORS: allow the React frontend to call this API ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Routers ----
app.include_router(health.router)
app.include_router(compare.router)
app.include_router(report.router)


# ---- Global error handler as a safety net ----
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logging.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong on the server.",
        },
    )


@app.get("/")
async def root():
    return {
        "message": f"{settings.APP_NAME} API is running.",
        "docs": "/docs",
        "endpoints": ["/health", "/compare", "/download-report/{comparison_id}"],
    }
