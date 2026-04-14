#!/usr/bin/env python3
"""
Chunk pre-processed documents for embedding.

Source-agnostic: takes a directory of pre-processed HTML and/or markdown files,
splits them by headings, merges small chunks, and flags oversized ones for
summary indexing.

HTML splitting: custom splitter that preserves raw HTML (including <table> tags)
in chunk content. LangChain's HTMLHeaderTextSplitter strips tags, which destroys
table structure.

Expects:
  - HTML files have proper heading tags (h1-h4) — run source-specific
    pre-processors first (e.g. knowva_preprocess.py)
  - Markdown files have ATX headings (#, ##, ###, ####)
  - Each file has a companion .json metadata sidecar (optional)

Output: data/knowva_manuals/chunks/all_chunks.json

Run from repo root:
    python3 scripts/chunk_documents.py
"""

import glob
import json
import os
import re

from bs4 import BeautifulSoup, Tag
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
import tiktoken

# Directories — override via env vars or edit here
HTML_DIR = os.environ.get(
    "CHUNK_HTML_DIR",
    os.path.join(os.path.dirname(__file__), "..", "data", "knowva_manuals", "preprocessed"),
)
MD_DIR = os.environ.get(
    "CHUNK_MD_DIR",
    os.path.join(os.path.dirname(__file__), "..", "data", "vadir_parsed"),
)
OUTPUT_DIR = os.environ.get(
    "CHUNK_OUTPUT_DIR",
    os.path.join(os.path.dirname(__file__), "..", "data", "knowva_manuals", "chunks"),
)

# Metadata sidecar directories — look here for .json files matching source IDs
META_DIRS = [
    os.path.join(os.path.dirname(__file__), "..", "data", "knowva_manuals", "articles"),
    os.path.join(os.path.dirname(__file__), "..", "data"),
]

TOKENIZER = tiktoken.get_encoding("cl100k_base")
OVERSIZE_THRESHOLD = 1024  # tokens — tables/lists above this get summary-indexed
MERGE_THRESHOLD = 50  # tokens — chunks below this get merged with next
PROSE_CHUNK_SIZE = 800  # tokens — max size for prose sub-chunks
PROSE_CHUNK_OVERLAP = 100  # tokens — overlap between prose sub-chunks
TABLE_SPLIT_THRESHOLD = 50000  # tokens — tables above this get row-group split
TABLE_ROW_GROUP_TARGET = 800  # tokens — target size per row-group chunk

HEADING_TAGS = {"h1", "h2", "h3", "h4"}
HEADING_LEVELS = ("h1", "h2", "h3", "h4")

MD_SPLITTER = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
        ("####", "h4"),
    ]
)


def count_tokens(text: str) -> int:
    return len(TOKENIZER.encode(text))


def split_html_by_headings(html: str) -> list[dict]:
    """Split HTML into chunks at heading boundaries, preserving raw HTML content.

    Returns list of dicts with 'content' (raw HTML string) and 'heading_path'
    (dict mapping h1-h4 to heading text).
    """
    soup = BeautifulSoup(html, "html.parser")
    body = soup.find("body") or soup

    chunks = []
    current_content = []
    current_headings = {}

    for element in body.children:
        if isinstance(element, Tag) and element.name in HEADING_TAGS:
            # Flush current chunk
            content_html = "".join(str(e) for e in current_content).strip()
            if content_html:
                chunks.append({
                    "content": content_html,
                    "heading_path": dict(current_headings),
                })

            # Update heading stack — clear deeper levels
            level = element.name
            heading_text = element.get_text(strip=True)
            current_headings[level] = heading_text
            # Clear any deeper heading levels
            level_num = int(level[1])
            for deeper in HEADING_LEVELS:
                if int(deeper[1]) > level_num:
                    current_headings.pop(deeper, None)

            current_content = []
        else:
            current_content.append(element)

    # Flush final chunk
    content_html = "".join(str(e) for e in current_content).strip()
    if content_html:
        chunks.append({
            "content": content_html,
            "heading_path": dict(current_headings),
        })

    return chunks


ELEMENT_BOUNDARY_TAGS = {"table", "ul", "ol"}


