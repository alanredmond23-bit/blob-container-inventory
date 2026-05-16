# Azure blob dedup — AG-4 manifest merge

## Inputs

- **AG-2 path:** `artifacts/dedup/ag2` — no `delete_candidates.csv` present (or directory absent when merge ran).
- **AG-3 path:** `artifacts/dedup/ag3` — same.

## Merged output (PROVEN only)

| Metric | Value |
| --- | ---: |
| Delete candidate rows in master manifest | **0** |
| Total bytes reclaimable | **0** |
| `PROVEN_EXACT` | 0 |
| `PROVEN_EXACT_COMPUTED` | 0 |

## Files

- **`MASTER_DEDUP_MANIFEST.csv`:** not written — the merge script only emits this file when there is at least one qualifying row (`certainty` is `PROVEN_EXACT` or `PROVEN_EXACT_COMPUTED` after deduplication).
- **`SUMMARY.json` / `STATUS.json`:** written by AG-4 merge step with the counts above.

## Validation

- **Certainty:** No manifest rows to check. When a master CSV exists, every included row is restricted to `PROVEN_EXACT` or `PROVEN_EXACT_COMPUTED` by construction (non-matching certainties are dropped at merge time).

---

*No credentials or storage account names are recorded in this summary.*
