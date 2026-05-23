# AG-4 — Human approval request (no deletes performed)

**Date:** 2026-05-23  
**Manifest:** `artifacts/dedup/MASTER_DEDUP_MANIFEST.csv`  
**Action:** Review only — no blob deletes have been executed.

---

## Summary metrics

| Metric | Value |
|--------|------:|
| Total delete rows | 14,969 |
| Bytes reclaimable | 360,085,194 (~343.5 MiB) |

### Certainty breakdown

| Certainty | Rows |
|-----------|-----:|
| `PROVEN_EXACT` | 0 |
| `PROVEN_EXACT_COMPUTED` | 14,969 |

All rows are byte-identical duplicates verified by full SHA-256 hash (blobs ≤10 MB in size-collision groups). No `SUSPECT` rows are included.

---

## Coverage

| Scope | Blobs scanned | Containers |
|-------|--------------:|-----------:|
| SDK list + Content-MD5 / SHA-256 pass | 109,773 | 30 |
| Large containers (>50k blobs each) | Not scanned | 13 |

The master manifest covers duplicates found in **30 containers** totaling **109,773 blobs**. **13 large containers** still require Blob Inventory CSV export before dedup can run on them (`uploads`, `organization`, `onedrive-personal`, `backups`, `discovery`, `five9-calls`, `legal`, `legal-filings`, `45gb-final-onedrive`, `super-master-triage`, `personal`, `loose-files`, and others capped at 50,001+ blobs).

---

## Top 15 delete examples (by bytes)

Paths below are sanitized for review; no credentials or account keys are included.

| # | delete_container | delete_blob | keep_container | keep_blob | bytes |
|---|------------------|-------------|----------------|----------|------:|
| 1 | `save-money` | `financial-docs/onedrive2/.../processing_agreement/[REDACTED]@PH0PR17MB47.eml` | `financial-docs` | `onedrive2/.../processing_agreement/[REDACTED]@PH0PR17MB47.eml` | 10,304,840 |
| 2 | `save-money` | `financial-docs/onedrive2/.../processing_agreement/[REDACTED]@connect.xfinity.co.eml` | `financial-docs` | `onedrive2/.../processing_agreement/[REDACTED]@connect.xfinity.co.eml` | 10,295,086 |
| 3 | `save-money` | `financial-docs/onedrive2/.../processing_agreement/[REDACTED]@connect.xfinity.c.eml` | `financial-docs` | `onedrive2/.../processing_agreement/[REDACTED]@connect.xfinity.c.eml` | 10,293,925 |
| 4 | `save-money` | `financial-docs/onedrive2/.../CONTRACTS_EXTRACTED/Forte/20260210_201000_329873_12-16-24 - FL - Delivered Service of Process - ABN NETWORK LLC.pdf` | `financial-docs` | `onedrive2/.../CONTRACTS_EXTRACTED/Forte/20260210_201000_329873_12-16-24 - FL - Delivered Service of Process - ABN NETWORK LLC.pdf` | 9,893,312 |
| 5 | `financial-docs` | `onedrive2/.../acmltd105/wow_brand/[REDACTED]@PH0PR17MB44.eml` | `financial-docs` | `onedrive2/.../acmltd105/benefits_now/[REDACTED]@PH0PR17MB44.eml` | 9,739,813 |
| 6 | `save-money` | `financial-docs/onedrive2/.../acmltd105/benefits_now/[REDACTED]@PH0PR17MB44.eml` | `financial-docs` | `onedrive2/.../acmltd105/benefits_now/[REDACTED]@PH0PR17MB44.eml` | 9,739,813 |
| 7 | `save-money` | `financial-docs/onedrive2/.../acmltd105/wow_brand/[REDACTED]@PH0PR17MB44.eml` | `financial-docs` | `onedrive2/.../acmltd105/benefits_now/[REDACTED]@PH0PR17MB44.eml` | 9,739,813 |
| 8 | `financial-docs` | `onedrive2/.../[REDACTED]/merchant_industry/[REDACTED]@MW4PR17MB47.eml` | `financial-docs` | `onedrive2/.../[REDACTED]/benefits_now/[REDACTED]@MW4PR17MB47.eml` | 9,524,438 |
| 9 | `financial-docs` | `onedrive2/.../[REDACTED]/processing_agreement/[REDACTED]@MW4PR17MB47.eml` | `financial-docs` | `onedrive2/.../[REDACTED]/benefits_now/[REDACTED]@MW4PR17MB47.eml` | 9,524,438 |
| 10 | `save-money` | `financial-docs/onedrive2/.../[REDACTED]/benefits_now/[REDACTED]@MW4PR17MB47.eml` | `financial-docs` | `onedrive2/.../[REDACTED]/benefits_now/[REDACTED]@MW4PR17MB47.eml` | 9,524,438 |
| 11 | `save-money` | `financial-docs/onedrive2/.../[REDACTED]/merchant_industry/[REDACTED]@MW4PR17MB47.eml` | `financial-docs` | `onedrive2/.../[REDACTED]/benefits_now/[REDACTED]@MW4PR17MB47.eml` | 9,524,438 |
| 12 | `save-money` | `financial-docs/onedrive2/.../[REDACTED]/processing_agreement/[REDACTED]@MW4PR17MB47.eml` | `financial-docs` | `onedrive2/.../[REDACTED]/benefits_now/[REDACTED]@MW4PR17MB47.eml` | 9,524,438 |
| 13 | `save-money` | `financial-docs/onedrive2/.../[REDACTED]/benefits_now/[REDACTED]@Spark.eml` | `financial-docs` | `onedrive2/.../[REDACTED]/benefits_now/[REDACTED]@Spark.eml` | 9,379,501 |
| 14 | `save-money` | `financial-docs/onedrive2/.../acmltd105/benefits_now/[REDACTED].eml` | `financial-docs` | `onedrive2/.../acmltd105/benefits_now/[REDACTED].eml` | 8,718,157 |
| 15 | `financial-docs` | `onedrive2/.../acmltd105/benefits_now/[REDACTED].eml` | `financial-docs` | `onedrive2/.../acmltd105/MID_merchant/[REDACTED].eml` | 8,645,136 |

Full paths for all 14,969 rows are in `MASTER_DEDUP_MANIFEST.csv`.

---

## Approvals required

These are **separate** decisions. Checking one does not imply the other.

- [ ] **Approve PR #2 merge** — merge the index-repo consolidation PR (remove duplicate `repos/azure-blob-file-system/` folder; identical to `repos/FINALINDEX2027/`).
- [ ] **Approve blob deletes** — authorize execution against rows in `MASTER_DEDUP_MANIFEST.csv` only (14,969 proven duplicate blobs, ~343.5 MiB reclaimable in the scanned subset).

---

## Blocked: inventory policy (Portal only)

AG-1 cannot apply the Blob Inventory policy from this environment because the available storage credentials are **read/list only** (no write permission on `inventory-reports`). To unlock dedup on the 13 large containers, an operator with **Storage Account Contributor** (or equivalent write access) must apply the policy via **Azure Portal** (Storage account → Blob inventory → Add policy) or Azure CLI with an account key that can create inventory rules, following `artifacts/dedup/ag1/DEPLOY.md`. No other blockers apply to the current manifest; this step is required only for containers exceeding the 50k-blob SDK scan cap.

---

## Artifacts

| File | Purpose |
|------|---------|
| `MASTER_DEDUP_MANIFEST.csv` | Approved-delete list (PROVEN only) |
| `SUMMARY.json` | Machine-readable totals |
| `SUMMARY.md` | Human run summary |
| `STATUS.json` | Overseer agent status |
