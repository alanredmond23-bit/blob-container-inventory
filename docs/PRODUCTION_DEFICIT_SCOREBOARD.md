# Production deficit scoreboard (repo-verified)

**Source:** Full scan of `artifacts/dedup/ag1/Alansinv_1000000_*.csv` (~10.37M rows) via `scripts/production_deficit_scan.py`.  
**Generated:** 2026-05-27. **No Everlaw API, no blacksand passphrase.**

## Total deficit (Bates-numbered productions)

| Metric | Count |
|--------|------:|
| Federal Bates declared (PROD01–04) | **711,728** |
| Distinct Bates confirmed in Azure | **2,085** |
| **Distinct Bates deficit** | **709,643** |
| PROD05 index rows (`prod_3/deep_v4.csv`) | **108,018 / 108,018** (0 deficit in repo) |

Five9 WAVs are **not** in the federal Bates table; see PROD04/05 Five9 rows below.

---

## Scoreboard (your column format)

| Name | Feds declared | Have confirmed | % done | Potential locations |
|------|-------------:|---------------:|-------:|---------------------|
| **PROD01** — RedmondTax 000001–008835 | 8,835 | **0** distinct IDs (0 blob rows in range) | **0%** | Memorex USB stubs (~2,208 blobs, mostly PROD02-range IDs); `FED FED 2026 FINAL DISCO` tree (~372k paths); **no `disco26/` container** in inventory |
| **PROD02** — RedmondTax 000836–693308 | 692,473 | **2,085** distinct IDs (**262,864** duplicate blob rows) | **0.3%** | `organization` (85,555 in-range blobs), `uploads` (82,985), `super-master-triage` (81,981), `discovery` (6,424), `backups` (5,091); Memorex `.txt` under `45gb-final-onedrive` / `backups` |
| **PROD03** — RedmondOvertActs 0001–0722 | 722 | **0** | **0%** | Heim disc paths (~3,143); `DISCOVERY_PART_2_Heim_delivery.csv` index copies; **no `RedmondOvertActs` filenames** in Azure |
| **PROD04** — FIVE9_02 WAVs | *(govt unknown)* | **319,608** tagged blobs; **152,136** distinct `AR-*` on WAVs | **✅ Azure-heavy** | `five9-calls`, `onedrive-personal`, `backups`, `organization`, `45gb-final-onedrive` |
| **PROD04** — Prod02_Confidential + RedmondiPhone 00001–09698 | 9,698 (iPhone) | **0** numbered iPhone; **~372** unnumbered iPhone paths | **0%** (numbered) | `organization/.../03_HEIM DISK DISC/Redmond Phone...`; blacksand EERM (offline) |
| **PROD05** — FIVE9_03 WAVs | *(govt unknown)* | **198,317** tagged blobs | **✅ Azure-heavy** | Same as FIVE9_02; ~153,776 `AR-*` IDs local-only per `repos/azure-blob-file-system/workhorse/FIVE9_COVERAGE.md` |
| **PROD05** — Prod03_Confidential docs | 108,018 (CSV index) | **108,018** rows in `prod_3/deep_v4.csv`; **0** confirmed as uploaded natives | **Index 100% / blobs 0%** | USB 3-part zip (not in Azure); ingest CSV to Supabase; `PROD03_folder_structure.csv` (894k files in zip layout) |

---

## Why “~84k PROD02” ≠ “2,085 PROD02”

- **84,490 / 85,555** = **blob rows** in `organization` (and mirrors) whose paths contain a `RedmondTax` ID in range 836–693308.
- **2,085** = **distinct Bates numbers** actually present (~126 blob copies per ID on average across containers).
- Federal gap is **690,388 missing distinct IDs**, not “608k missing from 84k.”

---

## Heat-seeking recipe (no blocked keys)

1. **Alansinv grep** — `rg 'RedmondTax|RedmondOvert|RedmondiPhone|FIVE9_0[23]|Memorex|HEIM DISC' artifacts/dedup/ag1/`
2. **Repo indexes** — `prod_3/deep_v4.csv`, `titles_v3.csv`, `pdf_classifications.csv`, `artifacts/INDEX.md`
3. **Blob inventory repo** — `repos/azure-blob-file-system/AZURE_BLOB_INVENTORY.md`, `workhorse/FIVE9_COVERAGE.md`
4. **Re-run scan** — `python3 scripts/production_deficit_scan.py` → `artifacts/catalog/production_deficit_scan.json`

---

## Next actions (highest yield)

| Priority | Action |
|----------|--------|
| 1 | Map **2,085** PROD02 IDs present → export missing ID list `836..693308 \ found` |
| 2 | Search **Heim disc** paths for OvertActs / iPhone under alternate naming |
| 3 | Reconcile **153,776** local-only Five9 `AR-*` vs Azure virtual-prefix trees |
| 4 | Upload / expand **Prod03_Confidential** zip; match `deep_v4` `ar_id` to blob paths |
| 5 | PROD01: expand Memorex + `FINAL FED PULL` zips; lowest RedmondTax in Azure is **≥10,304** (PROD02 range) |
