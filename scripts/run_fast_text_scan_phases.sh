#!/usr/bin/env bash
# Phase 1: priority TXT/MD fulltext (strict Overt regex)
# Phase 2: non-priority fast extensions (txt,md,pdf,docx)
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)/azdedup/src"

run_phase() {
  local out="$1"
  shift
  mkdir -p "$out"
  echo "=== Phase -> $out ==="
  for s in 0 1 2 3 4; do
    python3 scripts/fast_text_scan_worker.py --shard "$s" --num-shards 5 --workers 32 \
      --out "$out" "$@" > "${out}/shard_${s}.log" 2>&1 &
  done
  wait
}

echo "Phase 1: priority TXT+MD..."
run_phase artifacts/catalog/fast_scan_p1_txt --priority-only --extensions txt,md

echo "Phase 2: non-priority fast path..."
run_phase artifacts/catalog/fast_scan_p2_rest --non-priority-only --extensions txt,md,pdf,docx

echo "Fetch overt_act_matrix.json from Azure..."
python3 << 'PY'
import json
import os
import re
from pathlib import Path

from azdedup.azure_client import download_blob_bytes, get_blob_service_client

account = os.environ.get("AZURE_STORAGE_ACCOUNT", "")
if not account:
    raise SystemExit("Set AZURE_STORAGE_ACCOUNT")

client = get_blob_service_client(account)
container = "legal-filings"
blob_path = "LEGAL/LEGAL/Superseding/output/overt_act_matrix.json"
data = download_blob_bytes(client, container, blob_path)
out = Path("artifacts/catalog/fast_scan/overt_act_matrix.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(data)
text = data.decode("utf-8", errors="replace")
overt = set(int(m.group(1)) for m in re.finditer(r"Redmond\s*Overt\s*Acts?\s*0*(\d{1,4})", text, re.I) if 1 <= int(m.group(1)) <= 722)
summary = {"bytes": len(data), "distinct_overt_in_matrix": len(overt), "sample_ids": sorted(overt)[:30]}
Path("artifacts/catalog/fast_scan/overt_act_matrix_summary.json").write_text(
    json.dumps(summary, indent=2) + "\n"
)
print(json.dumps(summary, indent=2))
PY

python3 scripts/fast_text_scan_merge.py \
  artifacts/catalog/fast_scan_p1_txt \
  artifacts/catalog/fast_scan_p2_rest

echo "Done."
