# RAG Ingestion Skills & Skill Packs — Research

**Date:** 2026-04-11
**Target stack:** Postgres + pgvector, Claude Sonnet (LLM chunker), AWS Bedrock Titan Text Embeddings V2 (8,192 tokens, 1,024 dims), PDFs (with tables) + Confluence
**Research goal:** Find downloadable, reusable Claude Code skills / agentic skill packs / markdown-based skill files that would help build a production RAG ingestion pipeline (parsing, chunking, metadata framework, pgvector schema, evaluation).

---

## 1. Executive Summary

The honest headline: **there is exactly one Claude Code skill that seriously attempts end-to-end RAG ingestion as a SKILL.md playbook** (Curiositech Windags `rag-document-ingestion-pipeline`), and **one that serves as a knowledge-only architect's reference** (alirezarezvani `rag-architect`). Everything else is either:

- A Confluence-authoring skill that happens to be able to download pages (Spillwave),
- A general-purpose chunking/parsing library you'd call from code (Docling, Chonkie, Unstructured, smart-ingest-kit), or
- An AWS sample notebook / cookbook (aws-samples, anthropic-cookbooks).

**No existing skill covers "metadata framework design based on corpus analysis"** — that remains a genuine gap to build custom.

**Top 5 recommendations (ranked by likely usefulness for your stack):**

| Rank | Skill / Pack | Why it matters |
|---|---|---|
| 1 | **Curiositech Windags `rag-document-ingestion-pipeline`** | Only Claude Code SKILL.md that walks Sources → Parser → Chunker → Enricher → Embedder → Vector DB end-to-end. Explicitly names pgvector as a supported destination. Good scaffold to fork. |
| 2 | **alirezarezvani `rag-architect`** (engineering/POWERFUL tier) | Knowledge-only, but covers pgvector indexing, chunking taxonomy, RAGAS eval. Best "architect reference" to load when making design decisions. |
| 3 | **Docling examples (hybrid chunker + table export)** | Not a skill, but the reference implementation for layout-aware PDF parsing with atomic tables. Wrap its `HybridChunker` + `export_tables.py` as your own internal skill. |
| 4 | **SpillwaveSolutions `mastering-confluence-agent-skill`** | Actual Claude Code skill with `download_confluence.py` that emits markdown + YAML frontmatter metadata (page ID, space key, version, parent ID, title). Directly usable for the Confluence arm of the pipeline. |
| 5 | **aws-samples `semantic-search-using-amazon-aurorapg-pgvector-and-amazon-bedrock`** | Not a skill, but the canonical working example of Titan Embeddings → pgvector on Aurora. Use as a reference for schema + embed call patterns. |

---

## 2. Per-Skill Entries

### 2.1 Curiositech Windags — `rag-document-ingestion-pipeline`

- **Source:** https://github.com/curiositech/windags-skills (listed on LobeHub at https://lobehub.com/skills/curiositech-windags-skills-rag-document-ingestion-pipeline)
- **Format:** Claude Code SKILL.md (YAML frontmatter + body). Part of a 190+ skill pack; convertible to Codex, Gemini CLI, Cursor, and 40+ other agents.
- **What it does:** Walks Claude through building production-grade ingestion workflows following the canonical Sources → Parser → Chunker → Enricher → Embedder → Vector DB flow. Recommends recursive, semantic, and document-structure-aware chunking. Names pgvector, Pinecone, Qdrant, Weaviate, Milvus as supported destinations. Recommends dedup by content hash before embedding to save 30-50% cost.
- **Install:**
  - `claude plugin add /path/to/windags-skills` after cloning, OR
  - `curl` the SKILL.md via LobeHub marketplace, OR
  - copy the skill folder to `~/.claude/skills/`
