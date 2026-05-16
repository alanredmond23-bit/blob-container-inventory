#!/usr/bin/env python3
"""Merge AG-2 and AG-3 outputs into MASTER_DEDUP_MANIFEST.csv (PROVEN only)."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ALLOWED = frozenset({"PROVEN_EXACT", "PROVEN_EXACT_COMPUTED"})


def load_delete_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ag2", type=Path, default=Path("artifacts/dedup/ag2"))
    ap.add_argument("--ag3", type=Path, default=Path("artifacts/dedup/ag3"))
    ap.add_argument("--ag3b", type=Path, default=Path("artifacts/dedup/ag3b"))
    ap.add_argument("--output", type=Path, default=Path("artifacts/dedup/MASTER_DEDUP_MANIFEST.csv"))
    ap.add_argument("--exclude-test-ag2", action="store_true", help="Skip ag2 sample_inventory artifacts")
    args = ap.parse_args()

    sources = [args.ag3, args.ag3b]
    if not args.exclude_test_ag2:
        sources.insert(0, args.ag2)
    rows: list[dict] = []
    for base in sources:
        rows.extend(load_delete_csv(base / "delete_candidates.csv"))

    # Dedupe delete rows
    seen = set()
    master: list[dict] = []
    for r in rows:
        cert = r.get("certainty", "")
        if cert not in ALLOWED:
            continue
        key = (r["delete_container"], r["delete_blob"], r.get("content_md5", ""), r.get("sha256_computed", ""))
        if key in seen:
            continue
        seen.add(key)
        master.append(r)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "certainty",
        "action",
        "keep_container",
        "keep_blob",
        "delete_container",
        "delete_blob",
        "content_length",
        "content_md5",
        "sha256_computed",
    ]
    with args.output.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        if master:
            w.writerows(master)

    summary = {
        "delete_rows": len(master),
        "bytes_reclaimable": sum(int(r.get("content_length") or 0) for r in master),
        "certainty_breakdown": {},
    }
    for r in master:
        c = r.get("certainty", "")
        summary["certainty_breakdown"][c] = summary["certainty_breakdown"].get(c, 0) + 1

    (args.output.parent / "SUMMARY.json").write_text(json.dumps(summary, indent=2))
    (args.output.parent / "STATUS.json").write_text(
        json.dumps({"agent": "AG-4-MANIFEST", "status": "complete", "summary": summary}, indent=2)
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
