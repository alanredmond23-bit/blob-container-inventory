# PROD03 — RedmondOvertActs 0001–0722

**Status:** Not uploaded as a labeled set. **Do not search by filename.**

Bates are stamped **top-right or bottom-right** on pages (`RedmondOvertActs 0001`–`0722`), not in blob names.

## Correct hunt

1. `python3 scripts/prod03_document_census.py` — all scannable docs, priority Heim/superseding paths
2. `python3 scripts/prod03_bates_corner_ocr.py` — corner OCR on downloaded PDFs/images

See `docs/PROD03_BATES_SCAN_PLAN.md`.

## Legacy filename scan (misleading)

- Distinct `RedmondOvertActs` in path: **0** (expected — wrong method)
- Heim disc path blobs: **3175**
- Heim delivery CSV copies: **7**
- `overt_act_matrix.json` in Superseding/output (download for crosswalk)
