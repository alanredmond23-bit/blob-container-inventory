# Approval request — blob dedup (retry run)

**Status:** Ready for your approval. **No deletes executed.**

## Metrics

| Metric | Value |
|--------|------:|
| Delete rows | 14,953 |
| Bytes reclaimable | 360,064,034 (~343.4 MiB) |
| Certainty | 100% `PROVEN_EXACT_COMPUTED` (SHA-256) |
| Blobs scanned | 109,773 |
| Containers scanned | 30 (≤50k blobs each) |

## Approve

- [ ] **Merge PR #2** — https://github.com/alanredmond23-bit/blob-container-inventory/pull/2
- [ ] **Execute deletes** from `artifacts/dedup/MASTER_DEDUP_MANIFEST.csv` (after spot-check below)

## Top containers (delete count)

- `1triageworkhorse`: 5,032 deletes
- `workhorse-docs`: 3,108 deletes
- `fleet-sync`: 3,038 deletes
- `redmond-os`: 1,811 deletes
- `save-money`: 506 deletes
- `localtriage4162026admincomp`: 345 deletes
- `agent-outputs`: 240 deletes
- `financial-docs`: 153 deletes
- `program-files-hd`: 135 deletes
- `evidence-rush`: 109 deletes

## Sample deletes (largest)

- **10,304,840 B** — delete `save-money/financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESERVES_C...` → keep `financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESER...`
- **10,295,086 B** — delete `save-money/financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESERVES_C...` → keep `financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESER...`
- **10,293,925 B** — delete `save-money/financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESERVES_C...` → keep `financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESER...`
- **9,893,312 B** — delete `save-money/financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESERVES_C...` → keep `financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESER...`
- **9,739,813 B** — delete `financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESERVES_CALCULATION_2026...` → keep `financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESER...`
- **9,739,813 B** — delete `save-money/financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESERVES_C...` → keep `financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESER...`
- **9,739,813 B** — delete `save-money/financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESERVES_C...` → keep `financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESER...`
- **9,524,438 B** — delete `financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESERVES_CALCULATION_2026...` → keep `financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESER...`
- **9,524,438 B** — delete `financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESERVES_CALCULATION_2026...` → keep `financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESER...`
- **9,524,438 B** — delete `save-money/financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESERVES_C...` → keep `financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESER...`
- **9,524,438 B** — delete `save-money/financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESERVES_C...` → keep `financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESER...`
- **9,524,438 B** — delete `save-money/financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESERVES_C...` → keep `financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESER...`
- **9,379,501 B** — delete `save-money/financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESERVES_C...` → keep `financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESER...`
- **8,718,157 B** — delete `save-money/financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESERVES_C...` → keep `financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESER...`
- **8,645,136 B** — delete `financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESERVES_CALCULATION_2026...` → keep `financial-docs/onedrive2/MONEY VERTICALS/MONEY VERTICALS/RESERVES GOT/RESER...`

## AG-1 update (this retry)

- Created `inventory-reports` container successfully.
- Inventory **policy** not applied (no `az login` in agent). Run: `bash scripts/apply_inventory_policy.sh`

## Not in this manifest

13 containers with >50k blobs need inventory CSV after policy runs.
