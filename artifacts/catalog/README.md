# Blob hierarchy catalog

Visual reports from the May 2026 `Alansinv` inventory CSV (~10.4M blobs).

| File | Use |
|------|-----|
| **BLOB_HIERARCHY.html** | Open in a browser — filterable table + expandable per-container folder trees |
| **BLOB_HIERARCHY.md** | Same data in Markdown (GitHub-friendly) |
| **BLOB_HIERARCHY_SUMMARY.json** | Machine-readable totals per container |

Regenerate:

```bash
python3 scripts/blob_inventory_hierarchy_report.py
```
