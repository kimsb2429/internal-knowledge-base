#!/usr/bin/env python3
"""
Run the golden query set through retrieve + generate, save raw artifacts.

Produces data/eval_baseline_vN.raw.json — one record per query with the
retrieved chunks, formatted context, generated answer, and token usage.
Downstream scoring (DeepEval) reads this file.

Usage:
    python3 scripts/run_eval.py                         # all 110 queries
    python3 scripts/run_eval.py --limit 10              # first 10
    python3 scripts/run_eval.py --ids 1,2,3             # specific IDs
    python3 scripts/run_eval.py --out eval_subset.json  # custom output name
"""

import argparse
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

load_dotenv()

from scripts.retrieve import retrieve
from scripts.generate import generate
from scripts.rerank import rerank

GOLDEN_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "golden_query_set.json")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_queries() -> list[dict]:
    with open(GOLDEN_PATH) as f:
        return json.load(f)["queries"]


def expected_source_ids(q: dict) -> list[str]:
    """Extract expected source article id(s) from a golden query record."""
    ids = []
    if "source_article_id" in q:
        ids.append(str(q["source_article_id"]))
    for alt in q.get("source_article_id_alt", []) or []:
        ids.append(str(alt))
    # Some records have source_docs (list of human-readable refs), no direct id
    return ids


def _prep(q: dict, k: int, rerank_from: int = 0) -> dict:
    """Phase 1 — retrieve. CPU-bound; kept serial across queries so PyTorch
    doesn't thrash when running on CI's CPU-only runners. All the non-LLM
    work lives here; the shape is ready for phase 2 to attach the generated
    answer."""
    chunks = retrieve(q["query"], k=k)

    expected_ids = expected_source_ids(q)
    retrieved_ids = [str(c["source_id"]) for c in chunks]
    top1_match = bool(expected_ids and retrieved_ids[0] in expected_ids)
    topk_match = bool(expected_ids and any(rid in expected_ids for rid in retrieved_ids))

    # Strip embeddings/large fields from retrieved_chunks before saving
    slim_chunks = [
        {
            "chunk_id": c["chunk_id"],
            "source_id": c["source_id"],
            "title": c["title"],
            "heading_path": c["heading_path"],
            "chunk_type": c["chunk_type"],
            "token_count": c["token_count"],
            "score": c["score"],
            "content": c["content"],
        }
        for c in chunks
    ]

    return {
        "q": q,
        "chunks": chunks,
        "expected_ids": expected_ids,
        "retrieved_ids": retrieved_ids,
        "top1_match": top1_match,
        "topk_match": topk_match,
        "slim_chunks": slim_chunks,
    }


def _complete(prep: dict) -> dict:
    """Phase 2 — generate answer. API-bound; safe to run concurrently across
    queries because the Anthropic client is thread-safe and Anthropic accepts
    parallel requests."""
    q = prep["q"]
    gen = generate(q["query"], prep["chunks"])
    return {
        "id": q["id"],
        "query": q["query"],
        "expected_answer": q["answer"],
        "expected_source_ids": prep["expected_ids"],
        "query_type": q.get("query_type"),
        "answer_in_table": q.get("answer_in_table"),
        "tags": q.get("tags", []),
        "retrieved_chunks": prep["slim_chunks"],
        "context_strings": gen["context_strings"],
        "answer": gen["answer"],
        "model": gen["model"],
        "usage": gen["usage"],
        "retrieval_signals": {
            "top1_source_match": prep["top1_match"],
            "topk_source_match": prep["topk_match"],
            "retrieved_source_ids": prep["retrieved_ids"],
        },
    }


def run_one(q: dict, k: int, rerank_from: int = 0) -> dict:
    """Back-compat wrapper kept so external callers (e.g., ad-hoc scripts) still
    work. Internal two-phase path uses _prep + _complete directly."""
    return _complete(_prep(q, k=k, rerank_from=rerank_from))


import re

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "at", "for", "with",
    "is", "are", "was", "were", "be", "by", "as", "it", "its", "this", "that",
    "these", "those", "from", "but", "not", "no", "yes", "if", "then", "else",
    "what", "when", "where", "why", "how", "which", "who", "whom",
}


def extract_distinctive(text: str) -> set[str]:
    """Pull distinctive multi-word/proper-noun terms for keyword presence proxy."""
    if not text:
        return set()
    tokens = re.findall(
        r"\$[\d,]+|"                             # $45,000
        r"\d+%|"                                  # 80%
        r"[A-Z]{2,}-?\d*|"                        # M22-4, RPO, BAH
        r"[A-Z][a-z]{3,}|"                        # Muskogee, August
        r"\b[a-z]{6,}\b|"                         # 6+ char domain words
        r"\b\d{3,}\b",                            # 3+ digit numbers
        text,
    )
    return {t.lower() for t in tokens if t.lower() not in STOPWORDS}


