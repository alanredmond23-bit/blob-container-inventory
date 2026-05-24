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
4. Drag cards into domains (DEVOPS, FINANCE, LEGAL matters, **DUP LIKELY**, COLD) — L1/L2/L3 via `+L1` buttons
5. **Hard-refresh** (`Ctrl+Shift+R`) after updates — placements stay in browser (`blob_kanban_board_v2`)
6. **Export** or drop `blob_homes_assignments.json` in this folder → auto-loads on refresh
7. **Triage seed:** `python3 scripts/seed_kanban_from_triage.py` → `kanban_board_seed.json` (legal matters from Redmond register)

**Register your placements for the agent:**

```bash
python3 scripts/register_kanban_homes.py ~/Downloads/blob_homes_assignments.json
```

Regenerate hierarchy:

```bash
python3 scripts/blob_inventory_hierarchy_report.py
```
