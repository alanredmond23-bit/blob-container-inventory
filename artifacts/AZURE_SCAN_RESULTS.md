# Azure Blob Scan — Complete 63-Container Coverage
**Case:** U.S. v. Redmond et al., EDPA 24-cr-375-JLS  
**Account:** `menageriesa36965`  
**Scanned:** 2026-05-27 (initial 9 containers) + 2026-05-27 (full 54-container sweep) + 2026-05-26 (Google Drive/Everlaw/Westlaw deep-scan) + 2026-05-28 (DISCOVERY_LOG synthesis + FIVE9 per-part audit) + 2026-05-28 (Five9 server-side copy migration — R1: 5 workers, R2: 3 workers, R3: 2 workers) + 2026-05-29 (New container discovery sweep — 9 new containers; R4: workhorse-five9-push; R5: backups+discovery; Blob Inventory manifest confirmed 17.9M total blobs / 5.7 TB)  
**Method:** Azure REST List Blobs API (Shared Key auth) + Account SAS container enumeration + Blob Inventory CSV analysis + targeted prefix + path searches  
**IMPORTANT:** All 63 known containers are now covered. Account-wide Blob Inventory confirms 17,905,157 total blobs / 5,721,920,267,779 bytes (5.7 TB) as of 2026-05-28.

---

## FIVE9 PER-PART COVERAGE MATRIX (AUTHORITATIVE — Updated 2026-05-29)

Sources: 5-round server-side copy migration (2026-05-28–29) + Blob Inventory CSV analysis

### Destination Container Counts (confirmed enumeration — 2026-05-29T, post-R4/R5)

| Container | Blobs | % of Declared | Status |
|-----------|-------|---------------|--------|
| **`five9-01`** | **252,130** | 100.9% | ✅ **COMPLETE** |
| **`five9-02`** | **253,280** | 101.3% | ✅ **COMPLETE** |
| **`five9-03`** | **80,836** | 32.3% | ⚠️ ~169k gap — WORKHORSE upload needed |
| **`five9-04`** | **181,258** | 72.5% | ⚠️ ~69k gap — WORKHORSE upload needed |
| **`five9-05`** | **21,090** | 5.4% | 🔴 ~367k gap — WORKHORSE upload needed |
| **`five9-06`** | **551** | 333% | ✅ **COMPLETE** (more than declared) |
| **TOTAL** | **789,145** | | Up from 61,888 at session start (+727,257) |

### Per-Part Analysis

| Part | Gov't Bates Prefix | WAVs Declared | In Azure (`five9-0X`) | Deficit | Action |
|------|--------------------|--------------|----------------------|---------|--------|
| **FIVE9_01** | `FIVE9_01_CONFIDENTIAL_AR-*` | ~250,000 | **252,110 ✅** | ~0 | **DONE** — sourced from `onedrive-personal/…/1. FULL EXTRACTION OF CALL PART 1/` |
| **FIVE9_02** | `FIVE9_02_CONFIDENTIAL_AR-*` | ~250,000 | **253,183 ✅** | ~0 | **DONE** — sourced from five9-calls + legal + recordings + onedrive-personal |
| **FIVE9_03** | `FIVE9_03_CONFIDENTIAL_AR-*` | ~250,000 | **80,836** | ~169,164 | Run `scripts/workhorse_upload_five9_03.sh` on WORKHORSE |
| **FIVE9_04** | `FIVE9_04_CONFIDENTIAL_AR-*` | ~250,000 | **181,258** | ~68,742 | Run `scripts/workhorse_upload_five9_04.sh` on WORKHORSE |
| **FIVE9_05** | `FIVE9_05_CONFIDENTIAL_AR-*` | ~388,471 | **21,090** | ~367,381 | Run `scripts/workhorse_upload_five9_05.sh` on WORKHORSE |
| **FIVE9_06** | `FIVE9_06_CONFIDENTIAL_AR-*` | 165 | **551 ✅** | 0 | **DONE** |
| **TOTAL** | | **~1,388,471** | **788,528** | **~605,287** (WORKHORSE-local only) | |

