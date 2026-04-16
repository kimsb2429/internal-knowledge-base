# Deep Dive: Adjudicating the Docs-vs-Code RAG Tension

**Date:** 2026-04-16
**Context:** Resolves a tension between two claims in the same codebase before ship-cut v1 commits to README scaling-table language.

---

## Executive Summary

**Verdict: Claim A is right for text-like content (docs, wikis, tickets, chat, email). Claim B is right for source code specifically. The tension resolves cleanly if you stop treating "source type" as a single axis.** The "unified pgvector + source-type-column" pattern scales across **document-class sources** — which is what every production unified-index system actually contains. Source code is a separate retrieval class that needs its own pipeline, even when it lives in the same database (separate chunker, separate embedder, separate hybrid strategy). Semi-structured sources split along a spectrum: OpenAPI and Jupyter notebooks need their own patterns; YAML/JSON configs default to docs-like but degrade on exact-value queries; `.tf` / `.sql` files in a repo = code-like.

**This is consistent with what every vendor with commercial incentive to unify has actually shipped.** Glean splits code from general search internally. Sourcegraph *tried* unified embeddings at launch and retreated. GitHub keeps Blackbird (trigram index) architecturally separate from Copilot retrieval. Notion AI and Atlassian Rovo claim unified code indexing, but neither has published retrieval-quality numbers on code-specific queries.

**For the ship-cut README, the scaling-table language needs one sentence of caveat, not a redesign.** The 8-dimension table is correct for document corpora. Source code is a specialized retrieval class that uses the same MCP surface and the same Postgres, but a different pipeline behind it.

---

## The Precise Boundary

| Claim | Applies to | Does not apply to |
|---|---|---|
| **A** (unified pgvector + source-type columns scales to new sources) | Docs, wikis, tickets, chat logs, email, structured prose, meeting transcripts, policy manuals, KB articles | Source code, heavily structured formats where exact-value retrieval dominates |
| **B** (code is fundamentally different, grep+LSP often beats RAG) | Source code (`.py`/`.ts`/`.java`/`.go` etc), user-authored IaC (`.tf`), SQL DDL in repos | Docs about code, runbooks, engineering wikis, PR descriptions |

**The axis isn't "text vs code." It's "text-like vs identifier-structural."** Text-like content — even technical text, even content about code — has prose semantics where dense embeddings work well. Identifier-structural content (where the unique names, call graphs, and exact substrings *are* the content) needs code-specific tokenization, AST-aware chunking, and often a graph layer.

---

## Evidence Supporting the Verdict

### 1. Production multi-source systems reveal the real boundary

**Vendors split three ways on whether source code belongs in the same index as docs:**

- **Glean (the cleanest architectural answer):** maintains *separate* dedicated lexical + semantic indexes for code, distinct from document indexes. Even though both live inside Glean's platform, general Glean Search matches code only on PR descriptions and file names — not code file contents. Code contents are reachable via a distinct "Code Search" feature and a separate MCP surface ("MCP for Engineering"). *Same company, same database layer, two retrieval paths.* (Glean Code Search docs, engineering.fb.com "Indexing code at scale with Glean")

- **Dropbox Dash:** GitHub connector indexes "repository content" but no engineering blog confirms source files are chunked/embedded for semantic code search the way docs are. Ambiguous; closer to metadata + PR/release text than full code intelligence.

- **Spotify AiKA:** explicitly does NOT ingest source code. Backstage Search collators index TechDocs, Confluence, catalog entities, Slack — no repo contents. Spotify uses separate code-search tooling.

- **Atlassian Rovo:** indexes Bitbucket code into Teamwork Graph. Announced "Rovo Chat will index your entire codebase" in Sep 2025. *Does claim unified indexing.* However: no published retrieval-quality numbers on code-specific queries. The claim precedes public evaluation.

- **Notion AI:** indexes "all code files" via GitHub connector. Same caveat as Rovo — marketing claim, no published retrieval quality.

**Revealed preference is heavily split.** The vendors with the most mature retrieval stacks (Glean, Sourcegraph) separate code. The vendors marketing the strongest unification (Rovo, Notion) are the youngest in that feature and haven't published numbers. That's informative.

### 2. Code-intelligence vendors all argue code needs specialized retrieval

Every code-intel vendor has commercial incentive to say "unify your retrieval, simplifies everything." **Zero of them actually argue that:**

