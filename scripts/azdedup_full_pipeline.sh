#!/usr/bin/env bash
# Full azdedup pipeline (inventory bootstrap). Requires AZURE_STORAGE_ACCOUNT + credentials.
set -euo pipefail

: "${AZURE_STORAGE_ACCOUNT:?Set AZURE_STORAGE_ACCOUNT}"

INV="${AZDEDUP_INVENTORY_PATH:-artifacts/dedup/ag1/Alansinv_1000000_*.csv}"
ACCT="$AZURE_STORAGE_ACCOUNT"
COMMON=(--account "$ACCT" --source inventory --inventory-path "$INV" --containers all)

if [[ -f artifacts/dedup/ag1/Alansinv_1000000_0.0.csv ]]; then
  bash "$(dirname "$0")/cat_alansinv_part0.sh" 2>/dev/null || true
fi

echo "=== scan (meta tags) ==="
azdedup scan "${COMMON[@]}" --apply-tags --concurrency 64

echo "=== dedup partial ==="
azdedup dedup --stage partial "${COMMON[@]}" --apply-tags --concurrency 32

echo "=== dedup full ==="
azdedup dedup --stage full "${COMMON[@]}" --apply-tags --incremental --concurrency 16

echo "=== dedup canonical (mark-only) ==="
azdedup dedup --stage canonical "${COMMON[@]}" --apply-tags --strategy container_priority

echo "=== verify ==="
azdedup verify --account "$ACCT" --inventory-path "$INV" --sample-rate 0.001

echo "=== report ==="
azdedup report --account "$ACCT" --source inventory --inventory-path "$INV" --format table

echo "Done."
