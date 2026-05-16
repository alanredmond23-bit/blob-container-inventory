#!/usr/bin/env python3
"""
AG-1: Ensure `inventory-reports` exists; locate newest blob inventory CSV and download.

Uses AZURE_STORAGE_ACCOUNT and AZURE_STORAGE_KEY (account key credential).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from azure.core.exceptions import HttpResponseError, ResourceExistsError, ResourceNotFoundError
from azure.storage.blob import BlobServiceClient

DEFAULT_ACCOUNT = os.environ.get("AZURE_STORAGE_ACCOUNT", "")
PRIMARY_CONTAINER = "inventory-reports"


def get_client(account: str) -> BlobServiceClient:
    key = os.environ.get("AZURE_STORAGE_KEY")
    if not key:
        raise SystemExit("AZURE_STORAGE_KEY is required")
    return BlobServiceClient(
        account_url=f"https://{account}.blob.core.windows.net",
        credential=key,
    )


def ensure_container(client: BlobServiceClient, name: str) -> bool:
    cc = client.get_container_client(name)
    if cc.exists():
        return False
    try:
        cc.create_container()
    except ResourceExistsError:
        return False
    return True


def inventory_related_containers(client: BlobServiceClient) -> list[str]:
    names = []
    for c in client.list_containers():
        n = c.name
        if n == PRIMARY_CONTAINER or "inventory" in n.lower():
            names.append(n)
    # Prefer primary first, then alphabetical
    return sorted(set(names), key=lambda x: (0 if x == PRIMARY_CONTAINER else 1, x))


def is_likely_inventory_csv(blob_name: str, container: str) -> bool:
    lower = blob_name.lower()
    if not lower.endswith(".csv"):
        return False
    if container == PRIMARY_CONTAINER:
        return True
    # Other *inventory* containers: path hints (rule folder names vary)
    markers = ("blob-inventory", "inventory", "blobinventory")
    return any(m in lower for m in markers)


def _consider_blob(
    best: tuple[str, str, object] | None,
    container: str,
    blob_name: str,
    last_modified: object | None,
) -> tuple[str, str, object] | None:
    if last_modified is None:
        return best
    if best is None or last_modified > best[2]:
        return (container, blob_name, last_modified)
    return best


def find_newest_inventory_csv(client: BlobServiceClient) -> tuple[str, str] | None:
    """Return (container, blob_name) for newest candidate, or None."""
    best: tuple[str, str, object] | None = None
    for container in inventory_related_containers(client):
        cc = client.get_container_client(container)
        try:
            for blob in cc.list_blobs():
                if not is_likely_inventory_csv(blob.name, container):
                    continue
                best = _consider_blob(best, container, blob.name, blob.last_modified)
        except HttpResponseError:
            continue

    # Shallow pass: inventory rule folders often start with blob-inventory (any container)
    if best is None:
        prefixes = ("blob-inventory", "BlobInventory")
        try:
            for c in client.list_containers():
                cc = client.get_container_client(c.name)
                for pref in prefixes:
                    try:
                        for blob in cc.list_blobs(name_starts_with=pref):
                            if not blob.name.lower().endswith(".csv"):
                                continue
                            best = _consider_blob(best, c.name, blob.name, blob.last_modified)
                    except HttpResponseError:
                        continue
        except HttpResponseError:
            pass

    if not best:
        return None
    return best[0], best[1]


def download_blob(client: BlobServiceClient, container: str, blob_name: str, dest: Path) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    bc = client.get_blob_client(container, blob_name)
    data = bc.download_blob().readall()
    dest.write_bytes(data)
    return len(data)


def main() -> int:
    ap = argparse.ArgumentParser(description="Ensure inventory container and fetch latest inventory CSV.")
    ap.add_argument(
        "--account",
        default=DEFAULT_ACCOUNT,
        help="Storage account name (set AZURE_STORAGE_ACCOUNT or pass this flag)",
    )
    ap.add_argument(
        "--out-csv",
        type=Path,
        default=Path("artifacts/dedup/ag1/inventory_latest.csv"),
        help="Destination for downloaded inventory CSV",
    )
    ap.add_argument("--json-summary", action="store_true", help="Print JSON summary line to stdout")
    args = ap.parse_args()
    if not (args.account or "").strip():
        raise SystemExit("Set AZURE_STORAGE_ACCOUNT or pass --account <name>")
    client = get_client(args.account)
    created = False
    container_error: str | None = None
    try:
        created = ensure_container(client, PRIMARY_CONTAINER)
    except ResourceNotFoundError as e:
        container_error = f"container_create_ResourceNotFound: {e.message}"
    except HttpResponseError as e:
        container_error = f"container_create_{e.status_code}: {e.message}"

    result = {
        "account": args.account,
        "container_ensured": PRIMARY_CONTAINER,
        "container_created": created,
        "container_create_error": container_error,
        "inventory_csv_found": False,
        "inventory_container": None,
        "inventory_blob": None,
        "download_path": None,
        "download_bytes": 0,
        "row_count": None,
        "error": None,
    }

    try:
        loc = find_newest_inventory_csv(client)
        if loc:
            ctn, blob = loc
            n = download_blob(client, ctn, blob, args.out_csv)
            result["inventory_csv_found"] = True
            result["inventory_container"] = ctn
            result["inventory_blob"] = blob
            result["download_path"] = str(args.out_csv.resolve())
            result["download_bytes"] = n
            # Rough row count: count newlines in file (inventory can be large; stream first 0 lines is wrong — read full for small/med)
            try:
                text = args.out_csv.read_text(encoding="utf-8", errors="replace")
                result["row_count"] = max(0, text.count("\n") - 1)  # exclude header
            except OSError:
                result["row_count"] = None
    except HttpResponseError as e:
        result["error"] = f"{e.status_code}: {e.message}"

    if args.json_summary:
        import json

        print(json.dumps(result))
    else:
        print(
            f"container_created={result['container_created']} "
            f"found={result['inventory_csv_found']} "
            f"path={result.get('download_path')}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
