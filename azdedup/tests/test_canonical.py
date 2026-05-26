"""Tests for canonical selection."""

from azdedup.models.blob_ref import InventoryBlob
from azdedup.pipeline.canonical import FullHashGrouper, pick_canonical


def _blob(container: str, path: str, size: int = 100, lm: str = "") -> InventoryBlob:
    return InventoryBlob(
        container=container,
        blob_path=path,
        size=size,
        etag="e1",
        ext="bin",
        last_modified=lm or None,
    )


def test_pick_canonical_shortest() -> None:
    members = [
        _blob("c", "a/short.bin"),
        _blob("c", "a/much/longer/path/file.bin"),
    ]
    winner = pick_canonical(members, "shortest")
    assert winner.blob_path == "a/short.bin"


def test_pick_canonical_container_priority_prefers_discovery() -> None:
    members = [
        _blob("backups", "x.bin"),
        _blob("discovery", "y.bin"),
    ]
    winner = pick_canonical(members, "container_priority")
    assert winner.container == "discovery"


def test_full_hash_grouper_duplicate_groups() -> None:
    g = FullHashGrouper()
    b1 = _blob("c", "a.bin", size=4096)
    b2 = _blob("c", "b.bin", size=4096)
    b3 = _blob("c", "c.bin", size=100)
    g.add(b1, "abc123")
    g.add(b2, "abc123")
    g.add(b3, "def456")
    groups = g.duplicate_groups()
    assert len(groups) == 1
    _cid, members = groups[0]
    assert len(members) == 2
