#!/usr/bin/env python3
"""Merge parallel production hunt outputs into final scoreboard."""

from __future__ import annotations

import csv
import json
from pathlib import Path

FED = {
    "PROD01": 8835,
    "PROD02": 692473,
    "PROD03": 722,
    "PROD04_IPHONE": 9698,
    "PROD05_INDEX": 108018,
}


def load_ids_csv(path: Path) -> set[int]:
    if not path.is_file():
        return set()
    ids: set[int] = set()
    with path.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                ids.add(int(row.get("bates_id") or row.get("ar_id") or 0))
            except ValueError:
                continue
    return ids


def main() -> None:
    base = Path("artifacts/catalog/hunt")
    p2a = load_ids_csv(base / "prod02a/prod02_836-350000_found_ids.csv")
    p2b = load_ids_csv(base / "prod02b/prod02_350001-693308_found_ids.csv")
    prod02 = p2a | p2b
    prod01 = load_ids_csv(base / "prod01/prod01_found_ids.csv")
    prod04_iphone = load_ids_csv(base / "prod04_docs/prod04_iphone_found.csv")

    summaries = {}
    for sub in ["prod01", "prod02a", "prod02b", "prod03", "prod04_five9", "prod04_docs", "prod05"]:
        sp = base / sub / "summary.json"
        if sp.is_file():
            summaries[sub] = json.loads(sp.read_text())

    five9_02 = summaries.get("prod04_five9", {})
    five9_03_path = base / "prod05/five9_03_summary.json"
    five9_03 = json.loads(five9_03_path.read_text()) if five9_03_path.is_file() else {}
    prod05_join = summaries.get("prod05", {})

    rows = [
        {
            "name": "PROD01 RedmondTax 1-8835",
            "fed": FED["PROD01"],
            "have": len(prod01),
            "locations": "Memorex; FED 2026 DISCO; see prod01_zip_candidates.json",
        },
        {
            "name": "PROD02 RedmondTax 836-693308",
            "fed": FED["PROD02"],
            "have": len(prod02),
            "locations": "organization, uploads, super-master-triage, discovery, backups",
        },
        {
            "name": "PROD03 RedmondOvertActs 1-722",
            "fed": FED["PROD03"],
            "have": summaries.get("prod03", {}).get("distinct_overt_in_azure", 0),
            "locations": "NOT UPLOADED — Heim disc leads in prod03/",
        },
        {
            "name": "PROD04 FIVE9_02",
            "fed": None,
            "have": five9_02.get("distinct_ar_ids"),
            "locations": "five9-calls, onedrive-personal, backups",
        },
        {
            "name": "PROD04 iPhone 1-9698",
            "fed": FED["PROD04_IPHONE"],
            "have": len(prod04_iphone),
            "locations": "03_HEIM DISK DISC; prod04_iphone_unnumbered_paths.csv",
        },
        {
            "name": "PROD05 FIVE9_03",
            "fed": None,
            "have": five9_03.get("distinct_ar_ids"),
            "locations": "same as Five9_02",
        },
        {
            "name": "PROD05 deep_v4 index → Azure",
            "fed": FED["PROD05_INDEX"],
            "have": prod05_join.get("rows_with_azure_match", 0),
            "locations": "prod05_deep_v4_azure_join.csv",
        },
    ]

    out_md = Path("docs/PRODUCTION_HUNT_RESULTS.md")
    lines = [
        "# Production hunt results (merged)\n",
        "| Name | Feds declared | Have confirmed | % done | Potential locations |",
        "|------|-------------:|---------------:|-------:|---------------------|",
    ]
    for r in rows:
        fed = r["fed"]
        have = r["have"] or 0
        pct = f"{100.0 * have / fed:.1f}%" if fed else "n/a"
        lines.append(
            f"| {r['name']} | {fed or '—'} | {have:,} | {pct} | {r['locations']} |"
        )

    deficit_bates = (
        (FED["PROD01"] - len(prod01))
        + (FED["PROD02"] - len(prod02))
        + (FED["PROD03"] - summaries.get("prod03", {}).get("distinct_overt_in_azure", 0))
        + (FED["PROD04_IPHONE"] - len(prod04_iphone))
    )
    lines.extend(
        [
            "",
            f"**Total Bates deficit (PROD01–04):** {deficit_bates:,}",
            "",
            "## Hunt artifacts",
            "",
            "Under `artifacts/catalog/hunt/` per agent folder.",
            "",
        ]
    )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    merged = {
        "prod01_distinct": len(prod01),
        "prod02_distinct": len(prod02),
        "prod02_part_a": len(p2a),
        "prod02_part_b": len(p2b),
        "prod04_iphone_distinct": len(prod04_iphone),
        "bates_deficit_01_04": deficit_bates,
        "summaries": summaries,
        "five9_03": five9_03,
        "prod05_join": prod05_join,
    }
    Path("artifacts/catalog/production_hunt_merged.json").write_text(
        json.dumps(merged, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(merged, indent=2))


if __name__ == "__main__":
    main()
