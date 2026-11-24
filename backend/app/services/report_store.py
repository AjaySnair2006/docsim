"""
Very small in-memory registry mapping comparison_id -> report file path.

This is fine for a student mini-project / single-process demo. If you need
it to survive server restarts or run across multiple workers, swap this for
a database table or a simple JSON/SQLite file instead — the rest of the app
only calls the two functions below, so that's the only place to change.
"""

from pathlib import Path
from typing import Optional

_store: dict[str, str] = {}


def register_report(comparison_id: str, report_path: Path) -> None:
    _store[comparison_id] = str(report_path)


def get_report_path(comparison_id: str) -> Optional[Path]:
    path = _store.get(comparison_id)
    return Path(path) if path else None