def cheap_proxies(results: list[dict]) -> dict:
    """Compute fast retrieval/quality proxies from raw eval (no LLM judge)."""
    n = len(results)
    if n == 0:
        return {}
    # Top-K source match (already in retrieval_signals, but compute here for clarity)
    top1 = sum(1 for r in results if r.get("retrieval_signals", {}).get("top1_source_match"))
    topk = sum(1 for r in results if r.get("retrieval_signals", {}).get("topk_source_match"))
    # Answer-keyword recall: distinctive terms from expected answer present in retrieval context
    kw_recalls = []
    for r in results:
        expected = r.get("expected_answer", "") or ""
        terms = extract_distinctive(expected)
        if not terms:
            continue
        ctx_blob = " ".join(r.get("context_strings", []) or [])
        ctx_lower = ctx_blob.lower()
        hits = sum(1 for t in terms if t in ctx_lower)
        kw_recalls.append(hits / len(terms))
    # IDK rate (faithfulness proxy — high IDK = retrieval insufficiency)
    idk = sum(1 for r in results if "I don't know" in (r.get("answer") or ""))
    # Token cost
    avg_in = sum(r.get("usage", {}).get("input_tokens", 0) for r in results) / n
    avg_out = sum(r.get("usage", {}).get("output_tokens", 0) for r in results) / n
    return {
        "n": n,
        "top1_source_match_rate": round(top1 / n, 3),
        "topk_source_match_rate": round(topk / n, 3),
        "answer_keyword_recall_mean": round(sum(kw_recalls) / len(kw_recalls), 3) if kw_recalls else None,
        "answer_keyword_recall_n": len(kw_recalls),
        "idk_rate": round(idk / n, 3),
        "avg_input_tokens": int(avg_in),
        "avg_output_tokens": int(avg_out),
    }


