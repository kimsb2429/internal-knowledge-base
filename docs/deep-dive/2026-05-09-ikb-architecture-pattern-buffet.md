# Deep Dive: IKB Architecture Pattern Buffet

A catalog of small, composable components for internal knowledge base systems. Pick and mix — no single "right" architecture. You're already running router→specialist with hidden tools; everything below is adjacent.

---

## Executive Summary

Eight categories, ~70 named patterns. The honest pattern stack converging in 2025–2026 production:

- **Orchestration:** ReAct as default; add Reflection/Verifier when quality is the bottleneck; Supervisor/Hierarchical when work is parallelizable across independent contexts.
- **Retrieval:** Hybrid (BM25 + dense) + RRF + reranker is the floor. Layer Anthropic Contextual Retrieval or Jina Late Chunking on top for hard corpora.
- **Indexing:** Recursive chunking → Parent-document → Multi-vector. RAPTOR or document-summary index for global/synthetic queries.
- **Memory:** CoALA split (episodic/semantic/procedural) is the standard mental model; Letta/Mem0/Zep are the buy options.
- **Grounding:** Anthropic Citations API if on Claude; otherwise cite-then-answer + post-hoc verifier (MiniCheck/Lynx) + refusal-on-low-evidence.
- **Permissions:** ACL-aware indexing + identity passthrough + pre-filter at the vector DB.
- **Caching:** Embedding cache (free win) + Anthropic prompt-prefix caching + retrieval result cache. Add semantic cache cautiously (false-positive risk).
- **Eval:** Goldens + RAGAS faithfulness/context-precision + 👎 routed back into goldens.

---

## 1. Agent Orchestration Patterns

| Pattern | What it is | When to use | Real example |
|---|---|---|---|
| **Router → Specialist** | (You have it.) Router classifies and delegates to a specialist with scoped tools. | Heterogeneous query types. | Anthropic multi-agent research; LangGraph supervisor. |
| **Planner-Executor** | Planner produces a full multi-step plan upfront; executor runs each step; plan can be revised. | Long-horizon tasks where steps are knowable; cuts ReAct token bloat. | LangGraph `plan-and-execute`; ReWOO; Plan-and-Solve paper. |
| **ReAct** | Single agent loops Thought → Action → Observation. | Tool-heavy work where next step depends on the last result. | Default in LangChain agents and Anthropic tool-use. |
| **Supervisor / Orchestrator-Worker** | Lead agent decomposes, spawns workers in parallel, aggregates. | Breadth-first parallelizable work (research, multi-source synthesis). | Anthropic Research (Opus lead + Sonnet workers, >90% lift over single-agent). |
| **Hierarchical (teams of teams)** | Supervisors nested. | >5–10 workers; distinct functional domains. | LangGraph hierarchical teams. |
| **Reflection / Reflexion** | Critic reviews output; generator revises; verbal self-feedback persisted across attempts. | Quality is the bottleneck and failures repeat. | Self-Refine; Reflexion paper; Claude Code "Ultra Plan" (3 explorers + 1 critic). |
| **Generator-Verifier (Evaluator-Optimizer)** | Distinct verifier with explicit accept/reject rubric. | Verifiable acceptance criteria exist (tests pass, schema valid, score ≥ N). | Anthropic "Building Effective Agents" pattern. |
| **Swarm / Handoff** | Peer agents pass control via explicit handoffs; no central supervisor. | Conversational stage routing (triage → sales → support). | OpenAI Agents SDK `handoffs`. Note: hierarchies usually beat swarms in production. |
| **Group Chat / Debate** | Multiple agents post to a shared transcript; turn-taker picks who speaks. | Iterative refinement (code review, design critique). | AutoGen `SelectorGroupChat`; Multi-Agent Debate paper. |
| **Blackboard** | Agents read/write a shared structured workspace; controller activates next agent based on board state. | Loosely coupled specialists building a shared artifact. | Implicit in LangGraph `State`; rarely productized explicitly. |
| **Tree/Graph Search (ToT, LATS)** | Branch into candidate paths, evaluate, prune, expand. | Combinatorial solution spaces where greedy ReAct fails. | Tree of Thoughts; LATS. |

**Reusable rule of thumb:** ReAct default → add Reflexion when failures repeat → add Plan-and-Execute when planning is expensive → add Verifier when quality is verifiable → switch to Supervisor when work is parallelizable.

---

## 2. Context Isolation Between Agents

