"""Blob references from Azure Blob Inventory exports."""

from __future__ import annotations

from pathlib import PurePosixPath

from pydantic import BaseModel


class InventoryBlob(BaseModel):
    container: str
    blob_path: str
    size: int
    etag: str
    ext: str
    last_modified: str | None = None

    @property
    def name(self) -> str:
        return f"{self.container}/{self.blob_path}"

    @staticmethod
    def ext_from_path(blob_path: str) -> str:
        suffix = PurePosixPath(blob_path.replace("\\", "/")).suffix
        return suffix[1:] if suffix else ""
