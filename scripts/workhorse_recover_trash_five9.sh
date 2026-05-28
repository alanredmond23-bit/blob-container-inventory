#!/usr/bin/env bash
# Recover Five9 WAVs from WORKHORSE Trash before anything empties it.
# Step 1: Move Trash WAVs to a safe recovery folder.
# Step 2: Upload to Azure five9-calls/FIVE9_trash_recovery/.
#
# CRITICAL: Do NOT empty Trash until this script completes and upload is verified.
# 81,347 WAVs in Trash = sole local copy of some FIVE9_03 records.
#
# Usage:
#   export AZURE_STORAGE_KEY="<your-key>"
#   bash workhorse_recover_trash_five9.sh
set -euo pipefail

ACCOUNT="menageriesa36965"
CONTAINER="five9-calls"
DEST_PREFIX="FIVE9_trash_recovery"

TRASH_DIR="$HOME/.Trash"
RECOVERY_DIR="$HOME/Desktop/FIVE9_TRASH_RECOVERY_DO_NOT_DELETE"

if [[ -z "${AZURE_STORAGE_KEY:-}" ]]; then
  echo "ERROR: export AZURE_STORAGE_KEY='...' first" >&2
  exit 1
fi

echo "=== FIVE9 Trash Recovery ==="
echo "  Trash    : $TRASH_DIR"
echo "  Recovery : $RECOVERY_DIR"
echo ""

# Count WAVs in Trash
WAV_COUNT=$(find "$TRASH_DIR" -name "*.wav" -o -name "*.WAV" 2>/dev/null | wc -l | tr -d ' ')
echo "  WAV files in Trash: $WAV_COUNT"

if [[ "$WAV_COUNT" -eq 0 ]]; then
  echo "No WAVs in Trash. Nothing to do."
  exit 0
fi

# Step 1: Move to recovery folder (don't copy — saves disk space)
echo ""
echo "[Step 1] Moving Trash WAVs to recovery folder..."
mkdir -p "$RECOVERY_DIR"
find "$TRASH_DIR" \( -name "*.wav" -o -name "*.WAV" \) -print0 | \
  while IFS= read -r -d '' f; do
    rel="${f#$TRASH_DIR/}"
    dest_dir="$RECOVERY_DIR/$(dirname "$rel")"
    mkdir -p "$dest_dir"
    mv -n "$f" "$dest_dir/"
  done
echo "  Moved to: $RECOVERY_DIR"

# Step 2: Upload recovery folder to Azure
echo ""
echo "[Step 2] Uploading to Azure $CONTAINER/$DEST_PREFIX/..."

if command -v az &>/dev/null; then
  az storage blob upload-batch \
    --account-name "$ACCOUNT" \
    --account-key "$AZURE_STORAGE_KEY" \
    --destination "$CONTAINER" \
    --destination-path "$DEST_PREFIX" \
    --source "$RECOVERY_DIR" \
    --pattern "*.wav" \
    --overwrite false \
    --no-progress \
    --output table \
    2>&1 | tee "/tmp/five9_trash_upload_$(date +%Y%m%d_%H%M%S).log"
elif command -v azcopy &>/dev/null; then
  # Generate 48h SAS
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
  azcopy copy "$RECOVERY_DIR" \
    "https://$ACCOUNT.blob.core.windows.net/$CONTAINER/$DEST_PREFIX/?$SAS" \
    --recursive --include-pattern "*.wav" --overwrite false --put-md5 \
    2>&1 | tee "/tmp/five9_trash_azcopy_$(date +%Y%m%d_%H%M%S).log"
else
  echo "ERROR: Install 'az' (Azure CLI) or 'azcopy' to upload." >&2
  echo "Files are safe in: $RECOVERY_DIR"
  echo "Upload manually when az/azcopy is available."
  exit 1
fi

echo ""
echo "=== DONE ==="
echo "Recovery folder: $RECOVERY_DIR (safe to keep — do not delete until Azure upload verified)"
echo "Azure location : https://$ACCOUNT.blob.core.windows.net/$CONTAINER/$DEST_PREFIX/"
echo ""
echo "To verify upload count:"
echo "  python3 scripts/find_five9_all.py --container five9-calls --prefixes $DEST_PREFIX"
