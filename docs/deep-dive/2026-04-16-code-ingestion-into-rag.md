# Deep Dive: Should Source Code Go Into RAG? (Revised View)

**Date:** 2026-04-16
**Context:** Follow-up to the 2026-04-15 codebase-context-for-LLMs deep-dive. Earlier framing of "Pattern B (federated MCP retrieval) beats Pattern A (unified RAG)" was too clean — production teams like Dropbox Dash and Uber Genie explicitly converge on unified indexes. This revision focuses specifically on **how source code should be handled** within that picture.

## Executive Summary

**For most coding-agent and developer-tooling use cases in April 2026, source code does not belong in a generic docs RAG.** Production code retrieval lives in specialized systems (grep/BM25 + LSP + graph), not in the same vector index as documents. The strongest single piece of evidence is **GrepRAG (arXiv 2601.23254, Feb 2026)**: an optimized grep retriever (grep + identifier-weighted re-ranking + structure-aware deduplication) beats BM25 and an early graph baseline (GraphCoder) on CrossCodeEval by 7–15.6% exact match. Production systems that publish architectures (Dropbox Dash, Uber Genie, Atlassian Rovo, Glean) ingest docs, tickets, wikis, and Slack as the default; when they do index code (Rovo Bitbucket, Notion AI) it's usually via a distinct path, not folded into the primary docs index. Dedicated code intelligence lives in a parallel system (internal Sourcegraph equivalents, LSP-based tools, grep-over-monorepo).

**Important stress-test caveats** (validated by 2026-04-16 adjudication deep-dive, see `2026-04-16-docs-vs-code-rag-adjudication.md`):
- GrepRAG's only graph baseline is **GraphCoder**, which already loses to plain BM25 in their own numbers. The paper does **not** compare against stronger modern graph retrievers (RepoGraph, DraCo, CoCoMIC). The claim is "grep is competitive at the baseline band," not "grep matches all modern graph-based approaches."
- "GrepRAG" is not naive grep. The winning variant includes identifier-weighted re-ranking + structure-aware deduplication. Naive grep is introduced as a weaker baseline in the same paper.
- The 2026 consensus is **task-type-dependent**, not "grep dominates." Per CodeCompass: BM25 wins lexical/semantic tasks (100% ACS), graph wins architectural/hidden-dependency tasks (+20 ACS). Per CodeRAG-Bench (NAACL 2025): modern code-specific dense embedders (voyage-code-3, jina-code-v2) beat BM25 on code — reversing the classic BEIR finding. **Hybrid retrieval is the production answer for any code-RAG system.**

Code-RAG earns its keep in four specific conditions: (1) codebase too large for agentic exploration to converge (>5M LoC), (2) semantic/intent-based queries where lexical overlap is low, (3) non-agentic search UI that can't afford 5–10 tool turns, (4) cross-language/cross-repo discovery where LSP doesn't span. Two additional conditions surfaced during stress-test: (5) non-code artifacts alongside code (ADRs, design docs, commit messages) where dense retrieval spans the "code + why" gap, (6) latency-bound single-shot settings where the agent-iteration cost of grep-first dominates. Even in those conditions, the winning recipe is tree-sitter AST chunking + Anthropic Contextual Retrieval + hybrid BM25 + code-specific dense + cross-encoder rerank — not naive chunk-and-embed.

## Findings

### 1. What top production RAG systems actually do with code

| System | Code in main RAG? | Mechanism |
|---|---|---|
| **Dropbox Dash** | GitHub is a connector, but chunking is generic prose-style; code not first-class | Unified search index, on-the-fly chunking at query time, lexical first-stage + embedding rerank |
| **Uber Genie / EAg-RAG** | No — code lives in separate code-intel systems | SIA (in-house vector DB) over engineering docs/runbooks/wikis only |
| **Atlassian Rovo** | Not primarily — code-aware recursive separators on code snippets inside Confluence | EmbeddingGemma-300m, hybrid retrieval, Teamwork Graph overlay |
| **Glean** | GitHub connector, generic chunker | Unified hybrid index, permissions-aware |
| **LinkedIn KG-RAG** | No — oriented at customer-service/product knowledge | Hierarchical knowledge graph, not source code |

