"""Tests for full-stage hashing helpers."""

from __future__ import annotations

import base64

from azdedup.models.blob_ref import InventoryBlob
from azdedup.pipeline.full_hash import (
    CollisionGrouper,
    md5_shortcut_hash,
    normalize_inventory_md5,
    try_md5_group_hash,
)


def _blob(
    container: str,
    blob_path: str,
    *,
    size: int = 100,
    content_md5: str | None = None,
) -> InventoryBlob:
    return InventoryBlob(
        container=container,
        blob_path=blob_path,
        size=size,
        etag="etag",
        ext="bin",
        content_md5=content_md5,
    )


def test_normalize_inventory_md5_hex() -> None:
    assert normalize_inventory_md5("ABCDEF0123456789ABCDEF0123456789") == "abcdef0123456789abcdef0123456789"


def test_normalize_inventory_md5_base64() -> None:
    raw = base64.b64encode(bytes.fromhex("abcdef0123456789abcdef0123456789")).decode()
    assert normalize_inventory_md5(raw) == "abcdef0123456789abcdef0123456789"


def test_normalize_inventory_md5_empty_and_null() -> None:
    assert normalize_inventory_md5(None) is None
    assert normalize_inventory_md5("") is None
    assert normalize_inventory_md5("null") is None
    assert normalize_inventory_md5("none") is None


def test_md5_shortcut_hash() -> None:
    md5_hex = "abcdef0123456789abcdef0123456789"
    assert md5_shortcut_hash(md5_hex) == f"md5:{md5_hex}"


def test_collision_grouper_yields_only_multi_member_groups() -> None:
    grouper = CollisionGrouper()
    a = _blob("c1", "a.bin", size=10)
    b = _blob("c1", "b.bin", size=10)
    c = _blob("c2", "c.bin", size=10)
    solo = _blob("c2", "solo.bin", size=99)

    grouper.add(a, "hash1")
    grouper.add(b, "hash1")
    grouper.add(c, "hash1")
    grouper.add(solo, "hash2")

    groups = list(grouper.collision_groups())
    assert len(groups) == 1
    assert {m.blob_path for m in groups[0]} == {"a.bin", "b.bin", "c.bin"}


def test_collision_grouper_separates_size_and_hash_fast() -> None:
    grouper = CollisionGrouper()
    coll_a = _blob("c1", "coll-a.bin", size=10)
    coll_b = _blob("c1", "coll-b.bin", size=10)
    diff_size = _blob("c1", "large.bin", size=20)
    diff_hash_a = _blob("c1", "hash-a.bin", size=30)
    diff_hash_b = _blob("c1", "hash-b.bin", size=30)

    grouper.add(coll_a, "hash1")
    grouper.add(coll_b, "hash1")
    grouper.add(diff_size, "hash1")
    grouper.add(diff_hash_a, "hash1")
    grouper.add(diff_hash_b, "hash2")

    groups = list(grouper.collision_groups())
    assert len(groups) == 1
    assert {m.blob_path for m in groups[0]} == {"coll-a.bin", "coll-b.bin"}


def test_try_md5_group_hash_when_all_match() -> None:
    md5 = "abcdef0123456789abcdef0123456789"
    members = [
        _blob("c1", "a.bin", content_md5=md5),
        _blob("c2", "b.bin", content_md5=md5),
    ]
    assert try_md5_group_hash(members) == md5_shortcut_hash(md5)


def test_try_md5_group_hash_rejects_missing_or_mixed() -> None:
    md5 = "abcdef0123456789abcdef0123456789"
    assert try_md5_group_hash([_blob("c1", "a.bin", content_md5=md5), _blob("c2", "b.bin")]) is None
    assert (
        try_md5_group_hash(
            [
                _blob("c1", "a.bin", content_md5=md5),
                _blob("c2", "b.bin", content_md5="0123456789abcdef0123456789abcdef"),
            ]
        )
        is None
    )
