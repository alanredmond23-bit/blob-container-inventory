#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f "$SCRIPT_DIR/config.env" ]]; then
  echo "Missing $SCRIPT_DIR/config.env (copy from config.example.env)" >&2
  exit 1
fi

# shellcheck disable=SC1091
source "$SCRIPT_DIR/config.env"

mkdir -p "$LOCAL_ROOT"

DRY_RUN_FLAG=""
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN_FLAG="--dry-run"
fi

if [[ -z "${AZCOPY_FILES_SAS:-}" ]]; then
  echo "AZCOPY_FILES_SAS is empty in config.env" >&2
  exit 1
fi

REMOTE="https://${AZ_STORAGE_ACCOUNT}.file.core.windows.net/${AZ_FILES_SHARE}?${AZCOPY_FILES_SAS}"

echo "Sync (AzureFiles -> Local)"
echo "  remote: ${AZ_STORAGE_ACCOUNT}/${AZ_FILES_SHARE}"
echo "  local:  ${LOCAL_ROOT}"
echo "  delete: ${DELETE_DESTINATION}"

azcopy sync "$REMOTE" "$LOCAL_ROOT" \
  --recursive=true \
  --delete-destination="${DELETE_DESTINATION}" \
  ${DRY_RUN_FLAG}