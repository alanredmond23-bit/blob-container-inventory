# Blob hierarchy catalog

Visual reports from the May 2026 `Alansinv` inventory CSV (~10.4M blobs).

| File | Use |
|------|-----|
| **BLOB_HIERARCHY.html** | Open in a browser — filterable table + expandable per-container folder trees (local only; gitignored) |
| **BLOB_HIERARCHY.md** | Same data in Markdown (local only; gitignored) |
| **BLOB_HIERARCHY_SUMMARY.json** | Machine-readable totals per container (local only; gitignored) |

## Kanban organizer (drag domains)

1. `python3 scripts/export_kanban_data.py`
2. Serve this folder: `python3 -m http.server 8765` (from `artifacts/catalog`)
3. Open **http://127.0.0.1:8765/KANBAN.html**
4. Drag cards into DEVOPS / FINANCE / LEGAL / COLD sub-zones → **Export homes JSON** when done

Regenerate hierarchy:

```bash
python3 scripts/blob_inventory_hierarchy_report.py
```
