#!/usr/bin/env python3
"""Move non-canonical partial-hash (90%%) duplicate blobs into archive-gone-girl container."""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from datetime import timedelta

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.storage.blob import BlobSasPermissions, BlobServiceClient, generate_blob_sas

from azdedup.models.blob_ref import InventoryBlob
from azdedup.pipeline.canonical import pick_canonical

ARCHIVE_CONTAINER = "archive-gone-girl"
DEFAULT_JSONL = Path("artifacts/dedup/azdedup/dedup/partial_dry_run.jsonl")
DEFAULT_LOG = Path("artifacts/dedup/archive_gone_girl_moves.jsonl")


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
    raise RuntimeError("Set AZURE_STORAGE_KEY or AZURE_STORAGE_CONNECTION_STRING")


def archive_blob_path(source_container: str, blob_path: str) -> str:
    """Destination path preserves source container + blob path."""
    return f"{source_container}/{blob_path}"


def load_groups(jsonl_path: Path) -> list[tuple[list[InventoryBlob], dict[str, str]]]:
    """Group dry-run rows by (size, hash_fast)."""
    groups: dict[tuple[int, str], list[tuple[InventoryBlob, dict[str, str]]]] = defaultdict(list)
    with jsonl_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            size = int(row["size"])
            hash_fast = row.get("hash_fast") or (row.get("tags") or {}).get("hash_fast")
            if not hash_fast:
                continue
            blob = InventoryBlob(
                container=row["container"],
                blob_path=row["blob_path"],
                size=size,
                etag=row.get("etag", ""),
                ext=row.get("ext", InventoryBlob.ext_from_path(row["blob_path"])),
            )
            groups[(size, hash_fast)].append((blob, row.get("tags") or {}))

    out: list[tuple[list[InventoryBlob], dict[str, str]]] = []
    for members_with_tags in groups.values():
        if len(members_with_tags) < 2:
            continue
        members = [m[0] for m in members_with_tags]
        out.append((members, members_with_tags[0][1]))
    return out


def build_move_list(groups: list[tuple[list[InventoryBlob], dict[str, str]]]) -> list[InventoryBlob]:
    to_move: list[InventoryBlob] = []
    for members, _tags in groups:
        winner = pick_canonical(members, "container_priority")
        for member in members:
            if member is not winner:
                to_move.append(member)
    return to_move


def ensure_archive_container(client: BlobServiceClient) -> None:
    try:
        client.create_container(ARCHIVE_CONTAINER)
    except ResourceExistsError:
        pass


def _copy_source_url(client: BlobServiceClient, container: str, blob_path: str) -> str:
    key = os.environ.get("AZURE_STORAGE_KEY")
    if not key:
        raise RuntimeError("AZURE_STORAGE_KEY required for server-side copy")
    account = client.account_name
    sas = generate_blob_sas(
        account_name=account,
        container_name=container,
        blob_name=blob_path,
        account_key=key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    base = f"https://{account}.blob.core.windows.net/{container}/{blob_path}"
    return f"{base}?{sas}"


def move_one(
    client: BlobServiceClient,
    blob: InventoryBlob,
    *,
    dry_run: bool,
) -> dict:
    dest_path = archive_blob_path(blob.container, blob.blob_path)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": "move",
        "source_container": blob.container,
        "source_blob": blob.blob_path,
        "dest_container": ARCHIVE_CONTAINER,
        "dest_blob": dest_path,
        "size": blob.size,
        "dry_run": dry_run,
    }
    if dry_run:
        record["status"] = "dry_run"
        return record

    src = client.get_blob_client(blob.container, blob.blob_path)
    dst = client.get_blob_client(ARCHIVE_CONTAINER, dest_path)
    try:
        copy_url = _copy_source_url(client, blob.container, blob.blob_path)
        dst.start_copy_from_url(copy_url, requires_sync=True)
        src.delete_blob()
        record["status"] = "moved"
    except ResourceNotFoundError:
        record["status"] = "not_found"
    except Exception as exc:  # noqa: BLE001
        record["status"] = "error"
        record["error"] = str(exc)[:500]
    return record


def main() -> int:
    ap = argparse.ArgumentParser(description="Move 90%% partial-hash dupes to archive-gone-girl")
    ap.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    ap.add_argument("--log", type=Path, default=DEFAULT_LOG)
    ap.add_argument("--account", default=os.environ.get("AZURE_STORAGE_ACCOUNT"))
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--limit", type=int, default=0, help="Max moves (0=all)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.account:
        print("Set AZURE_STORAGE_ACCOUNT or --account", file=sys.stderr)
        return 1
    if not args.jsonl.is_file():
        print(f"Missing jsonl: {args.jsonl}", file=sys.stderr)
        return 1

    groups = load_groups(args.jsonl)
    to_move = build_move_list(groups)
    if args.limit > 0:
        to_move = to_move[: args.limit]

    print(f"Groups: {len(groups)} | To move (non-canonical): {len(to_move)}")
    if not to_move:
        return 0

    client = get_client(args.account)
    if not args.dry_run:
        ensure_archive_container(client)

    args.log.parent.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()
    stats = defaultdict(int)

    def worker(blob: InventoryBlob) -> dict:
        rec = move_one(client, blob, dry_run=args.dry_run)
        with lock:
            stats[rec["status"]] += 1
            with args.log.open("a", encoding="utf-8") as logf:
                logf.write(json.dumps(rec) + "\n")
        return rec

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(worker, b) for b in to_move]
        for i, fut in enumerate(as_completed(futures), 1):
            fut.result()
            if i % 500 == 0:
                print(f"  progress {i}/{len(to_move)} {dict(stats)}")

    print("Done:", dict(stats), "log:", args.log)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
