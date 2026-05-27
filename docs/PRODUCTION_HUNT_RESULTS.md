# Production hunt results (executed 2026-05-27)

**Method:** 7 parallel `production_hunt_worker.py` jobs over full Alansinv (~10.37M rows) + merge.  
**PROD03:** Not uploaded — leads-only pass (`artifacts/catalog/hunt/prod03/`).

## Scoreboard

| Name | Feds declared | Have confirmed | % done | Potential locations |
|------|-------------:|---------------:|-------:|---------------------|
| **PROD01** RedmondTax 1–8835 | 8,835 | **0** distinct Bates | **0%** | Memorex (2,208 blobs); FED 2026 DISCO (372,369 paths); **538 zip** candidates → `prod01_zip_candidates.json` |
| **PROD02** RedmondTax 836–693308 | 692,473 | **2,085** distinct (**262,864** blob rows) | **0.3%** | Part A: 1,432 IDs · Part B: 653 IDs · Top: `organization`, `uploads`, `super-master-triage` |
| **PROD03** RedmondOvertActs 1–722 | 722 | **0** (not uploaded) | **0%** | Heim disc 3,175 paths; Heim delivery CSV ×7 → `prod03_upload_watchlist.csv` |
| **PROD04** FIVE9_02 | unknown | **152,139** distinct `AR-*` · **319,608** WAV blobs | **✅** | `prod04_five9_02_ar_ids.csv` · containers: `five9-calls`, `backups`, `onedrive-personal` |
| **PROD04** iPhone + Prod02_Confidential | 9,698 | **0** numbered · **390** unnumbered paths | **0%** | `prod04_iphone_unnumbered_paths.csv` · `03_HEIM DISK DISC` |
| **PROD05** FIVE9_03 | unknown | **152,139** distinct `AR-*` · **198,317** WAV blobs | **✅** | `prod05_five9_03_ar_ids.csv` |
| **PROD05** Prod03_Confidential (`deep_v4`) | 108,018 | **23,423** paths share `ar_id` token | **21.7%** | See caveat below · full index in repo |

**Total Bates deficit (PROD01–04):** **709,643**

---

## PROD03 alone (not uploaded)

| Item | Value |
|------|------:|
| OvertActs Bates in Azure | **0** |
| Heim disc path blobs | **3,175** |
| `DISCOVERY_PART_2_Heim_delivery.csv` copies | **7** |
| Status file | `artifacts/catalog/hunt/prod03/prod03_status.md` |

**Post-upload:** Re-run `python3 scripts/production_hunt_worker.py --mode prod03 --all-inventory --out artifacts/catalog/hunt/prod03`

---

## PROD02 split (agents 2 + 3)

| Range | Distinct IDs | Blob rows |
|-------|-------------:|----------:|
| 836 – 350,000 | 1,432 | 69,829 |
| 350,001 – 693,308 | 653 | 69,706 |
| **Merged** | **2,085** | **139,535** (shard subset; full inventory ~262,864) |

Missing ID list: union of `prod02a` + `prod02b` found CSVs → **690,388** not in Azure.

---

## PROD05 `deep_v4` join caveat

**21.77%** match means an `ar_id` from `prod_3/deep_v4.csv` appears in **some** Azure path (often **Five9 `AR-*` WAV**, not a confidential PDF native). **0** `Prod02_Confidential` / `Prod03_Confidential` path hits in inventory.

True confidential **native upload** coverage is still **~0%** until USB 3-part zip is expanded to blobs.

---

## Artifacts

```
artifacts/catalog/hunt/
├── prod01/   prod01_found_ids.csv, prod01_missing_ids.csv (8835 rows), prod01_zip_candidates.json
├── prod02a/  prod02_836-350000_found_ids.csv
├── prod02b/  prod02_350001-693308_found_ids.csv
├── prod03/   prod03_status.md, prod03_upload_watchlist.csv
├── prod04_five9/  prod04_five9_02_ar_ids.csv
├── prod04_docs/   prod04_iphone_unnumbered_paths.csv
├── prod05/   prod05_five9_03_ar_ids.csv, prod05_deep_v4_azure_join.csv
└── production_hunt_merged.json (via merge script)
```

**Re-run:** `bash scripts/run_production_hunt_parallel.sh`
