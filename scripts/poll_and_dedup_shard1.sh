#!/usr/bin/env bash
set -euo pipefail

CSV="/workspace/artifacts/dedup/ag1/Alansinv_1000000_1.csv"
OUTPUT_DIR="/workspace/artifacts/dedup/ag2-live"
STATS="${OUTPUT_DIR}/shard_1/stats.json"
LOG="/workspace/artifacts/dedup/ag2-live/poll_dedup_shard1.log"

CONTAINER="localtriage4162026admincomp"
BLOB="2026/05/10/22-57-55/Alansinv/Alansinv_1000000_1.csv"

MAX_WAIT=3600
POLL_INTERVAL=15
DOWNLOAD_AFTER=60

mkdir -p "$(dirname "$CSV")" "$OUTPUT_DIR"
exec > >(tee -a "$LOG") 2>&1

start=$(date +%s)
downloaded=false

echo "[$(date -Is)] Waiting for $CSV (poll up to ${MAX_WAIT}s, download after ${DOWNLOAD_AFTER}s)"

while true; do
  if [[ -f "$CSV" && -s "$CSV" ]]; then
    echo "[$(date -Is)] Found $CSV ($(wc -c < "$CSV") bytes)"
    break
  fi

  elapsed=$(( $(date +%s) - start ))
  if (( elapsed >= MAX_WAIT )); then
    echo "[$(date -Is)] ERROR: timeout after ${MAX_WAIT}s; $CSV still missing"
    exit 1
  fi

  if (( elapsed >= DOWNLOAD_AFTER )) && [[ "$downloaded" == false ]]; then
    echo "[$(date -Is)] Missing after ${DOWNLOAD_AFTER}s; streaming download from ${CONTAINER}/${BLOB}"
    python3 - <<'PY'
import os
import sys
from pathlib import Path

from azure.storage.blob import BlobServiceClient

account = os.environ["AZURE_STORAGE_ACCOUNT"]
key = os.environ["AZURE_STORAGE_KEY"]
container = "localtriage4162026admincomp"
blob = "2026/05/10/22-57-55/Alansinv/Alansinv_1000000_1.csv"
dest = Path("/workspace/artifacts/dedup/ag1/Alansinv_1000000_1.csv")

client = BlobServiceClient(
    account_url=f"https://{account}.blob.core.windows.net",
    credential=key,
)
bc = client.get_blob_client(container, blob)
dest.parent.mkdir(parents=True, exist_ok=True)
total = 0
with dest.open("wb") as f:
    stream = bc.download_blob()
    for chunk in stream.chunks():
        f.write(chunk)
        total += len(chunk)
print(f"Downloaded {total} bytes to {dest}", flush=True)
if total == 0:
    sys.exit(1)
PY
    downloaded=true
    if [[ -f "$CSV" && -s "$CSV" ]]; then
      echo "[$(date -Is)] Download complete"
      break
    fi
  fi

  sleep "$POLL_INTERVAL"
done

echo "[$(date -Is)] Running blob_dedup_inventory_stream.py"
cd /workspace
python3 scripts/blob_dedup_inventory_stream.py \
  --csv "$CSV" \
  --shard-id 1 \
  --output-dir "$OUTPUT_DIR"

echo "[$(date -Is)] Done. stats.json:"
cat "$STATS"
