"""
KnowVA Knowledge Base Crawler
Crawls VA manuals from knowva.ebenefits.va.gov using the eGain v11 API.

Designed to produce output suitable for element-aware chunking (Docling
HybridChunker) and ingestion into a pgvector RAG pipeline.

Strategy (pure API — no headless browser needed):
  Phase 1 — Walk the topic tree via the topic API with $level parameter
            to discover every leaf topic and its place in the hierarchy.
  Phase 2 — For every leaf topic with articles, paginate the article
            listing API to collect all article IDs.
  Phase 3 — Fetch each article's full content via the single-article API.
            Save raw HTML (structure-preserving) + rich metadata JSON.

Output structure (feeds into Docling):
  data/knowva_manuals/
    _topic_tree.json          # full parent→child hierarchy
    _crawl_manifest.json      # every article with metadata + download status
    articles/
      {article_id}.html       # raw HTML body — headings, tables, lists intact
      {article_id}.json       # metadata aligned to pgvector schema

Usage:
  pip install httpx              # (or: uv pip install httpx)
  python scripts/crawl_knowva.py

  # Dry-run (discover only, no downloads):
  python scripts/crawl_knowva.py --discover-only
"""

import asyncio
import json
import re
import sys
import time
from html import unescape
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PORTAL_ID = "554400000001018"
BASE_URL = "https://www.knowva.ebenefits.va.gov"
API_BASE = f"{BASE_URL}/system/ws/v11/ss"

# Root topics to crawl.  The $level parameter fetches the entire subtree.
# M22-3 real ID is 554400000016105 (not 554400000016107 which is Chapter 01).
MANUAL_TOPICS = {
    "554400000016105": "M22-3",   # Manpower Control and Utilization
    "554400000016106": "M22-4",   # Education Program Administration
}

OUTPUT_DIR = Path("data/knowva_manuals")
ARTICLES_DIR = OUTPUT_DIR / "articles"
TOPIC_TREE_FILE = OUTPUT_DIR / "_topic_tree.json"
MANIFEST_FILE = OUTPUT_DIR / "_crawl_manifest.json"

# Polite crawling
REQUEST_DELAY_S = 2.0
RANGE_SIZE = 25
TOPIC_TREE_DEPTH = 5  # max nesting depth for $level param

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
# topic_id → {name, parent_id, child_ids[], article_count, depth, path[]}
topic_tree: dict[str, dict] = {}

# article_id → {name, topic_id, topic_breadcrumb[], downloaded}
article_index: dict[str, dict] = {}


# ===================================================================
# Phase 1 — Discover full topic tree via API
# ===================================================================

async def phase1_discover_topics(client: httpx.AsyncClient):
    """Fetch the full topic subtree for each manual using $level param."""
    print("=" * 60)
    print("Phase 1: Discovering topic tree via API")
    print("=" * 60)

    for root_id, manual_name in MANUAL_TOPICS.items():
        print(f"\n  Fetching tree for {manual_name} ({root_id})...")
        url = (
            f"{API_BASE}/topic/{root_id}"
            f"?$attribute=name,id,parentTopicId,totalArticleCount,homeArticleId,"
            f"&$lang=en-us"
            f"&$level={TOPIC_TREE_DEPTH}"
            f"&$pagenum=0&$pagesize=1000"
            f"&portalId={PORTAL_ID}"
            f"&usertype=customer"
        )
        resp = await client.get(url)
        if resp.status_code != 200:
            print(f"    ERROR: HTTP {resp.status_code}")
            continue

        _parse_topic_tree_xml(resp.text, manual_name)
        await asyncio.sleep(REQUEST_DELAY_S)

    # Build breadcrumb paths for every topic
    _compute_breadcrumb_paths()

    leaf_count = sum(1 for t in topic_tree.values() if t["article_count"] > 0)
    print(f"\n  Total topics: {len(topic_tree)}")
    print(f"  Leaf topics with articles: {leaf_count}")


