"""
Helpers for saving uploaded files to disk and cleaning them up afterwards.
"""

import uuid
from pathlib import Path

from app.config import settings


def save_temp_file(filename: str, content: bytes) -> Path:
    """Saves raw bytes to the uploads directory under a unique name and
    returns the path. Using a UUID prefix avoids collisions between
    simultaneous requests / identical filenames."""
    ext = Path(filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = settings.UPLOAD_DIR / unique_name
    with open(dest_path, "wb") as f:
        f.write(content)
    return dest_path


def delete_file_silently(path: Path) -> None:
    """Deletes a file if it exists; never raises."""
    try:
        if path and Path(path).exists():
            Path(path).unlink()
    except Exception:
        # Cleanup failures should never break the request/response cycle
        pass
