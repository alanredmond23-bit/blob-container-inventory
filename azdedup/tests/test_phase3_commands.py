"""Phase 3 command tests (canonical dry-run, report from jsonl)."""

import json
from pathlib import Path

from azdedup.commands.dedup import run_dedup
from azdedup.commands.report import run_report
from azdedup.config import DedupConfig, ReportConfig
from azdedup.tags import TAG_CANONICAL, TAG_HASH_FULL, canonical_tags_for_blob


def test_canonical_dry_run_groups_duplicates(tmp_path, monkeypatch) -> None:
    blobs = []

    def fake_collect(config):
        return blobs

    def fake_tags(client, container, blob_path):
        return {TAG_HASH_FULL: "samehash", "size": "4096"}

    monkeypatch.setattr("azdedup.commands.dedup._collect_blobs", fake_collect)
    monkeypatch.setattr("azdedup.commands.dedup.get_blob_tags", fake_tags)

    from azdedup.models.blob_ref import InventoryBlob

    blobs.extend(
        [
            InventoryBlob(container="c", blob_path="a.bin", size=4096, etag="e1", ext="bin"),
            InventoryBlob(container="c", blob_path="b.bin", size=4096, etag="e2", ext="bin"),
        ]
    )

    config = DedupConfig(
        account="acct",
        containers="all",
        prefix="",
        concurrency=2,
        stage="canonical",
        source="inventory",
        inventory_paths=[],
        read_bytes=1024,
        incremental=False,
        force=False,
        apply_tags=False,
        dry_run_output=None,
        output_dir=tmp_path,
        assume_meta=True,
    )
    run_dedup(config)
    out = tmp_path / "dedup/canonical_dry_run.jsonl"
    assert out.is_file()
    lines = out.read_text().strip().splitlines()
    assert len(lines) == 2
    rows = [json.loads(ln) for ln in lines]
    assert sum(1 for r in rows if r["tags"].get(TAG_CANONICAL) == "true") == 1
    assert sum(1 for r in rows if r["tags"].get(TAG_CANONICAL) == "false") == 1


def test_report_from_dry_run_jsonl(tmp_path) -> None:
    path = tmp_path / "full.jsonl"
    rows = [
        {
            "container": "c",
            "blob_path": "a",
            "size": 100,
            "tags": canonical_tags_for_blob(is_canonical=True, canonical_id="id1", etag="e", size=100),
        },
        {
            "container": "c",
            "blob_path": "b",
            "size": 100,
            "tags": {
                **canonical_tags_for_blob(is_canonical=False, canonical_id="id1", etag="e", size=100),
                TAG_HASH_FULL: "hf1",
            },
        },
    ]
    with path.open("w") as f:
        for row in rows:
            row["tags"][TAG_HASH_FULL] = row["tags"].get(TAG_HASH_FULL, "hf1")
            f.write(json.dumps(row) + "\n")

    config = ReportConfig(
        account="a",
        containers="all",
        prefix="",
        source="dry-run",
        inventory_paths=[],
        input_path=path,
        group_by="none",
        output_dir=tmp_path,
    )
    report = run_report(config, fmt="json")
    assert report.total_blobs == 2
    assert report.canonical_false == 1
    assert report.reclaimable_bytes == 100