def split_chunk_by_elements(chunk: dict) -> list[dict]:
    """Split a chunk at table/list boundaries so each gets its own chunk.

    Consecutive non-boundary elements (p, div, span, etc.) stay grouped as prose.
    Small table/list chunks will be merged later by merge_small_chunks.

    Expects pre-processed HTML where tables/lists are direct children (not wrapped
    in divs). Run source-specific pre-processors first to normalize the HTML.
    """
    content = chunk["content"]
    heading_path = chunk["heading_path"]

    soup = BeautifulSoup(content, "html.parser")

    # If content is just text nodes or has no boundary elements, return as-is
    boundary_elements = soup.find_all(ELEMENT_BOUNDARY_TAGS)
    if not boundary_elements:
        return [chunk]

    sub_chunks = []
    current_elements = []

    def flush():
        html = "".join(str(e) for e in current_elements).strip()
        if html:
            sub_chunks.append({
                "content": html,
                "heading_path": dict(heading_path),
            })

    for element in soup.children:
        if isinstance(element, Tag) and element.name in ELEMENT_BOUNDARY_TAGS:
            # Flush prose before this boundary element
            flush()
            current_elements = []
            # Boundary element gets its own chunk
            sub_chunks.append({
                "content": str(element).strip(),
                "heading_path": dict(heading_path),
            })
        else:
            current_elements.append(element)

    # Flush trailing prose
    flush()

    return sub_chunks if sub_chunks else [chunk]


def detect_chunk_type(content: str) -> str:
    """Classify chunk content as text, table, or list."""
    content_lower = content.lower()
    if "<table" in content_lower:
        return "table"
    if "<ul" in content_lower or "<ol" in content_lower:
        li_count = content_lower.count("<li")
        line_count = max(len(content.split("\n")), 1)
        if li_count / line_count > 0.3:
            return "list"
    return "text"


def merge_small_chunks(chunks: list[dict]) -> list[dict]:
    """Merge chunks under MERGE_THRESHOLD tokens with the next chunk."""
    if not chunks:
        return chunks

    merged = []
    i = 0
    while i < len(chunks):
        chunk = chunks[i]
        tokens = count_tokens(chunk["content"])

        if tokens < MERGE_THRESHOLD and i + 1 < len(chunks):
            next_chunk = chunks[i + 1]
            next_chunk["content"] = chunk["content"] + "\n" + next_chunk["content"]
            # Carry forward heading context
            for level in HEADING_LEVELS:
                if level in chunk["heading_path"] and level not in next_chunk["heading_path"]:
                    next_chunk["heading_path"][level] = chunk["heading_path"][level]
            i += 1
        else:
            merged.append(chunk)
            i += 1

    return merged


def _find_splittable_table(soup: BeautifulSoup) -> Tag | None:
    """Find the largest table with enough rows to split."""
    tables = soup.find_all("table")
    if not tables:
        return None

    best = None
    best_tokens = 0
    for t in tables:
        tbody = t.find("tbody") or t
        rows = tbody.find_all("tr", recursive=False)
        if len(rows) < 4:  # too few rows to split meaningfully
            continue
        t_tokens = count_tokens(str(t))
        if t_tokens > best_tokens:
            best = t
            best_tokens = t_tokens

    return best


def split_table_by_row_groups(content: str) -> list[str] | None:
    """Split a large table into row-group chunks, each with the header repeated.

    Returns a list of HTML strings, or None if the table can't be split.
    """
    soup = BeautifulSoup(content, "html.parser")
    table = _find_splittable_table(soup)
    if not table:
        return None

    tbody = table.find("tbody") or table
    rows = tbody.find_all("tr", recursive=False)
    if len(rows) < 4:
        return None

    # Detect header rows: rows at the top that contain <th> or are short
    header_rows = []
    for row in rows:
        if row.find("th") or count_tokens(str(row)) < 50:
            header_rows.append(row)
        else:
            break

    # If no header detected, use first row as header
    if not header_rows:
        header_rows = [rows[0]]

    data_rows = rows[len(header_rows):]
    if not data_rows:
        return None

    header_html = "".join(str(r) for r in header_rows)
    header_tokens = count_tokens(header_html)

    # Build the table shell (opening tag with attributes)
    table_attrs = " ".join(f'{k}="{v}"' for k, v in (table.attrs or {}).items())
    table_open = f"<table {table_attrs}>" if table_attrs else "<table>"
    tbody_tag = "<tbody>" if table.find("tbody") else ""
    tbody_close = "</tbody>" if tbody_tag else ""

    # Collect content outside the split table (preamble/postamble)
    # Replace the table in the soup with a placeholder to extract surrounding content
    preamble_parts = []
    postamble_parts = []
    found_table = False
    for sibling in (soup if table.parent == soup else table.parent).children:
        if sibling is table:
            found_table = True
            continue
        if isinstance(sibling, Tag) or (isinstance(sibling, str) and sibling.strip()):
            if not found_table:
                preamble_parts.append(str(sibling))
            else:
                postamble_parts.append(str(sibling))

    preamble = "".join(preamble_parts).strip()
    postamble = "".join(postamble_parts).strip()

    # Group data rows by token budget
    groups = []
    current_group = []
    current_tokens = 0

    for row in data_rows:
        row_tokens = count_tokens(str(row))
        if current_group and current_tokens + row_tokens > TABLE_ROW_GROUP_TARGET:
            groups.append(current_group)
            current_group = []
            current_tokens = 0
        current_group.append(row)
        current_tokens += row_tokens

    if current_group:
        groups.append(current_group)

    if len(groups) <= 1:
        return None  # didn't actually split

    # Build chunk HTML for each group
    chunks = []
    for group in groups:
        rows_html = "".join(str(r) for r in group)
        chunk_html = f"{table_open}{tbody_tag}{header_html}{rows_html}{tbody_close}</table>"
        # Include preamble only on first chunk
        if not chunks and preamble:
            chunk_html = preamble + "\n" + chunk_html
        chunks.append(chunk_html)

    # Include postamble on last chunk
    if postamble and chunks:
        chunks[-1] = chunks[-1] + "\n" + postamble

    return chunks


