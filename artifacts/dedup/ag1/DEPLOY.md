# AG-1 — Deploy blob inventory policy (`blob-inventory-dedup`)

Run from the repository root (`/workspace` or your clone). Set storage context once:

```bash
export AZURE_STORAGE_ACCOUNT="<your-storage-account-name>"
export AZURE_STORAGE_KEY="<your-account-key>"
```

Replace `<RESOURCE_GROUP>` with the storage account’s resource group.

The JSON template matches the inventory policy payload expected by `az storage account blob-inventory-policy create` (see [az storage account blob-inventory-policy](https://learn.microsoft.com/en-us/cli/azure/storage/account/blob-inventory-policy?view=azure-cli-latest)).

## 1. (Optional) Verify / install extension

Blob inventory policy CLI commands are in **preview**:

```bash
az extension add --name storage-preview --yes
```

## 2. Show current policy (if any)

```bash
az storage account blob-inventory-policy show \
  --resource-group "<RESOURCE_GROUP>" \
  --account-name "$AZURE_STORAGE_ACCOUNT"
```

## 3. Apply policy from `blob-inventory-dedup.json`

**Initial create** (use when no policy exists yet):

```bash
az storage account blob-inventory-policy create \
  --resource-group "<RESOURCE_GROUP>" \
  --account-name "$AZURE_STORAGE_ACCOUNT" \
  --policy @"Azure blob dedup/policies/blob-inventory-dedup.json"
```

If the CLI reports that a policy already exists, delete it first (destructive — confirm this is intended), then run `create` again:

```bash
az storage account blob-inventory-policy delete \
  --resource-group "<RESOURCE_GROUP>" \
  --account-name "$AZURE_STORAGE_ACCOUNT" \
  --yes

az storage account blob-inventory-policy create \
  --resource-group "<RESOURCE_GROUP>" \
  --account-name "$AZURE_STORAGE_ACCOUNT" \
  --policy @"Azure blob dedup/policies/blob-inventory-dedup.json"
```

## 4. Ensure destination container (inventory reports)

The rule writes to container `inventory-reports`. Create it if it does not exist (uses account key; omit `--account-key` if using `--auth-mode login` and RBAC):

```bash
az storage container create \
  --account-name "$AZURE_STORAGE_ACCOUNT" \
  --name "inventory-reports" \
  --account-key "$AZURE_STORAGE_KEY"
```

## 5. Re-download latest inventory (Python)

After the first scheduled run completes:

```bash
python3 scripts/ag1_ensure_inventory_container.py \
  --out-csv "artifacts/dedup/ag1/inventory_latest.csv" \
  --json-summary
```

(With `AZURE_STORAGE_ACCOUNT` set, `--account` can be omitted.)
