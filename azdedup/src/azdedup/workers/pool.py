"""Thread-pool worker runner for scan passes."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Iterable, Literal, TypeVar

WorkerOutcome = Literal["scanned", "skipped", "tagged"]
T = TypeVar("T")


@dataclass
class ScanStats:
    scanned: int = 0
    skipped: int = 0
    tagged: int = 0
    errors: int = 0

    def increment(self, outcome: WorkerOutcome) -> None:
        setattr(self, outcome, getattr(self, outcome) + 1)


def run_scan_workers(
    items: Iterable[T],
    worker_fn: Callable[[T], WorkerOutcome],
    concurrency: int,
) -> ScanStats:
    """Process items concurrently and aggregate scan counters."""
    if concurrency < 1:
        raise ValueError(f"concurrency must be >= 1, got {concurrency}")

    stats = ScanStats()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(worker_fn, item) for item in items]
        for future in as_completed(futures):
            try:
                outcome = future.result()
            except Exception:
                stats.errors += 1
                continue
            stats.increment(outcome)
    return stats
