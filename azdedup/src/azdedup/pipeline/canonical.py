"""Canonical selection within duplicate groups (mark-only, no deletes)."""

from __future__ import annotations

import uuid
from typing import Any, Literal

CanonicalStrategy = Literal["oldest", "shortest", "container_priority"]

KEEP_CONTAINER_PRIORITY = (
    "discovery",
    "five9-calls",
    "evidence",
    "legal",
    "gmail-takeout",
)

DEPRIORITIZE_CONTAINERS = (
    "ice-cold-triage",
    "backups",
    "uploads",
    "123triageonedrive",
    "45gb-final-onedrive",
    "bin",
)


def _container_rank(container: str) -> tuple[int, int, str]:
    c = container.lower()
    for i, pref in enumerate(KEEP_CONTAINER_PRIORITY):
        if pref in c:
            return (0, i, c)
    for pref in DEPRIORITIZE_CONTAINERS:
        if pref in c:
            return (2, 0, c)
    return (1, 0, c)


def pick_canonical(members: list[Any], strategy: CanonicalStrategy = "container_priority") -> Any:
    """Choose the single canonical blob from a duplicate group."""

    def key_oldest(m: Any) -> tuple:
        lm = getattr(m, "last_modified", None) or ""
        return (lm, m.container, m.blob_path)

    def key_shortest(m: Any) -> tuple:
        return (len(m.blob_path), m.container, m.blob_path)

    def key_container_priority(m: Any) -> tuple:
        depth = m.blob_path.count("/")
        return (_container_rank(m.container), depth, -len(m.blob_path), m.last_modified or "", m.container, m.blob_path)

    if strategy == "oldest":
        return min(members, key=key_oldest)
    if strategy == "shortest":
        return min(members, key=key_shortest)
    return min(members, key=key_container_priority)


def new_canonical_id() -> str:
    return str(uuid.uuid4())


class FullHashGrouper:
    """Group blobs by (size, hash_full) for canonical marking."""

    def __init__(self) -> None:
        self._groups: dict[tuple[int, str], list[Any]] = {}

    def add(self, blob: Any, hash_full: str) -> None:
        key = (blob.size, hash_full)
        self._groups.setdefault(key, []).append(blob)

    def duplicate_groups(self) -> list[tuple[str, list[Any]]]:
        """Return (canonical_id, members) for groups with 2+ blobs."""
        out: list[tuple[str, list[Any]]] = []
        for members in self._groups.values():
            if len(members) >= 2:
                out.append((new_canonical_id(), members))
        return out
