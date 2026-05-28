#!/usr/bin/env python3
"""Fast Bates scan: txt/md grep + PDF/DOCX header/footer text. No OCR. No images."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from azdedup.azure_client import download_blob_bytes, get_blob_service_client
from azdedup.inventory import iter_inventory, resolve_inventory_paths

FAST_EXT = {".pdf", ".txt", ".md", ".docx", ".doc", ".rtf"}
MAX_BYTES = {".txt": 1_000_000, ".md": 1_000_000, ".pdf": 5_000_000, ".docx": 8_000_000, ".doc": 8_000_000, ".rtf": 2_000_000}

PRIORITY_KEYS = (
    "heim disc", "03_heim disk", "david heim", "discovery_part_2",
    "superseding", "overt_act", "fed fed 2026", "memorex", "natives/",
    "legal-filings", "discovery/", "uploads/", "redmondtax",
)

RE_TAX = re.compile(r"RedmondTax0*(\d{1,6})", re.I)
RE_OVERT = re.compile(r"Redmond\s*Overt\s*Acts?\s*0*(\d{1,4})", re.I)
# Strict: full production name only (avoid ROA-## false positives in legal docs)
RE_OVERT_ANY = re.compile(r"Redmond\s*Overt\s*Acts?\s*0*(\d{1,4})", re.I)

DEFAULT_ACCOUNT = os.environ.get("AZURE_STORAGE_ACCOUNT", "")


def is_priority(path: str) -> bool:
    low = path.lower()
    return any(k in low for k in PRIORITY_KEYS)


def ext_of(path: str) -> str:
    m = re.search(r"(\.[a-z0-9]+)$", path.lower())
    return m.group(1) if m else ""


def path_bates(path: str) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    m = RE_TAX.search(path)
    if m:
        n = int(m.group(1))
        prod = "PROD01" if n <= 8835 else "PROD02" if n >= 836 else "TAX_OTHER"
        out.append((prod, n))
    m = RE_OVERT.search(path)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 722:
            out.append(("PROD03", n))
    return out


def text_bates(text: str) -> list[tuple[str, int]]:
    found: list[tuple[str, int]] = []
    for m in RE_OVERT_ANY.finditer(text):
        g = m.group(1) or m.group(2)
        if g:
            n = int(g)
            if 1 <= n <= 722:
                found.append(("PROD03", n))
    for m in RE_TAX.finditer(text):
        n = int(m.group(1))
        if 1 <= n <= 8835:
            found.append(("PROD01", n))
        elif 836 <= n <= 693308:
            found.append(("PROD02", n))
    return found


def scan_txt_md(data: bytes) -> list[tuple[str, int]]:
    try:
        text = data.decode("utf-8", errors="replace")
    except Exception:
        return []
    return text_bates(text)


def scan_pdf_headfoot(data: bytes) -> list[tuple[str, int]]:
    import fitz

    found: list[tuple[str, int]] = []
    try:
        doc = fitz.open(stream=data, filetype="pdf")
        if len(doc) == 0:
            doc.close()
            return []
        page = doc[0]
        r = page.rect
        regions = [
            fitz.Rect(r.x0, r.y0, r.x1, r.y0 + r.height * 0.15),
            fitz.Rect(r.x0, r.y0 + r.height * 0.85, r.x1, r.y1),
        ]
        for rect in regions:
            found.extend(text_bates(page.get_text("text", clip=rect)))
        doc.close()
    except Exception:
        pass
    return found


def scan_docx(data: bytes) -> list[tuple[str, int]]:
    found: list[tuple[str, int]] = []
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for name in zf.namelist():
                if not (
                    name.startswith("word/header")
                    or name.startswith("word/footer")
                    or name == "word/document.xml"
                ):
                    continue
                try:
                    found.extend(text_bates(zf.read(name).decode("utf-8", errors="replace")))
                except Exception:
                    continue
    except Exception:
        pass
    return found


def process_blob(client, container: str, blob_path: str, size: int, ext: str) -> dict:
    row = {
        "container": container,
        "blob_path": blob_path,
        "size": size,
        "ext": ext,
        "hits": [],
        "method": [],
        "error": None,
    }
    for prod, n in path_bates(blob_path):
        row["hits"].append({"prod": prod, "bates": n, "via": "path"})
        row["method"].append("path")

    cap = MAX_BYTES.get(ext)
    if cap is None or size > cap:
        return row

    try:
        data = download_blob_bytes(client, container, blob_path, length=min(size, cap))
    except Exception as e:
        row["error"] = str(e)[:200]
        return row

    content_hits: list[tuple[str, int]] = []
    if ext in {".txt", ".md", ".rtf"}:
        content_hits = scan_txt_md(data)
        via = "fulltext"
    elif ext == ".pdf":
        content_hits = scan_pdf_headfoot(data)
        via = "pdf_headfoot"
    elif ext in {".docx", ".doc"}:
        content_hits = scan_docx(data) if ext == ".docx" else []
        via = "docx_xml"

    for prod, n in content_hits:
        if not any(h["prod"] == prod and h["bates"] == n for h in row["hits"]):
            row["hits"].append({"prod": prod, "bates": n, "via": via})
            row["method"].append(via)
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, required=True, help="0..num-shards-1")
    ap.add_argument("--num-shards", type=int, default=5)
    ap.add_argument("--priority-only", action="store_true", default=True)
    ap.add_argument("--all-fast", action="store_true", help="Include non-priority paths")
    ap.add_argument("--non-priority-only", action="store_true", help="Skip priority paths")
    ap.add_argument(
        "--extensions",
        default="",
        help="Comma list e.g. txt,md (default: all fast extensions)",
    )
    ap.add_argument(
        "--path-contains",
        default="",
        help="Comma substrings; blob path must match at least one",
    )
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--max-files", type=int, default=0, help="0 = no cap")
    ap.add_argument("--account", default=os.environ.get("AZURE_STORAGE_ACCOUNT", ""))
    ap.add_argument("--out", type=Path, default=Path("artifacts/catalog/fast_scan"))
    args = ap.parse_args()

    if args.all_fast or args.non_priority_only:
        args.priority_only = False

    allowed_ext = FAST_EXT
    if args.extensions.strip():
        allowed_ext = {f".{e.strip().lstrip('.')}" for e in args.extensions.split(",") if e.strip()}

    path_filters = [s.strip().lower() for s in args.path_contains.split(",") if s.strip()]

    inv = resolve_inventory_paths("artifacts/dedup/ag1/Alansinv_1000000_*.csv")
    if not args.account:
        raise SystemExit("Set AZURE_STORAGE_ACCOUNT")
    client = get_blob_service_client(args.account)
    out_dir = args.out / f"shard_{args.shard:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    work: list[tuple[str, str, int, str]] = []
    for i, blob in enumerate(iter_inventory(inv)):
        if i % args.num_shards != args.shard:
            continue
        ext = ext_of(blob.blob_path)
        if ext not in allowed_ext:
            continue
        path = f"{blob.container}/{blob.blob_path}"
        pri = is_priority(path)
        if args.priority_only and not pri:
            continue
        if args.non_priority_only and pri:
            continue
        if path_filters and not any(f in path.lower() for f in path_filters):
            continue
        work.append((blob.container, blob.blob_path, blob.size, ext))
        if args.max_files and len(work) >= args.max_files:
            break

    hits_rows: list[dict] = []
    stats = defaultdict(int)
    stats["queued"] = len(work)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(process_blob, client, c, p, s, e): (c, p)
            for c, p, s, e in work
        }
        for fut in as_completed(futures):
            stats["processed"] += 1
            try:
                row = fut.result()
            except Exception as e:
                stats["errors"] += 1
                continue
            if row.get("error"):
                stats["download_errors"] += 1
            for h in row.get("hits", []):
                stats[f"hit_{h['prod']}"] += 1
                stats[f"via_{h['via']}"] += 1
                hits_rows.append(
                    {
                        "production": h["prod"],
                        "bates_id": h["bates"],
                        "via": h["via"],
                        "container": row["container"],
                        "blob_path": row["blob_path"],
                        "ext": row["ext"],
                    }
                )
            if stats["processed"] % 500 == 0:
                print(f"shard {args.shard}: {stats['processed']}/{stats['queued']}", file=sys.stderr)

    hits_path = out_dir / "bates_hits.csv"
    with hits_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["production", "bates_id", "via", "container", "blob_path", "ext"],
        )
        w.writeheader()
        w.writerows(hits_rows)

    distinct = defaultdict(set)
    for r in hits_rows:
        distinct[r["production"]].add(r["bates_id"])

    summary = {
        "shard": args.shard,
        "queued": stats["queued"],
        "processed": stats["processed"],
        "hits_total": len(hits_rows),
        "distinct": {k: len(v) for k, v in distinct.items()},
        "stats": dict(stats),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
