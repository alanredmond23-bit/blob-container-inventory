"""Blob Index Tag schema (authoritative state on each blob)."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Literal

from azdedup.models.blob_ref import InventoryBlob

DedupStage = Literal["none", "meta", "partial", "full", "canonical"]

STAGE_ORDER: dict[str, int] = {
    "none": 0,
    "meta": 1,
    "partial": 2,
    "full": 3,
    "canonical": 4,
}

TAG_DEDUP_STAGE = "dedup_stage"
TAG_SIZE = "size"
TAG_EXT = "ext"
TAG_HASH_FAST = "hash_fast"
TAG_HASH_FULL = "hash_full"
TAG_CANONICAL = "canonical"
TAG_CANONICAL_ID = "canonical_id"
TAG_DEDUP_ETAG = "dedup_etag"

REQUIRED_FOR_STAGE: dict[DedupStage, tuple[str, ...]] = {
    "meta": (TAG_DEDUP_STAGE, TAG_SIZE, TAG_DEDUP_ETAG),
    "partial": (TAG_HASH_FAST,),
    "full": (TAG_HASH_FULL,),
    "canonical": (TAG_CANONICAL, TAG_CANONICAL_ID),
}


def file_extension(blob_path: str) -> str:
    """Return extension without dot from a blob path (POSIX-style)."""
    return PurePosixPath(blob_path).suffix.lstrip(".")


def partial_tags_for_blob(hash_fast: str, etag: str, size: int) -> dict[str, str]:
    """Tags written by the dedup (partial) pass."""
    return {
        TAG_DEDUP_STAGE: "partial",
        TAG_HASH_FAST: hash_fast,
        TAG_DEDUP_ETAG: etag,
        TAG_SIZE: str(size),
    }


def full_tags_for_blob(hash_full: str, etag: str, size: int) -> dict[str, str]:
    """Tags written by the dedup (full) pass."""
    return {
        TAG_DEDUP_STAGE: "full",
        TAG_HASH_FULL: hash_full,
        TAG_DEDUP_ETAG: etag,
        TAG_SIZE: str(size),
    }


def meta_tags_for_blob(size_or_blob: int | InventoryBlob, ext: str = "", etag: str = "") -> dict[str, str]:
    """Tags written by the scan (meta) pass."""
    if isinstance(size_or_blob, InventoryBlob):
        blob = size_or_blob
        tags = {
            TAG_DEDUP_STAGE: "meta",
            TAG_SIZE: str(blob.size),
            TAG_DEDUP_ETAG: blob.etag,
        }
        if blob.ext:
            tags[TAG_EXT] = blob.ext
        return tags
    return {
        TAG_DEDUP_STAGE: "meta",
        TAG_SIZE: str(size_or_blob),
        TAG_EXT: ext,
        TAG_DEDUP_ETAG: etag,
    }


def parse_stage(tags: dict[str, str] | None) -> DedupStage:
    if not tags:
        return "none"
    stage = tags.get(TAG_DEDUP_STAGE, "none")
    if stage in STAGE_ORDER:
        return stage  # type: ignore[return-value]
    return "none"


def merge_tags(existing: dict[str, str], updates: dict[str, str]) -> dict[str, str]:
    merged = dict(existing or {})
    merged.update({k: str(v) for k, v in updates.items() if v is not None})
    if len(merged) > 10:
        # Drop ext first per plan §4 overflow strategy
        merged.pop(TAG_EXT, None)
    return merged
