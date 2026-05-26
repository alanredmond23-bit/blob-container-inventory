# Discovery Log — Bates-to-Location Index
**Case:** U.S. v. Redmond et al., EDPA Dkt. No. 24-cr-375-JLS  
**Defense Counsel:** William Rush  
**Gov't Counsel:** AUSAs Mary Crawley and Samuel Dalke  
**Defendants:** (1) Alan Redmond, (2) Bene Market LLC, (3) Seguro Medico LLC  
**Generated:** 2026-05-26  
**Source of truth:** Azure `menageriesa36965` (Alansinv ~10.4M rows via dedup manifest + AZURE_BLOB_INVENTORY.md)  
**Priority order:** Azure → OneDrive → Google Drive → iCloud → Local

> **Note 1 (Gov't):** Many records were produced in native format without bates labels.  
> Examples: native Excel spreadsheets, native Five-9 sales recordings, Redmond's iPhone download, audio recordings.  
> **Note 2 (Gov't):** Protective Order issued June 2, 2025 (ECF No. 82). Discovery materials for defense counsel + defendants only.

---

## Production 1
| Field | Value |
|---|---|
| **Production #** | 1 |
| **Date** | 10/31/24 |
| **Method** | USAfx Fileshare |
| **Bates Range** | `RedmondTax000001` – `RedmondTax008835` |
| **Gov't Description** | Dept. of Labor Civil Wage Litigation Folder; Redmond Interview Folder; Grand Jury Exhibit Folder; Guaranteed Payments Folder; IRS Folder; Grand Jury Interviews; Other Files (Redmond Criminal History); Indictment; ACA article; release conditions |

### File Locations

| Priority | Storage | Container / Drive | Path | Notes |
|---|---|---|---|---|
| 1 | **Azure** | `organization` | `super-master-triage/uploads/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/fed teddies/Fed drive/NATIVES/0001/RedmondTax{000001–008835}.*` | Native-format files; no individual bates stamp on filename |
| 1 | **Azure** | `organization` | `backups/onedrive-acct1/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/fed teddies/RedmondTax{######}.*` | Backup copy; confirmed via manifest |
| 1 | **Azure** | `uploads` | `Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/fed teddies/Fed drive/RedmondTax{######}.*` | Mirror in `uploads` container |
| 2 | **OneDrive** | OneDrive-Personal | `01_LEGAL/LEGAL DOMAIN/` → synced to Azure `onedrive-personal/01_LEGAL/01_LEGAL/` | 941,618 blobs in `01_LEGAL` tree |
| 3 | **Google Drive** | alanredmond23@gmail.com | `FED FED 2026 FINAL DISCO/NEW ALAN FEDS/fed teddies/` | Source of Azure mirror |
| — | — | — | — | Bates range 000001–008835 not observed as duplicates in manifest; files are present but unique in this range |

---

## Production 2
| Field | Value |
|---|---|
| **Production #** | 2 |
| **Date** | 01/16/25 |
| **Method** | Flash Drive via FedEx |
| **Bates Range** | `RedmondTax000836` – `RedmondTax693308` |
| **Gov't Description** | Grand Jury Subpoena Returns including from financial institutions, Grand Jury Subpoena Returns, including from financial institutions, Seguro Medico, John Sardella, C. Malcolm Smith, Stephanie Miller, Sharer Petree, Mark Poserina |

### File Locations

| Priority | Storage | Container / Drive | Path | Notes |
|---|---|---|---|---|
| 1 | **Azure** | `organization` | `backups/onedrive-acct1/Google Drive/DAVID HEIM DISC/1. Discovery_Docket/00 Raw discovery/01_SMALL DISK DISC/DISC_2_2025/FILES/TEXT/0001/RedmondTax{######}.txt` | Confirmed in manifest; text versions of bates docs |
| 1 | **Azure** | `organization` | `super-master-triage/uploads/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/fed teddies/Fed drive/NATIVES/0001/RedmondTax{######}.xlsm` | Native Excel (confirmed: `RedmondTax171689.xlsm`) |
| 1 | **Azure** | `organization` | `super-master-triage/uploads/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/feds 2025-01/NATIVES/0003/RedmondTax{######}.*` | feds 2025-01 batch |
| 1 | **Azure** | `organization` | `super-master-triage/uploads/google-drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/FINAL FED FUCK YOU copy/Stephanie_Miller/FINAL FED FUCK YOU /…/NATIVES/0003/RedmondTax{######}.*` | Stephanie Miller subpoena return files |
| 1 | **Azure** | `organization` | `super-master-triage/uploads/Imports/alanredmond23@gmail.com - Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/fed teddies/Fed drive/RedmondTax{######}.*` | Gmail import mirror |
| 1 | **Azure** | `backups` | `onedrive-acct1/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/fed teddies/Fed drive/NATIVES/0001/RedmondTax{######}.*` | Backup copy (confirmed: `RedmondTax171689.xlsm`) |
| 1 | **Azure** | `backups` | `onedrive-acct1/onedrive-acct2/OneDrive-Personal(2)/LEGAL/BANKRUPTCY AND FORECLOSURE/_archive/BANKRUPTCY_DOCS_GATHERED/FROM_ADMIN/Users/alanredmond/mcswain_analysis/Fed drive/Memorex USB/TEXT/0020/RedmondTax{######}.txt` | Memorex USB physical media copy |
| 1 | **Azure** | `backups` | `onedrive-acct1/onedrive-acct2/…/mcswain_analysis/office only!/Memorex USB/TEXT/0020–0024/RedmondTax{######}.txt` | Office copy of Memorex USB (TEXT 0020, 0022, 0024 batches) |
| 1 | **Azure** | `backups` | `onedrive-acct1/onedrive-acct2/…/mega_pull/MASTER OF ALL/Google Workspace/All teddie files/RedmondTax{######}.jpg` | Image scans (confirmed: `RedmondTax013502.jpg`) |
| 1 | **Azure** | `uploads` | `Google Drive/DAVID HEIM DISC/1. Discovery_Docket/00 Raw discovery/01_SMALL DISK DISC/DISC_2_2025/FILES/TEXT/0001/RedmondTax{######}.txt` | DAVID HEIM DISC upload |
| 1 | **Azure** | `uploads` | `Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/fed teddies/Fed drive/RedmondTax{######}.*` | |
| 1 | **Azure** | `uploads` | `00_---- DOMAINS/BANKRUPTCY_DOCS_GATHERED/FROM_ADMIN/Users/alanredmond/mcswain_analysis/Fed drive/Memorex USB/TEXT/0021–0030/RedmondTax{######}.txt` | Memorex USB batches 0021, 0030 |
| 1 | **Azure** | `uploads` | `Imports/alanredmond23@gmail.com - Google Drive/DAVID HEIM DISC/1. Discovery_Docket/00 Raw discovery/01_SMALL DISK DISC/DISC_2_2025/FILES/TEXT/0001/RedmondTax{######}.txt` | Gmail-import version |
| 2 | **OneDrive** | OneDrive-Personal | `01_LEGAL/LEGAL DOMAIN/FULL EXTRACTIONS/` → Azure `onedrive-personal/01_LEGAL/01_LEGAL/LEGAL DOMAIN/` | Full extraction tree |
| 3 | **Google Drive** | alanredmond23@gmail.com | `FED FED 2026 FINAL DISCO/NEW ALAN FEDS/` + `DAVID HEIM DISC/` | Original source |
| — | **Bates range note** | Confirmed manifest range | `RedmondTax008836` (low) → `RedmondTax687555` (high) seen in manifest | Higher bates (687556–693308) are in Azure but not caught as duplicates |

---

## Production 3
| Field | Value |
|---|---|
| **Production #** | 3 |
| **Date** | 07/18/25 |
| **Method** | USAfx Fileshare |
| **Bates Range** | `RedmondOvertActs0001` – `RedmondOvertActs0722` |
| **Gov't Description** | Records supporting the Overt Acts in the Superseding Indictment; Interviews and Transcripts with Redmond; Redmond's criminal history; Search Warrant Affidavit and related documents from searches of Seguro Medico and Redmond's cell phone |

### File Locations

| Priority | Storage | Container / Drive | Path | Notes |
|---|---|---|---|---|
| 1 | **Azure** | `evidence-federal` | `final-FBI-defensive-DOJ-strategy/` (73 blobs) | FBI / DOJ overt acts materials; 4 sub-parts |
| 1 | **Azure** | `evidence-federal` | `analysis/` (23 blobs) | Supporting analysis: actors, carriers, financial, intel, legal, tools-api |
| 1 | **Azure** | `evidence-federal` | `redmond-defense-artifacts/` (17 blobs) | Defense artifacts from federal discovery |
| 1 | **Azure** | `evidence-federal` | `redmond-defense-transcripts/` (7 blobs) | Interview transcripts |
| 1 | **Azure** | `evidence-federal` | `operation-freedom/assets/` (13 blobs) | Search warrant related |
| 1 | **Azure** | `evidence-federal` | `legal/CASES/` (81 blobs) + `legal/GLOBAL/` (24 blobs) | Case law / legal research |
| 1 | **Azure** | `onedrive-personal` | `01_LEGAL/SUPERSEDWINSTARTS/` (178 blobs) | Superseding Indictment starts — directly named for this production |
| 1 | **Azure** | `legal` | `evidence-federal/` (243 blobs total) | Mirror of `evidence-federal` container within `legal` |
| 2 | **OneDrive** | OneDrive-Personal | `01_LEGAL/SUPERSEDWINSTARTS/` | Source for Azure mirror |
| — | — | — | — | `RedmondOvertActs` bates prefix not seen in manifest as duplicates — files are present but unique (small set, 722 docs) |

---

## Production 4
| Field | Value |
|---|---|
| **Production #** | 4 |
| **Date** | 09/29/25 |
| **Method** | Hard Drive, delivered in person |
| **Bates Range** | `Prod02_Confidential_000000001` – `Prod02_Confidential_000991938` and `RedmondiPhone_00001` – `RedmondiPhone_09698` |
| **Gov't Description** | Records from awalsh413@aol.com account; Records from QPH1 HP Notebook computer; Records from Five-9 (over 1.1 million recorded audio calls, with Cellebrite reader); Redmond's iPhone (with Cellebrite reader) |

### 4a — Five-9 Call Recordings (`FIVE9_02_CONFIDENTIAL_AR-*`)

The `Prod02_Confidential` bates prefix is encoded directly into the filename as `FIVE9_02_CONFIDENTIAL_AR-{NNNNNNN}`. Files are `.wav` audio.

| Priority | Storage | Container / Drive | Path | Blobs |
|---|---|---|---|---|
| 1 | **Azure** | `five9-calls` | `FIVE9_02_folder/FIVE9_02_CONFIDENTIAL_AR-{NNNNNNN}.wav` | 57,562 |
| 1 | **Azure** | `five9-calls` | `trash-series02/.Trash/FIVE9_02_CONFIDENTIAL_AR-{NNNNNNN}.wav` | ~9,102 in trash |
| 1 | **Azure** | `legal` | `recordings/00_---- DOMAINS/01_LEGAL/FULL EXTRACTIONS/2. FULL EXTRACTION CALL PART 2/{batch}/FIVE9_02_CONFIDENTIAL_AR-{NNNNNNN}.wav` | Part of 401,167 total |
| 1 | **Azure** | `legal` | `recordings/ALL_CALL_RECORDINGS/ALL_CALL_RECORDINGS/{Agent}/SALES_CALLS/{Agent}_CALLID{########}_FIVE9_01_CONFIDENTIAL_AR-{NNNNNNN}_P1.wav` | Seguro Medico agent sales calls |
| 1 | **Azure** | `backups` | `onedrive-acct1/FIVE9_02_CONFIDENTIAL_AR-0000132430 7.wav/01_LEGAL/FULL EXTRACTIONS/FIVE9_ 06_CONFIDENTIAL_AR/FIVE9-06 Alan Redmond/IMAGES/0001/FIVE9_06_CONFIDENTIAL_AR-{NNNNNNN}.tif` | Cellebrite UFED forensic image tiles |
| 1 | **Azure** | `organization` | `super-master-triage/uploads/FIVE9_02_CONFIDENTIAL_AR-0000132430 7.wav/01_LEGAL/FULL EXTRACTIONS/FIVE9_ 06_CONFIDENTIAL_AR/…` | Duplicate of Cellebrite extract |
| 2 | **OneDrive** | OneDrive-Personal | `01_LEGAL/LEGAL DOMAIN/FULL EXTRACTIONS/` → Azure `onedrive-personal/OneDrive-Personal/FIVE9_02_CONFIDENTIAL_AR-0000132430 7.wav/` | 57,426 blobs |
| — | **Coverage note** | — | 250,000 distinct AR-IDs local; 96,224 in Azure `five9-calls`; **153,776 AR-IDs local-only** (FIVE9_03 series) | Run `repos/FINALINDEX2027/five9_coverage.py` |

#### Five-9 Series Key
| Series prefix | Production | Location |
|---|---|---|
| `FIVE9_01_CONFIDENTIAL_AR-*` | (Pre-indictment sales calls) | `legal/recordings/ALL_CALL_RECORDINGS/` + `onedrive-personal/.../FULL EXTRACTIONS/1. FULL EXTRACTION OF CALL PART 1/` |
| `FIVE9_02_CONFIDENTIAL_AR-*` | **Production 4** (`Prod02_Confidential`) | `five9-calls/FIVE9_02_folder/` (primary) |
| `FIVE9_03_CONFIDENTIAL_AR-*` | **Production 5** (`Prod03_Confidential`) | `five9-calls/trash-series03/.Trash/` + local only |
| `FIVE9_04_CONFIDENTIAL_AR-*` | (Part of Prod02 extraction set) | `legal/recordings/.../2. FULL EXTRACTION CALL PART 2/` |
| `FIVE9_05_CONFIDENTIAL_AR-*` | (Part of Prod02 extraction set) | `legal/recordings/.../2. FULL EXTRACTION CALL PART 2/` |
| `FIVE9_06_CONFIDENTIAL_AR-*` | (Cellebrite phone extraction frames) | `backups/onedrive-acct1/FIVE9_02_CONFIDENTIAL_AR-0000132430 7.wav/01_LEGAL/FULL EXTRACTIONS/FIVE9_ 06_CONFIDENTIAL_AR/FIVE9-06 Alan Redmond/IMAGES/` |

### 4b — awalsh413@aol.com Account Records

| Priority | Storage | Container / Drive | Path | Blobs |
|---|---|---|---|---|
| 1 | **Azure** | `backups` | `onedrive-acct1/` (top-level sync of this account) | 160,425 |
| 1 | **Azure** | `backups` | `onedrive-acct1/onedrive-acct2/` (nested secondary account) | 131,352 sub-blobs |
| 1 | **Azure** | `backups` | `onedrive-acct1/Google Drive/` | 10,748 |
| 2 | **OneDrive** | awalsh413@aol.com account | Root → mirrored to `backups/onedrive-acct1/` | Source |

### 4c — QPH1 HP Notebook

| Priority | Storage | Container / Drive | Path | Blobs |
|---|---|---|---|---|
| 1 | **Azure** | `backups` | `admin-2026-04-17/` | 15,230 |
| 1 | **Azure** | `backups` | `admin-2026-04-17/Supabase-S3/` | 5,159 |
| 1 | **Azure** | `backups` | `admin-2026-04-17/githubrepos/` | 1,603 |
| 1 | **Azure** | `backups` | `admin-2026-04-17/FBI (master)/` | 3 |
| 1 | **Azure** | `backups` | `ai-data-admin-2026-04-17/` (AI tool session data from notebook) | 153,802 |

### 4d — Redmond iPhone (Cellebrite) — `RedmondiPhone_00001–09698`

| Priority | Storage | Container / Drive | Path | Notes |
|---|---|---|---|---|
| 1 | **Azure** | `backups` | `admin-2026-04-17/rclone-staging/iphone_forensic_20250821T052231Z/run.log` | Confirmed in manifest; iPhone forensic extraction dated 2025-08-21 |
| 1 | **Azure** | `backups` | `onedrive-acct1/FIVE9_02_CONFIDENTIAL_AR-0000132430 7.wav/01_LEGAL/FULL EXTRACTIONS/FIVE9_ 06_CONFIDENTIAL_AR/FIVE9-06 Alan Redmond/IMAGES/0001/FIVE9_06_CONFIDENTIAL_AR-{NNNNNNN}.tif` | Cellebrite UFED physical image (.tif) tiles; `FIVE9-06 Alan Redmond` = phone extraction package |
| 1 | **Azure** | `onedrive-personal` | `01_LEGAL/REDMOND_TRIAL/` (5,683 blobs) | Trial-prep iPhone exhibit copies |
| 2 | **OneDrive** | OneDrive-Personal | `01_LEGAL/REDMOND_TRIAL/` | Source |
| — | — | — | `RedmondiPhone` bates prefix not seen as filename prefix in manifest; physical device extraction stored as Cellebrite image tiles | |

---

## Production 5
| Field | Value |
|---|---|
| **Production #** | 5 |
| **Date** | 03/23/26 |
| **Method** | Flash Drive, delivered in person |
| **Bates Range** | `Prod03_Confidential_000000001` – `Prod03_Confidential_000677497` |
| **Gov't Description** | FBI casefile serials and attachments, to include interview reports; Selected Records pulled from Redmond's iPhone; Grand Jury Exhibits; Scans of Materials Recovered from Seguro Medico; Additional Grand Jury Subpoena Returns; Medico Search Warrant; including from financial institutions and other businesses |

### 5a — Five-9 Recordings (`FIVE9_03_CONFIDENTIAL_AR-*`)

`Prod03_Confidential` bates prefix encoded as `FIVE9_03_CONFIDENTIAL_AR-{NNNNNNN}`.

| Priority | Storage | Container / Drive | Path | Blobs |
|---|---|---|---|---|
| 1 | **Azure** | `five9-calls` | `trash-series03/.Trash/FIVE9_03_CONFIDENTIAL_AR-{NNNNNNN}.wav` | 72,212 |
| 2 | **OneDrive** | OneDrive-Personal | `01_LEGAL/LEGAL DOMAIN/FULL EXTRACTIONS/3. FULL EXTRACTION CALL PART 3/NATIVES/0001/FIVE9_03_CONFIDENTIAL_AR-{NNNNNNN}.wav` → Azure `onedrive-personal/01_LEGAL/01_LEGAL/LEGAL DOMAIN/FULL EXTRACTIONS/3. FULL EXTRACTION CALL PART 3/` | **153,776 AR-IDs local-only** — not fully uploaded to Azure |
| — | **Gap alert** | — | 153,776 FIVE9_03 AR-IDs confirmed local, not in `five9-calls` Azure container | Upload via `scripts/download_alansinv_inventory.sh` + re-run Five9 coverage |

### 5b — FBI Casefile Materials

| Priority | Storage | Container / Drive | Path | Blobs |
|---|---|---|---|---|
| 1 | **Azure** | `backups` | `admin-2026-04-17/FBI (master)/` | 3 |
| 1 | **Azure** | `evidence-federal` | `final-FBI-defensive-DOJ-strategy/` (73 blobs, 4 sub-parts + REDMOND_DOCTRINE_v1) | |
| 1 | **Azure** | `evidence-federal` | `redmond-defense-artifacts/` (17 blobs) | |

### 5c — Grand Jury Exhibits + Subpoena Returns

| Priority | Storage | Container / Drive | Path | Blobs |
|---|---|---|---|---|
| 1 | **Azure** | `onedrive-personal` | `01_LEGAL/REDMOND_TRIAL/` (5,683 blobs) | GJ exhibit copies |
| 1 | **Azure** | `discovery` | `EVIDENCE_PULL_ROOT/EVIDENCE_PULL/` (6,961 blobs) | GJ subpoena returns — financial institutions |
| 1 | **Azure** | `discovery` | `EVIDENCE_PULL_LEGAL/EVIDENCE_PULL/` (1,720 blobs) | Additional legal subpoena returns |
| 1 | **Azure** | `legal` | `discovery/EVIDENCE_PULL_ROOT/` + `discovery/EVIDENCE_PULL_LEGAL/` | Mirror under `legal` container |
| 1 | **Azure** | `organization` | `super-master-triage/uploads/google-drive/FED FED 2026 FINAL DISCO/FINAL FED FUCK YOU/Stephanie_Miller/…/NATIVES/0003/RedmondTax{######}.*` | Stephanie Miller GJ subpoena materials |

### 5d — Seguro Medico Scans + Search Warrant

| Priority | Storage | Container / Drive | Path | Blobs |
|---|---|---|---|---|
| 1 | **Azure** | `evidence-federal` | `analysis/evidence/` + `analysis/financial/` | Seguro Medico analysis |
| 1 | **Azure** | `discovery` | `EVIDENCE_PULL_ROOT/EVIDENCE_PULL/` (6,961 blobs) | Seguro Medico scans included here |
| 1 | **Azure** | `legal-filings` | `RUSH_SANCTIONS/RUSH SANCTIONS:MOTION EXEMPTIONS/` (8,004 blobs) | Medico-related motion filings |

### 5e — iPhone Records (selected)

| Priority | Storage | Container / Drive | Path | Notes |
|---|---|---|---|---|
| 1 | **Azure** | `backups` | `admin-2026-04-17/rclone-staging/iphone_forensic_20250821T052231Z/` | Confirmed rclone iPhone forensic extraction |
| 1 | **Azure** | `onedrive-personal` | `01_LEGAL/REDMOND_TRIAL/` (5,683 blobs) | Selected iPhone records in trial folder |

---

## Cross-Production Container Summary

| Azure Container | Blobs | Primary Bates Coverage |
|---|---|---|
| `five9-calls` | 165,674 | Prod02 (02_CONFIDENTIAL) + Prod03 trash + Staging |
| `legal` | 697,763 | All productions (recordings + discovery + filings) |
| `legal/recordings` sub-path | 401,167 | Prod02/Prod01 Five-9 audio (full extraction sets) |
| `legal/discovery` sub-path | 189,664 | Prod02/Prod05 GJ subpoena returns |
| `legal/legal-filings` sub-path | 93,768 | Prod03/Prod05 legal filings |
| `legal/evidence-federal` sub-path | 243 | Prod03 overt acts + FBI materials |
| `discovery` | 189,664 | Prod02/Prod05 GJ subpoena returns |
| `evidence-federal` | 243 | Prod03 overt acts |
| `onedrive-personal` | 2,314,019 | All productions (01_LEGAL tree) |
| `onedrive-personal/01_LEGAL` | 941,618 | All productions |
| `onedrive-personal/01_LEGAL/REDMOND_TRIAL` | 5,683 | Prod04+Prod05 iPhone + GJ exhibits |
| `onedrive-personal/01_LEGAL/SUPERSEDWINSTARTS` | 178 | Prod03 overt acts |
| `backups` | 509,642 | Prod04 (awalsh413, QPH1, iPhone forensic) |
| `backups/onedrive-acct1` | 160,425 | Prod04 awalsh413@aol.com |
| `backups/admin-2026-04-17` | 15,230 | Prod04 QPH1 HP notebook |
| `backups/ai-data-admin-2026-04-17` | 153,802 | Prod04 QPH1 AI session data |
| `organization` | 1,377,551 | Prod01/Prod02 (super-master-triage uploads + Google Drive) |
| `organization/super-master-triage/uploads` | 186,803 | Prod01/Prod02 Google Drive imports |
| `uploads` | (in super-master-triage) | Prod01/Prod02 Google Drive |
| `financial-docs` | 3,496 | Prod02 financial institution returns |

---

## Known Gaps / Action Items

| Gap | Detail | Resolution |
|---|---|---|
| **FIVE9_03 upload incomplete** | 153,776 AR-IDs in local OneDrive, only 72,212 in Azure `five9-calls/trash-series03/` | Upload from `onedrive-personal/.../FULL EXTRACTIONS/3. FULL EXTRACTION CALL PART 3/` |
| **Alansinv CSV not in repo** | ~10.4M-row CSV is Git LFS pointer; requires Azure credentials to download | Run `scripts/download_alansinv_inventory.sh` with `AZURE_STORAGE_ACCOUNT` + `AZURE_STORAGE_KEY` |
| **Prod01 bates 000001–008835 not in dedup manifest** | These files appear unique (no duplicates); present in Azure but not surfaced in manifest | Re-run `azdedup scan` on `discovery` + `uploads` containers targeting `RedmondTax0000[01-8]` range |
| **RedmondOvertActs not in manifest** | Only 722 documents; too small to have duplicates caught in dedup scan | Directly in `evidence-federal` container; verify via `az storage blob list --container evidence-federal --prefix ""` |
| **RedmondiPhone bates prefix** | Filename prefix `RedmondiPhone_*` not observed in manifest | Files stored as Cellebrite UFED image tiles (`FIVE9_06_CONFIDENTIAL_AR-*.tif`) not by iPhone bates name |
| **iCloud not yet indexed** | `icloud-archive` container has 48,873 blobs (`iCloud Drive (Archive)/`) — not mapped to productions yet | Run inventory against `organization/icloud-archive/` |
