# Preprocessing Reference

What was done to each source before chunking. Each source has different quirks — this doc captures the transforms applied so they can be reproduced or adapted for new sources.

## KnowVA HTML Articles (237 articles)

**Source:** KnowVA CMS (knowva.ebenefits.va.gov) via `scripts/crawl_knowva.py`

### Crawler processing (built into crawl_knowva.py)

- Fetches article HTML + metadata from KnowVA REST API
- Wraps content in structured HTML with `<meta>` tags (source-system, article-id, last-modified, etc.)
- Adds `<h1>` title if not present in content
- Extracts heading hierarchy for metadata JSON (handles 3 HTML patterns: standard `<h2>`-`<h6>`, `<a name>+<strong>`, and split-word edge cases)

### Metadata enrichment (scripts/enrich_metadata.py)

Batch-applied to all 237 article JSON sidecars:
- `acl: "public"`
- `source_authority_tier: 1`
- `content_category: "gov_docs_and_manuals"`

### Heading normalization (scripts/knowva_heading_fix.py)

**Problem:** ~164 articles use `<a name="..."> + <strong>` instead of proper heading tags. `HTMLHeaderTextSplitter` can't split on these.

**Fix:** Converts anchor patterns to proper `<h2>`/`<h3>`/`<h4>` tags based on anchor name patterns:

| Anchor pattern | Heading level | Example |
|---|---|---|
| `S[IVX]+` | `<h2>` | `<a name="SI">` → Subchapter I |
| `Topic\d+` | `<h2>` | `<a name="Topic1">` → Topic 1 |
| `\d{3,}` | `<h3>` | `<a name="801">` → Section 8.01 |
| `\d{3,}[a-z]` | `<h4>` | `<a name="801a">` → Subsection a |
| `\d{3,}\d[a-z]` | `<h4>` | `<a name="8051a">` → Deep subsection |
| `[A-Z]` | `<h3>` | `<a name="A">` → Section A |
| `[A-Z][a-z]` | `<h4>` | `<a name="Aa">` → Subsection Aa |

Skipped anchors: `top`/`_top` (navigation), `f\d+` (figures), `_Hlk` (Word bookmarks).

**Input:** `data/knowva_manuals/articles/*.html`
**Output:** `data/knowva_manuals/preprocessed/*.html`

### What was NOT done

- **Colspan/rowspan tables** — 54 articles, 445 rows with merged cells. Left intact in HTML. `HTMLHeaderTextSplitter` preserves the original `<table>` structure, and oversized tables get summary-indexed during embedding (summary captures the table's meaning, full table goes to LLM at query time).
- **No markdown conversion** — decided to skip HTML→markdown for these articles. HTML is the source of truth; markdown conversion is lossy for tables.

---

## VADIR ICD PDF (1 document)

**Source:** `data/VADIR_CH33_LTS_WS_V2.1.1_ICD_20220509.pdf`

### PDF → Markdown (manual, no script)

Used Docling with `TableFormerMode.ACCURATE` to convert PDF to markdown. Post-processing:
1. Stripped cover page OCR junk
2. Removed tripled Table of Contents (62K of redundant content)
3. Stripped `[Go to Top]` nav links

**Output:** `data/knowva_manuals/parsed/VADIR_CH33_LTS_WS_V2.1.1_ICD_20220509.md`
**Also copied to:** `data/vadir_parsed/` (isolated dir for chunker input)

### Metadata (manual)

Created `data/VADIR_CH33_LTS_WS_V2.1.1_ICD_20220509.json` with:
- `acl: "public"`
- `source_authority_tier: 1`
- `content_category: "gov_docs_and_manuals"`

### Known issues

- **6 split tables at page breaks** — Docling splits tables that span PDF pages. Rows are present but in separate table blocks. Deferred to summary indexing (the summary captures both halves).
- **Flat heading hierarchy** — all headings are `##` (Docling doesn't infer depth from PDF formatting). `MarkdownHeaderTextSplitter` treats them all as `h2`, so chunking is coarser than ideal.
