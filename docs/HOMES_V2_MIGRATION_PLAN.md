# Homes v2 — six organized blob containers + catalog sheet

## What you are building

| Layer | Purpose |
|-------|---------|
| **Catalog sheet** (database table) | One row per blob (or per folder aggregate during planning): name, paths, sizes, dates, which *home* it belongs to, migration status |
| **6 new blob containers** | Physical homes that mirror your Kanban breakdown — not 200+ legacy containers |
| **Legacy storage** | Stays until copy-verify-delete; no big-bang cutover |

The six homes match your current board (excluding DELETE QUEUE):

| # | Container name | Kanban domain | ~assigned today (from export) |
|---|----------------|---------------|-------------------------------|
| 1 | `home-devops` | DEVOPS | 220 cards · ~0.08 TiB |
| 2 | `home-finance` | FINANCE | 22 cards · ~0.18 TiB |
| 3 | `home-legal` | LEGAL | 80 cards · ~1.49 TiB |
| 4 | `home-dup-likely` | DUP LIKELY | 48 cards · ~0.49 TiB (staging / review) |
| 5 | `home-cold` | COLD ARCHIVE | 115 cards · ~1.96 TiB |
| 6 | `home-organization` | ORGANIZATION | 66 cards · ~2.45 TiB |

**Do not** put delete-queue items into a seventh home — they stay in manifest + `DELETE_QUEUE` until executed, then gone.

---

## Cosmos vs SQL catalog vs something else?

### Recommendation: **Cloud SQL catalog** for the sheet (primary), **blob Parquet/CSV** as backup

| Option | Verdict | Why |
|--------|---------|-----|
| **Cosmos DB** | No | Wrong shape: you need tabular reports, filters, joins, Excel, 10M-row scans. Cosmos is for app documents at high RU, not a migration catalog. Cost and query pain at this scale. |
| **Managed SQL** | **Yes (primary)** | Use your existing cloud SQL instance. Tables, indexes, views, Power BI / Excel, SQL for “show me top 10 in home-legal”. Fits ~10M rows with proper indexing and bulk loads. |
| **PostgreSQL on app VM** | Good dev mirror | Same schema as managed SQL; use for FastAPI CRUD during build. Sync or treat managed SQL as prod catalog. |
| **Table Storage (key-value)** | Optional cheap index | Only if you need key-value lookups by `(home, path)` — not your main “sheet”. |
| **CSV / Parquet in blob** | Yes (artifact) | Nightly export from SQL for agents and offline tools; already matches inventory pipeline. |

**Cosmos** only makes sense later if you build a real-time app that reads *small* JSON docs per matter — not for the migration spreadsheet.

---

## Catalog sheet — table design (the “sheet”)

Core table: `blob_catalog` (one row per blob in inventory).

| Column | Type | Notes |
|--------|------|-------|
| `id` | BIGINT IDENTITY | Surrogate key |
| `source_container` | NVARCHAR(128) | Legacy container |
| `source_path` | NVARCHAR(1024) | Blob path |
| `content_length` | BIGINT | Bytes |
| `creation_time` | DATETIME2 | From inventory |
| `last_modified` | DATETIME2 | From inventory |
| `content_md5` | VARBINARY(16) NULL | When inventory has MD5 |
| `home_id` | NVARCHAR(32) | `devops`, `finance`, `legal`, `dup-likely`, `cold`, `organization` |
| `home_path` | NVARCHAR(512) | Target path inside `home-{home_id}` |
| `zone_path` | NVARCHAR(256) | Kanban zone e.g. `legal → bk-24-13093 → evidence` |
| `card_id` | NVARCHAR(256) | Kanban card id |
| `migrate_status` | NVARCHAR(32) | `mapped`, `queued`, `copied`, `verified`, `delete_legacy` |
| `dup_group_id` | NVARCHAR(64) NULL | Link to dedup manifest |
| `updated_at` | DATETIME2 | |

Views you will actually use:

- `v_home_summary` — blobs, bytes, min/max dates per `home_id`
- `v_zone_top10` — top 10 largest per zone (what SECTION_VIEWS does today)
- `v_migration_queue` — rows ready for AzCopy / server-side copy