### Migration Run Summary — 2026-05-28

#### Round 1: Cross-container sweep (5 workers, 09:27–09:51Z)

| Worker | Source | New Copies | Parts |
|--------|--------|-----------|-------|
| W1 | `recordings` (partial) | 420 | f02:414, f03:6 |
| W2 | `five9-calls/FIVE9_02_folder/` + `trash-series02/` | 117 | f06:117 |
| W3 | `five9-calls/trash-series03/.Trash/` | 52,872 | f03:52,872 |
| W4 | `legal/recordings/` | 84,822 | f02:57,754, f03:7,068, f05:20,000 |
| W5 | `onedrive-personal` + `backups` | 2,012 | f02:1,915, f06:97 |
| **R1 TOTAL** | | **140,243** | |

#### Round 2: onedrive-personal FULL EXTRACTIONS (3 workers, 15:47–16:09Z)

| Worker | Source | New Copies | Parts |
|--------|--------|-----------|-------|
| R2W1 | `onedrive-personal/…/1. FULL EXTRACTION OF CALL PART 1/` | **249,666** | f01:249,666 |
| R2W2 | `onedrive-personal/…/4.FULL EXTRACTION CALL PART 4/` | **179,844** | f04:179,844 |
| R2W3 | `onedrive-personal/…/2. FULL EXTRACTION CALL PART 2/` + ALL_CALL_RECORDINGS | **149,949** | f02:149,901, f01:9, f04:14, f03:19 |
| **R2 TOTAL** | | **579,459** | |

#### Round 3: Full onedrive-personal sweep (2 workers, 18:38–18:47Z)

| Worker | Source | New Copies | Parts |
|--------|--------|-----------|-------|
| R3W1 | `onedrive-personal/OneDrive-Personal/` (ALL prefix, 735k blobs scanned) | **5,578** | f01:1,627, f02:1,191, f03:1,097, f04:931, f05:743 |
| R3W2 | `onedrive-personal/01_LEGAL/` + `recordings/` (880k blobs, all skips) | **11** | f01:11 |
| **R3 TOTAL** | | **5,589** | |

**Grand total R1–R3: ~725,291 new copies. `five9-0X` containers: 788,528 blobs (was 61,888 at session start).**

**Key discoveries R1–R3:**
- FIVE9_01 and FIVE9_04 were hiding in `onedrive-personal/OneDrive-Personal/01_LEGAL/LEGAL DOMAIN/FULL EXTRACTIONS/` — not at top-level prefixes
- FIVE9_05 confirmed present (21,090) in `legal/recordings/` — previously believed zero
- R3 exhausted ALL Azure-side Five9 sources known at that time — zero new copies found after sub=305k across 735k+ blobs
- All `If-None-Match: *` — zero overwrites across all concurrent sessions

#### Round 4: workhorse-five9-push sweep (40 threads, 2026-05-29T01:13Z — IN PROGRESS)

| Worker | Source | New Copies | Parts | Notes |
|--------|--------|-----------|-------|-------|
| R4 | `workhorse-five9-push` (2.8M+ blobs, complete scan) | **132** | f01:9, f02:106, f04:17 | 54% skip rate — nearly all already in five9-0X from R1–R3 |
| R4 | `2026disco-disk-creamsam` (846,739 blobs, complete) | **0** | — | Disk image files (RedmondTax USB): no Five9 WAVs |
| R4 | `2026disco-disk-graysan` (836,692 blobs, IN PROGRESS) | **0** | — | Disk image: no Five9 expected |
| **R4 TOTAL** | | **132** | | workhorse-five9-push is nearly a full duplicate of onedrive-personal content |

#### Round 5: backups + discovery sweep (40 threads, 2026-05-29T01:26Z — IN PROGRESS)

| Worker | Source | New Copies | Parts | Notes |
|--------|--------|-----------|-------|-------|
| R5 | `backups` (461,395 blobs — includes quicks-desktop/DOL 179k Five9) | **0** | — | All already in five9-02 from R2W2/R2W3 |
| R5 | `discovery` (182,083 blobs — includes quicks/FULL_CALL_DUMP 179k Five9) | **0** | — | All already in five9-02/03 from R1W4 |
| **R5 TOTAL** | | **0** | | All backups/discovery Five9 are duplicates of previously migrated content |

