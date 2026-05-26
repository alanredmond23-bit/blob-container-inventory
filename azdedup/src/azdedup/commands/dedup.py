"""Multi-stage hashing pipeline — partial, full, and canonical dedup passes."""

from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from azdedup.azure_client import get_blob_service_client, get_blob_tags, set_blob_tags
from azdedup.config import ContainersSpec, DedupConfig
from azdedup.inventory import iter_inventory, resolve_inventory_paths
from azdedup.models.blob_ref import InventoryBlob
from azdedup.pipeline.full_hash import CollisionGrouper, resolve_full_hash
from azdedup.pipeline.incremental import needs_full_scan, needs_partial_scan
from azdedup.pipeline.partial_hash import compute_partial_hash
from azdedup.tags import (
    STAGE_ORDER,
    TAG_HASH_FAST,
    full_tags_for_blob,
    merge_tags,
    parse_stage,
    partial_tags_for_blob,
)
from azdedup.workers.checkpoint import CheckpointWriter
from azdedup.workers.pool import ScanStats, run_scan_workers

PARTIAL_DRY_RUN_NAME = "dedup/partial_dry_run.jsonl"
FULL_DRY_RUN_NAME = "dedup/full_dry_run.jsonl"


@dataclass
class _DryRunRecord:
    blob: InventoryBlob
    tags: dict[str, str]
    hash_fast: str | None = None
    hash_full: str | None = None


def _container_filter(containers: ContainersSpec) -> set[str] | None:
    if containers == "all":
        return None
    if isinstance(containers, list):
        return set(containers)
    return {part.strip() for part in str(containers).split(",") if part.strip()}


def _inventory_glob(config: DedupConfig) -> str:
    if config.inventory_paths:
        return config.inventory_paths[0]
    return "artifacts/dedup/ag1/Alansinv_1000000_*.csv"


def _dry_run_output_path(config: DedupConfig) -> Path:
    if config.dry_run_output is not None:
        return config.dry_run_output
    if config.stage == "partial":
        return config.output_dir / PARTIAL_DRY_RUN_NAME
    return config.output_dir / FULL_DRY_RUN_NAME


def _checkpoint_path(config: DedupConfig) -> Path:
    return config.output_dir / f"checkpoints/dedup_{config.stage}.jsonl"


def _eligible_for_partial(
    existing_tags: dict[str, str] | None,
    *,
    assume_meta: bool,
) -> bool:
    if assume_meta:
        return True
    stage = parse_stage(existing_tags)
    return STAGE_ORDER.get(stage, 0) >= STAGE_ORDER["meta"]


def _should_partial_scan(
    existing_tags: dict[str, str] | None,
    etag: str,
    *,
    incremental: bool,
    force: bool,
) -> bool:
    if not incremental:
        return True
    return needs_partial_scan(existing_tags, etag, force=force)


def _should_full_scan(
    existing_tags: dict[str, str] | None,
    etag: str,
    *,
    incremental: bool,
    force: bool,
) -> bool:
    if not incremental:
        return True
    return needs_full_scan(existing_tags, etag, force=force)


def _collect_blobs(config: DedupConfig) -> list[InventoryBlob]:
    container_set = _container_filter(config.containers)

    if config.source == "inventory":
        paths = resolve_inventory_paths(_inventory_glob(config))
        return list(iter_inventory(paths, containers=container_set, prefix=config.prefix))

    client = get_blob_service_client(config.account)
    if container_set is None:
        from azdedup.azure_client import list_account_containers

        container_set = set(list_account_containers(client))

    blobs: list[InventoryBlob] = []
    for container in sorted(container_set):
        container_client = client.get_container_client(container)
        for item in container_client.list_blobs(name_starts_with=config.prefix or None):
            content_md5 = None
            if item.content_settings and item.content_settings.content_md5:
                raw = item.content_settings.content_md5
                if isinstance(raw, bytes):
                    content_md5 = raw.hex()
            blobs.append(
                InventoryBlob(
                    container=container,
                    blob_path=item.name,
                    size=item.size or 0,
                    etag=item.etag or "",
                    ext=InventoryBlob.ext_from_path(item.name),
                    content_md5=content_md5,
                )
            )
    return blobs


def _write_dry_run_jsonl(records: list[_DryRunRecord], output_path: Path) -> ScanStats:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            payload: dict[str, Any] = {
                "container": record.blob.container,
                "blob_path": record.blob.blob_path,
                "size": record.blob.size,
                "etag": record.blob.etag,
                "ext": record.blob.ext,
                "tags": record.tags,
            }
            if record.hash_fast is not None:
                payload["hash_fast"] = record.hash_fast
            if record.hash_full is not None:
                payload["hash_full"] = record.hash_full
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return ScanStats(scanned=len(records))


