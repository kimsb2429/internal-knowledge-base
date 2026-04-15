#!/usr/bin/env python3
"""
Score a baseline eval artifact with DeepEval LLM-as-judge metrics.

Reads data/eval_baseline_vN.raw.json (from run_eval.py) and produces
data/eval_baseline_vN.scores.json with per-query metric scores + aggregates.

Metrics (Haiku judge):
  - Faithfulness           (answer vs. retrieval context — hallucination check)
  - Answer Relevancy       (answer vs. input query)
  - Contextual Precision   (are relevant chunks ranked higher?)
  - Contextual Recall      (does context contain what's needed for expected answer?)
  - Contextual Relevancy   (is context relevant to input?)

Usage:
    python3 scripts/score_eval.py --raw eval_baseline_v1.raw.json --out eval_baseline_v1.scores.json
    python3 scripts/score_eval.py --raw eval_baseline_v1.raw.json --limit 10   # subset test
"""

import argparse
import json
import os
import statistics
import sys
import time

from dotenv import load_dotenv

load_dotenv(".env")

from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    ContextualRelevancyMetric,
    FaithfulnessMetric,
)
from deepeval.models import AnthropicModel
from deepeval.test_case import LLMTestCase

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
JUDGE_MODEL = "claude-haiku-4-5-20251001"


def build_test_case(record: dict) -> LLMTestCase:
    return LLMTestCase(
        input=record["query"],
        actual_output=record["answer"],
        expected_output=record["expected_answer"],
        retrieval_context=record["context_strings"],
    )


def score_one(tc: LLMTestCase, metrics: list) -> dict:
    scores = {}
    for m in metrics:
        try:
            m.measure(tc)
            scores[m.__class__.__name__] = {
                "score": m.score,
                "reason": (m.reason or "")[:500],
                "success": m.is_successful(),
            }
        except Exception as e:
            scores[m.__class__.__name__] = {"error": str(e)[:300]}
    return scores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="eval_baseline_v1.raw.json")
    ap.add_argument("--out", default="eval_baseline_v1.scores.json")
    ap.add_argument("--limit", type=int, help="Only score the first N queries")
    ap.add_argument("--threshold", type=float, default=0.7)
    args = ap.parse_args()

    raw_path = os.path.join(DATA_DIR, args.raw)
    out_path = os.path.join(DATA_DIR, args.out)

    with open(raw_path) as f:
        raw = json.load(f)
    records = raw["results"]
    # Skip records that had errors during generation
    records = [r for r in records if "answer" in r]
    if args.limit:
        records = records[: args.limit]

    print(f"Scoring {len(records)} queries with Haiku judge ({JUDGE_MODEL})...")

    judge = AnthropicModel(model=JUDGE_MODEL, temperature=0.0)
    # Instantiate per query so internal state (reason, score) doesn't leak
    def fresh_metrics():
        return [
            FaithfulnessMetric(model=judge, threshold=args.threshold, async_mode=True),
            AnswerRelevancyMetric(model=judge, threshold=args.threshold, async_mode=True),
            ContextualPrecisionMetric(model=judge, threshold=args.threshold, async_mode=True),
            ContextualRecallMetric(model=judge, threshold=args.threshold, async_mode=True),
            ContextualRelevancyMetric(model=judge, threshold=args.threshold, async_mode=True),
        ]

    scored = []
    t0 = time.time()
    for i, rec in enumerate(records, 1):
        tc = build_test_case(rec)
        scores = score_one(tc, fresh_metrics())
        # Compact per-query summary line
        shorts = {
            "faith": scores.get("FaithfulnessMetric", {}).get("score"),
            "ans_rel": scores.get("AnswerRelevancyMetric", {}).get("score"),
            "ctx_prec": scores.get("ContextualPrecisionMetric", {}).get("score"),
            "ctx_rec": scores.get("ContextualRecallMetric", {}).get("score"),
            "ctx_rel": scores.get("ContextualRelevancyMetric", {}).get("score"),
        }
        print(
            f"  [{i:3d}/{len(records)}] id={rec['id']:>3}  "
            + "  ".join(f"{k}={v:.2f}" if isinstance(v, (int, float)) else f"{k}=ERR" for k, v in shorts.items())
        )
        scored.append({
            "id": rec["id"],
            "query": rec["query"],
            "query_type": rec.get("query_type"),
            "top1_source_match": rec["retrieval_signals"]["top1_source_match"],
            "topk_source_match": rec["retrieval_signals"]["topk_source_match"],
            "scores": scores,
            "answer_len_chars": len(rec["answer"]),
            "says_idk": "I don't know" in rec["answer"],
        })

    # Aggregate
    def mean_of(metric_name):
        vals = [
            s["scores"][metric_name]["score"]
            for s in scored
            if s["scores"].get(metric_name, {}).get("score") is not None
        ]
        return round(statistics.mean(vals), 3) if vals else None

    def pass_rate(metric_name):
        total = [
            1 if s["scores"][metric_name].get("success") else 0
            for s in scored
            if s["scores"].get(metric_name, {}).get("score") is not None
        ]
        return round(sum(total) / len(total), 3) if total else None

    aggregates = {}
    for m in ["FaithfulnessMetric", "AnswerRelevancyMetric", "ContextualPrecisionMetric",
              "ContextualRecallMetric", "ContextualRelevancyMetric"]:
        aggregates[m] = {"mean": mean_of(m), "pass_rate": pass_rate(m)}

    elapsed = time.time() - t0
    summary = {
        "n_scored": len(scored),
        "judge_model": JUDGE_MODEL,
        "threshold": args.threshold,
        "elapsed_seconds": round(elapsed, 1),
        "aggregates": aggregates,
    }

    with open(out_path, "w") as f:
        json.dump({"summary": summary, "results": scored}, f, indent=2)

    print("\n" + "=" * 60)
    print("AGGREGATES")
    for m, v in aggregates.items():
        short = m.replace("Metric", "")
        mean = v["mean"]
        pr = v["pass_rate"]
        print(f"  {short:<22} mean={mean}  pass_rate={pr}")
    print(f"\n  elapsed: {elapsed:.1f}s")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
