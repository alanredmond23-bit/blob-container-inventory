#!/usr/bin/env python3
"""Merge inventory shard dedup + SDK dedup CSVs into master manifest."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

DEFAULT_CERTAINTIES = frozenset({"PROVEN_EXACT", "PROVEN_EXACT_ETAG", "PROVEN_EXACT_COMPUTED"})
SECRET = re.compile(r"AC[a-f0-9]{32}", re.I)

DEFAULT_DIRS = [
    Path("artifacts/dedup/ag2-live/shard_0"),
    Path("artifacts/dedup/ag2-live/shard_1"),
    Path("artifacts/dedup/ag3b"),
]

FIELDS = [
    "certainty",
    "action",
    "keep_container",
    "keep_blob",
    "delete_container",
    "delete_blob",
    "content_length",
    "content_md5",
    "etag",
    "source",
    "sha256_computed",
]


def load_delete_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return list(csv.DictReader(path.open(newline="", encoding="utf-8")))


def resolve_sources(dirs: list[Path], extra_csvs: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for d in dirs:
        p = d / "delete_candidates.csv" if d.is_dir() else d
        if p.exists():
            paths.append(p)
    for p in extra_csvs:
        if p.exists():
            paths.append(p)
    return paths


def scrub_line(line: str) -> bool:
    """Return True if line should be dropped (contains Twilio AC SID)."""
    return bool(SECRET.search(line))


def write_manifest(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            line = ",".join(str(r.get(k, "")) for k in FIELDS)
            if scrub_line(line):
                continue
            w.writerow(r)


def container_breakdown(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rows:
        c = r.get("delete_container") or ""
        counts[c] = counts.get(c, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def largest_samples(rows: list[dict], n: int = 15) -> list[dict]:
    return sorted(rows, key=lambda r: int(r.get("content_length") or 0), reverse=True)[:n]


def update_approval_request(
    path: Path,
    summary: dict,
    top_containers: dict[str, int],
    samples: list[dict],
    sources: list[str],
) -> None:
    mib = summary["bytes_reclaimable"] / (1024 * 1024)
    cert_parts = ", ".join(f"`{k}`: {v:,}" for k, v in sorted(summary["certainty_breakdown"].items()))
    top_lines = "\n".join(f"- `{c}`: {n:,} deletes" for c, n in list(top_containers.items())[:10])
    sample_lines = []
    for r in samples:
        kb = int(r.get("content_length") or 0)
        dk = f"{r.get('delete_container')}/{r.get('delete_blob', '')[:80]}"
        kk = f"{r.get('keep_container')}/{r.get('keep_blob', '')[:80]}"
        sample_lines.append(f"- **{kb:,} B** — delete `{dk}` → keep `{kk}`")

    body = f"""# Approval request — blob dedup (inventory merge)

**Status:** Ready for your approval. **No deletes executed.**

## Metrics

| Metric | Value |
|--------|------:|
| Delete rows | {summary['delete_rows']:,} |
| Bytes reclaimable | {summary['bytes_reclaimable']:,} (~{mib:.1f} MiB) |
| Certainty breakdown | {cert_parts} |

## Sources merged

{chr(10).join(f'- `{s}`' for s in sources)}

## Approve

- [ ] **Execute deletes** from `artifacts/dedup/MASTER_DEDUP_MANIFEST.csv` (after spot-check below)

## Top containers (delete count)

{top_lines}

## Sample deletes (largest)

{chr(10).join(sample_lines)}

## Notes

- Twilio account SID patterns (`AC[a-f0-9]{{32}}`) scrubbed from manifest lines.
- Inventory shards: `PROVEN_EXACT` (Content-MD5) and `PROVEN_EXACT_ETAG`.
- SDK scan (ag3b): `PROVEN_EXACT_COMPUTED` (SHA-256 verified).
"""
    path.write_text(body, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Merge dedup delete_candidates CSVs into master manifest.")
    ap.add_argument("--dir", type=Path, action="append", dest="dirs", default=[], help="Dir containing delete_candidates.csv")
    ap.add_argument("--csv", type=Path, action="append", default=[], help="Explicit delete_candidates.csv path")
    ap.add_argument(
        "--certainty",
        action="append",
        dest="certainties",
        default=[],
        help="Allowed certainty values (repeatable)",
    )
    ap.add_argument("--output", type=Path, default=Path("artifacts/dedup/MASTER_DEDUP_MANIFEST.csv"))
    ap.add_argument("--approval", type=Path, default=Path("artifacts/dedup/APPROVAL_REQUEST.md"))
    args = ap.parse_args()

    dirs = args.dirs or DEFAULT_DIRS
    allowed = frozenset(args.certainties) if args.certainties else DEFAULT_CERTAINTIES
    source_paths = resolve_sources(dirs, args.csv)

    rows: list[dict] = []
    for p in source_paths:
        rows.extend(load_delete_csv(p))

    seen: set[tuple] = set()
    master: list[dict] = []
    for r in rows:
        if r.get("certainty") not in allowed:
            continue
        blob_text = (r.get("delete_blob") or "") + (r.get("keep_blob") or "")
        if SECRET.search(blob_text):
            continue
        key = (
            r["delete_container"],
            r["delete_blob"],
            r.get("content_md5", ""),
            r.get("etag", ""),
            r.get("sha256_computed", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        master.append(r)

    write_manifest(args.output, master)

    breakdown: dict[str, int] = {}
    for r in master:
        c = r.get("certainty", "")
        breakdown[c] = breakdown.get(c, 0) + 1

    summary = {
        "delete_rows": len(master),
        "bytes_reclaimable": sum(int(r.get("content_length") or 0) for r in master),
        "certainty_breakdown": breakdown,
        "sources": [str(p) for p in source_paths],
    }
    summary_path = args.output.parent / "SUMMARY.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    top = container_breakdown(master)
    update_approval_request(
        args.approval,
        summary,
        top,
        largest_samples(master),
        [str(p) for p in source_paths],
    )

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
