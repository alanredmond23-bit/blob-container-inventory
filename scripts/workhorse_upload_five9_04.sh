#!/usr/bin/env bash
# Upload FIVE9_04 WAVs from WORKHORSE OneDrive to Azure five9-04 container.
# Run ON WORKHORSE (local Mac). Requires: az CLI or azcopy + AZURE_STORAGE_KEY.
#
# Coverage: Azure already has 180,327 of ~250,000 FIVE9_04 files
# (sourced from onedrive-personal Part 4 folder via server-side copy).
# This script closes the remaining ~70k gap from WORKHORSE local storage.
#
# Usage:
#   export AZURE_STORAGE_KEY="<your-key>"
#   bash workhorse_upload_five9_04.sh
#
# Resumes automatically — safe to re-run.
set -euo pipefail

ACCOUNT="menageriesa36965"
DEST_CONTAINER="five9-04"

LOCAL_PART4="$HOME/Library/CloudStorage/OneDrive-Personal/01_LEGAL/LEGAL DOMAIN/FULL EXTRACTIONS/4.FULL EXTRACTION CALL PART 4"

if [[ -z "${AZURE_STORAGE_KEY:-}" ]]; then
  echo "ERROR: export AZURE_STORAGE_KEY='...' first" >&2
  exit 1
fi

if [[ ! -d "$LOCAL_PART4" ]]; then
  echo "ERROR: Source path does not exist: $LOCAL_PART4" >&2
  echo "Check OneDrive is synced. Run: ls \"$LOCAL_PART4\"" >&2
  exit 1
fi

echo "=== FIVE9_04 Upload — WORKHORSE → Azure ==="
echo "  Source : $LOCAL_PART4"
echo "  Dest   : https://$ACCOUNT.blob.core.windows.net/$DEST_CONTAINER/"
echo ""

WAV_COUNT=$(find "$LOCAL_PART4" -name "*.wav" -not -path "*/\.Trash/*" | wc -l | tr -d ' ')
echo "  WAV files found locally (excl. Trash): $WAV_COUNT"
echo ""

# Method 1: az CLI
if command -v az &>/dev/null; then
  echo "[Method: az storage blob upload-batch]"
  az storage blob upload-batch \
    --account-name "$ACCOUNT" \
    --account-key "$AZURE_STORAGE_KEY" \
    --destination "$DEST_CONTAINER" \
    --source "$LOCAL_PART4" \
    --pattern "*.wav" \
    --overwrite false \
    --no-progress \
    --output table \
    2>&1 | tee "/tmp/five9_04_upload_$(date +%Y%m%d_%H%M%S).log"
  echo "Done. Check log in /tmp/five9_04_upload_*.log"
  exit 0
fi

# Method 2: azcopy with SAS
if command -v azcopy &>/dev/null; then
  echo "[Method: azcopy with generated SAS token]"
  SAS=$(python3 - <<PYEOF
import base64, hashlib, hmac, datetime, urllib.parse
key = base64.b64decode("$AZURE_STORAGE_KEY")
account = "$ACCOUNT"
now = datetime.datetime.utcnow()
expiry = (now + datetime.timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
start = now.strftime("%Y-%m-%dT%H:%M:%SZ")
sp, ss, srt, sv, spr = "rwl", "b", "sco", "2020-08-04", "https"
sts = "\n".join([account, sp, ss, srt, start, expiry, "", spr, sv, ""])
sig = base64.b64encode(hmac.new(key, sts.encode(), hashlib.sha256).digest()).decode()
print(urllib.parse.urlencode({"sv":sv,"ss":ss,"srt":srt,"sp":sp,"st":start,"se":expiry,"spr":spr,"sig":sig}))
PYEOF
  )
  azcopy copy "$LOCAL_PART4" \
    "https://$ACCOUNT.blob.core.windows.net/$DEST_CONTAINER/?$SAS" \
    --recursive --include-pattern "*.wav" --overwrite false --put-md5 \
    --exclude-path ".Trash" \
    2>&1 | tee "/tmp/five9_04_azcopy_$(date +%Y%m%d_%H%M%S).log"
  echo "Done. Check log in /tmp/five9_04_azcopy_*.log"
  exit 0
fi

echo "ERROR: Install 'az' (Azure CLI) or 'azcopy' to upload." >&2
echo "Files are safe locally at: $LOCAL_PART4"
exit 1
