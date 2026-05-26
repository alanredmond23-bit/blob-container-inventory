# azdedup — Implementation Plan

Production CLI for hyperscale Azure Blob deduplication (10M+ blobs).  
Spec source: user CLI spec (May 2026).  
Target account scale: **~10.37M rows** in `artifacts/dedup/ag1/Alansinv_*.csv` on `main`.

---

## 1. Goals & non‑negotiables

| Principle | Implementation |
|-----------|----------------|
| Incremental | Skip blobs whose **ETag** unchanged and `dedup_stage` already set |
| State on blobs | **Blob Index Tags** (authoritative); optional local checkpoint JSONL for worker resume only |
| Minimal I/O | `scan` → metadata only; `partial` → 2× read window; `full` → only collision groups |
| Delete last | `cleanup` never default; requires `--confirm` for delete |
| Parallel | Async workers sharded by container + prefix + size bucket |
| Crash-safe | Idempotent tag writes; per-shard progress files under `artifacts/dedup/azdedup/` |

**Certainty ladder** (inherits from `Azure blob dedup/SKILL.md`):

- `PROVEN_EXACT` — same Content-MD5 + Content-Length (from inventory or blob properties)
- `PROVEN_EXACT_COMPUTED` — SHA-256 over full bytes matches
- `PROVEN_PARTIAL` — same `hash_fast` + size (candidates for full stage only)
- Never delete on partial alone

---

## 2. Relationship to existing repo

| Existing | Role in azdedup |
|----------|-----------------|
| `artifacts/dedup/ag1/Alansinv_*.csv` | **Bootstrap** for `scan --source inventory` (no live list of 10M on day 1) |
| `scripts/blob_dedup_from_inventory.py` | Port **canonical pick** + MD5 grouping → `dedup --stage canonical` policy module |
| `scripts/blob_hash_scan_sdk.py` | Port **SHA-256 streaming** → `dedup --stage full` |
| `scripts/blob_dedup_inventory_stream.py` | Shard pattern → worker pool model |
| `scripts/execute_dedup_deletes.py` | Reference for **cleanup --mode move/delete** (expand paths, jsonl audit log) |
| `artifacts/dedup/MASTER_DEDUP_MANIFEST.csv` | **Legacy export**; azdedup `report` supersedes for ongoing ops |

**Deprecation path:** Keep `scripts/*` until azdedup reaches parity; add thin wrappers that call `azdedup` subcommands.

---

## 3. Repository layout

```
azdedup/
├── pyproject.toml              # entry point: azdedup = azdedup.cli:app
├── README.md                   # quickstart + tag schema
├── Dockerfile
├── deploy/
│   └── containerapp.yaml       # Azure Container Apps job (optional phase 4)
├── src/azdedup/
│   ├── __init__.py
│   ├── __main__.py             # python -m azdedup
│   ├── cli.py                  # Typer/Click root: scan|dedup|verify|report|cleanup
│   ├── config.py               # defaults, env, policy YAML loader
│   ├── tags.py                 # Index tag schema read/write/merge (authoritative)
│   ├── azure_client.py         # BlobServiceClient factory (key | MI | conn string)
│   ├── inventory.py            # Alansinv CSV stream parser (reuse parse_blob_row)
│   ├── commands/
│   │   ├── scan.py
│   │   ├── dedup.py            # partial | full | canonical sub-stages
│   │   ├── verify.py
│   │   ├── report.py
│   │   └── cleanup.py
│   ├── pipeline/
│   │   ├── partial_hash.py     # xxhash64 first/last N bytes
│   │   ├── full_hash.py        # sha256 stream
│   │   ├── canonical.py        # oldest | shortest_path | container_priority
│   │   └── incremental.py    # etag/stage filter
│   ├── workers/
│   │   ├── pool.py             # asyncio + semaphore concurrency
│   │   ├── shard.py            # container × prefix × size_bucket
│   │   └── checkpoint.py       # artifacts/dedup/azdedup/shard_<id>.jsonl
│   └── models/
│       ├── blob_ref.py         # container, name, etag, size, tags
│       └── stats.py            # counters for report
└── tests/
    ├── conftest.py             # mock blob client
    ├── test_tags.py
    ├── test_partial_hash.py
    ├── test_canonical.py
    ├── test_scan_inventory.py
    └── fixtures/
        └── mini_inventory.csv
```

