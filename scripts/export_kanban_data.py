#!/usr/bin/env python3
"""Export compact container + L1 folder stats for the Kanban organizer UI."""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blob_inventory_hierarchy_report import folder_levels, fmt_bytes, parse_blob_row  # noqa: E402


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
    ap.add_argument("-o", "--output", default="artifacts/catalog/kanban_data.json")
    args = ap.parse_args()

    containers: dict[str, dict] = defaultdict(
        lambda: {"blobs": 0, "bytes": 0, "folders": defaultdict(lambda: {"blobs": 0, "bytes": 0})}
    )
    rows = 0
    t0 = time.time()

    for path in [Path(p) for p in args.csv]:
        if not path.exists():
            print(f"Missing {path}", file=sys.stderr)
            return 1
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                parsed = parse_blob_row(row)
                if not parsed:
                    continue
                container, blob_path, size = parsed
                c = containers[container]
                c["blobs"] += 1
                c["bytes"] += size
                l1, _ = folder_levels(blob_path)
                fd = c["folders"][l1]
                fd["blobs"] += 1
                fd["bytes"] += size
                rows += 1

    cards: list[dict] = []
    for cname in sorted(containers, key=lambda n: -containers[n]["blobs"]):
        c = containers[cname]
        cid = f"container:{cname}"
        cards.append(
            {
                "id": cid,
                "type": "container",
                "container": cname,
                "folder": None,
                "label": cname,
                "blobs": c["blobs"],
                "bytes": c["bytes"],
                "bytes_human": fmt_bytes(c["bytes"]),
            }
        )
        for l1 in sorted(c["folders"], key=lambda k: -c["folders"][k]["blobs"]):
            fd = c["folders"][l1]
            cards.append(
                {
                    "id": f"folder:{cname}/{l1}",
                    "type": "folder",
                    "container": cname,
                    "folder": l1,
                    "label": f"{cname} / {l1}",
                    "blobs": fd["blobs"],
                    "bytes": fd["bytes"],
                    "bytes_human": fmt_bytes(fd["bytes"]),
                }
            )

    out = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rows": rows,
        "elapsed_s": round(time.time() - t0, 1),
        "card_count": len(cards),
        "cards": cards,
    }
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {out_path} ({len(cards)} cards, {rows:,} rows, {out['elapsed_s']}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
