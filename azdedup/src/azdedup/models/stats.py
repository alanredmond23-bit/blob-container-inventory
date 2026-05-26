"""Aggregated dedup statistics for report output."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DedupReport:
    total_blobs: int = 0
    unique_groups: int = 0
    duplicate_blobs: int = 0
    reclaimable_bytes: int = 0
    by_container: dict[str, int] = field(default_factory=dict)
    by_stage: dict[str, int] = field(default_factory=dict)
    canonical_false: int = 0
    verify_sampled: int = 0
    verify_mismatches: int = 0

    @property
    def confidence(self) -> float:
        if self.verify_sampled == 0:
            return 1.0
        return 1.0 - (self.verify_mismatches / self.verify_sampled)
