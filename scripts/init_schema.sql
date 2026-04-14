-- pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Source documents (one row per article/PDF)
CREATE TABLE documents (
    id              SERIAL PRIMARY KEY,
    source_id       TEXT UNIQUE NOT NULL,          -- e.g. "554400000063717" or "VADIR_ICD"
    title           TEXT,
    source_type     TEXT NOT NULL,                 -- "knowva_html" | "pdf"
    source_url      TEXT,
    acl             TEXT NOT NULL DEFAULT 'public',
    authority_tier  INTEGER NOT NULL DEFAULT 1,
    content_category TEXT,
    raw_content     TEXT NOT NULL,                 -- full HTML or markdown
    last_modified   TIMESTAMPTZ,                  -- source document last-modified date (for freshness decay)
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Chunks (one row per chunk, references parent document)
CREATE TABLE document_chunks (
    id              SERIAL PRIMARY KEY,
    document_id     INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL,              -- ordering within document
    content         TEXT NOT NULL,                  -- full chunk content (sent to LLM)
    embed_text      TEXT NOT NULL,                  -- text that was embedded (= content, or summary for large chunks)
    embedding       vector(1024),                  -- mxbai-embed-large
    heading_path    TEXT[],                         -- e.g. {"Part 12","Chapter 33","Section 8.13"}
    chunk_type      TEXT NOT NULL DEFAULT 'text',   -- "text" | "table" | "list"
    token_count     INTEGER,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- HNSW index for vector similarity search
CREATE INDEX idx_chunks_embedding ON document_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Lookup chunks by document
CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