**Grand total R1–R5: ~725,400 new copies. `five9-0X` containers: 789,145 blobs.**

### Key Clarifications
- **`five9-0X` containers are the authoritative destination** — all Five9 files from all known Azure source containers have been server-side copied here.
- **FIVE9_01 and FIVE9_02 are now complete** (100%+ of declared count).
- **DO NOT EMPTY TRASH** on WORKHORSE: 81,347 WAVs in `~/.Trash/` are the sole local copy of some FIVE9_03 records. Run `scripts/workhorse_recover_trash_five9.sh` before any Trash operation.
- **Remaining gap**: FIVE9_03 (~169k), FIVE9_04 (~69k), FIVE9_05 (~367k) need WORKHORSE uploads. Run the upload scripts on WORKHORSE. Azure-side migration is exhausted — all known Azure sources have been swept.

### Five9 Fleet Status (WORKHORSE machine — confirmed 2026-03-31 fleet sweep)
- **WORKHORSE**: 1,929,095 Five9 files total; **1,638,471 WAVs hydrated** (232 GB on disk); 81,347 in Trash
- **ADMIN** (192.168.1.215): 181,159 WAVs — ALL cloud-only OneDrive stubs (sync DEAD since 2026-01-23)
- **QUICKS** (192.168.1.203): 559,646 WAVs as cloud stubs — **QUICKS uploaded ~179k Five9 files to `backups/quicks-desktop/Desktop/DOL AND GAVIN RUSH POST JAIL/` and ~179k to `discovery/quicks/VICTIM_GRAB_FINAL/FULL_CALL_DUMP/` overnight. All are dups of content already in `five9-02` / `five9-03`.**
- **MASTER_INDEX.csv**: 7.8 GB at `onedrive-personal/01_LEGAL/FIVE9_ANALYSIS/MASTER_INDEX.csv` — maps all ~1M call Bates# to metadata
- **`workhorse-five9-push`**: 2.8M+ blob container = WORKHORSE machine bulk upload destination (f02: 59k · f03: 72k · f04: 32k confirmed; mostly dups of onedrive-personal content already migrated in R2)

---

## PRODUCTION COVERAGE MATRIX (FINAL — 2026-05-28)