- **Coverage:**
  - Parsing: partial (names PDF, HTML, MD, DOCX, OCR for images; no specific library recommendation)
  - Chunking: yes (recursive, semantic, doc-structure-aware) — does NOT explicitly call out LLM-based chunking with Sonnet
  - Metadata: partial (enricher stage named, no framework)
  - pgvector: yes (listed as destination)
  - Titan V2: no (lists OpenAI, Cohere, BGE, Nomic)
  - Eval: not covered
- **Pros:** The only Claude Code skill that actually tries to be an end-to-end ingestion playbook. Correct architectural mental model.
- **Cons:** Generic. No Titan, no explicit LLM-chunker-with-Sonnet guidance, no metadata framework, no eval. You'd fork and specialize it.
- **Fit with stack:** Good scaffold, will need customization for Titan V2 and LLM chunking.

---

### 2.2 alirezarezvani `claude-skills` — `engineering/rag-architect/SKILL.md`

- **Source:** https://github.com/alirezarezvani/claude-skills/blob/main/engineering/rag-architect/SKILL.md
- **Format:** Claude Code SKILL.md (knowledge-only, no runnable scripts).
- **What it does:** Comprehensive design-time reference for RAG pipelines. Covers chunking taxonomy, embedding selection (dimension/speed/quality tradeoffs), vector DB comparison **including pgvector with indexing options (HNSW / IVFFlat)**, hybrid retrieval, HyDE, multi-query, reranking, RAGAS-based eval, production patterns, cost, guardrails.
- **Install:**
  - `/plugin marketplace add alirezarezvani/claude-skills` then `/plugin install engineering-advanced-skills@claude-code-skills`, OR
  - Clone and copy `engineering/rag-architect/` into `~/.claude/skills/`
- **Coverage:**
  - Parsing: no (mentions doc-aware chunking generically; no PDF/Confluence specifics)
  - Chunking: yes (taxonomy, not implementation)
  - Metadata framework: no
  - pgvector: yes (indexing options discussed)
  - Titan V2: no (open-source + general models)
  - LLM-based chunking: conceptually, no implementation
  - Eval: yes (RAGAS metrics discussed, no harness code)
- **Pros:** Best "load-me-when-designing" reference. Triggers automatically when asking about RAG design.
- **Cons:** No runnable code, no scripts, no schema templates. Knowledge skill, not action skill.
- **Fit with stack:** Use it as a design consultant, not a builder.

---

### 2.3 SpillwaveSolutions — `mastering-confluence-agent-skill`

- **Source:** https://github.com/SpillwaveSolutions/mastering-confluence-agent-skill
- **Format:** Claude Code SKILL.md + Python scripts (`download_confluence.py`, `upload_confluence.py`, `mark` CLI integration).
- **What it does:** Confluence page management via Atlassian MCP server + REST API. Critically: `download_confluence.py` downloads pages to markdown with YAML frontmatter containing page ID, space key, version, parent ID, title — which is exactly the structured intermediate you need for the Confluence arm.
- **Install:** `pip install skilz` then `skilz install SpillwaveSolutions_mastering-confluence-agent-skill/mastering-confluence` (or manual git clone to `~/.claude/skills/`).
- **Coverage:**
  - Parsing (Confluence storage → markdown): yes
  - Bulk download / CQL-driven selection: partial (CQL supported, bulk not explicitly detailed)
  - Metadata: yes (frontmatter)
  - Chunking / pgvector / Titan / eval: no
- **Pros:** Actual working download script with metadata preservation. Saves a meaningful amount of wiring.
- **Cons:** Authoring-focused, not RAG-focused. Bulk-download ergonomics may need a wrapper for corpus ingestion.
- **Fit with stack:** Direct fit for the Confluence ingestion layer. Pair with a chunking step downstream.

---

### 2.4 SpillwaveSolutions — `confluence-skill`

