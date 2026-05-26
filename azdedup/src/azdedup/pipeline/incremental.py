"""Incremental skip logic for the scan (meta) pass."""

from __future__ import annotations

from azdedup.tags import STAGE_ORDER, TAG_DEDUP_ETAG, parse_stage


def needs_meta_scan(
    existing_tags: dict[str, str] | None,
    current_etag: str,
    force: bool = False,
) -> bool:
    """Return True when the blob needs a metadata scan and tag update."""
    if force:
        return True
    existing = existing_tags or {}
    stage = parse_stage(existing)
    if (
        existing.get(TAG_DEDUP_ETAG) == current_etag
        and STAGE_ORDER.get(stage, 0) >= STAGE_ORDER["meta"]
    ):
        return False
    return True


def should_apply_meta(
    existing_tags: dict[str, str] | None,
    blob_etag: str,
    force: bool = False,
) -> tuple[bool, str]:
    """Return whether meta tags should be applied and a short reason code."""
    if force:
        return True, "force"
    if not existing_tags:
        return True, "new_blob"
    stage = parse_stage(existing_tags)
    if existing_tags.get(TAG_DEDUP_ETAG) != blob_etag:
        return True, "etag_changed"
    if STAGE_ORDER.get(stage, 0) < STAGE_ORDER["meta"]:
        return True, "stage_below_meta"
    return False, "skip"
