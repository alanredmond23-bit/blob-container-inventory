#!/usr/bin/env python3
"""Execute approved deletes from MASTER_DEDUP_MANIFEST.csv with resume support."""
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="artifacts/dedup/MASTER_DEDUP_MANIFEST.csv")
    ap.add_argument("--log", default="artifacts/dedup/DELETE_EXECUTION.jsonl")
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--limit", type=int, default=0, help="Max deletes this run (0=all pending)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--retry-errors",
        action="store_true",
        help="Re-attempt rows logged as error (e.g. SnapshotsPresent)",
    )
    args = ap.parse_args()

    account = os.environ.get("AZURE_STORAGE_ACCOUNT")
    if not account:
        print("AZURE_STORAGE_ACCOUNT required", file=sys.stderr)
        return 1

    manifest = Path(args.manifest)
    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    done = load_done(log_path)
    error_keys: set[tuple[str, str]] = set()
    if args.retry_errors and log_path.exists():
        with log_path.open() as f:
            for line in f:
                rec = json.loads(line)
                if rec.get("status") == "error":
                    error_keys.add((rec["container"], rec["blob"]))

    rows: list[dict[str, str]] = []
    with manifest.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["delete_container"], row["delete_blob"])
            if args.retry_errors:
                if key not in error_keys:
                    continue
            elif key in done:
                continue
            rows.append(row)

    if args.limit:
        rows = rows[: args.limit]

    total_pending = len(rows)
    print(f"Pending deletes: {total_pending} (already logged: {len(done)})")

    if args.dry_run:
        for r in rows[:5]:
            print(f"  would delete {r['delete_container']}/{r['delete_blob'][:60]}...")
        return 0

    if not rows:
        print("Nothing to delete.")
        return 0

    client = get_client(account)
    lock = threading.Lock()
    stats: dict[str, int] = {"deleted": 0, "not_found": 0, "error": 0}
    started = time.time()

    def delete_one(row: dict[str, str]) -> dict:
        container = row["delete_container"]
        blob = row["delete_blob"]
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
            "keep_container": row.get("keep_container"),
            "keep_blob": (row.get("keep_blob") or "")[:200],
            "certainty": row.get("certainty"),
            "content_length": row.get("content_length"),
        }
        if err:
            rec["error"] = err
        return rec

    with log_path.open("a", encoding="utf-8") as log_f:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = {ex.submit(delete_one, r): r for r in rows}
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
                            f"  {n}/{total_pending} "
                            f"deleted={stats['deleted']} "
                            f"nf={stats['not_found']} err={stats['error']} "
                            f"({rate:.1f}/s)",
                            flush=True,
                        )

    summary = {
        "deleted": stats["deleted"],
        "not_found": stats["not_found"],
        "error": stats["error"],
        "pending_at_start": total_pending,
        "elapsed_s": round(time.time() - started, 1),
    }
    print(json.dumps(summary, indent=2))

    status_path = Path("artifacts/dedup/STATUS.json")
    status = {}
    if status_path.exists():
        status = json.loads(status_path.read_text())
    status["delete_execution"] = {
        "approved_at": status.get("delete_execution", {}).get("approved_at")
        or datetime.now(timezone.utc).isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        **summary,
        "log": str(log_path),
    }
    status_path.write_text(json.dumps(status, indent=2) + "\n")
    return 0 if summary["error"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