- **Source:** https://github.com/SpillwaveSolutions/confluence-skill (SKILL.md at https://github.com/SpillwaveSolutions/confluence-skill/blob/main/SKILL.md)
- **Format:** Claude Code SKILL.md + Python scripts.
- **What it does:** Simpler sibling of mastering-confluence. Also has `download_confluence.py` with macro conversion and attachment download.
- **Install:** clone → copy to `~/.claude/skills/`.
- **Coverage:** Confluence download/upload/convert. No RAG specifics.
- **Pros:** Smaller surface, easier to read.
- **Cons:** Less capable than its "mastering" sibling.
- **Fit with stack:** Partial fit — choose between this and `mastering-confluence-agent-skill` based on whether the Mermaid/mark CLI features are needed.

---

### 2.5 Docling (reference implementations, not a skill)

- **Source:** https://github.com/docling-project/docling
- **Key examples:**
  - Hybrid chunking: https://docling-project.github.io/docling/examples/hybrid_chunking/
  - Table export: https://docling-project.github.io/docling/examples/export_tables/
  - Custom convert: https://docling-project.github.io/docling/examples/custom_convert/
  - Pipeline options: https://docling-project.github.io/docling/reference/pipeline_options/
- **Format:** Python library + example scripts. NOT a Claude Code skill — but the examples are markdown-rich and trivially wrap-able as a local skill.
- **What it does:**
  - **Parser:** Layout-aware PDF parsing with `TableFormerMode.ACCURATE` vs `FAST`, OCR engine selection (EasyOCR, Tesseract, system OCR).
  - **Chunker:** `HybridChunker` (docling-core ≥ 2.8.0) = hierarchical document structure + tokenization-aware refinement. Emits chunks with heading breadcrumbs, page info, content type.
  - **Table handling:** `export_tables.py` exports each PDF table as CSV/HTML/Markdown — directly enabling the "tables atomic + multi-representation" strategy you want.
- **Coverage:** Parsing (PDF) = yes, chunking = yes, table atomicity = yes, metadata (headings, page, content type) = yes. Confluence = no. pgvector/Titan/eval = no.
- **Pros:** Production-quality. Active development. The tokenizer-aware HybridChunker is designed to respect the 8,192-token Titan limit if you pass the Titan tokenizer.
- **Cons:** Not a skill — you'd wrap it as one. Python dependency.
- **Fit with stack:** **Strong.** This is the parsing+chunking engine you likely want under the hood, with Sonnet supplementing for cases HybridChunker can't handle well.
- **Suggested action:** Create a local `~/.claude/skills/rag-parsing/` with a SKILL.md that instructs Claude to drive Docling for PDF ingestion.

---

### 2.6 Unstructured.io (library + reference)

- **Source:** https://github.com/Unstructured-IO/unstructured; docs: https://docs.unstructured.io/
- **Format:** Python library + CLI + managed platform. Not a Claude Code skill.
- **What it does:**
  - 71 pre-built source/destination connectors including Confluence and PostgreSQL/pgvector.
  - Element-based parsing (elements carry category_depth, parent_id, page_number — ready for hierarchical metadata).
- **Key refs:**
  - PostgreSQL destination: https://docs.unstructured.io/open-source/ingestion/source-connectors/postgresql
  - Confluence source: https://unstructured-io.github.io/unstructured/ingest/source_connectors/confluence.html
- **Coverage:** Parsing = yes, metadata = yes (element taxonomy), pgvector destination = yes. LLM chunking with Sonnet = no. Eval = no.
- **Pros:** Widest connector coverage including both sources (Confluence) and destinations (pgvector) in one library.
- **Cons:** Heavier dependency footprint than Docling. Some connectors require the managed platform for best results.
- **Fit with stack:** Partial fit. Could replace Docling if you want a single tool for both Confluence and PDFs, at the cost of heft.

---

### 2.7 Chonkie (`chonkie-inc/chonkie`)

