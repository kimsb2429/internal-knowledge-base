# TODO — internal-knowledge-base

## Completed
- [x] Step 1: Pick first corpus (M22-3, M22-4 from KnowVA + VADIR ICD)
- [x] Step 2: Build golden query set (110 queries, validated)
- [x] Build KnowVA crawler (scripts/crawl_knowva.py)
- [x] Validate golden set (faithfulness 0.93, correctness 0.997, relevance 0.993)

## Next — Zero-to-MCP Steps 3-9

- [x] Step 3: Bronze layer — heading extraction fix, acl, source_authority_tier, content_category enrichment
- [ ] Step 4: Guardrails — secret/credential regex scanning, space allowlist config, result count cap
- [x] Step 5: Parsing layer — markdownify for 237 HTML articles, Docling (TableFormerMode.ACCURATE) for VADIR ICD PDF. Post-processed PDF to strip cover OCR junk + tripled ToC (165K→103K). Validated: 20-article HTML sample (14/20 pass, 6 fail on colspan tables — deferred to Step 7 context blurbs), PDF validated for content completeness. Known limitations: 54 HTML articles have broken pipe tables from colspan (445 rows), PDF has 6 split tables at page breaks + flat heading hierarchy.
- [ ] Step 6: Metadata schema — create pgvector tables (documents + document_chunks) per buy-vs-build doc
- [ ] Step 7: Chunking pipeline — MarkdownHeaderTextSplitter for HTML articles, Docling HybridChunker for PDFs. Context blurbs must specifically address: (a) merged-cell tables — LLM description should capture the semantic meaning the colspan header conveyed, (b) PDF split tables — detect consecutive tables with matching column headers and merge before chunking, (c) heading hierarchy — use section number prefixes (1.3.1, 5.1.3) not markdown heading levels for PDF chunks
- [ ] Step 8: Embed and store — Titan V2 → pgvector with HNSW index
- [ ] Step 9: Eval harness — DeepEval with golden_query_set.json as baseline

## Later — Loops and Scaling
- [ ] Loop A: Fix chunks (3-5 iterations)
- [ ] Step 11: Add Cohere Rerank 3.5 on Bedrock
- [ ] Loop B: Tune retrieval (2-3 iterations)
- [ ] Steps 13-14: Build MCP server (FastMCP) + first consumer
- [ ] Steps 15-17: Instrument (Langfuse, telemetry, usage insights)
