# TODO — internal-knowledge-base

## Completed
- [x] Step 1: Pick first corpus (M22-3, M22-4 from KnowVA + VADIR ICD)
- [x] Step 2: Build golden query set (110 queries, validated)
- [x] Build KnowVA crawler (scripts/crawl_knowva.py)
- [x] Validate golden set (faithfulness 0.93, correctness 0.997, relevance 0.993)

## Zero-to-MCP Progress

Canonical plan: `docs/2026-04-11-engineering-rag-evidence-and-howtos.md` § "From Zero to Knowledge MCP"

- [x] Step 1: Pick first corpus
- [x] Step 2: Build golden query set
- [x] Step 3: Bronze layer (metadata enrichment)
- [ ] Step 4: Guardrails
- [x] Step 5: Parsing layer (PDF only — HTML articles skip markdown, go straight to HTMLHeaderTextSplitter)
- [x] Step 6: Metadata schema (pgvector) — Docker, port 5433, mxbai-embed-large 1024 dims
- [x] Step 7: Chunking pipeline — 9,315 chunks (7,113 text, 1,444 table, 758 list), 0 errors. Custom HTML splitter preserves table structure. Generic chunker + `knowva_preprocess.py` for source-specific quirks. Row-group splitting for tables >50K. Max chunk: 49,708 tokens.
  - [x] Row-group splitting for large tables (was Loop A candidate) — all tables >50K now split with repeated headers
- [x] Validate chunks using independent subagents — 4 parallel subagents caught multi-table chunks, misclassified lists, list fragments, threshold-gap; all fixed
- [x] Step 8: Embed and store — 238 documents, 9,315 chunks in pgvector. Heading-only `embed_text` for oversized chunks (title + heading_path). mxbai-embed-large via sentence-transformers. $0 API cost (deferred LLM summary indexing to Loop A if eval shows need).
- [ ] Step 9: Eval harness (baseline) — DeepEval + golden query set, score Contextual Recall/Precision/Relevancy/Faithfulness/Answer Relevancy
- [ ] Loop A: Fix chunks
  - [ ] Loop A candidate: if content-level queries against oversized tables fail at eval, add LLM summary indexing OR `retrieve_full_doc` MCP method
- [ ] Step 11: Add reranker
- [ ] Step 12: Add HyDE
- [ ] Step 13: Add CRAG
- [ ] Loop B: Tune retrieval
- [ ] Steps 15-16: Ship (MCP + first consumer)
- [ ] Steps 17-19: Instrument
- [ ] Step 20: Freshness
- [ ] Loop C: Learn
- [ ] Step 22: Validate eval
- [ ] Loop D: Scale sources
- [ ] Loop E: Tune consumers