- **Source:** https://github.com/chonkie-inc/chonkie
- **Format:** Python library (`pip install chonkie` or `chonkie[all]`).
- **What it does:** Lightweight chunking-only library. Notable strategies: `SemanticChunker`, `LateChunker` (embedding-informed), `NeuralChunker`, `SlumberChunker` (LLM-powered chunking), `RecursiveChunker`, `CodeChunker`.
- **Coverage:** Chunking = yes (including LLM-powered), pgvector = yes (listed as integration), Titan = not mentioned.
- **Pros:** `SlumberChunker` / `NeuralChunker` are directly relevant to "LLM-based chunking with Sonnet" — you could route Chonkie through Sonnet via a custom model adapter.
- **Cons:** Chunking only; no parsing, no metadata framework, no eval. Not a skill.
- **Fit with stack:** Good complement to Docling if you want a drop-in LLM chunker that can be pointed at Claude Sonnet, rather than writing the orchestration by hand.

---

### 2.8 smart-ingest-kit (2dogsandanerd)

- **Source:** https://github.com/2dogsandanerd/smart-ingest-kit
- **Format:** Toolkit repo (not a skill). **Archived 2026-03-15, read-only.**
- **What it does:** Production-extracted RAG ingestion pipeline using Docling for parsing + smart heuristics that pick chunking based on file type (PDF / code / MD). Converts PDF tables to markdown before chunking.
- **Coverage:** Parsing = yes (via Docling), chunking heuristics = yes, table handling = yes. Metadata/pgvector/Titan/eval = no.
- **Pros:** Real production code. Good reference for "PDF tables → markdown before chunking" pattern.
- **Cons:** Archived, no longer maintained. Not pip-installable.
- **Fit with stack:** Read-only reference. Steal patterns, don't depend on it.

---

### 2.9 LlamaIndex `ConfluenceReader` (llamahub)

- **Source:** https://github.com/run-llama/llama_index/tree/main/llama-index-integrations/readers/llama-index-readers-confluence
- **Format:** Python package (`pip install llama-index-readers-confluence`). Not a Claude Code skill.
- **What it does:** Loads Confluence pages via `space_key`, `page_ids`, `label`, `folder_id`, or `cql`. Supports attachments (`include_attachments=True` extracts text from downloaded attachments via custom_parsers). Emits LlamaIndex `Document` objects with metadata.
- **Coverage:** Confluence ingestion = yes, attachment parsing = yes, metadata = yes. pgvector/Titan/eval = no.
- **Pros:** More flexible source selection than the Spillwave skill (CQL + label + folder). Production-grade.
- **Cons:** LlamaIndex dependency. Output is LlamaIndex objects, not raw markdown.
- **Fit with stack:** Strong alternative to Spillwave for Confluence; pick based on whether you want raw markdown+frontmatter (Spillwave) or structured Document objects (LlamaIndex).

---

### 2.10 Knowledge RAG (`lyonzin/knowledge-rag`)

- **Source:** https://github.com/lyonzin/knowledge-rag
- **Format:** MCP server for Claude Code (not a SKILL.md skill). `clone → pip install → restart Claude Code`.
- **What it does:** Local hybrid search (semantic + BM25 + cross-encoder reranker) with markdown-aware chunking (`##`/`###` headers) over 9 formats (MD, PDF via PyMuPDF, DOCX, XLSX, PPTX, CSV, TXT, PY, JSON).
- **Coverage:** Parsing (PDF/MD/office) = yes, chunking (header-aware) = yes, eval = no, metadata framework = no.
- **Pros:** Turnkey local RAG you can point at a corpus.
- **Cons:** **ChromaDB/DuckDB backend, not pgvector.** No Confluence. Not configurable enough to adopt as the production pipeline.
- **Fit with stack:** **Poor fit** for the target stack — different vector store, different ergonomics. Useful only as a local dev sandbox or structural reference.

---

### 2.11 applied-artificial-intelligence — `claude-code-toolkit/skills/rag-implementation`

