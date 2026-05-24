#!/usr/bin/env bash
set -euo pipefail

STATS0="/workspace/artifacts/dedup/ag2-live/shard_0/stats.json"
STATS1="/workspace/artifacts/dedup/ag2-live/shard_1/stats.json"
LOG="/workspace/artifacts/dedup/ag2-live/wait_and_merge.log"
MAX_WAIT=5400
INTERVAL=30

exec > >(tee -a "$LOG") 2>&1
start=$(date +%s)

echo "[$(date -Is)] Polling for shard stats (up to ${MAX_WAIT}s)"

while true; do
  s0=false
  s1=false
  [[ -f "$STATS0" ]] && s0=true
  [[ -f "$STATS1" ]] && s1=true

  if $s0 && $s1; then
    echo "[$(date -Is)] Both stats.json present"
    break
  fi

  elapsed=$(( $(date +%s) - start ))
  if (( elapsed >= MAX_WAIT )); then
    echo "[$(date -Is)] ERROR: timeout; s0=$s0 s1=$s1"
    exit 1
  fi

  echo "[$(date -Is)] waiting... s0=$s0 s1=$s1 elapsed=${elapsed}s"
  pgrep -af 'blob_dedup_inventory_stream' || echo "  (no inventory stream running)"
  sleep "$INTERVAL"
done

echo "[$(date -Is)] Running merge_inventory_dedup.py"
cd /workspace
python3 scripts/merge_inventory_dedup.py \
  --dir artifacts/dedup/ag2-live/shard_0 \
  --dir artifacts/dedup/ag2-live/shard_1 \
  --dir artifacts/dedup/ag3b

echo "[$(date -Is)] Merge complete"