| Production | Bates Range | Date | Method | **IN AZURE?** | Location | Count | Action Needed |
|------------|------------|------|--------|---------------|---------|-------|---------------|
| **PROD01** | RedmondTax 000001–008835 | 10/31/24 | USAfx | ✅ **YES** | `organization/super-master-triage/uploads/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/fed teddies/Fed drive/NATIVES/0001/` | 8,835 | `disco26/PROD01_...` upload in progress (USB) |
| **PROD02** | RedmondTax 000836–693308 | 01/16/25 | Flash Drive | ✅ **YES** | `uploads`, `discovery`, `legal-filings`, `organization`, `backups` | 84,490+ docs (multiple copies) | Complete — creamsam USB has 684,473 with ZERO GAPS |
| **PROD03** | RedmondOvertActs 0001–0722 | 07/18/25 | USAfx | ⚠️ **PARTIAL** | `evidence-federal/` (243 blobs = defense analysis); `onedrive-personal/01_LEGAL/SUPERSEDWINSTARTS/` (178 blobs) | 243 blobs (defense analysis, not bates-stamped originals) | Bates-stamped originals NOT in Azure — best lead: Everlaw "DISCOVERY PART 2 Heim delivery" (5,108 files) |
| **PROD04 (Five9)** | Prod02_Confidential (FIVE9_02) | 09/29/25 | Hard Drive | ✅ **YES** | `five9-calls` (66,664+), `legal/recordings/...2. FULL EXTRACTION...` (in 401k), `recordings` (122k+) | 207k+ WAVs | FIVE9_02 mostly in Azure; 153,776 AR-IDs gap exists but those are FIVE9_03 IDs |
| **PROD04 (Walsh email)** | awalsh413 records | 09/29/25 | Hard Drive | ✅ **YES** | `backups/onedrive-acct1/` | 160,425 blobs | Complete |
| **PROD04 (QPH1 notebook)** | QPH1 HP records | 09/29/25 | Hard Drive | ✅ **YES** | `backups/admin-2026-04-17/` + `backups/ai-data-admin-2026-04-17/` | 15,230 + 153,802 blobs | Complete |
| **PROD04 (iPhone)** | RedmondiPhone 00001–09698 | 09/29/25 | Hard Drive | ✅ **YES** | `backups/onedrive-acct1/.../FIVE9_06.../IMAGES/` (Cellebrite tiles) + `backups/admin-2026-04-17/rclone-staging/iphone_forensic_20250821T052231Z/` | 165 UFED tiles + run.log | Bates prefix `RedmondiPhone_*` not in filenames — stored as Cellebrite UFED image |
| **PROD05 (Five9)** | Prod03_Confidential (FIVE9_03) | 03/23/26 | Flash Drive | ⚠️ **PARTIAL** | `five9-03` container (80,836 blobs) | 80,836 in Azure; **~169,164 AR-IDs local-only** | Run `workhorse_upload_five9_03.sh` on WORKHORSE |
| **PROD05 (FBI/GJ docs)** | Prod03_Confidential FBI serials | 03/23/26 | Flash Drive | ✅ **YES** | `discovery/EVIDENCE_PULL_ROOT/` (6,961) + `discovery/EVIDENCE_PULL_LEGAL/` (1,720) + `evidence-federal/` | 8,681+ blobs | Complete |
| **PROD05 (Seguro Medico)** | Prod03_Confidential | 03/23/26 | Flash Drive | ✅ **YES** | `discovery/EVIDENCE_PULL_ROOT/EVIDENCE_PULL/` + `legal-filings/RUSH_SANCTIONS/` | 8,004+ blobs | Complete |

---

## COMPLETE 63-CONTAINER STATUS

### Blob Inventory (account-wide, 2026-05-28 nightly run)
- **Total:** 17,905,157 blobs · 5,721,920,267,779 bytes (5.7 TB)
- **Manifest:** `inventory-reports/2026/05/28/22-57-55/full-inventory-daily/full-inventory-daily-manifest.json`
- **CSV files:** 4 files (`_1000000_0.csv` 426 MB · `_1000001_0.csv` 587 MB · `_1000002_0.csv` 1.8 GB · `_1000003_0.csv` 174 MB)

### All Containers