def _parse_topic_tree_xml(xml_text: str, manual_name: str):
    """Parse the nested ns2:topicTree XML into the flat topic_tree dict."""
    # The XML nests children inside <ns2:topicTree> wrappers.
    # Topic tags look like: <ns2:topic childCount="8" id="554400000016105">
    # Fields use ns2: prefix: <ns2:name>, <ns2:articleCount>, etc.

    # Match every <ns2:topic ...> block (non-greedy to the closing tag)
    for m in re.finditer(
        r'<ns2:topic\s+childCount="(\d+)"\s+id="(\d+)">(.*?)</ns2:topic>',
        xml_text, re.DOTALL,
    ):
        child_count = int(m.group(1))
        tid = m.group(2)
        block = m.group(3)

        name = _xml_val_ns2(block, "name") or ""
        parent_id = _xml_val_ns2(block, "parentTopicId")
        article_count = int(_xml_val_ns2(block, "articleCount") or 0)
        total_article_count = int(_xml_val_ns2(block, "articleTotalCount") or 0)

        if tid not in topic_tree:
            topic_tree[tid] = {
                "name": name,
                "parent_id": parent_id,
                "child_ids": [],
                "article_count": article_count,
                "total_article_count": total_article_count,
                "child_count": child_count,
                "manual_name": manual_name,
                "breadcrumb_path": [],
            }

    # Wire parent → child relationships
    for tid, info in topic_tree.items():
        pid = info.get("parent_id")
        if pid and pid in topic_tree:
            if tid not in topic_tree[pid]["child_ids"]:
                topic_tree[pid]["child_ids"].append(tid)


def _compute_breadcrumb_paths():
    """Walk up from each topic to build the full breadcrumb path."""
    for tid in topic_tree:
        path = []
        current = tid
        seen = set()
        while current and current in topic_tree and current not in seen:
            seen.add(current)
            path.append(topic_tree[current]["name"])
            current = topic_tree[current].get("parent_id")
        path.reverse()
        topic_tree[tid]["breadcrumb_path"] = path


# ===================================================================
# Phase 2 — Enumerate articles from leaf topics
# ===================================================================

async def phase2_enumerate_articles(client: httpx.AsyncClient):
    """For each topic with article_count > 0, paginate the listing API."""
    print("\n" + "=" * 60)
    print("Phase 2: Enumerating all articles via listing API")
    print("=" * 60)

    leaf_topics = [
        (tid, info) for tid, info in topic_tree.items()
        if info["article_count"] > 0
    ]
    print(f"  Leaf topics to query: {len(leaf_topics)}")

    for idx, (tid, info) in enumerate(leaf_topics):
        range_start = 0
        topic_name = info["name"]
        while True:
            url = (
                f"{API_BASE}/article"
                f"?$attribute=name,id,lastModifiedDate"
                f"&$lang=en-us"
                f"&$rangesize={RANGE_SIZE}"
                f"&$rangestart={range_start}"
                f"&portalId={PORTAL_ID}"
                f"&topicId={tid}"
                f"&usertype=customer"
            )
            resp = await client.get(url)
            if resp.status_code != 200:
                print(f"    Error listing topic {tid}: HTTP {resp.status_code}")
                break

            text = resp.text
            count = int(_xml_val(text, "count") or 0)
            max_range = int(_xml_val(text, "maxRange") or 0)

            if count == 0:
                break

            for m in re.finditer(
                r'<(?:ns2:)?article\s[^>]*id="(\d+)"[^>]*>(.*?)</(?:ns2:)?article>',
                text, re.DOTALL,
            ):
                aid = m.group(1)
                block = m.group(2)
                if aid in article_index:
                    continue

                name = _xml_val(block, "name") or ""
                breadcrumb = info.get("breadcrumb_path", []).copy()

                article_index[aid] = {
                    "id": aid,
                    "name": name,
                    "topic_id": tid,
                    "topic_name": topic_name,
                    "topic_breadcrumb": breadcrumb,
                    "manual_name": info.get("manual_name", ""),
                    "downloaded": False,
                }

            range_start += RANGE_SIZE
            if range_start >= max_range:
                break
            await asyncio.sleep(REQUEST_DELAY_S)

        if (idx + 1) % 20 == 0:
            print(f"    ...queried {idx+1}/{len(leaf_topics)} topics, "
                  f"{len(article_index)} articles found so far")
        await asyncio.sleep(REQUEST_DELAY_S)

    print(f"\n  Total articles discovered: {len(article_index)}")