- **Source:** https://github.com/applied-artificial-intelligence/claude-code-toolkit/blob/main/skills/rag-implementation/SKILL.md
- **Format:** Claude Code SKILL.md (knowledge-only).
- **What it does:** General RAG playbook. Vector DB comparison (Qdrant/Pinecone/Chroma/Weaviate/Milvus — **no pgvector**), chunking strategies, embedding models, retrieval optimization, production patterns.
- **Coverage:** Partial. Does NOT mention pgvector, Titan V2, Claude Sonnet chunking, PDF parsing libraries, Confluence, or table handling. Generic foundational guide.
- **Pros:** Cleanly structured reference.
- **Cons:** Shallower and less relevant than `alirezarezvani/rag-architect`. **Partial fit at best.**

---

### 2.12 Anthropic official skills (`anthropics/skills`)

- **Source:** https://github.com/anthropics/skills
- **Relevant sub-skills:** `skills/pdf` (extract text, tables, metadata; merge/annotate), `skills/docx`, `skills/xlsx`, `skills/pptx`.
- **Format:** Official Anthropic SKILL.md skills.
- **What they do:** Document manipulation primitives. `skills/pdf` can extract text and tables from PDFs with reasonable quality.
- **Coverage:** PDF extraction = yes, tables = yes. No chunking, no RAG, no pgvector, no Confluence, no eval.
- **Pros:** Officially supported, maintained by Anthropic.
- **Cons:** Document manipulation, not ingestion pipeline. Partial fit as a fallback parser if Docling is too heavy.
- **Fit with stack:** Partial fit for PDF parsing only.

---

### 2.13 aws-samples — `semantic-search-using-amazon-aurorapg-pgvector-and-amazon-bedrock`

- **Source:** https://github.com/aws-samples/semantic-search-using-amazon-aurorapg-pgvector-and-amazon-bedrock
- **Format:** AWS sample repo (Python + Terraform/CDK). Not a skill.
- **What it does:** **The reference implementation for your exact embedding+store combo.** Uses Amazon Titan Embeddings from Bedrock → stores in Aurora PostgreSQL with pgvector. Demonstrates schema, embedding call, retrieval via LangChain.
- **Coverage:** Titan embedding call = yes, pgvector schema = yes, RAG retrieval = yes. Parsing/chunking/metadata/eval = no or minimal.
- **Pros:** Canonical working example of the exact stack.
- **Cons:** Not a skill. LangChain-centric.
- **Fit with stack:** **Essential reference.** Copy the Titan-Bedrock call pattern and the pgvector schema DDL.

---

### 2.14 aws-samples — `rag-with-amazon-bedrock-and-pgvector`

- **Source:** https://github.com/aws-samples/rag-with-amazon-bedrock-and-pgvector
- **Format:** AWS sample (Lambda + RDS + LangChain).
- **What it does:** Deploys a RAG web app on AWS with Bedrock + pgvector on RDS. Uses OpenAI embeddings by default (swappable for Titan with code changes).
- **Coverage:** Deployment scaffolding (Lambda-in-VPC → RDS) = yes; Titan = requires a swap.
- **Pros:** Infrastructure pattern for pgvector-on-RDS + Bedrock from inside a VPC.
- **Cons:** Not a skill. Default embeddings are OpenAI, not Titan.
- **Fit with stack:** Partial fit — useful if the team ever needs the infra scaffold, otherwise the sibling Aurora sample is closer.

---

### 2.15 aws-samples — `amazon-bedrock-samples/embeddings/Titan-V2-Embeddings.ipynb`

- **Source:** https://github.com/aws-samples/amazon-bedrock-samples/blob/main/embeddings/Titan-V2-Embeddings.ipynb
- **Format:** Notebook.
- **What it does:** Minimal Titan V2 embedding call pattern. Confirms: 8,192 token input, 1,024-dim default output, dimensionality configurable down for ~33% cost reduction vs V1.
- **Coverage:** Titan V2 API = yes. Everything else = no.
- **Pros:** Definitive call pattern.
- **Cons:** Trivial scope.
- **Fit with stack:** Reference-only.

---

### 2.16 Anthropic knowledge-graph cookbook

