#!/usr/bin/env python3
"""
Compare local Five9-ish WAV paths against Azure `five9-calls`.

Azure naming note: many blobs look like:
  `FIVE9_02_CONFIDENTIAL_AR-0000132430 7.wav/DESKTOP WORKHORSE/.../file.eml`
So terminal `Path(name).suffix` is NOT `.wav`. We match on **AR-########** ids instead.

Requires AZURE_BLOB_ACCOUNT + AZURE_BLOB_KEY in environment.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from azure.storage.blob import ContainerClient

# Do not use \\b: Five9 paths often contain `_AR-0000123` (underscore glued to AR-).
AR_RE = re.compile(r"(?i)AR-\d+")


def load_secrets() -> None:
    p = Path.home() / "MASTER_RULES" / "SECRETS.env"
    if not p.is_file():
        return
    raw = p.read_text(encoding="utf-8", errors="replace")
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip("'").strip('"')
        if k and k not in os.environ:
            os.environ[k] = v


def is_five9_wav(rel_path: str) -> bool:
    """Local disk: real .wav files with Five9-ish naming."""
    lower = rel_path.lower()
    base = Path(rel_path).name.lower()
    if not base.endswith(".wav"):
        return False
    if "five9" in lower or "5_9" in lower:
        return True
    if "confidential_ar" in lower.replace(" ", "_").replace("-", "_"):
        return True
    return False


def extract_ar_ids(text: str) -> frozenset[str]:
    return frozenset(m.group(0).upper() for m in AR_RE.finditer(text))


def main() -> None:
    load_secrets()
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--index-jsonl",
        type=Path,
        default=Path(__file__).resolve().parent / "workhorse" / "index.jsonl",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "workhorse",
    )
    ap.add_argument("--container", default="five9-calls")
    args = ap.parse_args()

    account = os.environ.get("AZURE_BLOB_ACCOUNT")
    key = os.environ.get("AZURE_BLOB_KEY")
    if not account or not key:
        print("Missing AZURE_BLOB_ACCOUNT / AZURE_BLOB_KEY", file=sys.stderr)
        sys.exit(1)

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    azure_jsonl = out_dir / "five9_azure.jsonl"
    md_path = out_dir / "FIVE9_COVERAGE.md"

    # Local: AR-id -> example paths
    local_by_ar: dict[str, list[tuple[str, int]]] = {}
    local_lines = 0
    local_wav_hits = 0
    if args.index_jsonl.is_file():
        with open(args.index_jsonl, encoding="utf-8") as f:
            for line in f:
                local_lines += 1
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                rel = rec.get("path", "")
                size = int(rec.get("size", 0))
                if not is_five9_wav(rel):
                    continue
                local_wav_hits += 1
                for aid in extract_ar_ids(rel):
                    local_by_ar.setdefault(aid, []).append((rel, size))

    url = f"https://{account}.blob.core.windows.net"
    cc = ContainerClient(account_url=url, container_name=args.container, credential=key)

    azure_by_ar: dict[str, list[tuple[str, int]]] = {}
    with open(azure_jsonl, "w", encoding="utf-8") as af:
        for blob in cc.list_blobs():
            name = blob.name
            size = int(blob.size or 0)
            af.write(json.dumps({"name": name, "size": size}, ensure_ascii=True) + "\n")
            nl = name.lower()
            if "five9" not in nl and "confidential" not in nl:
                continue
            for aid in extract_ar_ids(name):
                azure_by_ar.setdefault(aid, []).append((name, size))

    local_ids = set(local_by_ar)
    azure_ids = set(azure_by_ar)
    only_local = sorted(local_ids - azure_ids)
    only_azure = sorted(azure_ids - local_ids)
    both = sorted(local_ids & azure_ids)

    lines: list[str] = []
    lines.append("# Five9 coverage (local vs Azure) — by `AR-########` id\n")
    lines.append(
        "Azure `five9-calls` uses **virtual-prefix** blob names (a `.wav` segment can be a folder prefix), "
        "so basename-only diffs are invalid. This report keys off **`AR-\\d+`** tokens found in paths.\n\n"
    )
    lines.append(f"- Local index lines scanned: **{local_lines:,}**\n")
    lines.append(f"- Local Five9-ish WAV files (matched filter): **{local_wav_hits:,}**\n")
    lines.append(f"- Distinct `AR-` ids seen locally: **{len(local_ids):,}**\n")
    lines.append(f"- Distinct `AR-` ids seen in Azure (`{args.container}`): **{len(azure_ids):,}**\n")
    lines.append(f"- In both: **{len(both):,}**\n")
    lines.append(f"- Only local ids (not found in Azure names): **{len(only_local):,}**\n")
    lines.append(f"- Only Azure ids (not found in local Five9-ish wav paths): **{len(only_azure):,}**\n")
    lines.append("\n---\n")
    lines.append("## Sample: only-local `AR-` ids (first 200)\n\n")
    for aid in only_local[:200]:
        rel, sz = local_by_ar[aid][0]
        lines.append(f"- `{aid}` — e.g. `{rel}` ({sz} bytes)\n")
    if len(only_local) > 200:
        lines.append(f"\n*(+ {len(only_local) - 200} more)*\n")
    lines.append("\n---\n")
    lines.append("## Sample: only-Azure `AR-` ids (first 200)\n\n")
    for aid in only_azure[:200]:
        nm, sz = azure_by_ar[aid][0]
        lines.append(f"- `{aid}` — e.g. `{nm}` ({sz} bytes)\n")
    if len(only_azure) > 200:
        lines.append(f"\n*(+ {len(only_azure) - 200} more)*\n")

    with open(md_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"WROTE {md_path}", flush=True)


if __name__ == "__main__":
    main()
