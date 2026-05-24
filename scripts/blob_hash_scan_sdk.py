#!/usr/bin/env python3
"""
List blobs via Azure SDK and find exact duplicates with computed SHA-256.

Certainty PROVEN_EXACT: Azure Content-MD5 matches + same length.
Certainty PROVEN_EXACT_COMPUTED: SHA-256 of full bytes matches (--verify-bytes).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

from azure.core.exceptions import AzureError
from azure.storage.blob import BlobServiceClient

CERTAINTY_PROVEN = "PROVEN_EXACT"
CERTAINTY_COMPUTED = "PROVEN_EXACT_COMPUTED"


def get_client(account: str) -> BlobServiceClient:
    conn = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if conn:
        return BlobServiceClient.from_connection_string(conn)
    key = os.environ.get("AZURE_STORAGE_KEY")
    if key:
        return BlobServiceClient(
            account_url=f"https://{account}.blob.core.windows.net",
            credential=key,
        )
    return BlobServiceClient(
        account_url=f"https://{account}.blob.core.windows.net",
        credential=__import__("azure.identity", fromlist=["DefaultAzureCredential"]).DefaultAzureCredential(),
    )


def list_container_blobs(client: BlobServiceClient, container: str) -> list[dict]:
    cc = client.get_container_client(container)
    out: list[dict] = []
    for blob in cc.list_blobs(include=["metadata"]):
        md5 = None
        if blob.content_settings and blob.content_settings.content_md5:
            raw = blob.content_settings.content_md5
            md5 = raw.hex() if isinstance(raw, bytes) else None
        out.append(
            {
                "container": container,
                "blob": blob.name,
                "content_length": blob.size or 0,
                "content_md5": md5,
                "last_modified": blob.last_modified.isoformat() if blob.last_modified else "",
                "etag": blob.etag,
            }
        )
    return out


def sha256_blob(client: BlobServiceClient, container: str, blob_name: str) -> str:
    bc = client.get_blob_client(container, blob_name)
    h = hashlib.sha256()
    stream = bc.download_blob()
    for chunk in stream.chunks():
        h.update(chunk)
    return h.hexdigest()


def verify_group_bytes(
    client: BlobServiceClient,
    members: list[dict],
    max_verify_bytes: int,
) -> bool:
    if len(members) < 2:
        return False
    if any(m["content_length"] > max_verify_bytes for m in members):
        return False
    digests = []
    for m in members:
        digests.append(sha256_blob(client, m["container"], m["blob"]))
    return len(set(digests)) == 1 and digests[0] is not None


def analyze_cross_container(
    all_blobs: list[dict],
    client: BlobServiceClient,
    verify_bytes: bool,
    max_verify_bytes: int = 50 * 1024 * 1024,
) -> dict:
    by_md5: dict[tuple[str, int], list[dict]] = defaultdict(list)
    by_sha: dict[tuple[str, int], list[dict]] = defaultdict(list)

    for b in all_blobs:
        if b["content_length"] <= 0:
            continue
        if b["content_md5"]:
            by_md5[(b["content_md5"], b["content_length"])].append(b)

    proven: list[dict] = []
    computed: list[dict] = []
    delete_rows: list[dict] = []

    for key, members in by_md5.items():
        if len(members) < 2:
            continue
        md5, length = key
        # unique paths
        uniq = {(m["container"], m["blob"]): m for m in members}
        members = list(uniq.values())
        if len(members) < 2:
            continue

        certainty = CERTAINTY_PROVEN
        if verify_bytes and not verify_group_bytes(client, members, max_verify_bytes):
            continue

        canonical = sorted(members, key=lambda m: (m["container"], m["blob"]))[0]
        group = {
            "certainty": certainty,
            "content_md5": md5,
            "content_length": length,
            "members": members,
            "canonical": canonical,
        }
        proven.append(group)

        for m in members:
            if (m["container"], m["blob"]) == (canonical["container"], canonical["blob"]):
                continue
            delete_rows.append(
                {
                    "certainty": certainty,
                    "action": "DELETE_AFTER_APPROVAL",
                    "keep_container": canonical["container"],
                    "keep_blob": canonical["blob"],
                    "delete_container": m["container"],
                    "delete_blob": m["blob"],
                    "content_length": length,
                    "content_md5": md5,
                }
            )

    # For blobs without MD5: group by size then hash (expensive)
    if verify_bytes:
        no_md5 = [b for b in all_blobs if not b["content_md5"] and b["content_length"] > 0]
        by_len: dict[int, list[dict]] = defaultdict(list)
        for b in no_md5:
            by_len[b["content_length"]].append(b)

        for length, candidates in by_len.items():
            if len(candidates) < 2:
                continue
            if length > max_verify_bytes:
                continue
            for b in candidates:
                b["sha256"] = sha256_blob(client, b["container"], b["blob"])
            sha_groups: dict[str, list[dict]] = defaultdict(list)
            for b in candidates:
                sha_groups[b["sha256"]].append(b)

            for sha, members in sha_groups.items():
                if len(members) < 2:
                    continue
                if not verify_group_bytes(client, members, max_verify_bytes):
                    continue
                canonical = sorted(members, key=lambda m: (m["container"], m["blob"]))[0]
                computed.append(
                    {
                        "certainty": CERTAINTY_COMPUTED,
                        "sha256": sha,
                        "content_length": length,
                        "members": members,
                        "canonical": canonical,
                    }
                )
                for m in members:
                    if (m["container"], m["blob"]) == (canonical["container"], canonical["blob"]):
                        continue
                    delete_rows.append(
                        {
                            "certainty": CERTAINTY_COMPUTED,
                            "action": "DELETE_AFTER_APPROVAL",
                            "keep_container": canonical["container"],
                            "keep_blob": canonical["blob"],
                            "delete_container": m["container"],
                            "delete_blob": m["blob"],
                            "content_length": length,
                            "content_md5": "",
                            "sha256_computed": sha,
                        }
                    )

    return {
        "proven_groups": proven,
        "computed_groups": computed,
        "delete_candidates": delete_rows,
        "stats": {
            "blobs_scanned": len(all_blobs),
            "proven_groups": len(proven),
            "computed_groups": len(computed),
            "delete_candidates": len(delete_rows),
            "bytes_reclaimable": sum(r["content_length"] for r in delete_rows),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", default=os.environ.get("AZURE_STORAGE_ACCOUNT", ""))
    ap.add_argument("--containers", default="", help="Comma-separated container names (optional with --all-containers)")
    ap.add_argument("--output-dir", type=Path, default=Path("artifacts/dedup/ag3"))
    ap.add_argument("--verify-bytes", action="store_true", help="SHA-256 verify all groups")
    ap.add_argument(
        "--max-verify-bytes",
        type=int,
        default=50 * 1024 * 1024,
        help="Only download bytes for verify when blob size <= this (default 50MB)",
    )
    ap.add_argument("--all-containers", action="store_true", help="Scan every container in account")
    ap.add_argument("--max-blobs-per-container", type=int, default=0, help="Cap list per container (0=all)")
    ap.add_argument("--skip-container-over", type=int, default=0, help="Skip containers with more than N blobs (0=none)")
    ap.add_argument("--max-blobs", type=int, default=0, help="Limit per container (0=all); alias for max-blobs-per-container")
    args = ap.parse_args()

    if not args.account:
        print("ERROR: set AZURE_STORAGE_ACCOUNT", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    per_cap = args.max_blobs_per_container or args.max_blobs

    try:
        client = get_client(args.account)
    except Exception as e:
        print(f"ERROR auth: {e}", file=sys.stderr)
        return 1

    if args.all_containers:
        containers = [c.name for c in client.list_containers()]
    else:
        containers = [c.strip() for c in args.containers.split(",") if c.strip()]

    if not containers:
        print("ERROR: specify --containers or --all-containers", file=sys.stderr)
        return 1

    all_blobs: list[dict] = []
    errors: list[str] = []
    skipped: list[str] = []

    for c in containers:
        try:
            cc = client.get_container_client(c)
            if args.skip_container_over:
                n = 0
                for _ in cc.list_blobs(results_per_page=500):
                    n += 1
                    if n > args.skip_container_over:
                        break
                if n > args.skip_container_over:
                    skipped.append(f"{c} (>{args.skip_container_over} blobs)")
                    print(f"Skip {c}: >{args.skip_container_over} blobs")
                    continue

            blobs = list_container_blobs(client, c)
            if per_cap:
                blobs = blobs[:per_cap]
            all_blobs.extend(blobs)
            print(f"Listed {len(blobs)} blobs in {c}")
        except AzureError as e:
            errors.append(f"{c}: {e}")
            print(f"WARN {c}: {e}", file=sys.stderr)

    result = analyze_cross_container(
        all_blobs, client, args.verify_bytes, args.max_verify_bytes
    )
    result["stats"]["containers_skipped"] = len(skipped)
    result["stats"]["skipped"] = skipped

    out = args.output_dir
    with (out / "proven_exact_groups.jsonl").open("w") as f:
        for g in result["proven_groups"]:
            f.write(json.dumps(g, default=str) + "\n")
    with (out / "proven_exact_computed.jsonl").open("w") as f:
        for g in result["computed_groups"]:
            f.write(json.dumps(g, default=str) + "\n")

    import csv

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
    with (out / "delete_candidates.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        if result["delete_candidates"]:
            w.writerows(result["delete_candidates"])

    (out / "stats.json").write_text(json.dumps(result["stats"], indent=2))
    (out / "STATUS.json").write_text(
        json.dumps(
            {
                "agent": "AG-3-SCANNER",
                "status": "complete" if not errors else "partial",
                "outputs": [str(out / "delete_candidates.csv"), str(out / "stats.json")],
                **result["stats"],
                "errors": errors,
            },
            indent=2,
        )
    )

    print(json.dumps(result["stats"], indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
