# internal-knowledge-base

VA Education RAG pipeline — from raw corpus to MCP server.

## Zero-to-MCP plan

The canonical build plan is the **"From Zero to Knowledge MCP"** section in `docs/2026-04-11-engineering-rag-evidence-and-howtos.md`. The plan doc is authoritative for any "zero to mcp" references.

## Standing rules

**Post-eval analysis protocol (apply after every eval run — baseline, Loop A iteration, Loop B iteration, anywhere):** never report aggregate metrics alone. Always follow with (a) per-`query_type` segmentation, (b) 2-3 representative failures pulled per failure cluster with full chunk/judge reasoning, (c) named failure patterns with concrete mechanisms, (d) mapping from each pattern to a specific plan step / lever. The plan doc (§ "From Zero to Knowledge MCP", step 9) has the full template. Anti-pattern: proposing the next intervention directly from aggregate deltas — that tunes blindly.

## Key decisions

- **HTML articles stay as HTML** — no markdown conversion. Markdown is lossy for tables (colspan/rowspan). LLMs read HTML fine. One code path for all 237 HTML articles.
- **Markdown only for VADIR ICD PDF** — no HTML source, so parsed markdown + `MarkdownHeaderTextSplitter` is the right path.
- **Generic chunker + source-specific preprocessors** — `chunk_documents.py` is source-agnostic; each source gets its own `<source>_preprocess.py` that normalizes HTML quirks (headings, layout tables, div wrappers) before chunking. Adding a new source means writing a preprocessor, not forking the chunker.
- **Custom HTML splitter** — LangChain's `HTMLHeaderTextSplitter` strips HTML tags, destroying table structure. We use our own (`split_html_by_headings` + `split_chunk_by_elements` in `chunk_documents.py`) that preserves raw HTML.
- **Row-group splitting for tables >50K tokens** — above 50K, summary indexing breaks down (full content can't be served in a 200K context window). Split into row-groups with repeated headers; each chunk is self-contained.
- **Heading-only `embed_text` for oversized chunks** — instead of LLM-generated summaries ($13 in Sonnet calls), use `title + heading_path` for the embed vector. Full content still served at generation. If eval shows content-level queries failing, add a `retrieve_full_doc` MCP method or upgrade to LLM summaries in Loop A.
- Schema: `embed_text` holds what was embedded (content for regular chunks, heading-only for oversized); `content` always holds the full original.

## Stack

- **Database:** Postgres + pgvector (Docker, `docker-compose.yml`). Container `ikb_pgvector`, port 5433. Connection: `postgresql://ikb:ikb_local@localhost:5433/ikb`.
- **Embedding:** mxbai-embed-large (1024 dims, via sentence-transformers/HuggingFace) — replaces original Titan V2 plan, same dimensions, runs locally, no API cost.
- **Generation:** Claude Sonnet (query-time generation; also available for Loop A LLM summary indexing if needed).
- **Chunking:** custom HTML splitter (preserves raw HTML), `MarkdownHeaderTextSplitter` for VADIR PDF.
- **Eval:** DeepEval (planned, Step 9).

## Key docs

- `docs/2026-04-11-engineering-rag-evidence-and-howtos.md` — evidence base + Zero-to-MCP plan (26 steps, 5 loops)
- `docs/2026-04-12-rag-pipeline-buy-vs-build.md` — tool decisions per step
- `docs/2026-04-11-rag-ingestion-skills-research.md` — skills/ecosystem research
