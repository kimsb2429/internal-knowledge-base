#!/usr/bin/env python3
"""
Enrich all KnowVA article metadata JSONs:

1. Re-extract heading_outline using the improved _extract_headings()
   (handles KnowVA's non-semantic heading markup)
2. Add acl: "public" (KnowVA is publicly accessible)
3. Add source_authority_tier: 1 (authoritative VA manuals)
4. Classify content_category based on manual structure / topic breadcrumbs

Run from repo root:
    python3 scripts/enrich_metadata.py
"""

import json
import os
import re
import sys
from collections import Counter

# Import heading extraction from the crawler
sys.path.insert(0, os.path.dirname(__file__))
from crawl_knowva import _extract_headings

ARTICLE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "data", "knowva_manuals", "articles"
)

# --- Content category ---
# Multi-purpose tag used for: freshness decay curves, retrieval filtering/faceting,
# and chunking strategy.  All KnowVA articles share the same decay rate — they're
# authoritative VA manuals updated infrequently.  When Confluence/Jira sources are
# added, they'll get their own categories (e.g. "confluence_wiki", "jira_ticket").
KNOWVA_CONTENT_CATEGORY = "gov_docs_and_manuals"


def enrich_article(json_path: str, html_path: str) -> dict:
    """Update a single article's metadata JSON."""
    with open(json_path) as f:
        meta = json.load(f)

    with open(html_path) as f:
        html = f.read()

    # 1. Re-extract headings
    headings = _extract_headings(html)
    meta["heading_outline"] = headings
    meta["heading_count"] = len(headings)

    # 2. ACL — KnowVA is public
    meta["acl"] = "public"

    # 3. Source authority tier — authoritative VA manuals
    meta["source_authority_tier"] = 1

    # 4. Content category
    meta["content_category"] = KNOWVA_CONTENT_CATEGORY

    with open(json_path, "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    return meta


def main():
    article_dir = os.path.normpath(ARTICLE_DIR)
    json_files = sorted(
        f for f in os.listdir(article_dir) if f.endswith(".json")
    )

    updated = 0
    heading_stats = {"total": 0, "with_headings": 0, "total_headings": 0}
    category_counts: Counter = Counter()

    for fname in json_files:
        json_path = os.path.join(article_dir, fname)
        html_path = os.path.join(article_dir, fname.replace(".json", ".html"))

        if not os.path.exists(html_path):
            print(f"  SKIP {fname} — no matching HTML file")
            continue

        meta = enrich_article(json_path, html_path)
        updated += 1

        heading_stats["total"] += 1
        if meta["heading_count"] > 0:
            heading_stats["with_headings"] += 1
            heading_stats["total_headings"] += meta["heading_count"]
        category_counts[meta["content_category"]] += 1

    print(f"\nUpdated {updated} article metadata files")
    print(f"  Headings: {heading_stats['with_headings']}/{heading_stats['total']} "
          f"articles have headings ({heading_stats['total_headings']} total)")
    if heading_stats["with_headings"]:
        avg = heading_stats["total_headings"] / heading_stats["with_headings"]
        print(f"  Avg headings per article: {avg:.1f}")
    print("  Added: acl='public', source_authority_tier=1")
    print("  Content categories:")
    for cat, count in category_counts.most_common():
        print(f"    {cat}: {count}")


if __name__ == "__main__":
    main()
