#!/usr/bin/env python3
"""PROD03 phase 1: census all scannable documents (filename-agnostic).

Redmond Overt Acts are NOT named RedmondOvertActs in paths. Bates appear
stamped top-right or bottom-right on pages — use prod03_bates_corner_ocr.py
for phase 2.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from azdedup.inventory import iter_inventory, resolve_inventory_paths

DOC_EXT = re.compile(r"\.(pdf|tif|tiff|jpg|jpeg|png|doc|docx|txt|xlsx|msg|eml)$", re.I)

# Priority path signals (not production names)
PRIORITY_KEYS = (
    "heim disc",
    "03_heim disk",
    "david heim",
    "discovery_part_2",
    "superseding",
    "overt_act",
    "raw discovery",
    "small disk disc",
    "natives/",
    "text/",
)

RE_OVERT_BATES = re.compile(
    r"Redmond\s*Overt\s*Acts?\s*0*(\d{1,4})|ROA[-_]?0*(\d{1,4})",
    re.I,
)


def classify_path(path: str) -> str:
    low = path.lower()
    for key in PRIORITY_KEYS:
        if key in low:
            return key.replace("/", "").replace(" ", "_")
    return "other"


def main() -> int:
    inv = resolve_inventory_paths("artifacts/dedup/ag1/Alansinv_1000000_*.csv")
    out_dir = Path("artifacts/catalog/hunt/prod03")
    out_dir.mkdir(parents=True, exist_ok=True)

    total_docs = 0
    priority_docs = 0
    by_bucket: dict[str, int] = defaultdict(int)
    by_ext: dict[str, int] = defaultdict(int)
    overt_in_txt_path = 0

    census_path = out_dir / "prod03_document_census.csv"
    with census_path.open("w", newline="", encoding="utf-8") as cf:
        w = csv.writer(cf)
        w.writerow(["container", "blob_path", "size", "bucket", "extension"])

        for blob in iter_inventory(inv):
            bp = blob.blob_path
            if not DOC_EXT.search(bp):
                continue
            ext = DOC_EXT.search(bp).group(1).lower()
            bucket = classify_path(bp)
            total_docs += 1
            by_ext[ext] += 1
            by_bucket[bucket] += 1
            if bucket != "other":
                priority_docs += 1
            if RE_OVERT_BATES.search(bp):
                overt_in_txt_path += 1
            if total_docs <= 2_000_000:
                w.writerow([blob.container, bp, blob.size or 0, bucket, ext])

    summary = {
        "method": "document_census_filename_agnostic",
        "total_scannable_blobs": total_docs,
        "priority_path_blobs": priority_docs,
        "overt_pattern_in_path": overt_in_txt_path,
        "by_extension": dict(sorted(by_ext.items(), key=lambda x: -x[1])[:15]),
        "by_bucket": dict(sorted(by_bucket.items(), key=lambda x: -x[1])),
        "note": "PROD03 Bates 1-722 require corner OCR; see prod03_bates_corner_ocr.py",
        "federal_declared": 722,
    }
    (out_dir / "prod03_census_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    print(f"Wrote {census_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
