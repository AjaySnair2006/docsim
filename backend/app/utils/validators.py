"""
Validation helpers for uploaded files.
"""

from pathlib import Path
from fastapi import UploadFile

from app.config import settings


class FileValidationError(Exception):
    """Raised when an uploaded file fails validation."""

    def __init__(self, message: str, code: str = "INVALID_FILE"):
        self.message = message
        self.code = code
        super().__init__(message)


def validate_extension(filename: str) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file type '{ext}'. Only PDF files are allowed.",
            code="UNSUPPORTED_FILE_TYPE",
        )


def validate_not_empty(filename: str, content: bytes) -> None:
    if not content or len(content) == 0:
        raise FileValidationError(
            f"Uploaded file '{filename}' is empty.", code="EMPTY_FILE"
        )


def validate_size(filename: str, content: bytes) -> None:
    if len(content) > settings.MAX_FILE_SIZE_BYTES:
        raise FileValidationError(
            f"File '{filename}' exceeds the {settings.MAX_FILE_SIZE_MB}MB size limit.",
            code="FILE_TOO_LARGE",
        )


def validate_pdf_signature(filename: str, content: bytes) -> None:
    """Quick magic-byte check that the file is actually a PDF, not just named .pdf"""
    if not content.startswith(b"%PDF-"):
        raise FileValidationError(
            f"File '{filename}' does not appear to be a valid PDF.",
            code="CORRUPT_OR_INVALID_PDF",
        )


async def validate_upload(file: UploadFile) -> bytes:
    """
    Runs all validation checks on an UploadFile and returns its raw bytes.
    Raises FileValidationError on any failure.
    """
    if not file.filename:
        raise FileValidationError("No filename provided.", code="MISSING_FILENAME")

    validate_extension(file.filename)

    content = await file.read()
    validate_not_empty(file.filename, content)
    validate_size(file.filename, content)
    validate_pdf_signature(file.filename, content)

    # reset pointer in case something else needs to read the file again
    await file.seek(0)
    return content