- **Source:** https://platform.claude.com/cookbook/capabilities-knowledge-graph-guide (March 2026)
- **Format:** Official cookbook guide.
- **What it does:** Entity extraction, relation mining, deduplication. Relevant to **metadata enrichment** — if you go beyond "flat metadata fields" into entity-aware metadata, this is the starting point.
- **Coverage:** Metadata (entity-level) = yes. Parsing/chunking/pgvector = no.
- **Pros:** Official Anthropic guide using Claude for the LLM work.
- **Cons:** Not a skill. Not directly about chunk metadata frameworks.
- **Fit with stack:** Useful input when designing the custom metadata framework.

---

### 2.17 Ragas (`vibrantlabsai/ragas`)

- **Source:** https://github.com/vibrantlabsai/ragas — https://docs.ragas.io/
- **Format:** Python library. Not a skill.
- **What it does:** RAG evaluation harness. Metrics: faithfulness, answer relevance, context precision/recall. LLM-as-judge with `judge_alignment` metric against human expert verdicts. Synthetic golden dataset generation.
- **Coverage:** Evaluation = yes. Other = no.
- **Pros:** De facto standard for RAG eval.
- **Cons:** Not a skill, but trivially wrappable. AWS has notebooks demonstrating Ragas + Claude 3 Sonnet on Bedrock (`aws-samples/sample-rag-evaluation-ragas`).
- **Fit with stack:** **Essential** — wrap as a local skill that Claude can invoke to run evals. Good integration path with Sonnet as the judge model.

---

## 3. Gap Analysis

Honest read: **the Claude Code ecosystem has NOT produced strong, purpose-built RAG ingestion skill packs yet.** The generally-excellent skills repos (obra/superpowers, anthropics/skills, alirezarezvani, Curiositech Windags, Spillwave) each fill only a corner:

| Need | Existing coverage | Gap |
|---|---|---|
| PDF parsing (layout + tables) | Docling + Unstructured libraries; anthropics/skills/pdf as fallback. **No skill wraps them.** | Need a local SKILL.md that instructs Claude to drive Docling with the correct config (HybridChunker + TableFormer.ACCURATE + OCR fallback). |
| Confluence → structured intermediate | Spillwave skills (2 of them) + LlamaIndex ConfluenceReader | Decent. Spillwave works; choose between the two. |
| LLM-based chunking with Sonnet | Chonkie has `SlumberChunker`/`NeuralChunker` (library only); no skill | Need a custom skill that encodes your chunking prompt, validation (max char cap + numerical sanity), and the "re-chunk on failure" loop. |
| Metadata framework design from corpus analysis | **None.** No skill, no template, no public framework. Unstructured emits element-level metadata but doesn't help you *design* a schema. | **Biggest gap. Must be built custom.** A skill that takes a sample corpus, invokes Claude to propose a metadata taxonomy (content/technical/semantic per arxiv 2512.05411), and outputs a schema + extractor prompts. |
| Multi-representation indexing for split tables (description prepended, summary chunks, HyDE questions, link metadata) | **None.** Discussed in blog posts (Microsoft Azure chunk enrichment; Unstructured insights) but not codified. | Build custom. Relatively straightforward once the metadata framework exists. |
| pgvector schema + HNSW tuning | alirezarezvani/rag-architect (knowledge); aws-samples Aurora repo (code) | Decent. Combine the two. |
| Titan V2 integration | aws-samples Titan-V2 notebook + Aurora sample | Decent reference; no skill. |
| Evaluation harness (golden queries, LLM-as-judge) | Ragas library + aws-samples Ragas+Bedrock notebook | Decent, not wrapped as a skill. Easy to wrap. |

**What does NOT exist as a downloadable skill:**

1. A Claude Code skill that drives Docling with stack-aware defaults (Titan tokenizer for chunk sizing).
2. A Claude Code skill for **corpus analysis → metadata schema generation**.
3. A Claude Code skill for **LLM-chunking-with-Sonnet** specifically, with the chunk validation loop.
4. A Claude Code skill for pgvector-with-Titan schema DDL generation.
5. A Claude Code skill that runs a Ragas eval harness on a pgvector store.

