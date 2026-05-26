import json
from pathlib import Path

from azdedup.config import load_scan_config_from_env
from azdedup.workers.checkpoint import CheckpointWriter
from azdedup.workers.pool import run_scan_workers


def test_load_scan_config_defaults(monkeypatch) -> None:
    monkeypatch.delenv("AZDEDUP_CONTAINERS", raising=False)
    cfg = load_scan_config_from_env("myaccount")
    assert cfg.account == "myaccount"
    assert cfg.containers == "all"
    assert cfg.concurrency == 64
    assert cfg.source == "live"
    assert cfg.apply_tags is False
    assert cfg.output_dir == Path("artifacts/dedup/azdedup")


def test_load_scan_config_cli_overrides(monkeypatch) -> None:
    monkeypatch.setenv("AZDEDUP_CONTAINERS", "all")
    monkeypatch.setenv("AZDEDUP_CONCURRENCY", "128")
    cfg = load_scan_config_from_env(
        "myaccount",
        containers="c1,c2",
        apply_tags=True,
        source="inventory",
        inventory_paths=["a.csv", "b.csv"],
    )
    assert cfg.containers == ["c1", "c2"]
    assert cfg.concurrency == 128
    assert cfg.apply_tags is True
    assert cfg.source == "inventory"
    assert cfg.inventory_paths == ["a.csv", "b.csv"]


def test_checkpoint_writer_appends_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "shard.jsonl"
    with CheckpointWriter(path) as writer:
        writer.write(
            container="c1",
            blob_path="a/b.txt",
            action="tagged",
            tags={"dedup_stage": "meta"},
            ts="2026-05-26T00:00:00+00:00",
        )
    line = json.loads(path.read_text(encoding="utf-8").strip())
    assert line["container"] == "c1"
    assert line["blob_path"] == "a/b.txt"
    assert line["action"] == "tagged"
    assert line["tags"]["dedup_stage"] == "meta"
    assert line["ts"] == "2026-05-26T00:00:00+00:00"


def test_run_scan_workers_aggregates_stats() -> None:
    def worker(item: int) -> str:
        if item % 2 == 0:
            return "skipped"
        return "tagged"

    stats = run_scan_workers(range(1, 6), worker, concurrency=2)
    assert stats.tagged == 3
    assert stats.skipped == 2
    assert stats.errors == 0


def test_run_scan_workers_counts_errors() -> None:
    def worker(_: int) -> str:
        raise ValueError("fail")

    stats = run_scan_workers([1, 2], worker, concurrency=2)
    assert stats.errors == 2
    assert stats.tagged == 0