# ===================================================================
# Phase 3 — Download full article content
# ===================================================================

async def phase3_download_articles(client: httpx.AsyncClient):
    """Fetch full content for every article. Save raw HTML + metadata."""
    print("\n" + "=" * 60)
    print("Phase 3: Downloading article content")
    print("=" * 60)

    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    to_download = [
        (aid, info) for aid, info in article_index.items()
        if not info.get("downloaded")
    ]
    total = len(to_download)
    print(f"  Articles to download: {total}")

    for i, (aid, info) in enumerate(to_download):
        print(f"  [{i+1}/{total}] {info.get('name', aid)}")

        url = (
            f"{API_BASE}/article/{aid}"
            f"?$lang=en-us&portalId={PORTAL_ID}&usertype=customer"
        )
        resp = await client.get(url)
        if resp.status_code != 200:
            print(f"    FAILED: HTTP {resp.status_code}")
            continue

        article_data = _parse_full_article(aid, resp.text)
        if not article_data:
            print(f"    FAILED: could not parse article XML")
            continue

        # Merge listing-level info (topic tree context)
        article_data["topic_id"] = info.get("topic_id")
        article_data["manual_name"] = info.get("manual_name", "")
        if not article_data.get("topic_breadcrumb"):
            article_data["topic_breadcrumb"] = info.get("topic_breadcrumb", [])

        # --- Save raw HTML (structure intact for Docling) ---
        html_path = ARTICLES_DIR / f"{aid}.html"
        html_path.write_text(
            _build_structured_html(article_data), encoding="utf-8"
        )

        # --- Save metadata JSON (maps to pgvector schema) ---
        meta = _build_metadata(article_data)
        meta_path = ARTICLES_DIR / f"{aid}.json"
        meta_path.write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        info["downloaded"] = True
        _save_manifest()  # checkpoint after each article

        await asyncio.sleep(REQUEST_DELAY_S)


# ===================================================================
# Article parsing + output formatting
# ===================================================================

def _parse_full_article(aid: str, xml_text: str) -> dict | None:
    """Extract all fields from a single-article API response."""
    m = re.search(
        r'<(?:ns2:)?article\s[^>]*id="(\d+)"[^>]*>(.*)</(?:ns2:)?article>',
        xml_text, re.DOTALL,
    )
    if not m:
        return None
    # aid from attribute confirms match; block is the inner content
    block = m.group(2)

    # Content — ns2:content with XML-escaped HTML, or CDATA-wrapped
    content_html = ""
    cm = re.search(r'<(?:ns2:)?content>(.*?)</(?:ns2:)?content>', block, re.DOTALL)
    if cm:
        raw = cm.group(1).strip()
        if raw.startswith("<![CDATA["):
            content_html = raw[9:-3]
        else:
            # XML-escaped HTML: &lt;p&gt; → <p>
            content_html = unescape(unescape(raw))  # double-unescape for &amp;nbsp; etc.

    # Topic breadcrumb from article response
    breadcrumb = []
    bc = re.search(r'<topicBreadcrumb>(.*?)</topicBreadcrumb>', block, re.DOTALL)
    if bc:
        breadcrumb = re.findall(r'<name>(.*?)</name>', bc.group(1))

    # Custom attributes
    custom_attrs = {}
    for ca in re.finditer(
        r'<(?:ns2:)?customAttribute>(.*?)</(?:ns2:)?customAttribute>',
        block, re.DOTALL,
    ):
        ca_block = ca.group(1)
        ca_name = _xml_val(ca_block, "attributeName")
        ca_val = _xml_val(ca_block, "attributeValue")
        if ca_name:
            custom_attrs[ca_name] = ca_val

    # Attachments
    attachments = []
    for att in re.finditer(
        r'<(?:ns2:)?attachment>(.*?)</(?:ns2:)?attachment>',
        block, re.DOTALL,
    ):
        att_block = att.group(1)
        att_name = _xml_val(att_block, "name")
        att_url = _xml_val(att_block, "url")
        if att_name:
            attachments.append({"name": att_name, "url": att_url})

    return {
        "id": aid,
        "name": _xml_val(block, "name"),
        "description": _xml_val(block, "description"),
        "content_html": content_html,
        "keywords": _xml_val(block, "keywords"),
        "created_date": _xml_val(block, "createdDate"),
        "last_modified_date": _xml_val(block, "lastModifiedDate"),
        "state": _xml_val(block, "state"),
        "topic_breadcrumb": breadcrumb,
        "custom_attributes": custom_attrs,
        "attachments": attachments,
        "version": _xml_val(block, "version"),
        "alternate_id": _xml_val(block, "alternateId"),
    }


