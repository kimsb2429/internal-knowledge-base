# Deep Dive: State of the Art for HTML RAG Ingestion (April 2026)

## Executive Summary

After researching Unstructured, Docling, LlamaIndex, and what top production RAG teams (Uber, Dropbox, LinkedIn, Atlassian, Notion, Spotify, Anthropic) actually ship, the honest answer is: **no framework covers 80% of our needs, and none of the top teams use a full framework for HTML ingestion either.** They all go custom or native-API for parsing and chunking.

**Recommendation: stay custom, but make targeted library swaps for the three real problems we have.** (1) Use Unstructured's `partition_html` + `text_as_html` as a reference implementation for table handling, keeping our current lxml+BS4 approach since it already does this. (2) Adopt Anthropic's **Contextual Retrieval** pattern (documented +35% retrieval lift) — 50-100 token LLM-generated context prefix per chunk, cached — which addresses our chunk-size distribution problem at the embedding layer rather than by re-chunking. (3) Write a ~30-line base64 + image-orphan filter as a post-chunk pass. Do NOT rip-and-replace to Unstructured or Docling; neither solves our actual blockers and both introduce new integration debt.

## Findings

### Frameworks evaluated

**Unstructured.io (v0.22.x, open-source)**
- Table handling: strong. `partition_html` preserves colspan/rowspan in `Table.metadata.text_as_html`. Table isolation during chunking, `repeat_table_headers`, `reconstruct_table_from_chunks()` all present as of 0.22.21.
- Chunking: only `basic` and `by_title` strategies, both with `max_characters` / `new_after_n_chars` — **no distribution targeting**, just greedy pack-to-max. `combine_text_under_n_chars` is the only minimum floor (same mechanism as our current `MERGE_THRESHOLD = 50`).
- Base64 filtering for HTML: **no built-in filter.** HTML path has no `image_url_pattern_to_replace` equivalent (that exists only in hosted Platform API).
- Heading breadcrumb: you walk `parent_id` chains yourself; no first-class `heading_path` field.
- Estimated coverage of our needs: ~60-70%. Below the 80% threshold per our research-first rule.

