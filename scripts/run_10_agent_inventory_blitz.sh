#!/usr/bin/env bash
# 10-agent inventory proven pass — ~11M rows in under 10 minutes wall clock.
# Serious results: PROVEN_EXACT + PROVEN_EXACT_ETAG delete_candidates (100% certainty).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SHARD_COUNT="${SHARD_COUNT:-10}"
INV_GLOB="${AZDEDUP_INVENTORY_PATH:-artifacts/dedup/ag1/Alansinv_1000000_*.csv}"
SHARD_DIR="${SHARD_DIR:-artifacts/dedup/shards}"
OUT_DIR="${BLITZ_OUTPUT_DIR:-artifacts/dedup/blitz-10m}"
MASTER="${MASTER_MANIFEST:-artifacts/dedup/MASTER_DEDUP_MANIFEST_v2.csv}"

start=$(date +%s)
echo "=== 10-agent inventory blitz (proven pass only) ==="
echo "Shards: $SHARD_COUNT | Output: $OUT_DIR"

echo "=== Step 1/3: split inventory (~2-4 min, one-time per export) ==="
python3 scripts/prep_alansinv_shards.py \
  --inventory-glob "$INV_GLOB" \
  --shard-count "$SHARD_COUNT" \
  --output-dir "$SHARD_DIR"

echo "=== Step 2/3: $SHARD_COUNT parallel analyzers ==="
mkdir -p "$OUT_DIR"
pids=()
for i in $(seq 0 $((SHARD_COUNT - 1))); do
  id=$(printf '%02d' "$i")
  python3 scripts/blob_dedup_inventory_stream.py \
    --csv "$SHARD_DIR/shard_${id}.csv" \
    --shard-id "$id" \
    --output-dir "$OUT_DIR" &
  pids+=($!)
done
fail=0
for pid in "${pids[@]}"; do
  wait "$pid" || fail=1
done
if (( fail )); then
  echo "ERROR: one or more shards failed" >&2
  exit 1
fi

echo "=== Step 3/3: merge master manifest ==="
merge_args=(--output "$MASTER" --approval "artifacts/dedup/APPROVAL_REQUEST_v2.md")
for i in $(seq 0 $((SHARD_COUNT - 1))); do
  merge_args+=(--dir "$OUT_DIR/shard_$(printf '%02d' "$i")")
done
python3 scripts/merge_inventory_dedup.py "${merge_args[@]}"

elapsed=$(( $(date +%s) - start ))
echo "=== Done in ${elapsed}s ==="
echo "Master manifest: $MASTER"
echo "Per-shard stats: $OUT_DIR/shard_*/stats.json"
python3 - <<'PY'
import json
from pathlib import Path
out = Path("artifacts/dedup/blitz-10m")
total_del = total_bytes = total_rows = 0
for stats_path in sorted(out.glob("shard_*/stats.json")):
    s = json.loads(stats_path.read_text())
    total_del += s.get("delete_candidates", 0)
    total_bytes += s.get("bytes_reclaimable", 0)
    total_rows += s.get("rows_read", 0)
print(f"Rows scanned: {total_rows:,}")
print(f"Delete candidates (proven): {total_del:,}")
print(f"Reclaimable bytes: {total_bytes:,} ({total_bytes/1024**3:.2f} GiB)")
PY
