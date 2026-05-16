#!/usr/bin/env python3
"""
Analyze Azure Blob Inventory CSV/Parquet for exact duplicates (100% certainty).

Duplicate = same Content-MD5 (non-empty) AND same Content-Length.
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

CERTAINTY_PROVEN = "PROVEN_EXACT"
CERTAINTY_SUSPECT = "SUSPECT"
CERTAINTY_REJECTED = "REJECTED"

# Prefer keeping blobs in these containers (prefix match)
KEEP_CONTAINER_PRIORITY = (
    "discovery",
    "five9-calls",
    "evidence",
    "legal",
    "gmail-takeout",
)

DEPRIORITIZE_CONTAINERS = (
    "ice-cold-triage",
    "backups",
    "uploads",
    "123triageonedrive",
    "45gb-final-onedrive",
    "bin",
)


def normalize_md5(raw: str | None) -> str | None:
    if raw is None or raw == "" or str(raw).lower() in ("none", "null"):
        return None
    s = str(raw).strip()
    # Inventory may use base64 MD5
    if len(s) == 24 and s.endswith("=="):
        try:
            return base64.b64decode(s).hex()
        except Exception:
            pass
    # Already hex
    if len(s) == 32 and all(c in "0123456789abcdefABCDEF" for c in s):
        return s.lower()
    try:
        return base64.b64decode(s).hex()
    except Exception:
        return None


def parse_container_blob(name: str) -> tuple[str, str]:
    """Inventory Name is often container/path or path within container depending on export."""
    name = name.lstrip("/")
    if "/" not in name:
        return "", name
    parts = name.split("/", 1)
    return parts[0], parts[1]


def container_rank(container: str) -> tuple[int, int, str]:
    c = container.lower()
    for i, pref in enumerate(KEEP_CONTAINER_PRIORITY):
        if pref in c:
            return (0, i, c)
    for pref in DEPRIORITIZE_CONTAINERS:
        if pref in c:
            return (2, 0, c)
    return (1, 0, c)


def pick_canonical(members: list[dict]) -> dict:
    def sort_key(m: dict) -> tuple:
        container = m.get("container") or ""
        blob = m.get("blob") or m.get("name", "")
        depth = blob.count("/")
        return (container_rank(container), depth, -len(blob), m.get("last_modified", ""), container, blob)

    return sorted(members, key=sort_key)[0]


def load_inventory(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        import pandas as pd

        df = pd.read_parquet(path)
        return df.to_dict(orient="records")

    rows: list[dict] = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def row_to_blob(row: dict, container_col: str | None = None) -> dict | None:
    name = row.get("Name") or row.get("name") or ""
    length_raw = row.get("Content-Length") or row.get("ContentLength") or row.get("content_length")
    md5_raw = row.get("Content-MD5") or row.get("ContentMD5") or row.get("content_md5")

    try:
        length = int(length_raw)
    except (TypeError, ValueError):
        return None

    md5 = normalize_md5(md5_raw)
    if container_col and row.get(container_col):
        container = row[container_col]
        blob = name
    else:
        container, blob = parse_container_blob(name)

    return {
        "container": container,
        "blob": blob,
        "name": name,
        "content_length": length,
        "content_md5": md5,
        "last_modified": row.get("Last-Modified") or row.get("LastModified") or "",
        "blob_type": row.get("BlobType") or row.get("blob_type") or "BlockBlob",
    }


def analyze(rows: list[dict], container_col: str | None = None) -> dict:
    blobs: list[dict] = []
    for row in rows:
        b = row_to_blob(row, container_col)
        if b and b["content_length"] > 0 and b["blob_type"]:
            blobs.append(b)

    by_md5: dict[tuple[str, int], list[dict]] = defaultdict(list)
    by_size_only: dict[int, list[dict]] = defaultdict(list)

    for b in blobs:
        by_size_only[b["content_length"]].append(b)
        if b["content_md5"]:
            by_md5[(b["content_md5"], b["content_length"])].append(b)

    proven_groups: list[dict] = []
    delete_candidates: list[dict] = []
    suspects: list[dict] = []

    for (md5, length), members in by_md5.items():
        if len(members) < 2:
            continue
        # Dedupe same container+path
        seen = set()
        unique: list[dict] = []
        for m in members:
            key = (m["container"], m["blob"])
            if key in seen:
                continue
            seen.add(key)
            unique.append(m)

        if len(unique) < 2:
            continue

        canonical = pick_canonical(unique)
        group = {
            "certainty": CERTAINTY_PROVEN,
            "content_md5": md5,
            "content_length": length,
            "member_count": len(unique),
            "canonical": canonical,
            "members": unique,
        }
        proven_groups.append(group)

        for m in unique:
            if (m["container"], m["blob"]) == (canonical["container"], canonical["blob"]):
                continue
            delete_candidates.append(
                {
                    "certainty": CERTAINTY_PROVEN,
                    "action": "DELETE_AFTER_APPROVAL",
                    "keep_container": canonical["container"],
                    "keep_blob": canonical["blob"],
                    "delete_container": m["container"],
                    "delete_blob": m["blob"],
                    "content_length": length,
                    "content_md5": md5,
                }
            )

    # Size-only suspects (no MD5) — never delete
    for length, members in by_size_only.items():
        no_md5 = [m for m in members if not m["content_md5"]]
        if len(no_md5) >= 2:
            suspects.append(
                {
                    "certainty": CERTAINTY_SUSPECT,
                    "reason": "same_content_length_no_md5",
                    "content_length": length,
                    "member_count": len(no_md5),
                    "members": no_md5[:20],
                }
            )

    bytes_reclaimable = sum(d["content_length"] for d in delete_candidates)

    return {
        "proven_groups": proven_groups,
        "delete_candidates": delete_candidates,
        "suspects": suspects,
        "stats": {
            "rows_read": len(rows),
            "blobs_with_length": len(blobs),
            "proven_groups": len(proven_groups),
            "delete_candidates": len(delete_candidates),
            "suspects": len(suspects),
            "bytes_reclaimable": bytes_reclaimable,
        },
    }


def write_outputs(result: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    with (output_dir / "proven_exact_groups.jsonl").open("w") as f:
        for g in result["proven_groups"]:
            f.write(json.dumps(g, default=str) + "\n")

    dc_fields = (
        list(result["delete_candidates"][0].keys()) if result["delete_candidates"] else []
    )
    with (output_dir / "delete_candidates.csv").open("w", newline="") as f:
        if dc_fields:
            w = csv.DictWriter(f, fieldnames=dc_fields)
            w.writeheader()
            w.writerows(result["delete_candidates"])
        else:
            w = csv.DictWriter(
                f,
                fieldnames=[
                    "certainty",
                    "action",
                    "keep_container",
                    "keep_blob",
                    "delete_container",
                    "delete_blob",
                    "content_length",
                    "content_md5",
                ],
            )
            w.writeheader()

    with (output_dir / "suspects.jsonl").open("w") as f:
        for s in result["suspects"]:
            f.write(json.dumps(s, default=str) + "\n")

    stats = result["stats"]
    (output_dir / "stats.json").write_text(json.dumps(stats, indent=2))
    (output_dir / "STATUS.json").write_text(
        json.dumps(
            {
                "agent": "AG-2",
                "status": "complete",
                "outputs": [
                    str(output_dir / "proven_exact_groups.jsonl"),
                    str(output_dir / "delete_candidates.csv"),
                    str(output_dir / "suspects.jsonl"),
                    str(output_dir / "stats.json"),
                ],
                "proven_exact_groups": stats["proven_groups"],
                "delete_candidates": stats["delete_candidates"],
                "bytes_reclaimable": stats["bytes_reclaimable"],
                "errors": [],
            },
            indent=2,
        )
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Find exact blob duplicates from inventory export")
    ap.add_argument("--inventory-csv", type=Path, help="Inventory CSV path")
    ap.add_argument("--inventory-parquet", type=Path, help="Inventory Parquet path")
    ap.add_argument("--output-dir", type=Path, default=Path("artifacts/dedup/ag2"))
    ap.add_argument("--container-col", help="CSV column for container if Name is blob-only")
    ap.add_argument("--account", default="", help="Storage account label for logs")
    args = ap.parse_args()

    path = args.inventory_parquet or args.inventory_csv
    if not path or not path.exists():
        print("ERROR: provide --inventory-csv or --inventory-parquet", file=sys.stderr)
        return 1

    rows = load_inventory(path)
    result = analyze(rows, args.container_col)
    write_outputs(result, args.output_dir)

    print(json.dumps(result["stats"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
