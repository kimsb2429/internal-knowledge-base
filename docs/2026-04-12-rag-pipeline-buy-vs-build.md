# RAG Pipeline: Buy vs Build Map

**Date:** 2026-04-12
**Stack:** Postgres + pgvector, Claude Sonnet, AWS Bedrock Titan V2 (1024 dims, 8192 tokens), PDFs (with tables) + Confluence → MCP server

---

## Decision Fork: Bedrock Knowledge Bases vs Custom Pipeline

Before the component-level analysis, there's a platform-level decision:

**Amazon Bedrock Knowledge Bases** covers ~85% of the pipeline if you use **Aurora PostgreSQL** (not standard RDS pgvector). It handles: Confluence connector (incremental sync), hierarchical/semantic/custom chunking, contextual retrieval, Titan V2 embeddings, hybrid search (BM25 + vector), reranking — all managed.

**Limitations:** Aurora PostgreSQL only (not standard RDS). Weak PDF table extraction (the critical gap). No MCP server output — needs custom wrapper around the Retrieve API. Customization ceiling on chunking.

**Recommendation:** If Aurora is acceptable, use Bedrock KB for Confluence ingestion + retrieval and run PDFs through a custom Docling pipeline feeding the same Aurora store. If standard pgvector is required, build custom using the components below.

---

## Pipeline Stage Map

```
Raw Sources (PDF / Confluence)
    │
    ▼  PARSING
Structured intermediate (markdown + metadata)
    │
    ▼  CHUNKING
Chunks with heading breadcrumbs + metadata
    │
    ▼  CONTEXTUAL ENRICHMENT
Chunks with LLM-generated context blurbs prepended
    │
    ▼  EMBEDDING
Titan V2 vectors (1024 dims)
    │
    ▼  STORAGE
pgvector + tsvector + metadata columns
    │
    ▼  RETRIEVAL (hybrid search + reranking)
Top-K chunks with scores + metadata
    │
    ▼  MCP SERVER
Chunks + metadata returned to consuming LLMs/apps
    │
    ▼  EVAL + MONITORING
Ragas/DeepEval metrics, Langfuse observability, drift detection
```

---

## Component-Level Buy vs Build

### 1. PDF Parsing + Table Extraction