def print_proxies_with_delta(label: str, current: dict, baseline: dict | None):
    print(f"\n{'=' * 60}\n  {label}  (n={current['n']})\n{'=' * 60}")
    keys = ["top1_source_match_rate", "topk_source_match_rate",
            "answer_keyword_recall_mean", "idk_rate", "avg_input_tokens", "avg_output_tokens"]
    for k in keys:
        cur = current.get(k)
        if cur is None:
            continue
        if baseline is None:
            print(f"  {k:<32} {cur}")
        else:
            base = baseline.get(k)
            if base is None or not isinstance(cur, (int, float)) or not isinstance(base, (int, float)):
                print(f"  {k:<32} {cur}")
            else:
                d = cur - base
                arrow = "▲" if d > 0 else ("▼" if d < 0 else " ")
                # Sign convention: lower idk is better; lower tokens is better
                better = (d < 0) if k in {"idk_rate", "avg_input_tokens", "avg_output_tokens"} else (d > 0)
                marker = "✓" if better and abs(d) > 0.001 else (" " if abs(d) < 0.001 else "✗")
                print(f"  {k:<32} {cur:<8}  vs base {base:<8}  Δ {d:+.3f} {arrow} {marker}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5, help="Top-k chunks returned to generation")
    ap.add_argument("--rerank-from", type=int, default=0,
                    help="If >0, retrieve this many candidates from pgvector then rerank down to --k.")
    ap.add_argument("--limit", type=int, help="Only run the first N queries")
    ap.add_argument("--ids", type=str, help="Comma-separated list of query ids to run")
    ap.add_argument("--out", type=str, default="eval_baseline_v1.raw.json")
    ap.add_argument("--fast", action="store_true",
                    help="Fast triage mode: limit=30 by default, prints cheap proxies, no DeepEval scoring.")
    ap.add_argument("--baseline", type=str,
                    help="Path to a prior raw eval JSON (e.g. eval_v2b_rerank.raw.json) — print proxy deltas vs it.")
    ap.add_argument("--concurrency", type=int, default=8,
                    help="Phase-2 (Sonnet generation) concurrency. Retrieve+rerank stays serial.")
    args = ap.parse_args()

    if args.fast and args.limit is None:
        args.limit = 30

    queries = load_queries()
    if args.ids:
        wanted = set(int(x) for x in args.ids.split(","))
        queries = [q for q in queries if q["id"] in wanted]
    if args.limit:
        queries = queries[: args.limit]

    rr_note = f"  rerank_from={args.rerank_from}" if args.rerank_from else ""
    print(
        f"Running {len(queries)} queries (k={args.k}){rr_note}  "
        f"concurrency={args.concurrency}"
    )

    out_path = os.path.join(OUT_DIR, args.out)
    results: list[dict | None] = [None] * len(queries)
    total_in = total_out = 0
    t0 = time.time()

    # Phase 1 — serial retrieve + rerank.
    print(f"Phase 1 (retrieve+rerank, serial): {len(queries)} queries", flush=True)
    preps: list[dict | None] = [None] * len(queries)
    phase1_errors: list[tuple[int, str]] = []
    phase1_start = time.time()
    for i, q in enumerate(queries):
        t_q = time.time()
        try:
            preps[i] = _prep(q, k=args.k, rerank_from=args.rerank_from)
            dt = time.time() - t_q
            print(f"  P1 [{i+1:3d}/{len(queries)}] id={q['id']:>3}  {dt:>5.1f}s", flush=True)
        except Exception as e:
            phase1_errors.append((i, str(e)))
            results[i] = {"id": q["id"], "query": q["query"], "error": f"phase1: {e}"}
            print(f"  P1 [{i+1:3d}/{len(queries)}] id={q['id']} PHASE1 FAILED: {e}", flush=True)
    phase1_done = time.time()
    print(f"Phase 1 done in {phase1_done - phase1_start:.1f}s", flush=True)

    # Phase 2 — concurrent Sonnet generation.
    pending = [(i, p) for i, p in enumerate(preps) if p is not None]
    print(f"Phase 2 (generate, concurrency={args.concurrency}): {len(pending)} queries")
    print_lock = threading.Lock()
    done_count = 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        future_to_idx = {pool.submit(_complete, p): i for i, p in pending}
        for fut in as_completed(future_to_idx):
            idx = future_to_idx[fut]
            q = queries[idx]
            try:
                rec = fut.result()
                results[idx] = rec
                total_in += rec["usage"]["input_tokens"]
                total_out += rec["usage"]["output_tokens"]
                sig = rec["retrieval_signals"]
                with print_lock:
                    done_count += 1
                    print(
                        f"  [{done_count:3d}/{len(pending)}] id={q['id']:>3}  "
                        f"top1_match={sig['top1_source_match']}  topk_match={sig['topk_source_match']}  "
                        f"tokens_in={rec['usage']['input_tokens']:>5} out={rec['usage']['output_tokens']:>3}"
                    )
            except Exception as e:
                results[idx] = {"id": q["id"], "query": q["query"], "error": f"phase2: {e}"}
                with print_lock:
                    done_count += 1
                    print(f"  [{done_count:3d}/{len(pending)}] id={q['id']} PHASE2 FAILED: {e}")

    # Save
    elapsed = time.time() - t0
    # Sonnet 4.6: $3/M input, $15/M output
    cost = total_in * 3 / 1_000_000 + total_out * 15 / 1_000_000
    top1_hits = sum(1 for r in results if r.get("retrieval_signals", {}).get("top1_source_match"))
    topk_hits = sum(1 for r in results if r.get("retrieval_signals", {}).get("topk_source_match"))

    summary = {
        "n_queries": len(results),
        "elapsed_seconds": round(elapsed, 1),
        "total_input_tokens": total_in,
        "total_output_tokens": total_out,
        "estimated_cost_usd": round(cost, 4),
        "top1_source_match_rate": round(top1_hits / len(results), 3) if results else 0,
        "topk_source_match_rate": round(topk_hits / len(results), 3) if results else 0,
        "k": args.k,
        "rerank_from": args.rerank_from,
    }

    with open(out_path, "w") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)

    print("\n" + "=" * 60)
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print(f"\nSaved: {out_path}")

    # Cheap proxies + optional baseline delta
    proxies = cheap_proxies(results)
    baseline_proxies = None
    if args.baseline:
        baseline_path = args.baseline if os.path.isabs(args.baseline) else os.path.join(OUT_DIR, args.baseline)
        if os.path.exists(baseline_path):
            with open(baseline_path) as f:
                base_raw = json.load(f)
            base_results = base_raw.get("results", [])
            # Match baseline to same set of query ids for fair delta
            current_ids = {r["id"] for r in results}
            base_results = [r for r in base_results if r.get("id") in current_ids]
            baseline_proxies = cheap_proxies(base_results)
            baseline_proxies["__source"] = args.baseline
            baseline_proxies["__matched_n"] = len(base_results)
        else:
            print(f"  (baseline {args.baseline} not found; skipping delta)")
    print_proxies_with_delta("FAST PROXIES" if args.fast else "PROXIES", proxies, baseline_proxies)
    if baseline_proxies:
        print(f"\n  baseline: {baseline_proxies['__source']}  matched n={baseline_proxies['__matched_n']}")
    if args.fast:
        print("\n  (fast mode: DeepEval scoring skipped — run scripts/score_eval.py for full metrics)")


if __name__ == "__main__":
    main()
