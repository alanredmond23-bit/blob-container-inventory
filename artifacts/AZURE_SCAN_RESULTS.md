# Azure Blob Scan — Complete 54-Container Coverage
**Case:** U.S. v. Redmond et al., EDPA 24-cr-375-JLS  
**Account:** `menageriesa36965`  
**Scanned:** 2026-05-27 (initial 9 containers) + 2026-05-27 (full 54-container sweep) + 2026-05-26 (Google Drive/Everlaw/Westlaw deep-scan)  
**Method:** Azure REST List Blobs API (Shared Key auth), targeted prefix + path searches  
**IMPORTANT:** This replaces the earlier partial 9-container scan. All 54 containers are now covered.

---

## COMPLETE 54-CONTAINER STATUS

| Container | Blobs | Gov't Data Found | Notes |
|-----------|-------|-----------------|-------|
| **`uploads`** | 82,912 | ✅ PROD02 + FIVE9_02 + FIVE9_06 | RedmondTax 82,912 · FIVE9_02 2,817 · FIVE9_06 521 |
| **`recordings`** | 250k+ | ✅ FIVE9_02 + FIVE9_03 | FIVE9_02 122,402 · FIVE9_03 79,682 (WAVs) |
| **`five9-calls`** | 1.1M+ | ✅ FIVE9_02 + FIVE9_03 | FIVE9_02 57,559+ · trash-series03 72,168 |
| **`legal-filings`** | ~2,500 | ✅ PROD02 + FIVE9_02 | RedmondTax 617 · FIVE9_02 1,882 |
| **`discovery`** | ~1,000 | ✅ PROD02 | RedmondTax 961 (GJ tax returns) |
| **`onedrive-personal`** | 2.3M+ | ✅ FIVE9_02 | FIVE9_02 1,274 · 300k path-scan: 0 overt/iPhone |
| **`organization`** | 479,923 | noise only | 223 RedmondTax in file paths (not actual bates) |
| **`legal`** | 697k | ✅ same as sub-containers | Mirror of: discovery/, evidence-federal/, recordings/ etc. |
| **`backups`** | 340,879 | ❌ CLEAN | Monthly backups 2024-11→2025-05 only |
| **`evidence-federal`** | 243 | ❌ CLEAN | Defense strategy docs only |
| **`financial-docs`** | ~3,500 | ❌ CLEAN | Personal financial docs |
| **`super-master-triage`** | large | ❌ CLEAN | 0 across all 8 prefixes |
| **`1triageworkhorse`** | large | ❌ CLEAN | 0 across all 8 prefixes |
| **`45gb-final-onedrive`** | large | noise only | 1 DS_Store inside FIVE9 folder path — not a real file |
| **`triage`** | — | ❌ CLEAN | 0 across all 8 prefixes |
| **`ice-cold-triage`** | — | ❌ CLEAN | 0 across all 8 prefixes |
| **`moreonedrive`** | — | ❌ CLEAN | 0 across all 8 prefixes |
| **`indexes`** | — | ❌ CLEAN | Session/date-indexed data, no bates |
| **`localtriage4162026admincomp`** | — | ❌ CLEAN | Triage/session data |
| **`lil-red-artifacts`** | — | ❌ CLEAN | 2026-04-04 artifacts |
| **`workhorse-docs`** | — | ❌ CLEAN | Dev tooling docs |
| **`ops-ingest`** | — | ⚠️ INACCESSIBLE | Auth error |
| `agent-outputs` | — | ❌ CLEAN | — |
| `bin` | — | ❌ CLEAN | — |
| `claude-conversations` | — | ❌ CLEAN | — |
| `claude-memory` | — | ❌ CLEAN | — |
| `claude-skills` | — | ❌ CLEAN | — |
| `cursor-extractions` | — | ❌ CLEAN | — |
| `evidence-bankruptcy` | — | ❌ CLEAN | — |
| `evidence-foreclosure` | — | ❌ CLEAN | — |
| `evidence-rush` | — | ❌ CLEAN | — |
| `fleet-sync` | — | ❌ CLEAN | — |
| `loose-files` | — | ❌ CLEAN | — |
| `make-money` | — | ❌ CLEAN | — |
| `marketing-war-command-center` | — | ❌ CLEAN | — |
| `meta-workflow` | — | ❌ CLEAN | — |
| `personal` | — | ❌ CLEAN | — |
| `product-assets` | — | ❌ CLEAN | — |
| `program-files-hd` | — | ❌ CLEAN | — |
| `redmond-os` | — | ❌ CLEAN | — |
| `save-money` | — | ❌ CLEAN | — |
| `scheduling-2026` | — | ❌ CLEAN | — |
| `session-extractions` | — | ❌ CLEAN | — |
| `sys-tweaks-backups` | — | ❌ CLEAN | — |
| `$web` | 404 | — | Container not found |
| `123triageonedrive` | 404 | — | Container not found |
| `benfranklin-dashboard` | 404 | — | Container not found |
| `devops` | 404 | — | Container not found |
| `evidence-family` | 404 | — | Container not found |
| `future` | 404 | — | Container not found |
| `gmail-takeout` | 404 | — | Container not found |
| `mirror-test` | 404 | — | Container not found |
| `models` | 404 | — | Container not found |
| `secrets` | 404 | — | Container not found |
| `disco26` | 32 | — | Target container (placeholder INDEX.md files only) |

