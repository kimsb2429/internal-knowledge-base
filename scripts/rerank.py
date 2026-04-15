#!/usr/bin/env python3
"""
Cross-encoder reranking: fine-grained relevance scoring for top-K chunks.

Sits between vector retrieval (scripts/retrieve.py) and generation. Takes a
query plus N candidate chunks, runs each (query, chunk) through a cross-encoder
for full-attention relevance scoring, returns the top-k by rerank score.

Why: bi-encoder cosine similarity (pgvector) confuses "chunk mentions the
query terms" with "chunk answers the query." A cross-encoder sees query and
chunk together at inference time and distinguishes them.

Model: mixedbread-ai/mxbai-rerank-base-v2 (Apache 2.0, 0.5B params, MPS-compatible).

Usage:
    from scripts.retrieve import retrieve
    from scripts.rerank import rerank

    candidates = retrieve(query, k=20)
    top5 = rerank(query, candidates, top_k=5)
"""

import argparse
import os
from functools import lru_cache

from mxbai_rerank import MxbaiRerankV2

MODEL_NAME = os.environ.get("IKB_RERANK_MODEL", "mixedbread-ai/mxbai-rerank-base-v2")
# Truncation cap (chars, ~4:1 char:token ratio) sent to the cross-encoder.
# The cross-encoder trains on short passages; feeding 47K-token tables explodes
# attention to O(n^2). Full content is preserved in returned chunks for gen.
RERANK_MAX_CHARS = int(os.environ.get("IKB_RERANK_MAX_CHARS", "2000"))


@lru_cache(maxsize=1)
def _reranker() -> MxbaiRerankV2:
    return MxbaiRerankV2(MODEL_NAME)


def rerank(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    """Rerank chunks (each must have a 'content' field) and return top_k.

    Preserves all original chunk fields; adds 'rerank_score' and 'rerank_rank'.
    Original cosine 'score' is retained as 'cosine_score' for diagnostics.
    """
    if not chunks:
        return []
    # Prefer a compact representation for reranking: heading_path + content head.
    # The cross-encoder ranks best on ≤512-token passages anyway.
    def _rerank_text(c: dict) -> str:
        heading = " > ".join(c.get("heading_path") or [])
        content = c["content"][:RERANK_MAX_CHARS]
        return f"{heading}\n\n{content}" if heading else content

    docs = [_rerank_text(c) for c in chunks]
    results = _reranker().rank(
        query=query,
        documents=docs,
        return_documents=False,
        top_k=min(top_k, len(docs)),
    )
    out = []
    for rank, r in enumerate(results):
        c = dict(chunks[r.index])
        c["cosine_score"] = c.get("score")
        c["rerank_score"] = float(r.score)
        c["rerank_rank"] = rank
        out.append(c)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--k-first", type=int, default=20, help="Top-k from vector search")
    ap.add_argument("--k-final", type=int, default=5, help="Top-k after reranking")
    args = ap.parse_args()

    from scripts.retrieve import retrieve

    candidates = retrieve(args.query, k=args.k_first)
    final = rerank(args.query, candidates, top_k=args.k_final)

    print(f"\nQUERY: {args.query}")
    print("=" * 70)
    print(f"Vector retrieval: top-{args.k_first} candidates")
    print(f"After rerank:     top-{args.k_final}\n")
    for i, c in enumerate(final, 1):
        print(
            f"  [{i}] rerank={c['rerank_score']:.3f}  cosine={c['cosine_score']:.3f}  "
            f"src={c['source_id']}"
        )
        print(f"      {' > '.join(c['heading_path'] or [])}")


if __name__ == "__main__":
    main()
