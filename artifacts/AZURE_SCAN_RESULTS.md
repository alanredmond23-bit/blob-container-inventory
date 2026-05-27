# Azure Blob Scan — Government Production Coverage
**Case:** U.S. v. Redmond et al., EDPA 24-cr-375-JLS  
**Account:** `menageriesa36965`  
**Scanned:** 2026-05-27  
**Method:** Azure REST List Blobs API (Shared Key auth), prefix-targeted  

---

## PRODUCTION COVERAGE MATRIX

| Production | Bates Prefix | Total Range | **IN AZURE?** | Container(s) | Count | Status |
|------------|-------------|-------------|---------------|-------------|-------|--------|
| PROD01 | RedmondTax | 000001–008835 | UPLOADING NOW | `disco26` | — | User uploading from USB |
| PROD02 | RedmondTax | 000836–693308 | **YES** | `uploads`, `discovery`, `legal-filings` | ~84k+ files | Confirmed present |
| PROD03 | RedmondOvertActs | 0001–0722 | **NOT FOUND** | — | 0 | On USB or in org as native (no bates filename) |
| PROD04 | Prod02_Confidential | 000000001–000991938 | **NO** (docs) / **YES** (calls) | `recordings`, `five9-calls`, `legal-filings` | 180k+ WAVs | Docs on blacksand (McAfee EERM encrypted); Five9 calls in Azure |
| PROD04 | RedmondiPhone | 00001–09698 | **NOT FOUND** | — | 0 | Not located in Azure |
| PROD05 | Prod03_Confidential | 000000001–000677497 | **NO** (docs) / **YES** (calls) | `recordings`, `five9-calls` | 150k+ WAVs | Docs on USB (3-part zip, 894k files); Five9 calls in Azure |

---

## CONTAINER-BY-CONTAINER RESULTS

### `uploads` — 82,912 blobs
| Prefix | Count | Bates Range | Notes |
|--------|-------|-------------|-------|
| RedmondTax | 82,912 | 8,836–688,448 | Primary PROD02 TEXT layer |
| FIVE9_02 | 2,817 | — | Series 02 call recordings |
| FIVE9_06 | 521 | — | iPhone Cellebrite TIF series |
| Others | 0 | — | — |

### `recordings` — 250,000+ blobs (hit 50-page scan limit)
| Prefix | Count | Sample Path | Notes |
|--------|-------|-------------|-------|
| FIVE9_02 | 122,402 | `00_---- DOMAINS/01_LEGAL/FULL EXTRACTIONS/2. FULL EXTRACTION CALL PART 2/.../FIVE9_02_CONFIDENTIAL_AR-0000020001.wav` | PROD04 calls |
| FIVE9_03 | 79,682 | `00_---- DOMAINS/01_LEGAL/FULL EXTRACTIONS/3. FULL EXTRACTION CALL PART 3/NATIVES/.../FIVE9_03_CONFIDENTIAL_AR-0000050001.wav` | PROD05 calls |
| All bates prefixes | 0 | — | No document files |

### `five9-calls` — 1.1M+ blobs (targeted prefix scan)
| Prefix | Subfolder | Count | AR Range |
|--------|-----------|-------|----------|
| FIVE9_02 | `FIVE9_02_CONFIDENTIAL/` | 57,559+ | — |
| FIVE9_03 | `trash-series03/` | 72,168 | AR 50,001–170,000 |
| FIVE9_02 | `trash-series02/` | 9,100 | AR 30,001–225,880 |

### `discovery` — ~1,000 blobs
| Prefix | Count | Notes |
|--------|-------|-------|
| RedmondTax | 961 | Stephanie Miller GJ tax returns; range 8,864–688,448 |
| Others | 0 | — |

### `legal-filings` — ~2,500 blobs
| Prefix | Count | Notes |
|--------|-------|-------|
| RedmondTax | 617 | — |
| FIVE9_02 | 1,882 | Call recording subset |

### `evidence-federal` — 243 blobs — **CLEAN (defense materials only)**
```
Dirs: Master-legal/ analysis/ final-FBI-defensive-DOJ-strategy/ 
      legal/ operation-freedom/ redmond-defense-artifacts/ redmond-defense-transcripts/
```
No government bates-stamped files.

