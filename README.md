# redmond-overlord

Azure VM infrastructure and implementation plans for the Menagerie platform.

## Structure

```
repos/                           # Merged index / inventory repos (see repos/README.md)
  INDEXES/                       # Azure org map (xlsx)
  FINALINDEX2027/                # Blob + Workhorse inventory
  azure-blob-file-system/        # Blob/files mirror scripts (same lineage as FINALINDEX2027)
triage/                          # March 2026 -- Full VM implementation package
  MENAGERIE_FINAL_MASTER.pdf     # Master document (20 pages)
  MENAGERIE_VM_IMPLEMENTATION_PLAN.pdf  # V1 iteration
  predictive-wall-clock.html     # Interactive estimation tool
  CLAUDE.md                      # Drop-in rules for Claude Code
  setup.sh                       # One-run VM provisioning script
  TRANSCRIPT.md                  # Session decision log
  README.md                      # Folder guide
  build_final_master.py          # PDF generator (ReportLab)
  build_plan.py                  # V1 PDF generator
```

## Quick Start

- **Blob indexes (10M-row Alansinv + maps):** `artifacts/INDEX.md`
- Index and inventory tools: `repos/README.md`
- Azure blob dedup (100% MD5/SHA-256): `Azure blob dedup/SKILL.md` → `artifacts/dedup/MASTER_DEDUP_MANIFEST.csv`
- VM deployment: `triage/README.md`

---

Digital Principles Corp | Internal
