#!/usr/bin/env python3
"""
Cross-encoder reranking: fine-grained relevance scoring for top-K chunks.

Sits between vector retrieval (scripts/retrieve.py) and generation. Takes a
query plus N candidate chunks, runs each (query, chunk) through a cross-encoder
for full-attention relevance scoring, returns the top-k by rerank score.

Why: bi-encoder cosine similarity (pgvector) confuses "chunk mentions the
query terms" with "chunk answers the query." A cross-encoder sees query and
chunk together at inference time and distinguishes them.

Model: FlashRank `ms-marco-MiniLM-L-12-v2` (22M params, ONNX-optimized encoder,
Apache 2.0). Picked over mxbai-rerank-base-v2 because the latter is a 0.5B
generative reward model whose per-pair scoring loop ran ~30s/query (20 docs)
on local MPS/CPU — too slow to gate every PR in CI. FlashRank MiniLM is
10-15x faster with acceptable quality for the Option A fast-proxy gate.
See docs/demo-prep-raw.md Act 30 for the CI-timeout + reranker-swap journey.

Usage:
    from scripts.retrieve import retrieve
    from scripts.rerank import rerank

    candidates = retrieve(query, k=20)
    top5 = rerank(query, candidates, top_k=5)
"""

import argparse
import os
from functools import lru_cache

from flashrank import Ranker, RerankRequest

MODEL_NAME = os.environ.get("IKB_RERANK_MODEL", "ms-marco-MiniLM-L-12-v2")
# FlashRank's max_length is passage + query tokens. 512 fits a 2K-char passage
# (~500 tokens) plus a short query. If you raise RERANK_MAX_CHARS, raise this
# in step.
RERANK_MAX_LENGTH = int(os.environ.get("IKB_RERANK_MAX_LENGTH", "512"))
# Truncation cap (chars, ~4:1 char:token ratio) sent to the cross-encoder.
# Cross-encoders train on short passages; long tables add noise, not signal.
# Full content is preserved in returned chunks for generation.
RERANK_MAX_CHARS = int(os.environ.get("IKB_RERANK_MAX_CHARS", "2000"))
# FlashRank downloads model ONNX files to its own cache dir. Point at a stable
# location so CI can restore it between runs via actions/cache.
RERANK_CACHE_DIR = os.environ.get("IKB_RERANK_CACHE_DIR", "/tmp/flashrank-cache")


@lru_cache(maxsize=1)
def _reranker() -> Ranker:
    os.makedirs(RERANK_CACHE_DIR, exist_ok=True)
    return Ranker(
        model_name=MODEL_NAME,
        cache_dir=RERANK_CACHE_DIR,
        max_length=RERANK_MAX_LENGTH,
    )


def rerank(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    """Rerank chunks (each must have a 'content' field) and return top_k.

    Preserves all original chunk fields; adds 'rerank_score' and 'rerank_rank'.
    Original cosine 'score' is retained as 'cosine_score' for diagnostics.
    """
    if not chunks:
        return []

    def _rerank_text(c: dict) -> str:
        heading = " > ".join(c.get("heading_path") or [])
        content = c["content"][:RERANK_MAX_CHARS]
        return f"{heading}\n\n{content}" if heading else content

    passages = [
        {"id": i, "text": _rerank_text(c)} for i, c in enumerate(chunks)
    ]
    results = _reranker().rerank(RerankRequest(query=query, passages=passages))
    # FlashRank returns passages sorted by score (descending). Slice to top_k.
    results = results[: min(top_k, len(results))]

    out = []
    for rank, r in enumerate(results):
        c = dict(chunks[r["id"]])
        c["cosine_score"] = c.get("score")
        c["rerank_score"] = float(r["score"])
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