**The pattern:** production RAG stacks ingest tacit knowledge (docs, tickets, Slack, wikis), not source code. When code appears, it's incidental. Dedicated code intelligence lives in a parallel system (internal Sourcegraph-equivalents, LSP-based tools, or grep-over-monorepo).

This matters for the question. If you're asking "should I build a RAG over my codebase," the honest answer is: **the teams with the most engineering resources looked at this problem and chose not to.**

### 2. GrepRAG — the February 2026 paper (with important baseline caveats)

GrepRAG (arXiv 2601.23254) is the cleanest recent ablation isolating grep-based retrieval. Findings as stated in the paper:

- **Optimized GrepRAG** (grep + identifier-weighted re-ranking + structure-aware deduplication) scores **42.29% EM** on CrossCodeEval Python, vs best baseline RLCoder at 36.59% and BM25 VanillaRAG at 24.99%. Java EM: GrepRAG 43.15% vs RLCoder 39.46%.
- Naive grep (the unoptimized baseline) matches BM25 and beats the single graph baseline tested (**GraphCoder**, 19.44% EM).
- Retrieval latency: 0.02s (vs GraphCoder 0.26s, RepoFuse 1.64s).
- Implication: for **repo-level code completion**, optimized grep was competitive with the baselines evaluated. LLM-issued grep commands can be a better retrieval policy than naive dense embeddings + rerank when given grep as a tool.

**Critical baseline caveats (per 2026-04-16 adjudication):**
- The only graph baseline is **GraphCoder**, which already loses to plain BM25 (19.44% < 24.99%). GrepRAG does NOT compare against modern graph retrievers — **RepoGraph, DraCo, or CoCoMIC** — that show the strongest graph advantages elsewhere in the literature. "Beats graph" is narrower than it sounds.
- "GrepRAG" is not equivalent to agent-driven ripgrep calls. The winning variant has non-trivial post-processing (identifier-weighted re-ranking, structure-aware dedup). The naive variant is introduced as a baseline, not the headline result.
- Paper is ~10 weeks old as of this writing; no independent replication or critique yet published.

Caveat (original): GrepRAG tested code completion, not debugging/refactoring/cross-file reasoning. Those tasks are more favorable to grep than tasks requiring semantic similarity without lexical anchors, or architectural/transitive-dependency queries (where CodeCompass shows graph wins by +20 ACS).

### 3. The modest actual gains from AST chunking (cAST)

cAST (arXiv 2506.15655, EMNLP Findings 2025) is the cleanest published code-chunking ablation:
- Tree-sitter AST chunking vs naive line/char splits: **+4.3 Recall@5, +2.67 Pass@1** on RepoEval / SWE-bench.
- StarCoder2-7B end-to-end: +5.5 pts on RepoEval.

Real win, but modest. Most of the lift comes from not shredding function bodies. The gap between "did AST chunking" and "did naive chunking" is smaller than the gap between "used grep" and "used vector retrieval."

### 4. Contextual Retrieval — the biggest measured single lever for code-RAG

Anthropic's Contextual Retrieval (prepend LLM-generated 1–3 sentence context to each chunk before embedding):
- Embeddings alone: **-35% failure rate** (5.7% → 3.7%, top-20)
- + Contextual BM25: **-49%**
- + Rerank: **-67%**

Code was in Anthropic's test mix, but they didn't publish a per-domain breakdown isolating code. No independent reproduction on code-specific benchmarks (RepoEval, SWE-bench) has surfaced. This is the single biggest load-bearing unknown for code-RAG.

### 5. BM25 consistently wins or ties on code — identifier overlap is high-signal

Repeated finding across 2025–2026 studies: **BM25 alone often beats pure dense retrieval on code** because code has high identifier overlap (exact symbol names, error strings, version numbers) and dense embeddings blur these. Hybrid (dense + sparse + RRF) is the 2026 production default:

- **SPLADE-Code** (arXiv 2603.22008, March 2026): learned sparse retrieval specialized for code, 600M–8B params, sub-ms latency. Claims SOTA vs dense at fraction of the cost. No clean lift numbers in public abstracts yet.
- **Code embedding leaderboard (April 2026 MTEB-Code)**: Voyage-Code 3 (84.0) leads managed; Qwen3-Embedding-8B leads open-source; CodeRankEmbed, Jina Code V2 competitive.
- Empirical rule: dense only ≪ BM25 only ≤ BM25 + dense + RRF + rerank.

