# Internal Knowledge Base — RAG Pipeline Research & Build Plan

Research, evidence analysis, and implementation plan for building a production RAG (Retrieval-Augmented Generation) pipeline that serves organizational knowledge through an MCP (Model Context Protocol) server.

## Getting Started

### Prerequisites

- Python 3.12+ with `venv`
- Docker Desktop (for pgvector)
- ~500 MB disk space for embeddings + corpus

### Setup

```bash
# Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install beautifulsoup4 sentence-transformers psycopg2-binary tiktoken langchain-text-splitters

# Database (pgvector in Docker)
docker compose up -d
docker exec -i ikb_pgvector psql -U ikb -d ikb < scripts/init_schema.sql
```

Connection string: `postgresql://ikb:ikb_local@localhost:5433/ikb` (container: `ikb_pgvector`, port: 5433).

### Running the pipeline

The pipeline has four stages. Each script is idempotent and resume-safe.

```bash
# 1. Crawl the corpus (already done — outputs in data/knowva_manuals/articles/)
python scripts/crawl_knowva.py

# 2. Enrich metadata (headings, acl, authority tier, content_category)
python scripts/enrich_metadata.py

# 3. Preprocess HTML — source-specific normalization (heading fix, layout-table unwrap, div-table unwrap)
python scripts/knowva_preprocess.py

# 4. Chunk — generic source-agnostic splitter (outputs data/knowva_manuals/chunks/all_chunks.json)
python scripts/chunk_documents.py

# 5. Embed and store in pgvector (resume-safe — skips already-inserted documents)
python scripts/embed_and_store.py
```

### Repo layout

```
data/
  knowva_manuals/
    articles/          ← raw crawled HTML + metadata sidecars (committed)
    preprocessed/      ← normalized HTML (gitignored — regenerable)
    chunks/            ← chunked JSON (gitignored — regenerable)
  vadir_parsed/        ← Docling-parsed PDF (committed — slow to reproduce)
  golden_query_set.json ← 110 validated evaluation queries

scripts/
  crawl_knowva.py         ← eGain v11 API crawler
  enrich_metadata.py      ← adds headings, acl, authority tier, content_category
  knowva_preprocess.py    ← source-specific HTML normalizations for KnowVA
  chunk_documents.py      ← source-agnostic chunker (HTML + markdown)
  embed_and_store.py      ← mxbai-embed-large → pgvector
  init_schema.sql         ← documents + document_chunks tables, HNSW index
```

### Current status

See `TODO.md` for the Zero-to-MCP checklist. Canonical plan is in `docs/2026-04-11-engineering-rag-evidence-and-howtos.md` § "From Zero to Knowledge MCP". Steps 1-3, 5-8 done; Step 9 (eval harness) is next.

## What's in here

### [Engineering RAG — Evidence, Methodology, and How-Tos](docs/2026-04-11-engineering-rag-evidence-and-howtos.md)

Deep analysis of the engineering RAG landscape:

- **Measurable gains** — evidence-ranked analysis of published RAG deployments (Uber Genie/EAg-RAG, Dropbox Dash, LinkedIn KG-RAG, DoorDash, Spotify AiKA, Stripe Minions), graded by strength of evidence (RCT > offline eval > telemetry > self-report)
- **Disclosed architectures** — what each team actually built (chunking, embedding, retrieval, reranking, eval)
- **Multi-source evidence** — does combining codebase + wiki + on-call docs actually help? (honest answer: ubiquitously assumed, never benchmarked)
- **Dos, don'ts, and tradeoffs** — practitioner consensus on chunking, ACLs, freshness, citations, feedback loops
- **Proof points** — evidence tables for 8 key architectural decisions with "if challenged" responses
- **Zero-to-MCP step-by-step build plan** — 22 steps + 5 iteration loops (A-E) with specific eval metrics per loop
- **2026 production RAG consensus** — contextual retrieval (49-67% failure reduction), hierarchical chunking, hybrid search, reranker benchmarks, eval frameworks, cost control

### [RAG Ingestion Skills & Skill Packs — Research](docs/2026-04-11-rag-ingestion-skills-research.md)

Survey of existing Claude Code skills, open-source libraries, and AWS samples for RAG ingestion:

- 17 tools evaluated across parsing, chunking, metadata, pgvector, evaluation
- Gap analysis identifying what exists vs what needs custom building
- Ranked recommendations for the target stack (Postgres + pgvector, Claude Sonnet, AWS Bedrock Titan V2)

### [RAG Pipeline — Buy vs Build Map](docs/2026-04-12-rag-pipeline-buy-vs-build.md)

Component-level buy-vs-build analysis for every pipeline stage:

- **Decision matrix** — which stages use existing tools vs custom code
- **Tool recommendations** with specific repos, versions, licenses, and costs
- **Cost breakdown** — free vs paid, estimated monthly costs (~$65-75/mo at moderate volume)
- **Tools mapped to each build step** — specific tool for every step in the zero-to-MCP plan, including schema DDL and MCP server signature

## Actual stack (as built)

- **Vector store:** Postgres + pgvector (local via Docker during build; RDS-ready for prod)
- **Embeddings:** mxbai-embed-large (1024 dims, local via sentence-transformers) — replaces original Titan V2 plan, zero API cost
- **LLM:** Claude Sonnet (planned for eval + generation; optional for Loop A summary indexing)
- **Sources (current):** KnowVA HTML manuals (M22-3, M22-4) + VADIR PDF. Confluence/Jira deferred to Loop D.
- **Output:** MCP server returning chunks + metadata (Steps 15-16, not yet built)
- **Eval:** DeepEval + golden query set (Step 9, next)

## Key finding

Most of the pipeline is buyable with open-source tools. Only ~500-700 lines of custom code needed:

1. Contextual retrieval (~50 lines) — LLM context blurbs prepended to chunks
2. pgvector schema + hybrid search (~100 lines SQL) — two-table pattern with RRF fusion
3. MCP server (~200-400 lines) — thin retrieval wrapper via FastMCP
4. Two-tier guardrails (~100 lines) — DoorDash-style cosine check + LLM judge

Everything else is configuration and wiring on top of: Docling (PDF parsing), confluence-markdown-exporter, Docling HybridChunker, LangChain MultiVectorRetriever, Cohere Rerank on Bedrock, DeepEval, and Langfuse.

## License

MIT