def split_oversized_prose(content: str) -> list[str]:
    """Split oversized prose into sub-chunks with overlap."""
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=PROSE_CHUNK_SIZE,
        chunk_overlap=PROSE_CHUNK_OVERLAP,
    )
    return splitter.split_text(content)


def find_metadata(source_id: str) -> dict:
    """Look for a .json metadata sidecar in known directories."""
    for meta_dir in META_DIRS:
        meta_path = os.path.join(os.path.normpath(meta_dir), f"{source_id}.json")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                return json.load(f)
    return {}


def finalize_chunks(raw_chunks: list[dict], source_id: str, metadata: dict) -> list[dict]:
    """Merge small chunks, split oversized prose, flag oversized tables for summary indexing."""
    raw_chunks = [c for c in raw_chunks if c["content"].strip()]
    raw_chunks = merge_small_chunks(raw_chunks)

    chunks = []
    chunk_index = 0
    for raw in raw_chunks:
        content = raw["content"]
        heading_path = [raw["heading_path"].get(level) for level in HEADING_LEVELS
                        if raw["heading_path"].get(level)]
        token_count = count_tokens(content)
        chunk_type = detect_chunk_type(content)

        # Oversized text/lists: split further with overlap
        # Oversized tables: keep whole, flag for summary indexing
        if token_count > OVERSIZE_THRESHOLD and chunk_type in ("text", "list"):
            for sub_text in split_oversized_prose(content):
                sub_token_count = count_tokens(sub_text)
                # Re-detect type: splitting may produce fragments without
                # the original list/table markup
                sub_type = detect_chunk_type(sub_text)
                chunks.append({
                    "source_id": source_id,
                    "chunk_index": chunk_index,
                    "content": sub_text,
                    "heading_path": heading_path,
                    "chunk_type": sub_type,
                    "token_count": sub_token_count,
                    "oversized": False,
                    "source_metadata": metadata,
                })
                chunk_index += 1
        # Extreme tables: row-group split with repeated headers
        elif token_count > TABLE_SPLIT_THRESHOLD and chunk_type == "table":
            row_groups = split_table_by_row_groups(content)
            if row_groups:
                for sub_html in row_groups:
                    sub_token_count = count_tokens(sub_html)
                    chunks.append({
                        "source_id": source_id,
                        "chunk_index": chunk_index,
                        "content": sub_html,
                        "heading_path": heading_path,
                        "chunk_type": "table",
                        "token_count": sub_token_count,
                        "oversized": sub_token_count > OVERSIZE_THRESHOLD,
                        "source_metadata": metadata,
                    })
                    chunk_index += 1
            else:
                # Couldn't split — keep whole, flag oversized
                chunks.append({
                    "source_id": source_id,
                    "chunk_index": chunk_index,
                    "content": content,
                    "heading_path": heading_path,
                    "chunk_type": chunk_type,
                    "token_count": token_count,
                    "oversized": True,
                    "source_metadata": metadata,
                })
                chunk_index += 1
        else:
            chunks.append({
                "source_id": source_id,
                "chunk_index": chunk_index,
                "content": content,
                "heading_path": heading_path,
                "chunk_type": chunk_type,
                "token_count": token_count,
                "oversized": token_count > OVERSIZE_THRESHOLD,
                "source_metadata": metadata,
            })
            chunk_index += 1

    return chunks


