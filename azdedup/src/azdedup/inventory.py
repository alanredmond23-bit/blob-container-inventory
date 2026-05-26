"""Azure Blob Inventory CSV stream parser."""

from __future__ import annotations

import csv
import glob
from collections.abc import Iterator
from pathlib import Path

from azdedup.models.blob_ref import InventoryBlob


def _norm_etag(raw: str | None) -> str | None:
    if not raw:
        return None
    s = str(raw).strip().strip('"')
    if not s or s == "*":
        return None
    return s


def _parse_row(row: dict[str, str]) -> InventoryBlob | None:
    name = (row.get("Name") or row.get("name") or "").strip()
    if not name or name == "Name":
        return None

    deleted = (row.get("Deleted") or "").strip().lower() in ("true", "1", "yes")
    if deleted:
        return None

    try:
        size = int(float(row.get("Content-Length") or row.get("ContentLength") or 0))
    except (TypeError, ValueError):
        return None
    if size <= 0:
        return None

    if "/" in name:
        container, blob_path = name.split("/", 1)
    else:
        container = (row.get("Container-Name") or row.get("container") or "").strip()
        blob_path = name

    if not container or not blob_path:
        return None

    return InventoryBlob(
        container=container,
        blob_path=blob_path.replace("\\", "/"),
        size=size,
        etag=_norm_etag(row.get("Etag") or row.get("ETag")) or "",
        ext=InventoryBlob.ext_from_path(blob_path),
        last_modified=(row.get("Last-Modified") or row.get("LastModified") or None),
    )


def resolve_inventory_paths(pattern: str) -> list[Path]:
    matches = sorted(glob.glob(pattern))
    if not matches:
        path = Path(pattern)
        if path.is_file():
            return [path]
        raise FileNotFoundError(f"No inventory files match: {pattern}")
    return [Path(p) for p in matches]


def iter_inventory(
    paths: list[Path],
    *,
    containers: set[str] | None = None,
    prefix: str = "",
) -> Iterator[InventoryBlob]:
    for path in paths:
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                blob = _parse_row(row)
                if blob is None:
                    continue
                if containers is not None and blob.container not in containers:
                    continue
                if prefix and not blob.blob_path.startswith(prefix):
                    continue
                yield blob
