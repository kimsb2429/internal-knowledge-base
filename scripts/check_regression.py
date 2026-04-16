#!/usr/bin/env python3
"""Compare the current eval run's proxies against a baseline; exit 1 on regression.

This is the blocking gate for the eval-in-CI merge check (Option A — fast
proxies on every PR). Full DeepEval scoring is NOT run here; it's a separate
nightly/release check (Option C).

Tolerances (v1 — intentionally conservative; Sonnet 4.6 generation is the
primary source of per-run noise):
  - top1_source_match_rate:      regression if drops > 0.05 (5pp)
  - topk_source_match_rate:      regression if drops > 0.05
  - answer_keyword_recall_mean:  regression if drops > 0.05
  - idk_rate:                    regression if rises  > 0.10 (10pp — higher = worse)

Token counts (avg_input_tokens, avg_output_tokens) are informational only.

Usage:
    python -m scripts.check_regression --current data/eval_current.raw.json \\
                                       --baseline evals/baseline.fast.json
"""
from __future__ import annotations

import argparse
import json
import sys

from scripts.run_eval import cheap_proxies

TOLERANCES = {
    "top1_source_match_rate":     {"direction": "down", "threshold": 0.05},
    "topk_source_match_rate":     {"direction": "down", "threshold": 0.05},
    "answer_keyword_recall_mean": {"direction": "down", "threshold": 0.05},
    "idk_rate":                   {"direction": "up",   "threshold": 0.10},
}


def load_results(path: str) -> list[dict]:
    with open(path) as f:
        data = json.load(f)
    return data["results"] if isinstance(data, dict) else data


def check(current_proxies: dict, baseline_proxies: dict) -> list[str]:
    """Return list of regression messages (empty = pass)."""
    failures = []
    for metric, rule in TOLERANCES.items():
        cur = current_proxies.get(metric)
        base = baseline_proxies.get(metric)
        if cur is None or base is None:
            failures.append(f"{metric}: missing (current={cur}, baseline={base})")
            continue
        delta = cur - base
        bad = (rule["direction"] == "down" and delta < -rule["threshold"]) or \
              (rule["direction"] == "up" and delta > rule["threshold"])
        if bad:
            failures.append(
                f"{metric}: {cur:.3f} vs baseline {base:.3f} "
                f"(Δ {delta:+.3f}, tolerance ±{rule['threshold']:.2f} {rule['direction']})"
            )
    return failures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--current", required=True, help="Current eval raw JSON")
    ap.add_argument("--baseline", required=True, help="Baseline eval raw JSON")
    args = ap.parse_args()

    current = cheap_proxies(load_results(args.current))
    baseline = cheap_proxies(load_results(args.baseline))

    print(f"{'metric':<32} {'current':>10} {'baseline':>10} {'Δ':>10}  verdict")
    print("-" * 74)
    for metric, rule in TOLERANCES.items():
        cur = current.get(metric)
        base = baseline.get(metric)
        if cur is None or base is None:
            print(f"{metric:<32} {str(cur):>10} {str(base):>10} {'-':>10}  MISSING")
            continue
        d = cur - base
        # verdict: better / worse / within tolerance
        better = (rule["direction"] == "down" and d > 0.001) or \
                 (rule["direction"] == "up" and d < -0.001)
        worse_exceeds = (rule["direction"] == "down" and d < -rule["threshold"]) or \
                        (rule["direction"] == "up" and d > rule["threshold"])
        if worse_exceeds:
            verdict = "✗ REGRESSION"
        elif better:
            verdict = "✓ improved"
        elif abs(d) < 0.001:
            verdict = "= identical"
        else:
            verdict = "~ within tolerance"
        print(f"{metric:<32} {cur:>10.3f} {base:>10.3f} {d:>+10.3f}  {verdict}")

    failures = check(current, baseline)
    if failures:
        print("\nREGRESSION — gate blocks merge:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"\nAll gated metrics within tolerance. n_current={current['n']} n_baseline={baseline['n']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
