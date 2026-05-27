#!/usr/bin/env python3
"""Scan Alansinv + repo indexes for federal production coverage (PROD01-05)."""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from azdedup.inventory import iter_inventory, resolve_inventory_paths

# Federal declared totals (from discovery log / user baseline)
FED_TOTALS = {
    "PROD01_RedmondTax_000001-008835": 8_835,
    "PROD02_RedmondTax_000836-693308": 692_473,
    "PROD03_RedmondOvertActs_0001-0722": 722,
    "PROD04_RedmondiPhone_00001-09698": 9_698,
    "PROD05_deep_v4_index_rows": 108_018,  # Prod03_Confidential CSV index in repo
}

RE_TAX = re.compile(r"RedmondTax0*(\d{1,6})", re.I)
RE_OVERT = re.compile(r"RedmondOvertActs0*(\d{1,4})|RedmondOvert0*(\d{1,4})", re.I)
RE_IPHONE = re.compile(r"RedmondiPhone0*(\d{1,5})|RedmondPhone0*(\d{1,5})", re.I)
RE_FIVE9 = re.compile(r"FIVE9_0[23]|FIVE9[-_ ]0[23]", re.I)
RE_AR = re.compile(r"AR-0*(\d+)", re.I)

CONTAINERS_FIVE9 = (
    "five9-calls",
    "uploads",
    "legal",
    "legal-filings",
    "backups",
    "organization",
    "onedrive-personal",
    "45gb-final-onedrive",
)


def scan_azure_inventory(paths: list[Path]) -> dict:
    stats = {
        "prod01_tax_ids": set(),
        "prod02_tax_ids": set(),
        "prod03_overt_ids": set(),
        "prod04_iphone_ids": set(),
        "prod01_blob_rows": 0,
        "prod02_blob_rows": 0,
        "five9_02_wav": 0,
        "five9_03_wav": 0,
        "five9_wav_total": 0,
        "ar_ids": set(),
        "path_leads": defaultdict(int),
        "by_container": defaultdict(lambda: defaultdict(int)),
        "sample_paths": defaultdict(list),
    }

    for blob in iter_inventory(paths):
        path = f"{blob.container}/{blob.blob_path}"
        low = path.lower()

        m = RE_TAX.search(blob.blob_path)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 8835:
                stats["prod01_tax_ids"].add(n)
                stats["prod01_blob_rows"] += 1
                stats["by_container"]["PROD01"][blob.container] += 1
            elif 836 <= n <= 693308:
                stats["prod02_tax_ids"].add(n)
                stats["prod02_blob_rows"] += 1
                stats["by_container"]["PROD02"][blob.container] += 1

        m = RE_OVERT.search(blob.blob_path)
        if m:
            g = m.group(1) or m.group(2)
            if g:
                n = int(g)
                if 1 <= n <= 722:
                    stats["prod03_overt_ids"].add(n)
                    stats["by_container"]["PROD03"][blob.container] += 1

        m = RE_IPHONE.search(blob.blob_path)
        if m:
            g = m.group(1) or m.group(2)
            if g:
                n = int(g)
                if 1 <= n <= 9698:
                    stats["prod04_iphone_ids"].add(n)
                    stats["by_container"]["PROD04_iphone"][blob.container] += 1

        if low.endswith(".wav") or ".wav/" in low:
            if blob.container in CONTAINERS_FIVE9 or "five9" in low or RE_FIVE9.search(path):
                stats["five9_wav_total"] += 1
                if "five9_02" in low or "five9-02" in low or "five9_2" in low:
                    stats["five9_02_wav"] += 1
                if "five9_03" in low or "five9-03" in low or "five9_3" in low:
                    stats["five9_03_wav"] += 1
                if len(stats["sample_paths"]["five9"]) < 5:
                    stats["sample_paths"]["five9"].append(path[:120])

        m = RE_AR.search(path)
        if m and low.endswith(".wav"):
            stats["ar_ids"].add(int(m.group(1)))

        for key in ("RedmondOvert", "OvertActs", "RedmondTax", "disco26", "Memorex"):
            if key.lower() in low and len(stats["sample_paths"][key]) < 3:
                stats["sample_paths"][key].append(path[:120])

        if "memorex" in low:
            stats["path_leads"]["memorex_blobs"] += 1
        if "f fed 2026 final disco" in low or "fed fed 2026" in low:
            stats["path_leads"]["fed_2026_disco_paths"] += 1
        if "heim" in low and ("disc" in low or "disk" in low):
            stats["path_leads"]["heim_disc_paths"] += 1
        if "redmond phone" in low or "redmond apple iphone" in low:
            stats["path_leads"]["unnumbered_iphone_paths"] += 1

    return stats


