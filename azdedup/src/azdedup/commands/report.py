"""Dedup visibility report from inventory + blob tags or dry-run jsonl."""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

from rich.console import Console
from rich.table import Table

from azdedup.azure_client import get_blob_service_client, get_blob_tags
from azdedup.config import ReportConfig
from azdedup.inventory import iter_inventory, resolve_inventory_paths
from azdedup.models.stats import DedupReport
from azdedup.tags import TAG_CANONICAL, TAG_DEDUP_STAGE, TAG_HASH_FULL, TAG_SIZE, parse_stage


def _container_filter(containers) -> set[str] | None:
    if containers == "all":
        return None
    if isinstance(containers, list):
        return set(containers)
    return {p.strip() for p in str(containers).split(",") if p.strip()}


def _report_from_inventory_tags(config: ReportConfig) -> DedupReport:
    paths = resolve_inventory_paths(
        config.inventory_paths[0] if config.inventory_paths else "artifacts/dedup/ag1/Alansinv_1000000_*.csv"
    )
    container_set = _container_filter(config.containers)
    client = get_blob_service_client(config.account)
    report = DedupReport()
    seen_hashes: dict[tuple[int, str], int] = defaultdict(int)

    for blob in iter_inventory(paths, containers=container_set, prefix=config.prefix):
        if config.sample_rate < 1.0 and random.random() > config.sample_rate:
            continue
        report.total_blobs += 1
        report.by_container[blob.container] = report.by_container.get(blob.container, 0) + 1

        tags = get_blob_tags(client, blob.container, blob.blob_path)
        stage = parse_stage(tags)
        report.by_stage[stage] = report.by_stage.get(stage, 0) + 1

        hash_full = tags.get(TAG_HASH_FULL, "")
        size = int(tags.get(TAG_SIZE, blob.size))
        if hash_full:
            seen_hashes[(size, hash_full)] += 1

        if tags.get(TAG_CANONICAL) == "false":
            report.canonical_false += 1
            report.reclaimable_bytes += size

    for count in seen_hashes.values():
        if count >= 2:
            report.duplicate_blobs += count - 1
    report.unique_groups = len(seen_hashes)
    return report


def _report_from_jsonl(path: Path) -> DedupReport:
    report = DedupReport()
    seen_hashes: dict[tuple[int, str], int] = defaultdict(int)

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            report.total_blobs += 1
            container = row.get("container", "")
            report.by_container[container] = report.by_container.get(container, 0) + 1
            tags = row.get("tags") or {}
            stage = parse_stage(tags)
            report.by_stage[stage] = report.by_stage.get(stage, 0) + 1
            hash_full = tags.get(TAG_HASH_FULL) or row.get("hash_full", "")
            size = int(tags.get(TAG_SIZE, row.get("size", 0)))
            if hash_full:
                seen_hashes[(size, hash_full)] += 1
            if tags.get(TAG_CANONICAL) == "false":
                report.canonical_false += 1
                report.reclaimable_bytes += size

    for count in seen_hashes.values():
        if count >= 2:
            report.duplicate_blobs += count - 1
    report.unique_groups = len(seen_hashes)
    return report


def _print_report(console: Console, report: DedupReport, *, fmt: str, group_by: str) -> None:
    if fmt == "json":
        payload = {
            "total_blobs": report.total_blobs,
            "unique_hash_groups": report.unique_groups,
            "duplicate_blobs": report.duplicate_blobs,
            "reclaimable_bytes": report.reclaimable_bytes,
            "confidence": report.confidence,
            "by_stage": report.by_stage,
            "by_container": report.by_container if group_by == "container" else {},
        }
        console.print_json(json.dumps(payload))
        return

    table = Table(title="azdedup report", show_header=True, header_style="bold")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Total blobs", f"{report.total_blobs:,}")
    table.add_row("Unique (hash_full groups)", f"{report.unique_groups:,}")
    table.add_row("Duplicate blobs", f"{report.duplicate_blobs:,}")
    table.add_row("Reclaimable (non-canonical)", _fmt_bytes(report.reclaimable_bytes))
    table.add_row("Confidence", f"{report.confidence * 100:.4f}%")
    console.print(table)

    if group_by == "stage" and report.by_stage:
        st = Table(title="By stage")
        st.add_column("Stage")
        st.add_column("Count", justify="right")
        for stage, count in sorted(report.by_stage.items(), key=lambda x: -x[1]):
            st.add_row(stage, str(count))
        console.print(st)

    if group_by == "container" and report.by_container:
        ct = Table(title="By container (top 20)")
        ct.add_column("Container")
        ct.add_column("Count", justify="right")
        for container, count in sorted(report.by_container.items(), key=lambda x: -x[1])[:20]:
            ct.add_row(container, str(count))
        console.print(ct)


def _fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    for u in ("KiB", "MiB", "GiB", "TiB"):
        n /= 1024
        if n < 1024:
            return f"{n:.2f} {u}"
    return f"{n:.2f} PiB"


def run_report(config: ReportConfig, *, fmt: str = "table", console: Console | None = None) -> DedupReport:
    out = console or Console()

    if config.source == "inventory":
        report = _report_from_inventory_tags(config)
    elif config.source == "dry-run":
        path = config.input_path or config.output_dir / "dedup/full_dry_run.jsonl"
        if not path.is_file():
            path = config.output_dir / "dedup/partial_dry_run.jsonl"
        report = _report_from_jsonl(path)
    else:
        raise ValueError(f"Unsupported report source: {config.source}")

    out_path = config.output_dir / "reports" / "latest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            {
                "total_blobs": report.total_blobs,
                "duplicate_blobs": report.duplicate_blobs,
                "reclaimable_bytes": report.reclaimable_bytes,
                "confidence": report.confidence,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    _print_report(out, report, fmt=fmt, group_by=config.group_by)
    out.print(f"[dim]Wrote {out_path}[/dim]")
    return report