def _print_summary(
    console: Console,
    stats: ScanStats,
    *,
    stage: str,
    mode: str,
    total: int,
    output: Path | None,
    extra: dict[str, str] | None = None,
) -> None:
    table = Table(title=f"azdedup dedup ({stage}) summary", show_header=True, header_style="bold")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Stage", stage)
    table.add_row("Mode", mode)
    table.add_row("Total blobs", str(total))
    processed = stats.scanned + stats.tagged + stats.skipped
    table.add_row("Processed", str(processed))
    if stats.skipped:
        table.add_row("Skipped (incremental)", str(stats.skipped))
    if stats.tagged:
        table.add_row("Tagged", str(stats.tagged))
    if stats.scanned:
        table.add_row("Hashed", str(stats.scanned))
    if stats.errors:
        table.add_row("Errors", str(stats.errors))
    if extra:
        for key, value in extra.items():
            table.add_row(key, value)
    if output is not None:
        table.add_row("Output", str(output))
    console.print(table)


def _run_partial_apply_tags(
    blobs: list[InventoryBlob],
    config: DedupConfig,
    *,
    checkpoint_path: Path,
) -> ScanStats:
    client = get_blob_service_client(config.account)

    with CheckpointWriter(checkpoint_path) as checkpoint:

        def worker(blob: InventoryBlob) -> str:
            existing = get_blob_tags(client, blob.container, blob.blob_path)
            if not _eligible_for_partial(existing, assume_meta=config.assume_meta):
                return "skipped"
            if not _should_partial_scan(
                existing,
                blob.etag,
                incremental=config.incremental,
                force=config.force,
            ):
                return "skipped"

            hash_fast = compute_partial_hash(
                client,
                blob.container,
                blob.blob_path,
                blob.size,
                config.read_bytes,
            )
            merged = merge_tags(existing, partial_tags_for_blob(hash_fast, blob.etag, blob.size))
            set_blob_tags(client, blob.container, blob.blob_path, merged)
            checkpoint.write(
                container=blob.container,
                blob_path=blob.blob_path,
                action="tagged",
                tags=merged,
            )
            return "tagged"

        return run_scan_workers(blobs, worker, config.concurrency)


def _run_partial_dry_run(blobs: list[InventoryBlob], config: DedupConfig) -> ScanStats:
    client = get_blob_service_client(config.account)
    records: list[_DryRunRecord] = []
    lock = threading.Lock()
    stats = ScanStats()

    def worker(blob: InventoryBlob) -> None:
        nonlocal stats
        existing = get_blob_tags(client, blob.container, blob.blob_path)
        if not _eligible_for_partial(existing, assume_meta=config.assume_meta):
            with lock:
                stats.skipped += 1
            return
        if not _should_partial_scan(
            existing,
            blob.etag,
            incremental=config.incremental,
            force=config.force,
        ):
            with lock:
                stats.skipped += 1
            return

        hash_fast = compute_partial_hash(
            client,
            blob.container,
            blob.blob_path,
            blob.size,
            config.read_bytes,
        )
        tags = partial_tags_for_blob(hash_fast, blob.etag, blob.size)
        with lock:
            records.append(_DryRunRecord(blob=blob, tags=tags, hash_fast=hash_fast))
            stats.scanned += 1

    with ThreadPoolExecutor(max_workers=config.concurrency) as executor:
        futures = [executor.submit(worker, blob) for blob in blobs]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception:
                with lock:
                    stats.errors += 1

    output_path = _dry_run_output_path(config)
    if records:
        _write_dry_run_jsonl(records, output_path)
    return stats


def _run_partial(config: DedupConfig, console: Console) -> ScanStats:
    blobs = _collect_blobs(config)
    total = len(blobs)

    if config.apply_tags:
        checkpoint_path = _checkpoint_path(config)
        stats = _run_partial_apply_tags(blobs, config, checkpoint_path=checkpoint_path)
        _print_summary(
            console,
            stats,
            stage="partial",
            mode="apply-tags",
            total=total,
            output=checkpoint_path,
        )
        return stats

    stats = _run_partial_dry_run(blobs, config)
    _print_summary(
        console,
        stats,
        stage="partial",
        mode="dry-run",
        total=total,
        output=_dry_run_output_path(config),
    )
    return stats


def _build_collision_grouper(
    blobs: list[InventoryBlob],
    client,
) -> tuple[CollisionGrouper, int]:
    """Pass 1: group blobs that have hash_fast tags."""
    grouper = CollisionGrouper()
    skipped = 0
    for blob in blobs:
        existing = get_blob_tags(client, blob.container, blob.blob_path)
        hash_fast = existing.get(TAG_HASH_FAST)
        if not hash_fast:
            skipped += 1
            continue
        grouper.add(blob, hash_fast)
    return grouper, skipped


