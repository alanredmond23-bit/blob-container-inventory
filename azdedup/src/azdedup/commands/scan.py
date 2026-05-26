"""Discovery & metadata pass — inventory stream or live enumeration."""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

from azdedup.azure_client import get_blob_service_client, get_blob_tags, list_account_containers, set_blob_tags
from azdedup.config import ContainersSpec, ScanConfig
from azdedup.inventory import iter_inventory, resolve_inventory_paths
from azdedup.models.blob_ref import InventoryBlob
from azdedup.pipeline.incremental import needs_meta_scan
from azdedup.tags import merge_tags, meta_tags_for_blob
from azdedup.workers.checkpoint import CheckpointWriter
from azdedup.workers.pool import ScanStats, run_scan_workers

META_DRY_RUN_NAME = "scan/meta_dry_run.jsonl"
SCAN_CHECKPOINT_NAME = "checkpoints/scan_meta.jsonl"


def _container_filter(containers: ContainersSpec) -> set[str] | None:
    if containers == "all":
        return None
    if isinstance(containers, list):
        return set(containers)
    return {part.strip() for part in str(containers).split(",") if part.strip()}


def _inventory_glob(config: ScanConfig) -> str:
    if config.inventory_paths:
        return config.inventory_paths[0]
    return "artifacts/dedup/ag1/Alansinv_1000000_*.csv"


def _dry_run_output_path(config: ScanConfig) -> Path:
    if config.dry_run_output is not None:
        return config.dry_run_output
    return config.output_dir / META_DRY_RUN_NAME


def _checkpoint_path(config: ScanConfig) -> Path:
    return config.output_dir / SCAN_CHECKPOINT_NAME


def _write_dry_run_jsonl(blobs: list[InventoryBlob], output_path: Path) -> ScanStats:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for blob in blobs:
            record = {
                "container": blob.container,
                "blob_path": blob.blob_path,
                "size": blob.size,
                "etag": blob.etag,
                "ext": blob.ext,
                "tags": meta_tags_for_blob(blob),
            }
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    return ScanStats(scanned=len(blobs))


def _print_summary(
    console: Console,
    stats: ScanStats,
    *,
    mode: str,
    total: int,
    output: Path | None,
) -> None:
    table = Table(title="azdedup scan summary", show_header=True, header_style="bold")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Mode", mode)
    table.add_row("Total blobs", str(total))
    processed = stats.scanned + stats.tagged + stats.skipped
    table.add_row("Processed", str(processed))
    if stats.skipped:
        table.add_row("Skipped (incremental)", str(stats.skipped))
    if stats.tagged:
        table.add_row("Tagged", str(stats.tagged))
    if stats.errors:
        table.add_row("Errors", str(stats.errors))
    if output is not None:
        table.add_row("Output", str(output))
    console.print(table)


def _run_apply_tags(
    blobs: list[InventoryBlob],
    config: ScanConfig,
    *,
    checkpoint_path: Path,
) -> ScanStats:
    client = get_blob_service_client(config.account)

    with CheckpointWriter(checkpoint_path) as checkpoint:

        def worker(blob: InventoryBlob) -> str:
            existing = get_blob_tags(client, blob.container, blob.blob_path)
            if not needs_meta_scan(existing, blob.etag, force=config.force):
                return "skipped"
            merged = merge_tags(existing, meta_tags_for_blob(blob))
            set_blob_tags(client, blob.container, blob.blob_path, merged)
            checkpoint.write(
                container=blob.container,
                blob_path=blob.blob_path,
                action="tagged",
                tags=merged,
            )
            return "tagged"

        return run_scan_workers(blobs, worker, config.concurrency)


def run_scan(config: ScanConfig, *, console: Console | None = None) -> ScanStats:
    """Run metadata discovery for inventory or live sources."""
    out = console or Console()
    container_set = _container_filter(config.containers)

    if config.source == "inventory":
        paths = resolve_inventory_paths(_inventory_glob(config))
        blobs = list(iter_inventory(paths, containers=container_set, prefix=config.prefix))
        total = len(blobs)

        if not config.apply_tags:
            output_path = _dry_run_output_path(config)
            stats = _write_dry_run_jsonl(blobs, output_path)
            _print_summary(out, stats, mode="dry-run (inventory)", total=total, output=output_path)
            return stats

        checkpoint_path = _checkpoint_path(config)
        stats = _run_apply_tags(blobs, config, checkpoint_path=checkpoint_path)
        _print_summary(out, stats, mode="apply-tags (inventory)", total=total, output=checkpoint_path)
        return stats

    if config.source == "live":
        client = get_blob_service_client(config.account)
        if container_set is None:
            container_set = set(list_account_containers(client))

        blobs: list[InventoryBlob] = []
        for container in sorted(container_set):
            container_client = client.get_container_client(container)
            for item in container_client.list_blobs(name_starts_with=config.prefix or None):
                blobs.append(
                    InventoryBlob(
                        container=container,
                        blob_path=item.name,
                        size=item.size or 0,
                        etag=item.etag or "",
                        ext=InventoryBlob.ext_from_path(item.name),
                    )
                )
        total = len(blobs)

        if not config.apply_tags:
            output_path = _dry_run_output_path(config)
            stats = _write_dry_run_jsonl(blobs, output_path)
            _print_summary(out, stats, mode="dry-run (live)", total=total, output=output_path)
            return stats

        checkpoint_path = _checkpoint_path(config)
        stats = _run_apply_tags(blobs, config, checkpoint_path=checkpoint_path)
        _print_summary(out, stats, mode="apply-tags (live)", total=total, output=checkpoint_path)
        return stats

    raise ValueError(f"Unsupported scan source: {config.source!r}")
