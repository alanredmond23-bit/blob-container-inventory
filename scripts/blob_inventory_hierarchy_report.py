#!/usr/bin/env python3
"""
Build container → folder → file counts from Azure Blob Inventory CSV(s).

Outputs Markdown + HTML for visual review.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path


def parse_blob_row(row: dict) -> tuple[str, str, int] | None:
    name = (row.get("Name") or "").strip()
    if not name or name == "Name":
        return None
    deleted = (row.get("Deleted") or "").strip().lower() in ("true", "1", "yes")
    if deleted:
        return None
    if "/" not in name:
        return None
    container, blob_path = name.split("/", 1)
    if not container or not blob_path:
        return None
    try:
        size = int(float(row.get("Content-Length") or 0))
    except (TypeError, ValueError):
        size = 0
    return container, blob_path.replace("\\", "/"), size


def folder_levels(blob_path: str) -> tuple[str, str]:
    """First two virtual directory levels (matches existing AZURE_BLOB_INVENTORY.md)."""
    parts = [p for p in blob_path.split("/") if p]
    if len(parts) <= 1:
        return "(root)", "(root)"
    if len(parts) == 2:
        return parts[0], "(root)"
    return parts[0], parts[1]


def l2_folder_count(c: dict) -> int:
    return sum(len(l1d["l2"]) for l1d in c["l1"].values())


def fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    for u in ("KiB", "MiB", "GiB", "TiB"):
        n /= 1024
        if n < 1024:
            return f"{n:.2f} {u}"
    return f"{n:.2f} PiB"


def stream_inventory(paths: list[Path], max_l2_per_l1: int) -> dict:
    containers: dict[str, dict] = defaultdict(
        lambda: {
            "blobs": 0,
            "bytes": 0,
            "l1": defaultdict(lambda: {"blobs": 0, "bytes": 0, "l2": defaultdict(lambda: {"blobs": 0, "bytes": 0})}),
        }
    )
    rows = 0
    t0 = time.time()

    for path in paths:
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                parsed = parse_blob_row(row)
                if not parsed:
                    continue
                container, blob_path, size = parsed
                c = containers[container]
                c["blobs"] += 1
                c["bytes"] += size
                l1, l2 = folder_levels(blob_path)
                c["l1"][l1]["blobs"] += 1
                c["l1"][l1]["bytes"] += size
                c["l1"][l1]["l2"][l2]["blobs"] += 1
                c["l1"][l1]["l2"][l2]["bytes"] += size
                rows += 1
                if rows % 1_000_000 == 0:
                    print(f"  … {rows:,} rows ({time.time() - t0:.0f}s)", flush=True)

    # trim l2 maps for huge l1 folders (keep top N by count)
    for c in containers.values():
        for l1_name, l1_data in c["l1"].items():
            l2 = l1_data["l2"]
            if len(l2) > max_l2_per_l1:
                top = sorted(l2.items(), key=lambda x: -x[1]["blobs"])[:max_l2_per_l1]
                l1_data["l2"] = dict(top)
                l1_data["l2_truncated"] = True
            else:
                l1_data["l2_truncated"] = False

    return {"rows": rows, "containers": dict(containers), "elapsed_s": round(time.time() - t0, 1)}


def write_markdown(data: dict, out_md: Path, account: str) -> None:
    containers = data["containers"]
    total_blobs = sum(c["blobs"] for c in containers.values())
    total_bytes = sum(c["bytes"] for c in containers.values())
    lines = [
        "# Azure Blob Hierarchy Report",
        "",
        f"**Account:** `{account}`  ",
        f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}  ",
        f"**Source rows:** {data['rows']:,}  ",
        f"**Scan time:** {data['elapsed_s']}s  ",
        "",
        "---",
        "",
        "## At a glance",
        "",
        "| Metric | Value |",
        "|--------|------:|",
        f"| Containers | **{len(containers)}** |",
        f"| Total blobs (files) | **{total_blobs:,}** |",
        f"| Total size | **{fmt_bytes(total_bytes)}** |",
        "",
        "## All containers (sortable overview)",
        "",
        "| Container | Blobs (files) | Top-level folders | L2 subfolders | Size |",
        "|-----------|-------------:|------------------:|--------------:|-----:|",
    ]
    for name in sorted(containers, key=lambda n: -containers[n]["blobs"]):
        c = containers[name]
        l1_count = len(c["l1"])
        l2_count = l2_folder_count(c)
        lines.append(
            f"| `{name}` | {c['blobs']:,} | {l1_count:,} | {l2_count:,} | {fmt_bytes(c['bytes'])} |"
        )
    lines.extend(
        [
            "",
            "*L2 subfolders* = distinct second path segments under each top-level folder (see detail below).",
            "",
            "---",
            "",
            "## Per-container detail",
            "",
            "For each container: **top-level folder** → **second-level folder** → blob count.",
            "",
        ]
    )

    for name in sorted(containers, key=lambda n: -containers[n]["blobs"]):
        c = containers[name]
        lines.append(f"### `{name}` — **{c['blobs']:,}** blobs · {fmt_bytes(c['bytes'])}")
        lines.append("")
        lines.append(
            f"- Top-level folders: **{len(c['l1']):,}**  "
            f"- L2 subfolders: **{l2_folder_count(c):,}**"
        )
        lines.append("")
        for l1 in sorted(c["l1"], key=lambda k: -c["l1"][k]["blobs"]):
            l1d = c["l1"][l1]
            lines.append(f"- **{l1}**: {l1d['blobs']:,} blobs ({fmt_bytes(l1d['bytes'])})")
            l2_items = sorted(l1d["l2"].items(), key=lambda x: -x[1]["blobs"])
            for l2, l2d in l2_items[:40]:
                label = l2 if l2 != "(root)" else "(files directly under folder)"
                lines.append(f"  - {label}: {l2d['blobs']:,}")
            if len(l2_items) > 40:
                lines.append(f"  - … *{len(l2_items) - 40} more subfolders*")
            if l1d.get("l2_truncated"):
                lines.append("  - … *subfolder list truncated in data (top by count kept)*")
        lines.append("")

    out_md.write_text("\n".join(lines), encoding="utf-8")


def write_html(data: dict, out_html: Path, account: str) -> None:
    containers = data["containers"]
    total_blobs = sum(c["blobs"] for c in containers.values())
    total_bytes = sum(c["bytes"] for c in containers.values())

    parts = [
        "<!DOCTYPE html><html><head><meta charset=utf-8>",
        "<title>Blob hierarchy — ",
        html.escape(account),
        "</title>",
        "<style>",
        "body{font-family:system-ui,sans-serif;margin:1.5rem;background:#0f1419;color:#e7ecf3}",
        "h1,h2{color:#7dd3fc}",
        ".cards{display:flex;flex-wrap:wrap;gap:1rem;margin:1rem 0}",
        ".card{background:#1a2332;border:1px solid #2d3a4f;border-radius:8px;padding:1rem 1.25rem;min-width:140px}",
        ".card b{font-size:1.5rem;display:block}",
        "table{border-collapse:collapse;width:100%;margin:1rem 0;font-size:0.9rem}",
        "th,td{border:1px solid #2d3a4f;padding:0.4rem 0.6rem;text-align:left}",
        "th{background:#1a2332;position:sticky;top:0}",
        "tr:nth-child(even){background:#151c26}",
        "tr:hover{background:#1f2a3d}",
        "details{margin:0.5rem 0;background:#151c26;border:1px solid #2d3a4f;border-radius:6px}",
        "summary{cursor:pointer;padding:0.6rem 0.8rem;font-weight:600}",
        "summary:hover{background:#1f2a3d}",
        ".l1{margin-left:0.5rem}",
        ".l2{margin-left:1.5rem;color:#94a3b8;font-size:0.85rem}",
        ".bar{height:6px;background:#2563eb;border-radius:3px;margin-top:4px}",
        "input#filter{width:100%;max-width:480px;padding:0.5rem;margin:0.5rem 0;background:#1a2332;border:1px solid #2d3a4f;color:#e7ecf3;border-radius:4px}",
        "</style></head><body>",
        f"<h1>Azure Blob Hierarchy</h1>",
        f"<p>Account <code>{html.escape(account)}</code> · "
        f"{time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} · "
        f"{data['rows']:,} inventory rows</p>",
        '<div class="cards">',
        f'<div class="card"><span>Containers</span><b>{len(containers)}</b></div>',
        f'<div class="card"><span>Total blobs</span><b>{total_blobs:,}</b></div>',
        f'<div class="card"><span>Total size</span><b>{fmt_bytes(total_bytes)}</b></div>',
        "</div>",
        "<h2>Container overview</h2>",
        '<input id="filter" type="search" placeholder="Filter containers…" />',
        "<table id='ctable'><thead><tr>",
        "<th>Container</th><th>Blobs</th><th>L1 folders</th><th>L2 subfolders</th><th>Size</th>",
        "</tr></thead><tbody>",
    ]

    max_blobs = max(c["blobs"] for c in containers.values()) or 1
    for name in sorted(containers, key=lambda n: -containers[n]["blobs"]):
        c = containers[name]
        pct = int(100 * c["blobs"] / max_blobs)
        parts.append(
            f"<tr data-name='{html.escape(name.lower())}'>"
            f"<td><code>{html.escape(name)}</code></td>"
            f"<td>{c['blobs']:,}<div class='bar' style='width:{pct}%'></div></td>"
            f"<td>{len(c['l1']):,}</td>"
            f"<td>{l2_folder_count(c):,}</td>"
            f"<td>{fmt_bytes(c['bytes'])}</td></tr>"
        )
    parts.append("</tbody></table>")

    parts.append("<h2>Folder tree by container</h2>")
    parts.append("<p>Click a container to expand. Each line is a virtual folder; numbers are <strong>blob (file) counts</strong>.</p>")

    for name in sorted(containers, key=lambda n: -containers[n]["blobs"]):
        c = containers[name]
        parts.append(
            f"<details><summary><code>{html.escape(name)}</code> — "
            f"{c['blobs']:,} blobs · {len(c['l1'])} top folders · {fmt_bytes(c['bytes'])}</summary>"
        )
        for l1 in sorted(c["l1"], key=lambda k: -c["l1"][k]["blobs"])[:80]:
            l1d = c["l1"][l1]
            parts.append(
                f"<div class='l1'><strong>{html.escape(l1)}</strong> — {l1d['blobs']:,} files "
                f"({fmt_bytes(l1d['bytes'])})</div>"
            )
            for l2, l2d in sorted(l1d["l2"].items(), key=lambda x: -x[1]["blobs"])[:25]:
                lab = l2 if l2 != "(root)" else "· (direct)"
                parts.append(f"<div class='l2'>{html.escape(lab)}: {l2d['blobs']:,}</div>")
        if len(c["l1"]) > 80:
            parts.append(f"<p class='l2'>… {len(c['l1']) - 80} more top-level folders</p>")
        parts.append("</details>")

    parts.append(
        "<script>document.getElementById('filter').oninput=function(){"
        "const q=this.value.toLowerCase();"
        "document.querySelectorAll('#ctable tbody tr').forEach(r=>{"
        "r.style.display=r.dataset.name.includes(q)?'':'none';});};</script>"
    )
    parts.append("</body></html>")
    out_html.write_text("".join(parts), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--csv",
        action="append",
        default=[
            "artifacts/dedup/ag1/Alansinv_1000000_0.csv",
            "artifacts/dedup/ag1/Alansinv_1000000_1.csv",
        ],
    )
    ap.add_argument("--out-dir", default="artifacts/catalog")
    ap.add_argument("--account", default=os.environ.get("AZURE_STORAGE_ACCOUNT", ""))
    ap.add_argument("--max-l2-per-l1", type=int, default=200)
    args = ap.parse_args()

    paths = [Path(p) for p in args.csv]
    for p in paths:
        if not p.exists():
            print(f"Missing: {p}", file=sys.stderr)
            return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Streaming inventory…", flush=True)
    data = stream_inventory(paths, args.max_l2_per_l1)

  # Convert sets for JSON
    summary = {
        "account": args.account,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rows": data["rows"],
        "elapsed_s": data["elapsed_s"],
        "container_count": len(data["containers"]),
        "total_blobs": sum(c["blobs"] for c in data["containers"].values()),
        "total_bytes": sum(c["bytes"] for c in data["containers"].values()),
        "containers": [
            {
                "name": n,
                "blobs": c["blobs"],
                "bytes": c["bytes"],
                "l1_folder_count": len(c["l1"]),
                "l2_subfolder_count": l2_folder_count(c),
            }
            for n, c in sorted(
                data["containers"].items(), key=lambda x: -x[1]["blobs"]
            )
        ],
    }
    (out_dir / "BLOB_HIERARCHY_SUMMARY.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    write_markdown(data, out_dir / "BLOB_HIERARCHY.md", args.account)
    write_html(data, out_dir / "BLOB_HIERARCHY.html", args.account)

    print(f"Wrote {out_dir}/BLOB_HIERARCHY.html")
    print(f"Wrote {out_dir}/BLOB_HIERARCHY.md")
    print(
        f"Containers: {summary['container_count']:,} | "
        f"Blobs: {summary['total_blobs']:,} | "
        f"Size: {fmt_bytes(summary['total_bytes'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