SQL file: `schema/blob_catalog.sql`

---

## Inside each of the 6 new containers (folder standard)

Same layout everywhere so tools and humans never guess:

```
home-{domain}/
  _meta/
    README.json          # domain description, owner, retention
    manifest.json        # last catalog sync time, row counts
  {l2}/                  # e.g. hot-active, tax, bk-24-13093
    {l3}/                # e.g. evidence, discovery (legal only)
      {original_container}/
        {original_path}    # preserves provenance during migration
```

Example target path for a file today in `{legacy-container}/a/b/c.dat` assigned to legal → general-legal → discovery:

```
home-legal/general-legal/discovery/{legacy-container}/a/b/c.dat
```

After stabilization you may shorten paths; **phase 1 copies with provenance prefix** so nothing is ambiguous.

---

## Start-to-finish phases

### Phase 0 — Freeze taxonomy (1 session, no data move)

1. Confirm six `home-*` names and zone → `home_path` rules (from `blob_homes_assignments.json`).
2. Load catalog sheet: run `scripts/build_blob_catalog_sql.py` → CSV bulk load into managed SQL.
3. Review `v_home_summary` and fix mis-assigned cards in Kanban → re-export → reload delta.

### Phase 1 — Create containers + empty structure (cloud CLI)

```bash
# Set AZURE_STORAGE_ACCOUNT in your environment first
for h in devops finance legal dup-likely cold organization; do
  az storage container create --account-name "$AZURE_STORAGE_ACCOUNT" --name "home-$h" --auth-mode login
done
```

Upload `_meta/README.json` per container (script can generate from board export).

### Phase 2 — Build migration manifest (SQL → CSV)

- Query: `migrate_status = 'mapped'` and not in dup delete queue.
- Emit AzCopy / `start_copy_from_url` batch files per home (batch size 10k–50k paths).
- **Server-side copy only** — never pull 3 TiB through the VM.

### Phase 3 — Copy in waves

| Wave | Home | Rationale |
|------|------|-----------|
| 1 | `home-devops` | Smallest; validate pipeline |
| 2 | `home-finance` | Small; finance sensitivity |
| 3 | `home-dup-likely` | Staging; many may be deleted not copied |
| 4 | `home-legal` | Matter-critical; verify counts per matter |
| 5 | `home-cold` | Large but low churn |
| 6 | `home-organization` | Largest; last |

Per wave: copy → `migrate_status = copied` → spot-check counts vs inventory → `verified`.

### Phase 4 — Dedup + delete legacy

- Dup work stays in SQL + existing dedup manifests; deletes only after `verified` + your Kanban DELETE QUEUE export.
- When a legacy container is empty: soft-delete container or mark `archived-*` — **RED zone**, human approval.

### Phase 5 — App cutover (API VM)

- FastAPI resolves `home_id` + path from SQL, SAS points at `home-{domain}`.
- AI Search index per home or single index with `home_id` filter.

---

## What to do first (this week)

1. **Create the sheet** — deploy `schema/blob_catalog.sql` to managed SQL (or PG on VM).
2. **Run catalog builder** — `python3 scripts/build_blob_catalog_sql.py` (streams inventory + assignments).
3. **Open sheet** — SQL client / Excel / Power BI on `v_home_summary` and `v_zone_top10`.
4. **Create six containers** — Phase 1 CLI above.
5. **Pilot copy** — one small devops folder end-to-end before legal/organization waves.

---

## Cost / risk notes

- **Double storage** during migration (legacy + home-*): plan ~3 TiB peak until legacy deleted.
- **Managed SQL**: lower tiers may need scale-up for 10M-row bulk insert; consider loading via CSV to blob + bulk insert or batch 500k rows.
- **Do not** mirror dup-likely into `home-dup-likely` for everything — prefer delete or skip copy when `dup_group_id` says delete.

---

## Related repo artifacts

| File | Role |
|------|------|
| `schema/blob_catalog.sql` | Table + views |
| `scripts/build_blob_catalog_sql.py` | Build load files from inventory + Kanban |
| `artifacts/catalog/blob_homes_assignments.json` | Zone assignments source |
| `scripts/kanban_section_report.py` | HTML section review until SQL sheet is live |
