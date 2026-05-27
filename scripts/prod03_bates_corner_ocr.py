#!/usr/bin/env python3
"""PROD03 phase 2: detect RedmondOvertActs Bates 0001-0722 from page corners.

Bates stamps are typically top-right or bottom-right (per operator). Works on
local files or blobs downloaded from Azure.

Requires: pip install pymupdf pillow pytesseract
System: apt install tesseract-ocr

Usage:
  python3 scripts/prod03_bates_corner_ocr.py --input path/to/doc.pdf
  python3 scripts/prod03_bates_corner_ocr.py --manifest artifacts/catalog/hunt/prod03/ocr_queue.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

BATES_MIN, BATES_MAX = 1, 722

RE_OVERT = re.compile(
    r"Redmond\s*Overt\s*Acts?\s*0*(\d{1,4})",
    re.I,
)
# Fallback: isolated 1-4 digit stamp in corner crop only (high false-positive risk)
RE_CORNER_DIGITS = re.compile(r"\b(\d{1,4})\b")

# Corner crop as fraction of page (width, height from each edge)
CORNERS = {
    "top_right": (0.62, 0.0, 1.0, 0.18),
    "bottom_right": (0.62, 0.82, 1.0, 1.0),
    "top_left": (0.0, 0.0, 0.38, 0.18),
    "bottom_left": (0.0, 0.82, 0.38, 1.0),
}


def _import_ocr():
    try:
        import fitz  # pymupdf
        from PIL import Image
        import pytesseract
    except ImportError as e:
        raise SystemExit(
            "Install OCR deps: pip install pymupdf pillow pytesseract; "
            "apt install tesseract-ocr"
        ) from e
    return fitz, Image, pytesseract


def page_to_corners(fitz, Image, path: Path, page_num: int = 0, dpi: int = 200):
    doc = fitz.open(path)
    page = doc[page_num]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    w, h = img.size
    crops = {}
    for name, (x0, y0, x1, y1) in CORNERS.items():
        crops[name] = img.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
    doc.close()
    return crops


def ocr_corners(path: Path, pytesseract) -> dict[str, list[int]]:
    fitz, Image, _ = _import_ocr()
    found: dict[str, list[int]] = {k: [] for k in CORNERS}
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        doc = fitz.open(path)
        pages = min(len(doc), 3)  # Bates usually on page 1; check first 3
        doc.close()
        for p in range(pages):
            crops = page_to_corners(fitz, Image, path, p)
            for corner, crop in crops.items():
                text = pytesseract.image_to_string(crop, config="--psm 6")
                for m in RE_OVERT.finditer(text):
                    n = int(m.group(1))
                    if BATES_MIN <= n <= BATES_MAX:
                        found[corner].append(n)
    elif suffix in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}:
        img = Image.open(path)
        w, h = img.size
        for corner, (x0, y0, x1, y1) in CORNERS.items():
            crop = img.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
            text = pytesseract.image_to_string(crop, config="--psm 6")
            for m in RE_OVERT.finditer(text):
                n = int(m.group(1))
                if BATES_MIN <= n <= BATES_MAX:
                    found[corner].append(n)
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, help="Single PDF/image")
    ap.add_argument("--manifest", type=Path, help="CSV: container,blob_path,local_path")
    ap.add_argument("--out", type=Path, default=Path("artifacts/catalog/hunt/prod03"))
    args = ap.parse_args()

    _, _, pytesseract = _import_ocr()
    args.out.mkdir(parents=True, exist_ok=True)
    results = []

    paths: list[tuple[str, Path]] = []
    if args.input:
        paths.append((str(args.input), args.input))
    elif args.manifest:
        with args.manifest.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                lp = Path(row.get("local_path") or "")
                if lp.is_file():
                    paths.append((row.get("blob_path", ""), lp))
    else:
        ap.error("Provide --input or --manifest")

    all_ids: set[int] = set()
    for blob_path, local in paths:
        try:
            corners = ocr_corners(local, pytesseract)
            ids = {n for vals in corners.values() for n in vals}
            all_ids |= ids
            results.append(
                {
                    "blob_path": blob_path,
                    "local_path": str(local),
                    "bates_ids": sorted(ids),
                    "corners": corners,
                }
            )
        except Exception as e:
            results.append({"blob_path": blob_path, "error": str(e)})

    out_json = args.out / "prod03_bates_ocr_results.json"
    out_json.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    summary = {
        "files_scanned": len(paths),
        "distinct_bates_1_722": sorted(all_ids),
        "count": len(all_ids),
        "federal_declared": BATES_MAX,
    }
    (args.out / "prod03_bates_ocr_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