**IBM Docling (2025-2026, now Linux Foundation AAIF)**
- HTML is first-class input in 2026 (was PDF-focused in 2024). `DoclingDocument` preserves `row_span`/`col_span` on HTML tables, with known edge cases on deeply nested spans (discussion #2241).
- `HybridChunker` layers token-budget refinement over `HierarchicalChunker`, which uses heading structure. Chunk metadata carries `headings` path. **This is the closest to what we need for chunk-size control plus breadcrumbs.**
- Image handling: `PictureItem` nodes; Granite-Docling-258M VLM (Sep 2025) provides captioning, Apache 2.0.
- Base64 inline handling: not documented clearly — possible gap.
- Integration: LangChain `DoclingLoader` official; LlamaIndex `BaseChunker` plug-in; no first-party pgvector but trivial via LangChain `PGVector`.
- **Key shift from our 2026-04-11 evaluation:** we called Docling "misaligned with HTML-as-HTML" because it normalizes to its own document model. That reasoning was correct for keeping raw HTML in storage, but the model's chunk output still exposes structured data suitable for retrieval. **Worth re-evaluating as a heavyweight option if targeted swaps plateau.**

**LlamaIndex (ingestion pipeline + node parsers)**
- `HTMLNodeParser` is weak: default tag list doesn't include `<table>`/`<tr>`/`<td>`, flattens tables to text. Issue #14695 confirms colspan mishandling. **Not competitive for our corpus.**
- `HierarchicalNodeParser` is size-based, not structure-based — doesn't read heading hierarchy.
- `SemanticSplitterNodeParser` is for prose, poor for tabular/semi-structured HTML.
- `IngestionPipeline`: composable `TransformComponent` makes it easy to drop in custom steps. But you're writing the HTML parser yourself.
- The managed `LlamaParse` service handles colspan/rowspan and image captioning, but is paid, API-dependent, and loses our "local determinism" property.

**Chunk-size distribution control across all three:** none of them let you target a median or mean. All use greedy pack-to-max with a minimum-merge floor. **Our "60% of chunks under 300 tokens" problem is inherent to heading-based splitters everywhere — not a bug unique to our code.**

### What top production RAG teams actually use

This was the most surprising finding.

| Team | HTML parser | Chunking strategy |
|---|---|---|
| **Uber Genie** | Custom: Google Docs Python API → HTML, custom loader | Structure-aware; **Post-Processor Agent** re-orders retrieved chunks by source position |
| **Dropbox Dash** | In-house | **Query-time chunking** — docs are NOT pre-chunked at index time |
| **LinkedIn RAG** | Custom: tickets parsed into trees, linked as knowledge graph | Hierarchical; chunks only within graph nodes |
| **Atlassian Rovo** | Native Confluence/Jira connectors | Not publicly disclosed; hybrid retrieval with Llama-Nemotron-Embed-1B |
| **Notion AI** | Apache Hudi + Kafka + Debezium CDC data lake | Not disclosed |
| **Spotify AiKA** | Backstage plugins | Not disclosed |
| **Anthropic cookbook** | No parser prescribed; format-agnostic | **Fixed-size ~800-token chunks + Contextual Retrieval prefix** |

**None** use Unstructured or Docling as their documented HTML parser. The pattern is either (a) native-API extraction from the source system, or (b) in-house parsers. **Every team with publicly documented architecture built custom for this layer.** Our instinct to stay custom is vindicated by what works in production.

### The real win: Anthropic's Contextual Retrieval

Anthropic's Contextual Retrieval technique is the most directly transferable finding (Anthropic News, Sep 2024; still the current cookbook as of 2026):

1. Chunk normally (fixed-size or any strategy)
2. For each chunk, prepend a 50-100 token LLM-generated context snippet that situates the chunk in its parent document
3. Embed the *contextualized* chunk, not the raw chunk
4. Index the same contextualized text in BM25 too
5. Retrieve via hybrid (dense + BM25) → Reciprocal Rank Fusion → rerank → top-K

Reported results: **–35% top-20 retrieval failure rate** from contextual embeddings alone; combined with reranking, errors go from 5.7% → 1.9% (**+67% accuracy**).

Cost: ~$1.02 per million document tokens to generate context, viable because of **prompt caching** (each document prefix cached, contexts appended as non-cached suffix). For our 9,315 chunks × ~400 tokens avg = ~3.7M tokens, that's ~$4 one-time cost.

**Why this matters for us:** it solves the chunk-size distribution problem at the *embedding* layer without re-chunking. A 100-token chunk becomes a 200-token contextualized chunk that embeds with much richer semantic signal. It's additive to everything we have — works with our existing lxml+BS4 chunker, our mxbai-embed-large embeddings, our pgvector store, our reranker.

### Image and base64 handling

None of the frameworks solve this cleanly for HTML:
- Unstructured: `<img>` becomes `Image` element, no captioning pipeline for HTML, no base64 filter
- Docling: Granite-Docling-258M captions images but primarily for PDF/image pipelines; HTML base64 behavior undocumented
- LlamaIndex: `HTMLNodeParser` drops images silently

**This is a pre-processing problem, not a framework problem.** A ~30-line BeautifulSoup pass detecting (a) base64 blobs (long no-space tokens > 200 chars), (b) image-only chunks (mostly `<img>` tag and a caption line, no prose) handles it. The frameworks don't save us work here.

## Open Questions

- **Docling re-evaluation:** if targeted swaps + Contextual Retrieval don't lift Contextual Recall into the 0.80+ range, Docling's `HybridChunker` + `DoclingDocument` structured model is worth a real A/B test against our custom chunker. Would take ~1 day to wire and measure.
- **Contextual Retrieval cost at scale:** $4 one-time is trivial for our 238 docs, but if we Loop D onto a 10K-doc Confluence later, generation cost becomes ~$400. Budget to watch.
- **Spotify/Notion/Atlassian internals:** the best-in-class detail is under NDA. If specific problems appear (e.g. Confluence macro handling), targeted research on their engineering talks would surface more.

## Sources

### Framework research
- Unstructured Chunking docs — https://docs.unstructured.io/open-source/core-functionality/chunking
- Unstructured Partitioning docs — https://docs.unstructured.io/open-source/core-functionality/partitioning
- Unstructured CHANGELOG — https://github.com/Unstructured-IO/unstructured/blob/main/CHANGELOG.md
- IBM Docling announcement — https://research.ibm.com/blog/docling-generative-AI
- Docling: Open-source document processing (InfoWorld) — https://www.infoworld.com/article/3997240/docling-an-open-source-tool-kit-for-advanced-document-processing.html
- Docling chunking concepts — https://docling-project.github.io/docling/concepts/chunking/
- Docling Discussion #2241 (complex tables) — https://github.com/docling-project/docling/discussions/2241
- Granite-Docling-258M announcement — https://dev.to/aairom/just-announced-ibm-granite-docling-end-to-end-document-understanding-with-one-tiny-model-1nog
- LangChain Docling integration — https://docs.langchain.com/oss/python/integrations/document_loaders/docling
- LlamaIndex Node Parser Modules — https://developers.llamaindex.ai/python/framework/module_guides/loading/node_parsers/modules/
- LlamaIndex HTMLNodeParser — https://docs.llamaindex.ai/en/stable/api_reference/node_parsers/html/
- LlamaIndex IngestionPipeline — https://developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/transformations/
- LlamaIndex Issue #14695 — https://github.com/run-llama/llama_index/issues/14695

### Production RAG architectures
- Uber Enhanced Agentic-RAG — https://www.uber.com/blog/enhanced-agentic-rag/
- Dropbox Dash — RAG + AI agents — https://dropbox.tech/machine-learning/building-dash-rag-multi-step-ai-agents-business-users
- Dropbox Dash — Context engineering — https://dropbox.tech/machine-learning/how-dash-uses-context-engineering-for-smarter-ai
- LinkedIn RAG with Knowledge Graphs (arXiv 2404.17723) — https://arxiv.org/abs/2404.17723
- Atlassian Rovo semantic search — https://www.atlassian.com/blog/atlassian-engineering/advancing-rovo-semantic-search
- Atlassian Rovo Deep Research — https://www.atlassian.com/blog/atlassian-engineering/how-rovo-deep-research-works
- Notion AI infrastructure (ZenML LLMOps DB) — https://www.zenml.io/llmops-database/scaling-data-infrastructure-for-ai-features-and-rag
- Spotify AiKA (Backstage blog) — https://backstage.spotify.com/discover/blog/aika-data-plugins-coming-to-portal
- KubeCon EU 2025 AiKA talk — https://kccnceu2025.sched.com/event/1tx9t

### Contextual Retrieval
- Anthropic — Contextual Retrieval — https://www.anthropic.com/news/contextual-retrieval
- Claude Cookbook — Contextual Embeddings — https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide
