#!/usr/bin/env python3
"""Move dupe-report candidates into dup-likely zones in homes JSON."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

DUP_STRUCTURAL = ["dup-likely", "structural-mirror"]
DUP_MD5 = ["dup-likely", "md5-pending"]
DUP_REVIEW = ["dup-likely", "review-before-delete"]

# Card ids from ZONE_INBOX_DUPE_REPORT — same-size / mirror candidates
MOVE_TO_DUP: dict[str, list[str]] = {
    "container:gmail-takeout": DUP_STRUCTURAL,
    "folder:gmail-takeout/(root)": DUP_STRUCTURAL,
    "folder:indexes/gmail-takeout": DUP_STRUCTURAL,
    "container:product-assets": DUP_STRUCTURAL,
    "folder:product-assets/(root)": DUP_STRUCTURAL,
    "folder:make-money/product-assets": DUP_STRUCTURAL,
    "container:bin": DUP_STRUCTURAL,
    "folder:bin/(root)": DUP_STRUCTURAL,
    "container:cursor-extractions": DUP_STRUCTURAL,
    "folder:cursor-extractions/(root)": DUP_STRUCTURAL,
    "container:insights-logs-auditevent": DUP_MD5,
    "folder:insights-logs-auditevent/resourceId=": DUP_MD5,
    "container:insights-metrics-pt1m": DUP_MD5,
    "folder:insights-metrics-pt1m/resourceId=": DUP_MD5,
    "container:onedrive-rescue-20260508": DUP_STRUCTURAL,
    "folder:onedrive-rescue-20260508/(root)": DUP_STRUCTURAL,
    "folder:onedrive-rescue-20260508/a": DUP_STRUCTURAL,
    "folder:onedrive-rescue-20260508/b": DUP_STRUCTURAL,
    "folder:onedrive-rescue-20260508/c": DUP_STRUCTURAL,
    "folder:onedrive-rescue-20260508/d": DUP_STRUCTURAL,
    "folder:onedrive-rescue-20260508/sp1": DUP_STRUCTURAL,
    "folder:onedrive-rescue-20260508/sp2": DUP_STRUCTURAL,
    "folder:onedrive-rescue-20260508/benchmark-d95da8f3-5dc7-7d42-579c-724fd16fd012": DUP_STRUCTURAL,
    "folder:onedrive-rescue-20260508/benchmark-6899c2dc-a07a-2a4f-7487-b17d3a7fbb1b": DUP_STRUCTURAL,
    "folder:make-money/src": DUP_STRUCTURAL,
    "folder:marketing-war-command-center/src": DUP_STRUCTURAL,
    "folder:make-money/benfranklin-dashboard": DUP_REVIEW,
    "folder:triage/imported": DUP_REVIEW,
}

ORG_BOTTOM = {
    "id": "organization",
    "title": "ORGANIZATION",
    "color": "org",
    "children": [
        {"id": "mirrors", "title": "Mirrors / duplicates of hot", "children": []},
        {"id": "onedrive-trees", "title": "OneDrive / desktop trees", "children": []},
        {"id": "super-master", "title": "Super-master triage", "children": []},
        {"id": "loose-uploads", "title": "Loose / uploads", "children": []},
        {"id": "unfiled", "title": "Unfiled", "children": []},
    ],
}

ORG_HOMES: dict[str, list[str]] = {
    "container:organization": ["organization", "mirrors"],
    "container:loose-files": ["organization", "loose-uploads"],
    "container:super-master-triage": ["organization", "super-master"],
    "container:onedrive-personal": ["organization", "onedrive-trees"],
    "container:45gb-final-onedrive": ["organization", "onedrive-trees"],
    "container:backups": ["organization", "mirrors"],
}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    path = root / "artifacts/catalog/blob_homes_assignments.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assignments = data.get("assignments") or data
    board = data.get("board") or {}

    moved = 0
    for cid, path_list in MOVE_TO_DUP.items():
        if cid in assignments:
            assignments[cid] = {
                "path": path_list,
                "moved_at": datetime.now(timezone.utc).isoformat(),
                "auto": "dup-report",
            }
            moved += 1

    org_moved = 0
    for cid, path_list in ORG_HOMES.items():
        if cid in assignments:
            assignments[cid] = {
                "path": path_list,
                "moved_at": datetime.now(timezone.utc).isoformat(),
                "auto": "organization-domain",
            }
            org_moved += 1

    domains = board.get("domains") or []
    domains = [d for d in domains if d.get("id") != "organization"]
    domains.append(ORG_BOTTOM)
    board["domains"] = domains

    out = {
        "version": 2,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "board": board,
        "assignments": assignments,
    }
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    reg = root / "artifacts/catalog/registered_homes.json"
    reg.write_text(
        json.dumps(
            {
                "version": 2,
                "updated_at": out["exported_at"],
                "assignments": assignments,
                "board": board,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Dup moves: {moved} · Org homes: {org_moved} · Organization domain at bottom")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
