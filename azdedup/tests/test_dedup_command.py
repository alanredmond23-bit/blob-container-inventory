"""Tests for dedup partial and full command paths."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from rich.console import Console

from azdedup.commands import dedup as dedup_module
from azdedup.commands.dedup import run_dedup
from azdedup.config import DedupConfig
from azdedup.inventory import iter_inventory, resolve_inventory_paths
from azdedup.models.blob_ref import InventoryBlob
from azdedup.pipeline.partial_hash import partial_hash_from_ranges
from azdedup.tags import meta_tags_for_blob

FIXTURE = Path(__file__).parent / "fixtures" / "mini_inventory.csv"
QUIET = Console(quiet=True)


def _meta_tags(blob: InventoryBlob) -> dict[str, str]:
    return meta_tags_for_blob(blob)


def _partial_hash_for_blob(blob: InventoryBlob, read_bytes: int) -> str:
    content = (f"{blob.container}/{blob.blob_path}").encode("utf-8")
    repeated = (content * ((blob.size // len(content)) + 1))[: blob.size]
    head_len = min(read_bytes, blob.size)
    head = repeated[:head_len]
    if blob.size <= 2 * read_bytes:
        return partial_hash_from_ranges(head, b"", blob.size, read_bytes)
    tail = repeated[blob.size - read_bytes : blob.size]
    return partial_hash_from_ranges(head, tail, blob.size, read_bytes)


@pytest.fixture
def fixture_blobs() -> list[InventoryBlob]:
    paths = resolve_inventory_paths(str(FIXTURE))
    return list(iter_inventory(paths))


@pytest.fixture
def mock_partial_client(monkeypatch: pytest.MonkeyPatch, fixture_blobs: list[InventoryBlob]) -> MagicMock:
    client = MagicMock()
    tag_store: dict[tuple[str, str], dict[str, str]] = {
        (blob.container, blob.blob_path): _meta_tags(blob) for blob in fixture_blobs
    }

    def fake_get_tags(_client, container: str, blob_path: str) -> dict[str, str]:
        return dict(tag_store.get((container, blob_path), {}))

    def fake_compute_partial_hash(
        _client,
        container: str,
        blob_path: str,
        size: int,
        read_bytes: int,
    ) -> str:
        blob = InventoryBlob(
            container=container,
            blob_path=blob_path,
            size=size,
            etag="etag",
            ext=InventoryBlob.ext_from_path(blob_path),
        )
        return _partial_hash_for_blob(blob, read_bytes)

    monkeypatch.setattr(dedup_module, "get_blob_service_client", lambda _account: client)
    monkeypatch.setattr(dedup_module, "get_blob_tags", fake_get_tags)
    monkeypatch.setattr(dedup_module, "compute_partial_hash", fake_compute_partial_hash)
    return client


def test_partial_dry_run_produces_hash_fast(
    tmp_path: Path,
    fixture_blobs: list[InventoryBlob],
    mock_partial_client: MagicMock,
) -> None:
    output = tmp_path / "partial_dry_run.jsonl"
    config = DedupConfig(
        account="testaccount",
        containers="all",
        prefix="",
        concurrency=4,
        stage="partial",
        source="inventory",
        inventory_paths=[str(FIXTURE)],
        read_bytes=1024,
        incremental=False,
        force=False,
        apply_tags=False,
        dry_run_output=output,
        output_dir=tmp_path,
        assume_meta=True,
    )

    stats = run_dedup(config, console=QUIET)

    assert stats.scanned == len(fixture_blobs)
    lines = output.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == len(fixture_blobs)

    records = [json.loads(line) for line in lines]
    for record in records:
        assert record["hash_fast"]
        assert len(record["hash_fast"]) == 16
        assert record["tags"]["dedup_stage"] == "partial"
        assert record["tags"]["hash_fast"] == record["hash_fast"]

    dup_a = next(r for r in records if r["blob_path"] == "data/dup-a.bin")
    dup_b = next(r for r in records if r["blob_path"] == "data/dup-b.bin")
    assert dup_a["size"] == dup_b["size"] == 4096
    assert dup_a["hash_fast"] != dup_b["hash_fast"]


def test_partial_dry_run_skips_without_meta_when_not_assume_meta(
    tmp_path: Path,
    mock_partial_client: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        dedup_module,
        "get_blob_tags",
        lambda _client, _container, _blob_path: {},
    )
    output = tmp_path / "partial_dry_run.jsonl"
    config = DedupConfig(
        account="testaccount",
        containers="all",
        prefix="",
        concurrency=4,
        stage="partial",
        source="inventory",
        inventory_paths=[str(FIXTURE)],
        read_bytes=1024,
        incremental=False,
        force=False,
        apply_tags=False,
        dry_run_output=output,
        output_dir=tmp_path,
        assume_meta=False,
    )

    stats = run_dedup(config, console=QUIET)

    assert stats.skipped == len(list(iter_inventory(resolve_inventory_paths(str(FIXTURE)))))
    assert stats.scanned == 0
    assert not output.exists()


def test_full_dry_run_collision_group_hash_full(
    tmp_path: Path,
    mock_partial_client: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shared_hash_fast = "abcd1234ef567890"
    dup_paths = {
        ("container-a", "data/dup-a.bin"),
        ("container-a", "data/dup-b.bin"),
    }
    unique_paths = {
        ("container-b", "incoming/file2.csv"),
        ("container-b", "incoming/dup-match.bin"),
    }

    def fake_get_tags(_client, container: str, blob_path: str) -> dict[str, str]:
        key = (container, blob_path)
        if key in dup_paths:
            return {
                "dedup_stage": "partial",
                "hash_fast": shared_hash_fast,
                "dedup_etag": "etag-dup",
                "size": "4096",
            }
        if key in unique_paths:
            return {
                "dedup_stage": "partial",
                "hash_fast": f"unique-{container}-{blob_path}",
                "dedup_etag": "etag-unique",
                "size": "4096",
            }
        return {
            "dedup_stage": "partial",
            "hash_fast": f"solo-{container}-{blob_path}",
            "dedup_etag": "etag-solo",
            "size": "1024",
        }

    def fake_resolve_full_hash(_client, blob: InventoryBlob, *, content_md5=None) -> str:
        if (blob.container, blob.blob_path) in dup_paths:
            return hashlib.sha256(b"dup-content").hexdigest()
        return hashlib.sha256(f"{blob.container}/{blob.blob_path}".encode()).hexdigest()

    monkeypatch.setattr(dedup_module, "get_blob_tags", fake_get_tags)
    monkeypatch.setattr(dedup_module, "resolve_full_hash", fake_resolve_full_hash)

    output = tmp_path / "full_dry_run.jsonl"
    config = DedupConfig(
        account="testaccount",
        containers="all",
        prefix="",
        concurrency=4,
        stage="full",
        source="inventory",
        inventory_paths=[str(FIXTURE)],
        read_bytes=1024,
        incremental=False,
        force=False,
        apply_tags=False,
        dry_run_output=output,
        output_dir=tmp_path,
        assume_meta=True,
    )

    stats = run_dedup(config, console=QUIET)

    records = [json.loads(line) for line in output.read_text(encoding="utf-8").strip().splitlines()]
    assert len(records) == 2
    assert stats.scanned == 2

    hash_full_values = {record["hash_full"] for record in records}
    assert len(hash_full_values) == 1
    assert hash_full_values.pop() == hashlib.sha256(b"dup-content").hexdigest()

    paths = {record["blob_path"] for record in records}
    assert paths == {"data/dup-a.bin", "data/dup-b.bin"}


def test_run_dedup_canonical_dry_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from azdedup.tags import TAG_HASH_FULL

    dup_hash = hashlib.sha256(b"canonical-dup").hexdigest()
    blobs = [
        InventoryBlob(container="container-a", blob_path="a.bin", size=100, etag="e1", ext="bin"),
        InventoryBlob(container="container-a", blob_path="b.bin", size=100, etag="e2", ext="bin"),
    ]

    def fake_collect(_config: DedupConfig) -> list[InventoryBlob]:
        return blobs

    def fake_get_tags(_client, container: str, blob_path: str) -> dict[str, str]:
        return {TAG_HASH_FULL: dup_hash, "size": "100"}

    monkeypatch.setattr(dedup_module, "_collect_blobs", fake_collect)
    monkeypatch.setattr(dedup_module, "get_blob_tags", fake_get_tags)

    config = DedupConfig(
        account="testaccount",
        containers="all",
        prefix="",
        concurrency=4,
        stage="canonical",
        source="inventory",
        inventory_paths=[str(FIXTURE)],
        read_bytes=1024,
        incremental=False,
        force=False,
        apply_tags=False,
        dry_run_output=None,
        output_dir=tmp_path,
        assume_meta=True,
    )
    stats = run_dedup(config, console=QUIET)
    assert stats.scanned == 2
    out = tmp_path / "dedup/canonical_dry_run.jsonl"
    records = [json.loads(line) for line in out.read_text(encoding="utf-8").strip().splitlines()]
    assert sum(1 for r in records if r["tags"].get("canonical") == "true") == 1
    assert sum(1 for r in records if r["tags"].get("canonical") == "false") == 1