**Artifacts output** (gitignored except summaries):

```
artifacts/dedup/azdedup/
├── checkpoints/          # shard progress (resume)
├── reports/              # report JSON snapshots
├── verify/               # verify sample results
└── cleanup/              # dry-run manifests
```

---

## 4. Index tag schema (authoritative)

Azure limits: **10 tags/blob**, tag key ≤ 128 chars, value ≤ 256 chars ([docs](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-manage-find-blobs)).

| Tag key | Values | Notes |
|---------|--------|-------|
| `dedup_stage` | `none` \| `meta` \| `partial` \| `full` \| `canonical` | State machine |
| `size` | decimal bytes | Denormalized for tag queries |
| `ext` | extension without dot | From blob name |
| `hash_fast` | 16-char hex xxhash64 | Partial stage |
| `hash_full` | 64-char hex sha256 | Full stage (optional until full) |
| `canonical` | `true` \| `false` | Set at canonical stage |
| `canonical_id` | uuid4 hex | Groups duplicates |
| `dedup_etag` | blob ETag at last process | Incremental skip |

**Overflow strategy:** If approaching 10 tags, drop `ext` first; never drop `dedup_stage`, `size`, `hash_fast`, `canonical`.

**Query:** Use `find_blobs_by_tags` where supported; else list-by-prefix + filter tags in worker (expected at 10M scale).

---

## 5. Command specifications (implementation mapping)

### 5.1 `azdedup scan`

```bash
azdedup scan \
  --account "$AZURE_STORAGE_ACCOUNT" \
  --containers c1,c2 | all \
  --prefix optional/path/ \
  --concurrency 64 \
  --source live|inventory \
  --inventory-path artifacts/dedup/ag1/Alansinv_1000000_*.csv
```

**Behavior:**

1. Enumerate blobs (live `list_blobs` **or** stream inventory CSV).
2. For each blob, if `dedup_etag == current ETag` and `dedup_stage >= meta` → skip.
3. Else `set_blob_tags`: `dedup_stage=meta`, `size`, `ext`, `dedup_etag`.
4. Emit checkpoint line + increment stats.

**Guarantee:** Zero content reads.

**MVP shortcut:** `--source inventory --dry-run-tags` writes a local `meta.jsonl` without Azure writes (dev/test); `--apply-tags` pushes to Azure.

---

### 5.2 `azdedup dedup`

```bash
azdedup dedup --stage partial|full|canonical \
  --account ... --containers all \
  --read-bytes 1048576 \
  --concurrency 32 \
  --incremental
```

#### Stage `partial`

- Filter: `dedup_stage=meta` (or etag changed).
- Read range: `[0, read_bytes)` and `[size-read_bytes, size)` (handle `size < 2*read_bytes` overlap).
- `hash_fast = xxhash64(head + tail)`.
- Tags: `dedup_stage=partial`, `hash_fast`.

#### Stage `full`

- Build in-memory (or spill-to-disk) map: `(size, hash_fast) → [blob refs]`.
- Only groups with **count ≥ 2** proceed.
- Stream SHA-256 entire blob; tag `hash_full`, `dedup_stage=full`.
- Optional: use inventory Content-MD5 when present → promote to `PROVEN_EXACT` without full read.

#### Stage `canonical`

- Group by `hash_full` (or MD5) within size bucket.
- Policy (`--strategy oldest|shortest|container_priority|policy-file`).
- Port ranks from `blob_dedup_from_inventory.py` (`KEEP_CONTAINER_PRIORITY`, `DEPRIORITIZE_CONTAINERS`).
- Tags: `canonical=true|false`, `canonical_id=<uuid>` shared within group.
- **`--mark-only` default** — no deletes.

#### `--incremental`

Union of: missing stage tag, `dedup_etag` ≠ current ETag, or `--force-stage`.

---

### 5.3 `azdedup verify`

```bash
azdedup verify --sample-rate 0.001 --rehash full --account ...
```

- Sample blobs where `canonical=false` from duplicate groups.
- Recompute SHA-256; compare to `hash_full`.
- Output confidence: `1 - (mismatches / samples)`.
- Write `artifacts/dedup/azdedup/verify/<timestamp>.json`.

---

### 5.4 `azdedup report`

```bash
azdedup report --format table|json --group-by container|stage
```

Aggregates from:

