-- ============================================================
-- DISCOVERY INGESTION SCHEMA
-- U.S. v. Redmond et al., EDPA 24-cr-375-JLS
-- Supabase / PostgreSQL + pgvector
-- Protected: Protective Order ECF No. 82 (June 2, 2025)
-- ============================================================

-- Enable pgvector if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- for BM25-style full-text

-- ============================================================
-- 1. PRODUCTIONS  (the 5 government discs)
-- ============================================================
CREATE TABLE IF NOT EXISTS discovery_productions (
    production_id       TEXT PRIMARY KEY,          -- PROD01 … PROD05
    bates_prefix        TEXT NOT NULL,             -- RedmondTax, Prod02_Confidential …
    bates_start         TEXT,
    bates_end           TEXT,
    produced_date       DATE,
    production_method   TEXT,                      -- USAfx | Flash Drive | Hard Drive
    total_doc_count     INTEGER,
    storage_account     TEXT,                      -- Azure account name
    container_name      TEXT,                      -- disco26
    folder_path         TEXT,                      -- PROD03_RedmondOvertActs0001-0722/
    index_csv_path      TEXT,                      -- path to the deep_v4.csv etc.
    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO discovery_productions VALUES
  ('PROD01','RedmondTax','000001','008835','2024-10-31','USAfx',NULL,NULL,'disco26','PROD01_RedmondTax000001-008835/',NULL,NULL,NOW()),
  ('PROD02','RedmondTax','000836','693308','2025-01-16','Flash Drive / FedEx',NULL,NULL,'disco26','PROD02_RedmondTax000836-693308/',NULL,NULL,NOW()),
  ('PROD03','RedmondOvertActs','0001','0722','2025-07-18','USAfx',NULL,NULL,'disco26','PROD03_RedmondOvertActs0001-0722/',NULL,NULL,NOW()),
  ('PROD04','Prod02_Confidential','000000001','000991938','2025-09-29','Hard Drive',NULL,NULL,'disco26','PROD04_Prod02Confidential/',NULL,NULL,NOW()),
  ('PROD05','Prod03_Confidential','000000001','000677497','2026-03-23','Flash Drive',107577,NULL,'disco26','PROD05_Prod03Confidential/','prod_3/deep_v4.csv',
   'AR-ID 0000000002–0000677496; 3-part zip; 894k files',NOW())
ON CONFLICT (production_id) DO NOTHING;

-- ============================================================
-- 2. DOCUMENTS  (one row per government-produced document)
-- ============================================================
CREATE TABLE IF NOT EXISTS discovery_documents (
    id                  BIGSERIAL PRIMARY KEY,
    ar_id               TEXT        NOT NULL,      -- 0000000002 (zero-padded 10 digits)
    production_id       TEXT        NOT NULL REFERENCES discovery_productions(production_id),

    -- Classification (from deep_v4 / enriched)
    doc_type            TEXT,                      -- Form | Email | Interview | Invoice …
    doc_type_original   TEXT,                      -- PDF | Document | XLS …
    subject_long        TEXT,                      -- FD-1057, SECTION, etc.
    pdf_rule_id         TEXT,                      -- FBI_COVER, etc.
    pdf_confidence      NUMERIC(4,2),

    -- Parties
    parties_from        TEXT,
    parties_to          TEXT,
    parties_cc          TEXT,

    -- Dates & amounts
    primary_date        DATE,
    dollar_amounts      TEXT,
    policy_numbers      TEXT,
    status_flags        TEXT,

    -- Structure
    pdf_pages           INTEGER,
    xlsx_sheets         INTEGER,
    eml_attachments     INTEGER,

    -- Content summary (from index, before blob download)
    first_paragraph     TEXT,
    synopsis            TEXT,

    -- Azure blob location
    blob_container      TEXT,
    blob_path           TEXT,                      -- e.g. PROD05/.../0001/AR-0000000002.pdf
    blob_size_bytes     BIGINT,

    -- Processing state
    text_extracted      BOOLEAN DEFAULT FALSE,
    chunks_created      BOOLEAN DEFAULT FALSE,
    embedded            BOOLEAN DEFAULT FALSE,
    extraction_error    TEXT,
    ingested_at         TIMESTAMPTZ,

    UNIQUE (ar_id, production_id)
);

CREATE INDEX IF NOT EXISTS idx_disc_doc_arid       ON discovery_documents (ar_id);
CREATE INDEX IF NOT EXISTS idx_disc_doc_prod        ON discovery_documents (production_id);
CREATE INDEX IF NOT EXISTS idx_disc_doc_type        ON discovery_documents (doc_type);
CREATE INDEX IF NOT EXISTS idx_disc_doc_date        ON discovery_documents (primary_date);
CREATE INDEX IF NOT EXISTS idx_disc_doc_from        ON discovery_documents USING gin (parties_from gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_disc_doc_subject     ON discovery_documents USING gin (subject_long gin_trgm_ops);

-- ============================================================
-- 3. CHUNKS  (text chunks ready for embedding)
-- ============================================================
CREATE TABLE IF NOT EXISTS discovery_chunks (
    id              BIGSERIAL PRIMARY KEY,
    ar_id           TEXT        NOT NULL,
    production_id   TEXT        NOT NULL,
    chunk_index     INTEGER     NOT NULL,          -- 0-based within document

    chunk_text      TEXT        NOT NULL,
    chunk_tokens    INTEGER,                       -- tiktoken count
    chunk_type      TEXT,                          -- body | header | table | field | metadata
    page_start      INTEGER,                       -- PDF page where chunk begins
    page_end        INTEGER,

    -- Overlap pointers for re-ranking context retrieval
    prev_chunk_id   BIGINT,
    next_chunk_id   BIGINT,

    created_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (ar_id, production_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_disc_chunk_arid  ON discovery_chunks (ar_id, production_id);
CREATE INDEX IF NOT EXISTS idx_disc_chunk_fts   ON discovery_chunks USING gin (to_tsvector('english', chunk_text));

-- ============================================================
-- 4. EMBEDDINGS  (pgvector — 1536 dims, text-embedding-3-small)
-- ============================================================
CREATE TABLE IF NOT EXISTS discovery_embeddings (
    id              BIGSERIAL PRIMARY KEY,
    chunk_id        BIGINT      NOT NULL REFERENCES discovery_chunks(id) ON DELETE CASCADE,
    ar_id           TEXT        NOT NULL,
    production_id   TEXT        NOT NULL,
    chunk_index     INTEGER     NOT NULL,

    embedding       vector(1536) NOT NULL,
    model           TEXT        DEFAULT 'text-embedding-3-small',
    created_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (chunk_id)
);

-- HNSW index: fast ANN search, tuned for legal recall over speed
CREATE INDEX IF NOT EXISTS idx_disc_emb_hnsw ON discovery_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 128);

-- ============================================================
-- 5. BATES INDEX  (ground truth: bates stamp → ar_id)
-- ============================================================
CREATE TABLE IF NOT EXISTS discovery_bates (
    bates_number    TEXT        PRIMARY KEY,       -- RedmondTax000001
    bates_prefix    TEXT        NOT NULL,
    bates_seq       INTEGER     NOT NULL,
    ar_id           TEXT,
    production_id   TEXT        REFERENCES discovery_productions(production_id),
    blob_path       TEXT,
    confirmed       BOOLEAN     DEFAULT FALSE      -- TRUE once physically verified
);

CREATE INDEX IF NOT EXISTS idx_bates_arid   ON discovery_bates (ar_id);
CREATE INDEX IF NOT EXISTS idx_bates_prod   ON discovery_bates (production_id);

-- ============================================================
-- 6. ENTITIES  (people, orgs, amounts, case IDs — extracted)
-- ============================================================
CREATE TABLE IF NOT EXISTS discovery_entities (
    id              BIGSERIAL   PRIMARY KEY,
    ar_id           TEXT        NOT NULL,
    production_id   TEXT,
    chunk_id        BIGINT      REFERENCES discovery_chunks(id),

    entity_type     TEXT        NOT NULL,          -- PERSON | ORG | CASE_ID | MONEY | DATE | EMAIL | PHONE | AGENT
    entity_value    TEXT        NOT NULL,
    context         TEXT,                          -- surrounding 100 chars
    confidence      NUMERIC(4,2),

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_disc_ent_type    ON discovery_entities (entity_type);
CREATE INDEX IF NOT EXISTS idx_disc_ent_value   ON discovery_entities USING gin (entity_value gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_disc_ent_arid    ON discovery_entities (ar_id);

-- ============================================================
-- 7. SEARCH VIEW  (hybrid: semantic + BM25 in one query)
-- ============================================================
CREATE OR REPLACE VIEW discovery_search_view AS
SELECT
    c.id            AS chunk_id,
    c.ar_id,
    c.production_id,
    c.chunk_index,
    c.chunk_text,
    c.chunk_type,
    d.doc_type,
    d.subject_long,
    d.parties_from,
    d.parties_to,
    d.primary_date,
    d.dollar_amounts,
    d.synopsis,
    d.blob_path,
    to_tsvector('english', c.chunk_text) AS tsv
FROM discovery_chunks c
JOIN discovery_documents d USING (ar_id, production_id);

-- ============================================================
-- 8. INGEST STATUS VIEW  (progress dashboard)
-- ============================================================
CREATE OR REPLACE VIEW discovery_ingest_status AS
SELECT
    p.production_id,
    p.bates_prefix,
    COUNT(d.id)                                     AS total_docs,
    SUM(d.text_extracted::int)                      AS text_extracted,
    SUM(d.chunks_created::int)                      AS chunks_created,
    SUM(d.embedded::int)                            AS embedded,
    SUM(CASE WHEN d.extraction_error IS NOT NULL THEN 1 ELSE 0 END) AS errors,
    ROUND(100.0 * SUM(d.embedded::int) / NULLIF(COUNT(d.id),0), 1) AS pct_done
FROM discovery_productions p
LEFT JOIN discovery_documents d USING (production_id)
GROUP BY p.production_id, p.bates_prefix
ORDER BY p.production_id;