### 6. No clean benchmark isolates vector-vs-symbol-vs-grep with model held constant

This is the honest gap. CodeRAG-Bench (NAACL 2025) covers 10 retrievers × 10 LMs but only dense/sparse retrievers — no symbol-graph or tree-sitter comparators. SWE-bench Pro April 2026 (Augment 51.8 / Cursor 50.2 / Claude Code 49.8 on same Opus 4.5) shows hybrid > embedding > pure-agentic deltas of ~2pp, but retrieval is confounded with scaffold quality. The "filesystem beats vector" LlamaIndex study was on **documents, not code** — citing it as evidence for code is a category error.

No published 2026 benchmark cleanly isolates vector-search vs symbol-tools vs agentic-grep on code with the same LLM. Anyone claiming otherwise is extrapolating.

### 7. When each approach wins — the conditional matrix

| Condition | Winner | Why |
|---|---|---|
| Structural queries (callers, definitions, refs, type hierarchies) | **LSP / symbol tools** (Serena, Cody) | Deterministic, compiler-accurate; RAG and grep are both worse |
| Repo fits practical agent exploration (<5M LoC, reasonable naming) | **Agentic grep** | GrepRAG evidence; no index maintenance; zero staleness |
| Semantic/intent queries with low lexical overlap | **Hybrid RAG** with Contextual Retrieval | Embeddings bridge naming gap; identifier-BM25 keeps lexical safety net |
| Very large monorepo (Linux/Chromium/Google3 scale) | **Meta-RAG / summarization-over-code** | Raw chunks don't fit; agent exploration can't converge |
| Non-agentic UI (instant search, no tool budget) | **Hybrid RAG** | No other option — can't afford 5+ tool turns |
| Cross-language / cross-repo discovery | **Code graph** (Cody/Sourcegraph) or **unified RAG** | LSP doesn't span boundaries |

## The Best Recipe for Code-in-RAG (If You're Going to Do It)

Synthesized from cAST, Anthropic Contextual Retrieval, CodeRAG-Bench, Qodo's 10k-repo writeup, Prem AI 2026 benchmark guide, and Atlassian Rovo's engineering blog.

### Pipeline

1. **Chunk at symbol granularity via tree-sitter AST.** cAST pattern: split large nodes, merge siblings to a token budget (~512–1024). Fall back to code-aware recursive separators on class/function boundaries if no parser. Attach rich metadata per chunk: `repo`, `path`, `language`, `symbol_name`, `symbol_kind`, `imports`, `commit_sha`, `is_test`, `is_generated`, `line_range`.

2. **Contextualize before embedding.** Prepend 1–3 LLM-generated sentences per chunk ("This function validates JWT signatures in the auth middleware; called by X and Y"). Measured −35% failure alone, up to −67% stacked with BM25 + rerank. The biggest single lever.

3. **Choose embedder.** Voyage-Code 3 (managed, MTEB-Code 84.0) or Qwen3-Embedding-8B (self-hosted leader). A strong general embedder in a unified index with `content_type` filter is an acceptable simplification once hybrid + rerank are in place.

4. **Hybrid retrieval is non-negotiable.** Dense + BM25 (or SPLADE-Code if you can host it) + Reciprocal Rank Fusion. Hybrid reports ~17% recall lift over dense alone on code in 2026 production benchmarks. Use identifier-aware tokenization for BM25 (split camelCase, snake_case) — vanilla tokenization under-indexes identifiers.

5. **Rerank with a cross-encoder.** Top ~50 hybrid candidates → top 5–10. Cohere rerank-v3 is the 2026 production default; BGE/Jina for self-hosted. Consistently the largest single-component improvement in production studies. Use FlashRank if latency-bound; don't skip.

6. **Filter before scoring.** Narrow vector search by `repo`, `language`, `branch`, `is_test=false`, `is_generated=false` pre-similarity. Tests and generated code share identifiers with real code and drown out actual implementations.

7. **Incremental re-embedding.** Hash chunks by content; only re-embed changed symbols on commit. Don't rebuild the whole index.

