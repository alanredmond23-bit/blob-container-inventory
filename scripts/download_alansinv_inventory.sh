#!/usr/bin/env bash
# Download Azure blob inventory export (Alansinv ~10.4M rows) into artifacts/dedup/ag1/
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/artifacts/dedup/ag1"
CONTAINER="${ALANSINV_CONTAINER:-localtriage4162026admincomp}"
PREFIX="${ALANSINV_PREFIX:-2026/05/10/22-57-55/Alansinv/}"

: "${AZURE_STORAGE_ACCOUNT:?Set AZURE_STORAGE_ACCOUNT}"
: "${AZURE_STORAGE_KEY:?Set AZURE_STORAGE_KEY}"

mkdir -p "$OUT"

for part in Alansinv_1000000_0.csv Alansinv_1000000_1.csv; do
  blob="${PREFIX}${part}"
  dest="$OUT/$part"
  echo "Downloading $blob -> $dest"
  az storage blob download \
    --account-name "$AZURE_STORAGE_ACCOUNT" \
    --account-key "$AZURE_STORAGE_KEY" \
    --container-name "$CONTAINER" \
    --name "$blob" \
    --file "$dest" \
    --no-progress \
    --overwrite
  ls -lh "$dest"
done

echo "Done. Row check: wc -l $OUT/Alansinv_1000000_*.csv"