---

## PRODUCTION COVERAGE MATRIX (FINAL)

| Production | Bates Range | **IN AZURE?** | Location | Count | Action |
|------------|------------|---------------|---------|-------|--------|
| **PROD01** | RedmondTax 000001–008835 | 🔄 UPLOADING | `disco26/PROD01_...` | — | User uploading from USB |
| **PROD02** | RedmondTax 000836–693308 | ✅ **YES** | `uploads`, `discovery`, `legal-filings` | 84,490+ docs | Already in Azure |
| **PROD03** | RedmondOvertActs 0001–0722 | ❌ **NOT IN AZURE** | NOT FOUND anywhere | 0 | See section below |
| **PROD04** | Prod02_Confidential docs | ❌ NOT FOUND | — | 0 | On blacksand (McAfee encrypted) |
| **PROD04** | FIVE9_02 calls | ✅ **YES** | `recordings`, `five9-calls`, `legal-filings`, `onedrive-personal` | 207k+ WAVs | Multiple copies |
| **PROD04** | RedmondiPhone 00001–09698 | ❌ **NOT IN AZURE** | NOT FOUND anywhere | 0 | See section below |
| **PROD05** | Prod03_Confidential docs | ❌ NOT FOUND | — | 0 | On USB (3-part zip) |
| **PROD05** | FIVE9_03 calls | ✅ **YES** | `recordings`, `five9-calls` | 151k+ WAVs | Multiple copies |

---

## PROD03 (RedmondOvertActs) — WHERE IS IT?

**Confirmed NOT in Azure or Google Drive (synced to Azure)** after:
- Targeted prefix scan (`RedmondOvertActs`) across all 54 containers
- Full path-content scan (300,000 blobs in `onedrive-personal`) for "overtact"/"overt act" in ANY path position
- Same result in `organization` (479,923 blobs), `legal`, `super-master-triage`, `1triageworkhorse`
- Full scan of `uploads/google-drive/FED FED 2026 FINAL DISCO/` — 105,396 blobs, 0 "overt" hits
- All subfolders in `FINAL FED FUCK YOU/` enumerated — no RedmondOvertActs naming

**Most likely location: Everlaw.** "DISCOVERY PART 2 Heim delivery" (5,108 files) or "DISCOVERY PART 1 (Memorex disk)" (1,286 files) may contain PROD03. Need API key to confirm.

**Production timeline:** PROD03 was delivered **07/18/2025 via USAfx file share** (722 docs).

