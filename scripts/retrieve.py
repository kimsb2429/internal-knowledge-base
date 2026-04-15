#!/usr/bin/env python3
"""
Vanilla vector retrieval against pgvector.

Embeds the query with mxbai-embed-large and returns the top-k most
semantically similar chunks via pgvector cosine distance.

Usage:
    from scripts.retrieve import retrieve
    results = retrieve("What RPO handles GI Bill claims in Texas?", k=5)

    # or CLI:
    python3 scripts/retrieve.py "your query" --k 5
"""

import argparse
import json
import os
import sys

import psycopg2
import psycopg2.extras
from sentence_transformers import SentenceTransformer

DB_URL = os.environ.get("IKB_DB_URL", "postgresql://ikb:ikb_local@localhost:5433/ikb")
MODEL_NAME = "mixedbread-ai/mxbai-embed-large-v1"

_MODEL = None
_CONN = None


def _get_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(MODEL_NAME)
    return _MODEL


def _get_conn():
    global _CONN
    if _CONN is None or _CONN.closed:
        _CONN = psycopg2.connect(DB_URL)
    return _CONN


def retrieve(query: str, k: int = 5) -> list[dict]:
    vec = _get_model().encode(query).tolist()
    vec_literal = "[" + ",".join(f"{x:.8f}" for x in vec) + "]"

    sql = """
        SELECT
            c.id              AS chunk_id,
            c.document_id     AS document_id,
            d.source_id       AS source_id,
            d.title           AS title,
            c.heading_path    AS heading_path,
            c.chunk_type      AS chunk_type,
            c.token_count     AS token_count,
            c.content         AS content,
            c.embed_text      AS embed_text,
            1 - (c.embedding <=> %s::vector) AS score
        FROM document_chunks c
        JOIN documents d ON d.id = c.document_id
        ORDER BY c.embedding <=> %s::vector
        LIMIT %s
    """
    with _get_conn().cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (vec_literal, vec_literal, k))
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", help="Natural-language query")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--show-content", action="store_true", help="Print full chunk content")
    args = ap.parse_args()

    results = retrieve(args.query, k=args.k)
    for i, r in enumerate(results, 1):
        print(f"\n[{i}] score={r['score']:.4f}  chunk_id={r['chunk_id']}  type={r['chunk_type']}  tokens={r['token_count']}")
        print(f"    source: {r['source_id']} — {r['title']}")
        print(f"    heading: {' > '.join(r['heading_path'] or [])}")
        if args.show_content:
            content = r["content"]
            if len(content) > 500:
                content = content[:500] + "…"
            print(f"    content: {content}")


if __name__ == "__main__":
    main()