**What the team will have to build from scratch:** items 2, 3, and 5. Items 1 and 4 are thin wrappers around existing libraries/samples.

---

## 4. Recommended Next Action

**Try these two first, in order:**

1. **Install `curiositech/windags-skills` rag-document-ingestion-pipeline AND `alirezarezvani/claude-skills` rag-architect side-by-side.** Five minutes. They don't conflict (one is a builder playbook, one is a design reference). Use them together on a test ingestion and observe where they fall short — those gaps become the spec for the custom skills you'll build.

    ```bash
    # Windags
    git clone https://github.com/curiositech/windags-skills ~/tmp/windags
    cp -r ~/tmp/windags/skills/rag-document-ingestion-pipeline ~/.claude/skills/

    # rag-architect (via marketplace)
    # In Claude Code:
    /plugin marketplace add alirezarezvani/claude-skills
    /plugin install engineering-advanced-skills@claude-code-skills
    ```

2. **Install SpillwaveSolutions `mastering-confluence-agent-skill` for the Confluence arm.**

    ```bash
    pip install skilz
    skilz install SpillwaveSolutions_mastering-confluence-agent-skill/mastering-confluence
    ```

    Then test: pull a small Confluence space to markdown+frontmatter via the included script. If bulk/CQL selection is too limited, fall back to LlamaIndex `ConfluenceReader`.

**Then build custom (in priority order):**

1. **A local `rag-parse-pdf` skill** that drives Docling (`HybridChunker` + `TableFormerMode.ACCURATE` + Titan tokenizer) and emits atomic-table markdown with heading breadcrumbs as metadata.
2. **A local `rag-metadata-framework` skill** that takes a sample corpus, asks Claude to analyze format/content types, and proposes a metadata schema (content/technical/semantic taxonomy per arxiv:2512.05411). This is the highest-value custom build since nothing public covers it.
3. **A local `rag-llm-chunker` skill** encoding the Sonnet chunking prompt + validation loop (max char cap, numerical sanity, re-chunk on failure). Consider wrapping Chonkie's `SlumberChunker` pointed at Sonnet rather than writing the orchestration by hand.
4. **A local `rag-eval-harness` skill** that wraps Ragas with Sonnet-as-judge + a golden-query fixture, invokable against the pgvector store.

---

## Sources

