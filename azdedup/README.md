# azdedup

Hyperscale incremental Azure Blob deduplication.

**Plan:** [`docs/AZDEDUP_IMPLEMENTATION_PLAN.md`](../docs/AZDEDUP_IMPLEMENTATION_PLAN.md)

## Status

| Phase | Status |
|-------|--------|
| 0 Scaffold | Done |
| **1 scan** | **Done** — inventory dry-run + apply-tags |
| 2 dedup partial/full | Planned |
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

## Tests

```bash
cd azdedup && python3 -m pytest -q
```

## Tag schema

`dedup_stage`, `size`, `ext`, `hash_fast`, `hash_full`, `canonical`, `canonical_id`, `dedup_etag`