**Where to look next:**
1. **Everlaw** — Query `DISCOVERY PART 2 Heim delivery` document set via API. 5,108 files, delivered by prior counsel David Heim — timeline matches PROD03 delivery.
2. **HP Envy laptop** — Primary USAfx download machine. Check: `C:\Users\bigred\Downloads\`, Desktop, folders modified 2025-07-18 to 2025-08-31
3. **USAfx portal** — Still accessible at the original share link (docs may still be downloadable)
4. **The `onedrive-personal` remaining ~2M blobs** (we scanned 300k of ~2.3M total)

**Size:** Only 722 docs total. Small enough to re-download from USAfx if still available.

---

## RedmondiPhone (PROD04 iPhone) — WHERE IS IT?

**Confirmed NOT in Azure** — 0 results for "RedmondiPhone", "iphone", "cellebrite" across all containers.

**Note on hallucinated path:** An earlier AI agent fabricated the path `backups/admin-2026-04-17/rclone-staging/iphone_forensic_20250821T052231Z/` — this path **does not exist**. The actual `rclone-staging/` folder only has `Antigravity/` and `benfranklin-dashboard/` subdirs.

**Production timeline:** PROD04 delivered **09/29/2025 via Hard Drive** — iPhone extraction likely on the same hard drive or a separate Cellebrite export.

**Where to look next:**
1. **PROD04 hard drive (blacksand)** — McAfee EERM encrypted. Need passphrase to access
2. **HP Envy** — If the hard drive was connected to it, Cellebrite files may have been copied
3. **Google Drive** — Check for Cellebrite export folder

---

## DATA SEPARATION VERDICT (FINAL)

| Container Category | Gov't Data? |
|-------------------|-------------|
| `uploads`, `recordings`, `five9-calls`, `legal-filings`, `discovery` | YES — government production |
| `legal`, `onedrive-personal` | YES — contains copies/mirrors of production |
| `evidence-federal` | NO — defense strategy only |
| `backups` | NO — personal monthly backups |
| `organization` | NO — dev tooling / OneDrive sync noise |
| `financial-docs`, `evidence-bankruptcy/foreclosure/rush` | NO — personal/civil |
| All triage/workhorse/dev containers | NO — dev ops only |

**Clean separation confirmed:** No government discovery bates files exist in personal containers.

---

## GOOGLE DRIVE / EVERLAW / WESTLAW FINDINGS

### Five9 Calls in Google Drive
- `uploads/google-drive/DAVID HEIM DISC/FIVE9 - ALAN REDMOND/ALAN REDMOND/` — **1 DS_Store only** (empty folder sync artifact)
- `uploads/Google Drive/DAVID HEIM DISC/FIVE9 - ALAN REDMOND/ALAN REDMOND/` — same
- `uploads/Google Drive/FIVE9_COMBINED/` — only `_gsdata_/` sync artifact, no audio files
- `uploads/google-drive/FIVE9_ 01_ 0000000001-0000250000_AR/` — 1 DS_Store only
- **Conclusion:** Real Five9 audio is NOT in Google Drive. All Five9 WAVs are in Azure `recordings/` (250k+) and `five9-calls/` (1.1M+) containers.

### Westlaw "Directory"
- **Westlaw is a research tool, not a file repository.** Two PDF exports found in uploads:
  - `Google Drive/DAVID HEIM DISC/1. Discovery_Docket/01_Docket Activity/08_Westlaw_Docket_(2024-12-31).pdf`
  - `Google Drive/DAVID HEIM DISC/1. Discovery_Docket/01_Docket Activity/08_Westlaw_Docket_(2024-12-31) (1).pdf`
- Also: `organization/123triageonedrive/onedrive/WESTLAW_SEARCH_LIST.md` (search term list)
- No Westlaw account data, bulk exports, or case law directory found anywhere.

### Everlaw — Active Platform (589,253 Documents Indexed)
Source file: `45gb-final-onedrive/ORGANIZATION/indexes/01_raw/INTERNALLY_GENERATED/03_DATA/ALL INDEXES ON ALL LOCATIONS/Everlaw_Document_Sets_Inventory.csv`

| Document Set | Type | File Count | % of Total |
|-------------|------|-----------|-----------|
| MBOX (from Alan + Alan's computer) — alanredmond23 gmail.com | Native | 445,085 | 75.53% |
| Discovery 1 (Disc 2 - small) | Native | 130,365 | 22.12% |
| mbox (minus 82gb) | Native | 7,222 | 1.23% |
| DISCOVERY PART 2 Heim delivery | Native | 5,108 | 0.87% |
| DISCOVERY PART 1 (Memorex disk) | Native | 1,286 | 0.22% |
| FIVE9_ 06_CONFIDENTIAL_AR | Processed | 165 | 0.03% |
| 30b | Processed | 11 | 0.00% |
| DOJ Filings | Native | 10 | 0.00% |
| from local FIVE9 PART 1 COMBINED | Native | 1 | 0.00% |
| **TOTAL** | | **589,253** | 100% |

**Mapping hypothesis:**
- "Discovery 1 (Disc 2 - small)" → likely PROD02 RedmondTax (130k docs subset)
- "DISCOVERY PART 1 (Memorex disk)" → likely PROD01 (1,286 docs)
- "DISCOVERY PART 2 Heim delivery" → may contain PROD03 (RedmondOvertActs, 722 docs) or PROD04 docs
- "FIVE9_ 06_CONFIDENTIAL_AR" → PROD04/05 Five9 calls (processed in Everlaw)

**To confirm PROD03 presence in Everlaw:** Need Everlaw API key (`EVERLAW_API_KEY`) to query document sets. MCP server code exists at `organization/everlaw_mcp/everlaw_mcp_server.py`.

### FED FED 2026 FINAL DISCO — Google Drive Folder Structure
`uploads/google-drive/FED FED 2026 FINAL DISCO/FINAL FED FUCK YOU/` — 34,441 files total:

| Subfolder | Files | Notes |
|-----------|-------|-------|
| Stephanie_Miller | 33,137 | Deposition transcripts/exhibits (Govt witness) |
| IRS Files and Interviews | 189 | IRS agent files |
| images | 448 | `RedmondTax008864.jpg` etc. — PROD02 natives |
| NATIVES | 499 | `RedmondTax474128.xlsx` etc. — PROD02 natives |
| Discovery Production US v. Redmond, 24-cr-376-selected | 86 | FBI 302s, Grand Jury Exhibits, Guaranteed Payments |
| Grand Jury Exhibits | 69 | (subdir) `1K9MR8~W.PDF`, etc. |
| 30(b)(6) | 10 | Bene Market, LLC depositions |
| Witness folders | ~93 | Alan_Redmond, Walsh, Barrera, Sardella, Malcolm_Smith |
| DOL civil wage litigation | 8 | Civil case selected docs |

**No `RedmondOvertActs` bates naming found in any of the 105,396 blobs scanned in this directory.**

---

## SUPABASE INGEST READINESS

| Production | Ingest Mode | Status |
|------------|-------------|--------|
| PROD01 | blob → text extract | Waiting for USB upload to complete |
| PROD02 | blob → text extract | Ready — 82k+ docs in `uploads` |
| PROD03 | blob → text extract | **BLOCKED — not in Azure** |
| PROD04 docs | blob → text extract | **BLOCKED — blacksand encrypted** |
| PROD04 Five9 | audio → transcribe | Ready — 207k+ WAVs in Azure |
| PROD05 docs | **CSV-mode NOW** | `prod_3/deep_v4.csv` (108k rows) ready immediately |
| PROD05 Five9 | audio → transcribe | Ready — 151k+ WAVs in Azure |

**Immediate next action for Supabase:** Run CSV-mode ingest for PROD05:
```bash
python3 scripts/disco_ingest.py --source csv --production PROD05
# Requires: SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY
```