def _build_structured_html(article: dict) -> str:
    """
    Build a self-contained HTML file preserving all structure.

    - Original heading hierarchy (h1-h6), tables, lists are untouched.
    - Topic breadcrumb + metadata in <head> for downstream parsers.
    - Article name as <h1> if not already present in content.
    """
    name = article.get("name", "")
    breadcrumb = article.get("topic_breadcrumb", [])
    content = article.get("content_html", "")
    manual = article.get("manual_name", "")
    bc_str = " &gt; ".join(breadcrumb)

    has_h1 = bool(re.match(r'\s*<h1', content, re.IGNORECASE))
    title_block = "" if has_h1 else f"<h1>{name}</h1>\n"

    # Breadcrumb as structured nav (parseable by Docling, not just a comment)
    nav_block = ""
    if breadcrumb:
        items = " / ".join(f'<span class="bc-item">{b}</span>' for b in breadcrumb)
        nav_block = (
            f'<nav class="topic-breadcrumb" aria-label="Topic hierarchy">'
            f'{items}</nav>\n'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{name}</title>
  <meta name="source-system" content="KnowVA (knowva.ebenefits.va.gov)">
  <meta name="source-type" content="va_manual">
  <meta name="manual-name" content="{manual}">
  <meta name="article-id" content="{article.get('id', '')}">
  <meta name="alternate-id" content="{article.get('alternate_id', '')}">
  <meta name="last-modified" content="{article.get('last_modified_date', '')}">
  <meta name="created" content="{article.get('created_date', '')}">
  <meta name="keywords" content="{article.get('keywords', '')}">
  <meta name="topic-breadcrumb" content="{bc_str}">
  <meta name="content-category" content="{article.get('custom_attributes', {}).get('km_content_type', '')}">
  <meta name="target-audience" content="{article.get('custom_attributes', {}).get('km_target_audience', '')}">
</head>
<body>
{nav_block}{title_block}{content}
</body>
</html>"""


def _build_metadata(article: dict) -> dict:
    """
    Build metadata JSON aligned to the pgvector document_chunks schema.

    Fields map to:
      source_type          → 'va_manual'
      heading_breadcrumb   → topic hierarchy path
      last_modified        → from article API
      content_category     → from km_content_type custom attribute
      contains_table       → detected from HTML
      source_id            → KnowVA article ID
    """
    content = article.get("content_html", "")

    contains_table = bool(re.search(r'<table[\s>]', content, re.IGNORECASE))
    contains_list = bool(re.search(r'<[ou]l[\s>]', content, re.IGNORECASE))

    # Extract heading hierarchy within the article content
    headings = []
    for hm in re.finditer(
        r'<(h[1-6])[^>]*>(.*?)</\1>', content, re.IGNORECASE | re.DOTALL
    ):
        level = int(hm.group(1)[1])
        text = re.sub(r'<[^>]+>', '', hm.group(2)).strip()
        if text:
            headings.append({"level": level, "text": text})

    custom_attrs = article.get("custom_attributes", {})

    return {
        # --- Identity ---
        "article_id": article["id"],
        "alternate_id": article.get("alternate_id"),
        "source_type": "va_manual",
        "source_system": "knowva.ebenefits.va.gov",
        "source_url": (
            f"{BASE_URL}/system/templates/selfservice/va_ssnew/help/customer"
            f"/locale/en-US/portal/{PORTAL_ID}/content/{article['id']}"
        ),

        # --- Document-level hierarchy (from topic tree) ---
        "topic_breadcrumb": article.get("topic_breadcrumb", []),
        "topic_id": article.get("topic_id"),
        "manual_name": article.get("manual_name", ""),

        # --- Article metadata ---
        "title": article.get("name"),
        "description": article.get("description"),
        "keywords": article.get("keywords"),
        "last_modified": article.get("last_modified_date"),
        "created": article.get("created_date"),
        "version": article.get("version"),
        "state": article.get("state"),

        # --- Content structure (for chunking decisions) ---
        "contains_table": contains_table,
        "contains_list": contains_list,
        "heading_outline": headings,
        "heading_count": len(headings),

        # --- Classification ---
        "content_category": custom_attrs.get("km_content_type", ""),
        "target_audience": custom_attrs.get("km_target_audience", ""),
        "process_change": custom_attrs.get("km_process_change", ""),

        # --- Attachments (PDFs — may want to ingest separately via Docling) ---
        "attachments": article.get("attachments", []),
    }


# ===================================================================
# Helpers
# ===================================================================

def _xml_val(text: str, tag: str) -> str | None:
    """Quick regex extraction of a single XML tag value (plain or ns2: prefix)."""
    m = re.search(rf'<(?:ns2:)?{tag}>(.*?)</(?:ns2:)?{tag}>', text, re.DOTALL)
    return m.group(1).strip() if m else None


def _xml_val_ns2(text: str, tag: str) -> str | None:
    """Extract value from an ns2:-prefixed tag."""
    m = re.search(rf'<ns2:{tag}>(.*?)</ns2:{tag}>', text, re.DOTALL)
    return m.group(1).strip() if m else None


# ===================================================================
# Persistence — resume support
# ===================================================================

def _load_prior_state():
    """If a prior crawl exists, mark already-downloaded articles."""
    if not MANIFEST_FILE.exists():
        return
    prior = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    for aid, info in prior.get("articles", {}).items():
        if info.get("downloaded") and (ARTICLES_DIR / f"{aid}.html").exists():
            if aid not in article_index:
                article_index[aid] = info
            else:
                article_index[aid]["downloaded"] = True
    count = sum(1 for a in article_index.values() if a.get("downloaded"))
    if count:
        print(f"  Resuming: {count} articles already downloaded")


def _save_manifest():
    """Save current state for resume support."""
    manifest = {
        "crawl_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": BASE_URL,
        "portal_id": PORTAL_ID,
        "manuals_crawled": list(MANUAL_TOPICS.values()),
        "stats": {
            "topics_discovered": len(topic_tree),
            "articles_discovered": len(article_index),
            "articles_downloaded": sum(
                1 for a in article_index.values() if a.get("downloaded")
            ),
        },
        "articles": {
            aid: {
                "name": info.get("name"),
                "topic_id": info.get("topic_id"),
                "topic_breadcrumb": info.get("topic_breadcrumb", []),
                "manual_name": info.get("manual_name", ""),
                "downloaded": info.get("downloaded", False),
            }
            for aid, info in article_index.items()
        },
    }
    MANIFEST_FILE.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _save_topic_tree():
    """Save the full topic tree for downstream reference."""
    TOPIC_TREE_FILE.write_text(
        json.dumps(topic_tree, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ===================================================================
# Main
# ===================================================================

async def main():
    discover_only = "--discover-only" in sys.argv

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

    _load_prior_state()

    async with httpx.AsyncClient(
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 VA-KnowVA-Research-Crawler/1.0"
            ),
            "Accept": "application/xml",
        },
        timeout=30.0,
        follow_redirects=True,
    ) as client:

        # Phase 1 — discover topic tree
        await phase1_discover_topics(client)
        _save_topic_tree()

        # Phase 2 — enumerate articles
        await phase2_enumerate_articles(client)
        _save_manifest()

        if discover_only:
            print(f"\n  --discover-only: skipping downloads.")
            print(f"  Topics:   {len(topic_tree)}")
            print(f"  Articles: {len(article_index)}")
            return

        # Phase 3 — download full content
        await phase3_download_articles(client)

    _save_manifest()

    downloaded = sum(1 for a in article_index.values() if a.get("downloaded"))
    print("\n" + "=" * 60)
    print("Done!")
    print(f"  Topics:              {len(topic_tree)}")
    print(f"  Articles discovered: {len(article_index)}")
    print(f"  Articles downloaded: {downloaded}")
    print(f"  Output:              {ARTICLES_DIR}/")
    print(f"  Topic tree:          {TOPIC_TREE_FILE}")
    print(f"  Manifest:            {MANIFEST_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