- **Sourcegraph** shipped embeddings at Cody launch, then **removed them** for Cody Enterprise. Their stated reason: embeddings didn't scale across repos, and Sourcegraph Search (their existing graph + trigram system) gave "equal or better quality retrieval" at multi-repo scale with less operational cost. (Sourcegraph "How Cody understands your codebase", Cody FAQs)

- **GitHub Blackbird (Code Search)** is a custom Rust-based trigram inverted index, not a vector store. Stated reasons: code search needs exact substring, regex, ignoring-punctuation, no-stemming — all wrong for standard text tokenization. GitHub maintains Blackbird *separately from* the retrieval Copilot uses. Two retrieval systems inside one company is strong revealed-preference evidence that unification didn't work. (github.blog "The technology behind GitHub's new code search")

- **Cursor** uses vector embeddings, but with **AST-aware chunking** (tree-sitter, function/class-level). Explicitly: "Simple approaches that split code by characters, words, or lines often miss semantic boundaries—resulting in degraded embedding quality." Cursor is the softest vendor stance, but even Cursor rejects "throw code into a general pgvector index chunked like prose." (cursor.com "Securely indexing large codebases")

- **Augment Code** rejects chunk-level RAG for code entirely. Their "Context Engine" maps dependencies via static analysis, not chunk-level similarity. (augmentcode.com "Context Engine vs RAG")

### 3. Technical failure modes of code in text-optimized pipelines are quantified

**Code-specific embeddings beat general text embeddings on code by ~13–17%:**
- Voyage `voyage-code-3` beats OpenAI `text-embedding-3-large` by **+13.8% avg** across 32 code retrieval benchmarks (Voyage AI, Dec 2024)
- Jina-code-v2 beats BGE-base by **+6.6 NDCG@10** on CodeRAG-Bench
- CodeRankEmbed scores **77.9 MRR** on CodeSearchNet

**"Identifier imprecision" is a named failure mode:** queries specifying exact APIs (e.g., `UserRepository.findById`) retrieve semantically similar but incorrect classes, because dense embeddings generalize across lexically-similar identifiers. Standard production mitigation is hybrid lexical+dense precisely because dense alone can't anchor on rare identifiers. (arXiv 2512.12117 "Citation-Grounded Code Comprehension")

**Cross-reference resolution quantified:** DraCo (dataflow-guided retrieval, ACL 2024) reports **+3.43% absolute EM improvement** over RepoCoder (text-similarity dense) by adding data-flow graphs. RepoGraph and AlignCoder extend this. Text embeddings literally cannot encode "function A calls function B defined in file X" — the structural fact has no representation in vector space.

**AST chunking is practitioner consensus** (LanceDB, Sourcegraph, supermemory.ai, Cursor, cAST paper). Naive prose chunking degrades code retrieval quality.

### 4. Benchmarks: the winner is task-type-dependent

The Feb 2026 consensus is **not** "grep always beats dense" — it's more nuanced:

- **CodeRAG-Bench (NAACL 2025):** modern dense embedders **beat BM25** on code, reversing the classic BEIR result. *But only when the dense model is code-specific* (jina-code-v2, voyage-code-2, CodeRankEmbed). General text embeddings lose to BM25 on code.

- **CodeCompass (arXiv 2602.20048):** retrieval winner is task-type-dependent:
  - G1 semantic/lexical tasks: BM25 dominates (100% ACS vs 90% vanilla)
  - G3 architectural/hidden-dependency tasks: graph navigation wins by **+20 ACS points** over BM25
  - Neither dominates globally

- **HERB benchmark (Salesforce AI Research):** best agentic system on heterogeneous retrieval (docs + code + issues + logs) scores only **32.96/100 average**. Best non-agentic baseline (hybrid dense+sparse) scores 20.61. **Heterogeneous retrieval over mixed source types is an unsolved problem.** Retriever is the bottleneck, not the generator.

- **SWE-Bench retrieval:** at 27K token budget, BM25 retrieves a superset of oracle files in only ~40% of instances and retrieves *zero* oracle files in nearly 50% of instances. Localization is a major bottleneck for agent systems.

### 5. GrepRAG and cAST — real papers, narrower claims than the repo doc stated

Both papers referenced in `2026-04-16-code-ingestion-into-rag.md` exist, but they make narrower claims than the repo doc implies:

- **GrepRAG (arXiv 2601.23254, Jan 2026):** CONFIRMED the paper exists. Headline: 42.29% EM on CrossCodeEval Python (vs 36.59% for best baseline RLCoder, 27.50% RepoFuse). **Important caveat:** the only graph baseline compared is GraphCoder, which *already loses to plain BM25* (19.44% vs 24.99%). The paper does NOT compare against RepoGraph, DraCo, or CoCoMIC. "GrepRAG beats graph" = "GrepRAG beats one weak graph baseline." Additionally, "GrepRAG" is not naive grep — it's grep + identifier-weighted re-ranking + structure-aware deduplication.

- **cAST (arXiv 2506.15655):** CONFIRMED. +1.8 to +4.3 Recall@5 on RepoEval, +2.3–2.7 Pass@1 on SWE-Bench. **Important caveat:** the comparator is fixed-size line-based chunking only. No ablation against tree-sitter-without-cAST's-merge-logic. Anyone already using tree-sitter likely captures most of the gain.

**Both papers are ~10 weeks old; no published replications or critiques yet.** Their direction is consistent with the broader 2026 picture, but the specific strength of their claims relative to stronger baselines is unverified.

### 6. The four/five escape-hatch conditions for code-RAG — validated with refinements

The repo doc's four conditions map cleanly to practitioner consensus (Jason Liu/Augment, Morph, MindStudio, LlamaIndex 2026 benchmarks, nuss-and-bolts):

1. **"Don't know the name" / terminology mismatch** — user asks "retry logic" but code calls it `backoff_handler`. LSP can't jump to a symbol you can't name. **Validated.**
2. **Cross-repo scale where LSP's index is prohibitive** — enterprise monorepos, Sourcegraph's scale argument. **Validated.**
3. **Natural-language intent queries** — embedding retrieval spans the lexical gap between NL and code. CodeRAG-Bench shows jina-code-v2 beats BM25 by +7.4 NDCG@10 on NL→code. **Validated.**
4. **Architectural / transitive-dependency queries** — graph wins +20 ACS per CodeCompass. **Validated with stronger evidence than the repo doc cites.**
5. **(New) Non-code artifacts alongside code** — ADRs, design docs, commit messages, inline rationale. Grep handles the code side but misses the "why" context. **Worth adding to the list.**
6. **(New) Latency-bound single-shot RAG** — embeddings front-load the work; grep requires the model to iterate, which costs tokens and turns. **Worth adding for consulting conversations with latency-sensitive buyers.**

### 7. Semi-structured sources are a real third class — no unified answer

Per Glean's architecture and the limited research:

| Source | Pattern | Evidence |
|---|---|---|
| OpenAPI / Swagger | **Own pattern**: operation-level chunks, embed summaries (not raw JSON), or convert to tool defs | arXiv 2411.19804 + Qdrant writeup. Strong. |
| Jupyter notebooks | **Own pattern**: cell-aware hybrid chunking (markdown + code cells preserved) | Practitioner consensus. Strong. |
| Terraform/HCL | **Split**: registry docs = docs-like; user `.tf` = code-like | arXiv 2512.14792, 2509.05303. Medium. |
| SQL schemas | Code-like if in repo, docs-like if exported. No direct evidence. | Gap. |
| JSON/YAML configs | Docs-like by default; exact-value queries ("what port") degrade. | Weak (inferred). |
| K8s manifests | Docs-like in practice; no specialized tooling surfaced. | Weak. |

**The one unmet need:** exact-value retrieval across configs — "what image tag does service X use" — is not addressed by either docs-RAG or code-RAG. This is a real product gap in 2026 enterprise RAG.

---

## Is This a Category Error?

**Yes, partially.** Claim A's authors (the README scaling table, this repo's prior research) implicitly meant "text-like document source types" when they said "source type." The phrase "documents, wikis, tickets" in the table telegraphs the assumption, but the words don't. A reviewer on Show HN / Reddit who reads "scales to arbitrary source types" and thinks "what about source code" is reading the text literally — and the text is too permissive as written.

**The resolution is a one-sentence caveat**, not a rewrite. The architecture pattern (Postgres + pgvector + source-type columns + unified MCP tool surface) genuinely does scale across source types — at the *database* level. What doesn't transfer is the *retrieval pipeline behind the MCP tool*. Docs-RAG and code-RAG are two pipelines that terminate in two MCP tools on the same server. The database schema supports both; the chunkers, embedders, rerankers, and hybrid strategies differ.

