#!/usr/bin/env bash
# 5-agent fast Bates scan (priority PDF/TXT/DOCX/MD — no images, no OCR).
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)/azdedup/src"
# Requires storage account name in environment (see config.example.env)

mkdir -p artifacts/catalog/fast_scan

echo "Starting 5 fast-text scan shards (priority queue)..."
for s in 0 1 2 3 4; do
  python3 scripts/fast_text_scan_worker.py --shard "$s" --num-shards 5 --workers 28 \
    > "artifacts/catalog/fast_scan/shard_${s}.log" 2>&1 &
done
wait
echo "Merging summaries..."
python3 scripts/fast_text_scan_merge.py
echo "Done."
