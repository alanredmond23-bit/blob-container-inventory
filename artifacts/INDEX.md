# Blob & inventory indexes (main branch)

Account: see `AZURE_STORAGE_ACCOUNT` / `repos/azure-blob-file-system/config.example.env` (container tree counts in `AZURE_BLOB_INVENTORY.md`).

## Primary — per-blob file list (~10.4M rows)

| File | Rows (approx) | Size |
|------|---------------|------|
| `artifacts/dedup/ag1/Alansinv_1000000_0.csv` | 8.37M | ~2.0 GiB |
| `artifacts/dedup/ag1/Alansinv_1000000_1.csv` | 1.99M | ~670 MiB |

**Total ~10,366,934 blob rows** (Azure inventory export, May 2026). Stored via **Git LFS**.

Re-download if missing:

```bash
export AZURE_STORAGE_ACCOUNT="$AZURE_STORAGE_ACCOUNT" AZURE_STORAGE_KEY='…'
bash scripts/download_alansinv_inventory.sh
```

## Dedup manifest

| File | Notes |
|------|--------|
| `artifacts/dedup/MASTER_DEDUP_MANIFEST.csv` | ~56k exact-duplicate delete candidates |

## Folder-count indexes (no per-file paths)

| File | Notes |
|------|--------|
| `repos/azure-blob-file-system/AZURE_BLOB_INVENTORY.md` | Container → prefix blob counts |
| `repos/FINALINDEX2027/AZURE_BLOB_INVENTORY.md` | Same snapshot (duplicate import) |
| `repos/azure-blob-file-system/workhorse/WORKHORSE_INVENTORY.md` | Local Mac workhorse counts |
| `repos/INDEXES/AZURE_ORGANIZATION_MAP_MASTER.xlsx` | Organization map |
| `triage/blob_container_sizes_full.tsv` | Container size rollup |

## Generated from Alansinv (gitignored — regenerate locally)

```bash
python3 scripts/blob_inventory_hierarchy_report.py
python3 scripts/export_kanban_data.py
python3 scripts/build_blob_catalog_sql.py
```

Outputs under `artifacts/catalog/` (BLOB_HIERARCHY, kanban_data, blob_catalog_load.csv.gz, etc.).