### Claude Code skills / skill packs
- [anthropics/skills (official)](https://github.com/anthropics/skills)
- [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official)
- [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills)
- [rag-architect SKILL.md](https://github.com/alirezarezvani/claude-skills/blob/main/engineering/rag-architect/SKILL.md)
- [curiositech/windags-skills](https://github.com/curiositech/windags-skills)
- [rag-document-ingestion-pipeline on LobeHub](https://lobehub.com/skills/curiositech-windags-skills-rag-document-ingestion-pipeline)
- [applied-artificial-intelligence/claude-code-toolkit rag-implementation SKILL.md](https://github.com/applied-artificial-intelligence/claude-code-toolkit/blob/main/skills/rag-implementation/SKILL.md)
- [SpillwaveSolutions/confluence-skill](https://github.com/SpillwaveSolutions/confluence-skill)
- [SpillwaveSolutions/mastering-confluence-agent-skill](https://github.com/SpillwaveSolutions/mastering-confluence-agent-skill)
- [obra/superpowers](https://github.com/obra/superpowers)
- [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills)
- [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)
- [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code)
- [rohitg00/awesome-claude-code-toolkit](https://github.com/rohitg00/awesome-claude-code-toolkit)
- [lyonzin/knowledge-rag (MCP server)](https://github.com/lyonzin/knowledge-rag)

### Libraries (parsing, chunking, connectors)
- [docling-project/docling](https://github.com/docling-project/docling)
- [Docling hybrid chunking example](https://docling-project.github.io/docling/examples/hybrid_chunking/)
- [Docling table export example](https://docling-project.github.io/docling/examples/export_tables/)
- [Docling pipeline options](https://docling-project.github.io/docling/reference/pipeline_options/)
- [chonkie-inc/chonkie](https://github.com/chonkie-inc/chonkie)
- [Unstructured PostgreSQL connector docs](https://docs.unstructured.io/open-source/ingestion/source-connectors/postgresql)
- [Unstructured Confluence connector docs](https://unstructured-io.github.io/unstructured/ingest/source_connectors/confluence.html)
- [Unstructured metadata for RAG guide](https://unstructured.io/insights/how-to-use-metadata-in-rag-for-better-contextual-results)
- [LlamaIndex ConfluenceReader](https://docs.llamaindex.ai/en/stable/api_reference/readers/confluence/)
- [llama-index-readers-confluence source](https://github.com/run-llama/llama_index/blob/main/llama-index-integrations/readers/llama-index-readers-confluence/README.md)
- [LlamaHub](https://llamahub.ai/)
- [2dogsandanerd/smart-ingest-kit (archived)](https://github.com/2dogsandanerd/smart-ingest-kit)

### AWS Bedrock + Titan + pgvector references
- [aws-samples/semantic-search-using-amazon-aurorapg-pgvector-and-amazon-bedrock](https://github.com/aws-samples/semantic-search-using-amazon-aurorapg-pgvector-and-amazon-bedrock)
- [aws-samples/rag-with-amazon-bedrock-and-pgvector](https://github.com/aws-samples/rag-with-amazon-bedrock-and-pgvector)
- [aws-samples Titan-V2-Embeddings notebook](https://github.com/aws-samples/amazon-bedrock-samples/blob/main/embeddings/Titan-V2-Embeddings.ipynb)
- [Amazon Titan Text Embeddings V2 docs](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html)
- [Titan V2 launch announcement](https://aws.amazon.com/blogs/aws/amazon-titan-text-v2-now-available-in-amazon-bedrock-optimized-for-improving-rag/)

### pgvector schema / design references
- [Building a Production RAG System with pgvector (Markaicode)](https://markaicode.com/pgvector-rag-production/)
- [pgvector key features 2026 guide (Instaclustr)](https://www.instaclustr.com/education/vector-database/pgvector-key-features-tutorial-and-pros-and-cons-2026-guide/)

### Metadata frameworks
- [Systematic Framework for Enterprise Knowledge Retrieval (arxiv:2512.05411) — LLM-generated metadata + three-category taxonomy (content/technical/semantic)](https://arxiv.org/html/2512.05411v2)
- [Azure RAG chunk enrichment phase](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-enrichment-phase)
- [AutoMeta RAG dynamic metadata framework](https://thinkinbytes.medium.com/autometa-rag-enhancing-data-retrieval-with-dynamic-metadata-driven-rag-framework-6ace339fda75)
- [Anthropic knowledge-graph construction cookbook](https://platform.claude.com/cookbook/capabilities-knowledge-graph-guide)

### Evaluation
- [vibrantlabsai/ragas](https://github.com/vibrantlabsai/ragas)
- [Ragas docs](https://docs.ragas.io/)
- [aws-samples/sample-rag-evaluation-ragas notebook](https://github.com/aws-samples/sample-rag-evaluation-ragas/blob/main/ragas_notebook.ipynb)
- [confident-ai/deepeval](https://github.com/confident-ai/deepeval)

### Cookbook / RAG design background
- [anthropics/claude-cookbooks RAG with Pinecone](https://github.com/anthropics/claude-cookbooks/blob/main/third_party/Pinecone/rag_using_pinecone.ipynb)
- [anthropics/claude-cookbooks RAG with MongoDB](https://github.com/anthropics/claude-cookbooks/blob/main/third_party/MongoDB/rag_using_mongodb.ipynb)
