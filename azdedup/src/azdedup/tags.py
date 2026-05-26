"""Blob Index Tag schema (authoritative state on each blob)."""

from __future__ import annotations

from typing import Literal

DedupStage = Literal["none", "meta", "partial", "full", "canonical"]

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


def merge_tags(existing: dict[str, str], updates: dict[str, str]) -> dict[str, str]:
    merged = dict(existing or {})
    merged.update({k: str(v) for k, v in updates.items() if v is not None})
    if len(merged) > 10:
        # Drop ext first per plan §4 overflow strategy
        merged.pop(TAG_EXT, None)
    return merged
