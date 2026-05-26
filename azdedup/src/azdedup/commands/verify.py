"""Spot-verify hash_full tags by re-hashing sampled non-canonical blobs."""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.table import Table

from azdedup.azure_client import get_blob_service_client, get_blob_tags
from azdedup.config import VerifyConfig
from azdedup.inventory import iter_inventory, resolve_inventory_paths
from azdedup.pipeline.full_hash import sha256_blob
from azdedup.tags import TAG_CANONICAL, TAG_HASH_FULL


def _container_filter(containers) -> set[str] | None:
    if containers == "all":
        return None
    if isinstance(containers, list):
        return set(containers)
    return {p.strip() for p in str(containers).split(",") if p.strip()}


def run_verify(config: VerifyConfig, *, console: Console | None = None) -> dict:
    out = console or Console()
    paths = resolve_inventory_paths(
        config.inventory_paths[0] if config.inventory_paths else "artifacts/dedup/ag1/Alansinv_1000000_*.csv"
    )
    container_set = _container_filter(config.containers)
    client = get_blob_service_client(config.account)

    sampled = 0
    mismatches = 0
    mismatch_rows: list[dict] = []

    for blob in iter_inventory(paths, containers=container_set, prefix=config.prefix):
        if random.random() > config.sample_rate:
            continue
        tags = get_blob_tags(client, blob.container, blob.blob_path)
        if tags.get(TAG_CANONICAL) != "false":
            continue
        expected = tags.get(TAG_HASH_FULL, "")
        if not expected or expected.startswith("md5:"):
            continue

        sampled += 1
        actual = sha256_blob(client, blob.container, blob.blob_path)
        if actual != expected:
            mismatches += 1
            mismatch_rows.append(
                {
                    "container": blob.container,
                    "blob_path": blob.blob_path,
                    "expected": expected,
                    "actual": actual,
                }
            )

    confidence = 1.0 if sampled == 0 else 1.0 - (mismatches / sampled)
    result = {
        "sampled": sampled,
        "mismatches": mismatches,
        "confidence": confidence,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    out_path = config.output_dir / "verify" / f"verify_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({**result, "mismatch_samples": mismatch_rows[:20]}, indent=2), encoding="utf-8")

    table = Table(title="azdedup verify", show_header=True, header_style="bold")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Sampled (non-canonical)", str(sampled))
    table.add_row("Mismatches", str(mismatches))
    table.add_row("Confidence", f"{confidence * 100:.6f}%")
    table.add_row("Output", str(out_path))
    out.print(table)

    return result
