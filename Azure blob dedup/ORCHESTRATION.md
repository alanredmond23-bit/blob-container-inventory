# Blob dedup orchestration — 4 agents + overseer

**Run ID:** `dedup-2026-05-16`  
**Branch:** `cursor/azure-blob-dedup-233a`  
**Goal:** `MASTER_DEDUP_MANIFEST.csv` containing **only** `PROVEN_EXACT` / `PROVEN_EXACT_COMPUTED` delete rows.

---

## Overseer checklist

- [ ] Create branch `cursor/azure-blob-dedup-233a`
- [ ] Commit skill + scripts
- [ ] Launch AG-1..AG-4 in parallel
- [ ] Collect artifacts under `artifacts/dedup/<agent>/`
- [ ] Merge → `artifacts/dedup/MASTER_DEDUP_MANIFEST.csv`
- [ ] Reject any agent output missing `certainty` column or with `SUSPECT`
- [ ] Push + PR with manifest summary (counts, bytes reclaimable, zero guesses)

---

## AG-1 INVENTORY

**Inputs:** `Azure blob dedup/policies/blob-inventory-dedup.json`  
**Tasks:**
1. Ensure destination container `inventory-reports` exists
2. Document `az storage account blob-inventory-policy` create/update (or Portal)
3. Poll `BlobInventoryPolicyCompleted` / latest manifest URL
4. Download newest CSV to `artifacts/dedup/ag1/inventory_latest.csv`

**Done when:** `inventory_latest.csv` exists OR blocker logged (no az CLI → use Portal + manual download path)

---

## AG-2 ANALYZER

**Inputs:** `artifacts/dedup/ag1/inventory_latest.csv` (or sample CSV for test)  
**Tasks:**
1. Run `python3 scripts/blob_dedup_from_inventory.py --help`
2. Run analyzer on inventory file → `artifacts/dedup/ag2/`
3. Add/run `scripts/test_blob_dedup.py` with synthetic CSV (two rows same MD5+length)

**Done when:** `proven_exact_groups.jsonl` + `delete_candidates.csv` exist; unit test passes

---

## AG-3 SCANNER

**Inputs:** `AZURE_STORAGE_ACCOUNT`, `AZURE_STORAGE_KEY`  
**Tasks:**
1. Priority containers: `gmail-takeout`, `ice-cold-triage`, `triage`, `benfranklin-dashboard`
2. Run `blob_hash_scan_sdk.py --containers ... --verify-bytes`
3. Write `artifacts/dedup/ag3/proven_exact_computed.jsonl`

**Done when:** Priority containers scanned; every group has matching SHA-256 (and length)

---

## AG-4 MANIFEST

**Inputs:** `artifacts/dedup/ag2/*`, `artifacts/dedup/ag3/*`  
**Tasks:**
1. Merge proven groups; dedupe by `(md5_or_sha256, length)`
2. Apply canonical selection rules from SKILL.md
3. Emit `MASTER_DEDUP_MANIFEST.csv` + `SUMMARY.md` (counts only, no secrets)

**Done when:** Master manifest ready for human RED-zone approval

---

## Handoff protocol

Each agent writes `artifacts/dedup/<agN>/STATUS.json`:

```json
{
  "agent": "AG-2",
  "status": "complete|blocked|failed",
  "outputs": ["path1", "path2"],
  "proven_exact_groups": 0,
  "delete_candidates": 0,
  "bytes_reclaimable": 0,
  "errors": []
}
```

Overseer reads all STATUS files before merge.

---

## 100% certainty gate (overseer)

Before a row enters `MASTER_DEDUP_MANIFEST.csv`:

```python
assert certainty in ("PROVEN_EXACT", "PROVEN_EXACT_COMPUTED")
assert content_length > 0
assert md5_or_sha256  # non-empty hex
# For PROVEN_EXACT: Azure Content-MD5 present on all members of group
# For PROVEN_EXACT_COMPUTED: byte verify passed
```

**Forbidden:** size-only, name-only, prefix-count, org-map "likely duplicate" without hash proof.
