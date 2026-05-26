"""Append-only JSONL checkpoint writer for worker resume."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO


class CheckpointWriter:
    """Context manager that appends checkpoint lines to a JSONL file."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._file: TextIO | None = None
        self._lock = threading.Lock()

    def __enter__(self) -> CheckpointWriter:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("a", encoding="utf-8")
        return self

    def write(
        self,
        *,
        container: str,
        blob_path: str,
        action: str,
        tags: dict[str, str] | None = None,
        ts: str | None = None,
    ) -> None:
        """Append one checkpoint record."""
        if self._file is None:
            raise RuntimeError("CheckpointWriter is not open; use it as a context manager")

        record: dict[str, Any] = {
            "container": container,
            "blob_path": blob_path,
            "action": action,
            "tags": tags or {},
            "ts": ts or datetime.now(timezone.utc).isoformat(),
        }
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        with self._lock:
            self._file.write(line + "\n")
            self._file.flush()

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None
