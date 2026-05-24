#!/usr/bin/env python3
"""Merge exported Kanban JSON into artifacts/catalog/registered_homes.json."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("export_file", help="blob_homes_assignments.json from Kanban export")
    ap.add_argument(
        "-o",
        "--output",
        default="artifacts/catalog/registered_homes.json",
    )
    ap.add_argument("--replace", action="store_true", help="Replace instead of merge assignments")
    args = ap.parse_args()

    src = Path(args.export_file)
    data = json.loads(src.read_text(encoding="utf-8"))
    incoming = data.get("assignments") or data
    board = data.get("board")

    out_path = Path(args.output)
    existing: dict = {}
    if out_path.exists() and not args.replace:
        existing = json.loads(out_path.read_text(encoding="utf-8"))

    merged = dict(existing.get("assignments") or {})
    merged.update(incoming)

    doc = {
        "version": 2,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(src),
        "assignments": merged,
        "board": board or existing.get("board"),
        "summary": data.get("summary"),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"Registered {len(merged)} assignments -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