1. Live tag scan (sampled) **or**
2. Inventory CSV + sidecar `artifacts/dedup/azdedup/reports/latest.json` from last full pass.

Fields: total blobs, unique (by hash_full), duplicates, reclaimable bytes (sum size where `canonical=false`), confidence from last verify.

---

### 5.5 `azdedup cleanup`

```bash
azdedup cleanup --mode tag-only|move|delete \
  --destination _duplicates/ \
  --dry-run \
  --confirm   # required for delete
```

| Mode | Action |
|------|--------|
| `tag-only` | Add tag `dedup_cleanup=pending` |
| `move` | Copy to dest container/prefix, verify, delete source (with audit jsonl) |
| `delete` | Hard delete non-canonical only; **requires `--confirm`** |

Reuse audit pattern from `execute_dedup_deletes.py` + `execute_delete_queue.py`.

---

## 6. Execution model

```
                    ┌─────────────┐
                    │   scan      │  metadata / inventory → tags(meta)
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │ dedup       │  partial → hash_fast
                    │  partial    │
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │ dedup full  │  collision groups only → hash_full
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │ dedup       │  canonical marks (no delete)
                    │  canonical  │
                    └──────┬──────┘
                           ▼
              ┌────────────┴────────────┐
              ▼                         ▼
       ┌─────────────┐           ┌─────────────┐
       │   verify    │           │   report    │
       └─────────────┘           └─────────────┘
                           ▼
                    ┌─────────────┐
                    │  cleanup    │  optional, human-gated
                    └─────────────┘
```

**Sharding key:** `{container}/{prefix_shard}/{size_bucket}` where `size_bucket = floor(log2(size))`.

**Worker contract:** Each worker processes one shard; checkpoint after N blobs; safe to kill -9.

**Event Grid (phase 4):** `BlobCreated` → enqueue shard for incremental `dedup --incremental` on prefix.

---

## 7. Dependencies

```toml
# pyproject.toml
dependencies = [
  "azure-storage-blob>=12.24.0",
  "azure-identity>=1.15.0",
  "typer>=0.12.0",
  "xxhash>=3.4.0",
  "rich>=13.0.0",          # table report
  "pydantic>=2.0.0",
]
optional = { parquet = ["pandas", "pyarrow"] }
```

---

## 8. Phased delivery (Cursor task breakdown)

### Phase 0 — Scaffold (1 session)

| # | Task | Files |
|---|------|-------|
| 0.1 | Create package + `pyproject.toml` entry point | `azdedup/pyproject.toml` |
| 0.2 | CLI skeleton with `--version` | `cli.py`, `__main__.py` |
| 0.3 | Azure client + config from env | `azure_client.py`, `config.py` |
| 0.4 | Tag schema helpers + unit tests | `tags.py`, `tests/test_tags.py` |
| 0.5 | Update `artifacts/INDEX.md` + root README link | docs |

**Done when:** `pip install -e azdedup && azdedup --help` works.

---

### Phase 1 — scan (MVP) ✅

| # | Task | Files |
|---|------|-------|
| 1.1 | Inventory CSV streamer (reuse `parse_blob_row`) | `inventory.py` ✅ |
| 1.2 | `scan --source inventory --dry-run-tags` → jsonl | `commands/scan.py` ✅ |
| 1.3 | `scan --apply-tags` with concurrency pool | `workers/pool.py` ✅ |
| 1.4 | Incremental etag skip | `pipeline/incremental.py` ✅ |
| 1.5 | Integration test on `tests/fixtures/mini_inventory.csv` | `tests/test_scan_inventory.py` ✅ |

**Done:** 18 unit tests pass; dry-run + live list paths; apply-tags with checkpoint.

---

### Phase 2 — dedup partial + full ✅

| # | Task | Files |
|---|------|-------|
| 2.1 | xxhash partial reader (range download) | `pipeline/partial_hash.py` ✅ |
| 2.2 | `dedup --stage partial` | `commands/dedup.py` ✅ |
| 2.3 | Collision grouper | `pipeline/full_hash.py` ✅ |
| 2.4 | SHA-256 full hash + MD5 short-circuit | `pipeline/full_hash.py` ✅ |
| 2.5 | `dedup --stage full` | `commands/dedup.py` ✅ |

**Done:** 40 unit tests pass; partial xxhash + full SHA-256 on collision groups only.

