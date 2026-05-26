# azdedup

Hyperscale incremental Azure Blob deduplication.

**Plan:** [`docs/AZDEDUP_IMPLEMENTATION_PLAN.md`](../docs/AZDEDUP_IMPLEMENTATION_PLAN.md)

## Status

| Phase | Status |
|-------|--------|
| 0 Scaffold | Done |
| **1 scan** | **Done** |
| **2 dedup partial/full** | **Done** |
| 3 canonical/report/verify | Planned |
| 4 cleanup + sharding | Planned |

## Install

```bash
pip install -e azdedup/
azdedup --version
```

## Phase 1: `scan`

Metadata pass — **zero blob content reads**. Writes Index Tags (`dedup_stage=meta`, `size`, `ext`, `dedup_etag`) or dry-run JSONL.

```bash
# Dry-run from Alansinv inventory (default, safe)
azdedup scan --account "$AZURE_STORAGE_ACCOUNT" \
  --source inventory \
  --inventory-path 'artifacts/dedup/ag1/Alansinv_1000000_*.csv' \
  --dry-run-tags

# Apply tags to Azure (requires AZURE_STORAGE_KEY or MI)
azdedup scan --account "$AZURE_STORAGE_ACCOUNT" \
  --source inventory \
  --inventory-path 'artifacts/dedup/ag1/Alansinv_1000000_*.csv' \
  --apply-tags \
  --concurrency 64

# Live list (no inventory CSV)
azdedup scan --account "$AZURE_STORAGE_ACCOUNT" \
  --source live --containers discovery,legal --dry-run-tags
```

Outputs:

- Dry-run: `artifacts/dedup/azdedup/scan/meta_dry_run.jsonl`
- Apply-tags checkpoint: `artifacts/dedup/azdedup/checkpoints/scan_meta.jsonl`

Incremental: skips blobs where `dedup_etag` matches and stage ≥ `meta`. Use `--force` to re-tag.

## Phase 2: `dedup`

Partial xxhash (first/last `--read-bytes`) then full SHA-256 only on `(size, hash_fast)` collision groups.

```bash
# Partial hash dry-run (reads blob ranges only for listed inventory rows)
azdedup dedup --stage partial \
  --account "$AZURE_STORAGE_ACCOUNT" \
  --source inventory \
  --inventory-path 'artifacts/dedup/ag1/Alansinv_1000000_*.csv' \
  --read-bytes 1048576 \
  --dry-run-tags

# Apply partial tags to Azure
azdedup dedup --stage partial --account "$AZURE_STORAGE_ACCOUNT" \
  --source inventory --apply-tags --concurrency 32

# Full hash on collision groups only (requires hash_fast tags or prior partial pass)
azdedup dedup --stage full \
  --account "$AZURE_STORAGE_ACCOUNT" \
  --source inventory \
  --incremental \
  --dry-run-tags
```

Outputs:

- Partial dry-run: `artifacts/dedup/azdedup/dedup/partial_dry_run.jsonl`
- Full dry-run: `artifacts/dedup/azdedup/dedup/full_dry_run.jsonl`
- Checkpoints: `artifacts/dedup/azdedup/checkpoints/dedup_partial.jsonl`, `dedup_full.jsonl`

Inventory **Content-MD5** short-circuit: identical MD5 within a collision group skips full byte read (`hash_full` stored as `md5:<hex>`).

## Tests

```bash
cd azdedup && python3 -m pytest -q
```

## Tag schema

`dedup_stage`, `size`, `ext`, `hash_fast`, `hash_full`, `canonical`, `canonical_id`, `dedup_etag`
