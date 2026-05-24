#!/usr/bin/env python3
"""Execute Kanban DELETE QUEUE (approved) items against Azure Blob Storage.

Reads artifacts/catalog/DELETE_QUEUE_MANIFEST.json produced by process_homes_export.py.
Expands container/folder cards to blob paths via inventory CSV (fast at scale).

Default is dry-run. Pass --execute to delete (requires AZURE_STORAGE_ACCOUNT + creds).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.storage.blob import BlobServiceClient

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blob_inventory_hierarchy_report import folder_levels, parse_blob_row  # noqa: E402


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


def load_done(log_path: Path) -> set[tuple[str, str]]:
    done: set[tuple[str, str]] = set()
    if not log_path.exists():
        return done
    with log_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("container") and rec.get("blob"):
                done.add((rec["container"], rec["blob"]))
    return done


def expand_targets(items: list[dict], csv_paths: list[Path]) -> list[tuple[str, str, str]]:
    """Return (container, blob, card_id) tuples to delete."""
    rules: list[tuple[str, str | None, str]] = []
    for it in items:
        container = it.get("container")
        if not container:
            continue
        folder = it.get("folder")
        rules.append((container, folder, it.get("id", container)))

    out: list[tuple[str, str, str]] = []
    for path in csv_paths:
        if not path.exists():
            raise FileNotFoundError(path)
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                parsed = parse_blob_row(row)
                if not parsed:
                    continue
                container, blob_path, _size = parsed
                for rule_container, rule_folder, card_id in rules:
                    if container != rule_container:
                        continue
                    if rule_folder is None:
                        out.append((container, blob_path, card_id))
                    else:
                        l1, _ = folder_levels(blob_path)
                        if l1 == rule_folder:
                            out.append((container, blob_path, card_id))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--manifest",
        default="artifacts/catalog/DELETE_QUEUE_MANIFEST.json",
    )
    ap.add_argument(
        "--inventory-csv",
        action="append",
        default=[
            "artifacts/dedup/ag1/Alansinv_1000000_0.csv",
            "artifacts/dedup/ag1/Alansinv_1000000_1.csv",
        ],
    )
    ap.add_argument("--log", default="artifacts/dedup/DELETE_QUEUE_EXECUTION.jsonl")
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--limit", type=int, default=0, help="Max blob deletes this run (0=all)")
    ap.add_argument("--execute", action="store_true", help="Actually delete (default: dry-run)")
    args = ap.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"Missing {manifest_path} — run process_homes_export.py after Kanban export", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    items = [
        it
        for it in manifest.get("items") or []
        if (it.get("path") or [])[:2] == ["delete-queue", "approved"]
    ]
    if not items:
        print("DELETE QUEUE is empty (no approved items).")
        return 0

    print(f"Approved queue cards: {len(items)}")
    for it in items:
        label = it.get("label") or it.get("id")
        scope = it.get("folder") or "(entire container)"
        print(f"  - {label} [{scope}] blobs≈{it.get('blobs')} {it.get('bytes_human', '')}")

    csv_paths = [Path(p) for p in args.inventory_csv]
    print("Expanding blobs from inventory CSV…")
    t0 = time.time()
    targets = expand_targets(items, csv_paths)
    print(f"  {len(targets):,} blobs in {time.time() - t0:.1f}s")

    log_path = Path(args.log)
    done = load_done(log_path)
    pending = [(c, b, card) for c, b, card in targets if (c, b) not in done]
    if args.limit:
        pending = pending[: args.limit]

    print(f"Pending after resume log: {len(pending):,} (skipped {len(targets) - len(pending):,} already logged)")

    if not args.execute:
        for c, b, card in pending[:8]:
            print(f"  [dry-run] {c}/{b[:70]}…  (card {card})")
        if len(pending) > 8:
            print(f"  … and {len(pending) - 8:,} more")
        print("\nRe-run with --execute to delete (and optional --limit N for a test batch).")
        return 0

    account = os.environ.get("AZURE_STORAGE_ACCOUNT")
    if not account:
        print("AZURE_STORAGE_ACCOUNT required", file=sys.stderr)
        return 1

    if not pending:
        print("Nothing to delete.")
        return 0

    client = get_client(account)
    lock = threading.Lock()
    stats: dict[str, int] = {"deleted": 0, "not_found": 0, "error": 0}
    started = time.time()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def delete_one(container: str, blob: str, card_id: str) -> dict:
        cc = client.get_container_client(container)
        err: str | None = None
        try:
            cc.delete_blob(blob)
            status = "deleted"
        except ResourceNotFoundError:
            status = "not_found"
        except HttpResponseError as e:
            if e.error_code == "SnapshotsPresent":
                try:
                    cc.delete_blob(blob, delete_snapshots="include")
                    status = "deleted"
                except ResourceNotFoundError:
                    status = "not_found"
                except Exception as e2:
                    status = "error"
                    err = str(e2)[:500]
            else:
                status = "error"
                err = str(e)[:500]
        except Exception as e:
            status = "error"
            err = str(e)[:500]

        rec = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "container": container,
            "blob": blob,
            "status": status,
            "card_id": card_id,
            "source": "delete_queue",
        }
        if err:
            rec["error"] = err
        return rec

    total = len(pending)
    with log_path.open("a", encoding="utf-8") as log_f:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = {
                ex.submit(delete_one, c, b, card): (c, b, card) for c, b, card in pending
            }
            n = 0
            for fut in as_completed(futures):
                rec = fut.result()
                with lock:
                    log_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    log_f.flush()
                    sk = rec["status"] if rec["status"] in stats else "error"
                    stats[sk] = stats.get(sk, 0) + 1
                    n += 1
                    if n % 500 == 0:
                        elapsed = time.time() - started
                        rate = n / elapsed if elapsed else 0
                        print(
                            f"  {n}/{total} deleted={stats['deleted']} "
                            f"nf={stats['not_found']} err={stats['error']} ({rate:.1f}/s)",
                            flush=True,
                        )

    summary = {
        "queue_cards": len(items),
        "blobs_targeted": len(targets),
        "pending_at_start": total,
        **stats,
        "elapsed_s": round(time.time() - started, 1),
        "log": str(log_path),
    }
    print(json.dumps(summary, indent=2))
    return 0 if stats.get("error", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
