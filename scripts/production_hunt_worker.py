#!/usr/bin/env python3
"""Shard-aware production hunt over Alansinv inventory."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from azdedup.inventory import iter_inventory, resolve_inventory_paths

RE_TAX = re.compile(r"RedmondTax0*(\d{1,6})", re.I)
RE_OVERT = re.compile(r"RedmondOvertActs0*(\d{1,4})|RedmondOvert0*(\d{1,4})|OvertActs0*(\d{1,4})", re.I)
RE_IPHONE = re.compile(r"RedmondiPhone0*(\d{1,5})|RedmondPhone0*(\d{1,5})", re.I)
RE_AR = re.compile(r"AR-0*(\d+)", re.I)
RE_FIVE9_02 = re.compile(r"FIVE9[_\- ]?0?2", re.I)
RE_FIVE9_03 = re.compile(r"FIVE9[_\- ]?0?3", re.I)


def paths_for_shards(shards: str | None, all_inv: bool) -> list[Path]:
    if shards:
        ids = [s.strip() for s in shards.split(",")]
        return [Path(f"artifacts/dedup/shards/shard_{i}.csv") for i in ids]
    if all_inv:
        return resolve_inventory_paths("artifacts/dedup/ag1/Alansinv_1000000_*.csv")
    raise ValueError("Specify --shards or --all-inventory")


def pick_canonical(paths: list[str]) -> str:
    if not paths:
        return ""
    ranked = sorted(paths, key=lambda p: (p.count("/"), len(p), p))
    for pref in ("uploads/", "discovery/", "legal-filings/"):
        for p in ranked:
            if pref in p:
                return p
    return ranked[0]


def hunt_prod01(paths: list[Path], out: Path) -> dict:
    found: dict[int, list[str]] = defaultdict(list)
    memorex = 0
    fed_disco = 0
    zips: list[str] = []
    for blob in iter_inventory(paths):
        low = f"{blob.container}/{blob.blob_path}".lower()
        if "memorex" in low:
            memorex += 1
        if "fed fed 2026" in low or "fed 2026 final disco" in low:
            fed_disco += 1
        if low.endswith(".zip") and ("memorex" in low or "final fed" in low or "disco" in low):
            if len(zips) < 500:
                zips.append(f"{blob.container}/{blob.blob_path}")
        m = RE_TAX.search(blob.blob_path)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 8835:
                found[n].append(f"{blob.container}/{blob.blob_path}")
    out.mkdir(parents=True, exist_ok=True)
    with (out / "prod01_found_ids.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bates_id", "canonical_path", "copy_count"])
        for n in sorted(found):
            ps = found[n]
            w.writerow([n, pick_canonical(ps), len(ps)])
    missing = [n for n in range(1, 8836) if n not in found]
    with (out / "prod01_missing_ids.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bates_id"])
        for n in missing:
            w.writerow([n])
    with (out / "prod01_zip_candidates.json").open("w", encoding="utf-8") as f:
        json.dump(zips[:200], f, indent=2)
    return {
        "distinct_found": len(found),
        "missing": len(missing),
        "memorex_blobs": memorex,
        "fed_2026_disco_blobs": fed_disco,
    }


def hunt_prod02(paths: list[Path], out: Path, bates_min: int, bates_max: int, label: str) -> dict:
    found: dict[int, list[str]] = defaultdict(list)
    by_container: dict[str, int] = defaultdict(int)
    for blob in iter_inventory(paths):
        m = RE_TAX.search(blob.blob_path)
        if not m:
            continue
        n = int(m.group(1))
        if bates_min <= n <= bates_max:
            p = f"{blob.container}/{blob.blob_path}"
            found[n].append(p)
            by_container[blob.container] += 1
    out.mkdir(parents=True, exist_ok=True)
    tag = label.replace("/", "_")
    with (out / f"prod02_{tag}_found_ids.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bates_id", "canonical_path", "copy_count"])
        for n in sorted(found):
            ps = found[n]
            w.writerow([n, pick_canonical(ps), len(ps)])
    with (out / f"prod02_{tag}_container_heatmap.json").open("w", encoding="utf-8") as f:
        json.dump(dict(sorted(by_container.items(), key=lambda x: -x[1])), f, indent=2)
    return {
        "range": f"{bates_min}-{bates_max}",
        "distinct_found": len(found),
        "blob_rows": sum(len(v) for v in found.values()),
        "top_containers": dict(sorted(by_container.items(), key=lambda x: -x[1])[:10]),
    }


def hunt_prod04_five9(paths: list[Path], out: Path, prod: str) -> dict:
    tag_re = RE_FIVE9_02 if prod == "02" else RE_FIVE9_03
    tag_sub = f"five9_{prod}"
    ar_ids: dict[int, list[str]] = defaultdict(list)
    blob_total = 0
    for blob in iter_inventory(paths):
        path = f"{blob.container}/{blob.blob_path}"
        low = path.lower()
        if not (low.endswith(".wav") or ".wav/" in low):
            continue
        if not (tag_re.search(path) or tag_sub in low):
            continue
        blob_total += 1
        m = RE_AR.search(path)
        if m:
            ar_ids[int(m.group(1))].append(path)
    out.mkdir(parents=True, exist_ok=True)
    fname = f"prod04_five9_{prod}_ar_ids.csv" if prod == "02" else f"prod05_five9_{prod}_ar_ids.csv"
    with (out / fname).open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ar_id", "canonical_path", "copy_count"])
        for n in sorted(ar_ids):
            ps = ar_ids[n]
            w.writerow([n, pick_canonical(ps), len(ps)])
    summary = {
        "prod": f"FIVE9_{prod}",
        "wav_blob_rows": blob_total,
        "distinct_ar_ids": len(ar_ids),
    }
    with (out / f"five9_{prod}_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return summary


def hunt_prod04_docs(paths: list[Path], out: Path) -> dict:
    iphone: dict[int, list[str]] = defaultdict(list)
    unnumbered: list[str] = []
    confidential: list[str] = []
    for blob in iter_inventory(paths):
        path = f"{blob.container}/{blob.blob_path}"
        low = path.lower()
        m = RE_IPHONE.search(blob.blob_path)
        if m:
            g = m.group(1) or m.group(2)
            if g:
                n = int(g)
                if 1 <= n <= 9698:
                    iphone[n].append(path)
        if "redmond phone" in low or "redmond apple iphone" in low:
            if len(unnumbered) < 5000:
                unnumbered.append(path)
        if "prod02_confidential" in low or "prod02 confidential" in low:
            if len(confidential) < 500:
                confidential.append(path)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "prod04_iphone_found.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bates_id", "canonical_path", "copy_count"])
        for n in sorted(iphone):
            ps = iphone[n]
            w.writerow([n, pick_canonical(ps), len(ps)])
    with (out / "prod04_iphone_unnumbered_paths.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["path"])
        for p in unnumbered[:5000]:
            w.writerow([p])
    with (out / "prod04_confidential_paths.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["path"])
        for p in confidential:
            w.writerow([p])
    return {
        "iphone_distinct": len(iphone),
        "iphone_unnumbered_paths": len(unnumbered),
        "confidential_path_hits": len(confidential),
    }


def hunt_prod05_join(paths: list[Path], out: Path, deep_v4: Path, sample_search: int) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    ar_paths: dict[int, list[str]] = defaultdict(list)
    for blob in iter_inventory(paths):
        path = f"{blob.container}/{blob.blob_path}"
        for m in re.finditer(r"(?:AR|AG)-0*(\d+)", path, re.I):
            ar_paths[int(m.group(1))].append(path)

    matched = 0
    rows_out = []
    total_rows = 0
    with deep_v4.open(encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            ar = (row.get("ar_id") or "").strip()
            if not ar:
                continue
            total_rows += 1
            digits = re.sub(r"\D", "", ar)
            key = int(digits) if digits else None
            hits = ar_paths.get(key, []) if key is not None else []
            if hits:
                matched += 1
            rows_out.append([ar, len(hits), pick_canonical(hits) if hits else ""])
    with (out / "prod05_deep_v4_azure_join.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ar_id", "match_count", "sample_path"])
        w.writerows(rows_out)
    return {
        "deep_v4_rows_scanned": total_rows,
        "rows_with_azure_match": matched,
        "match_pct": round(100.0 * matched / total_rows, 2) if total_rows else 0,
    }


def hunt_prod03(paths: list[Path], out: Path) -> dict:
    """PROD03: filename regex is invalid — Overt Acts Bates are on-page stamps.

    Use scripts/prod03_document_census.py + prod03_bates_corner_ocr.py instead.
    This mode only collects path leads (Heim, overt_act_matrix, delivery CSV).
    """
    overt: dict[int, list[str]] = defaultdict(list)
    heim_csv: list[str] = []
    heim_disc = 0
    for blob in iter_inventory(paths):
        path = f"{blob.container}/{blob.blob_path}"
        low = path.lower()
        if "heim" in low and ("disc" in low or "disk" in low):
            heim_disc += 1
        if "discovery_part_2" in low and "heim" in low and low.endswith(".csv"):
            heim_csv.append(path)
        m = RE_OVERT.search(blob.blob_path)
        if m:
            g = m.group(1) or m.group(2) or m.group(3)
            if g:
                n = int(g)
                if 1 <= n <= 722:
                    overt[n].append(path)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "prod03_upload_watchlist.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["note", "path"])
        w.writerow(["status", "NOT_UPLOADED — 0 expected in Azure until upload"])
        for p in heim_csv[:20]:
            w.writerow(["heim_delivery_index", p])
    with (out / "prod03_status.md").open("w", encoding="utf-8") as f:
        f.write(
            "# PROD03 — RedmondOvertActs 0001–0722\n\n"
            "**Status:** Not uploaded to Azure (per operator).\n\n"
            f"- Distinct OvertActs Bates in inventory: **{len(overt)}**\n"
            f"- Heim disc path blobs: **{heim_disc}**\n"
            f"- Heim delivery CSV copies: **{len(heim_csv)}**\n\n"
            "Post-upload: re-run `production_hunt_worker.py --mode prod03-verify`.\n"
        )
    return {
        "distinct_overt_in_azure": len(overt),
        "heim_disc_blobs": heim_disc,
        "heim_csv_paths": len(heim_csv),
        "federal_declared": 722,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--shards", default=None, help="e.g. 00,01,02")
    ap.add_argument("--all-inventory", action="store_true")
    ap.add_argument("--bates-min", type=int, default=836)
    ap.add_argument("--bates-max", type=int, default=693308)
    ap.add_argument("--label", default="full")
    args = ap.parse_args()

    inv_paths = paths_for_shards(args.shards, args.all_inventory)
    print(f"Scanning {len(inv_paths)} file(s) mode={args.mode}", file=sys.stderr)

    if args.mode == "prod01":
        stats = hunt_prod01(inv_paths, args.out)
    elif args.mode == "prod02":
        stats = hunt_prod02(inv_paths, args.out, args.bates_min, args.bates_max, args.label)
    elif args.mode == "prod04-five9-02":
        stats = hunt_prod04_five9(inv_paths, args.out, "02")
    elif args.mode == "prod04-five9-03":
        stats = hunt_prod04_five9(inv_paths, args.out, "03")
    elif args.mode == "prod04-docs":
        stats = hunt_prod04_docs(inv_paths, args.out)
    elif args.mode == "prod05-join":
        deep = Path("prod_3/deep_v4.csv")
        stats = hunt_prod05_join(inv_paths, args.out, deep, sample_search=0)
    elif args.mode == "prod03":
        stats = hunt_prod03(inv_paths, args.out)
    else:
        raise SystemExit(f"Unknown mode: {args.mode}")

    summary_path = args.out / "summary.json"
    summary_path.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