**This is actually the point of MCP.** The consuming LLM sees `search_docs(query)` and `search_code(query)` as two affordances and picks the right one per question. The MCP server hides the pipeline differences behind a clean surface. That's the correct architecture; the README just needs language that reflects it.

---

## Ship-Cut Implications

### Proposed README change (scaling-table section)

**Current language (implicit universal scaling claim):**
> *"Same schema, same MCP endpoint, no rewrite."*

**Proposed language (honest about the boundary):**
> *"Same schema and same MCP endpoint scale across text-like document sources: wikis, tickets, chat, meeting transcripts, policy manuals. Source code and heavily-structured content (Terraform, OpenAPI, Jupyter notebooks, SQL schemas) are a separate retrieval class — different chunker, different embedder, different hybrid strategy — even when they live in the same Postgres. The MCP surface exposes both as parallel tools (`search_docs`, `search_code`) so the consuming LLM picks. See [Docs vs. code RAG boundary — 2026-04-16 deep dive] for the specific evidence behind this split."*

### New post-launch spoke worth drafting

> **"Where the unified RAG pattern stops working: the docs-vs-code retrieval boundary"** — Medium + HN Show HN. Counter-consensus framing ("public RAG demos pretend one pipeline handles everything; here's where that breaks and what to do instead"). Cites: Glean's internal code/docs split, Sourcegraph's retreat from embeddings, GitHub Blackbird's separate trigram index, GrepRAG's narrow-baseline caveat, CodeCompass's task-type dependency. **High-signal spoke because the audience (enterprise buyers evaluating RAG) has this exact question.**

### V1 MCP architecture — no changes needed

The current FastMCP server (`scripts/mcp_server.py`) correctly exposes `query` as a docs-RAG tool. If code-RAG were ever added (per the 2026-04-16 blueprint, FedRAMP-constrained Sonnet 4.5 deployment), it would add **`search_code` and `trace_impact` as additional `@mcp.tool` decorators on the same server** — same FastMCP, same Postgres, same `auth_context` seam, same Langfuse instrumentation. The database schema already supports this via source-type-specific nullable columns (already in `init_schema.sql`). **Zero architectural change required to accommodate the code-RAG extension.**