| Pattern | What it is | Problem solved |
|---|---|---|
| **Separate context windows per subagent** | Each subagent has its own system prompt and history. | Context bloat. Anthropic: subagent reads 20 files but lead context grows by "a few hundred tokens." |
| **Output summarization at boundaries** | Subagent returns distilled findings, not raw transcript. | Token noise. (Tradeoff: Cognition's "Don't Build Multi-Agents" argues this *breaks* coherence on creative tasks. Settle by isolating for read-heavy parallel work, sharing full context for write-heavy creative work.) |
| **Tool hiding (you have this)** | Each agent only sees its scoped tools. | Tool confusion past ~20–30 tools; reduces prompt-injection blast radius. |
| **Context firewalls (input/output classifiers)** | Classifier scans data crossing the boundary for injection attempts. | Indirect prompt injection. Claude Code "auto mode" runs inbound (probe tool outputs) + outbound (re-check at subagent delegation/return). |
| **Scratchpad isolation** | Per-agent working memory; shared state explicit and minimal. | Cross-agent contamination, race conditions. LangGraph `State` with channel reducers. |
| **Capability sandboxing** | Per-agent FS / shell / network permissions even if the tool is granted. | Blast-radius containment. Claude Code `permissions` model. |
| **Stateless subagents** | Subagents don't persist across calls; orchestrator owns continuity. | State drift, cross-task leakage. Anthropic's Research system. |

---

## 3. Advanced Retrieval Patterns

| Pattern | What it is | Notes |
|---|---|---|
| **Hybrid Search (BM25 + Vector)** | Sparse + dense retrievers fused with RRF. | 15–30% lift over vector-only; default starting point. |
| **Reranking** | Over-retrieve top-100, cross-encoder re-scores to top-5/10. | Anthropic: contextual retrieval + reranker drove top-20 failure 5.7% → 1.9%. Cohere Rerank, BGE, Voyage. |
| **Query Rewriting / Decomposition** | LLM cleans or splits the query. | Chat KBs with follow-ups; compound questions. LangChain `MultiQueryRetriever`. |
| **HyDE** | LLM generates a fake "ideal answer," embed *that*. | Asymmetric query/doc lengths. Skip if domain hallucinations are a risk. |
| **RAG-Fusion** | N paraphrases × retrievals, RRF. | Recall over latency. |
| **Self-RAG** | Reflection tokens (`Retrieve`, `IsRel`, `IsSup`, `IsUse`) gate retrieval and grounding. | Noisy KBs; agents that should sometimes answer parametrically. |
| **CRAG (Corrective RAG)** | Retrieval evaluator → fall back to web search / rewrite when retrieved docs are weak. | Known coverage gaps; mixed internal+public knowledge. |
| **Contextual Retrieval (Anthropic)** | Prepend each chunk with 50–100 token LLM-generated context before embedding. | -49% retrieval failures with contextual BM25; -67% with reranker. ~$1.02/M tokens with prompt caching. |
| **Step-Back Prompting** | Generate an abstract version of the question; retrieve on both. | Reasoning-heavy KBs (technical, legal). |
| **Multi-Vector Retrieval** | Multiple embeddings per chunk: parent-child, summary, hypothetical questions, ColBERT-style tokens. | Mixed query styles, mixed granularity. |

---

## 4. Indexing & Chunking Patterns

| Pattern | What it improves | Library |
|---|---|---|
| **Fixed-size** | Simplicity / predictable cost. Baseline. | Any. |
| **Recursive chunking** | Coherence; respects natural boundaries. **Default first choice.** | LangChain `RecursiveCharacterTextSplitter` at ~512 tokens, 15% overlap. |
| **Semantic chunking** | Topic boundaries via embedding distance. | LlamaIndex `SemanticSplitterNodeParser`. (Often produces tiny fragments — benchmark before adopting.) |
| **Parent-document (small-to-big)** | Match small, return big. | LangChain `ParentDocumentRetriever`; LlamaIndex `AutoMergingRetriever`. |
| **Hierarchical / RAPTOR** | Tree of summaries → multi-hop and global queries. | RAPTOR (Sarthi et al. 2024). |
| **Sentence-window** | Index sentences; return ±K sentences. | LlamaIndex `SentenceWindowNodeParser`. |
| **Late chunking (Jina)** | Embed full doc first, mean-pool to chunks; resolves coreference. Cheaper than contextual retrieval. | Jina `jina-embeddings-v3`. |
| **Proposition-based (Dense X)** | LLM decomposes to atomic facts; index propositions, return passage. | LlamaIndex `DenseXRetrievalPack`. |
| **Document summary index** | Per-doc summary for two-stage routing. | LlamaIndex `DocumentSummaryIndex`. |
| **Multi-vector per chunk** | Multiple embeddings per chunk (raw + summary + hypothetical Qs). | LangChain `MultiVectorRetriever`. |
| **Contextual chunk headers (Anthropic)** | LLM-generated 1–2 sentence context prepended pre-embed. | Anthropic cookbook. Pairs with prompt caching to keep cost low. |

---

## 5. Memory & State Patterns

| Pattern | What it is |
|---|---|
| **Short-term / working memory** | Thread-scoped scratchpad. LangGraph `State` + checkpointer. |
| **Long-term memory** | Cross-thread, namespaced. LangGraph `Store`. |
| **CoALA split: episodic / semantic / procedural** | Past interactions / decontextualized facts / learned behaviors. The standard mental model. |
| **MemGPT / Letta virtual memory** | OS-paging metaphor: core (RAM) + recall (history) + archival (vector store), self-managed via tool calls. |
| **Summary buffer** | Last N raw + rolling summary of older. LangChain `ConversationSummaryBufferMemory`. |
| **Vector-stored conversation memory** | Embed every message, top-K retrieve. Mem0's substrate. |
| **Entity memory** | Per-noun records that update over time. LangGraph / CrewAI entity memory. |
| **Knowledge graph memory** | (subject, predicate, object) for multi-hop reasoning. Cognee, Mem0-Graph. |
| **Temporal KG (Zep / Graphiti)** | Edges have validity intervals; query "as-of" date X. |
| **Layered memory-as-a-service** | Letta / Mem0 / Zep — separate memory subsystem with SDK. |
| **Fact extraction pipeline** | Async post-turn LLM extracts atomic facts → ADD/UPDATE/DELETE against memory store. Mem0's two-phase pattern. |
| **Write-on-significance** | Only persist turns above a significance threshold (preference change, new entity, contradicted prior). |
| **Dual-layer (hot path / cold path)** | Recent + summary always in context; vector/graph store queried on demand; memory node updates both. Emerging 2026 standard. |

---

## 6. Citation & Grounding Patterns

| Pattern | What it is |
|---|---|
| **Anthropic Citations API** | Native `cited_text` + char/page offsets. Endex went from 10% → 0% source hallucinations. |
| **Perplexity-style inline `[1][2]`** | Numbered footnotes; easy on any LLM; no span-level guarantee. |
| **Span-level attribution** | Sentence/claim → exact source span. VeriCite (SIGIR-AP 2025); REFIND. |
| **Post-hoc verifier (faithfulness check)** | Separate model scores entailment; flag/regen/strip if unsupported. MiniCheck, Lynx, Granite-Guardian, RAGAS faithfulness. |
| **Grounded / constrained decoding** | Logit biasing or copy heads constrained to retrieved tokens. CAD, DoLa. |
| **"Answer only from context" prompt** | Cheapest baseline. Standard in OpenAI/LangChain templates. |
| **Cite-then-answer** | Pick evidence first, answer conditioned on it. Higher faithfulness, less fluent. Self-RAG style. |
| **Answer-then-cite** | Write answer, attach citations after. Fluent, citations can be confabulated. |
| **RARR** | Post-hoc loop: decompose → search per claim → entailment check → minimal edit. Adds attribution to *any* generator. |
| **Self-consistency / SelfCheckGPT** | Sample N answers; low cross-sample agreement → likely hallucination. |
| **Refusal on low evidence** | Threshold retrieval/entailment score; route to "I don't know" or clarifying question. |
| **Evidence-aware reranking** | Reranker scores chunks against candidate answer (or CoT), promoting *entailing* chunks. VERA. |

---

## 7. Permission-Aware Retrieval & Caching

### Permissions

| Pattern | What it is |
|---|---|
| **ACL-aware indexing** | Principals attached as metadata at ingest; travel through embedding/index/retrieval. Glean, Azure AI Search, Databricks Mosaic. |
| **Pre-filter** | Apply ACL before ANN. Accurate, slower. Pinecone inline metadata filtering. |
| **Post-filter** | ANN first, drop unauthorized. Faster but can starve top-K. |
| **Row-level security in vector DB** | DB-engine-enforced. Supabase pgvector + RLS. |
| **User-token-based filtering** | User's OAuth/OIDC identity drives the filter. Avoids "god-mode bot user" antipattern. |
| **Identity passthrough from source systems** | Live ACL check or near-real-time sync to avoid drift. Glean's connector pattern. |
| **Tenant isolation** | Hard partitioning per tenant. Pinecone namespaces, Weaviate multi-tenancy. |
| **ABAC / ReBAC** | Attribute/relationship-based access; recommended over flat ACL/RBAC for relationship-rich permissions. |

### Caching

| Pattern | Cost / win |
|---|---|
| **Embedding cache** | `sha256(text)+model` → vector. Free win. Always add. |
| **Exact-match prompt cache** | Hash → response. <10 ms hit. |
| **Semantic cache (GPTCache, Redis Vector)** | Embedding-similarity match. 61–69% hit rate; ~97% positive accuracy. False-positive risk — invalidation is the hard part. |
| **Anthropic prompt-prefix cache** | `cache_control` on stable prefix. ~90% cost / ~85% latency reduction on long prompts. 5-min default TTL, 1-hour available. |
| **Retrieval result cache** | (query → top-K) keyed by hash. |
| **Server-side KV cache (vLLM APC, SGLang, LMCache)** | Self-hosted prefill reuse. RAG wrinkle: reordered retrieved chunks break naive prefix matching → CacheBlend / position-independent KV-fusion. |

---

## 8. Evaluation & Feedback Patterns

| Pattern | What it is |
|---|---|
| **Golden question set** | 30–50 representative queries with expected answers/contexts. Day-1 asset. |
| **RAGAS metrics** | Faithfulness, Answer Relevancy, Context Precision, Context Recall. Targets: 0.9 / 0.85 / 0.8 / labeled. |
| **LLM-as-judge** | Judge LLM scores against rubric. Calibrate against human labels — Snowflake's RAG-triad benchmark shows judge drift. |
| **TruLens RAG Triad** | Context relevance + groundedness + answer relevance with OTel tracing. |
| **Retrieval-only eval** | recall@k / MRR / nDCG / context precision. Run **first** when debugging — most failures are retrieval failures. |
| **End-to-end eval** | Faithfulness + answer relevancy on the final answer. |
| **Synthetic eval generation** | LLM generates (q, a, ctx) triples from corpus; human verifies sample. RAGAS `TestsetGenerator`. |
| **Rubric grading** | Dimensional rubric (factuality, completeness, citation quality 1–5). Interpretable for stakeholders. |
| **👎 capture and routing** | 👎 → investigation queue → categorized → high-confidence ones promoted to golden suite. |
| **Query log mining** | Cluster queries by embedding; low-confidence clusters = failure modes. Phoenix, LangSmith, Arize AX. |
| **A/B testing retrieval strategies** | Online split; beats offline eval for distribution-shift-sensitive changes. Braintrust, LangSmith experiments. |
| **CI-integrated eval (DeepEval pytest)** | Every PR runs the golden set; build fails on faithfulness drop. |
| **Eval-driven loop** | Goldens → offline RAGAS+judge → ship → capture 👎 + clusters → promote to goldens → repeat. |

---

## Open Questions

- **Single-context vs multi-agent for write-heavy work.** Anthropic (compress at boundaries) vs Cognition (share full traces) is unresolved. Default: isolate for read/research, single-context for creative.
- **Swarm vs hierarchy.** Frameworks ship swarm-first; production retrospectives prefer hierarchy. Likely task-complexity dependent.
- **Procedural memory.** Still immature — most systems implement it as editable system-prompt blocks rather than a distinct mechanism.
- **Forgetting/decay.** TTL vs importance-weighted eviction is unsettled.

---

## Sources

(Deduplicated across all eight research threads.)

### Orchestration & Multi-agent
- Anthropic — How we built our multi-agent research system: https://www.anthropic.com/engineering/multi-agent-research-system
- Anthropic — Building Effective Agents: https://www.anthropic.com/research/building-effective-agents
- Anthropic — Multi-agent coordination patterns: https://claude.com/blog/multi-agent-coordination-patterns
- Cognition — Don't Build Multi-Agents: https://cognition.ai/blog/dont-build-multi-agents
- LangChain — How and when to build multi-agent systems: https://blog.langchain.com/how-and-when-to-build-multi-agent-systems/
- ReAct vs Plan-and-Execute: https://dev.to/jamesli/react-vs-plan-and-execute-a-practical-comparison-of-llm-agent-patterns-4gh9
- Plan-and-Execute / ReWOO / ToT / ReAct overview: https://www.wollenlabs.com/blog-posts/navigating-modern-llm-agent-architectures-multi-agents-plan-and-execute-rewoo-tree-of-thoughts-and-react

### Context Isolation
- Claude Code auto mode (Anthropic): https://www.anthropic.com/engineering/claude-code-auto-mode
- Claude Code custom subagents: https://code.claude.com/docs/en/sub-agents
- Securely deploying AI agents: https://platform.claude.com/docs/en/agent-sdk/secure-deployment
- LangChain multi-agent docs: https://docs.langchain.com/oss/python/langchain/multi-agent

### Retrieval
- Anthropic — Introducing Contextual Retrieval: https://www.anthropic.com/news/contextual-retrieval
- Anthropic Contextual Embeddings cookbook: https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide
- Self-Reflective RAG with LangGraph (Self-RAG, CRAG): https://blog.langchain.com/agentic-rag-with-langgraph/
- Hybrid Search & Reranking: https://superlinked.com/vectorhub/articles/optimizing-rag-with-hybrid-search-reranking
- HyDE (Haystack): https://docs.haystack.deepset.ai/docs/hypothetical-document-embeddings-hyde

### Indexing & Chunking
- Late Chunking paper (arXiv 2409.04701): https://arxiv.org/pdf/2409.04701
- Late Chunking (Jina blog): https://jina.ai/news/late-chunking-in-long-context-embedding-models/
- Dense X Retrieval (arXiv 2312.06648): https://arxiv.org/abs/2312.06648
- Chunking strategies (Weaviate): https://weaviate.io/blog/chunking-strategies-for-rag
- Best chunking strategies 2026 (Firecrawl): https://www.firecrawl.dev/blog/best-chunking-strategies-rag

### Memory
- State of AI Agent Memory 2026 (Mem0): https://mem0.ai/blog/state-of-ai-agent-memory-2026
- Memory systems comparison (n1n.ai): https://explore.n1n.ai/blog/ai-agent-memory-comparison-2026-mem0-zep-letta-cognee-2026-04-23
- LangGraph Memory: https://docs.langchain.com/oss/python/langgraph/memory
- Mem0 paper (arXiv 2504.19413): https://arxiv.org/html/2504.19413v1
- Memory systems for AI agents (Steve Kinney): https://stevekinney.com/writing/agent-memory-systems

### Citation & Grounding
- Anthropic Citations API: https://platform.claude.com/docs/en/build-with-claude/citations
- RARR (arXiv 2210.08726): https://arxiv.org/abs/2210.08726
- VeriCite (arXiv 2510.11394): https://arxiv.org/html/2510.11394v1
- VERA (arXiv 2409.15364): https://arxiv.org/html/2409.15364
- Hallucination mitigation survey (arXiv 2510.24476): https://arxiv.org/html/2510.24476v1

### Permissions & Caching
- Supabase RAG with Permissions: https://supabase.com/docs/guides/ai/rag-with-permissions
- Glean permissions-aware AI: https://www.glean.com/perspectives/security-permissions-aware-ai
- Databricks Mosaic ACL/metadata filtering: https://community.databricks.com/t5/technical-blog/mastering-rag-chatbot-security-acl-and-metadata-filtering-with/ba-p/101946
- Pinecone RAG with Access Control: https://www.pinecone.io/learn/rag-access-control/
- Azure AI Search Query-Time ACL/RBAC: https://learn.microsoft.com/en-us/azure/search/search-query-access-control-rbac-enforcement
- Permission-Aware RAG (IEEE): https://ieeexplore.ieee.org/document/11224764/
- vLLM Automatic Prefix Caching: https://docs.vllm.ai/en/stable/design/prefix_caching/
- LMCache: https://github.com/LMCache/LMCache

### Evaluation
- RAGAS metrics: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/
- RAGAS faithfulness: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/
- LLM-as-judge guide (Evidently): https://www.evidentlyai.com/llm-guide/llm-as-a-judge
- Snowflake — Benchmarking LLM-as-Judge: https://www.snowflake.com/en/engineering-blog/benchmarking-LLM-as-a-judge-RAG-triad-metrics/
- Arize Phoenix — Evaluate RAG: https://arize.com/docs/phoenix/cookbook/evaluation/evaluate-rag
- 7 Failure Points in RAG (Unite.AI): https://www.unite.ai/how-to-build-reliable-rag-a-deep-dive-into-7-failure-points-and-evaluation-frameworks/