8. **Staged retrieval for monorepos.** For very large repos (Qodo 10k repos), first do a coarse repo/module selector via summary embeddings, then symbol-level retrieval within selected scope.

9. **Evaluate continuously.** Separate retrieval quality (recall@k, MRR) from end-to-end generation quality. CodeRAG-Bench pattern: a good retriever can still produce chunks the LM can't use.

### Things to Avoid

- **Naive fixed char/line splits.** Breaks functions mid-body. Measured ~13% vs ~87% adaptive chunking in 2026 studies.
- **Dense-only retrieval.** Misses exact identifiers, error codes, version strings. Always add BM25 or SPLADE.
- **Indexing tests, fixtures, vendored deps, minified bundles, generated code alongside first-party source.** They pollute retrieval. Tag and filter, or keep in a separate index.
- **One giant chunk per file.** Buries the correct symbol.
- **No overlap / no parent-child linking.** Losing imports and class context hurts cross-passage reasoning. Include imports in chunk header or store `parent_id` for retrieval-time expansion.
- **Re-embedding the whole repo on every commit.** Embed by content hash per symbol.
- **Skipping the reranker.** The precision@5 loss is almost always worse than the latency savings.
- **Trusting a single eval number.** Retrieval and generation quality need separate measurement.
- **Ignoring identifier collision.** Without `path`/`module` metadata, top-k on `User`, `handler`, `utils.py` is noise.

### Code-Specific Gotchas

- High identifier reuse → need identifier-aware BM25 tokenization.
- Test files share names with prod — use `is_test` filter religiously.
- Generated code (protobuf, ORM, OpenAPI clients) is often highest-BM25 garbage — exclude or separately index.
- Keep docstrings/comments in the chunk (signal-dense).
- Language-specific tuning: Python implicit imports, Java boilerplate, JS/TS barrel re-exports all need custom tokenization/chunking rules.

## Verdict

**Default: don't put code in RAG.** Use agentic grep + LSP/symbol tools. Start with Claude Code / Cursor / Cody's built-in mechanics; add Serena MCP for structural queries; only add embedding retrieval if you measure a concrete gap.

**Escape hatch: the four conditions where code-RAG is worth it.**
1. Codebase > ~5M LoC where agent exploration can't converge — use Meta-RAG / summarization-over-code, not raw chunk embeddings.
2. Semantic/intent queries with low lexical overlap AND inconsistent naming — apply Contextual Retrieval heavily.
3. Non-agentic user-facing search UI with sub-second latency requirements.
4. Cross-language / cross-repo discovery where LSP boundaries don't reach.

**Even when code-RAG is warranted, it's a complement to symbol tools, not a replacement.** The SWE-bench Pro numbers show hybrid graph+embed (Augment 51.8%) edges pure-agentic (Claude Code 49.8%) — but a 2pp delta on the same underlying model suggests most of the engineering value is in scaffold quality, not retrieval substrate.

**For the internal-knowledge-base project specifically:** the research you've already captured (docs/tickets/Slack being the right RAG targets, Dropbox/Uber unified architectures, custom parsers + Contextual Retrieval as the winning recipe) applies directly to your non-code corpora. If you want to add code coverage, do it as a *separate* index with tree-sitter chunking + the recipe above — not by dumping repos into your existing prose-oriented pipeline.

## Open Questions

- No public per-domain breakdown of Contextual Retrieval's lift on code specifically. Anthropic bundled code with prose.
- No head-to-head public benchmark of Voyage-Code 3 vs Qwen3-Embedding-8B vs CodeRankEmbed on a fixed code task with identical chunker + reranker.
- SPLADE-Code's measured lift over BM25+dense on code at production scale — no numbers out yet.
- No independent replication of Augment's "70% agent lift" from grafting Context Engine onto Claude Code. SWE-bench Pro is ~2pp over Cursor, which is much more modest.
- No public post-mortem from a team that built code-RAG, measured it honestly, and decided to rip it out. Evidence of non-adoption is circumstantial ("they don't publish it").
- No benchmark on repos > 5M LoC where pure-agentic genuinely fails.

## Sources

