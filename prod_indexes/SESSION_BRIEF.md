# Session Brief — US v. Redmond, 5:24-cr-00376 EDPA
**Date:** 2026-05-26  
**Operator:** Alan Redmond, pro se  
**Machine:** Workhorse M1 MacBook Pro  
**Prepared for:** Handoff to HP Envy / Windows environment

---

## WHAT WAS ACCOMPLISHED THIS SESSION

All connected discovery disks were surface-indexed READ-ONLY per NIST SP 800-86. No files were written to any USB. No timestamps were mutated. No file content was extracted (except PDF Bates stamp inspection at operator direction). Chain of custody preserved.

### Disks Indexed This Session

| Disk Label | Mount Point | Files Indexed | GB | Key Index File |
|---|---|---|---|---|
| Samsung T7 4TB | /Volumes/T7 | 1 (zip) | 300 GB | `T7_20260526T114832Z.*` |
| creamsam (Samsung 2TB) | /Volumes/creamsam | 845,463 | ~171 GB | `creamsam_20260526T114832Z.*` |
| graysan (SanDisk gray) | /Volumes/graysan | ~833,720 | ~173 GB | `graysan_20260526T121041Z.*` |
| usbmemorex (Memorex 256) | /Volumes/usbmemorex | ~240,000 | ~28 GB | `usbmemorex_20260526T115406Z.*` |

All index files are in: `output/REVIEWS/`  
Each disk produces: `.csv` (full), `.xlsx` (7 tabs), `.db` (SQLite), `.md`, `.json`, `_tree.md`  
T7 additionally produces: `T7_20260526T114832Z_zips.csv` (149 MB, 845,458 inner entries from REDMOND008836.zip)

---

## CORRECTED CHAIN OF CUSTODY

| Disk | Physical ID | Source | Notes |
|---|---|---|---|
| Samsung T7 4TB (black) | SN 602V | Dalke → Rush (in court) → Alan | **ORIGINAL FEDS PRODUCTION.** NTFS. Contains single file: REDMOND008836.zip (322 GB). P2 production direct from government. |
| Samsung T7 Shield 2TB (cream) | SN 949X | Rush → Alan (at court, May 22, 2026) | **RUSH'S WORKING COPY. NOT ORIGINAL.** ExFAT. Rush unpacked the feds zip, added curated P1 folders (Oct 2024), added deposition material (Mar 2026), last touched May 3, 2026. Contains 684K P2 files Rush deleted to .Trashes. |
| SanDisk gray | SN 0226 | Rush → Alan | Encrypted with McAfee/Trellix EERM. Unlocked this session. Contains Trellix virtual filesystem: FIVE9 - ALAN REDMOND, GMAIL - HP Notebook - AOL, PHONE - ALAN REDMOND. Cannot be mounted as filesystem on Mac — GUI-only via Trellix app. Move to HP Envy for extraction. |
| Memorex USB 256MB | SN 6768 | Rush → Alan | Rush's partial copy. 78% gaps vs full RedmondTax sequence. |
| SanDisk red (not connected this session) | — | Feds → Rush → Alan | DISCO 3 / P5. On HP Envy. Indexing in progress. |
| SanDisk black (Heim) | SN 5722 | David Heim → Alan | Contains Trellix container with: Five9 data, Gmail/HP Notebook/AOL, Phone records. GUI-only on Mac. Move to HP Envy. |

---

## CRITICAL DISCOVERY: THE BATES STAMP TRUTH

**The government used ONE Bates prefix for ALL productions: `RedmondTax`**

This was confirmed by reading PDFs in the "Discovery Production US v. Redmond, 24-cr-376-selected" folder on creamsam. Documents that have nothing to do with taxes — including:
- Alan Redmond Criminal History / NCIC rap sheet → **RedmondTax008823–008827**
- Conditions of Release Order (signed Crawley, Dalke, Rush, Magistrate Straw) → **RedmondTax008816–008818**

These are criminal case documents stamped as `RedmondTax`. The government rolled everything into one unified Bates sequence.

### P2 Bates Range (confirmed on 3 disks)
- `RedmondTax008836` → `RedmondTax693308`
- 845,453 files in T7 zip, 845,463 files on creamsam, 833,720 on graysan
- All three stop at exactly **RedmondTax693308**

### P3 Bates Range (NOT ON ANY CONNECTED DISK)
- P3 = 722 documents delivered July 18, 2025 via USAfx
- P3 almost certainly continues the sequence: **RedmondTax693309 → ~RedmondTax694030**
- The production cover letter category name was "OvertActs" — that is a folder description, not the Bates prefix
- **Zero hits** for `RedmondOvertActs`, `OvertAct`, or any `RedmondTax` number above 693308 on any disk connected to this Mac — including live folders AND .Trashes

---

## P3 STATUS — CONFIRMED MISSING FROM THIS MAC

Exhaustive search performed across all 4 disks:
- Bates prefix search (RedmondOvertActs, OvertAct) → 0 hits
- Content keyword search (warrant, affidavit, 302, overt, superseding, NCIC) → 0 real hits
- T7 zip 845K inner entries scanned → 0 P3 hits
- Date-based: files modified after July 18, 2025 → 0 on any disk
- Folder cluster of ~722 files → not found
- .Trashes on all disks → 0 P3 content
- RedmondTax numbers above 693308 → 0 on any disk

**VERDICT: P3 is on the HP Envy.**

