"""Pipeline stages for incremental deduplication."""

from azdedup.pipeline.incremental import needs_meta_scan, should_apply_meta

__all__ = ["needs_meta_scan", "should_apply_meta"]
