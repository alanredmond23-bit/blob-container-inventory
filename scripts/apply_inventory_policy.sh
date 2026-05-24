#!/usr/bin/env bash
# Apply blob inventory policy (requires: az login, AZURE_RESOURCE_GROUP, AZURE_STORAGE_ACCOUNT)
set -euo pipefail
: "${AZURE_RESOURCE_GROUP:?}"
: "${AZURE_STORAGE_ACCOUNT:?}"
POLICY="${1:-Azure blob dedup/policies/blob-inventory-dedup.json}"
az extension add --name storage-preview -y 2>/dev/null || true
az storage account blob-inventory-policy create \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --account-name "$AZURE_STORAGE_ACCOUNT" \
  --policy "@$POLICY" \
  && echo "Policy applied. First CSV will land under container inventory-reports/ within ~24h."
