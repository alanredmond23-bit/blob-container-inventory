#!/usr/bin/env python3
"""Build blob_catalog load files from inventory CSV + Kanban assignments.

Outputs:
  artifacts/catalog/blob_catalog_load.csv.gz  (bulk insert)
  artifacts/catalog/home_summary.json       (six-home rollup)
  artifacts/catalog/HOMES_V2_SHEET.html      (table view before SQL is wired)
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blob_inventory_hierarchy_report import folder_levels, fmt_bytes, parse_blob_row  # noqa: E402

HOME_IDS = ("devops", "finance", "legal", "dup-likely", "cold", "organization")


def parse_ts(raw: str) -> str:
    raw = (raw or "").strip()
    return raw if raw else ""


def zone_label(path: list[str]) -> str:
    return " → ".join(path) if path else ""


def load_zone_rules(homes_path: Path, kanban_path: Path) -> tuple[dict[str, list[str]], dict[tuple[str, str], list[str]], dict]:
    data = json.loads(homes_path.read_text(encoding="utf-8"))
    assignments = data.get("assignments") or {}
    cards = {}
    if kanban_path.exists():
        cards = {c["id"]: c for c in json.loads(kanban_path.read_text())["cards"]}

    container_zone: dict[str, list[str]] = {}
    folder_zone: dict[tuple[str, str], list[str]] = {}

    for cid, entry in assignments.items():
        path = entry.get("path") or []
        if not path or path[0] == "delete-queue":
            continue
        card = cards.get(cid, {})
        container = card.get("container") or cid.replace("container:", "").split("/")[0]
        folder = card.get("folder")
        if folder:
            folder_zone[(container, folder)] = path
        else:
            container_zone[container] = path

    return container_zone, folder_zone, cards


def resolve_home_path(path: list[str], container: str, blob_path: str) -> tuple[str, str]:
    """Return (home_id, home_path inside home-* container)."""
    home_id = path[0]
    if home_id not in HOME_IDS:
        home_id = "organization"
    l1, _ = folder_levels(blob_path)
    parts = path[1:] + [container, blob_path]
    home_path = "/".join(p for p in parts if p)
    return home_id, home_path


def resolve_zone(
    container: str,
    l1: str,
    container_zone: dict[str, list[str]],
    folder_zone: dict[tuple[str, str], list[str]],
) -> tuple[list[str], str | None]:
    key = (container, l1)
    if key in folder_zone:
        p = folder_zone[key]
        return p, zone_label(p)
    if container in container_zone:
        p = container_zone[container]
        return p, zone_label(p)
    return ["organization", "unfiled"], "organization → unfiled"


def write_html_summary(home_stats: dict, out: Path, meta: dict) -> None:
    rows = []
    for hid in HOME_IDS:
        s = home_stats.get(hid, {})
        rows.append(
            f"<tr><td><strong>home-{hid}</strong></td>"
            f"<td>{s.get('blobs', 0):,}</td>"
            f"<td>{fmt_bytes(s.get('bytes', 0))}</td>"
            f"<td>{s.get('cards', 0)}</td>"
            f"<td>{s.get('earliest_created') or '—'}</td>"
            f"<td>{s.get('latest_modified') or '—'}</td></tr>"
        )
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/><title>Homes v2 sheet</title>
<style>
body{{font-family:system-ui;background:#0b0f14;color:#e8eef5;padding:1rem}}
table{{border-collapse:collapse;width:100%;max-width:900px}}
th,td{{border:1px solid #2a3544;padding:0.4rem 0.6rem;text-align:left}}
th{{background:#141b24;color:#8b9cb3}}
</style></head><body>
<h1>Six homes — catalog summary</h1>
<p>{meta.get('rows', 0):,} blobs mapped · {meta.get('elapsed_s')}s · load file: blob_catalog_load.csv.gz</p>
<table>
<thead><tr><th>Home container</th><th>Blobs</th><th>Size</th><th>Kanban cards</th><th>Earliest created</th><th>Latest modified</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
<p>Deploy <code>schema/blob_catalog.sql</code> to Azure SQL, bulk load CSV, then use views <code>v_home_summary</code> and <code>v_zone_top10</code>.</p>
</body></html>"""
    out.write_text(html, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--homes", default="artifacts/catalog/blob_homes_assignments.json")
    ap.add_argument("--kanban", default="artifacts/catalog/kanban_data.json")
    ap.add_argument(
        "--csv",
        action="append",
        default=[
            "artifacts/dedup/ag1/Alansinv_1000000_0.csv",
            "artifacts/dedup/ag1/Alansinv_1000000_1.csv",
        ],
    )
    ap.add_argument("-o", "--output", default="artifacts/catalog/blob_catalog_load.csv.gz")
    ap.add_argument("--html", default="artifacts/catalog/HOMES_V2_SHEET.html")
    ap.add_argument("--summary-json", default="artifacts/catalog/home_summary.json")
    ap.add_argument("--limit", type=int, default=0, help="Max rows (0=all, for tests)")
    args = ap.parse_args()

    homes = Path(args.homes)
    if not homes.exists():
        print(f"Missing {homes}", file=sys.stderr)
        return 1

    container_zone, folder_zone, cards = load_zone_rules(homes, Path(args.kanban))
    card_homes = defaultdict(int)
    for cid, entry in (json.loads(homes.read_text())["assignments"] or {}).items():
        p = entry.get("path") or []
        if p and p[0] in HOME_IDS:
            card_homes[p[0]] += 1

    home_stats = {
        h: {"blobs": 0, "bytes": 0, "cards": card_homes.get(h, 0), "earliest_created": None, "latest_modified": None}
        for h in HOME_IDS
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rows = 0
    unmapped = 0

    fieldnames = [
        "source_container",
        "source_path",
        "content_length",
        "creation_time",
        "last_modified",
        "home_id",
        "home_path",
        "zone_path",
        "card_id",
        "migrate_status",
    ]

    with gzip.open(out_path, "wt", newline="", encoding="utf-8") as gz:
        w = csv.DictWriter(gz, fieldnames=fieldnames)
        w.writeheader()
        for csv_path in [Path(p) for p in args.csv]:
            if not csv_path.exists():
                print(f"Missing {csv_path}", file=sys.stderr)
                return 1
            with csv_path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
                for row in csv.DictReader(f):
                    parsed = parse_blob_row(row)
                    if not parsed:
                        continue
                    container, blob_path, size = parsed
                    l1, _ = folder_levels(blob_path)
                    path, zone = resolve_zone(container, l1, container_zone, folder_zone)
                    home_id, home_path = resolve_home_path(path, container, blob_path)
                    created = parse_ts(row.get("Creation-Time") or "")
                    modified = parse_ts(row.get("Last-Modified") or "")

                    w.writerow(
                        {
                            "source_container": container,
                            "source_path": blob_path,
                            "content_length": size,
                            "creation_time": created,
                            "last_modified": modified,
                            "home_id": home_id,
                            "home_path": home_path,
                            "zone_path": zone,
                            "card_id": "",
                            "migrate_status": "mapped",
                        }
                    )
                    st = home_stats[home_id]
                    st["blobs"] += 1
                    st["bytes"] += size
                    if created and (not st["earliest_created"] or created < st["earliest_created"]):
                        st["earliest_created"] = created
                    if modified and (not st["latest_modified"] or modified > st["latest_modified"]):
                        st["latest_modified"] = modified
                    rows += 1
                    if args.limit and rows >= args.limit:
                        break
                    if rows % 1_000_000 == 0:
                        print(f"  … {rows:,} rows ({time.time() - t0:.0f}s)", flush=True)
            if args.limit and rows >= args.limit:
                break

    elapsed = round(time.time() - t0, 1)
    from datetime import timezone

    meta = {
        "rows": rows,
        "unmapped": unmapped,
        "elapsed_s": elapsed,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    Path(args.summary_json).write_text(
        json.dumps({"homes": home_stats, "meta": meta}, indent=2) + "\n",
        encoding="utf-8",
    )
    write_html_summary(home_stats, Path(args.html), meta)
    print(f"Wrote {out_path} ({rows:,} rows, {elapsed}s)")
    print(f"Wrote {args.html}")
    print(f"Wrote {args.summary_json}")
    for h in HOME_IDS:
        s = home_stats[h]
        print(f"  home-{h}: {s['blobs']:,} blobs · {fmt_bytes(s['bytes'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