def chunk_html_file(file_path: str) -> list[dict]:
    """Chunk an HTML file, preserving raw HTML in content."""
    source_id = os.path.splitext(os.path.basename(file_path))[0]
    with open(file_path) as f:
        html = f.read()

    metadata = find_metadata(source_id)
    # First pass: split by headings
    heading_chunks = split_html_by_headings(html)
    # Second pass: split at table/list boundaries within each heading chunk
    element_chunks = []
    for chunk in heading_chunks:
        element_chunks.extend(split_chunk_by_elements(chunk))
    return finalize_chunks(element_chunks, source_id, metadata)


def chunk_md_file(file_path: str) -> list[dict]:
    """Chunk a markdown file."""
    source_id = os.path.splitext(os.path.basename(file_path))[0]
    with open(file_path) as f:
        md = f.read()

    metadata = find_metadata(source_id)
    docs = MD_SPLITTER.split_text(md)

    # Convert LangChain docs to our raw chunk format
    raw_chunks = []
    for doc in docs:
        raw_chunks.append({
            "content": doc.page_content,
            "heading_path": dict(doc.metadata),
        })

    return finalize_chunks(raw_chunks, source_id, metadata)


def main():
    output_dir = os.path.normpath(OUTPUT_DIR)
    os.makedirs(output_dir, exist_ok=True)

    all_chunks = []
    oversized_count = 0
    error_count = 0

    # Chunk HTML files
    html_dir = os.path.normpath(HTML_DIR)
    html_files = sorted(glob.glob(os.path.join(html_dir, "*.html")))
    if html_files:
        print(f"Chunking {len(html_files)} HTML files from {html_dir}...")
        for html_path in html_files:
            name = os.path.basename(html_path)
            try:
                chunks = chunk_html_file(html_path)
                oversized = sum(1 for c in chunks if c["oversized"])
                oversized_count += oversized
                all_chunks.extend(chunks)
                suffix = f" ({oversized} oversized)" if oversized else ""
                print(f"  {name}: {len(chunks)} chunks{suffix}")
            except Exception as e:
                error_count += 1
                print(f"  {name}: ERROR - {e}")

    # Chunk markdown files
    md_dir = os.path.normpath(MD_DIR)
    md_files = sorted(glob.glob(os.path.join(md_dir, "*.md")))
    if md_files:
        print(f"Chunking {len(md_files)} markdown files from {md_dir}...")
        for md_path in md_files:
            name = os.path.basename(md_path)
            try:
                chunks = chunk_md_file(md_path)
                oversized = sum(1 for c in chunks if c["oversized"])
                oversized_count += oversized
                all_chunks.extend(chunks)
                suffix = f" ({oversized} oversized)" if oversized else ""
                print(f"  {name}: {len(chunks)} chunks{suffix}")
            except Exception as e:
                error_count += 1
                print(f"  {name}: ERROR - {e}")

    # Write output
    output_path = os.path.join(output_dir, "all_chunks.json")
    with open(output_path, "w") as f:
        json.dump(all_chunks, f, indent=2, default=str)

    print(f"\nTotal: {len(all_chunks)} chunks, {oversized_count} oversized "
          f"(>{OVERSIZE_THRESHOLD} tokens), {error_count} errors")
    print(f"Output: {output_path}")

    # Token distribution
    if all_chunks:
        tokens = sorted(c["token_count"] for c in all_chunks)
        print(f"\nToken distribution:")
        print(f"  Min: {tokens[0]}, Max: {tokens[-1]}, "
              f"Median: {tokens[len(tokens)//2]}")
        print(f"  <256: {sum(1 for t in tokens if t < 256)}, "
              f"256-512: {sum(1 for t in tokens if 256 <= t < 512)}, "
              f"512-1024: {sum(1 for t in tokens if 512 <= t < 1024)}, "
              f">1024: {sum(1 for t in tokens if t >= 1024)}")

        # Chunk type breakdown
        from collections import Counter
        types = Counter(c["chunk_type"] for c in all_chunks)
        print(f"\nChunk types: {dict(types)}")


if __name__ == "__main__":
    main()
