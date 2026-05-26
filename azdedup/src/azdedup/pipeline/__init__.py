"""Pipeline stages for incremental deduplication."""

from azdedup.pipeline.incremental import (
    needs_full_scan,
    needs_meta_scan,
    needs_partial_scan,
    should_apply_meta,
)

__all__ = [
    "needs_full_scan",
    "needs_meta_scan",
    "needs_partial_scan",
    "should_apply_meta",
]
