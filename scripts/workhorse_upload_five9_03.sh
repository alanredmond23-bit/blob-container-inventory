#!/usr/bin/env bash
# Upload FIVE9_03 WAVs from WORKHORSE OneDrive to Azure five9-calls container.
# Run this ON WORKHORSE (local Mac). Requires: az CLI or azcopy + AZURE_STORAGE_KEY.
#
# Usage:
#   export AZURE_STORAGE_KEY="<your-key>"
#   bash workhorse_upload_five9_03.sh
#
# Resumes automatically if interrupted — safe to re-run.
set -euo pipefail

ACCOUNT="menageriesa36965"
CONTAINER="five9-calls"
DEST_PREFIX="FIVE9_03_folder"

# The local FULL EXTRACTION path for Part 3 (hydrated WAVs on WORKHORSE)
LOCAL_PART3="$HOME/Library/CloudStorage/OneDrive-Personal/01_LEGAL/LEGAL DOMAIN/FULL EXTRACTIONS/3. FULL EXTRACTION CALL PART 3"

if [[ -z "${AZURE_STORAGE_KEY:-}" ]]; then
  echo "ERROR: export AZURE_STORAGE_KEY='...' first" >&2
  exit 1
fi

if [[ ! -d "$LOCAL_PART3" ]]; then
  echo "ERROR: Source path does not exist: $LOCAL_PART3" >&2
  echo "Check OneDrive is synced. Run: ls \"$LOCAL_PART3\"" >&2
  exit 1
fi

echo "=== FIVE9_03 Upload — WORKHORSE → Azure ==="
echo "  Source : $LOCAL_PART3"
echo "  Dest   : https://$ACCOUNT.blob.core.windows.net/$CONTAINER/$DEST_PREFIX/"
echo ""

WAV_COUNT=$(find "$LOCAL_PART3" -name "*.wav" -not -path "*/\.Trash/*" | wc -l | tr -d ' ')
echo "  WAV files found locally (excl. Trash): $WAV_COUNT"
echo ""

# ── Method 1: az CLI (preferred — supports Shared Key directly) ──────────────
if command -v az &>/dev/null; then
  echo "[Method: az storage blob upload-batch]"
  az storage blob upload-batch \
    --account-name "$ACCOUNT" \
    --account-key "$AZURE_STORAGE_KEY" \
    --destination "$CONTAINER" \
    --destination-path "$DEST_PREFIX" \
    --source "$LOCAL_PART3" \
    --pattern "*.wav" \
    --overwrite false \
    --no-progress \
    --output table \
    2>&1 | tee "/tmp/five9_03_upload_$(date +%Y%m%d_%H%M%S).log"
  echo "Done. Check log in /tmp/five9_03_upload_*.log"
  exit 0
fi

# ── Method 2: azcopy with SAS token generated via Python ─────────────────────
if command -v azcopy &>/dev/null; then
  echo "[Method: azcopy with generated SAS token]"
  # Generate account SAS token valid for 48h using Python + Shared Key signing
  SAS=$(python3 - <<PYEOF
import base64, hashlib, hmac, datetime, urllib.parse

key = base64.b64decode("$AZURE_STORAGE_KEY")
account = "$ACCOUNT"
now = datetime.datetime.utcnow()
expiry = (now + datetime.timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
start = now.strftime("%Y-%m-%dT%H:%M:%SZ")

# Account SAS string-to-sign
# Format: account\nsp\nss\nst\nse\nsip\nspr\nsv\n
sp = "rwl"   # read, write, list
ss = "b"     # blob service
srt = "sco"  # service, container, object
sv = "2020-08-04"
spr = "https"

sts = "\n".join([account, sp, ss, srt, start, expiry, "", spr, sv, ""])
sig = base64.b64encode(hmac.new(key, sts.encode(), hashlib.sha256).digest()).decode()
params = {
    "sv": sv, "ss": ss, "srt": srt, "sp": sp,
    "st": start, "se": expiry, "spr": spr, "sig": sig
}
print(urllib.parse.urlencode(params))
PYEOF
  )

  DST_URL="https://$ACCOUNT.blob.core.windows.net/$CONTAINER/$DEST_PREFIX/?$SAS"
  SRC_PATH="$LOCAL_PART3"

  echo "  SAS generated (48h). Running azcopy..."
  azcopy copy \
    "$SRC_PATH" \
    "$DST_URL" \
    --recursive \
    --include-pattern "*.wav" \
    --overwrite false \
    --put-md5 \
    --log-level INFO \
    2>&1 | tee "/tmp/five9_03_azcopy_$(date +%Y%m%d_%H%M%S).log"
  echo "Done. Check log in /tmp/five9_03_azcopy_*.log"
  exit 0
fi

# ── Method 3: pure Python upload (slow but no extra deps) ───────────────────
echo "[Method: Python chunked upload — no az or azcopy found]"
echo "WARNING: This is slow (~1 file/sec). Install az CLI for 10x speed."
echo ""

python3 - "$LOCAL_PART3" "$CONTAINER" "$DEST_PREFIX" "$ACCOUNT" "$AZURE_STORAGE_KEY" <<'PYEOF'
import base64, hashlib, hmac, datetime, os, re, sys, time
import urllib.parse, requests

src_dir, container, prefix, account, key_b64 = sys.argv[1:]
key = base64.b64decode(key_b64)

def sign_put(url, headers, body_len):
    from urllib.parse import urlparse, parse_qs
    p = urlparse(url)
    ms = sorted((k.lower(), v.strip()) for k,v in headers.items() if k.lower().startswith("x-ms-"))
    ch = "".join(f"{k}:{v}\n" for k,v in ms)
    cr = f"/{account}{p.path}"
    qs = parse_qs(p.query, keep_blank_values=True)
    if qs:
        for qk in sorted(qs): cr += f"\n{qk}:{','.join(sorted(qs[qk]))}"
    sts = "\n".join(["PUT","","","application/octet-stream","",
                     "","","","","","",str(body_len)]) + "\n" + ch + cr
    sig = base64.b64encode(hmac.new(key, sts.encode(), hashlib.sha256).digest()).decode()
    return f"SharedKey {account}:{sig}"

uploaded = skipped = errors = 0
for root, dirs, files in os.walk(src_dir):
    # Skip .Trash
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    for fname in files:
        if not fname.lower().endswith('.wav'):
            continue
        local_path = os.path.join(root, fname)
        rel = os.path.relpath(local_path, src_dir)
        blob_name = f"{prefix}/{rel}"
        url = f"https://{account}.blob.core.windows.net/{container}/{urllib.parse.quote(blob_name)}"
        with open(local_path, 'rb') as f:
            data = f.read()
        now = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        h = {
            "x-ms-date": now,
            "x-ms-version": "2020-04-08",
            "x-ms-blob-type": "BlockBlob",
            "Content-Type": "application/octet-stream",
            "Content-Length": str(len(data)),
        }
        h["Authorization"] = sign_put(url, h, len(data))
        try:
            r = requests.put(url, headers=h, data=data, timeout=120)
            if r.status_code in (201, 409):
                uploaded += 1
            elif r.status_code == 409:
                skipped += 1  # already exists
            else:
                print(f"ERR {r.status_code}: {blob_name}", flush=True)
                errors += 1
        except Exception as e:
            print(f"EXC {blob_name}: {e}", flush=True)
            errors += 1
        if (uploaded + skipped + errors) % 1000 == 0:
            print(f"  Progress: uploaded={uploaded} skipped={skipped} errors={errors}", flush=True)

print(f"\nFinal: uploaded={uploaded} skipped={skipped} errors={errors}")
PYEOF
