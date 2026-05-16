# Azure blob dedup — run summary (2026-05-16)

## Coverage

| Scope | Blobs scanned | Method |
|-------|---------------|--------|
| 30 containers (≤50k blobs each) | 109,773 | SDK list + Content-MD5 grouping (AG-3) |
| 9 small containers (≤10MB hash pass) | 1,594 | SHA-256 on size-collision groups (AG-3b) |
| 13 large containers (>50k each) | Not scanned | **Requires Blob Inventory CSV** (AG-1 blocked on write key) |

Large containers skipped: `uploads`, `organization`, `onedrive-personal`, `backups`, `discovery`, `five9-calls`, `legal`, `legal-filings`, `45gb-final-onedrive`, `super-master-triage`, `personal`, `loose-files`, and others capped at 50,001+ blobs.

## Master manifest

| Metric | Value |
|--------|------:|
| Delete rows (`PROVEN_EXACT` + `PROVEN_EXACT_COMPUTED`) | See `SUMMARY.json` |
| Bytes reclaimable (scanned subset) | See `SUMMARY.json` |

Files:
- `MASTER_DEDUP_MANIFEST.csv` — human-approved deletes only
- `ag3b/delete_candidates.csv` — computed SHA-256 duplicates (small-container pass)
- `ag3b-full/` — full 30-container size-collision pass (may still be running)

## Certainty rules applied

- **PROVEN_EXACT:** same non-empty Content-MD5 and Content-Length (none found cross-container in AG-3 pass).
- **PROVEN_EXACT_COMPUTED:** full-byte SHA-256 match on blobs ≤10MB in size-collision groups.

No `SUSPECT` rows are included in the master manifest.

## AG-1 inventory

Apply policy per `artifacts/dedup/ag1/DEPLOY.md` using an account key or Portal with **write** permission. Current cloud agent key can **read/list** but not create `inventory-reports`.

## Repo duplicate (git)

Remove duplicate folder: `repos/azure-blob-file-system/` (identical to `repos/FINALINDEX2027/`).
