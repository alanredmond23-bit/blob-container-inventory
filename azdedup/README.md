# azdedup

Hyperscale incremental Azure Blob deduplication.

**Implementation plan:** [`docs/AZDEDUP_IMPLEMENTATION_PLAN.md`](../docs/AZDEDUP_IMPLEMENTATION_PLAN.md)

## Status

Scaffold only — commands are stubs until Phase 0–1 land.

```bash
pip install -e .
azdedup --help
```

## Tag schema

See plan §4: `dedup_stage`, `size`, `ext`, `hash_fast`, `hash_full`, `canonical`, `canonical_id`, `dedup_etag`.
