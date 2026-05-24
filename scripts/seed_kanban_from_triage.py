#!/usr/bin/env python3
"""Build kanban_board_seed.json from triage register + inventory case folders."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

MATTER_L2 = [
    {"id": "evidence", "title": "Evidence"},
    {"id": "discovery", "title": "Discovery"},
    {"id": "filings", "title": "Filings"},
    {"id": "strategy", "title": "Strategy"},
    {"id": "unfiled", "title": "Unfiled"},
]


def matter(id_: str, title: str) -> dict:
    return {"id": id_, "title": title, "children": [{**x, "children": []} for x in MATTER_L2]}


def matters_from_register(csv_path: Path) -> list[dict]:
    """Extract ACTIVE PROCEEDINGS / THREAT rows as legal matters."""
    out: list[dict] = []
    seen: set[str] = set()

    def add(id_: str, title: str) -> None:
        if id_ in seen:
            return
        seen.add(id_)
        out.append(matter(id_, title))

    add("bk-24-13093", "BK 24-13093")
    add("ap-25-00254", "AP 25-00254")
    add("foreclosure-25-13446", "Foreclosure 25-13446")

    if not csv_path.exists():
        return out

    lines = csv_path.read_text(encoding="utf-8", errors="replace").splitlines()
    start = 0
    for i, line in enumerate(lines):
        if line.startswith("ID,CATEGORY"):
            start = i
            break
    reader = csv.DictReader(lines[start:])
    for row in reader:
            item = (row.get("ITEM") or "").strip()
            cat = (row.get("CATEGORY") or "").strip()
            section = row.get("MASTER PLAN SECTION") or ""
            if cat != "ACTIVE THREAT" and "S19" not in section and "S20" not in section:
                continue
            if "Custody" in item:
                add("custody-montgomery-2016-47715", "Custody 2016-47715")
            elif "SBA Adversary" in item:
                add("sba-adv-25-00119", "SBA Adversary 25-00119")
            elif "Feldman" in item:
                add("feldman-doc-507", "Feldman Doc 507")
            elif "Foreclosure" in item and "foreclosure-25-13446" not in seen:
                add("foreclosure-8-morgan", "8 Morgan Foreclosure")
            elif "SNAP" in item:
                add("snap-osig-threat", "SNAP / OSIG (threat)")

    add("federal-defense", "Federal criminal defense")
    add("general-legal", "General / cross-matter")
    return out


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    register = root / "triage" / "REDMOND_DOCTRINE_COMPLETE_REGISTER.csv"
    legal_matters = matters_from_register(register)

    seed = {
        "version": 1,
        "source": ["triage/REDMOND_DOCTRINE_COMPLETE_REGISTER.csv", "123triageonedrive case folders"],
        "domains": [
            {
                "id": "legal",
                "merge": "replace_children",
                "children": legal_matters,
            }
        ],
        "container_hints": [
            {"container": "five9-calls", "suggest": ["legal", "federal-defense", "evidence"]},
            {"container": "discovery", "suggest": ["legal", "general-legal", "discovery"]},
            {"container": "legal-filings", "suggest": ["legal", "general-legal", "filings"]},
            {"container": "legal", "suggest": ["legal", "general-legal", "unfiled"]},
            {"container": "backups", "suggest": ["dup-likely", "structural-mirror"]},
            {"container": "organization", "suggest": ["dup-likely", "structural-mirror"]},
            {"container": "1triageworkhorse", "suggest": ["devops", "backups-caches"]},
            {"container": "financial-docs", "suggest": ["finance", "banking-cash"]},
            {"container": "save-money", "suggest": ["finance", "verticals"]},
            {"container": "make-money", "suggest": ["finance", "verticals"]},
        ],
    }
    out = root / "artifacts" / "catalog" / "kanban_board_seed.json"
    out.write_text(json.dumps(seed, indent=2), encoding="utf-8")
    print(f"Wrote {out} with {len(legal_matters)} legal matters")


if __name__ == "__main__":
    main()
