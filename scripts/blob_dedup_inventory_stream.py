#!/usr/bin/env python3
"""
Stream Azure Blob Inventory CSV and find exact duplicates.

Certainty PROVEN_EXACT when Content-MD5 present (md5 + length).
When MD5 absent: PROVEN_EXACT_ETAG if ETag non-empty and same (etag, length) with 2+ distinct paths.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

CERT_MD5 = "PROVEN_EXACT"
CERT_ETAG = "PROVEN_EXACT_ETAG"


def norm_etag(raw: str | None) -> str | None:
    if not raw or raw in ('""', '""'):
        return None
    s = str(raw).strip().strip('"')
    if not s or s == "*":
        return None
    return s


def norm_md5(raw: str | None) -> str | None:
    if not raw:
        return None
    s = str(raw).strip().strip('"')
    if not s:
        return None
    return s.lower()


def parse_row(row: dict) -> dict | None:
    name = (row.get("Name") or row.get("name") or "").strip()
    if not name or name == "Name":
        return None
    try:
        length = int(float(row.get("Content-Length") or row.get("ContentLength") or 0))
    except (TypeError, ValueError):
        return None
    if length <= 0:
        return None

    # Inventory CSV: Name may be full path container/blob or blob only
    if "/" in name:
        container, blob = name.split("/", 1)
    else:
        container = row.get("Container-Name") or row.get("container") or ""
        blob = name

    deleted = (row.get("Deleted") or "").strip().lower() in ("true", "1", "yes")
    if deleted:
        return None

    return {
        "container": container,
        "blob": blob,
        "name": name,
        "content_length": length,
        "content_md5": norm_md5(row.get("Content-MD5") or row.get("ContentMD5")),
        "etag": norm_etag(row.get("Etag") or row.get("ETag")),
    }


def pick_canonical(members: list[dict]) -> dict:
    return sorted(members, key=lambda m: (m["container"], m["blob"]))[0]


def process_csv(path: Path, shard_id: str, output_dir: Path) -> dict:
    by_md5: dict[tuple[str, int], list[dict]] = defaultdict(list)
    by_etag: dict[tuple[str, int], list[dict]] = defaultdict(list)
    rows_read = 0

    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            b = parse_row(row)
            if not b:
                continue
            rows_read += 1
            key_path = (b["container"], b["blob"])
            if b["content_md5"]:
                by_md5[(b["content_md5"], b["content_length"])].append(b)
            elif b["etag"]:
                by_etag[(b["etag"], b["content_length"])].append(b)

    delete_rows: list[dict] = []
    groups_md5 = groups_etag = 0

    for (md5, length), members in by_md5.items():
        uniq = {(m["container"], m["blob"]): m for m in members}
        members = list(uniq.values())
        if len(members) < 2:
            continue
        groups_md5 += 1
        canonical = pick_canonical(members)
        for m in members:
            if (m["container"], m["blob"]) == (canonical["container"], canonical["blob"]):
                continue
            delete_rows.append(
                {
                    "certainty": CERT_MD5,
                    "action": "DELETE_AFTER_APPROVAL",
                    "keep_container": canonical["container"],
                    "keep_blob": canonical["blob"],
                    "delete_container": m["container"],
                    "delete_blob": m["blob"],
                    "content_length": length,
                    "content_md5": md5,
                    "etag": m.get("etag") or "",
                    "source": f"inventory:{shard_id}",
                }
            )

    for (etag, length), members in by_etag.items():
        uniq = {(m["container"], m["blob"]): m for m in members}
        members = list(uniq.values())
        if len(members) < 2:
            continue
        groups_etag += 1
        canonical = pick_canonical(members)
        for m in members:
            if (m["container"], m["blob"]) == (canonical["container"], canonical["blob"]):
                continue
            delete_rows.append(
                {
                    "certainty": CERT_ETAG,
                    "action": "DELETE_AFTER_APPROVAL",
                    "keep_container": canonical["container"],
                    "keep_blob": canonical["blob"],
                    "delete_container": m["container"],
                    "delete_blob": m["blob"],
                    "content_length": length,
                    "content_md5": "",
                    "etag": etag,
                    "source": f"inventory:{shard_id}",
                }
            )

    out = output_dir / f"shard_{shard_id}"
    out.mkdir(parents=True, exist_ok=True)
    if delete_rows:
        fields = list(delete_rows[0].keys())
        with (out / "delete_candidates.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(delete_rows)

    stats = {
        "shard": shard_id,
        "rows_read": rows_read,
        "groups_md5": groups_md5,
        "groups_etag": groups_etag,
        "delete_candidates": len(delete_rows),
        "bytes_reclaimable": sum(r["content_length"] for r in delete_rows),
    }
    (out / "stats.json").write_text(json.dumps(stats, indent=2))
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, required=True)
    ap.add_argument("--shard-id", required=True)
    ap.add_argument("--output-dir", type=Path, default=Path("artifacts/dedup/ag2-live"))
    args = ap.parse_args()
    if not args.csv.exists():
        print(f"ERROR missing {args.csv}", file=sys.stderr)
        return 1
    stats = process_csv(args.csv, args.shard_id, args.output_dir)
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
