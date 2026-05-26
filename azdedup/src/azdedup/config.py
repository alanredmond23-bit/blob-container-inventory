"""Scan configuration from environment and CLI overrides."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ContainersSpec = Literal["all"] | list[str]
ScanSource = Literal["live", "inventory"]
DedupStage = Literal["partial", "full", "canonical"]

DEFAULT_OUTPUT_DIR = Path("artifacts/dedup/azdedup")
DEFAULT_CONCURRENCY = 64
DEFAULT_DEDUP_CONCURRENCY = 32
DEFAULT_READ_BYTES = 1_048_576


def _parse_bool(value: str | bool | None, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _parse_containers(value: str | ContainersSpec) -> ContainersSpec:
    if isinstance(value, list):
        return value
    if value.strip().lower() == "all":
        return "all"
    return [part.strip() for part in value.split(",") if part.strip()]


def _parse_inventory_paths(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(p) for p in value if str(p).strip()]
    return [part.strip() for part in value.split(",") if part.strip()]


def _parse_path(value: str | Path | None) -> Path | None:
    if value is None or value == "":
        return None
    return Path(value)


@dataclass(frozen=True)
class ScanConfig:
    account: str
    containers: ContainersSpec
    prefix: str
    concurrency: int
    source: ScanSource
    inventory_paths: list[str]
    apply_tags: bool
    dry_run_output: Path | None
    force: bool
    output_dir: Path


def load_scan_config_from_env(account: str, **cli_overrides) -> ScanConfig:
    """Build ScanConfig from AZDEDUP_* env vars with CLI overrides winning."""

    def pick(name: str, env_key: str, default):
        if name in cli_overrides and cli_overrides[name] is not None:
            return cli_overrides[name]
        env_val = os.environ.get(env_key)
        return env_val if env_val is not None else default

    containers_raw = pick("containers", "AZDEDUP_CONTAINERS", "all")
    inventory_raw = pick("inventory_paths", "AZDEDUP_INVENTORY_PATHS", "")
    dry_run_raw = pick("dry_run_output", "AZDEDUP_DRY_RUN_OUTPUT", None)
    output_dir_raw = pick("output_dir", "AZDEDUP_OUTPUT_DIR", str(DEFAULT_OUTPUT_DIR))

    source_raw = str(pick("source", "AZDEDUP_SOURCE", "live")).lower()
    if source_raw not in ("live", "inventory"):
        raise ValueError(f"invalid scan source: {source_raw!r} (expected live|inventory)")

    concurrency_raw = pick("concurrency", "AZDEDUP_CONCURRENCY", str(DEFAULT_CONCURRENCY))
    concurrency = int(concurrency_raw)
    if concurrency < 1:
        raise ValueError(f"concurrency must be >= 1, got {concurrency}")

    return ScanConfig(
        account=account,
        containers=_parse_containers(containers_raw),
        prefix=str(pick("prefix", "AZDEDUP_PREFIX", "")),
        concurrency=concurrency,
        source=source_raw,  # type: ignore[arg-type]
        inventory_paths=_parse_inventory_paths(inventory_raw),
        apply_tags=_parse_bool(pick("apply_tags", "AZDEDUP_APPLY_TAGS", "false"), False),
        dry_run_output=_parse_path(dry_run_raw),
        force=_parse_bool(pick("force", "AZDEDUP_FORCE", "false"), False),
        output_dir=Path(output_dir_raw),
    )


@dataclass(frozen=True)
class DedupConfig:
    account: str
    containers: ContainersSpec
    prefix: str
    concurrency: int
    stage: DedupStage
    source: ScanSource
    inventory_paths: list[str]
    read_bytes: int
    incremental: bool
    force: bool
    apply_tags: bool
    dry_run_output: Path | None
    output_dir: Path
    assume_meta: bool


def load_dedup_config_from_env(account: str, **cli_overrides) -> DedupConfig:
    """Build DedupConfig from AZDEDUP_* env vars with CLI overrides winning."""

    def pick(name: str, env_key: str, default):
        if name in cli_overrides and cli_overrides[name] is not None:
            return cli_overrides[name]
        env_val = os.environ.get(env_key)
        return env_val if env_val is not None else default

    containers_raw = pick("containers", "AZDEDUP_CONTAINERS", "all")
    inventory_raw = pick("inventory_paths", "AZDEDUP_INVENTORY_PATHS", "")
    dry_run_raw = pick("dry_run_output", "AZDEDUP_DRY_RUN_OUTPUT", None)
    output_dir_raw = pick("output_dir", "AZDEDUP_OUTPUT_DIR", str(DEFAULT_OUTPUT_DIR))

    source_raw = str(pick("source", "AZDEDUP_SOURCE", "live")).lower()
    if source_raw not in ("live", "inventory"):
        raise ValueError(f"invalid dedup source: {source_raw!r} (expected live|inventory)")

    stage_raw = str(pick("stage", "AZDEDUP_STAGE", "")).lower()
    if stage_raw not in ("partial", "full", "canonical"):
        raise ValueError(
            f"invalid dedup stage: {stage_raw!r} (expected partial|full|canonical)"
        )

    concurrency_raw = pick("concurrency", "AZDEDUP_CONCURRENCY", str(DEFAULT_DEDUP_CONCURRENCY))
    concurrency = int(concurrency_raw)
    if concurrency < 1:
        raise ValueError(f"concurrency must be >= 1, got {concurrency}")

    read_bytes_raw = pick("read_bytes", "AZDEDUP_READ_BYTES", str(DEFAULT_READ_BYTES))
    read_bytes = int(read_bytes_raw)
    if read_bytes < 1:
        raise ValueError(f"read_bytes must be >= 1, got {read_bytes}")

    assume_meta_default = source_raw == "inventory"
    assume_meta = _parse_bool(
        pick("assume_meta", "AZDEDUP_ASSUME_META", None),
        assume_meta_default,
    )

    return DedupConfig(
        account=account,
        containers=_parse_containers(containers_raw),
        prefix=str(pick("prefix", "AZDEDUP_PREFIX", "")),
        concurrency=concurrency,
        stage=stage_raw,  # type: ignore[arg-type]
        source=source_raw,  # type: ignore[arg-type]
        inventory_paths=_parse_inventory_paths(inventory_raw),
        read_bytes=read_bytes,
        incremental=_parse_bool(pick("incremental", "AZDEDUP_INCREMENTAL", "false"), False),
        force=_parse_bool(pick("force", "AZDEDUP_FORCE", "false"), False),
        apply_tags=_parse_bool(pick("apply_tags", "AZDEDUP_APPLY_TAGS", "false"), False),
        dry_run_output=_parse_path(dry_run_raw),
        output_dir=Path(output_dir_raw),
        assume_meta=assume_meta,
    )
