#!/usr/bin/env python3
"""Second pass: same Content-Length groups without proven MD5 match → SHA-256 → PROVEN_EXACT_COMPUTED."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

from azure.storage.blob import BlobServiceClient

CERTAINTY = "PROVEN_EXACT_COMPUTED"
MAX_HASH_BYTES = 50 * 1024 * 1024


def get_client(account: str) -> BlobServiceClient:
    key = os.environ.get("AZURE_STORAGE_KEY")
    return BlobServiceClient(f"https://{account}.blob.core.windows.net", credential=key)


def sha256_blob(client: BlobServiceClient, container: str, name: str) -> str:
    h = hashlib.sha256()
    for chunk in client.get_blob_client(container, name).download_blob().chunks():
        h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--containers", required=True)
    ap.add_argument("--output-dir", type=Path, default=Path("artifacts/dedup/ag3b"))
    ap.add_argument("--max-hash-bytes", type=int, default=MAX_HASH_BYTES)
    args = ap.parse_args()

    account = os.environ.get("AZURE_STORAGE_ACCOUNT", "")
    client = get_client(account)
    containers = [c.strip() for c in args.containers.split(",") if c.strip()]

    blobs: list[dict] = []
    for c in containers:
        for b in client.get_container_client(c).list_blobs():
            md5 = None
            if b.content_settings and b.content_settings.content_md5:
                md5 = b.content_settings.content_md5.hex()
            blobs.append(
                {
                    "container": c,
                    "blob": b.name,
                    "content_length": b.size or 0,
                    "content_md5": md5,
                }
            )

    by_size: dict[int, list[dict]] = defaultdict(list)
    for b in blobs:
        if b["content_length"] > 0:
            by_size[b["content_length"]].append(b)

    delete_rows: list[dict] = []
    groups: list[dict] = []

    candidates_sizes = [
        (length, members)
        for length, members in by_size.items()
        if 2 <= len(members) <= 100 and 0 < length <= args.max_hash_bytes
    ]
    print(f"Size-collision groups to hash: {len(candidates_sizes)}", flush=True)

    for gi, (length, members) in enumerate(candidates_sizes):
        if gi % 50 == 0:
            print(f"  group {gi}/{len(candidates_sizes)} len={length} n={len(members)}", flush=True)
        md5s = {m["content_md5"] for m in members if m["content_md5"]}
        if len(md5s) == 1 and md5s:
            continue

        for m in members:
            m["sha256"] = sha256_blob(client, m["container"], m["blob"])

        by_sha: dict[str, list[dict]] = defaultdict(list)
        for m in members:
            by_sha[m["sha256"]].append(m)

        for sha, grp in by_sha.items():
            if len(grp) < 2:
                continue
            canonical = sorted(grp, key=lambda x: (x["container"], x["blob"]))[0]
            groups.append(
                {
                    "certainty": CERTAINTY,
                    "sha256": sha,
                    "content_length": length,
                    "member_count": len(grp),
                    "canonical": canonical,
                }
            )
            for m in grp:
                if (m["container"], m["blob"]) == (canonical["container"], canonical["blob"]):
                    continue
                delete_rows.append(
                    {
                        "certainty": CERTAINTY,
                        "action": "DELETE_AFTER_APPROVAL",
                        "keep_container": canonical["container"],
                        "keep_blob": canonical["blob"],
                        "delete_container": m["container"],
                        "delete_blob": m["blob"],
                        "content_length": length,
                        "content_md5": m.get("content_md5") or "",
                        "sha256_computed": sha,
                    }
                )

    args.output_dir.mkdir(parents=True, exist_ok=True)
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
    with (args.output_dir / "delete_candidates.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(delete_rows)

    stats = {
        "blobs_scanned": len(blobs),
        "computed_groups": len(groups),
        "delete_candidates": len(delete_rows),
        "bytes_reclaimable": sum(r["content_length"] for r in delete_rows),
    }
    (args.output_dir / "stats.json").write_text(json.dumps(stats, indent=2))
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