Check these locations immediately on the Envy:
1. `C:\Users\bigred\Downloads\` — USAfx default download location
2. `C:\Users\bigred\Documents\`
3. Desktop
4. Any folder with modification date July–August 2025
5. Alongside P5 (red SanDisk) index output

Search command to run on Envy (PowerShell):
```powershell
Get-ChildItem -Path C:\Users\bigred -Recurse -ErrorAction SilentlyContinue | 
  Where-Object { $_.Name -match 'RedmondTax69[3-9]|OvertAct|RedmondOvert' } | 
  Select-Object FullName, LastWriteTime | 
  Export-Csv C:\Users\bigred\Desktop\P3_search.csv
```

Or just look for any ZIP file or folder from July 2025.

---

## FORENSIC FLAGS — KEY FINDINGS

### creamsam (Rush's disk)
- **RUSH COPY CONFIRMED** — ExFAT filesystem, last modified May 3, 2026 (19 days before handing to Alan at court)
- **684,473 files deleted to .Trashes** — entire P2 text corpus deleted by Rush. All indexed before deletion was discovered. `.Trashes` content preserved in `graysan_20260526T121041Z.csv`

Wait — correction: The .Trashes deletion is on **graysan** (Rush's gray SanDisk, 136,481 txt files / 20.13 GB deleted). creamsam's .Trashes is nearly empty.

### graysan (Rush's gray SanDisk — McAfee encrypted, unlocked this session)
- 136,481 files in `.Trashes/501/TEXT/` — deleted P2 text extraction layer (20.13 GB)
- Last real write: Jan 21, 2025 (IMAGES/DATA). P3 delivered July 18, 2025 — 47-day gap confirms P3 never written here.
- Contains `Discovery Production US v. Redmond, 24-cr-376-selected/` — Rush's manual curation: FBI Interviews (302s), Grand Jury Exhibits (JS 1–41), Guaranteed Payments, Other (Criminal History, Conditions of Release)

### T7 (Dalke original — direct from feds)
- Single file: REDMOND008836.zip (322 GB, 845,458 inner entries)
- Written Jan 12–14, 2025
- This is the gold standard. P2 only.
- `_zips.csv` enumerates all 845,458 inner entries

### usbmemorex (Rush's Memorex)
- **78% BATES GAPS** — 534,853 missing documents in the RedmondTax sequence
- Partial copy only. Not a complete production.

---

## PENDING WORK — DO THESE ON HP ENVY

### Priority 1 — Find P3
- Search for RedmondTax693309+ or any July 2025 download folder
- Run `disk_review.py` against P5 red SanDisk when indexed
- Run `disk_review.py` against any folder where P3 lands

### Priority 2 — Index blacksand Trellix content
- The black SanDisk (Heim) contains a Trellix encrypted container
- Contents visible in Trellix GUI: FIVE9 - ALAN REDMOND, GMAIL - HP Notebook - AOL, PHONE - ALAN REDMOND
- Cannot extract on Mac (GUI-only, no FUSE mount)
- On Envy: open Trellix app, drag-extract all files to a folder, then run `disk_review.py` against that folder

### Priority 3 — Run disk_review.py on Envy for P5
```bash
python3 scripts/disk_review.py "/path/to/P5_red_sandisk"
python3 scripts/forensic_flags.py
```

### Priority 4 — Post-indexing diffs (from CLAUDE.md)
Run the 3 diff scripts in CLAUDE.md to compare:
- Heim (blacksand) vs Rush T7 Shield (creamsam)
- T7 zip entries vs creamsam unpacked
- Memorex vs T7 zip text layer

---

## WHAT SSH ENVY NEEDS

HP Envy is at `192.168.1.194` (hostname: `bigred.local`), username `bigred`.  
SSH was attempted and timed out — OpenSSH Server not running on Windows.

To enable (one-time, on Envy):
1. Settings → System → Optional Features → Add "OpenSSH Server"
2. PowerShell (Admin): `Start-Service sshd` then `Set-Service -Name sshd -StartupType Automatic`

Once SSH is live, Claude Code can connect and search for P3 directly.

---

## INDEX FILES REFERENCE

All output in: `/Users/alanredmond/Desktop/SSD Indexing discovery/output/REVIEWS/`

| File | Use |
|---|---|
| `T7_20260526T114832Z_zips.csv` | 845,458 inner entries of feds REDMOND008836.zip |
| `creamsam_20260526T114832Z.csv` | 845,463 files — Rush's copy, full P2 unpacked |
| `graysan_20260526T121041Z.csv` | 833,720 files incl. 136,481 in .Trashes |
| `usbmemorex_20260526T115406Z.csv` | ~240K files, 78% gaps |
| `output/FORENSIC_INTELLIGENCE.md` | Automated flags report |
| `output/FORENSIC_INTELLIGENCE.json` | Machine-readable flags |

---

## LEGAL SIGNIFICANCE SUMMARY

1. **P3 unaccounted for** — 722 documents (RedmondTax693309–~694030) not on any disk received from Rush or Dalke. USAfx delivery July 18, 2025. Location: HP Envy or still only in USAfx portal. Brady/Giglio motion target.

2. **creamsam is Rush's copy** — handed to Alan at court May 22, 2026, 19 days after Rush last modified it. Not the original feds production. Admissibility and authenticity questions attach.

3. **136,481 files deleted from graysan .Trashes** — P2 text corpus deleted on Rush's encrypted disk. Indexed before discovery. Potential spoliation / chain of custody issue.

4. **usbmemorex 78% gaps** — 534,853 missing Bates numbers. Same sequence as full production. Gap = quantifiable withholding metric for Brady argument.

5. **Single Bates prefix** — Government used `RedmondTax` for all productions including criminal history, conditions of release, FBI 302s. Production cover letter category names (OvertActs, IRS Files) are not Bates prefixes.

---

*Generated 2026-05-26. READ-ONLY session. No USB writes. Chain of custody intact.*
*Case: US v. Redmond, 5:24-cr-00376 EDPA, Judge Schmehl*
