#!/usr/bin/env python3
"""
Memory reproducer for mxbai-rerank. Instruments each stage and prints
RSS delta so we can see where the 27GB spike came from.

Run from repo root:
    .venv/bin/python scripts/debug_rerank_mem.py [--device cpu|mps]
    .venv/bin/python scripts/debug_rerank_mem.py --with-embedder  # sim the real pipeline
"""

import argparse
import gc
import os
import resource
import sys
import time


def rss_mb() -> int:
    # macOS: ru_maxrss is in bytes (not KB like Linux)
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024)


def checkpoint(label: str, t0: float, last_rss: int) -> tuple[float, int]:
    now = time.time()
    cur = rss_mb()
    delta = cur - last_rss
    print(f"[{now - t0:6.1f}s] RSS={cur:>6} MB  (Δ {delta:+d} MB)  {label}")
    return now, cur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="mps", choices=["mps", "cpu"])
    ap.add_argument("--with-embedder", action="store_true",
                    help="Also load mxbai-embed-large (mirrors real pipeline)")
    ap.add_argument("--model", default="mixedbread-ai/mxbai-rerank-base-v2")
    ap.add_argument("--n-docs", type=int, default=20)
    ap.add_argument("--doc-tokens", type=int, default=500,
                    help="Approx size of each synthetic doc (tokens)")
    ap.add_argument("--n-calls", type=int, default=3,
                    help="How many successive rerank calls to simulate query loop")
    args = ap.parse_args()

    print(f"device={args.device}  with_embedder={args.with_embedder}  "
          f"model={args.model}  n_docs={args.n_docs}  n_calls={args.n_calls}")

    t0 = time.time()
    last = rss_mb()
    _, last = checkpoint("startup", t0, last)

    # Optionally load embedder first (matches real retrieval → rerank order)
    if args.with_embedder:
        from sentence_transformers import SentenceTransformer
        _, last = checkpoint("before embed load", t0, last)
        embedder = SentenceTransformer("mixedbread-ai/mxbai-embed-large-v1")
        _, last = checkpoint("after embed load", t0, last)
        # Run one encode to fully warm it
        _ = embedder.encode("What dollar threshold triggers four-signature review?")
        _, last = checkpoint("after one embed call", t0, last)

    # Load reranker
    from mxbai_rerank import MxbaiRerankV2
    _, last = checkpoint("before rerank load", t0, last)

    # Try to pass device if supported
    try:
        reranker = MxbaiRerankV2(args.model, device=args.device)
    except TypeError:
        # Older/newer wrapper may not expose device; fall back
        reranker = MxbaiRerankV2(args.model)
    _, last = checkpoint("after rerank load", t0, last)

    # Synthesize 20 chunks of repeated text (approx args.doc_tokens each)
    base = "The M22-4 policy manual for Chapter 33 Post-9/11 GI Bill education benefits specifies thresholds and review rules. "
    # ~25 tokens per sentence × 20 = 500 tokens
    doc = (base * max(1, args.doc_tokens // 25))[:args.doc_tokens * 4]
    docs = [doc for _ in range(args.n_docs)]
    query = "What dollar threshold triggers four-signature review for a Chapter 33 school payment?"

    for i in range(args.n_calls):
        _ = reranker.rank(query=query, documents=docs, return_documents=False, top_k=5)
        _, last = checkpoint(f"after rerank call {i+1}/{args.n_calls}", t0, last)

    gc.collect()
    _, last = checkpoint("after gc.collect()", t0, last)

    print(f"\nPeak RSS: {last} MB")


if __name__ == "__main__":
    main()
