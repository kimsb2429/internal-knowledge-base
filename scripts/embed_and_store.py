#!/usr/bin/env python3
"""
Embed chunks with mxbai-embed-large and store in pgvector.

For regular chunks, embed the full content.
For oversized chunks, embed a descriptive string built from the article title
and heading_path (summary indexing — the full content is still served at
generation time, but retrieval uses the descriptive headers).

Resume-safe: skips source_ids already present in the documents table.

Run from repo root:
    python3 scripts/embed_and_store.py
"""

import json
import os
import sys

import psycopg2
import psycopg2.extras
from sentence_transformers import SentenceTransformer

CHUNKS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "knowva_manuals", "chunks", "all_chunks.json"
)
DB_URL = os.environ.get("IKB_DB_URL", "postgresql://ikb:ikb_local@localhost:5433/ikb")
MODEL_NAME = "mixedbread-ai/mxbai-embed-large-v1"
EMBED_BATCH_SIZE = 32


def build_embed_text(chunk: dict) -> str:
    """For oversized chunks, embed a descriptive string instead of raw content."""
    if not chunk["oversized"]:
        return chunk["content"]

    title = (chunk.get("source_metadata", {}) or {}).get("title", "") or ""
    heading_parts = [h for h in (chunk.get("heading_path") or []) if h and h != title]
    heading = " > ".join(heading_parts)
    parts = [p for p in [title, heading] if p]
    return " | ".join(parts) if parts else chunk["content"][:500]


def vector_literal(embedding) -> str:
    """Format a list of floats as a pgvector literal."""
    return "[" + ",".join(f"{v:.6f}" for v in embedding) + "]"


def group_chunks_by_source(chunks: list[dict]) -> dict[str, list[dict]]:
    by_source = {}
    for c in chunks:
        by_source.setdefault(c["source_id"], []).append(c)
    return by_source


def insert_document(cur, source_id: str, chunks_for_source: list[dict]) -> int:
    """Insert one document row. Returns document_id."""
    # All chunks share the same source_metadata
    meta = chunks_for_source[0].get("source_metadata", {}) or {}
    title = meta.get("title")
    source_url = meta.get("source_url")
    source_type = meta.get("source_type", "va_manual")
    acl = meta.get("acl", "public")
    authority_tier = meta.get("authority_tier", 1)
    content_category = meta.get("content_category")
    last_modified = meta.get("last_modified") or meta.get("modified_date")

    # raw_content is all chunk content joined — used for debugging / reprocessing
    raw_content = "\n\n".join(c["content"] for c in chunks_for_source)

    cur.execute(
        """
        INSERT INTO documents
            (source_id, title, source_type, source_url, acl, authority_tier,
             content_category, raw_content, last_modified, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            source_id,
            title,
            source_type,
            source_url,
            acl,
            authority_tier,
            content_category,
            raw_content,
            last_modified,
            psycopg2.extras.Json(meta),
        ),
    )
    return cur.fetchone()[0]


def insert_chunks(cur, document_id: int, chunks: list[dict], embeddings: list):
    """Bulk insert chunks with embeddings."""
    rows = []
    for chunk, embedding in zip(chunks, embeddings):
        embed_text = build_embed_text(chunk)
        rows.append((
            document_id,
            chunk["chunk_index"],
            chunk["content"],
            embed_text,
            vector_literal(embedding),
            chunk.get("heading_path") or [],
            chunk["chunk_type"],
            chunk["token_count"],
            psycopg2.extras.Json({"oversized": chunk["oversized"]}),
        ))

    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO document_chunks
            (document_id, chunk_index, content, embed_text, embedding,
             heading_path, chunk_type, token_count, metadata)
        VALUES %s
        """,
        rows,
        template="(%s, %s, %s, %s, %s::vector, %s, %s, %s, %s)",
    )


def main():
    print(f"Loading chunks from {CHUNKS_PATH}...")
    with open(CHUNKS_PATH) as f:
        all_chunks = json.load(f)
    print(f"  Loaded {len(all_chunks)} chunks")

    print(f"Loading embedding model {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    by_source = group_chunks_by_source(all_chunks)
    print(f"  {len(by_source)} unique source documents")

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False

    # Resume-safe: find already-inserted source_ids
    with conn.cursor() as cur:
        cur.execute("SELECT source_id FROM documents")
        existing = {row[0] for row in cur.fetchall()}
    if existing:
        print(f"  Skipping {len(existing)} already-inserted documents")

    total_chunks_inserted = 0
    total_docs_inserted = 0

    for i, (source_id, source_chunks) in enumerate(sorted(by_source.items())):
        if source_id in existing:
            continue

        # Build embed_text strings and embed in batch
        embed_texts = [build_embed_text(c) for c in source_chunks]
        embeddings = model.encode(
            embed_texts,
            batch_size=EMBED_BATCH_SIZE,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        try:
            with conn.cursor() as cur:
                document_id = insert_document(cur, source_id, source_chunks)
                insert_chunks(cur, document_id, source_chunks, embeddings)
            conn.commit()
            total_chunks_inserted += len(source_chunks)
            total_docs_inserted += 1

            if (i + 1) % 10 == 0 or i == len(by_source) - 1:
                print(f"  [{i+1}/{len(by_source)}] source={source_id}: "
                      f"{len(source_chunks)} chunks "
                      f"(total: {total_docs_inserted} docs, {total_chunks_inserted} chunks)")
        except Exception as e:
            conn.rollback()
            print(f"  ERROR on {source_id}: {e}", file=sys.stderr)
            raise

    conn.close()
    print(f"\nDone. Inserted {total_docs_inserted} documents, {total_chunks_inserted} chunks.")


if __name__ == "__main__":
    main()
