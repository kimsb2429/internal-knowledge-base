# TODO — internal-knowledge-base

## Completed
- [x] Step 1: Pick first corpus (M22-3, M22-4 from KnowVA + VADIR ICD)
- [x] Step 2: Build golden query set (110 queries, validated)
- [x] Build KnowVA crawler (scripts/crawl_knowva.py)
- [x] Validate golden set (faithfulness 0.93, correctness 0.997, relevance 0.993)

## Next — Zero-to-MCP Steps 3-9

- [ ] Step 3: Bronze layer — enrich crawler output with ACL metadata, lastModified from Confluence REST API
- [ ] Step 4: Guardrails — secret/credential regex scanning, space allowlist config, result count cap
- [ ] Step 5: Parsing layer — run Docling (TableFormerMode.ACCURATE) on the 126 table-heavy articles
- [ ] Step 6: Metadata schema — create pgvector tables (documents + document_chunks) per buy-vs-build doc
- [ ] Step 7: Chunking pipeline — Docling HybridChunker (max_tokens=8192) + contextual retrieval (~50 lines)
- [ ] Step 8: Embed and store — Titan V2 → pgvector with HNSW index
- [ ] Step 9: Eval harness — DeepEval with golden_query_set.json as baseline

## Later — Loops and Scaling
- [ ] Loop A: Fix chunks (3-5 iterations)
- [ ] Step 11: Add Cohere Rerank 3.5 on Bedrock
- [ ] Loop B: Tune retrieval (2-3 iterations)
- [ ] Steps 13-14: Build MCP server (FastMCP) + first consumer
- [ ] Steps 15-17: Instrument (Langfuse, telemetry, usage insights)
