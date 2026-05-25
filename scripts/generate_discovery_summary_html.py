#!/usr/bin/env python3
"""HTML Discovery summary table from discovery_summary_data.json."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "artifacts/catalog/discovery_summary_data.json"
OUT = ROOT / "artifacts/catalog/DISCOVERY_SUMMARY_TABLE.html"


def main() -> int:
    p = json.loads(DATA.read_text(encoding="utf-8"))
    trs = []
    for r in p["rows"]:
        trs.append(
            f"<tr><td>{r['sort_order']}</td>"
            f"<td>{html.escape(r['category'])}</td>"
            f"<td>{html.escape(r['description'])}</td>"
            f"<td>{html.escape(r.get('bates_begin') or '')}</td>"
            f"<td>{html.escape(r.get('bates_end') or '')}</td>"
            f"<td>{html.escape(r.get('doc_date') or '')}</td>"
            f"<td class='muted'>{html.escape(r.get('notes') or '')}</td></tr>"
        )
    doc = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/><title>Discovery summary table</title>
<style>
body{{font-family:system-ui;margin:1rem;background:#0b0f14;color:#e8eef5}}
h1{{font-size:1.1rem}}
.meta{{color:#8b9cb3;font-size:0.85rem}}
table{{border-collapse:collapse;width:100%;font-size:0.78rem}}
th,td{{border:1px solid #2a3544;padding:0.35rem 0.5rem;text-align:left}}
th{{background:#141b24;position:sticky;top:0}}
.muted{{color:#8b9cb3;font-size:0.72rem}}
.photos img{{max-width:320px;margin:0.5rem;border:1px solid #2a3544}}
</style></head><body>
<h1>Discovery summary table</h1>
<p class="meta">{html.escape(p['title'])} · Case {html.escape(p['case_number'])} · Superseding {html.escape(p['superseding_indictment_date'])} · Due {html.escape(p['discovery_due_date'])}</p>
<table>
<thead><tr><th>#</th><th>Category</th><th>Description</th><th>Bates begin</th><th>Bates end</th><th>Date</th><th>Notes</th></tr></thead>
<tbody>{''.join(trs)}</tbody>
</table>
<div class="photos">
<h2>Source photos</h2>
<img src="photos/discovery-list-page-1-main.jpg" alt="Page 1 main"/>
<img src="photos/discovery-list-page-2-supplement.jpg" alt="Page 2 supplement"/>
</div>
</body></html>"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
