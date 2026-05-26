"""Tests for inventory-backed scan dry-run."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from rich.console import Console

from azdedup.commands.scan import run_scan
from azdedup.config import ScanConfig
from azdedup.inventory import iter_inventory, resolve_inventory_paths


FIXTURE = Path(__file__).parent / "fixtures" / "mini_inventory.csv"
EXPECTED_ACTIVE_ROWS = 9
QUIET = Console(quiet=True)


def test_iter_inventory_fixture() -> None:
    paths = resolve_inventory_paths(str(FIXTURE))
    blobs = list(iter_inventory(paths))
    assert len(blobs) == EXPECTED_ACTIVE_ROWS
    containers = {blob.container for blob in blobs}
    assert containers == {"container-a", "container-b"}

    dup_sizes = [blob.size for blob in blobs if blob.size == 4096]
    assert len(dup_sizes) == 4


def test_iter_inventory_container_filter() -> None:
    paths = resolve_inventory_paths(str(FIXTURE))
    blobs = list(iter_inventory(paths, containers={"container-a"}))
    assert len(blobs) == 5
    assert all(blob.container == "container-a" for blob in blobs)


def test_iter_inventory_prefix_filter() -> None:
    paths = resolve_inventory_paths(str(FIXTURE))
    blobs = list(iter_inventory(paths, prefix="incoming/"))
    assert len(blobs) == 3
    assert all(blob.blob_path.startswith("incoming/") for blob in blobs)


def test_run_scan_dry_run_jsonl_line_count(tmp_path: Path) -> None:
    output = tmp_path / "meta_dry_run.jsonl"
    config = ScanConfig(
        account="testaccount",
        containers="all",
        prefix="",
        concurrency=64,
        source="inventory",
        inventory_paths=[str(FIXTURE)],
        apply_tags=False,
        dry_run_output=output,
        force=False,
        output_dir=tmp_path,
    )
    stats = run_scan(config, console=QUIET)
    assert stats.scanned == EXPECTED_ACTIVE_ROWS

    lines = output.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == EXPECTED_ACTIVE_ROWS

    first = json.loads(lines[0])
    assert {"container", "blob_path", "size", "etag", "ext", "tags"} <= set(first.keys())
    assert first["tags"]["dedup_stage"] == "meta"


def test_run_scan_requires_inventory_files(tmp_path: Path) -> None:
    config = ScanConfig(
        account="testaccount",
        containers="all",
        prefix="",
        concurrency=64,
        source="inventory",
        inventory_paths=[str(tmp_path / "missing_*.csv")],
        apply_tags=False,
        dry_run_output=tmp_path / "out.jsonl",
        force=False,
        output_dir=tmp_path,
    )
    with pytest.raises(FileNotFoundError):
        run_scan(config, console=QUIET)
