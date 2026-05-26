from pathlib import Path

import pytest

from azdedup.config import load_dedup_config_from_env


def test_load_dedup_config_defaults(monkeypatch) -> None:
    monkeypatch.delenv("AZDEDUP_CONTAINERS", raising=False)
    monkeypatch.delenv("AZDEDUP_STAGE", raising=False)
    monkeypatch.delenv("AZDEDUP_SOURCE", raising=False)
    monkeypatch.delenv("AZDEDUP_ASSUME_META", raising=False)

    cfg = load_dedup_config_from_env("myaccount", stage="partial")

    assert cfg.account == "myaccount"
    assert cfg.containers == "all"
    assert cfg.prefix == ""
    assert cfg.concurrency == 32
    assert cfg.stage == "partial"
    assert cfg.source == "live"
    assert cfg.inventory_paths == []
    assert cfg.read_bytes == 1_048_576
    assert cfg.incremental is False
    assert cfg.force is False
    assert cfg.apply_tags is False
    assert cfg.dry_run_output is None
    assert cfg.output_dir == Path("artifacts/dedup/azdedup")
    assert cfg.assume_meta is False


def test_load_dedup_config_inventory_assume_meta_default(monkeypatch) -> None:
    monkeypatch.delenv("AZDEDUP_ASSUME_META", raising=False)

    cfg = load_dedup_config_from_env(
        "myaccount",
        stage="full",
        source="inventory",
        inventory_paths=["a.csv"],
    )

    assert cfg.source == "inventory"
    assert cfg.inventory_paths == ["a.csv"]
    assert cfg.assume_meta is True


def test_load_dedup_config_cli_overrides(monkeypatch) -> None:
    monkeypatch.setenv("AZDEDUP_CONTAINERS", "all")
    monkeypatch.setenv("AZDEDUP_CONCURRENCY", "128")
    monkeypatch.setenv("AZDEDUP_READ_BYTES", "524288")
    monkeypatch.setenv("AZDEDUP_INCREMENTAL", "true")
    monkeypatch.setenv("AZDEDUP_ASSUME_META", "false")

    cfg = load_dedup_config_from_env(
        "myaccount",
        stage="canonical",
        containers="c1,c2",
        prefix="org/",
        concurrency=64,
        source="inventory",
        inventory_paths=["a.csv", "b.csv"],
        read_bytes=2_097_152,
        incremental=False,
        force=True,
        apply_tags=True,
        dry_run_output="dry.jsonl",
        output_dir="out/dedup",
        assume_meta=True,
    )

    assert cfg.containers == ["c1", "c2"]
    assert cfg.prefix == "org/"
    assert cfg.concurrency == 64
    assert cfg.stage == "canonical"
    assert cfg.source == "inventory"
    assert cfg.inventory_paths == ["a.csv", "b.csv"]
    assert cfg.read_bytes == 2_097_152
    assert cfg.incremental is False
    assert cfg.force is True
    assert cfg.apply_tags is True
    assert cfg.dry_run_output == Path("dry.jsonl")
    assert cfg.output_dir == Path("out/dedup")
    assert cfg.assume_meta is True


@pytest.mark.parametrize("stage", ["partial", "full", "canonical"])
def test_load_dedup_config_accepts_all_stages(monkeypatch, stage: str) -> None:
    monkeypatch.delenv("AZDEDUP_STAGE", raising=False)
    cfg = load_dedup_config_from_env("acct", stage=stage)
    assert cfg.stage == stage


def test_load_dedup_config_invalid_stage(monkeypatch) -> None:
    monkeypatch.delenv("AZDEDUP_STAGE", raising=False)
    with pytest.raises(ValueError, match="invalid dedup stage"):
        load_dedup_config_from_env("acct", stage="invalid")