### Primary evidence (papers with measurements)
- [GrepRAG: An Empirical Study and Optimization of Grep-Like Retrieval for Code Completion — arXiv 2601.23254 (Feb 2026)](https://arxiv.org/abs/2601.23254)
- [cAST: Structural Chunking via AST — arXiv 2506.15655 (EMNLP Findings 2025)](https://arxiv.org/abs/2506.15655)
- [CodeRAG-Bench — arXiv 2406.14497 (NAACL 2025)](https://arxiv.org/abs/2406.14497)
- [SPLADE-Code — arXiv 2603.22008 (March 2026)](https://huggingface.co/papers/2603.22008)
- [Anthropic Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)
- [Contextual Retrieval Appendix II](https://assets.anthropic.com/m/1632cded0a125333/original/Contextual-Retrieval-Appendix-2.pdf)
- [Meta-RAG on Large Codebases Using Code Summarization — arXiv 2508.02611](https://arxiv.org/html/2508.02611v1)
- [A-RAG: Scaling Agentic RAG via Hierarchical Retrieval Interfaces — arXiv 2602.03442](https://arxiv.org/abs/2602.03442)
- [Retrieval-Augmented Code Generation Survey — arXiv 2510.04905](https://arxiv.org/html/2510.04905v1)
- [GraphCoder: Code Context Graph retrieval — arXiv 2406.07003](https://arxiv.org/abs/2406.07003)
- [Reliable Graph-RAG for Codebases: AST-Derived — arXiv 2601.08773](https://arxiv.org/pdf/2601.08773)
- [Codebase-Memory: Tree-Sitter Knowledge Graphs via MCP — arXiv 2603.27277](https://arxiv.org/html/2603.27277v1)

### Production architecture writeups
- [Dropbox Dash — Building RAG with AI agents](https://dropbox.tech/machine-learning/building-dash-rag-multi-step-ai-agents-business-users)
- [Dropbox Dash — Context engineering](https://dropbox.tech/machine-learning/how-dash-uses-context-engineering-for-smarter-ai)
- [Uber Enhanced Agentic-RAG](https://www.uber.com/blog/enhanced-agentic-rag/)
- [Atlassian Rovo semantic search](https://www.atlassian.com/blog/atlassian-engineering/advancing-rovo-semantic-search)
- [Atlassian Rovo entity linking](https://www.atlassian.com/blog/atlassian-engineering/how-rovo-solves-search-challenges-entity-linking)
- [Glean best RAG features](https://www.glean.com/perspectives/best-rag-features-in-enterprise-search)
- [Qodo — RAG for codebase with 10k repos](https://www.qodo.ai/blog/rag-for-large-scale-code-repos/)

### Recipe references
- [Supermemory: Building code-chunk AST-aware chunking](https://supermemory.ai/blog/building-code-chunk-ast-aware-code-chunking/)
- [CocoIndex: Large codebase context with tree-sitter](https://cocoindexio.substack.com/p/index-codebase-with-tree-sitter-and)
- [Prem AI — Production RAG guide 2026](https://blog.premai.io/building-production-rag-architecture-chunking-evaluation-monitoring-2026-guide/)
- [Prem AI — Chunking strategies 2026](https://blog.premai.io/rag-chunking-strategies-the-2026-benchmark-guide/)
- [Firecrawl — Best chunking strategies for RAG 2026](https://www.firecrawl.dev/blog/best-chunking-strategies-rag)
- [StackAI — Best embedding models for RAG 2026](https://www.stackai.com/insights/best-embedding-models-for-rag-in-2026-a-comparison-guide)
- [MTEB March 2026 embedding leaderboard](https://awesomeagents.ai/leaderboards/embedding-model-leaderboard-mteb-march-2026/)
- [Modal — 6 best code embedding models compared](https://modal.com/blog/6-best-code-embedding-models-compared)
- [Markaicode — RAG metadata filtering 2026](https://markaicode.com/rag-metadata-filtering-document-tags/)

### Context / counter-narratives
- [Is RAG Dead? What AI agents use instead — MindStudio](https://www.mindstudio.ai/blog/is-rag-dead-what-ai-agents-use-instead)
- [LlamaIndex — Vector search vs filesystem 2026 (document QA, NOT code)](https://www.llamaindex.ai/blog/did-filesystem-tools-kill-vector-search)
- [Buildmvpfast — Repository Intelligence 2026](https://www.buildmvpfast.com/blog/repository-intelligence-ai-coding-codebase-understanding-2026)
