#!/usr/bin/env python3
"""Split Alansinv inventory CSVs into N shard files (line-preserving, fast)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from azdedup.inventory import resolve_inventory_paths


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--inventory-glob",
        default="artifacts/dedup/ag1/Alansinv_1000000_*.csv",
    )
    ap.add_argument("--shard-count", type=int, default=10)
    ap.add_argument("--output-dir", type=Path, default=Path("artifacts/dedup/shards"))
    args = ap.parse_args()

    paths = resolve_inventory_paths(args.inventory_glob)
    if not paths:
        print("No inventory files found", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    handles = []
    for i in range(args.shard_count):
        p = args.output_dir / f"shard_{i:02d}.csv"
        handles.append(p.open("w", encoding="utf-8", newline=""))

    header: str | None = None
    total = 0
    for path in paths:
        with path.open(encoding="utf-8-sig", errors="replace") as src:
            first = src.readline()
            if not first.strip():
                continue
            if header is None:
                header = first if first.endswith("\n") else first + "\n"
                for h in handles:
                    h.write(header)
            else:
                # skip duplicate header rows in subsequent parts
                if first.strip().lower().startswith("name,") and "content-length" in first.lower():
                    pass
                else:
                    handles[total % args.shard_count].write(first)
                    total += 1
            for line in src:
                if line.strip().lower().startswith("name,") and "content-length" in line.lower():
                    continue
                handles[total % args.shard_count].write(line)
                total += 1

    for h in handles:
        h.close()

    print(f"Wrote {args.shard_count} shards under {args.output_dir} ({total:,} data rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
