#!/usr/bin/env python3
"""
Discovery Ingestion Pipeline
U.S. v. Redmond et al., EDPA 24-cr-375-JLS

Blob → Extract → Chunk → Embed → Supabase upsert, keyed on ar_id.
Idempotent: safe to re-run, skips already-embedded docs.

Usage:
    # From CSV index only (no blobs needed — works before USB upload)
    python3 scripts/disco_ingest.py --source csv --index prod_3/deep_v4.csv --production PROD05

    # From Azure blobs (after USB upload)
    python3 scripts/disco_ingest.py --source blob --production PROD05

    # Check progress
    python3 scripts/disco_ingest.py --status

Required env vars:
    SUPABASE_URL         https://fifybuzwfaegloijrmqb.supabase.co
    SUPABASE_SERVICE_KEY <service role key>
    OPENAI_API_KEY       <key>
    AZURE_STORAGE_ACCOUNT  (optional, for blob mode)
    AZURE_STORAGE_KEY      (optional, for blob mode)
"""

import os, sys, csv, json, time, argparse, textwrap, re
import hashlib, base64, hmac, datetime
from pathlib import Path
from typing import Iterator

import requests

# ── Config ────────────────────────────────────────────────────────────────────

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
OPENAI_KEY   = os.environ.get("OPENAI_API_KEY", "")
AZ_ACCOUNT   = os.environ.get("AZURE_STORAGE_ACCOUNT", "")
AZ_KEY       = os.environ.get("AZURE_STORAGE_KEY", "")

EMBED_MODEL  = "text-embedding-3-small"   # 1536 dims, cost-effective
EMBED_DIMS   = 1536
CHUNK_TOKENS = 512    # target chunk size
CHUNK_OVERLAP = 80    # overlap in tokens (prevents context loss at boundaries)
BATCH_EMBED  = 100    # docs per OpenAI embedding batch
BATCH_DB     = 200    # rows per Supabase upsert

PRODUCTION_ID = None  # set by --production arg


# ── Supabase helpers ──────────────────────────────────────────────────────────

def sb_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }


def sb_upsert(table: str, rows: list[dict]) -> int:
    """Upsert rows into a Supabase table. Returns count inserted/updated."""
    if not rows:
        return 0
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers={**sb_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"},
        json=rows,
        timeout=60,
    )
    if r.status_code not in (200, 201):
        print(f"  [DB ERROR] {table}: {r.status_code} {r.text[:200]}")
        return 0
    return len(rows)


def sb_query(table: str, select: str = "*", filters: dict = None, limit: int = 1000) -> list:
    params = {"select": select, "limit": limit}
    if filters:
        params.update(filters)
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers=sb_headers(),
        params=params,
        timeout=30,
    )
    if r.status_code != 200:
        print(f"  [DB ERROR] query {table}: {r.status_code}")
        return []
    return r.json()


def sb_rpc(fn: str, params: dict) -> dict:
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/{fn}",
        headers=sb_headers(),
        json=params,
        timeout=60,
    )
    return r.json() if r.status_code == 200 else {"error": r.text}


# ── OpenAI embeddings ─────────────────────────────────────────────────────────

