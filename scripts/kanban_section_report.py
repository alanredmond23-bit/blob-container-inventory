#!/usr/bin/env python3
"""Per Kanban zone: summary + table of top 10 largest files/folders (with dates)."""
from __future__ import annotations

import argparse
import csv
import heapq
import html
import json
import os
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blob_inventory_hierarchy_report import folder_levels, fmt_bytes, parse_blob_row  # noqa: E402


def parse_ts(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def fmt_ts(dt: datetime | None) -> str:
    if not dt:
        return "—"
    return dt.strftime("%Y-%m-%d %H:%M")


def zone_label(path: list[str]) -> str:
    return " → ".join(path) if path else "(unassigned)"


def slug_zone(path: list[str]) -> str:
    return re.sub(r"[^a-z0-9]+", "-", zone_label(path).lower()).strip("-")


@dataclass
class ZoneStats:
    path: list[str]
    cards: list[str] = field(default_factory=list)
    blobs: int = 0
    bytes: int = 0
    min_created: datetime | None = None
    max_created: datetime | None = None
    min_modified: datetime | None = None
    max_modified: datetime | None = None
    folders: dict[tuple[str, str], dict] = field(default_factory=dict)
    file_heap: list = field(default_factory=list)  # min-heap (size, seq, rec)
    _file_seq: int = 0

    def bump_dates(self, created: datetime | None, modified: datetime | None) -> None:
        if created:
            if self.min_created is None or created < self.min_created:
                self.min_created = created
            if self.max_created is None or created > self.max_created:
                self.max_created = created
        if modified:
            if self.min_modified is None or modified < self.min_modified:
                self.min_modified = modified
            if self.max_modified is None or modified > self.max_modified:
                self.max_modified = modified

    def add_file(self, size: int, rec: dict) -> None:
        self._file_seq += 1
        entry = (size, self._file_seq, rec)
        if len(self.file_heap) < 10:
            heapq.heappush(self.file_heap, entry)
        elif size > self.file_heap[0][0]:
            heapq.heapreplace(self.file_heap, entry)

    def folder_row(self, container: str, l1: str, agg: dict) -> dict:
        return {
            "kind": "folder",
            "name": f"{container}/{l1}/",
            "size": agg["bytes"],
            "blobs": agg["blobs"],
            "created_min": agg.get("min_created"),
            "created_max": agg.get("max_created"),
            "modified_min": agg.get("min_modified"),
            "modified_max": agg.get("max_modified"),
        }

    def top_ten(self) -> list[dict]:
        rows: list[dict] = []
        for (container, l1), agg in self.folders.items():
            if agg["bytes"] <= 0:
                continue
            rows.append(self.folder_row(container, l1, agg))
        for _size, _seq, rec in self.file_heap:
            rows.append(rec)
        rows.sort(key=lambda r: -r["size"])
        return rows[:10]


def load_zone_map(homes_path: Path, kanban_path: Path) -> tuple[dict, dict[str, list[str]]]:
    """container -> zone path; (container, l1) -> zone path (folder cards override)."""
    data = json.loads(homes_path.read_text(encoding="utf-8"))
    assignments = data.get("assignments") or {}

    cards: dict[str, dict] = {}
    if kanban_path.exists():
        cards = {c["id"]: c for c in json.loads(kanban_path.read_text())["cards"]}

    container_zone: dict[str, list[str]] = {}
    folder_zone: dict[tuple[str, str], list[str]] = {}
    zone_cards: dict[str, list[str]] = defaultdict(list)

    for cid, entry in assignments.items():
        path = entry.get("path") or []
        if not path:
            continue
        card = cards.get(cid, {})
        container = card.get("container") or cid.replace("container:", "").split("/")[0]
        folder = card.get("folder")
        label = card.get("label") or cid
        zk = zone_label(path)
        zone_cards[zk].append(label)
        if folder:
            folder_zone[(container, folder)] = path
        else:
            container_zone[container] = path

    zones: dict[str, ZoneStats] = {}
    for zk, labels in zone_cards.items():
        path = zk.split(" → ")
        zones[zk] = ZoneStats(path=path, cards=sorted(set(labels)))

    return zones, container_zone, folder_zone


def resolve_zone(
    container: str,
    l1: str,
    container_zone: dict[str, list[str]],
    folder_zone: dict[tuple[str, str], list[str]],
) -> str | None:
    key = (container, l1)
    if key in folder_zone:
        return zone_label(folder_zone[key])
    if container in container_zone:
        return zone_label(container_zone[container])
    return None


def write_html(zones: dict[str, ZoneStats], out: Path, account: str, meta: dict) -> None:
    ordered = sorted(zones.values(), key=lambda z: -z.bytes)
    nav = []
    sections = []
    for z in ordered:
        sid = slug_zone(z.path)
        zl = zone_label(z.path)
        top = z.top_ten()
        nav.append(f'<a href="#{sid}" data-bytes="{z.bytes}">{html.escape(zl)} <span class="meta">{fmt_bytes(z.bytes)}</span></a>')
        rows_html = []
        for i, row in enumerate(top, 1):
            if row["kind"] == "folder":
                created = f"{fmt_ts(row['created_min'])} … {fmt_ts(row['created_max'])}"
                modified = f"{fmt_ts(row['modified_min'])} … {fmt_ts(row['modified_max'])}"
                kind = "folder"
            else:
                created = fmt_ts(row.get("created"))
                modified = fmt_ts(row.get("modified"))
                kind = "file"
            rows_html.append(
                f"<tr><td>{i}</td><td class='kind'>{kind}</td>"
                f"<td class='name' title='{html.escape(row['name'])}'>{html.escape(row['name'][:120])}</td>"
                f"<td>{created}</td><td>{modified}</td>"
                f"<td class='num'>{fmt_bytes(row['size'])}</td>"
                f"<td class='num'>{row.get('blobs', 1):,}</td></tr>"
            )
        if not rows_html:
            rows_html.append("<tr><td colspan='7' class='muted'>No blobs matched this zone in inventory pass.</td></tr>")

        sections.append(
            f"""
<section id="{sid}" class="zone">
  <h2>{html.escape(zl)}</h2>
  <p class="cards">Cards: {html.escape(", ".join(z.cards[:12]))}{"…" if len(z.cards) > 12 else ""} ({len(z.cards)} total)</p>
  <table class="summary">
    <tr><th>Zone blobs</th><td>{z.blobs:,}</td><th>Zone size</th><td>{fmt_bytes(z.bytes)}</td></tr>
    <tr><th>Created (earliest)</th><td>{fmt_ts(z.min_created)}</td><th>Created (latest)</th><td>{fmt_ts(z.max_created)}</td></tr>
    <tr><th>Modified (earliest)</th><td>{fmt_ts(z.min_modified)}</td><th>Modified (latest)</th><td>{fmt_ts(z.max_modified)}</td></tr>
  </table>
  <h3>Top 10 largest files or folders</h3>
  <table class="top">
    <thead><tr><th>#</th><th>Type</th><th>Name</th><th>Created</th><th>Modified</th><th>Size</th><th>Blobs</th></tr></thead>
    <tbody>{"".join(rows_html)}</tbody>
  </table>
</section>"""
        )

    doc = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Kanban section review — {html.escape(account)}</title>
<style>
  :root {{ --bg:#0b0f14; --panel:#141b24; --border:#2a3544; --text:#e8eef5; --muted:#8b9cb3; --accent:#38bdf8; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font:13px/1.4 system-ui,sans-serif; background:var(--bg); color:var(--text); }}
  .wrap {{ display:grid; grid-template-columns:280px 1fr; min-height:100vh; }}
  nav {{ border-right:1px solid var(--border); background:#0f1419; padding:0.5rem; overflow-y:auto; position:sticky; top:0; height:100vh; }}
  nav h1 {{ font-size:0.85rem; margin:0 0 0.5rem; }}
  nav a {{ display:block; padding:0.25rem 0.35rem; color:var(--text); text-decoration:none; border-radius:4px; font-size:0.72rem; }}
  nav a:hover, nav a.active {{ background:var(--panel); color:var(--accent); }}
  nav .meta {{ color:var(--muted); float:right; }}
  main {{ padding:1rem 1.25rem; max-width:1100px; }}
  header.page {{ margin-bottom:1rem; }}
  header.page p {{ color:var(--muted); margin:0.25rem 0; }}
  section.zone {{ margin-bottom:2.5rem; padding-bottom:1.5rem; border-bottom:1px solid var(--border); scroll-margin-top:1rem; }}
  h2 {{ font-size:1.1rem; margin:0 0 0.35rem; }}
  h3 {{ font-size:0.85rem; color:var(--muted); margin:1rem 0 0.4rem; }}
  .cards {{ color:var(--muted); font-size:0.75rem; }}
  table {{ width:100%; border-collapse:collapse; font-size:0.78rem; margin:0.35rem 0; }}
  th, td {{ border:1px solid var(--border); padding:0.3rem 0.45rem; text-align:left; vertical-align:top; }}
  th {{ background:var(--panel); color:var(--muted); font-weight:600; }}
  td.name {{ max-width:420px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
  td.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
  td.kind {{ text-transform:capitalize; color:var(--accent); width:4rem; }}
  .muted {{ color:var(--muted); }}
  @media (max-width:900px) {{ .wrap {{ grid-template-columns:1fr; }} nav {{ position:relative; height:auto; max-height:40vh; }} }}
</style>
</head><body>
<div class="wrap">
<nav>
  <h1>Sections ({len(ordered)})</h1>
  {"".join(nav)}
</nav>
<main>
<header class="page">
  <h1>Kanban section review</h1>
  <p>Account <code>{html.escape(account)}</code> · {meta['rows']:,} inventory rows · {meta['elapsed_s']}s · export {html.escape(meta.get('exported_at') or '')}</p>
  <p>Each section: zone summary dates, then top 10 largest <strong>folders</strong> (L1 prefix) or <strong>files</strong>.</p>
</header>
{"".join(sections)}
</main>
</div>
<script>
const links = [...document.querySelectorAll('nav a')];
const obs = new IntersectionObserver((entries) => {{
  entries.forEach(e => {{
    if (e.isIntersecting) {{
      links.forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + e.target.id));
    }}
  }});
}}, {{ rootMargin: '-20% 0px -70% 0px' }});
document.querySelectorAll('section.zone').forEach(s => obs.observe(s));
</script>
</body></html>"""
    out.write_text(doc, encoding="utf-8")


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
    ap.add_argument("-o", "--output", default="artifacts/catalog/SECTION_VIEWS.html")
    ap.add_argument(
        "--account",
        default=os.environ.get("AZURE_STORAGE_ACCOUNT", ""),
        help="Label in report header (defaults to AZURE_STORAGE_ACCOUNT)",
    )
    args = ap.parse_args()

    homes = Path(args.homes)
    if not homes.exists():
        print(f"Missing {homes}", file=sys.stderr)
        return 1

    export = json.loads(homes.read_text(encoding="utf-8"))
    zones, container_zone, folder_zone = load_zone_map(homes, Path(args.kanban))
    zone_keys = set(zones.keys())

    t0 = time.time()
    rows = 0
    matched = 0

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
                zk = resolve_zone(container, folder_levels(blob_path)[0], container_zone, folder_zone)
                if not zk or zk not in zone_keys:
                    continue

                created = parse_ts(row.get("Creation-Time") or "")
                modified = parse_ts(row.get("Last-Modified") or "")
                z = zones[zk]
                z.blobs += 1
                z.bytes += size
                z.bump_dates(created, modified)
                matched += 1

                l1, _ = folder_levels(blob_path)
                fk = (container, l1)
                agg = z.folders.setdefault(
                    fk,
                    {"bytes": 0, "blobs": 0, "min_created": None, "max_created": None, "min_modified": None, "max_modified": None},
                )
                agg["bytes"] += size
                agg["blobs"] += 1
                if created:
                    if agg["min_created"] is None or created < agg["min_created"]:
                        agg["min_created"] = created
                    if agg["max_created"] is None or created > agg["max_created"]:
                        agg["max_created"] = created
                if modified:
                    if agg["min_modified"] is None or modified < agg["min_modified"]:
                        agg["min_modified"] = modified
                    if agg["max_modified"] is None or modified > agg["max_modified"]:
                        agg["max_modified"] = modified

                z.add_file(
                    size,
                    {
                        "kind": "file",
                        "name": f"{container}/{blob_path}",
                        "size": size,
                        "blobs": 1,
                        "created": created,
                        "modified": modified,
                    },
                )
                rows += 1
                if rows % 1_000_000 == 0:
                    print(f"  … {rows:,} rows ({time.time() - t0:.0f}s)", flush=True)

    elapsed = round(time.time() - t0, 1)
    meta = {"rows": rows, "matched": matched, "elapsed_s": elapsed, "exported_at": export.get("exported_at")}
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    account_label = args.account or "blob storage account"
    write_html(zones, out, account_label, meta)
    print(f"Wrote {out} ({len(zones)} sections, {matched:,} blobs matched, {elapsed}s)")

    # Markdown index for one-at-a-time review
    idx = Path(out.parent / "SECTION_INDEX.md")
    lines = ["# Kanban sections (review one at a time)", "", f"Open **SECTION_VIEWS.html** in a browser (serve `artifacts/catalog`).", ""]
    for z in sorted(zones.values(), key=lambda x: -x.bytes):
        sid = slug_zone(z.path)
        lines.append(f"- [{zone_label(z.path)}](SECTION_VIEWS.html#{sid}) — {z.blobs:,} blobs · {fmt_bytes(z.bytes)}")
    idx.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {idx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