---

### Phase 3 — canonical + report + verify ✅

| # | Task | Files |
|---|------|-------|
| 3.1 | Port canonical policy | `pipeline/canonical.py` ✅ |
| 3.2 | `dedup --stage canonical` (mark-only via tags) | `commands/dedup.py` ✅ |
| 3.3 | `report --format table` | `commands/report.py` ✅ |
| 3.4 | `verify --sample-rate` | `commands/verify.py` ✅ |
| 3.5 | One-command pipeline script | `scripts/azdedup_full_pipeline.sh` ✅ |

**Done:** 45+ unit tests; canonical dry-run/apply-tags, report from inventory or jsonl, verify spot-check.

---

### Phase 4 — cleanup + hyperscale hardening

| # | Task | Files |
|---|------|-------|
| 4.1 | `cleanup --dry-run` manifest csv | `commands/cleanup.py` |
| 4.2 | Move mode with audit jsonl | `commands/cleanup.py` |
| 4.3 | Shard orchestrator for 10M (`--shard-id`, `--shard-count`) | `workers/shard.py` |
| 4.4 | Dockerfile + ACA job YAML | `Dockerfile`, `deploy/containerapp.yaml` |
| 4.5 | Runbook: bootstrap from Alansinv then incremental live | `azdedup/README.md` |

**Done when:** Sharded scan of full inventory completes with checkpoints; cleanup dry-run matches legacy manifest counts order-of-magnitude.

---

## 9. Bootstrap runbook (10M account)

```bash
# 0. Install
pip install -e azdedup/

# 1. Join split inventory part 0 if needed
bash scripts/cat_alansinv_part0.sh

# 2. Meta pass from inventory (fast, can dry-run first)
azdedup scan --source inventory \
  --inventory-path 'artifacts/dedup/ag1/Alansinv_1000000_*.csv' \
  --account "$AZURE_STORAGE_ACCOUNT" \
  --containers all \
  --concurrency 64 \
  --apply-tags

# 3. Pipeline
azdedup dedup --stage partial --containers all --read-bytes 1048576 --concurrency 32
azdedup dedup --stage full --containers all --concurrency 16
azdedup dedup --stage canonical --strategy oldest --apply-tags
azdedup verify --sample-rate 0.001
azdedup report --format table

# 4. Human review, then optional cleanup
azdedup cleanup --mode move --destination _duplicates/ --dry-run
```

For **10M tags**, expect Phase 1–2 to run as **N parallel ACA jobs** (`--shard-id 0..31`).

---

## 10. Testing strategy

| Layer | What |
|-------|------|
| Unit | xxhash, tag merge, canonical pick, etag incremental |
| Fixture | 50-row inventory CSV with known duplicate MD5 pairs |
| Integration | Azurite or mocked `BlobServiceClient` |
| Soak | 100k rows from Alansinv shard locally (no Azure) |
| Prod gate | `verify` confidence ≥ 99.999% before any `cleanup --mode delete` |

---

## 11. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Index tag API rate limits | Batch shards; exponential backoff; checkpoint |
| `find_blobs_by_tags` not filterable enough | List by prefix + client filter |
| xxhash false positive | `full` stage mandatory before canonical |
| 2GB Git LFS inventory split | Already handled; inventory path glob in CLI |
| Tag write cost at 10M | `--source inventory` meta pass tags only changed etags |
| Legacy MD5 missing | Inventory Content-MD5 + full SHA-256 path |

---

## 12. Success criteria

- [ ] Single CLI entry point replaces 5+ ad-hoc scripts for steady-state ops
- [ ] Full pipeline resumable after interrupt on 10M scale
- [ ] Zero content reads on scan; &lt;2MB read per blob on partial (typical)
- [ ] No delete without explicit `--confirm`
- [ ] Report reclaimable TB within 5% of legacy `MASTER_DEDUP_MANIFEST` on same inventory generation

---

## 13. Immediate next Cursor session

**Start Phase 0 + Phase 1.1–1.2** in branch `cursor/azdedup-cli-233a`:

1. Create `azdedup/` scaffold per §3  
2. Implement `tags.py` + `inventory.py`  
3. `azdedup scan --source inventory --dry-run-tags` writing jsonl  
4. Open PR to `main` with plan doc + scaffold only (no production tagging until reviewed)
