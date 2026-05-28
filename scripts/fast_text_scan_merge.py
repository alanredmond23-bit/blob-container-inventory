#!/usr/bin/env python3
"""Merge 5-agent fast text scan outputs."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    import sys

    roots = [Path(p) for p in sys.argv[1:]] if len(sys.argv) > 1 else [Path("artifacts/catalog/fast_scan")]
    all_hits: list[dict] = []
    summaries = []
    distinct: dict[str, set[int]] = defaultdict(set)

    for base in roots:
        for shard_dir in sorted(base.glob("shard_*")):
            sp = shard_dir / "summary.json"
            if sp.is_file():
                summaries.append(json.loads(sp.read_text()))
            hp = shard_dir / "bates_hits.csv"
            if not hp.is_file():
                continue
            with hp.open(encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    all_hits.append(row)
                    distinct[row["production"]].add(int(row["bates_id"]))

    out_base = Path("artifacts/catalog/fast_scan")
    out_base.mkdir(parents=True, exist_ok=True)
    out_csv = out_base / "bates_hits_merged.csv"
    if all_hits:
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=all_hits[0].keys())
            w.writeheader()
            w.writerows(all_hits)

    matrix_summary = {}
    mp = out_base / "overt_act_matrix_summary.json"
    if mp.is_file():
        matrix_summary = json.loads(mp.read_text())

    merged = {
        "hits_total": len(all_hits),
        "distinct_bates": {k: len(v) for k, v in distinct.items()},
        "overt_act_matrix": matrix_summary,
        "shard_summaries": summaries,
        "phases_merged": [str(r) for r in roots],
    }
    (out_base / "fast_scan_merged.json").write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Fast text scan results (merged)\n",
        "| Production | Distinct Bates found |",
        "|------------|---------------------:|",
    ]
    for prod in ("PROD01", "PROD02", "PROD03", "PROD04", "PROD05"):
        lines.append(f"| {prod} | {merged['distinct_bates'].get(prod, 0):,} |")
    lines.append(f"\nTotal hit rows: **{len(all_hits):,}**\n")
    Path("docs/FAST_TEXT_SCAN_RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(merged, indent=2))


if __name__ == "__main__":
    main()
