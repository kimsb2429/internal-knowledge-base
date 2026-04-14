#!/usr/bin/env python3
"""
KnowVA HTML pre-processor.

Source-specific normalizations for KnowVA CMS HTML so the generic chunker
receives clean, standard HTML. Run this before chunk_documents.py.

Normalizations:
  1. Heading fix: converts <a name="..."> + <strong> patterns to proper
     <h2>/<h3>/<h4> tags.
  2. Layout-table unwrap: replaces outer layout <table> wrappers (one mega-row
     with >90% of the tokens) with their row contents as block elements.
  3. Div-unwrap tables: lifts <table> elements out of <div> wrappers so they
     become direct siblings for element-boundary splitting.

Heading hierarchy:
  S[IVX]+        → h2 (subchapter)
  Topic\d+       → h2 (topic — newer articles)
  \d{3,}         → h3 (section, e.g. 801)
  \d{3,}[a-z]    → h4 (subsection, e.g. 801a)
  \d{3,}\d[a-z]  → h4 (deep subsection, e.g. 8051a)
  [A-Z]          → h3 (single letter sections)
  [A-Z][a-z]     → h4 (letter combos, e.g. Aa)

Input:  data/knowva_manuals/articles/*.html (raw crawled HTML)
Output: data/knowva_manuals/preprocessed/*.html (heading tags normalized)

Run from repo root:
    python3 scripts/knowva_preprocess.py
"""

import glob
import os
import re

import tiktoken
from bs4 import BeautifulSoup, NavigableString, Tag

TOKENIZER = tiktoken.get_encoding("cl100k_base")

ARTICLE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "data", "knowva_manuals", "articles"
)
OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "data", "knowva_manuals", "preprocessed"
)


def classify_anchor(name: str) -> str | None:
    """Map anchor name to heading level."""
    name = name.strip("#")
    if re.match(r"^[Tt]op$", name) or re.match(r"^_top$", name, re.IGNORECASE):
        return None  # navigation, not a heading
    if re.match(r"^S[IVX]+$", name):
        return "h2"  # subchapter
    if re.match(r"^Topic\d+$", name):
        return "h2"  # topic (newer articles)
    if re.match(r"^f\d+", name):
        return None  # figure reference
    if re.match(r"^_Hlk", name):
        return None  # Word bookmark
    if re.match(r"^\d{3,}\d[a-z]$", name):
        return "h4"  # deep subsection like 8051a
    if re.match(r"^\d{3,}[a-z]$", name):
        return "h4"  # subsection like 801a
    if re.match(r"^\d{3,}$", name):
        return "h3"  # section like 801
    if re.match(r"^[A-Z]$", name):
        return "h3"
    if re.match(r"^[A-Z][a-z]$", name):
        return "h4"
    return None


def get_anchor_text(anchor) -> str:
    """Extract heading text from the anchor and its surrounding context."""
    # Pattern 1: <a name="X"><strong>text</strong></a>
    strong = anchor.find("strong")
    if strong:
        return strong.get_text(strip=True)

    # Pattern 2: <a name="X"></a><strong>text</strong>
    next_sib = anchor.next_sibling
    while next_sib and isinstance(next_sib, NavigableString) and not next_sib.strip():
        next_sib = next_sib.next_sibling
    if next_sib and next_sib.name == "strong":
        return next_sib.get_text(strip=True)

    # Pattern 3: text is directly after anchor in parent
    parent = anchor.parent
    if parent:
        text = parent.get_text(strip=True)
        if text:
            return text

    return ""


def preprocess_headings(html: str) -> str:
    """Convert <a name> + <strong> patterns to proper heading tags."""
    soup = BeautifulSoup(html, "html.parser")

    # Collect replacements first to avoid modifying tree while iterating
    replacements = []
    for anchor in soup.find_all("a", attrs={"name": True}):
        name = anchor["name"]
        level = classify_anchor(name)
        if not level:
            continue

        text = get_anchor_text(anchor)
        if not text:
            continue

        # Find the containing <p> block to replace
        container = anchor
        for parent in anchor.parents:
            if parent.name in ("p", "div"):
                container = parent
                break

        replacements.append((container, level, text, name))

    # Apply replacements — skip if container was already removed from tree
    for container, level, text, name in replacements:
        if not container.parent:
            continue
        heading = soup.new_tag(level)
        heading.string = text
        heading["id"] = name
        container.insert_before(heading)
        container.decompose()

    return str(soup)


def _count_tokens(text: str) -> int:
    return len(TOKENIZER.encode(text))


def unwrap_layout_tables(html: str) -> str:
    """Replace layout <table> wrappers with their content as block elements.

    Detects layout tables: one row holds >90% of the table's tokens (a "mega-row"
    containing the real content). Replaces the outer <table> with the contents of
    each row as <div> blocks, so nested data tables become direct children.
    """
    soup = BeautifulSoup(html, "html.parser")
    changed = False

    # Process top-level tables only (not nested ones)
    for table in soup.find_all("table"):
        if table.find_parent("table"):
            continue

        table_tokens = _count_tokens(str(table))
        if table_tokens < 5000:
            continue

        tbody = table.find("tbody") or table
        rows = tbody.find_all("tr", recursive=False)
        if not rows:
            continue

        # Check for layout pattern: one row has >90% of tokens
        row_tokens = [_count_tokens(str(r)) for r in rows]
        max_row_tokens = max(row_tokens)
        if max_row_tokens / table_tokens <= 0.9:
            continue

        # This is a layout table — unwrap each row's contents
        for row in rows:
            cells = row.find_all(["td", "th"], recursive=False)
            for cell in cells:
                # Wrap cell contents in a div to preserve block structure
                wrapper = soup.new_tag("div")
                for child in list(cell.children):
                    wrapper.append(child.extract())
                table.insert_before(wrapper)

        table.decompose()
        changed = True

    return str(soup) if changed else html


def unwrap_div_tables(html: str) -> str:
    """Lift <table> elements out of <div> wrappers.

    When a <div> contains a <table> (possibly alongside other content), replace
    the <div> with its children so the <table> becomes a direct sibling of
    surrounding elements. This lets the chunker's element-boundary splitter
    see tables at the top level.
    """
    soup = BeautifulSoup(html, "html.parser")
    changed = False

    # Find divs that contain tables (not inside tables themselves)
    for div in soup.find_all("div"):
        if div.find_parent("table"):
            continue
        if not div.find("table"):
            continue
        # Unwrap: replace div with its children
        div.unwrap()
        changed = True

    return str(soup) if changed else html


def main():
    article_dir = os.path.normpath(ARTICLE_DIR)
    output_dir = os.path.normpath(OUTPUT_DIR)
    os.makedirs(output_dir, exist_ok=True)

    html_files = sorted(glob.glob(os.path.join(article_dir, "*.html")))
    print(f"Pre-processing {len(html_files)} HTML articles...")

    for html_path in html_files:
        article_id = os.path.basename(html_path)
        with open(html_path) as f:
            html = f.read()

        processed = preprocess_headings(html)
        processed = unwrap_layout_tables(processed)
        processed = unwrap_div_tables(processed)
        output_path = os.path.join(output_dir, article_id)
        with open(output_path, "w") as f:
            f.write(processed)

    print(f"Output: {output_dir}/ ({len(html_files)} files)")


if __name__ == "__main__":
    main()
