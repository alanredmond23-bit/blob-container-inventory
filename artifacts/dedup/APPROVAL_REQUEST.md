# Approval request — blob dedup (inventory merge)

**Status:** Ready for your approval. **No deletes executed.**

## Metrics

| Metric | Value |
|--------|------:|
| Delete rows | 56,422 |
| Bytes reclaimable | 991,373,320 (~945.4 MiB) |
| Certainty breakdown | `PROVEN_EXACT_COMPUTED`: 57, `PROVEN_EXACT_ETAG`: 56,365 |

## Sources merged

- `artifacts/dedup/ag2-live/shard_0/delete_candidates.csv`
- `artifacts/dedup/ag2-live/shard_1/delete_candidates.csv`
- `artifacts/dedup/ag3b/delete_candidates.csv`

## Approve

- [ ] **Execute deletes** from `artifacts/dedup/MASTER_DEDUP_MANIFEST.csv` (after spot-check below)

## Top containers (delete count)

- `backups`: 48,247 deletes
- `five9-calls`: 3,047 deletes
- `loose-files`: 1,482 deletes
- `organization`: 1,457 deletes
- `onedrive-personal`: 768 deletes
- `super-master-triage`: 352 deletes
- `legal`: 292 deletes
- `personal`: 218 deletes
- `1triageworkhorse`: 185 deletes
- `uploads`: 141 deletes

## Sample deletes (largest)

- **359,634,194 B** — delete `workhorse-docs/five9-calls/FIVE9_FLEET_SWEEP_2026-03-31/WORKHORSE/raw/filesystem-wav.txt` → keep `workhorse-docs/five9-calls/FIVE9_FLEET_SWEEP_2026-03-31/WORKHORSE/raw/filesystem-wav-nohup.txt`
- **9,987,515 B** — delete `organization/super-master-triage/workhorse-docs/Library/CloudStorage/OneDrive-Personal/01_LEG` → keep `organization/backups/onedrive-acct1/00_---- DOMAINS/01_LEGAL/LEGAL DOMAIN/07_PROTECT_ASSETS/2`
- **7,247,375 B** — delete `legal/legal-filings/quicks/LEGAL-MONOREPO/LEGAL-MONOREPO/groff-rush-malpractice/RUSH S` → keep `legal/legal-filings/quicks/LEGAL-MONOREPO/LEGAL-MONOREPO/groff-rush-malpractice/004-EV`
- **6,907,960 B** — delete `legal/legal-filings/quicks/LEGAL-MONOREPO/LEGAL-MONOREPO/groff-rush-malpractice/RUSH S` → keep `legal/legal-filings/quicks/LEGAL-MONOREPO/LEGAL-MONOREPO/groff-rush-malpractice/004-EV`
- **5,843,872 B** — delete `super-master-triage/uploads/Desktop/consolidated/Desktop - WORKHORSE-MBP/rush is a faggot/banks/GAVI` → keep `super-master-triage/uploads/Desktop/consolidated/Desktop - WORKHORSE-MBP/rush is a faggot/banks/GAVI`
- **5,002,231 B** — delete `backups/onedrive-acct1/onedrive-acct2/OneDrive-Personal(2)/MONEY VERTICALS/RESERVES GOT/` → keep `backups/onedrive-acct1/onedrive-acct2/OneDrive-Personal(2)/MONEY VERTICALS/RESERVES GOT/`
- **4,911,817 B** — delete `organization/45gb-final-onedrive/ORGANIZATION/rush_law_emails/attachments/77002_C1_Sharepoint` → keep `organization/45gb-final-onedrive/ORGANIZATION/rush_law_emails/attachments/77001_C1_Sharepoint`
- **4,669,920 B** — delete `legal/recordings/ALL_CALL_RECORDINGS/ALL_CALL_RECORDINGS/Lesley_Rudge/SALES_CALLS/Lesl` → keep `legal/recordings/ALL_CALL_RECORDINGS/ALL_CALL_RECORDINGS/Lesley_Rudge/SALES_CALLS/Lesl`
- **4,532,581 B** — delete `organization/backups/onedrive-acct1/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/fed t` → keep `organization/backups/onedrive-acct1/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/fed t`
- **4,364,289 B** — delete `backups/onedrive-acct1/onedrive-acct2/OneDrive-Personal(2)/LEGAL/BANKRUPTCY AND FORECLOS` → keep `backups/onedrive-acct1/onedrive-acct2/OneDrive-Personal(2)/LEGAL/BANKRUPTCY AND FORECLOS`
- **4,364,289 B** — delete `organization/super-master-triage/uploads/00_---- DOMAINS/BANKRUPTCY_DOCS_GATHERED/FROM_QUICKS` → keep `organization/super-master-triage/uploads/00_---- DOMAINS/BANKRUPTCY_DOCS_GATHERED/FROM_QUICKS`
- **4,364,289 B** — delete `organization/super-master-triage/uploads/00_---- DOMAINS/BANKRUPTCY_DOCS_GATHERED/FROM_QUICKS` → keep `organization/super-master-triage/uploads/00_---- DOMAINS/BANKRUPTCY_DOCS_GATHERED/FROM_QUICKS`
- **4,364,289 B** — delete `organization/super-master-triage/uploads/00_---- DOMAINS/BANKRUPTCY_DOCS_GATHERED/FROM_QUICKS` → keep `organization/super-master-triage/uploads/00_---- DOMAINS/BANKRUPTCY_DOCS_GATHERED/FROM_QUICKS`
- **4,364,289 B** — delete `organization/super-master-triage/uploads/00_---- DOMAINS/BANKRUPTCY_DOCS_GATHERED/FROM_QUICKS` → keep `organization/super-master-triage/uploads/00_---- DOMAINS/BANKRUPTCY_DOCS_GATHERED/FROM_QUICKS`
- **4,364,289 B** — delete `organization/super-master-triage/uploads/00_---- DOMAINS/BANKRUPTCY_DOCS_GATHERED/FROM_QUICKS` → keep `organization/super-master-triage/uploads/00_---- DOMAINS/BANKRUPTCY_DOCS_GATHERED/FROM_QUICKS`

## Notes

- Twilio account SID patterns (`AC[a-f0-9]{32}`) scrubbed from manifest lines.
- Inventory shards: `PROVEN_EXACT` (Content-MD5) and `PROVEN_EXACT_ETAG`.
- SDK scan (ag3b): `PROVEN_EXACT_COMPUTED` (SHA-256 verified).
