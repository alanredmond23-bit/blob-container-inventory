#!/usr/bin/env python3
"""
Workhorse local filesystem inventory: streaming JSONL + Markdown summary.
Low-memory: one os.walk, one JSON line per file, periodic flush.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path


EXCLUDE_DIR_NAMES = frozenset(
    {
        "node_modules",
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        ".npm",
        ".nvm",
        ".gradle",
        ".android",
        ".docker",
        ".Trash",
        "DerivedData",
        "Pods",
    }
)

# If any of these appear in the full path (POSIX), skip the directory tree.
EXCLUDE_PATH_SUBSTRINGS = (
    "/node_modules/",
    "/.git/",
    "/Library/Caches/",
    "/Library/Containers/",
    "/Library/Application Support/",
    "/Library/Group Containers/",
    "/Library/Logs/",
    "/Library/Mail/",
    "/Library/Messages/",
    "/Library/Photos/",
    "/Library/Developer/",
    "/.cursor/extensions/",
    "/.cursor/plugins/cache/",
    "/DiagnosticReports/",
    "/.gradle/",
    "/.android/",
    "/.docker/",
    ".app/Contents/",
    "/.Trash/",
    "/.npm/",
    "/.nvm/",
)


def path_has_excluded_substring(p: str) -> bool:
    return any(s in p for s in EXCLUDE_PATH_SUBSTRINGS)


def should_prune_dir(dir_path: Path, root: Path) -> bool:
    try:
        full = str(dir_path.resolve())
    except OSError:
        return True
    if path_has_excluded_substring(full):
        return True
    name = dir_path.name
    if name in EXCLUDE_DIR_NAMES:
        return True
    return False


def split_levels(rel: str) -> tuple[str, str]:
    """Match AZURE_BLOB_INVENTORY.md grouping: first folder, second folder."""
    parts = rel.replace("\\", "/").split("/")
    parts = [p for p in parts if p]
    if len(parts) <= 1:
        return "(root)", "(root)"
    if len(parts) == 2:
        return parts[0], "(root)"
    return parts[0], parts[1]


def md_escape(s: str) -> str:
    return s.replace("`", "\\`")


def run_scan(root: Path, out_dir: Path) -> int:
    root = root.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "index.jsonl"
    md_path = out_dir / "WORKHORSE_INVENTORY.md"
    log_path = out_dir / "indexer.log"

    lvl1_totals: dict[str, int] = defaultdict(int)
    lvl2_totals: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    started = time.time()
    file_count = 0
    byte_total = 0
    last_log = started

    def log(msg: str) -> None:
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n"
        with open(log_path, "a", encoding="utf-8") as lf:
            lf.write(line)
        print(line, end="", flush=True)

    # Fresh log for this run
    with open(log_path, "w", encoding="utf-8") as lf:
        lf.write(f"# workhorse_indexer log started {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        lf.write(f"root={root}\n")

    log(f"START scan root={root}")

    with open(jsonl_path, "w", encoding="utf-8") as jf:
        for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
            dp = Path(dirpath)
            try:
                if not str(dp.resolve()).startswith(str(root)):
                    continue
            except OSError:
                continue

            # Prune before descending
            pruned: list[str] = []
            for d in list(dirnames):
                child = dp / d
                if should_prune_dir(child, root):
                    pruned.append(d)
            for d in pruned:
                dirnames.remove(d)

            for name in filenames:
                fp = dp / name
                try:
                    st = fp.stat()
                except OSError as e:
                    log(f"SKIP stat err {fp}: {e}")
                    continue
                if not fp.is_file():
                    continue
                try:
                    rel = str(fp.relative_to(root))
                except ValueError:
                    continue

                rec = {
                    "path": rel,
                    "size": int(st.st_size),
                    "mtime": int(st.st_mtime),
                }
                jf.write(json.dumps(rec, ensure_ascii=True) + "\n")

                l1, l2 = split_levels(rel)
                lvl1_totals[l1] += 1
                lvl2_totals[l1][l2] += 1
                file_count += 1
                byte_total += int(st.st_size)

                now = time.time()
                if file_count % 50000 == 0:
                    jf.flush()
                    log(f"PROGRESS files={file_count:,} bytes={byte_total:,}")
                elif now - last_log > 30 and file_count % 5000 == 0:
                    jf.flush()
                    log(f"PROGRESS files={file_count:,}")
                    last_log = now

    elapsed = time.time() - started

    lines: list[str] = []
    lines.append("# Workhorse local inventory (approx counts)\n")
    lines.append(f"Root: `{md_escape(str(root))}`\n")
    lines.append(f"Generated: `{time.strftime('%Y-%m-%d %H:%M:%S %Z')}`\n")
    lines.append("Method: local `os.walk` + JSONL stream (metadata only; excludes caches/deps per plan).\n")
    lines.append(f"Elapsed: `{elapsed:.1f}s`\n")
    lines.append("\n---\n")
    lines.append("## Summary\n")
    lines.append(f"- Total files indexed: **{file_count:,}**\n")
    lines.append(f"- Total bytes (sum of file sizes): **{byte_total:,}**\n")
    lines.append("\n---\n")
    lines.append("## Top-level → subfolder → file counts\n")

    l1_items = sorted(lvl1_totals.items(), key=lambda kv: (-kv[1], kv[0].lower()))
    for l1, l1_count in l1_items:
        lines.append(f"- **{md_escape(l1)}**: {l1_count:,}\n")
        l2_items = sorted(lvl2_totals[l1].items(), key=lambda kv: (-kv[1], kv[0].lower()))
        if len(l2_items) == 1 and l2_items[0][0] == "(root)":
            continue
        for l2, l2_count in l2_items[:50]:
            lines.append(f"  - {md_escape(l2)}: {l2_count:,}\n")
        if len(l2_items) > 50:
            rem = sum(v for _, v in l2_items[50:])
            lines.append(
                f"  - *(+ {len(l2_items) - 50} more subfolders, {rem:,} files total)*\n"
            )
    lines.append("\n")

    with open(md_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    log(f"DONE files={file_count:,} WROTE {md_path}")
    return file_count


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path.home())
    ap.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "workhorse",
    )
    args = ap.parse_args()
    n = run_scan(args.root.expanduser().resolve(), args.out.expanduser().resolve())
    print(f"Indexed {n:,} files", flush=True)


if __name__ == "__main__":
    main()
    sys.exit(0)