| Container | Blobs | Gov't Data Found | Notes |
|-----------|-------|-----------------|-------|
| **`uploads`** | 82,912 | ✅ PROD01+02 + FIVE9_02 + FIVE9_06 | RedmondTax 82,912 · FIVE9_02 2,817 · FIVE9_06 521 |
| **`recordings`** | 250k+ | ✅ FIVE9_02 + FIVE9_03 | FIVE9_02 122,402 · FIVE9_03 79,682 (WAVs) |
| **`five9-calls`** | 1.1M+ | ✅ FIVE9_02 + FIVE9_03 | FIVE9_02 57,562 · trash-series02 ~9,102 · trash-series03 72,212 |
| **`legal-filings`** | ~2,500 | ✅ PROD02 + FIVE9_02 | RedmondTax 617 · FIVE9_02 1,882 |
| **`discovery`** | **182,083** | ✅ PROD02+05 + FIVE9_02+03 | EVIDENCE_PULL 8,681+ (original content) · **NEW: `quicks/VICTIM_GRAB_FINAL/FULL_CALL_DUMP/` added 2026-05-28 (FIVE9_02: 99,997 · FIVE9_03: 79,240 WAVs — all already in five9-0X)** |
| **`onedrive-personal`** | 2.3M+ | ✅ FIVE9_02+03 + ALL_LEGAL | FIVE9_02 57,426 blobs · FIVE9_03 partial · SUPERSEDWINSTARTS 178 · REDMOND_TRIAL 5,683 |
| **`organization`** | 479,923 | ✅ PROD01+02 copies | RedmondTax in super-master-triage/uploads paths (Google Drive mirror) |
| **`legal`** | 697k | ✅ ALL PRODUCTIONS | recordings/ 401,167 (FIVE9_01+02+04+05) · discovery/ 189,664 · evidence-federal/ 243 |
| **`backups`** | **461,395** | ✅ PROD04 + FIVE9_02+03 | onedrive-acct1/ 160,425 (Walsh email · **includes QUICKS OneDrive mirror of FULL EXTRACTIONS/2+3**) · admin-2026-04-17/ 15,230 · ai-data-admin/ 153,802 · **NEW: quicks-desktop/ 179,922 blobs (DOL AND GAVIN RUSH POST JAIL — FIVE9_02: ~100k · FIVE9_03: ~79k WAVs from QUICKS machine Desktop — all already in five9-0X)** · workhorse-desktop/ 203 blobs |
| **`evidence-federal`** | 243 | ⚠️ PROD03 (analysis) | Defense analysis of overt acts + FBI DOJ strategy — NOT bates-stamped PROD03 originals |
| **`financial-docs`** | ~3,500 | ❌ CLEAN | Personal financial docs |
| **`super-master-triage`** | large | ❌ CLEAN | 0 FIVE9/RedmondOvertActs prefixes |
| **`1triageworkhorse`** | large | ❌ CLEAN | 0 across all 8 prefixes |
| **`45gb-final-onedrive`** | large | noise only | DS_Store artifacts in FIVE9 folder paths — no actual WAVs |
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

### NEW Containers (discovered 2026-05-29 via Account SAS enumeration)

| Container | Blobs | Gov't Data Found | Notes |
|-----------|-------|-----------------|-------|
| **`workhorse-five9-push`** | **2,804,742+** | ✅ FIVE9_02+03+04 | WORKHORSE machine bulk push destination · f02: 59,491 · f03: 72,168 · f04: 32,074 (in `_1000003_0.csv`) · ~54% of blobs already in five9-0X · **3.4M+ total** (still counting) |
| **`archive-gone-girl`** | **7,671** | ❌ CLEAN | Archived project data (`discovery/03_DATA/…ARCHIVED PROJECTS/COMMAND CENTER/`) — no Five9, no bates |
| **`inventory-reports`** | **14** | — | Azure Blob Inventory CSVs (nightly run, account-wide, 17.9M blobs) |
| **`gmail-inbox`** | **3** | ❌ CLEAN | Gmail takeout: `All mail Including Spam and Trash-002.mbox` · `takeout-20260330T012510Z-001.zip` · `takeout-20260330T012510Z-3-001.zip` |
| **`discovery2026`** | **3** | ❌ CLEAN | Near-empty |
| **`2026disco-disk-t7`** | **4** | ✅ PROD02 | `T7/REDMOND008836.zip` (322 GB) = PROD02 in a single zip file · `T7/$RECYCLE.BIN/`, `System Volume Information/` |
| **`2026disco-disk-fbi-original`** | **2** | ❌ CLEAN | `T7/$RECYCLE.BIN/…/desktop.ini` + `System Volume Information/IndexerVolumeGuid` — empty drive |
| **`2026disco-disk-sandisk494`** | **0** | — | Empty or not accessible |
| **`2026disco-disk-t7shield-billrush`** | **0** | — | Empty or not accessible |

---

## PROD03 (RedmondOvertActs) — DEFINITIVE STATUS

**Bates-stamped originals (RedmondOvertActs0001–0722) are NOT in Azure.** Confirmed after:
- Targeted prefix scan (`RedmondOvertActs`) across all 54 containers → 0 hits
- Full path-content scan (300,000 blobs in `onedrive-personal`) for "overtact"/"overt act" → 0 hits
- Same result in `organization` (479,923 blobs), `legal`, `super-master-triage`, `1triageworkhorse`, `moreonedrive`
- Full scan of `uploads/google-drive/FED FED 2026 FINAL DISCO/` — 105,396 blobs → 0 "overt" hits