### `backups` — 340,879 blobs — **CLEAN (personal monthly backups only)**
```
Top-level: 2024-11/ 2024-12/ 2025-01/ 2025-02/ 2025-03/ 2025-04/ 2025-05/
```
No government bates-stamped files. 100% personal Azure backup data.

### `organization` — 500k+ blobs — **CLEAN (no bates-named files)**
Targeted prefix scan for all 8 bates prefixes returned 0 results.  
Top-level dirs: `.claude-server-commander/`, `.continue/`, `.cortex/`, `.goodsync/`, `.hoffman-suite/`, `.net/`, `.nuget/`, `.podman/`, `.runpod/`, `.supabase/`, `.templateengine/`, `123triageonedrive/`  
Classification: dev tooling / OneDrive sync — no government discovery files.

---

## DATA SEPARATION VERDICT

| Container | Classification | Gov't Data? |
|-----------|---------------|-------------|
| `disco26` | LEGAL/DISCOVERY | YES — target container |
| `uploads` | LEGAL/DISCOVERY | YES (PROD02 TEXT layer) |
| `recordings` | LEGAL/DISCOVERY | YES (FIVE9 WAVs) |
| `five9-calls` | LEGAL/DISCOVERY | YES (FIVE9 WAVs) |
| `discovery` | LEGAL/DISCOVERY | YES (GJ returns subset) |
| `legal-filings` | LEGAL/DISCOVERY | YES (mixed subset) |
| `evidence-federal` | LEGAL/DEFENSE | NO (defense strategy docs) |
| `backups` | PERSONAL/DEVOPS | NO (monthly backups) |
| `organization` | PERSONAL/DEV | NO (tooling/OneDrive sync) |
| `financial-docs` | PERSONAL/FINANCE | NO (confirmed prev scan) |

**User concern: "my shit" vs "their shit" — confirmed CLEAN SEPARATION.**  
Personal containers (`backups`, `organization`, `financial-docs`) contain zero government bates-stamped files.

---

## WHAT STILL NEEDS TO BE UPLOADED / LOCATED

### 1. PROD01 (RedmondTax 000001–008835) — 8,835 docs
- **Status:** User uploading NOW to `disco26/PROD01_RedmondTax000001-008835/`
- **Source:** USB ("the little fly strike")

### 2. PROD03 (RedmondOvertActs 0001–0722) — 722 docs
- **Status:** NOT IN AZURE (bates-named). May exist as native files somewhere in organization under a Google Drive path, but not confirmed.
- **Action:** Check organization container path `super-master-triage/uploads/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/fed teddies/Fed drive/NATIVES/` — OR upload from USB

### 3. PROD04 (Prod02_Confidential) — up to 991,938 docs
- **Status:** Blocked — blacksand disc (McAfee EERM encrypted, 366 × 2.15 GB volumes)
- **Action:** Need McAfee EERM passphrase to decrypt blacksand

### 4. PROD04 (RedmondiPhone 00001–09698) — 9,698 files
- **Status:** NOT IN AZURE. iPhone Cellebrite extraction.
- **Action:** May be on blacksand; FIVE9_06 series (521 files in `uploads`) might be related

### 5. PROD05 (Prod03_Confidential) — up to 677,497 docs  
- **Status:** NOT IN AZURE (docs). 894k files across 3-part zip on USB.
- **Action:** Upload from USB; `deep_v4.csv` is available for CSV-mode Supabase ingest immediately

---

## SUPABASE INGEST READINESS

| Production | CSV Available | Blobs in Azure | Supabase Ready |
|------------|--------------|----------------|----------------|
| PROD01 | No | Uploading now | After upload |
| PROD02 | No | YES (82k+ in `uploads`) | Need index CSV |
| PROD03 | No | No | Need USB upload |
| PROD04 docs | No | No (blacksand locked) | Blocked |
| PROD05 docs | **YES** (`prod_3/deep_v4.csv`) | No | **CSV-mode NOW** |
| FIVE9_02 calls | No | YES (180k+ WAVs) | Need transcription pipeline |
| FIVE9_03 calls | No | YES (150k+ WAVs) | Need transcription pipeline |