What changes only if code-RAG gets built:
- Additional tables: `code_chunks`, `scip_symbols`, `scip_occurrences` (all source-type-keyed, per the plan doc's existing Loop D guidance)
- Additional MCP tools: `search_code`, `find_callers`, `trace_impact`
- Separate golden set + separate eval gate for the code-RAG tool

The v1 MCP server's "Tools + Resources + Prompts" architecture handles the extension cleanly without refactoring.

### V1 README message stays strong

The demo's **docs-RAG scaffolding** is genuinely what every production unified-search system contains. Claim A is right for that scope. The extension to code is a **documented future work / consulting-engagement scope**, not a v1 gap. Saying "this demo is docs-RAG; the architecture supports code as a parallel tool when warranted; here's where the boundary is" is **stronger** than the current open-ended scaling claim, because it shows the author has thought about the boundary.

---

## Open Questions

1. **Exact-value retrieval across configs** is an unmet 2026 need. Could be a future consulting angle or demo extension — especially for IaC-heavy enterprises.
2. **mxbai-embed-large on code specifically** has no published benchmark. The repo doesn't currently index code, so this is hypothetical — but if code-RAG is ever added, the embedder choice needs eval (likely swap to voyage-code-3 or jina-code-v2).
3. **GrepRAG and cAST replications** will be worth tracking over the next 3–6 months; their current baseline sets are thin.
4. **Atlassian Rovo's "entire codebase indexing" claim** has not published retrieval-quality numbers on code-specific queries. Worth revisiting when it does.

---

## Sources

### Production systems
- [Indexing code at scale with Glean — Meta Engineering](https://engineering.fb.com/2024/12/19/developer-tools/glean-open-source-code-indexing/)
- [Glean Code Search help](https://docs.glean.com/user-guide/assistant/code-search)
- [Glean MCP for Engineering](https://docs.glean.com/user-guide/mcp/engineering)
- [Is MCP + federated search killing the index? — Glean](https://www.glean.com/blog/federated-indexed-enterprise-ai)
- [Dropbox Dash GitHub connector guide](https://help.dropbox.com/integrations/connect-github-to-dash)
- [AiKA announcement — Backstage by Spotify](https://backstage.spotify.com/discover/blog/aika-data-plugins-coming-to-portal)
- [Atlassian: Rovo Chat in Bitbucket beta](https://www.atlassian.com/blog/bitbucket/rovo-chat-bitbucket-beta)
- [Notion AI GitHub connector help](https://www.notion.com/help/notion-ai-connector-for-github)

### Code-intelligence vendors
- [How Cody understands your codebase — Sourcegraph](https://sourcegraph.com/blog/how-cody-understands-your-codebase)
- [Lessons from Building AI Coding Assistants — Sourcegraph](https://sourcegraph.com/blog/lessons-from-building-ai-coding-assistants-context-retrieval-and-evaluation)
- [The technology behind GitHub's new code search](https://github.blog/engineering/architecture-optimization/the-technology-behind-githubs-new-code-search/)
- [Securely indexing large codebases — Cursor](https://cursor.com/blog/secure-codebase-indexing)
- [Context Engine vs. RAG — Augment Code](https://www.augmentcode.com/guides/context-engine-vs-rag-5-technical-showdowns-for-code-ai)

### Technical failure modes
- [Voyage AI: voyage-code-3 announcement](https://blog.voyageai.com/2024/12/04/voyage-code-3/)
- [Voyage AI: Evaluating vector-based code retrieval](https://blog.voyageai.com/2024/12/04/code-retrieval-eval/)
- [Citation-Grounded Code Comprehension — arXiv 2512.12117](https://arxiv.org/html/2512.12117v1)
- [DraCo (Dataflow-Guided Retrieval, ACL 2024) — arXiv 2405.19782](https://arxiv.org/html/2405.19782)
- [RepoGraph — arXiv 2410.14684](https://arxiv.org/html/2410.14684v1)
- [AlignCoder — arXiv 2601.19697](https://arxiv.org/html/2601.19697)
- [LanceDB — Building RAG on codebases Part 1](https://www.lancedb.com/blog/building-rag-on-codebases-part-1)
- [supermemory.ai — AST Aware Code Chunking](https://supermemory.ai/blog/building-code-chunk-ast-aware-code-chunking/)

### Benchmarks
- [HERB — arXiv 2506.23139](https://arxiv.org/abs/2506.23139)
- [CodeRAG-Bench — arXiv 2406.14497](https://arxiv.org/html/2406.14497v2)
- [CodeCompass — arXiv 2602.20048](https://arxiv.org/html/2602.20048v1)
- [CrossCodeEval — arXiv 2310.11248](https://arxiv.org/abs/2310.11248)
- [RepoCoder / RepoEval — arXiv 2303.12570](https://arxiv.org/abs/2303.12570)
- [SWE-Bench — arXiv 2310.06770](https://arxiv.org/pdf/2310.06770)

### GrepRAG + cAST stress-test
- [GrepRAG — arXiv 2601.23254](https://arxiv.org/abs/2601.23254)
- [cAST — arXiv 2506.15655](https://arxiv.org/abs/2506.15655)
- [Why Grep Beat Embeddings in Our SWE-Bench Agent — Jason Liu](https://jxnl.co/writing/2025/09/11/why-grep-beat-embeddings-in-our-swe-bench-agent-lessons-from-augment/)
- [Did Filesystem Tools Kill Vector Search — LlamaIndex](https://www.llamaindex.ai/blog/did-filesystem-tools-kill-vector-search)
- [On the Lost Nuance of Grep vs. Semantic Search](https://www.nuss-and-bolts.com/p/on-the-lost-nuance-of-grep-vs-semantic)

### Semi-structured sources
- [Analyzing OpenAPI Chunking for RAG — arXiv 2411.19804](https://arxiv.org/pdf/2411.19804)
- [Building Search/RAG for an OpenAPI spec — Qdrant](https://qdrant.tech/blog/building-search-rag-open-api/)
- [IaC Generation with LLMs — arXiv 2512.14792](https://arxiv.org/html/2512.14792)
- [Multi-IaC-Eval — arXiv 2509.05303](https://arxiv.org/pdf/2509.05303)
- [Best Chunking Strategies for RAG in 2025 — Firecrawl](https://www.firecrawl.dev/blog/best-chunking-strategies-rag)