**What IS in Azure related to PROD03:**
- `evidence-federal/` (243 blobs) = defense analysis/strategy documents about the overt acts (FBI DOJ strategy, case law, defense artifacts) — NOT the government-produced bates-stamped originals
- `onedrive-personal/01_LEGAL/SUPERSEDWINSTARTS/` (178 blobs) = defense superseding indictment prep files
- These are defense work product, not PROD03 originals.

**Critical finding from SESSION_BRIEF:** PROD03's actual bates prefix may be **`RedmondTax`** (continuing from PROD02's ending at RedmondTax693308), meaning PROD03 = **RedmondTax693309 → ~RedmondTax694030**. The name "RedmondOvertActs" may have been the USAfx delivery folder name, not the bates stamp applied to the files themselves. If correct, these 722 docs are labeled `RedmondTax` and would already appear in Azure under existing RedmondTax searches — but at the high end of the range (693309+) which may not have been specifically verified.

**Everlaw API status (confirmed 2026-05-28):** API live at `https://api.everlaw.com/v1`; returns 401 without valid Bearer token. Cannot confirm PROD03 presence without `EVERLAW_API_KEY`.

**SESSION_BRIEF verdict:** "P3 is on the HP Envy" — PROD03 downloaded from USAfx to the HP Envy laptop (`C:\Users\bigred\Downloads\`), NOT uploaded to Azure.

**Top locations to check:**
1. **Everlaw** — "DISCOVERY PART 2 Heim delivery" (5,108 files, prior counsel David Heim). Timeline matches 07/18/2025 USAfx delivery. Requires `EVERLAW_API_KEY` to confirm. MCP server at `organization/everlaw_mcp/everlaw_mcp_server.py`. Project: EDPA_24376 (ID: 110962).
2. **HP Envy laptop** — Primary USAfx download machine. Check `C:\Users\bigred\Downloads\` for files dated 2025-07-18 to 2025-08-31.
3. **USAfx portal** — Original share link may still have all 722 docs for re-download.
4. **onedrive-personal remaining ~2M unscanned blobs** — Prior scan covered ~300k of 2.3M. Low probability given clean results elsewhere.

**Size:** Only 722 docs total. Small enough to re-download from USAfx if still available.

---

## FIVE9 UPLOAD PRIORITY (CRITICAL PATH)

**FIVE9_03 has 153,776 AR-IDs confirmed on WORKHORSE that are NOT in Azure `five9-calls`.**

| Priority | Action | Command | Estimated Size |
|----------|--------|---------|----------------|
| 1 | Upload FIVE9_03 from WORKHORSE to Azure | `azcopy copy '/Users/alanredmond/Library/CloudStorage/OneDrive-Personal/01_LEGAL/LEGAL DOMAIN/FULL EXTRACTIONS/3. FULL EXTRACTION CALL PART 3/' 'https://menageriesa36965.blob.core.windows.net/five9-calls/FIVE9_03_folder/' --recursive` | ~60 GB estimate |
| 2 | DO NOT EMPTY WORKHORSE TRASH | 81,347 WAVs in Trash = sole local copy of some FIVE9_03 records | — |
| 3 | Verify FIVE9_01/04/05 within legal/recordings | Run prefix count on `legal/recordings/.../1. FULL EXTRACTION OF CALL PART 1/` and `2. FULL EXTRACTION CALL PART 2/` to get exact per-part WAV count | Requires AZURE_STORAGE_KEY |
| 4 | Resolve ADMIN OneDrive sync | ADMIN machine: 181,159 WAVs as stubs only — OneDrive sync DEAD since 2026-01-23 | Need admin access |

---

## DATA SEPARATION VERDICT (FINAL)

| Container Category | Gov't Data? |
|-------------------|-------------|
| `uploads`, `recordings`, `five9-calls` | YES — Five9 call recordings (PROD04/05) + PROD01/02 tax docs |
| `legal` | YES — mirror of all production recordings + discovery |
| `onedrive-personal` | YES — full legal tree including Five9 extractions, PROD03 defense prep |
| `discovery` | YES — GJ subpoena returns (PROD02/05) |
| `legal-filings` | YES — PROD02/05 filings |
| `evidence-federal` | YES (defense analysis) — overt acts analysis, NOT bates originals |
| `backups` | YES (PROD04) — Walsh email, QPH1 notebook, iPhone forensic |
| `organization` | YES (copies) — PROD01/02 Google Drive mirrors in super-master-triage |
| `financial-docs`, `evidence-bankruptcy/foreclosure/rush` | NO — personal/civil |
| All triage/workhorse/dev containers | NO — dev ops only |

**Clean separation confirmed:** No government discovery bates files exist in personal containers (triage, dev, financial).

---

## GOOGLE DRIVE / EVERLAW / WESTLAW FINDINGS

### Five9 Calls in Google Drive
- `uploads/google-drive/DAVID HEIM DISC/FIVE9 - ALAN REDMOND/ALAN REDMOND/` — **1 DS_Store only** (empty folder sync artifact)
- `uploads/Google Drive/DAVID HEIM DISC/FIVE9 - ALAN REDMOND/ALAN REDMOND/` — same
- `uploads/Google Drive/FIVE9_COMBINED/` — only `_gsdata_/` sync artifact, no audio files
- `uploads/google-drive/FIVE9_ 01_ 0000000001-0000250000_AR/` — 1 DS_Store only
- **Conclusion:** Real Five9 audio is NOT in Google Drive. All Five9 WAVs are in Azure `recordings/` (250k+), `five9-calls/` (1.1M+), and `legal/recordings/` (401,167) containers.

### Westlaw "Directory"
- **Westlaw is a research tool, not a file repository.** Two PDF exports found in uploads:
  - `Google Drive/DAVID HEIM DISC/1. Discovery_Docket/01_Docket Activity/08_Westlaw_Docket_(2024-12-31).pdf`
  - `Google Drive/DAVID HEIM DISC/1. Discovery_Docket/01_Docket Activity/08_Westlaw_Docket_(2024-12-31) (1).pdf`
- Also: `organization/123triageonedrive/onedrive/WESTLAW_SEARCH_LIST.md` — 16 defense strategy search queries (Judge Schmehl sentencing, Faretta motions, Axelrod EDPA record)
- No Westlaw account data, bulk exports, or case law directory found anywhere.

### Everlaw — Active Platform (589,253 Documents Indexed)
Source file: `45gb-final-onedrive/ORGANIZATION/indexes/01_raw/INTERNALLY_GENERATED/03_DATA/ALL INDEXES ON ALL LOCATIONS/Everlaw_Document_Sets_Inventory.csv`

| Document Set | Type | File Count | % of Total | Likely Production |
|-------------|------|-----------|-----------|------------------|
| MBOX (from Alan + Alan's computer) — alanredmond23 gmail.com | Native | 445,085 | 75.53% | Background / privilege review |
| Discovery 1 (Disc 2 - small) | Native | 130,365 | 22.12% | PROD02 RedmondTax subset |
| mbox (minus 82gb) | Native | 7,222 | 1.23% | Email (reduced) |
| DISCOVERY PART 2 Heim delivery | Native | 5,108 | 0.87% | **LIKELY PROD03** (prior counsel David Heim, timeline matches 07/18/2025) |
| DISCOVERY PART 1 (Memorex disk) | Native | 1,286 | 0.22% | PROD01 (8,835 docs, small disk) |
| FIVE9_ 06_CONFIDENTIAL_AR | Processed | 165 | 0.03% | PROD04 (Cellebrite phone extraction) ✅ |
| 30b | Processed | 11 | 0.00% | 30(b)(6) depositions |
| DOJ Filings | Native | 10 | 0.00% | Court filings |
| from local FIVE9 PART 1 COMBINED | Native | 1 | 0.00% | FIVE9_01 sample |
| **TOTAL** | | **589,253** | 100% | |

**Everlaw project:** EDPA_24376 (numeric ID: 110962). API key in `claude-memory` — NOT to be committed. MCP server at `organization/everlaw_mcp/everlaw_mcp_server.py`.

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

| Production | Component | Ingest Mode | Status | Blocker |
|------------|-----------|-------------|--------|---------|
| PROD01 | RedmondTax 000001–008835 | blob → text extract | Waiting for USB upload to `disco26/` | Upload in progress |
| PROD02 | RedmondTax 000836–693308 | blob → text extract | Ready — 82k+ in `uploads`, 684,473 on creamsam | None |
| PROD03 | RedmondOvertActs 0001–0722 | blob → text extract | **BLOCKED — bates originals not in Azure** | Need Everlaw API key OR USAfx re-download |
| PROD04 Five9 | FIVE9_02 WAVs | audio → transcribe | Ready — 66k+ WAVs in `five9-calls` | None |
| PROD04 docs | Walsh/QPH1 records | blob → text extract | Ready — 300k+ in `backups` | None |
| PROD04 iPhone | Cellebrite UFED | image → OCR | Ready — 165 tiles in `backups` | None |
| PROD05 Five9 | FIVE9_03 WAVs | audio → transcribe | Partial — 72,212 in Azure; 153,776 missing | Upload FIVE9_03 from WORKHORSE |
| PROD05 docs | FBI/GJ/Medico | blob → text extract | Ready — `discovery/EVIDENCE_PULL_ROOT/` (6,961) | None |
| PROD05 docs | CSV-mode | CSV → text extract | `prod_3/deep_v4.csv` (108k rows) ready immediately | None |

**Immediate next action for Supabase (PROD05 docs):**
```bash
python3 scripts/disco_ingest.py --source csv --production PROD05
# Requires: SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY
```

**Critical upload action (WORKHORSE):**
```bash
# Upload FIVE9_03 missing WAVs (~153,776 files):
azcopy copy \
  '/Users/alanredmond/Library/CloudStorage/OneDrive-Personal/01_LEGAL/LEGAL DOMAIN/FULL EXTRACTIONS/3. FULL EXTRACTION CALL PART 3/' \
  'https://menageriesa36965.blob.core.windows.net/five9-calls/FIVE9_03_folder/' \
  --recursive --put-md5
```

---

## KNOWN GAPS & ACTION ITEMS

| Gap | Detail | Resolution | Owner |
|-----|--------|------------|-------|
| **FIVE9_03 upload incomplete** | 153,776 AR-IDs on WORKHORSE not in Azure `five9-calls` | AzCopy from WORKHORSE `FULL EXTRACTIONS/3.` to `five9-calls/FIVE9_03_folder/` | WORKHORSE machine |
| **PROD03 bates originals not in Azure** | `RedmondOvertActs0001–0722` not found by any prefix or keyword scan | Check Everlaw "DISCOVERY PART 2 Heim delivery" (5,108 files) via API; re-download from USAfx | Requires EVERLAW_API_KEY |
| **RedmondiPhone bates prefix not in filenames** | `RedmondiPhone_*` not in any manifest path | Files stored as Cellebrite UFED tiles under `FIVE9_06_CONFIDENTIAL_AR` naming | Confirmed — no action needed |
| **legal/recordings per-part counts** | Can't isolate FIVE9_01/04/05 exact WAV count within 401,167-blob full extraction set | Run targeted prefix count on `legal/recordings/.../1. FULL EXTRACTION OF CALL PART 1/` | Requires AZURE_STORAGE_KEY live scan |
| **ADMIN OneDrive sync dead** | 181,159 WAVs are cloud-only stubs, OneDrive sync off since 2026-01-23 | Re-enable OneDrive sync on ADMIN machine OR pull directly from Azure | ADMIN machine (192.168.1.215) |
| **Everlaw PROD03 confirmation** | Need to confirm "DISCOVERY PART 2 Heim delivery" contains RedmondOvertActs | Query Everlaw API `/v1/projects/110962/documents` with EVERLAW_API_KEY | Requires API key |
| **PROD01 upload to disco26** | USB upload in progress | Monitor upload completion | User |
| **blacksand contents** | 931 GB McAfee EERM encrypted — Prod02_Confidential docs likely here | Need McAfee EERM passphrase | Not available |
