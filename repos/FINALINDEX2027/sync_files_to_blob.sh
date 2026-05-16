#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f "$SCRIPT_DIR/config.env" ]]; then
  echo "Missing $SCRIPT_DIR/config.env (copy from config.example.env)" >&2
  exit 1
fi

# Capture optional one-off overrides from the environment before sourcing config.
OVERRIDE_AZ_BLOB_CONTAINER="${AZ_BLOB_CONTAINER:-}"
OVERRIDE_AZCOPY_BLOB_SAS="${AZCOPY_BLOB_SAS:-}"
OVERRIDE_DELETE_DESTINATION="${DELETE_DESTINATION:-}"

# shellcheck disable=SC1091
source "$SCRIPT_DIR/config.env"

# Apply overrides after sourcing config (environment should win for ad-hoc runs).
if [[ -n "$OVERRIDE_AZ_BLOB_CONTAINER" ]]; then
  AZ_BLOB_CONTAINER="$OVERRIDE_AZ_BLOB_CONTAINER"
fi
if [[ -n "$OVERRIDE_AZCOPY_BLOB_SAS" ]]; then
  AZCOPY_BLOB_SAS="$OVERRIDE_AZCOPY_BLOB_SAS"
fi
if [[ -n "$OVERRIDE_DELETE_DESTINATION" ]]; then
  DELETE_DESTINATION="$OVERRIDE_DELETE_DESTINATION"
fi

DRY_RUN_FLAG=""
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN_FLAG="--dry-run"
fi

if [[ -z "${AZ_BLOB_CONTAINER:-}" || -z "${AZCOPY_BLOB_SAS:-}" ]]; then
  echo "Set AZ_BLOB_CONTAINER and AZCOPY_BLOB_SAS in config.env" >&2
  exit 1
fi

if [[ -z "${AZCOPY_FILES_SAS:-}" ]]; then
  echo "AZCOPY_FILES_SAS is empty in config.env" >&2
  exit 1
fi

SRC="https://${AZ_STORAGE_ACCOUNT}.file.core.windows.net/${AZ_FILES_SHARE}/${AZ_BLOB_CONTAINER}/?${AZCOPY_FILES_SAS}"
DST="https://${AZ_STORAGE_ACCOUNT}.blob.core.windows.net/${AZ_BLOB_CONTAINER}/?${AZCOPY_BLOB_SAS}"

echo "Sync (AzureFiles -> Blob)"
echo "  src: ${AZ_STORAGE_ACCOUNT}/${AZ_FILES_SHARE}/${AZ_BLOB_CONTAINER} (files)"
echo "  dst: ${AZ_STORAGE_ACCOUNT}/${AZ_BLOB_CONTAINER} (blob)"
echo "  delete: ${DELETE_DESTINATION}"

azcopy sync "$SRC" "$DST" \
  --recursive=true \
  --delete-destination="${DELETE_DESTINATION}" \
  ${DRY_RUN_FLAG}