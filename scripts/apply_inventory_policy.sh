#!/usr/bin/env bash
# Apply blob inventory dedup rule (management plane — service principal or az login).
set -euo pipefail
: "${AZURE_RESOURCE_GROUP:?}"
: "${AZURE_STORAGE_ACCOUNT:?}"
: "${AZURE_SUBSCRIPTION_ID:?}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! az account show &>/dev/null; then
  if [[ -n "${AZURE_CLIENT_ID:-}" && -n "${AZURE_CLIENT_SECRET:-}" && -n "${AZURE_TENANT_ID:-}" ]]; then
    az login --service-principal -u "$AZURE_CLIENT_ID" -p "$AZURE_CLIENT_SECRET" --tenant "$AZURE_TENANT_ID" --only-show-errors
    az account set --subscription "$AZURE_SUBSCRIPTION_ID"
  else
    echo "Run: az login" >&2
    exit 1
  fi
fi

az extension add --name storage-preview -y 2>/dev/null || true

python3 << 'PY'
import json, os, subprocess
from pathlib import Path

rg, acct = os.environ["AZURE_RESOURCE_GROUP"], os.environ["AZURE_STORAGE_ACCOUNT"]
show = json.loads(subprocess.check_output([
    "az", "storage", "account", "blob-inventory-policy", "show",
    "-g", rg, "--account-name", acct, "-o", "json",
], text=True))
policy = show["policy"]
dedup_rule = json.loads(Path("Azure blob dedup/policies/blob-inventory-dedup.json").read_text())["rules"][0]
dedup_rule["definition"]["format"] = "Csv"
dedup_rule["definition"]["objectType"] = "Blob"
dedup_rule["definition"]["schedule"] = "Daily"
rules = [r for r in policy.get("rules", []) if r["name"] != "blob-inventory-dedup"]
rules.append(dedup_rule)
policy["rules"] = rules
policy["enabled"] = True
Path("artifacts/dedup/ag1/policy_body.json").write_text(json.dumps(policy, indent=2))
print("Rules:", [r["name"] for r in rules])
PY

az storage account blob-inventory-policy update \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --account-name "$AZURE_STORAGE_ACCOUNT" \
  --set "policy=@artifacts/dedup/ag1/policy_body.json"

echo "OK: blob-inventory-dedup rule active → container inventory-reports (daily CSV with Content-MD5)."
echo "First report typically within 24h. Then: python3 scripts/ag1_ensure_inventory_container.py"