def main() -> int:
    inv = resolve_inventory_paths("artifacts/dedup/ag1/Alansinv_1000000_*.csv")
    print("Scanning Azure inventory...", file=sys.stderr)
    stats = scan_azure_inventory(inv)

  # deep_v4 row count
    deep_v4 = Path("prod_3/deep_v4.csv")
    prod05_rows = 0
    if deep_v4.is_file() and not deep_v4.read_text(encoding="utf-8", errors="replace").startswith("version https://git-lfs"):
        with deep_v4.open(encoding="utf-8-sig", errors="replace") as f:
            prod05_rows = sum(1 for _ in f) - 1

    p1 = len(stats["prod01_tax_ids"])
    p2 = len(stats["prod02_tax_ids"])
    p3 = len(stats["prod03_overt_ids"])
    p4 = len(stats["prod04_iphone_ids"])
    fed_bates_total = sum(
        v
        for k, v in FED_TOTALS.items()
        if k != "PROD05_deep_v4_index_rows"
    )
    have_bates = p1 + p2 + p3 + p4

    out = {
        "azure_confirmed": {
            "PROD01_distinct_RedmondTax_1-8835": p1,
            "PROD01_blob_rows_in_range": stats["prod01_blob_rows"],
            "PROD02_distinct_RedmondTax_836-693308": p2,
            "PROD02_blob_rows_in_range": stats["prod02_blob_rows"],
            "PROD03_distinct_RedmondOvertActs_1-722": p3,
            "PROD04_distinct_RedmondiPhone_1-9698": p4,
            "five9_wav_blobs_total": stats["five9_wav_total"],
            "five9_02_tagged_wavs": stats["five9_02_wav"],
            "five9_03_tagged_wavs": stats["five9_03_wav"],
            "distinct_AR_ids_on_wavs": len(stats["ar_ids"]),
        },
        "deficit_summary": {
            "federal_bates_declared_total": fed_bates_total,
            "distinct_bates_confirmed_in_azure": have_bates,
            "distinct_bates_deficit": fed_bates_total - have_bates,
            "prod05_index_rows_in_repo": prod05_rows,
            "prod05_index_deficit": max(0, FED_TOTALS["PROD05_deep_v4_index_rows"] - prod05_rows),
            "note": "Use distinct_bates for production completeness; blob_rows counts duplicate mirrors.",
        },
        "federal_declared": FED_TOTALS,
        "path_leads": dict(stats["path_leads"]),
        "top_containers": {
            k: dict(sorted(v.items(), key=lambda x: -x[1])[:8])
            for k, v in stats["by_container"].items()
        },
        "samples": dict(stats["sample_paths"]),
        "prod05_deep_v4_rows_in_repo": prod05_rows,
    }

    print(json.dumps(out, indent=2))

    out_path = Path("artifacts/catalog/production_deficit_scan.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    print("\n=== SCOREBOARD (Azure Alansinv, repo-verified) ===", file=sys.stderr)
    rows = [
        ("PROD01 RedmondTax 1-8835", FED_TOTALS["PROD01_RedmondTax_000001-008835"], p1),
        ("PROD02 RedmondTax 836-693308", FED_TOTALS["PROD02_RedmondTax_000836-693308"], p2),
        ("PROD03 RedmondOvertActs 1-722", FED_TOTALS["PROD03_RedmondOvertActs_0001-0722"], p3),
        ("PROD04 RedmondiPhone 1-9698", FED_TOTALS["PROD04_RedmondiPhone_00001-09698"], p4),
        ("PROD04/05 Five9 WAVs (all tags)", None, stats["five9_wav_total"]),
        ("PROD05 deep_v4.csv rows (repo)", FED_TOTALS["PROD05_deep_v4_index_rows"], prod05_rows),
    ]
    for name, fed, have in rows:
        if fed:
            pct = 100.0 * have / fed
            deficit = fed - have
            print(f"{name}: {have:,} / {fed:,} ({pct:.1f}%) deficit {deficit:,}", file=sys.stderr)
        else:
            print(f"{name}: {have:,} (no fed total in script)", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
