#!/usr/bin/env python3
"""
Parse KnowVA HTML articles to structured markdown for chunking.

Strips the crawler-added chrome (head, nav breadcrumb, meta tags) and converts
the article body to clean markdown with preserved tables, headings, and lists.

Output: data/knowva_manuals/parsed/{article_id}.md

Run from repo root:
    python3 scripts/parse_html_to_markdown.py
"""

import os
import re

from bs4 import BeautifulSoup
from markdownify import markdownify

ARTICLE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "data", "knowva_manuals", "articles"
)
OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "data", "knowva_manuals", "parsed"
)


def parse_article(html_path: str) -> str:
    """Convert a KnowVA HTML article to clean markdown."""
    with open(html_path) as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # Remove crawler-added chrome: <head>, <nav class="topic-breadcrumb">
    for tag in soup.find_all("nav", class_="topic-breadcrumb"):
        tag.decompose()

    # Get just the body content
    body = soup.find("body")
    if not body:
        body = soup

    # Convert to markdown
    md = markdownify(str(body), heading_style="ATX", strip=["script", "style"])

    # Remove "Go to Top" navigation links (various case/punctuation variants)
    md = re.sub(r"\[Go to [Tt]op\.?\]\([^)]*\)\s*", "", md)

    # Clean up excessive whitespace
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = md.strip()

    return md


def main():
    article_dir = os.path.normpath(ARTICLE_DIR)
    output_dir = os.path.normpath(OUTPUT_DIR)
    os.makedirs(output_dir, exist_ok=True)

    html_files = sorted(f for f in os.listdir(article_dir) if f.endswith(".html"))

    total = 0
    total_chars = 0

    for fname in html_files:
        html_path = os.path.join(article_dir, fname)
        article_id = fname.replace(".html", "")
        md_path = os.path.join(output_dir, f"{article_id}.md")

        md = parse_article(html_path)

        with open(md_path, "w") as f:
            f.write(md)

        total += 1
        total_chars += len(md)

    print(f"Parsed {total} articles to {output_dir}/")
    print(f"  Total markdown: {total_chars:,} chars ({total_chars // 1024:,} KB)")
    if total:
        print(f"  Avg per article: {total_chars // total:,} chars")


if __name__ == "__main__":
    main()