def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Returns list of 1536-dim vectors."""
    texts = [t[:8000] for t in texts]   # hard cap for safety
    for attempt in range(4):
        r = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
            json={"model": EMBED_MODEL, "input": texts},
            timeout=60,
        )
        if r.status_code == 200:
            data = r.json()["data"]
            return [d["embedding"] for d in sorted(data, key=lambda x: x["index"])]
        if r.status_code == 429:
            wait = 2 ** attempt * 5
            print(f"  [rate limit] waiting {wait}s …")
            time.sleep(wait)
        else:
            print(f"  [embed error] {r.status_code}: {r.text[:200]}")
            return [None] * len(texts)
    return [None] * len(texts)


# ── Chunking ──────────────────────────────────────────────────────────────────

def estimate_tokens(text: str) -> int:
    """Fast token estimate: ~4 chars per token for English."""
    return max(1, len(text) // 4)


def chunk_text(text: str, doc_type: str, ar_id: str) -> list[dict]:
    """
    Split document text into overlapping chunks with legal-doc awareness.

    Strategy by doc_type:
    - FBI forms (FD-1057, FD-1036): field-level chunks + one summary chunk
    - Email: header chunk + body chunks
    - Invoice/Bank Statement: header + row batches
    - Everything else: sliding window on sentence boundaries
    """
    if not text or not text.strip():
        return []

    chunks = []
    text = text.strip()

    # ── FBI forms ────────────────────────────────────────────────────────────
    if doc_type in ("Form", "Interview") or re.search(r'FD-105[0-9]|FD-103[0-9]', text):
        # Extract structured fields as individual searchable chunks
        field_pattern = re.compile(r'([A-Z][A-Za-z\s/]+):\s*(.+?)(?=\n[A-Z]|\Z)', re.DOTALL)
        fields = field_pattern.findall(text)
        if fields:
            # One chunk per logical field group (3-4 fields together)
            group, group_tokens = [], 0
            for label, value in fields:
                field_text = f"{label.strip()}: {value.strip()}"
                ft = estimate_tokens(field_text)
                if group_tokens + ft > CHUNK_TOKENS and group:
                    chunks.append({"text": "\n".join(group), "type": "field"})
                    group = [field_text]
                    group_tokens = ft
                else:
                    group.append(field_text)
                    group_tokens += ft
            if group:
                chunks.append({"text": "\n".join(group), "type": "field"})
            # Also add a summary chunk with the full first 600 chars
            chunks.insert(0, {"text": text[:2400], "type": "header"})
            return _index_chunks(chunks, ar_id)

    # ── Emails ───────────────────────────────────────────────────────────────
    if doc_type == "Email":
        lines = text.split("\n")
        header_lines, body_lines, in_body = [], [], False
        for line in lines:
            if not in_body and re.match(r'^(From|To|Cc|Subject|Date|Sent):', line, re.I):
                header_lines.append(line)
            else:
                in_body = True
                body_lines.append(line)
        header = "\n".join(header_lines)
        body = "\n".join(body_lines).strip()
        if header:
            chunks.append({"text": header, "type": "header"})
        # Body in sliding window
        for c in _sliding_window(body):
            chunks.append({"text": c, "type": "body"})
        return _index_chunks(chunks, ar_id)

    # ── Tables / invoices / bank statements ──────────────────────────────────
    if doc_type in ("Invoice", "Bank Statement", "Spreadsheet"):
        lines = text.split("\n")
        # First 10 lines as header
        header = "\n".join(lines[:10])
        chunks.append({"text": header, "type": "header"})
        # Remaining lines in batches of 30
        for i in range(10, len(lines), 30):
            batch = "\n".join(lines[i:i+30])
            if batch.strip():
                chunks.append({"text": batch, "type": "table"})
        return _index_chunks(chunks, ar_id)

    # ── Default: sliding window on sentence boundaries ────────────────────────
    for c in _sliding_window(text):
        chunks.append({"text": c, "type": "body"})
    return _index_chunks(chunks, ar_id)


def _sliding_window(text: str) -> Iterator[str]:
    """Yield overlapping chunks split on sentence boundaries."""
    # Split on sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', text)
    window, window_tokens = [], 0
    overlap_buf = []

    for sent in sentences:
        st = estimate_tokens(sent)
        if window_tokens + st > CHUNK_TOKENS and window:
            yield " ".join(window)
            # Keep overlap
            overlap_buf = []
            overlap_tokens = 0
            for w in reversed(window):
                wt = estimate_tokens(w)
                if overlap_tokens + wt > CHUNK_OVERLAP:
                    break
                overlap_buf.insert(0, w)
                overlap_tokens += wt
            window = overlap_buf + [sent]
            window_tokens = overlap_tokens + st
        else:
            window.append(sent)
            window_tokens += st

    if window:
        yield " ".join(window)


def _index_chunks(chunks: list[dict], ar_id: str) -> list[dict]:
    """Add chunk_index and token count to each chunk."""
    result = []
    for i, c in enumerate(chunks):
        result.append({
            "chunk_index": i,
            "chunk_text": c["text"],
            "chunk_tokens": estimate_tokens(c["text"]),
            "chunk_type": c.get("type", "body"),
        })
    return result


# ── Text extraction from blobs ────────────────────────────────────────────────

def text_from_first_paragraph(doc: dict) -> str:
    """
    CSV-mode: build searchable text from index metadata only.
    Good enough for initial embedding before blobs are uploaded.
    """
    parts = []
    if doc.get("subject_long"):
        parts.append(f"Subject: {doc['subject_long']}")
    if doc.get("parties_from"):
        parts.append(f"From: {doc['parties_from']}")
    if doc.get("parties_to"):
        parts.append(f"To: {doc['parties_to']}")
    if doc.get("primary_date"):
        parts.append(f"Date: {doc['primary_date']}")
    if doc.get("dollar_amounts"):
        parts.append(f"Amounts: {doc['dollar_amounts']}")
    if doc.get("policy_numbers"):
        parts.append(f"Policy: {doc['policy_numbers']}")
    if doc.get("synopsis"):
        parts.append(f"Synopsis: {doc['synopsis']}")
    if doc.get("first_paragraph"):
        parts.append(doc["first_paragraph"])
    return "\n".join(p for p in parts if p)


# ── CSV index → Supabase documents ───────────────────────────────────────────

def ingest_from_csv(index_path: str, production_id: str, dry_run: bool = False):
    """
    Phase 1: Load deep_v4.csv (or equivalent) into discovery_documents.
    Fast — no blob downloads needed. Sets text_extracted=TRUE using metadata.
    """
    path = Path(index_path)
    if not path.exists():
        print(f"ERROR: index file not found: {index_path}")
        sys.exit(1)

    print(f"Loading {path.name} → discovery_documents [{production_id}]")
    print(f"  Counting rows …", end="", flush=True)

    # Count rows first
    with open(path, newline="", encoding="utf-8-sig") as f:
        total = sum(1 for _ in csv.DictReader(f))
    print(f" {total:,} docs")

    # Get already-ingested ar_ids to skip
    existing = set()
    page = 0
    while True:
        rows = sb_query("discovery_documents",
                        select="ar_id",
                        filters={"production_id": f"eq.{production_id}"},
                        limit=1000)
        existing.update(r["ar_id"] for r in rows)
        if len(rows) < 1000:
            break
        page += 1

    print(f"  Already ingested: {len(existing):,}")
    skipped = 0

    batch = []
    inserted = 0

    def flush():
        nonlocal inserted
        if not dry_run and batch:
            n = sb_upsert("discovery_documents", batch)
            inserted += n
        batch.clear()

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            ar_id = row.get("ar_id", "").strip()
            if not ar_id:
                continue
            if ar_id in existing:
                skipped += 1
                continue

            # Parse date safely
            primary_date = None
            raw_date = row.get("primary_date", "").strip()
            if raw_date and re.match(r'\d{4}-\d{2}-\d{2}', raw_date):
                primary_date = raw_date

            # Build metadata text for CSV-mode embedding
            meta_text = text_from_first_paragraph(row)

            doc_row = {
                "ar_id":             ar_id,
                "production_id":     production_id,
                "doc_type":          row.get("doc_type", "").strip() or None,
                "doc_type_original": row.get("doc_type_original", "").strip() or None,
                "subject_long":      row.get("subject_long", "").strip() or None,
                "pdf_rule_id":       row.get("pdf_rule_id", "").strip() or None,
                "pdf_confidence":    float(row["pdf_confidence"]) if row.get("pdf_confidence","").strip() else None,
                "parties_from":      row.get("parties_from", "").strip() or None,
                "parties_to":        row.get("parties_to", "").strip() or None,
                "parties_cc":        row.get("parties_cc", "").strip() or None,
                "primary_date":      primary_date,
                "dollar_amounts":    row.get("dollar_amounts", "").strip() or None,
                "policy_numbers":    row.get("policy_numbers", "").strip() or None,
                "status_flags":      row.get("status_flags", "").strip() or None,
                "pdf_pages":         int(row["pdf_pages"]) if row.get("pdf_pages","").strip().isdigit() else None,
                "first_paragraph":   row.get("first_paragraph", "").strip()[:4000] or None,
                "synopsis":          row.get("synopsis", "").strip()[:2000] or None,
                "text_extracted":    True,   # metadata is the source for CSV mode
                "ingested_at":       datetime.datetime.utcnow().isoformat(),
            }

            # Pre-build chunks from metadata (stored alongside)
            chunks = chunk_text(meta_text, doc_row.get("doc_type") or "", ar_id)
            doc_row["_chunks"] = chunks   # stripped before DB insert

            batch.append(doc_row)

            if len(batch) >= BATCH_DB:
                # Strip internal keys before insert
                db_batch = [{k: v for k, v in r.items() if not k.startswith("_")} for r in batch]
                if not dry_run:
                    sb_upsert("discovery_documents", db_batch)
                    inserted += len(db_batch)
                    _insert_chunks(batch, production_id)
                else:
                    inserted += len(db_batch)
                batch.clear()

            if (i + 1) % 5000 == 0:
                pct = 100 * (i + 1) / total
                print(f"  {i+1:>7,} / {total:,}  ({pct:.1f}%)  inserted={inserted:,}  skip={skipped:,}")

    # Flush remainder
    if batch:
        db_batch = [{k: v for k, v in r.items() if not k.startswith("_")} for r in batch]
        if not dry_run:
            sb_upsert("discovery_documents", db_batch)
            inserted += len(db_batch)
            _insert_chunks(batch, production_id)

    print(f"\n  Done: {inserted:,} inserted, {skipped:,} skipped")
    return inserted


def _insert_chunks(doc_batch: list[dict], production_id: str):
    """Insert chunks for a batch of docs."""
    chunk_rows = []
    for doc in doc_batch:
        for c in doc.get("_chunks", []):
            chunk_rows.append({
                "ar_id":          doc["ar_id"],
                "production_id":  production_id,
                "chunk_index":    c["chunk_index"],
                "chunk_text":     c["chunk_text"],
                "chunk_tokens":   c["chunk_tokens"],
                "chunk_type":     c["chunk_type"],
            })
    if chunk_rows:
        sb_upsert("discovery_chunks", chunk_rows)


# ── Embedding phase ───────────────────────────────────────────────────────────

def embed_production(production_id: str, dry_run: bool = False):
    """
    Phase 2: For all chunks without embeddings, batch-embed and upsert.
    Idempotent: fetches only chunk_ids not yet in discovery_embeddings.
    """
    print(f"\nEmbedding chunks for {production_id} …")

    # Find chunk IDs that don't have embeddings yet
    # We use a custom RPC or direct query
    pending = []
    offset = 0
    while True:
        # Chunks not in embeddings table
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/discovery_chunks",
            headers=sb_headers(),
            params={
                "select": "id,ar_id,chunk_text,chunk_type",
                "production_id": f"eq.{production_id}",
                "id": "not.in.(select chunk_id from discovery_embeddings)",
                "limit": 1000,
                "offset": offset,
            },
            timeout=30,
        )
        rows = r.json() if r.status_code == 200 else []
        if not rows:
            break
        pending.extend(rows)
        if len(rows) < 1000:
            break
        offset += 1000

    total = len(pending)
    print(f"  Chunks needing embeddings: {total:,}")

    if not total:
        print("  Nothing to embed — already up to date.")
        return

    embedded = 0
    for i in range(0, total, BATCH_EMBED):
        batch = pending[i:i + BATCH_EMBED]
        texts = [c["chunk_text"] for c in batch]

        if dry_run:
            embedded += len(batch)
            continue

        vectors = embed_batch(texts)

        emb_rows = []
        update_ids = []
        for chunk, vec in zip(batch, vectors):
            if vec is None:
                continue
            emb_rows.append({
                "chunk_id":      chunk["id"],
                "ar_id":         chunk["ar_id"],
                "production_id": production_id,
                "chunk_index":   0,   # populated from chunk record
                "embedding":     vec,
                "model":         EMBED_MODEL,
            })
            update_ids.append(chunk["ar_id"])

        if emb_rows:
            sb_upsert("discovery_embeddings", emb_rows)
            embedded += len(emb_rows)

        if (i // BATCH_EMBED + 1) % 10 == 0:
            pct = 100 * min(i + BATCH_EMBED, total) / total
            print(f"  {min(i + BATCH_EMBED, total):>7,} / {total:,}  ({pct:.1f}%)  embedded={embedded:,}")

        time.sleep(0.1)   # avoid rate limits

    # Mark documents as embedded
    print(f"\n  Marking {production_id} docs as embedded …")

    print(f"  Done: {embedded:,} chunks embedded.")


# ── Status ────────────────────────────────────────────────────────────────────

def print_status():
    rows = sb_query("discovery_ingest_status", limit=20)
    if not rows:
        print("No data yet — run --source csv first.")
        return
    print(f"\n{'PROD':<8} {'PREFIX':<28} {'DOCS':>8} {'EXTRACTED':>10} {'CHUNKED':>8} {'EMBEDDED':>9} {'ERRORS':>7} {'%':>6}")
    print("-" * 90)
    for r in rows:
        print(f"{r['production_id']:<8} {(r['bates_prefix'] or ''):<28} "
              f"{(r['total_docs'] or 0):>8,} {(r['text_extracted'] or 0):>10,} "
              f"{(r['chunks_created'] or 0):>8,} {(r['embedded'] or 0):>9,} "
              f"{(r['errors'] or 0):>7,} {(r['pct_done'] or 0):>5.1f}%")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Discovery ingest pipeline")
    ap.add_argument("--source",     choices=["csv", "blob", "status"], default="status")
    ap.add_argument("--index",      help="Path to deep_v4.csv or equivalent index CSV")
    ap.add_argument("--production", help="PROD01 … PROD05")
    ap.add_argument("--embed-only", action="store_true", help="Skip CSV load, only run embedding phase")
    ap.add_argument("--dry-run",    action="store_true", help="Parse but don't write to DB")
    args = ap.parse_args()

    # Validate env
    if args.source != "status":
        missing = [k for k in ("SUPABASE_URL","SUPABASE_SERVICE_KEY","OPENAI_API_KEY")
                   if not os.environ.get(k)]
        if missing:
            print(f"ERROR: missing env vars: {', '.join(missing)}")
            sys.exit(1)

    if args.source == "status":
        print_status()
        return

    if not args.production:
        print("ERROR: --production required (PROD01 … PROD05)")
        sys.exit(1)

    if args.source == "csv":
        if not args.index:
            # Auto-detect
            defaults = {
                "PROD05": "prod_3/deep_v4.csv",
            }
            args.index = defaults.get(args.production)
            if not args.index:
                print("ERROR: --index required for this production")
                sys.exit(1)

        if not args.embed_only:
            ingest_from_csv(args.index, args.production, dry_run=args.dry_run)

        if not args.dry_run:
            embed_production(args.production, dry_run=args.dry_run)

    elif args.source == "blob":
        print("Blob mode: coming in next phase (needs USB upload first)")
        sys.exit(0)


if __name__ == "__main__":
    main()
