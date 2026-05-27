# PROD03 — Redmond Overt Acts (document-first, corner Bates)

## Problem with filename search

Prior hunts used `RedmondOvertActs` in blob paths → **0 hits**. Operator confirms:

- Production is **not named** `RedmondOvertActs` on disk.
- **Bates numbers** (`RedmondOvertActs 0001`–`0722`) are **stamped on the page**, usually **top-right or bottom-right**.

Filename / inventory regex is the wrong primary signal.

---

## Two-phase approach

### Phase 1 — Scan all documents (inventory census)

**Script:** `python3 scripts/prod03_document_census.py`

- Walks full Alansinv (~10.37M rows).
- Lists every blob with a scannable extension: `pdf`, `tif`, `jpg`, `txt`, `docx`, etc.
- Tags **priority buckets** (still not production names):
  - `heim disc`, `03_heim disk`, `david heim`
  - `discovery_part_2`, `superseding`, `overt_act`
  - `raw discovery`, `natives/`, `text/`

**Outputs:**

- `artifacts/catalog/hunt/prod03/prod03_document_census.csv`
- `artifacts/catalog/hunt/prod03/prod03_census_summary.json`

### Phase 2 — Corner Bates OCR

**Script:** `python3 scripts/prod03_bates_corner_ocr.py`

1. Download priority PDFs/images from Azure (or use local copies).
2. For each page (first 3 pages), crop **four corners**; weight **top-right** and **bottom-right**.
3. OCR with Tesseract (`--psm 6` block mode).
4. Match: `Redmond\s*Overt\s*Acts?\s*0*(\d{1,4})` with **1 ≤ n ≤ 722**.

**Deps:**

```bash
sudo apt install -y tesseract-ocr
pip install pymupdf pillow pytesseract
```

**Outputs:**

- `prod03_bates_ocr_results.json`
- `prod03_bates_ocr_summary.json` → `distinct_bates_1_722`

---

## Supporting leads (not Bates proof)

| Lead | Role |
|------|------|
| `overt_act_matrix.json` in `legal-filings/.../Superseding/output/` | Internal matrix — download and map to blob paths |
| `DISCOVERY_PART_2_Heim_delivery.csv` (~4 MB) | Upload index — crosswalk to natives |
| Heim `FILES/TEXT/0001/RedmondTax*.txt` | OCR text sidecars (may reference wrong production prefix) |

---

## Success metric

| Metric | Target |
|--------|--------|
| Federal declared | **722** distinct Bates |
| Phase 1 | Complete document universe + priority queue |
| Phase 2 | **722** distinct IDs from corner OCR (not path regex) |

---

## What we stop doing

- ❌ `rg RedmondOvertActs` as primary PROD03 hunt
- ❌ Counting PROD03 “found” from filename regex in `production_hunt_worker.py`

## What we do instead

- ✅ Census all docs → OCR queue
- ✅ Corner stamp detection on PDF/TIF/JPG
- ✅ Merge into production scoreboard as `prod03_bates_ocr_summary.json`
