# Internal Knowledge Base — RAG Pipeline Research & Build Plan

Research, evidence analysis, and implementation plan for building a production RAG (Retrieval-Augmented Generation) pipeline that serves organizational knowledge through an MCP (Model Context Protocol) server.

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

## Target stack

- **Vector store:** Postgres + pgvector (standard RDS, not Aurora)
- **Embeddings:** AWS Bedrock Titan Text Embeddings V2 (1024 dims, 8192 token limit)
- **LLM:** Claude Sonnet on Bedrock (chunking, eval, generation)
- **Sources:** PDFs (with complex tables) + Confluence + Jira + codebase (phased)
- **Output:** MCP server returning chunks + metadata to consuming LLMs and apps
- **Eval:** DeepEval + Ragas on Bedrock
- **Monitoring:** Langfuse (self-hosted)

## Key finding

Most of the pipeline is buyable with open-source tools. Only ~500-700 lines of custom code needed:

1. Contextual retrieval (~50 lines) — LLM context blurbs prepended to chunks
2. pgvector schema + hybrid search (~100 lines SQL) — two-table pattern with RRF fusion
3. MCP server (~200-400 lines) — thin retrieval wrapper via FastMCP
4. Two-tier guardrails (~100 lines) — DoorDash-style cosine check + LLM judge

Everything else is configuration and wiring on top of: Docling (PDF parsing), confluence-markdown-exporter, Docling HybridChunker, LangChain MultiVectorRetriever, Cohere Rerank on Bedrock, DeepEval, and Langfuse.

## License

MIT