def _run_full_apply_tags(
    blobs: list[InventoryBlob],
    config: DedupConfig,
    *,
    checkpoint_path: Path,
    grouper: CollisionGrouper,
    pass1_skipped: int,
) -> ScanStats:
    client = get_blob_service_client(config.account)
    collision_groups = list(grouper.collision_groups())

    with CheckpointWriter(checkpoint_path) as checkpoint:

        def worker(entry_blob: InventoryBlob, existing: dict[str, str]) -> str:
            if not _should_full_scan(
                existing,
                entry_blob.etag,
                incremental=config.incremental,
                force=config.force,
            ):
                return "skipped"

            hash_full = resolve_full_hash(client, entry_blob)
            merged = merge_tags(existing, full_tags_for_blob(hash_full, entry_blob.etag, entry_blob.size))
            set_blob_tags(client, entry_blob.container, entry_blob.blob_path, merged)
            checkpoint.write(
                container=entry_blob.container,
                blob_path=entry_blob.blob_path,
                action="tagged",
                tags=merged,
            )
            return "tagged"

        work_items: list[tuple[InventoryBlob, dict[str, str]]] = []
        for members in collision_groups:
            for entry_blob in members:
                existing = get_blob_tags(client, entry_blob.container, entry_blob.blob_path)
                work_items.append((entry_blob, existing))

        stats = run_scan_workers(work_items, lambda item: worker(item[0], item[1]), config.concurrency)
        stats.skipped += pass1_skipped
        return stats


def _run_full_dry_run(
    blobs: list[InventoryBlob],
    config: DedupConfig,
    *,
    grouper: CollisionGrouper,
    pass1_skipped: int,
) -> ScanStats:
    client = get_blob_service_client(config.account)
    collision_groups = list(grouper.collision_groups())
    records: list[_DryRunRecord] = []
    lock = threading.Lock()
    stats = ScanStats(skipped=pass1_skipped)

    work_items: list[tuple[InventoryBlob, dict[str, str]]] = []
    for members in collision_groups:
        for entry_blob in members:
            existing = get_blob_tags(client, entry_blob.container, entry_blob.blob_path)
            work_items.append((entry_blob, existing))

    def worker(blob: InventoryBlob, existing: dict[str, str]) -> None:
        nonlocal stats
        if not _should_full_scan(
            existing,
            blob.etag,
            incremental=config.incremental,
            force=config.force,
        ):
            with lock:
                stats.skipped += 1
            return

        hash_full = resolve_full_hash(client, blob)
        tags = full_tags_for_blob(hash_full, blob.etag, blob.size)
        with lock:
            records.append(_DryRunRecord(blob=blob, tags=tags, hash_full=hash_full))
            stats.scanned += 1

    with ThreadPoolExecutor(max_workers=config.concurrency) as executor:
        futures = [executor.submit(worker, blob, tags) for blob, tags in work_items]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception:
                with lock:
                    stats.errors += 1

    output_path = _dry_run_output_path(config)
    if records:
        _write_dry_run_jsonl(records, output_path)
    return stats


def _run_full(config: DedupConfig, console: Console) -> ScanStats:
    blobs = _collect_blobs(config)
    total = len(blobs)
    client = get_blob_service_client(config.account)
    grouper, pass1_skipped = _build_collision_grouper(blobs, client)
    collision_groups = list(grouper.collision_groups())

    extra = {
        "Collision groups": str(len(collision_groups)),
        "Grouped blobs": str(sum(len(m) for m in collision_groups)),
    }

    if config.apply_tags:
        checkpoint_path = _checkpoint_path(config)
        stats = _run_full_apply_tags(
            blobs,
            config,
            checkpoint_path=checkpoint_path,
            grouper=grouper,
            pass1_skipped=pass1_skipped,
        )
        _print_summary(
            console,
            stats,
            stage="full",
            mode="apply-tags",
            total=total,
            output=checkpoint_path,
            extra=extra,
        )
        return stats

    stats = _run_full_dry_run(
        blobs,
        config,
        grouper=grouper,
        pass1_skipped=pass1_skipped,
    )
    _print_summary(
        console,
        stats,
        stage="full",
        mode="dry-run",
        total=total,
        output=_dry_run_output_path(config),
        extra=extra,
    )
    return stats


def run_dedup(config: DedupConfig, *, console: Console | None = None) -> ScanStats:
    """Run partial, full, or canonical dedup for inventory or live sources."""
    out = console or Console()

    if config.stage == "canonical":
        raise NotImplementedError("Phase 3")

    if config.stage == "partial":
        return _run_partial(config, out)

    if config.stage == "full":
        return _run_full(config, out)

    raise ValueError(f"Unsupported dedup stage: {config.stage!r}")