| Decision | **BUY — Docling** |
|---|---|
| Tool | [Docling](https://github.com/docling-project/docling) v2.86.0 |
| Why | 97.9% table accuracy (TableFormer), MIT license, 57K stars, weekly releases, IBM Research. Built-in HybridChunker with token-aware splitting. `contextualize()` prepends heading breadcrumbs. |
| Runner-up | [OCRFlux](https://github.com/chatdoc-com/OCRFlux) (Apache 2.0) — only tool with native cross-page table merging (98.3%). Use as fallback for scanned/cross-page-heavy PDFs. |
| Avoid | PyMuPDF4LLM (weak tables), Unstructured OSS (declining table quality), AWS Textract standalone (too much glue code). |
| Custom code needed | Minimal — configure `TableFormerMode.ACCURATE`, set HybridChunker token limit to 8192 for Titan V2, wrap as ingestion script. |

### 2. Confluence Ingestion

| Decision | **BUY + SUPPLEMENT** |
|---|---|
| Primary tool | [confluence-markdown-exporter](https://github.com/Spenhouet/confluence-markdown-exporter) v4.0.5 (MIT, 365 stars, actively maintained) |
| What it handles | Bulk export, incremental sync (lockfile), macro conversion (code, panels, draw.io → Mermaid, PlantUML, expand sections), labels in frontmatter, breadcrumbs, hierarchical folder output. |
| Gaps to supplement | ACLs (use REST API `expand=restrictions.read.restrictions.group`), Jira macro resolution (use `body.export_view`), attachment PDF extraction (use Docling or LlamaIndex ConfluenceReader attachment pipeline). |
| Alternative | If already on Bedrock KB: native Confluence connector handles incremental sync, but no macro expansion. |
| Avoid | LangChain ConfluenceLoader (buggy labels), SpillwaveSolutions skills (authoring-focused, not ingestion). |

### 3. Chunking

| Decision | **BUY — Docling HybridChunker** (for PDFs) + **LangChain MarkdownHeaderTextSplitter** (for Confluence markdown) |
|---|---|
| Docling HybridChunker | Structure-aware, token-budget-aware (set to 8192 for Titan V2), keeps tables atomic, repeats headers on split, preserves heading hierarchy as metadata. Ships with Docling — no extra dependency. |
| Markdown splitter | For Confluence output (already markdown from confluence-markdown-exporter). Preserves heading hierarchy as metadata. Simple, free, production-grade. |
| LLM chunking (Sonnet) | Defer to later. At $21/M tokens vs ~$0 for HybridChunker, only justified for the hard 10% (messy structure, ambiguous boundaries). Start with deterministic chunking, measure quality, add Sonnet for failures. |
| Alternative | [Chonkie](https://github.com/chonkie-inc/chonkie) (MIT, 3.9K stars) — 10+ strategies including SlumberChunker (LLM-powered) and native pgvector integration. Good if you want a unified chunking library with more strategies. |

### 4. Contextual Retrieval (Context Blurb Prepending)

| Decision | **BUILD — ~50 lines of custom code** |
|---|---|
| What | Anthropic's technique: send full doc + each chunk to Claude Haiku, get a 1-2 sentence context blurb, prepend to chunk before embedding. |
| Why build | No production-ready open-source implementation exists. The technique is simple (prompt + caching loop). Cost: ~$1.02/M document tokens with prompt caching. Performance: 49-67% retrieval failure reduction. |
| Reference | [Anthropic blog post](https://www.anthropic.com/news/contextual-retrieval) provides the exact prompt template. |
| Bedrock KB option | Bedrock KB supports this via custom Lambda, but requires Aurora PostgreSQL. |
| Impact | **Single biggest retrieval quality win in the pipeline.** Prioritize implementing this. |

### 5. Multi-Representation Indexing (Summary + Detail + HyDE)

| Decision | **BUY — LangChain MultiVectorRetriever + PGVector + PostgresByteStore** |
|---|---|
| What it does | Stores multiple vector representations per document (child chunks for retrieval, parent chunks for context, summary embeddings, HyDE question embeddings). All backed by pgvector. |
| Why | Production-grade, MIT license, native pgvector support with persistent PostgresByteStore. Well-documented pattern. |
| Alternative | LlamaIndex HierarchicalNodeParser + AutoMergingRetriever — same pattern, different framework. Choose based on which framework you adopt. |
| Custom code needed | Configuration only — define chunk hierarchies, summary generation prompts, optional HyDE question generation for high-value tables. |

### 6. Embedding

| Decision | **BUY — Bedrock Titan V2** |
|---|---|
| Already decided | $0.02/M input tokens. 1024 dims. 8192 token input limit. Direct boto3 call. |
| No alternatives needed | This is already the right choice for the stack. |

### 7. Storage (pgvector Schema)

| Decision | **BUILD — but pattern is well-established** |
|---|---|
| Schema pattern | Two-table (documents + chunks) with JSONB metadata, HNSW index on embeddings, GIN index on tsvector + metadata. Source-type-specific fields as nullable columns or in JSONB. |
| HNSW defaults | `m=16, ef_construction=200` — start here, tune with benchmarks. 15.5x higher QPS than IVFFlat at same recall. |
| Hybrid search | **Option A:** Native `tsvector + ts_rank` (simplest, no extensions, good enough for most cases but lacks IDF). **Option B:** [pg_textsearch](https://github.com/timescale/pg_textsearch) (true BM25, 4x faster, actively developed by TigerData). **Option C:** ParadeDB pg_search (mature but dropped from Neon Mar 2026). |
| RRF fusion | Supabase's documented SQL pattern is directly portable — single query combining vector + text scores via Reciprocal Rank Fusion. |
| Reference repos | [aws-samples/rag-with-amazon-bedrock-and-pgvector](https://github.com/aws-samples/rag-with-amazon-bedrock-and-pgvector), Supabase hybrid search docs, [RemembrallMCP](https://github.com/cdnsteve/remembrallmcp) (pgvector + tsvector + RRF). |

### 8. Reranking

| Decision | **BUY — Cohere Rerank 3.5 on Bedrock** (start), migrate to BGE-v2-m3 on SageMaker at volume |
|---|---|
| Cohere Rerank 3.5 | $2.00/1K queries (up to 100 docs per query). Native Bedrock Rerank API. Available in us-east-1. State-of-the-art quality, 100+ languages. Zero infrastructure. |
| Migration path | At high volume, self-host [BGE-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3) on SageMaker (~$0.30-1.50/hr for ml.g5.xlarge). Zero per-query cost. Same quality tier. |
| Retrieval flow | Query → Titan V2 embed → pgvector top-50 (fast, rough) → Cohere rerank → top-5 (accurate) → consuming LLM. |

### 9. MCP Server

| Decision | **BUILD — no existing server matches the full stack** |
|---|---|
| What to build | Custom MCP server exposing `query` tool returning top-K chunks with full metadata (source_type, heading_breadcrumb, last_modified, score, etc.). No generation — retrieval only. |
| Framework | [FastMCP](https://github.com/jlowin/fastmcp) (Python) or official MCP SDK (TypeScript). |
| Design reference | [knowledge-rag (lyonzin)](https://github.com/lyonzin/knowledge-rag) — best MCP tool design (12 tools: search/ingest/manage pattern). Adapt from ChromaDB to pgvector. |
| Other references | [Memex](https://github.com/achetronic/memex) (Go + pgvector + MCP, Apache 2.0) — most production-oriented pgvector MCP server, but lacks hybrid search and reranking. [RemembrallMCP](https://github.com/cdnsteve/remembrallmcp) (Rust + pgvector + hybrid, MIT) — only project doing pgvector + tsvector + MCP together, but very early. |
| Scope | The MCP server itself is thin (~200-400 lines). The real work is the pipeline feeding it. |

### 10. Eval Harness

| Decision | **BUY — DeepEval + Ragas + Langfuse** |
|---|---|
| Eval framework | [DeepEval](https://github.com/confident-ai/deepeval) (MIT, 14.7K stars) — **best native Bedrock support** with drop-in `AmazonBedrockModel` class. pytest-style tests, CI/CD friendly. |
| Golden dataset generation | [Ragas TestsetGenerator](https://docs.ragas.io/en/stable/getstarted/rag_testset_generation/) — best for generating Q&A pairs with source chunk references (exactly what you need for retrieval quality eval). Use Ragas for testset gen even if using DeepEval for eval. |
| Production monitoring | [Langfuse](https://github.com/langfuse/langfuse) (MIT, 24.8K stars) — self-hosted on AWS (Docker/K8s/Terraform), Bedrock integration, Ragas integration for online scoring, feedback API (thumbs up/down). |
| Embedding drift | [Arize Phoenix](https://github.com/Arize-ai/phoenix) (9.3K stars) — UMAP-based embedding visualization. Unique capability. Use periodically, not real-time. |
| Guardrails | DoorDash two-tier pattern (custom): Tier 1 = cosine similarity check (pgvector, free), Tier 2 = Claude Sonnet judge (only when Tier 1 flags). + AWS Bedrock Guardrails for content filtering. |
| Cost | ~$60 to bootstrap (golden set generation + first eval runs). ~$5-8 per eval run ongoing. One weekend of setup. |

---

## Summary: What's Buy vs Build

| Pipeline Stage | Verdict | Primary Tool | Custom Code |
|---|---|---|---|
| PDF parsing | **BUY** | Docling | Config + wrapper script |
| Confluence ingestion | **BUY + supplement** | confluence-markdown-exporter + REST API for ACLs/metadata | Metadata enrichment script |
| Structure-aware chunking | **BUY** | Docling HybridChunker + MarkdownHeaderTextSplitter | Config only |
| Contextual retrieval | **BUILD** | ~50 lines on Claude Haiku + prompt caching | Core custom code |
| Multi-representation indexing | **BUY** | LangChain MultiVectorRetriever + PostgresByteStore | Config + prompts |
| Embeddings | **BUY** | Bedrock Titan V2 | boto3 call |
| pgvector schema | **BUILD** (well-documented pattern) | pgvector + tsvector + HNSW | Schema DDL + query functions |
| Hybrid search + fusion | **BUILD** (Supabase RRF pattern) | tsvector or pg_textsearch + RRF SQL | ~50 lines SQL |
| Reranking | **BUY** | Cohere Rerank 3.5 on Bedrock | API call |
| MCP server | **BUILD** | FastMCP or MCP SDK | ~200-400 lines |
| Eval framework | **BUY** | DeepEval + Ragas TestsetGenerator | Config + golden set curation |
| Production monitoring | **BUY** | Langfuse (self-hosted) | Deployment + integration |
| Guardrails | **BUILD** (DoorDash pattern) | pgvector cosine + Sonnet judge | ~100 lines |

### Genuinely custom code surface area

Only 4 components need real custom code:
1. **Contextual retrieval** (~50 lines) — prompt + caching loop
2. **pgvector schema + hybrid search** (~100 lines SQL) — DDL + RRF query
3. **MCP server** (~200-400 lines) — thin retrieval wrapper
4. **DoorDash guardrails** (~100 lines) — two-tier check

Everything else is configuration, wiring, and metadata enrichment scripts on top of existing tools. **Total custom code estimate: ~500-700 lines** for the core pipeline, plus integration/glue.

---

## Key Repos to Clone and Study

| Repo | What to steal |
|---|---|
| [aws-samples/rag-with-amazon-bedrock-and-pgvector](https://github.com/aws-samples/rag-with-amazon-bedrock-and-pgvector) | CDK patterns, pgvector schema, Bedrock call patterns |
| [knowledge-rag (lyonzin)](https://github.com/lyonzin/knowledge-rag) | MCP tool design (12 tools), hybrid search + reranking architecture |
| [RemembrallMCP](https://github.com/cdnsteve/remembrallmcp) | pgvector + tsvector hybrid + MCP together |
| [Rag_pgvector_docling](https://github.com/rajarshiverma/Rag_pgvector_docling) | Docling + pgvector + Bedrock integration reference |
| [Supabase hybrid search docs](https://supabase.com/docs/guides/ai/hybrid-search) | RRF fusion SQL pattern |
| [confluence-markdown-exporter](https://github.com/Spenhouet/confluence-markdown-exporter) | Confluence extraction with incremental sync |

---

## Sources

All sources are documented in the individual research agent outputs. Key ones:

- Docling: https://github.com/docling-project/docling (MIT, 57K stars)
- OCRFlux: https://github.com/chatdoc-com/OCRFlux (Apache 2.0, cross-page tables)
- confluence-markdown-exporter: https://github.com/Spenhouet/confluence-markdown-exporter (MIT)
- Chonkie: https://github.com/chonkie-inc/chonkie (MIT, 10+ chunking strategies)
- Anthropic Contextual Retrieval: https://www.anthropic.com/news/contextual-retrieval
- LangChain MultiVectorRetriever: https://python.langchain.com/docs/how_to/multi_vector/
- pg_textsearch: https://github.com/timescale/pg_textsearch (true BM25 for Postgres)
- Cohere Rerank on Bedrock: https://aws.amazon.com/blogs/machine-learning/cohere-rerank-3-5-is-now-available-in-amazon-bedrock-through-rerank-api/
- BGE-reranker-v2-m3: https://huggingface.co/BAAI/bge-reranker-v2-m3
- DeepEval: https://github.com/confident-ai/deepeval (MIT, native Bedrock)
- Ragas: https://github.com/explodinggradients/ragas (Apache 2.0)
- Langfuse: https://github.com/langfuse/langfuse (MIT, self-hosted)
- Arize Phoenix: https://github.com/Arize-ai/phoenix (embedding drift visualization)
- Memex: https://github.com/achetronic/memex (pgvector MCP server)
- knowledge-rag: https://github.com/lyonzin/knowledge-rag (MCP tool design reference)
- FastMCP: https://github.com/jlowin/fastmcp
- Amazon Bedrock Knowledge Bases: https://aws.amazon.com/bedrock/knowledge-bases/
- Bedrock KB contextual retrieval: https://aws.amazon.com/blogs/machine-learning/contextual-retrieval-in-anthropic-using-amazon-bedrock-knowledge-bases/

---

## Tools for Each Step in the Zero-to-MCP Plan

*Maps specific tools to each step in the [build plan](2026-04-11-engineering-rag-evidence-and-howtos.md#from-zero-to-knowledge-mcp-step-by-step-with-iteration-loops). Decision: full custom on standard RDS pgvector (Bedrock KB ruled out — Aurora tax not justified when building custom pipelines for 3 of 4 sources anyway).*

### Steps 1-9: BUILD (first working eval baseline)

#### Step 1: Pick first corpus
No tooling needed. Decision: one Confluence space, 50-200 docs.

#### Step 2: Build golden query set

| Tool | How |
|---|---|
| **Ragas TestsetGenerator** | Generate synthetic Q&A pairs from your corpus with source chunk references. Supplement with 20-30 real questions from Slack/meetings. |

#### Step 3: Set up bronze layer (raw docs + metadata)

| Tool | How |
|---|---|
| [**confluence-markdown-exporter**](https://github.com/Spenhouet/confluence-markdown-exporter) (MIT, v4.0.5) | Bulk export the space. Gets you markdown + YAML frontmatter (labels, breadcrumbs) + hierarchical folder structure + incremental sync via lockfile. |
| **Confluence REST API** (via `atlassian-python-api`) | Supplement with ACL groups (`expand=restrictions.read.restrictions.group`), `lastModified` from version history, ancestor paths for full breadcrumbs. |
| [**Docling**](https://github.com/docling-project/docling) (MIT, v2.86.0) | For any PDFs attached to Confluence pages — pull attachments via REST API, run through Docling. |

#### Step 4: Make guardrails decisions

| Tool | How |
|---|---|
| **Custom regex scanner** | Secret/credential scanning at ingestion (AWS keys, GitHub PATs, passwords). ~20 lines of regex. |
| No tooling for the rest — space allowlist is a config file, result count cap is a constant in the MCP server. |

#### Step 5: Build parsing layer

| Tool | How |
|---|---|
| **Docling** (`TableFormerMode.ACCURATE`) | For PDFs. Run 3 worst PDFs (most tables, most complex layout) through Docling, compare to current text extraction. |
| [**OCRFlux**](https://github.com/chatdoc-com/OCRFlux) (Apache 2.0) | Fallback for scanned/cross-page-heavy PDFs. Only tool with native cross-page table merging (98.3% accuracy). Evaluate only if Docling struggles on specific docs. |
| **confluence-markdown-exporter** output | For Confluence — already parsed to markdown. Check macro handling on 3 worst pages (heavy `{expand}`, `{code}`, `{include}`). If macros are mangled, supplement with `body.export_view` from REST API. |

#### Step 6: Design metadata schema

| Tool | How |
|---|---|
| **pgvector + SQLAlchemy + pgvector-python** | Two-table pattern (documents + chunks) with JSONB metadata, HNSW index on embeddings, GIN index on tsvector + metadata. |

```sql
CREATE TABLE documents (
  id BIGSERIAL PRIMARY KEY,
  source_type TEXT,           -- 'confluence', 'pdf'
  source_id TEXT,
  title TEXT,
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE document_chunks (
  id BIGSERIAL PRIMARY KEY,
  document_id BIGINT REFERENCES documents(id),
  chunk_index INT,
  content TEXT NOT NULL,
  context_blurb TEXT,         -- contextual retrieval output
  content_tsvector TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
  embedding VECTOR(1024),     -- Titan V2
  heading_breadcrumb TEXT[],
  source_type TEXT,
  contains_table BOOLEAN DEFAULT FALSE,
  content_category TEXT,      -- 'runbook', 'architecture', 'policy', 'meeting_notes'
  last_modified TIMESTAMPTZ,
  parent_table_id TEXT,       -- for split tables
  total_chunks INT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 200);
CREATE INDEX ON document_chunks USING gin (content_tsvector);
CREATE INDEX ON document_chunks USING gin (metadata);
CREATE INDEX ON document_chunks (source_type);
CREATE INDEX ON document_chunks (last_modified);
```

#### Step 7: Build chunking pipeline

| Tool | How |
|---|---|
| [**Docling HybridChunker**](https://docling-project.github.io/docling/concepts/chunking/) | For PDFs. Set `max_tokens=8192` (Titan V2 limit). Tables stay atomic. Heading breadcrumbs via `contextualize()`. |
| **LangChain `MarkdownHeaderTextSplitter`** | For Confluence markdown. Splits by headers, preserves heading hierarchy as metadata. |
| **Custom contextual retrieval** (~50 lines) | After chunking, prepend context blurbs. Send full doc + each chunk to **Claude Haiku** on Bedrock with prompt caching. ~$1.02/M doc tokens. Store blurb in `context_blurb` column and prepend to chunk text before embedding. |

#### Step 8: Embed and store

| Tool | How |
|---|---|
| **Bedrock Titan V2** | boto3 `invoke_model` call. Embed `context_blurb + chunk_content` as one string. 1024 dims. $0.02/M input tokens. |
| **SQLAlchemy + pgvector-python** | ORM for the insert loop. First-class `Vector` type support. |

#### Step 9: Set up eval harness

| Tool | How |
|---|---|
| [**DeepEval**](https://github.com/confident-ai/deepeval) (MIT) | Primary eval framework. Drop-in `AmazonBedrockModel(model="anthropic.claude-3-5-sonnet...")`. pytest-style test runner. Metrics: faithfulness, answer_correctness, context_precision, context_recall. |
| **Ragas TestsetGenerator** | Already used in step 2. Ragas metrics also available as DeepEval metrics. |

Run first eval against golden query set. This is the baseline.

---

### Loop A: FIX CHUNKS (3-5 iterations, highest leverage)

| Tool | Role |
|---|---|
| **Docling** | Adjust `TableFormerMode` (FAST vs ACCURATE), OCR engine selection, pipeline options |
| **Docling HybridChunker** | Adjust token budget, chunking aggressiveness |
| **DeepEval** | Run `context_precision` + `context_recall` + `faithfulness` per iteration, broken down by query type (table queries, multi-section, heading-dependent) |
| **Custom orphan chunk scanner** | SQL query: flag chunks starting mid-sentence, partial table rows without headers, empty heading_breadcrumb. Target: 0 orphans. |

---

### Step 11: Add reranker

| Tool | How |
|---|---|
| [**Cohere Rerank 3.5 on Bedrock**](https://aws.amazon.com/blogs/machine-learning/cohere-rerank-3-5-is-now-available-in-amazon-bedrock-through-rerank-api/) | Native Bedrock Rerank API. $2/1K queries (up to 100 docs per query). Available in us-east-1. |
| **Native `tsvector + ts_rank`** | Add hybrid search. Already in schema (generated `content_tsvector` column). Start with native Postgres full-text search. |
| **RRF fusion in SQL** | [Supabase pattern](https://supabase.com/docs/guides/ai/hybrid-search) — single query combining vector + text scores via Reciprocal Rank Fusion. ~30 lines of SQL. |
| Upgrade path | If eval shows synonym/paraphrase queries failing, upgrade to [**pg_textsearch**](https://github.com/timescale/pg_textsearch) (true BM25 with IDF, 4x faster). At high volume, migrate reranker to self-hosted [**BGE-reranker-v2-m3**](https://huggingface.co/BAAI/bge-reranker-v2-m3) on SageMaker (~$0.30-1.50/hr flat). |

Retrieval flow: Query → Titan V2 embed → pgvector top-50 (fast, rough) → tsvector top-50 → RRF merge → Cohere rerank → top-5 (accurate) → return.

### Loop B: TUNE RETRIEVAL (2-3 iterations, diminishing returns)

| Tool | Role |
|---|---|
| **DeepEval** | Measure MRR before/after reranker. Top-K sensitivity check (top-5 vs top-10 vs top-20 vs top-50). Synonym/paraphrase check on 10 vocab-mismatch golden queries. |

---

### Steps 13-14: SHIP (MCP + first consumer)

| Tool | How |
|---|---|
| [**FastMCP**](https://github.com/jlowin/fastmcp) (Python) | MCP server framework. Expose a `query` tool returning top-K chunks with full metadata. |
| [**knowledge-rag**](https://github.com/lyonzin/knowledge-rag) (MIT) | Design reference — 12 MCP tools covering search/ingest/manage. Adapt the tool signatures, replace ChromaDB backend with your pgvector queries. |

```python
# Core MCP tool signature (simplified)
@mcp.tool()
async def search(query: str, top_k: int = 5, source_type: str | None = None) -> list[Chunk]:
    # 1. Embed query with Titan V2
    # 2. Hybrid search (vector + tsvector) with RRF
    # 3. Rerank with Cohere
    # 4. Return chunks + metadata (heading_breadcrumb, source_type, last_modified, score)
```

---

### Steps 15-17: INSTRUMENT

| Tool | How |
|---|---|
| [**Langfuse**](https://github.com/langfuse/langfuse) (MIT, self-hosted) | **Query telemetry:** log every MCP call with query, chunks_returned, top_chunk_score, doc_sources, latency_ms. **Feedback collection:** thumbs up/down via Langfuse's feedback API. **Online scoring:** Langfuse + Ragas integration runs `faithfulness` on production queries periodically. |
| **Langfuse dashboards** | Monthly usage insights: most-queried topics, queries with no good results, source distribution, power users vs inactive teams. |
| **Custom Lambda/cron** | Pipeline health (6 monitors): ingestion completion, docs processed vs expected, embedding API errors/latency, vector DB health, MCP server uptime, index size over time. Slack alerts on failure. |

---

### Step 18: FRESHNESS

| Tool | How |
|---|---|
| **Custom SQL at query time** | Apply per-`content_category` decay curves using `last_modified`. Runbooks: steep decay (6-month half-life). Architecture docs: flat decay (2-year half-life). Derive `content_category` from Confluence labels or LLM-infer during chunking. |

---

### Loop C: LEARN (continuous, two speeds)

| Tool | Role |
|---|---|
| **Langfuse** | **Automated detection:** cluster queries by topic weekly, flag topics with >40% negative feedback, identify sources with low `faithfulness`, flag freshness issues. Outputs a report. |
| **DeepEval** | Re-run eval on expanded golden set (original + representative queries from production via Langfuse query gap detection). |
| [**Arize Phoenix**](https://github.com/Arize-ai/phoenix) | Periodic embedding drift visualization — UMAP projection of query/document embeddings. Spot when new queries cluster away from indexed documents. Not real-time; run monthly or when retrieval quality drops. |
| **Human review** | Fast loop: adjust reranker weights, freshness decay, source_type boosting, top-K — no re-ingest. Slow loop: accumulated patterns diagnose parsing/chunking problems → re-run Loop A for affected sources. **Never automate parameter changes** — spiral feedback risk. |

---

### Step 20: VALIDATE EVAL

| Tool | How |
|---|---|
| **DeepEval** + **human grading** | Human grades 20-30 queries on all 4 dimensions. Compare to DeepEval metric scores. 90%+ agreement = trust automated eval at scale. Re-calibrate when switching Sonnet versions or when corpus changes significantly. |

---

### Loop D: SCALE SOURCES (separate ingestion pipelines, same table + endpoint)

#### Jira (when ready)

| Tool | How |
|---|---|
| **Jira REST API** (via `atlassian-python-api`) | Custom JQL queries: `project = X AND status IN (Done, Resolved, Closed) AND updated >= -90d`. Extract Summary + Description + Resolution + substantive comments. ~200-300 lines. |
| **Noise filtering** | Skip status transitions, field changes, "+1" comments. Index resolved/completed tickets only. |
| **Metadata columns** | Add nullable: `jira_priority`, `jira_status`, `linked_ticket_ids`, `jira_project`. Same pgvector table. |

#### Codebase (when ready)

| Tool | How |
|---|---|
| **LlamaIndex `CodeSplitter`** (wraps tree-sitter) | Parse at function/class boundaries. 100+ languages. |
| **tree-sitter fallback** | Line-based chunking for partial/malformed files that tree-sitter can't parse (migration scripts, config files, PRs). |
| **git diff-based incremental** | On merge to main, re-parse + re-embed only changed files. Track file → chunk mapping for deletion/replacement. |
| **Metadata columns** | Add nullable: `file_path`, `function_name`, `class_name`, `language`, `start_line`, `end_line`. Same pgvector table. |

---

### Steps 23-24: OPEN TO CONSUMERS + Loop E

| Tool | Role |
|---|---|
| **FastMCP** | Same MCP server, no changes — additional consumers are incremental. |
| **Langfuse** | Per-consumer telemetry via trace metadata. Per-consumer eval subsets if needed. |
| **DoorDash two-tier guardrails** (when a consumer is customer-facing) | Tier 1: cosine similarity check between response embedding and chunk embeddings (pgvector, free). Tier 2: Claude Sonnet judge for groundedness + compliance (only when Tier 1 flags). ~100 lines. |

---

### Full Tool Stack at a Glance

| Category | Tool | License | Cost | When |
|---|---|---|---|---|
| PDF parsing | **Docling** | MIT | Free | Step 5 |
| PDF fallback (cross-page tables) | **OCRFlux** | Apache 2.0 | Free | Step 5 (if needed) |
| Confluence export | **confluence-markdown-exporter** | MIT | Free | Step 3 |
| Confluence metadata | **atlassian-python-api** | Apache 2.0 | Free | Step 3 |
| Chunking (PDF) | **Docling HybridChunker** | MIT | Free | Step 7 |
| Chunking (Confluence) | **LangChain MarkdownHeaderTextSplitter** | MIT | Free | Step 7 |
| Context blurbs | **Custom** + Claude Haiku | — | ~$1.02/M doc tokens | Step 7 |
| Multi-representation indexing | **LangChain MultiVectorRetriever + PostgresByteStore** | MIT | Free | Step 7 (for split tables / high-value docs) |
| Embeddings | **Bedrock Titan V2** | AWS | $0.02/M tokens | Step 8 |
| Vector store | **pgvector** + HNSW | PostgreSQL | Free (on existing RDS) | Step 6 |
| Full-text search | **Native tsvector** → upgrade to **pg_textsearch** if needed | OSS | Free | Step 11 |
| ORM | **SQLAlchemy + pgvector-python** | MIT | Free | Step 8 |
| Reranking | **Cohere Rerank 3.5 on Bedrock** → **BGE-v2-m3 on SageMaker** at volume | AWS / MIT | $2/1K queries → ~$1/hr flat | Step 11 |
| MCP server | **FastMCP** | MIT | Free | Step 13 |
| MCP design reference | **knowledge-rag** (lyonzin) | MIT | Free | Step 13 |
| Eval framework | **DeepEval** | MIT | Free | Step 9 |
| Golden set generation | **Ragas TestsetGenerator** | Apache 2.0 | Free | Step 2 |
| Monitoring + telemetry | **Langfuse** (self-hosted) | MIT | Free | Step 15 |
| Embedding drift | **Arize Phoenix** | Elastic v2 | Free | Loop C |
| Guardrails (customer-facing) | **Custom** DoorDash two-tier | — | Free (pgvector) + Sonnet cost | Loop E |
| Jira ingestion (Loop D) | **Jira REST API** + custom | — | Free | Loop D |
| Codebase ingestion (Loop D) | **LlamaIndex CodeSplitter** (tree-sitter) | MIT | Free | Loop D |
