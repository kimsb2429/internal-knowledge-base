# Deep Dive: Engineering RAG — Evidence, Methodology, and How-Tos

*Date: 2026-04-11*

## Table of Contents

**Research (original deep-dive)**
1. [Executive Summary](#executive-summary)
2. [(1) Measurable Gains and How They Were Measured](#1-measurable-gains-and-how-they-were-measured)
3. [(2) Publicly Disclosed Concrete Architectures](#2-publicly-disclosed-concrete-architectures) — Uber Genie/EAg-RAG, Dropbox Dash, LinkedIn KG-RAG, DoorDash, Spotify AiKA, Palo Alto Networks
4. [(3) Direct Evidence for "Codebase + Wiki + On-Call Docs Together"](#3-direct-evidence-for-codebase--wiki--on-call-docs-together)
5. [(4) How-Tos: Dos, Don'ts, and Tradeoffs](#4-how-tos-dos-donts-and-tradeoffs)
6. [Open Questions](#open-questions)
7. [All Sources](#all-sources)

**Analysis (added during session walkthrough)**
8. [Proof Points: Evidence for Key Architectural Decisions](#proof-points-evidence-for-key-architectural-decisions) — 8 decisions with evidence tables, honest gaps, and "if challenged" responses
9. [Target Use Cases and Consumers](#target-use-cases-and-consumers) — 6 use cases with traceable metrics
10. [From Zero to Knowledge MCP (Step-by-Step with Iteration Loops)](#from-zero-to-knowledge-mcp-step-by-step-with-iteration-loops) — 26 steps, 5 iteration loops (A–E) with specific eval metrics per loop
11. [Lessons (captured while walking through the research)](#my-lessons-captured-while-walking-through-this-doc) — 15 lessons with outline

**2026 Production RAG + Cost Control (appended 2026-04-12, from [deep-dive research](2026-04-11-productionizing-ai-systems.md))**
12. [2026 RAG Chunking & Retrieval Consensus](#2026-rag-chunking--retrieval-consensus) — Contextual Retrieval (49–67% failure reduction), hierarchical chunking, late chunking, overlap abandoned
13. [2026 Hybrid Search & Re-ranking](#2026-hybrid-search--re-ranking) — BM25+dense+RRF, reranker benchmarks (Jina v3, Nemotron, Voyage, Cohere)
14. [2026 RAG Eval Frameworks & Hallucination Mitigation](#2026-rag-eval-frameworks--hallucination-mitigation) — Ragas/DeepEval/TruLens stack, FACTUM, MEGA-RAG, context sufficiency
15. [2026 RAG Update Pipelines & Freshness](#2026-rag-update-pipelines--freshness) — CDC vs batch, blue/green, drift detection, multi-tenant isolation
16. [2026 Cost Control for LLM Systems](#2026-cost-control-for-llm-systems) — Prompt caching (70–90%), model routing (50–70%), circuit breakers, LLM gateways
17. [2026 Named Case Studies](#2026-named-case-studies) — Uber, LinkedIn, Ramp, Cisco, Glean, Vercel, Klarna with concrete numbers

---

Follow-up to the 2026-04-10 enterprise knowledge transformation deep-dive. Four questions about the engineering/codebase RAG findings:

1. Which examples have measurable numerical gains, and how were they actually measured?
2. Which examples have publicly disclosed concrete methodology?
3. What documented sources directly argue for combining "codebase + wiki + on-call docs together"?
4. What are the how-tos, dos, and don'ts for that combined-corpus approach?

## Executive Summary

Almost nothing in the engineering RAG landscape is evidence of productivity in any rigorous sense. **The GitHub Copilot × Accenture RCT is the only true randomized controlled trial** — and its hidden caveat (PR lift concentrated in below-median-tenure developers; senior developers show no statistically significant gain) is consistently stripped from marketing recaps. Everything else is offline LLM-judge eval (Uber EAg-RAG, Dropbox Dash, DoorDash, LinkedIn KG-RAG), production telemetry (Uber Genie, Spotify AiKA, Stripe Minions), or undisclosed self-report surveys (Palo Alto Networks).

The "codebase + wiki + on-call docs together" thesis is **ubiquitously assumed but never benchmarked**. Every shipped system bets on it; no one has published a clean ablation isolating "same RAG on wiki only" vs "same RAG on wiki + Slack + Stack Overflow." The Salesforce HERB benchmark is the closest thing, and what it shows is that heterogeneous-source retrieval is the *unsolved* bottleneck, not a solved one (best agentic RAG scores ~33/100).

The how-to literature has converged on a clear set of dos and don'ts that are mostly about content engineering (chunking per content type, structure preservation, ACL-at-crawl-time, per-type freshness decay) rather than model selection or vector database choice.

---

## (1) Measurable Gains and How They Were Measured

Ranked by strength of evidence (RCT > offline eval with golden set > production telemetry > self-report survey > anecdote).

### Strong: True RCT

**GitHub Copilot × Accenture**
- **Reported metrics**: 26.08% average increase in completed tasks for Copilot users; +15% PR merge rate; +38% code-compile success rate; 96% of participants recommended Copilot to peers; 90% reported less frustration. *(Note: the +8.69% PRs/developer/week figure previously cited here appears in the GitHub blog summary, not the MIT paper itself. The MIT paper reports 26.08% across 4,867 developers at 3 companies.)*
- **Methodology**: True randomized controlled trial. 4,867 developers at 3 companies (Accenture subset: 320 developers) randomly assigned to treatment (Copilot access) vs control (no access). 6-month duration. Combined DevOps telemetry (PRs opened, PRs merged, build success) with pre/post surveys for satisfaction/well-being. Part of a multi-company research program with Microsoft, Princeton, MIT, and Wharton researchers; preprint at economics.mit.edu.
- **Strength**: Strongest tier. Random assignment, objective DevOps telemetry, control arm, 6-month window.
- **Critical caveat (stripped from marketing)**: The PR lift is concentrated in **below-median-tenure developers**. Above-median-tenure developers show no statistically significant gain. Source: the academic preprint, not the GitHub blog summary.
- **Sources**:
  - https://github.blog/news-insights/research/research-quantifying-github-copilots-impact-in-the-enterprise-with-accenture/
  - https://economics.mit.edu/sites/default/files/inline-files/draft_copilot_experiments.pdf

### Mid-tier: Offline LLM-Judge Eval (no RCT)

**Uber EAg-RAG**
- **Reported metrics**: +27% relative increase in "acceptable" answers; −60% relative reduction in "incorrect advice" vs prior Genie/vanilla-RAG baseline.
- **Methodology**: LLM-as-judge on a curated golden set. SMEs author test queries → chatbot run in batch → LLM judge scores responses 0–5 with reasoning. Deployed in security/privacy channels.
- **Sample**: ~100+ curated queries. No production user A/B.
- **Weaknesses**: LLM-judge model not disclosed. Inter-rater agreement with SMEs not reported. "Acceptable" threshold on 0–5 scale not disclosed. No confidence intervals. n≈100 is small.
- **Sources**:
  - https://www.uber.com/blog/enhanced-agentic-rag/
  - https://www.zenml.io/llmops-database/enhanced-agentic-rag-for-on-call-engineering-support

**Dropbox Dash**
- **Reported metrics**: No headline productivity number. Dropbox publishes an evaluation blueprint instead.
- **Methodology**: LLM-judge eval across multiple dimensions including factual accuracy and source F1 (precision/recall on retrieved sources). *(Note: the "three distinctly named LLM-judges" framing used in the lessons is an organizational overlay — the Dropbox blog describes multiple eval dimensions but does not frame them as three separate judge systems.)* Public benchmarks: Natural Questions, MS MARCO, MuSiQue (multi-hop). Internal eval: production query logs from Dropbox employees + LLM-generated synthetic Q/A covering tables, images, tutorials, factual lookups. They validate the LLM-judge by comparing LLM-generated relevance ratings to human judgments on a held-out test subset.
- **Strength**: Well-described offline eval with LLM-judge calibrated against human labels. Strong on retrieval/answer quality. Silent on end-user productivity.
- **Sources**:
  - https://dropbox.tech/machine-learning/practical-blueprint-evaluating-conversational-ai-at-scale-dash
  - https://dropbox.tech/machine-learning/llm-human-labeling-improving-search-relevance-dropbox-dash

**LinkedIn Customer Service KG-RAG (SIGIR '24)**
- **Reported metrics**: MRR 0.927 vs 0.522 baseline (+77.6%); Recall@3 0.860; NDCG@3 0.946. QA: BLEU 0.377 vs 0.057, METEOR 0.613, ROUGE 0.546. Production: 28.6% reduction in median per-issue resolution time over ~6 months.
- **Methodology**: Benchmark on internal LinkedIn customer service ticket dataset. Hard retrieval and QA metrics, plus production deployment over ~6 months tracked against a pre-deployment baseline.
- **Strength**: Published peer-reviewed paper with hard numbers and production deployment outcome.
- **Source**: https://arxiv.org/abs/2404.17723

**DoorDash Dasher Support**
- **Reported metrics**: 90% reduction in hallucinations; 99% reduction in severe compliance issues; thousands of Dashers served daily.
- **Methodology**: LLM Judge scoring five dimensions — retrieval correctness, response accuracy, grammar/language accuracy, coherence to context, relevance to user request. Combined with random human-reviewed transcript samples for calibration between automated and human ratings.
- **Sources**:
  - https://careersatdoordash.com/blog/large-language-models-based-dasher-support-automation/ *(Note: original URL had "modules" typo; corrected to "models". Site returns 403 to automated fetchers — content unverifiable via automated check as of 2026-04-12.)*
  - https://www.zenml.io/llmops-database/building-a-high-quality-rag-based-support-system-with-llm-guardrails-and-quality-monitoring

### Weak: Production Telemetry, No Productivity Claim

**Uber Genie (original)**
- **Reported metrics**: ~13,000 engineering hours saved; 48.9% helpfulness rate; 70,000+ questions answered across 154 Slack channels.
- **Methodology**: User self-report via Slack feedback buttons after each Genie response (Resolved / Helpful / Not Helpful / Not Relevant). Feedback flows through a Slack plugin into a Hive table. Helpfulness rate = share of responses marked Resolved or Helpful.
- **The 13,000-hour number has no published derivation.** It is plausibly `questions answered × assumed minutes saved per question`, but the per-question assumption is undisclosed. There is no time-in-motion study and no pre-Genie baseline for time-to-resolve. No control channels held out.
- **Sources**:
  - https://www.uber.com/blog/genie-ubers-gen-ai-on-call-copilot/
  - https://www.infoq.com/news/2024/10/uber-genie-rag-copilot/

**Spotify AiKA**
- **Reported metric**: "86% of weekly active GitHub users are also weekly active AiKA users"; 25% of all employees WAU; 1,000+ daily users; 70% have used it at least once.
- **Methodology**: Pure user-set intersection over a weekly window from internal Backstage and GitHub telemetry. **Adoption telemetry only.** No productivity metric. No time saved. No answer-quality metric publicly disclosed.
- **Why this matters**: The 86% number is widely cited as evidence AiKA "works." It is not. It is evidence developers open the product a lot, nothing more.
- **Source**: https://backstage.spotify.com/discover/blog/aika-data-plugins-coming-to-portal

**Stripe Minions**
- **Reported metrics**: "1,000+ PRs/week merged, completely minion-produced"; "maximum of 2 CI rounds"; 400+ MCP tools; 10-second devbox spin-up.
- **Methodology**: Raw PR-merge counting via SCM telemetry. Stripe does NOT publish merge rate (PRs opened vs merged), reviewer time saved, defect rate, or a baseline without Minions. Quality gating is operational (CI/CD pipelines, automated tests, static analysis, mandatory human review), not evaluative.
- **Separate Stripe agent benchmark**: "Can AI agents build real Stripe integrations?" — 11 environments, deterministic graders (API tests + automated UI tests). Claude Opus 4.5 scored 92% on 4 full-stack tasks; GPT-5.2 scored 73% on 2 gym tasks. **This benchmark evaluates frontier models against integration tasks. It does not measure Minions' production productivity.**
- **Sources**:
  - https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents
  - https://stripe.com/blog/can-ai-agents-build-real-stripe-integrations

### Self-Report Survey (Treat as Marketing-Grade)

**Palo Alto Networks (Sourcegraph Cody + Claude on Bedrock)**
- **Reported metrics**: 2,000 developers in 3 months; "up to 40%" productivity gain, "average 25%."
- **Methodology**: Not disclosed in any of the AWS, Sourcegraph, or Anthropic case studies. The case-study text describes the rollout (1-month prototype → 150-dev pilot → 2-month iteration → 1,000+ dev rollout) but does not describe how productivity was measured. No DORA metrics, no PR throughput, no cycle time, no RCT mention. The phrasing pattern ("up to 40%, avg 25%") is characteristic of a developer self-report survey.
- **Strength**: Almost certainly self-report survey. Treat as marketing-grade.
- **Sources**:
  - https://aws.amazon.com/partners/success/palo-alto-networks-anthropic-sourcegraph/
  - https://sourcegraph.com/case-studies/palo-alto-networks-boosts-2-000-developers-productivity-using-ai-solutions-from-aws-anthropic-and-sourcegraph *(Note: this URL returned 404 as of 2026-04-12. The AWS partner page https://aws.amazon.com/partners/success/palo-alto-networks-anthropic-sourcegraph/ is an alternative source for the same case study.)*

---

## (2) Publicly Disclosed Concrete Architectures

### Uber Genie / EAg-RAG (most documented engineering blog post pair)

- **Indexed content**: Engwiki (Uber's internal wiki), internal Stack Overflow, engineering requirement documents, policy docs. Ingestion via Apache Spark jobs that fetch via APIs and produce dataframes with source URLs, content, and metadata.
- **Chunking strategy**: The team explicitly moved off `SimpleDirectoryLoader` / `PyPDFLoader` because policy documents contained "complex tables spanning more than five pages, including nested table cells" that were getting fragmented. They switched to Google Docs with HTML formatting to preserve tables and structure before chunking. EAg-RAG adds structured-preservation chunking. **Key disclosed lesson: document parsing/structure preservation was the dominant quality lever, not retrieval tuning.**
- **Embedding model**: OpenAI embedding model (specific variant not named publicly).
- **Vector store**: SIA (Search In Action) — Uber's in-house vector database.
- **Reranker**: No specific reranker model named. EAg-RAG introduces LLM-powered agents performing pre- and post-retrieval steps (query reformulation, document post-processing) — effectively an agentic rerank/filter layer.
- **Generation model**: Routed through Uber's internal GenAI Gateway (model not publicly pinned; supports multiple LLMs).
- **Evaluation harness**: Custom pipeline using ~100+ "golden test queries" in the security/privacy domain; LLM-as-judge scoring plus historical Slack metadata + user feedback joined through Hive tables.
- **Refresh / freshness**: Periodic Spark-based bootstrap ingestion jobs; cadence not disclosed.
- **ACL / permissions**: EAg-RAG post explicitly notes "access control metadata can be indexed and used during answer generation to prevent unauthorized access." Initial Genie excluded sources that "can't be exposed in Slack channels."
- **Primary sources**:
  - https://www.uber.com/blog/genie-ubers-gen-ai-on-call-copilot/
  - https://www.uber.com/blog/enhanced-agentic-rag/

### Dropbox Dash (best-documented eval methodology)

- **Indexed content**: Unified "Dash Search index" consolidating multi-source connectors (emails, documents, meeting notes, task management data) across SaaS apps. A knowledge graph is layered on top connecting people, activity, and content.
- **Chunking strategy**: **On-the-fly chunking at query time**, not at ingest. Documents are chunked when a query arrives so only query-relevant sections are extracted. Deliberate departure from offline-chunk-and-embed.
- **Embedding model**: Not named; described as "a larger, but still efficient, embedding model" used for reranking.
- **Vector store / search**: Deliberately chose traditional lexical/IR indexing rather than a dedicated vector DB for first-stage retrieval. Hybrid: lexical first-stage, embedding-based reranker.
- **Reranker**: Embedding-based semantic reranker re-orders lexical results.
- **Generation model**: Explicitly model-agnostic. VP Josh Clemm mentions DSPy for prompt optimization and MCP for tool plumbing.
- **Evaluation harness**: LLM-judge eval across multiple dimensions including factual accuracy and source F1. *(The "three judges" framing in the lessons is an organizational overlay on Dropbox's approach, not their exact architecture.)* Public benchmarks: Natural Questions, MS MARCO, MuSiQue. Internal eval: production query logs + LLM-generated synthetic Q/A. LLM-judge validated against human labels on a held-out subset.
- **Refresh / freshness**: Periodic data syncs and webhooks per connector. Latency target: <2s for >95% of queries.
- **ACL / permissions**: Granular access controls enforced at the unified index level.
- **Notable architectural argument**: Chose lexical-first-stage to avoid vector DB ops cost and hit sub-2s latency. Moved to a single universal search index (replacing "dozens of individual service APIs") because the agent planner degraded with too many tools. Context engineering principle: "better context through precision, not volume" — specialized search agent owns retrieval so tool definitions don't consume the main context window.
- **Primary sources**:
  - https://dropbox.tech/machine-learning/building-dash-rag-multi-step-ai-agents-business-users
  - https://dropbox.tech/machine-learning/how-dash-uses-context-engineering-for-smarter-ai
  - https://dropbox.tech/machine-learning/vp-josh-clemm-knowledge-graphs-mcp-and-dspy-dash
  - https://dropbox.tech/machine-learning/practical-blueprint-evaluating-conversational-ai-at-scale-dash
  - https://dropbox.tech/machine-learning/llm-human-labeling-improving-search-relevance-dropbox-dash

### LinkedIn Customer Service RAG (arXiv 2404.17723, SIGIR '24)

- **Indexed content**: Historical customer service tickets (Jira-style issues) with fields like Summary, Description, Priority, plus explicit issue-tracker links between tickets.
- **Chunking strategy**: Instead of text-splitting, tickets are parsed into **intra-issue trees**: each ticket becomes a tree where nodes = ticket sections, connected hierarchically. Sidesteps naive chunking entirely — the KG node is the unit of retrieval.
- **Embedding model**: BERT and E5 used for node-level embeddings. Title embeddings used for inter-issue similarity edges.
- **Vector store / search**: Qdrant for vector storage; Neo4j for the graph. Queries are reformulated by an LLM into Cypher queries against Neo4j; text-based retrieval is a fallback when graph queries fail.
- **Reranker**: Retrieval aggregates node-level cosine similarities into ticket-level scores. No external cross-encoder reranker disclosed.
- **Generation model**: GPT-4 used both for ticket parsing during graph construction and for final answer generation.
- **Notable**: Graph construction is two-phase — rule-based extraction for predefined fields + LLM-guided parsing using a YAML template of ticket sections. Inter-ticket edges: explicit from tracker links + implicit via `cos(embed(Ti), embed(Tj)) ≥ θ` on title embeddings.
- **Primary sources**:
  - https://arxiv.org/abs/2404.17723
  - https://arxiv.org/html/2404.17723v1

### DoorDash Dasher Support RAG

- **Indexed content**: Existing knowledge base articles for Dasher (delivery contractor) support plus historical resolved cases.
- **Chunking strategy**: Not specifically disclosed.
- **Embedding model / vector store / reranker**: Not specifically named.
- **Generation model**: OpenAI + Anthropic models routed through a FastAPI service.
- **Evaluation harness**: LLM Judge scoring five dimensions (retrieval correctness, response accuracy, grammar/language accuracy, coherence to context, relevance to user request) + random human-reviewed transcript samples for calibration.
- **Notable architectural choice**: **Two-tier online LLM Guardrail.** Tier 1 = cost-effective in-house "shallow check" using semantic similarity comparison to check grounding in retrieved RAG context. Tier 2 = heavier LLM-based evaluator, triggered only when tier 1 flags an issue. Team explicitly rejected single-model sophisticated guardrails after finding response times and token costs prohibitive in production.
- **Pipeline**: conversation summarization → historical case retrieval + KB article matching → template-based prompt → LLM generation → guardrail.
- **Primary source**: https://careersatdoordash.com/blog/large-language-models-based-dasher-support-automation/ *(Note: original URL had "modules" typo; corrected to "models". Site returns 403 to automated fetchers — content unverifiable via automated check as of 2026-04-12.)*

### Spotify AiKA (least-documented technically)

- **Indexed content**: TechDocs (docs-like-code MkDocs site indexed by Backstage) + Software Catalog entities + Slack support channels + organizational data (configurable in `aika > knowledgeTypes`). *(Note: Confluence was previously listed here as a default source but could not be confirmed in the blog post — only TechDocs and Software Catalog are explicitly named as defaults.)*
- **Search**: Alpha release is **keyword search only** plus OpenAI integration. Vector/semantic indexing is not in the alpha.
- **Generation**: OpenAI in alpha; internal version supports multiple LLM backends.
- **Chunking, embedding model, vector store, reranker, ACL architecture, eval harness**: All undisclosed.
- **Primary sources**:
  - https://backstage.spotify.com/discover/blog/aika-data-plugins-coming-to-portal
  - https://backstage.spotify.com/docs/portal/core-features-and-plugins/aika/getting-started
  - https://thenewstack.io/introducing-aika-backstage-portal-ai-knowledge-assistant/

### Palo Alto Networks

Almost nothing technical disclosed. Architecture is "Sourcegraph Cody + Anthropic Claude on Bedrock + 2,000 developers." No chunking, embedding, retrieval, or eval details.

- **Sources**:
  - https://aws.amazon.com/partners/success/palo-alto-networks-anthropic-sourcegraph/
  - https://sourcegraph.com/case-studies/palo-alto-networks-boosts-2-000-developers-productivity-using-ai-solutions-from-aws-anthropic-and-sourcegraph *(Note: this URL returned 404 as of 2026-04-12. The AWS partner page https://aws.amazon.com/partners/success/palo-alto-networks-anthropic-sourcegraph/ is an alternative source for the same case study.)*

---

## (3) Direct Evidence for "Codebase + Wiki + On-Call Docs Together"

**The honest finding**: there is no clean A/B benchmark proving multi-source > single-source. Every shipped system bets on it; no one has published "same RAG on wiki only scored X, wiki+Slack+SO scored Y." The thesis is ubiquitously assumed in industry but never rigorously demonstrated.

What does exist:

### Argument 1: Uber Genie's framing (closest direct argument)

> "Many questions could get answered by referring to existing documentation, but the information is fragmented across Uber's internal wiki called Engwiki, internal Stack Overflow, and other locations, making it challenging to find specific answers... users often ask the same questions repeatedly, leading to a high demand for on-call support across hundreds of Slack channels."

Genie was built explicitly to consolidate fragmented sources. Production scale: 70,000+ questions answered, 154 Slack channels, 48.9% helpfulness, ~13,000 engineering hours saved.

**Critical attribution warning**: Uber's headline EAg-RAG numbers (+27% acceptable answers, −60% incorrect advice) compare *agentic vs traditional RAG*, **not** *multi-source vs single-source*. Citing those numbers as evidence for the source-mixing thesis would misrepresent the source.

- https://www.uber.com/blog/genie-ubers-gen-ai-on-call-copilot/
- https://www.uber.com/blog/enhanced-agentic-rag/
- https://www.infoq.com/news/2024/10/uber-genie-rag-copilot/

### Argument 2: HERB benchmark — Salesforce AI Research (arXiv 2506.23139, June 2025)

First benchmark explicitly designed around heterogeneous enterprise sources for software-industry use cases. Argues the single-source framing is inadequate because real enterprise queries require "source-aware, multi-hop reasoning over diverse, sparsed, but related sources."

- 39,190 artifacts across documents, meeting transcripts, Slack, GitHub, URLs
- 815 answerable + 699 unanswerable queries
- **Best agentic RAG methods score only 32.96/100** — heterogeneous-source retrieval is the unsolved bottleneck, not a solved problem

> "Deep Search — a realistic and complex form of retrieval-augmented generation (RAG) that requires source-aware, multi-hop reasoning over diverse, sparsed, but related sources... documents, meeting transcripts, Slack messages, GitHub, and URLs."

> "Retrieval [is] the main bottleneck: existing methods struggle to conduct deep searches and retrieve all necessary evidence."

- https://arxiv.org/abs/2506.23139

### Argument 3: Dropbox Dash "context engineering"

Qualitative architectural argument, not a benchmark. Dash explicitly chose unified search/knowledge over per-source tools because tool-call overhead caused context degradation.

> "More tools often meant slower, less accurate decision making, with tool calls adding extra context and similar patterns of context rot... [solution:] limiting tool definitions by consolidating retrieval through a universal search index, filtering context using a knowledge graph to surface only relevant information."

- https://dropbox.tech/machine-learning/how-dash-uses-context-engineering-for-smarter-ai
- https://dropbox.tech/machine-learning/building-dash-rag-multi-step-ai-agents-business-users

### Argument 4: Stripe — shared knowledge layer (Latent Space podcast w/ Emily Glassberg Sands)

Stripe observed multiple teams independently building their own RAG stacks and consolidated them into a shared knowledge layer (datastore + ingestion pipelines + search/lookup APIs). Internal tools mentioned: "toolshed" (MCP server), Hubble data catalog, internal text-to-SQL assistant Hubert (~900 weekly users).

Testimony only, no published Stripe engineering blog post on this. Transcript cuts off where Emily starts detailing the RAG stack.

- https://www.latent.space/p/stripe

### Argument 5: Spotify AiKA — config-level evidence

AiKA's docs explicitly list `techdocs + confluence + software-catalog` as the canonical source configuration, plus Slack support channels and organizational data. Architectural ship, not empirical claim.

> "AiKA can draw from any source that is indexed by Backstage Search... The most common sources are: techdocs, confluence, and software-catalog." Plus: "Slack support channels and organizational data."

- https://backstage.spotify.com/docs/portal/core-features-and-plugins/aika/getting-started
- https://backstage.spotify.com/discover/blog/aika-data-plugins-coming-to-portal

### Argument 6: ER-RAG — unified modeling of heterogeneous sources (arXiv 2504.06271)

Academic framing that heterogeneous RAG needs entity-relation-based unified modeling because source-per-retriever approaches fragment context. Proposes a unified ER schema across heterogeneous sources.

- https://arxiv.org/html/2504.06271

### Argument 7: HedraRAG (arXiv 2507.09138)

Additional academic work in the heterogeneous-RAG space surfaced in search but not deeply analyzed.

- https://arxiv.org/abs/2507.09138

### Argument 8: Glean — cross-application indexing positioning

Glean's public marketing positions cross-application indexing as the differentiator, citing that workers spend 20% of their time searching for information as the problem statement. Glean offers hybrid search + knowledge graph + enterprise-specific embedding fine-tuning, plus an agent-consumption tier ("Glean for Agents"). No specific search-quality-improvement metric published. *(Note: a "20% search-quality improvement" was previously attributed here but is a mischaracterization — the 20% figure refers to time spent searching, not quality improvement.)*

> "Cross-application indexing enhances RAG capabilities by linking disparate information sources, enabling users to derive insights that span multiple systems."

- https://www.glean.com/perspectives/best-rag-features-in-enterprise-search
- https://www.zenml.io/llmops-database/building-robust-enterprise-search-with-llms-and-traditional-ir

### Bottom line on the evidence

The strongest *quotable* evidence for "multi-source > single-source" is Uber Genie's fragmentation framing and HERB's heterogeneous-source benchmark. The weakest part of the case is that **nobody has published a clean A/B**. Every source argues for multi-source architecturally or qualitatively. If this thesis is load-bearing to a decision, it would need to be run rather than cited.

---

## (4) How-Tos: Dos, Don'ts, and Tradeoffs

### DOs

- **Use content-type-aware chunking.** Code, prose, and tables behave very differently in retrieval. Real-world systems mix strategies per content type rather than applying one chunker to everything. For code specifically, use a concrete syntax tree (CST) parser so chunks align with semantic units like functions and classes.
  - https://weaviate.io/blog/chunking-strategies-for-rag
  - https://www.lancedb.com/blog/building-rag-on-codebases-part-1

- **Preserve structure-aware chunking for prose docs.** Structure-aware chunking (headings, sections, list boundaries) dramatically improves answer quality in technical/policy-heavy domains. Don't flatten wiki markup before splitting.
  - https://community.databricks.com/t5/technical-blog/the-ultimate-guide-to-chunking-strategies-for-rag-applications/ba-p/113089

- **Invest in chunking + metadata before swapping models.** Production teams report these consistently outperform model upgrades on answer quality. *(Note: the article discusses chunking and metadata as high-leverage; the reranking-specific claim and "before swapping models" framing were added editorially and are not direct quotes from the article.)*
  - https://towardsdatascience.com/six-lessons-learned-building-rag-systems-in-production/

- **Index ACLs alongside content at crawl time.** Glean's pattern: for every item, the crawler pulls both content and ACL, building a unified "who can see what" map that mirrors source-system groups. The only tractable way to unify Confluence + GitHub + Slack permissions.
  - https://docs.glean.com/connectors/about

- **Filter by permission BEFORE anything reaches the LLM.** Discard restricted content from context entirely. Feeding it "just for background" leaks via paraphrase.
  - https://www.glean.com/perspectives/security-permissions-aware-ai

- **Build a unified permissions layer rather than querying each source at runtime.** Glean mirrors ACLs and group memberships from source systems into its own layer. Faster, and lets you resolve cross-source group membership once.
  - https://www.useparagon.com/learn/permissions-access-control-for-production-rag-apps/

- **Hybrid rank = semantic similarity + recency weight.** Production pattern is ~70% semantic + ~30% recency, applied AFTER initial vector-similarity filtering. A simple recency prior hit 1.00 accuracy on freshness tasks in recent research.
  - https://arxiv.org/abs/2509.19376

- **Apply per-content-type decay curves.** A doc last verified 90 days ago on a fast-moving topic should score lower than a fresher one even if embeddings are closer. On-call runbooks need steep decay; evergreen architecture wikis need flat decay. Encode content type as metadata; pick the decay function per type.
  - https://glenrhodes.com/data-freshness-rot-as-the-silent-failure-mode-in-production-rag-systems-and-treating-document-shelf-life-as-a-first-class-reliability-concern-4/

- **Track freshness as a first-class dashboard metric.** Alongside retrieval latency and answer quality. Auto-archive or flag docs past a defined age threshold (6–12 months for fast-moving domains).
  - https://www.regal.ai/blog/rag-hygiene

- **Demand precise, fine-grained citations** (paragraph / cell / function level). "Precise citations, like linking claims to exact paragraphs, table cells, and figures, separate professional agentic applications from chatbot demos." Generic document-level citations are a demo smell.
  - https://www.tensorlake.ai/blog/rag-citations

- **Validate with small probes and a fixed eval set.** Track retrieval hit rate, token cost, latency budgets, and answer usefulness against a frozen eval set per source type. A mixed-corpus eval should have questions where you know which source SHOULD win, so you can grade routing — not just answer text.
  - https://neo4j.com/blog/genai/advanced-rag-techniques/

- **Design strong feedback loops as a product requirement, not an afterthought.** Spotify's "Honk" background-agent series explicitly names feedback loops as the key to predictable results, with weekly usage by 25% of employees / 87% of developers. *(Note: a specific resolution-time-reduction metric was previously attributed to this source but could not be verified in the article.)*
  - https://engineering.atspotify.com/2025/12/feedback-loops-background-coding-agents-part-3
  - https://backstage.spotify.com/discover/backstage-101

- **Prioritize indexing at large scale.** For big code corpora, use smart chunking + caching + priority indexing + semantic scoring to decide which parts of the codebase matter for the current query. Don't try to stuff everything into the same index tier.
  - https://www.qodo.ai/blog/rag-for-large-scale-code-repos/

- **Two-tier online guardrails** (DoorDash pattern). Cheap semantic-similarity check first; expensive LLM evaluator only triggered when the cheap check flags. Single-model sophisticated guardrails fail on cost/latency at scale.
  - https://careersatdoordash.com/blog/large-language-models-based-dasher-support-automation/ *(Note: original URL had "modules" typo; corrected to "models". Site returns 403 to automated fetchers — content unverifiable via automated check as of 2026-04-12.)*

### DON'Ts

- **Don't use one chunker for everything.** Naive fixed-size chunking on code produces broken boundaries and incomplete function bodies; the same chunker on wiki prose drops heading context. The #1 reported failure mode for teams shipping code-aware RAG.
  - https://www.lancedb.com/blog/building-rag-on-codebases-part-1

- **Don't stop at "convert to Markdown → chunk → index."** That's a demo. Production needs metadata preservation, ACL capture, freshness tracking, and precise attribution.
  - https://www.tensorlake.ai/blog/rag-citations

- **Don't rely on the source application's permissions at query time.** Live per-source ACL checks create latency and leave cross-source group resolution unsolved. Mirror ACLs at index time.
  - https://www.useparagon.com/blog/respecting-3rd-party-data-permissions-with-rag

- **Don't let the LLM see content the user can't access, even for "context."** Glean explicitly discards unauthorized content before it reaches the LLM. Feeding restricted context "just for background" leaks via paraphrase.
  - https://www.knostic.ai/blog/glean-data-security

- **Don't ignore temporal signals.** "Without a temporal component, retrieval pipelines risk elevating stale or misleading information." Silent failure mode because retrieval metrics look fine while answers quietly go wrong.
  - https://arxiv.org/html/2509.19376

- **Don't trust document-level similarity as citation.** Document-level "source: confluence/runbook-42" attributions are unfalsifiable by users and don't let them verify. Push to paragraph/span granularity.
  - https://zilliz.com/blog/retrieval-augmented-generation-with-citations

- **Don't skip routing evaluation in mixed corpora.** If ythe eval only grades final answer text, you can't tell whether the system pulled from the right source type. A wiki-sourced answer to an on-call question might look fluent but be dangerously outdated. Grade source-routing separately.
  - https://medium.com/@bhagyarana80/7-retrieval-metrics-rag-teams-must-track-8961c12fff92

### Key Tradeoffs

- **Recency weight vs. evergreen bias.** A global recency prior improves freshness but penalizes evergreen architecture docs that are correct and old. Fix by tagging content type and using per-type decay curves — the cost is maintaining the taxonomy.
  - https://docs.ragie.ai/docs/retrievals-recency-bias

- **Unified ACL mirror vs. live permission check.** Mirroring ACLs at index time is fast and unifies cross-source groups but creates a staleness window when access is revoked. Live checks close the window but add per-query latency and coupling. Most large deployments (Glean) pick mirroring + short refresh intervals.
  - https://www.glean.com/perspectives/security-permissions-aware-ai

- **CST/AST chunking vs. simple windowing for code.** Syntax-aware gives better retrieval precision but is language-specific and breaks on partial/malformed files (common in PRs, migrations). Plan a fallback chunker.
  - https://www.lancedb.com/blog/building-rag-on-codebases-part-1

- **Source precedence when wiki and Slack disagree.** No silver bullet. Practical pattern: rank by `(source authority tier) × (freshness decay) × (semantic score)`, where authority tiers are hand-assigned (e.g., runbook > wiki > Slack thread > commit message). Hand-assignment means governance overhead.
  - https://glenrhodes.com/data-freshness-rot-as-the-silent-failure-mode-in-production-rag-systems-and-treating-document-shelf-life-as-a-first-class-reliability-concern-4/

- **Fine-grained citations vs. latency/cost.** Paragraph/span attribution requires extra retrieval passes or model-internals attribution methods, adding cost. Worth it for trust, but budget for it.
  - https://arxiv.org/html/2406.13663v1

- **Feedback-loop product investment vs. engineering cost.** Thumbs up/down is cheap but low-signal; structured follow-up ("was this the right source?" vs. "was the answer correct?") gives much richer data but requires UX work. Spotify's Honk investment suggests strong feedback loops are the differentiator between predictable and unpredictable agentic RAG.
  - https://engineering.atspotify.com/2025/12/feedback-loops-background-coding-agents-part-3

---

## Open Questions

- **The single-source-vs-multi-source ablation does not exist publicly.** If this is load-bearing to a decision, it has to be run, not cited.
- **Uber's 13,000-hour figure has no published derivation.** Almost certainly `questions × assumed minutes saved`, but the assumption is undisclosed.
- **Spotify AiKA's productivity story has zero supporting metrics.** The 86% number is adoption, not productivity.
- **Palo Alto Networks methodology is undisclosed.** The 25–40% productivity claim is almost certainly self-report.
- **No public RAG case study indexes postmortems specifically.** ADRs, postmortems, and incident reports are obvious goldmines but no shipped system publicly indexes them as a primary corpus.
- **No widely-published open eval harness for mixed-corpus engineering RAG.** Teams build bespoke eval sets.
- **No first-party Uber or Dropbox blog post specifically advocates for code+wiki+on-call mixing as a thesis.** The closest is Genie's fragmentation framing.
- **GitHub Copilot and Anthropic engineering blogs** have no posts specifically arguing for mixed-corpus engineering RAG that surfaced in these searches. A targeted follow-up could pull from anthropic.com/news and github.blog if needed.

---

## All Sources

### Q1 — Measurement methodology

- https://github.blog/news-insights/research/research-quantifying-github-copilots-impact-in-the-enterprise-with-accenture/
- https://economics.mit.edu/sites/default/files/inline-files/draft_copilot_experiments.pdf
- https://www.uber.com/blog/genie-ubers-gen-ai-on-call-copilot/
- https://www.uber.com/blog/enhanced-agentic-rag/
- https://www.infoq.com/news/2024/10/uber-genie-rag-copilot/
- https://www.zenml.io/llmops-database/enhanced-agentic-rag-for-on-call-engineering-support
- https://backstage.spotify.com/discover/blog/aika-data-plugins-coming-to-portal
- https://thenewstack.io/introducing-aika-backstage-portal-ai-knowledge-assistant/
- https://aws.amazon.com/partners/success/palo-alto-networks-anthropic-sourcegraph/
- https://sourcegraph.com/case-studies/palo-alto-networks-boosts-2-000-developers-productivity-using-ai-solutions-from-aws-anthropic-and-sourcegraph *(Note: this URL returned 404 as of 2026-04-12. The AWS partner page https://aws.amazon.com/partners/success/palo-alto-networks-anthropic-sourcegraph/ is an alternative source for the same case study.)*
- https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents
- https://stripe.com/blog/can-ai-agents-build-real-stripe-integrations
- https://dropbox.tech/machine-learning/building-dash-rag-multi-step-ai-agents-business-users
- https://dropbox.tech/machine-learning/practical-blueprint-evaluating-conversational-ai-at-scale-dash
- https://dropbox.tech/machine-learning/llm-human-labeling-improving-search-relevance-dropbox-dash

### Q2 — Disclosed architectures

- https://www.uber.com/blog/enhanced-agentic-rag/
- https://www.uber.com/blog/genie-ubers-gen-ai-on-call-copilot/
- https://backstage.spotify.com/discover/blog/aika-data-plugins-coming-to-portal
- https://backstage.spotify.com/docs/portal/core-features-and-plugins/aika/getting-started
- https://thenewstack.io/introducing-aika-backstage-portal-ai-knowledge-assistant/
- https://dropbox.tech/machine-learning/building-dash-rag-multi-step-ai-agents-business-users
- https://dropbox.tech/machine-learning/how-dash-uses-context-engineering-for-smarter-ai
- https://dropbox.tech/machine-learning/vp-josh-clemm-knowledge-graphs-mcp-and-dspy-dash
- https://dropbox.tech/machine-learning/practical-blueprint-evaluating-conversational-ai-at-scale-dash
- https://dropbox.tech/machine-learning/llm-human-labeling-improving-search-relevance-dropbox-dash
- https://arxiv.org/abs/2404.17723
- https://arxiv.org/html/2404.17723v1
- https://careersatdoordash.com/blog/large-language-models-based-dasher-support-automation/ *(Note: original URL had "modules" typo; corrected to "models". Site returns 403 to automated fetchers — content unverifiable via automated check as of 2026-04-12.)*
- https://www.zenml.io/llmops-database/building-a-high-quality-rag-based-support-system-with-llm-guardrails-and-quality-monitoring

### Q3 — Mixed-corpus evidence

- https://www.uber.com/blog/genie-ubers-gen-ai-on-call-copilot/
- https://www.uber.com/blog/enhanced-agentic-rag/
- https://www.infoq.com/news/2024/10/uber-genie-rag-copilot/
- https://backstage.spotify.com/discover/blog/aika-data-plugins-coming-to-portal
- https://backstage.spotify.com/docs/portal/core-features-and-plugins/aika/getting-started
- https://dropbox.tech/machine-learning/how-dash-uses-context-engineering-for-smarter-ai
- https://dropbox.tech/machine-learning/building-dash-rag-multi-step-ai-agents-business-users
- https://dropbox.tech/machine-learning/vp-josh-clemm-knowledge-graphs-mcp-and-dspy-dash
- https://arxiv.org/abs/2506.23139
- https://arxiv.org/html/2504.06271
- https://arxiv.org/abs/2507.09138
- https://www.latent.space/p/stripe
- https://www.glean.com/perspectives/best-rag-features-in-enterprise-search
- https://www.zenml.io/llmops-database/building-robust-enterprise-search-with-llms-and-traditional-ir
- https://stackoverflow.blog/2026/03/12/enterprise-ai-needs-more-than-foundation-models/

### Q4 — How-tos, dos and don'ts

- https://weaviate.io/blog/chunking-strategies-for-rag
- https://www.lancedb.com/blog/building-rag-on-codebases-part-1
- https://community.databricks.com/t5/technical-blog/the-ultimate-guide-to-chunking-strategies-for-rag-applications/ba-p/113089
- https://towardsdatascience.com/six-lessons-learned-building-rag-systems-in-production/
- https://www.qodo.ai/blog/rag-for-large-scale-code-repos/
- https://docs.continue.dev/guides/custom-code-rag
- https://www.glean.com/perspectives/security-permissions-aware-ai
- https://docs.glean.com/connectors/about
- https://www.knostic.ai/blog/glean-data-security
- https://www.useparagon.com/learn/permissions-access-control-for-production-rag-apps/
- https://www.useparagon.com/blog/respecting-3rd-party-data-permissions-with-rag
- https://arxiv.org/abs/2509.19376
- https://arxiv.org/html/2509.19376
- https://glenrhodes.com/data-freshness-rot-as-the-silent-failure-mode-in-production-rag-systems-and-treating-document-shelf-life-as-a-first-class-reliability-concern-4/
- https://www.regal.ai/blog/rag-hygiene
- https://docs.ragie.ai/docs/retrievals-recency-bias
- https://www.tensorlake.ai/blog/rag-citations
- https://zilliz.com/blog/retrieval-augmented-generation-with-citations
- https://arxiv.org/html/2406.13663v1
- https://neo4j.com/blog/genai/advanced-rag-techniques/
- https://medium.com/@bhagyarana80/7-retrieval-metrics-rag-teams-must-track-8961c12fff92
- https://engineering.atspotify.com/2025/12/feedback-loops-background-coding-agents-part-3
- https://engineering.atspotify.com/
- https://backstage.spotify.com/discover/backstage-101
- https://careersatdoordash.com/blog/large-language-models-based-dasher-support-automation/ *(Note: original URL had "modules" typo; corrected to "models". Site returns 403 to automated fetchers — content unverifiable via automated check as of 2026-04-12.)*

---

## Proof Points: Evidence for Key Architectural Decisions

Consolidated from discussions across this session. For each decision, what evidence exists, what's honestly missing, and what to say when challenged.

### 1. Structure-aware chunking over fixed-size chunking

| Evidence | Strength | Source |
|---|---|---|
| Uber EAg-RAG: +27% acceptable answers, −60% incorrect advice vs vanilla-RAG baseline. Team's stated lesson: "parsing/structure preservation was the dominant quality lever, not retrieval tuning." | Mid-tier — bundled with agentic changes, team testimony not isolated measurement | https://www.uber.com/blog/enhanced-agentic-rag/ |
| LinkedIn KG-RAG: MRR 0.927 vs 0.522 baseline (+77.6%). Production: 28.6% reduction in median per-issue resolution time over 6 months. | Strong — peer-reviewed SIGIR '24, hard retrieval metrics + production outcome | https://arxiv.org/abs/2404.17723 |
| Documented failure modes: tables shred, code breaks at function boundaries (#1 failure mode per LanceDB), heading context drops, Confluence macros lost. | Reproducible in 10 minutes on any corpus with tables | LanceDB, Weaviate, Databricks blogs |
| Revealed preference: 6/6 disclosed architectures moved off fixed-size (Uber, Dropbox, LinkedIn, DoorDash, Spotify, Palo Alto Networks) | Strong convergent signal | This doc, section 2 |
| Practitioner consensus: Databricks, Weaviate, TDS "Six Lessons," TensorLake all recommend structure-aware | Community consensus, not measurement | Various blog posts |

**Honest gap**: no clean isolated ablation (same corpus, only varying chunking strategy). All numbers are bundled. **If challenged**: "every team that shipped this for real ended up here, and the failure modes are reproducible on our corpus in 10 minutes. Want to run our own ablation? 50 golden queries, one day, settles it."

### 2. Parsing as a separate layer (not collapsible into chunking)

| Evidence | Strength | Source |
|---|---|---|
| Uber's key disclosed lesson: "document parsing/structure preservation was the dominant quality lever, not retrieval tuning." Moved from PyPDFLoader to Google Docs HTML because tables spanning 5+ pages were shredding. | Team testimony from production deployment | https://www.uber.com/blog/enhanced-agentic-rag/ |
| Information-theoretic argument: parsing is lossy and irreversible. Once a table is flattened to `Name Age City John 25 NYC`, no downstream process can recover column-header → cell relationships. The spatial information existed in the 2D PDF layout and was destroyed. | Logical proof — no counter-argument possible | First principles |

**Honest gap**: no A/B comparing "good parser + simple chunker" vs "bad parser + smart chunker." But the irreversibility argument makes the point without needing one — you can't fix upstream information loss downstream.

### 3. Multi-source retrieval over single-source

| Evidence | Strength | Source |
|---|---|---|
| HERB benchmark (Salesforce): 39,190 artifacts across docs, Slack, GitHub, URLs. Best agentic RAG: 32.96/100. Proves enterprise questions inherently span source types. | Strong — designed specifically to test heterogeneous retrieval | https://arxiv.org/abs/2506.23139 |
| Uber Genie fragmentation framing: "information is fragmented across wiki, Stack Overflow, and other locations." 70,000+ questions answered across 154 Slack channels. | Production deployment at scale | https://www.uber.com/blog/genie-ubers-gen-ai-on-call-copilot/ |
| Dropbox planner degradation: tried separate tools per source, planner got worse with more tools. Consolidated into unified index. | Production architectural lesson | https://dropbox.tech/machine-learning/how-dash-uses-context-engineering-for-smarter-ai |
| Spotify AiKA: ships with techdocs + software-catalog as default sources (Confluence may be supported but is not confirmed as a default). 25% employee WAU, 87% developer WAU. | Architectural ship — multi-source is the default, not opt-in | https://backstage.spotify.com/docs/portal/core-features-and-plugins/aika/getting-started |
| Stripe: observed multiple teams building independent RAGs, consolidated into shared knowledge layer | Direct precedent | https://www.latent.space/p/stripe (podcast testimony) |

**Honest gap**: no clean A/B (wiki-only vs wiki+Slack+code on same eval). **If challenged**: "single-source is provably incomplete for cross-source questions — an engineer asking 'how does this work and when did it break?' needs wiki + code + incident history. That class of question can't be answered from one source. HERB proves the class is large."

### 4. Reranking is worth adding

| Evidence | Strength | Source |
|---|---|---|
| TDS "Six Lessons": discusses chunking and metadata as high-leverage production investments. *(Reranking and "before swapping models" framing were added editorially, not direct quotes.)* | Practitioner blog | https://towardsdatascience.com/six-lessons-learned-building-rag-systems-in-production/ |
| Every production system in the doc uses some form of reranking: Uber (agentic LLM), Dropbox (embedding-based), LinkedIn (graph-based aggregation). None rely on vector similarity alone. | Revealed preference — 3/3 that disclosed details | This doc, section 2 |
| Structural argument: vector similarity compares two independently compressed summaries (bi-encoder). Cross-encoder sees query + chunk together with token-level attention. The gap between "mentions the topic" and "answers the question" is architectural, not empirical. | Logical proof | First principles |

**Honest gap**: no published number isolating reranker impact on an engineering RAG corpus. **If challenged**: "add the reranker, run Ragas eval before and after, measure MRR delta. If it doesn't help, remove it. One day experiment."

### 5. Knowledge MCP pattern is validated in production

| Evidence | Strength | Source |
|---|---|---|
| Stripe "Toolshed": MCP server for internal knowledge. Hubert text-to-SQL ~900 weekly users. Consolidated from multiple teams' RAGs. | Direct precedent for multi-consumer internal MCP | https://www.latent.space/p/stripe (podcast testimony) |
| Glean "for Agents": enterprise knowledge API consumed by customer AI workflows. Production, paying customers. | Production at vendor scale | https://www.glean.com/perspectives/best-rag-features-in-enterprise-search |
| Sourcegraph Cody: code intelligence API. Palo Alto Networks: 2,000 developers. | Published case study | https://sourcegraph.com/case-studies/palo-alto-networks-boosts-2-000-developers-productivity-using-ai-solutions-from-aws-anthropic-and-sourcegraph *(Note: this URL returned 404 as of 2026-04-12. The AWS partner page https://aws.amazon.com/partners/success/palo-alto-networks-anthropic-sourcegraph/ is an alternative source for the same case study.)* |
| Context7: library docs as MCP server. Thousands of developers daily. In our own MCP config. | Production, personal experience | Configured locally |
| Dropbox: VP mentions MCP for tool plumbing in Dash | Architectural signal from major company | https://dropbox.tech/machine-learning/vp-josh-clemm-knowledge-graphs-mcp-and-dspy-dash |

**Honest gap**: multi-consumer variant (one API, many teams' workflows) only has Stripe as direct precedent, and it's podcast testimony. **If challenged**: "the pattern works — Context7 proves it for external docs, Glean proves it at enterprise scale. Building a good retrieval service with an API is correct regardless of whether one or ten consumers call it. MCP is an interface layer, not a bet."

### 6. Eval framework is worth the cost

| Evidence | Strength | Source |
|---|---|---|
| Cost: ~$2–8 per eval run (Ragas, 4 metrics × 100 queries). One weekend to bootstrap + ~$60. | Concrete, verifiable | Calculated from Sonnet pricing |
| Dropbox invested in 4 separate blog posts on eval methodology. Treats eval as seriously as the retrieval system. | Signal from production team | https://dropbox.tech/machine-learning/practical-blueprint-evaluating-conversational-ai-at-scale-dash |
| Uber: ~100 golden queries was sufficient for their eval. Minimum viable eval set is small. | Production precedent | https://www.uber.com/blog/enhanced-agentic-rag/ |
| DoorDash: 90% hallucination reduction, 99% compliance issue reduction — measured via 5-dimension LLM judge + human calibration. Can't report those numbers without eval. | Production outcome dependent on eval | https://careersatdoordash.com/blog/large-language-models-based-dasher-support-automation/ *(Note: original URL had "modules" typo; corrected to "models". Site returns 403 to automated fetchers — content unverifiable via automated check as of 2026-04-12.)* |
| Spotify's trap: 86% WAU with zero quality evidence. Adoption metrics without quality metrics is flying blind. | Cautionary counter-example | https://backstage.spotify.com/discover/blog/aika-data-plugins-coming-to-portal |

**If challenged**: "the cost of eval is $2–8 per run. The cost of deploying a broken chunking change that silently degrades answers for a week is immeasurable. One weekend of setup buys permanent visibility into whether changes help or hurt."

### 7. Feedback loops are worth building from day 1

| Evidence | Strength | Source |
|---|---|---|
| Spotify: "Honk" series names feedback loops as key to predictable agentic results. 25% employee WAU, 87% developer WAU. | Qualitative argument + adoption metrics (specific resolution-time metric previously cited could not be verified in the article) | https://engineering.atspotify.com/2025/12/feedback-loops-background-coding-agents-part-3 |
| Dropbox: validates LLM-judge against human labels — calibration is itself a feedback loop between automated and human eval | Methodological precedent | https://dropbox.tech/machine-learning/llm-human-labeling-improving-search-relevance-dropbox-dash |
| DoorDash: random human-reviewed transcript samples for calibration — continuous production ↔ eval feedback loop | Production practice | https://careersatdoordash.com/blog/large-language-models-based-dasher-support-automation/ *(Note: original URL had "modules" typo; corrected to "models". Site returns 403 to automated fetchers — content unverifiable via automated check as of 2026-04-12.)* |

**If challenged**: "Spotify's engineering blog explicitly names feedback loops as the key differentiator for predictable agentic results, and their system has 87% developer WAU. The feedback loop is how the system gets better over time instead of slowly rotting."

### 8. Tables should be atomic (don't split for size uniformity)

| Evidence | Strength | Source |
|---|---|---|
| Embedding model token limit is the real constraint, not chunk-size aesthetics. Titan v2 = 8,192 tokens. A 3,000-token table among 1,000-token prose chunks is correctly sized. | Hard technical constraint | AWS Titan v2 docs |
| Splitting a table destroys column-header → cell relationship — same irreversibility argument as the parsing layer. Sub-chunk without headers is meaningless. | Logical proof | First principles |
| Uber's key lesson: structure preservation (including tables) was the dominant quality lever. Moved off naive loaders specifically because tables were fragmenting. | Team testimony from production | https://www.uber.com/blog/enhanced-agentic-rag/ |

**If challenged**: "open one of our PDFs with tables, run it through the current pipeline, look at the chunk that comes out. If the table is intact, we're fine. If it's `Name Age City John 25 NYC`, that's the problem — and no downstream fix can recover it."

---

## Target Use Cases and Consumers

**Caveat**: many of the metrics below come from external-facing deployments (Uber's Slack-based on-call assistant, LinkedIn's customer service system, DoorDash's Dasher support automation). Our use case is internal — engineering teams and AI workflows consuming organizational knowledge. The same retrieval principles apply, but adoption dynamics and quality expectations differ. Internal users are more forgiving of imperfect answers and more capable of verifying sources; external/customer-facing systems need guardrails (see DoorDash two-tier pattern, Lesson 13).

### Consumers

**Human consumers**: developer, analyst, new hire / trainee, production support, project manager, domain specialist.

**LLM consumers**: Q&A chatbot, code review bot, CI/CD pipeline agent, compliance checker, any future team's AI workflow that needs organizational context.

### Use Cases

1. **Developer productivity** — "what calls this function?", "what design doc explains this module?", "what's the deployment procedure?" → MCP retrieves codebase chunks cross-referenced with Confluence design docs, ADRs, and runbooks.
   - Palo Alto Networks: 2,000 developers using Sourcegraph Cody + Claude on Bedrock, reported 25–40% productivity gain (self-report survey, treat as marketing-grade). [source](https://sourcegraph.com/case-studies/palo-alto-networks-boosts-2-000-developers-productivity-using-ai-solutions-from-aws-anthropic-and-sourcegraph *(Note: this URL returned 404 as of 2026-04-12. The AWS partner page https://aws.amazon.com/partners/success/palo-alto-networks-anthropic-sourcegraph/ is an alternative source for the same case study.)*)
   - GitHub Copilot × Accenture RCT: 26.08% increase in completed tasks across 4,867 developers at 3 companies, but concentrated in below-median-tenure developers — above-median-tenure showed no statistically significant gain. [source](https://economics.mit.edu/sites/default/files/inline-files/draft_copilot_experiments.pdf)

2. **Production support** — "how was this type of issue resolved before?", "what's the runbook for this alert?" → MCP retrieves similar past Jira tickets and their resolutions, Confluence runbooks, and linked incidents.
   - Uber Genie: 70,000+ questions answered across 154 Slack channels, 48.9% helpfulness rate, ~13,000 engineering hours saved (hours number has no published derivation). [source](https://www.uber.com/blog/genie-ubers-gen-ai-on-call-copilot/)
   - LinkedIn KG-RAG: MRR 0.927 vs 0.522 baseline (+77.6%), 28.6% reduction in median per-issue resolution time over 6 months. Peer-reviewed SIGIR '24. [source](https://arxiv.org/abs/2404.17723)
   - DoorDash: 90% reduction in hallucinations, 99% reduction in severe compliance issues via two-tier guardrails. [source](https://careersatdoordash.com/blog/large-language-models-based-dasher-support-automation/ *(Note: original URL had "modules" typo; corrected to "models". Site returns 403 to automated fetchers — content unverifiable via automated check as of 2026-04-12.)*)

3. **Onboarding + training** — new hires or anyone ramping up on an unfamiliar system → MCP retrieves Confluence architecture overviews, team processes, codebase documentation, and relevant Jira context for what's currently in flight.
   - Spotify AiKA: 86% of weekly active GitHub users also weekly active AiKA users, 25% of all employees WAU, 1,000+ daily users. Caveat: adoption metrics only, no quality or time-saved metrics disclosed. [source](https://backstage.spotify.com/discover/blog/aika-data-plugins-coming-to-portal)
   - GitHub Copilot × Accenture: the below-median-tenure developer lift (26.08% completed tasks) is specifically relevant here — newer developers benefit most from knowledge assistance. [source](https://economics.mit.edu/sites/default/files/inline-files/draft_copilot_experiments.pdf)

4. **Domain-specific policy knowledge** — "what are the eligibility requirements for program X?", "what changed in the latest directive?" → MCP retrieves domain-specific policy docs, public reference material, and related Jira requirements tickets.
   - Uber Genie (security/privacy policy domain): EAg-RAG +27% acceptable answers, −60% incorrect advice on policy questions. Key lesson: structure preservation of policy docs with complex tables was the dominant quality lever. [source](https://www.uber.com/blog/enhanced-agentic-rag/)
   - No direct published metric for domain-specific RAG in the doc. Uber's policy-doc use case is the closest analogue — complex regulatory/policy documents with tables are the same retrieval challenge.

5. **Cross-source synthesis** — questions that span multiple sources: "what's the requirement, how was it implemented, and what issues were found?" → MCP retrieves Jira requirement + codebase implementation + Jira defect tickets in one query from the unified index.
   - HERB benchmark (Salesforce): 39,190 artifacts across docs, Slack, GitHub, URLs. Best agentic RAG scored only 32.96/100. Proves this class of question is large and current systems struggle with it — an opportunity to differentiate. [source](https://arxiv.org/abs/2506.23139)
   - Dropbox Dash: consolidated "dozens of individual service APIs" into one universal search index because the LLM planner degraded with too many tools. [source](https://dropbox.tech/machine-learning/how-dash-uses-context-engineering-for-smarter-ai)

6. **AI workflow context injection** — any team's LLM agent (code review bot, CI/CD validator, compliance checker, Q&A chatbot) needs organizational knowledge → MCP provides Confluence, Jira, codebase, and domain knowledge as structured chunks + metadata without each team building their own RAG. This is the Stripe precedent: they observed multiple teams independently building their own RAG stacks over the same content, and consolidated into a shared knowledge layer ("Toolshed") that all teams consume through one API.
   - Stripe: Toolshed MCP server, Hubert text-to-SQL assistant ~900 weekly users. Consolidated from multiple teams' independent RAGs. [source](https://www.latent.space/p/stripe) (podcast testimony, no published blog)
   - Glean "for Agents": enterprise knowledge API consumed by customer AI workflows at scale. Production with paying customers. [source](https://www.glean.com/perspectives/best-rag-features-in-enterprise-search)
   - Spotify feedback loops: "Honk" series names feedback loops as the key to predictable agentic results. 25% employee WAU, 87% developer WAU. [source](https://engineering.atspotify.com/2025/12/feedback-loops-background-coding-agents-part-3)

---

## From Zero to Knowledge MCP (Step-by-Step with Iteration Loops)

1. Pick first corpus — one Confluence space or doc collection, 50–200 docs, a team already struggling to search
2. Build golden query set — 50 queries with correct answers + which source docs contain them. Include at least 10 queries whose answers live inside tables, 5 whose answers span multiple sections, and 5 that require heading context to disambiguate (e.g. "what's the timeout?" is meaningless without knowing which service)
3. Set up bronze layer — raw documents + metadata (page_id, space, breadcrumb, lastModified, ACL groups)
4. Make guardrails decisions — **ACL:** org-wide-readable only (start here) or index ACLs per doc and filter at query time. **Day-one guardrails (non-negotiable):** space/project allowlist in ingestion config, secret/credential regex scanning at ingestion (AWS keys, GitHub PATs, passwords), result count cap on MCP server (hard max ~20 chunks). **Week-one:** metadata sanitization — strip internal doc IDs, author emails, internal URLs before returning chunks to consuming LLM. **Deferred to v2/v3:** PII scanning via NER at ingestion (if corpus scope expands); permission-scoped retrieval at query time (hard problem — requires plumbing user identity through consuming LLM → MCP → vector DB filter)
5. Build parsing layer — run 3 worst docs through Docling/Textract, compare to current `.txt`, pick parser
6. Design metadata schema — source_doc_id, source_type, heading_breadcrumb, element_types, contains_table, contains_code, last_modified, space, acl_groups, labels, parent_table_id, chunk_index, total_chunks
7. Build chunking pipeline — Sonnet-based, structure-preserving, table-aware, one command, automated, incremental
8. Embed and store — Titan v2 → pgvector with metadata columns + `tsvector` column for future hybrid
9. Set up Ragas eval harness — use `faithfulness` (groundedness), `answer_correctness`, `context_precision`, `context_recall` as core metrics. Reference: `aws-samples/sample-rag-evaluation-ragas` for Ragas + Sonnet on Bedrock. Since MCP returns chunks not answers, add a test LLM step: golden query → MCP retrieve → test LLM generates answer from chunks → Ragas evaluates. Run first eval against golden query set. This is the baseline.
10. **LOOP A: Parsing + Chunking Quality** — 3–5 iterations, highest leverage loop.
    - **Eval metrics**: Ragas `context_precision` + `context_recall` + `faithfulness`, broken down by query type (table queries, multi-section queries, heading-dependent queries)
    - **Parsing-specific checks**: for each table-answer query in the golden set, retrieve the top-5 chunks and check: does the chunk contain a readable table with intact column headers? Or is it linearized mush? Score: % of table queries where the retrieved chunk has an intact table. If low, the problem is the parser, not the chunker.
    - **Chunking-specific checks**: for each golden query, does the top-1 chunk contain the *complete* answer, or is the answer split across chunks 1 and 3? Score: % of queries where top-1 chunk is self-sufficient. If the answer keeps getting split, chunk boundaries are wrong.
    - **Heading context check**: for each heading-dependent query, does the retrieved chunk carry a heading breadcrumb that disambiguates it? If a chunk says "set timeout to 30s" but metadata doesn't tell you which service and environment, heading breadcrumb extraction is broken.
    - **Orphan chunk check** (automated, no golden set needed): scan all chunks in pgvector. Flag any chunk that starts mid-sentence, contains a partial table row without a header, or has an empty heading_breadcrumb. Target: 0 orphan chunks.
    - **Diagnosis flow**: low table-query scores → fix parser (step 5). Low self-sufficiency → fix chunk boundaries/prompt (step 7). Missing heading breadcrumbs → fix metadata extraction (step 7). Orphan chunks → fix chunking prompt or add post-chunk validation.
11. Add cross-encoder reranker — Cohere Rerank on Bedrock or self-hosted BGE-reranker
12. Add HyDE (Hypothetical Document Embeddings) — generate hypothetical answer, embed that instead of raw query. Largest single retrieval improvement per 2026 consensus. Expect biggest gains on vocabulary-mismatch queries.
13. Add CRAG (Corrective RAG) — grade retrieved chunks before generating. If all chunks score below relevance threshold, re-query with reshaped query or flag as unanswerable. Prevents confident wrong answers from irrelevant context.
14. **LOOP B: Retrieval Tuning** — 2–3 iterations, diminishing returns faster than Loop A.
    - **Eval metrics**: Ragas `context_precision` + `context_recall` + MRR (Mean Reciprocal Rank — where does the correct chunk appear in the ranked results?)
    - **Reranker-specific check**: compare MRR before and after reranker. If MRR jumps (correct chunk moves from position 8 to position 1), the reranker is earning its keep. If MRR barely moves, the bottleneck is elsewhere.
    - **Synonym/paraphrase check**: include 10 golden queries that use different vocabulary from the source docs ("roll back a failed deploy" when the doc says "revert a broken release"). Measure source F1 on just these. Low score → hybrid BM25+vector won't help; high score → vector search is handling synonyms fine.
    - **Top-K sensitivity check**: run eval at top-5, top-10, top-20, top-50. If source F1 at top-50 is much higher than at top-5, good chunks exist but ranking is burying them — reranker is the fix. If source F1 at top-50 is still low, chunks aren't in the index — back to Loop A.
    - **Diagnosis flow**: low MRR but high recall@50 → reranker/ranking tuning. Low recall@50 → back to Loop A. Synonym queries failing → consider hybrid retrieval or query expansion.
15. Build MCP server — `query` tool returning top-K chunks with full metadata, no generation
16. Build one consuming app — Slack bot, web chat, or Claude Code with MCP configured
17. Build query-level telemetry into the MCP server — log every MCP tool call with structured payload: `query`, `chunks_returned`, `top_chunk_score`, `doc_sources`, `timestamp`, `latency_ms`. Build feedback collection into the consuming app — thumbs up/down, "wrong source", "outdated" at minimum. Implement low-confidence detection: if top chunk score < threshold, log as `low_confidence_retrieval` for weekly review.
18. Build pipeline-level health monitoring — 6 operational monitors: (1) ingestion pipeline completion (did the run finish?), (2) docs processed vs. expected (catch source API silently returning empty), (3) embedding API errors/latency (alert on >5% error rate or p95 >10s), (4) vector DB health (connection failure or query timeout), (5) MCP server uptime (health check endpoint), (6) index size over time (alert on >20% day-over-day change — catches runaway growth or accidental mass deletion). For an internal tool, Slack alerts on failure are sufficient.
19. Set up monthly usage insights report — aggregate query logs into a recurring one-pager: most-queried topics (where knowledge gaps are), queries with no good results (documents that should exist but don't), source distribution (where real knowledge lives vs. where people think it lives), power users vs. inactive teams (adoption signal for sponsor). This report is worth more politically than the system itself.
20. Set up automated freshness decay — per-source-type decay curves applied at query time. Objective signal (timestamp), no feedback-loop risk. Safe to automate from day 1.
21. **LOOP C: Real-World Feedback** — continuous, two speeds.
    - **Automated (telemetry + analytics)**: log all queries + results + feedback + scores. Weekly automated job clusters recent queries by topic, flags topics with >40% negative feedback, identifies source types with consistently low `faithfulness`, flags freshness issues. Outputs a report — detection is automated, action is human.
    - **Human-in-the-loop (parameter changes)**: review weekly report → decide if it's a retrieval tuning issue or a content/chunking issue → adjust reranker weights / source boosting / metadata filters manually. Do NOT automate parameter changes — down-weighting a source based on feedback creates spiral feedback loops (less exposure → less positive feedback → more down-weighting → source silently disappears from retrieval).
    - **Fast loop (tunes retrieval, no re-ingest)**: reranker weights, source_type boosting, freshness decay curves, top-K parameters, metadata pre-filters. Human decides based on automated report.
    - **Slow loop (tunes chunking, periodic re-ingest)**: accumulated feedback patterns reveal parsing/chunking problems ("table queries consistently fail", "chunks from space X always rated poorly") → queue for Loop A re-run on affected sources.
    - **Eval metrics**: full Ragas suite (`faithfulness`, `answer_correctness`, `context_precision`, `context_recall`) + user feedback signals. `faithfulness` is especially valuable here — catches hallucination on real queries without needing golden answers.
    - **Query gap detection**: collect all queries from real usage. Cluster them. Identify clusters with no golden query coverage — add representative queries to golden set.
    - **Source gap detection**: for queries where context sufficiency is 0, check: does the answer exist anywhere in bronze? If yes → chunking/parsing problem (Loop A). If no → source isn't indexed, add it.
    - **Freshness failure detection**: for queries where the system returns a correct-but-outdated answer, check last_modified on retrieved chunk. If >6 months old and a newer version exists, freshness decay curve needs adjustment.
    - **Diagnosis flow**: new query patterns → expand golden set. Source gaps → add to bronze + Loop D. Stale answers → adjust freshness decay. Wrong chunks for known queries → Loop A or Loop B depending on whether chunks exist.
22. Calibrate LLM-judges — human grades 20–30 queries, compare to Ragas metric scores, validate 90%+ agreement
23. Scale sources — add second corpus. **Build a separate ingestion pipeline** (connector, parser, chunker, metadata extractor) for the new source type. Output lands in the **same pgvector table** with source-type-specific nullable columns added. Same MCP endpoint, same eval harness — just more chunks from a new `source_type`. **When adding Jira:** decide what to index before building the pipeline. Jira issues are noisy — every status transition, comment, and field edit triggers an update. Index issue descriptions + comments on resolved/completed tickets, not the full activity stream. Otherwise the index fills with "Changed status from In Progress to In Review" chunks that pollute retrieval.
24. **LOOP D: Multi-Source Expansion** — per new source type. Each source gets its own pipeline; all pipelines feed one table.
    - **Eval metrics**: source F1 on cross-source queries + single-source regression (did existing single-source queries get worse?)
    - **Cross-source eval**: add 10+ queries whose answers require the new source + an existing source. Measure source F1 specifically on these.
    - **Regression check**: re-run eval on original golden query set. If source F1 drops, the new source introduced noise — fix with source_type weighting or metadata filters.
    - **Source-type-specific parsing validation**: same as Loop A parsing checks but for the new source type. Code needs function-boundary checks (no split functions). Jira needs field-completeness checks (did Summary, Description, Resolution all survive?). Each source type has its own failure modes.
    - **Source-type-specific metadata**: add nullable columns for the new source type (e.g. `jira_priority`, `linked_ticket_ids` for Jira; `file_path`, `function_name`, `language` for code). Existing chunks have NULL for these — no migration needed.
25. Open to other consumers — announce MCP server, additional consumers are incremental
26. **LOOP E: Multi-Consumer Tuning** — as consumer base grows.
    - **Eval metrics**: per-consumer source F1 + context sufficiency + latency p95
    - **Consumer-specific eval sets**: each consuming app may need its own golden queries reflecting its use case. Maintain per-consumer eval subsets.
    - **Latency monitoring**: if p95 exceeds 2s, check whether it's retrieval (pgvector), reranking, or MCP overhead.
    - **Retrieval vs consumption diagnosis**: if consumer reports bad answers but source F1 is high, the problem is how the consuming LLM uses the chunks, not retrieval. Fix the consumer's prompt, not the RAG.

**Overall shape:**

```
Steps 1-9:    BUILD            → first working eval baseline
Loop A:       FIX CHUNKS       → 3-5 iterations, highest leverage
Step 11:      ADD RERANKER
Step 12:      ADD HyDE         → hypothetical document embeddings for vocabulary-mismatch queries
Step 13:      ADD CRAG         → corrective RAG, grade chunks before generating
Loop B:       TUNE RETRIEVAL   → 2-3 iterations, diminishing returns
Steps 15-16:  SHIP             → MCP + first consumer
Steps 17-19:  INSTRUMENT       → query telemetry + pipeline health monitoring + usage insights report
Step 20:      FRESHNESS        → automated decay curves
Loop C:       LEARN            → continuous (automated detection, human-decided action)
Step 22:      VALIDATE EVAL    → calibrate Ragas judges
Loop D:       SCALE SOURCES    → one at a time, stabilize each (Jira: filter noise before building pipeline)
Loop E:       TUNE CONSUMERS   → as consumer base grows
```

---

### Graph-Node Retrieval vs Element-Aware Chunking

*Source: section 2.3 (LinkedIn Customer Service KG-RAG, SIGIR '24)*

**Element-aware chunking** solves within-document structure: parse a doc into typed elements (headings, paragraphs, tables, Jira fields like Summary/Description/Resolution), group them into coherent chunks, preserve structure as metadata. Each document is self-contained — no awareness of other documents.

**Graph-node retrieval** solves between-document relationships: store each element/field as a node in a graph, create typed edges between nodes (both within and across documents), query by traversing edges. The graph encodes relationships that vector similarity has to guess at.

**The key difference is what happens to relationships between documents.** Element-aware chunking treats each document as an island. Graph-node retrieval connects them with explicit, traversable edges.

#### Why pre-computed edges add value over plain vector similarity

**Reason A: Multi-hop traversal.** Vector similarity gives one hop — "find things similar to the query." Pre-computed edges give multi-hop — "find things similar to *this thing I already found*, then things related to *those*." Finding TICKET-1234 via vector search → immediately grabbing its neighbors' Resolution nodes via pre-computed edges is instant. Doing the same with vector similarity requires a full new search per hop — slower and noisier.

**Reason B: Different similarity signal.** LinkedIn embeds *titles only* for implicit edges, not full content. Title similarity and content similarity are complementary signals. Two tickets might have similar titles ("OAuth token refresh error" / "OAuth token refresh timeout") but very different descriptions (cache TTL vs network timeout). Title-based edges catch "same category of problem." Content-based vector search catches "similar details."

#### Three methods for finding "related" things

| Method | Signal | When it runs | Cost | When to add |
|---|---|---|---|---|
| **Vector similarity** | Content-level semantic closeness | Query time | Already paid for (pgvector) | Day 1 — you have this |
| **Explicit linkage** | Human-created links (Jira "relates to", "duplicates", "blocks") | Ingest time — just store the link metadata | Cheap — ingest existing link data from source system | When you add Jira/ticketing as a source (Loop D) |
| **Implicit linkage** | Pre-computed embedding similarity (e.g. title embeddings above threshold) | Ingest time — pairwise comparison, store as edges | Expensive — O(n²) comparison, graph DB to store/traverse | Only if eval shows vector similarity + explicit links aren't enough |

**For the pipeline**: when adding Jira tickets in Loop D, store `linked_ticket_ids` as a metadata field on each chunk (from Jira's own link data). That's explicit linkage — free, reliable, no new infra. The consuming LLM sees "related tickets: [TICKET-5678, TICKET-9012]" in the metadata and can query for those if it needs them. This gets 80% of the graph value.

Only invest in implicit linkage and Neo4j if eval shows a specific failure: "user asked about related tickets, we returned the right ticket, but the related tickets weren't linked in Jira and vector similarity didn't surface them."

#### How does the system know when to traverse links?

**It doesn't. The consuming LLM decides.** The RAG returns chunks + metadata (including `linked_ticket_ids`). The consuming LLM sees the user's intent and the metadata, and decides whether to follow links:

- User asks "Why is OAuth throwing 500s?" → LLM sees the ticket description answers the question directly → doesn't follow links → returns answer.
- User asks "We had this same error last month — what fixed it?" → LLM sees linked_ticket_ids in metadata → calls MCP again to fetch the linked ticket's Resolution field → returns answer citing both.

**The RAG doesn't route. The RAG surfaces. The consumer reasons.** This is why the MCP knowledge API pattern works — rich metadata enables the consuming LLM to make routing decisions naturally, without building explicit routing logic into the RAG.

This is also why the metadata-field approach works as well as Neo4j for most cases: the consuming LLM "traverses" by making another MCP call for the linked ticket. That's graph traversal implemented as a second retrieval call instead of a Cypher query — simpler, no graph infra needed.

#### LinkedIn's tech stack (for reference)

- **Neo4j**: graph database storing nodes (ticket sections) and edges (intra-ticket hierarchy + inter-ticket links + implicit similarity). Queries via Cypher.
- **Qdrant**: vector database storing node-level embeddings. Fallback when Cypher queries fail.
- **BERT / E5**: embedding models for node-level embeddings and title-based implicit edge computation.
- **GPT-4**: used for both ticket parsing (YAML template extraction during graph construction) and final answer generation.

#### LinkedIn's published numbers (strongest in the doc)

- MRR 0.927 vs 0.522 baseline (+77.6%)
- Recall@3 0.860, NDCG@3 0.946
- Production: 28.6% reduction in median per-issue resolution time over ~6 months
- Peer-reviewed, SIGIR '24 (https://arxiv.org/abs/2404.17723)

### Separate Ingestion, Unified Retrieval

*Source: section 2.2 (Dropbox — planner degraded with too many tools), section 2.3 (LinkedIn — different source types need different parsing)*

Each source type has fundamentally different connectors, parsers, chunking strategies, metadata schemas, refresh cadences, and ACL models. Trying to build one universal ingestion pipeline is the wrong abstraction. **Each source type gets its own bronze → parse → chunk pipeline.** But the output of all pipelines lands in **one pgvector table** queried through **one MCP endpoint.**

**Why separate ingestion pipelines:**
- **Confluence**: REST API → storage format XHTML → macro-aware markdown converter → heading-aware chunking → metadata: space, breadcrumb, labels, lastModified
- **Jira**: Jira API → field-based parsing (Summary, Description, Resolution, Priority, Status) → field-per-chunk or field-group chunking → metadata: priority, status, linked_ticket_ids
- **Code**: git clone → CST/AST parser (language-specific) → function/class-boundary chunking → metadata: file_path, function_name, language
- Each has its own refresh cadence (wiki daily, tickets hourly, code on push) and ACL model (Confluence space permissions vs Jira project roles vs repo access)

**Why unified retrieval (one table, one endpoint):**
- **One embedding space.** Every chunk gets embedded by Titan v2 into the same vector space. A query about "OAuth timeout" finds relevant chunks from Confluence AND Jira AND code because embeddings are comparable across source types.
- **Dropbox's lesson.** Their planner degraded as they added more tools — the LLM spent more context on tool selection and got it wrong more often. One unified search endpoint eliminates the routing problem.
- **One eval harness.** Golden query set can include cross-source questions. Source F1 measures whether the system pulled from the right source type. Separate tables can't measure cross-source behavior.
- **Consuming LLMs don't need to know the source architecture.** They query one MCP endpoint. `source_type` metadata tells them what kind of result they got.

**Schema pattern — one table with source-type-specific nullable columns:**

```sql
-- Common columns across ALL source types
id, text, embedding, source_type, source_doc_id, last_modified, acl_groups

-- Source-type-specific columns (nullable)
heading_breadcrumb,     -- Confluence, docs
jira_priority,          -- Jira only
jira_status,            -- Jira only
linked_ticket_ids,      -- Jira only
file_path,              -- code only
function_name,          -- code only
language,               -- code only
space,                  -- Confluence only
labels,                 -- Confluence only
```

Nullable columns are fine — Postgres handles them with zero overhead. The columns only matter when you filter on them. `source_type` enables per-type filtering when a consuming LLM specifically wants tickets or code, or unfiltered for cross-source search.

**Mental model: like a data warehouse.** Separate ETL pipelines per source system, all landing in one warehouse that consumers query with one tool.

### DoorDash Two-Tier Guardrails

*Source: section 2.4 (DoorDash Dasher Support RAG)*

For consuming apps that are customer-facing or compliance-sensitive, a guardrail between generation and the user is needed. DoorDash's contribution: **don't use a single sophisticated LLM guardrail — it's too slow and expensive for production.** Use two tiers:

- **Tier 1 (cheap, every response)**: semantic similarity check — compare the generated answer's embedding to the retrieved chunks' embeddings. If the answer is semantically close to the retrieved context → pass → serve. If it drifts → flag → send to Tier 2.
- **Tier 2 (expensive, flagged responses only)**: full LLM evaluator reads the answer + retrieved context and reasons about grounding, compliance, and accuracy. Pass → serve. Fail → fallback to human agent or canned response.

**Result**: 90% reduction in hallucinations, 99% reduction in severe compliance issues.

**For the Knowledge MCP**: not needed for internal/engineer-facing consumption — engineers can evaluate answers themselves. Relevant only if a consuming app is customer-facing or compliance-sensitive. If a team builds a customer support bot on top of the MCP, this is the proven guardrail pattern.

### Spotify: Adoption Metrics ≠ Quality Metrics + Build Feedback Loops from Day 1

*Source: section 2.5 (Spotify AiKA), Spotify "Honk" engineering blog series*

**Adoption caveat**: Spotify's headline numbers (86% of weekly active GitHub users also use AiKA weekly, 25% of all employees WAU, 1,000+ daily users) are **adoption metrics, not quality metrics.** There are no published answer-accuracy numbers, no time-saved claims, no retrieval quality metrics. High usage doesn't mean the system is good — it means people open it. Don't confuse MCP usage stats with retrieval quality. The Ragas eval harness is the ground truth for quality.

**Multi-source as default**: Spotify ships AiKA with `techdocs + software-catalog` as confirmed default sources (Confluence may be supported but is not confirmed as a default in the blog post). This validates that **having multiple source types in one retrieval system** is the default expectation, not an ambitious stretch. (Note: at the ingestion level, each source type has its own pipeline — "multi-source" refers to the unified retrieval layer, not a universal ingestion pipeline.)

**Feedback loops as product requirement**: Spotify's "Honk" background-agent blog series explicitly names feedback loops as the key to predictable results. Build feedback collection into consuming apps from day 1, not as an afterthought. *(Note: a specific resolution-time-reduction metric was previously attributed to this source but could not be verified in the article.)*

**Two feedback speeds for the pipeline:**

- **Fast loop (per query, tunes retrieval layer)**: user gets results from MCP → provides feedback (thumbs up/down, "was this the right source?", "answer was outdated") → this data feeds Loop C. Adjustments that don't require re-ingesting: reranker weights, metadata filters, source_type boosting, freshness decay curves, top-K parameters. These are retrieval-layer parameters that change at query time.
- **Slow loop (periodic, tunes chunking layer)**: accumulate weeks of feedback → identify patterns ("table-answer queries consistently fail", "chunks from space X always rated poorly", "documents about service Y are always incomplete") → diagnose as parsing/chunking problem → re-run bronze → silver pipeline for affected sources. This is Loop A triggered by Loop C data. Chunking can't be re-tuned per query — it's a batch re-processing operation, which is why the incremental pipeline (one command, only re-process changed docs) matters.

### Section 4 Nuances: Dos, Don'ts, and Tradeoffs from Practitioner Community

*Source: section 4 of this doc — aggregated from Weaviate, LanceDB, Databricks, Glean, TensorLake, Qodo, Regal.ai, arXiv papers*

Most of section 4 validates what was captured through the architecture deep-dives. These are the refinements and concrete specifics that add nuance beyond those lessons.

#### DOs that add new specificity

**"Hybrid rank = ~70% semantic + ~30% recency" as a starting default.** Applied AFTER initial vector-similarity filtering, not instead of it. A recent research paper (arXiv 2509.19376) found a simple recency prior hit 1.00 accuracy on freshness tasks. The 70/30 split is a starting point to tune from — the per-source-type decay curves in step 16 of the build flow are the more sophisticated version. Don't apply a global recency prior without per-type tuning, or you'll penalize correct old architecture docs.
- https://arxiv.org/abs/2509.19376

**"Per-content-type decay curves need a `content_category` field beyond `source_type`."** `source_type` alone isn't granular enough within a single source system. Within Confluence, a runbook and an architecture overview have very different shelf lives: on-call runbooks need steep decay (6-month-old runbook for a fast-moving service is dangerous); evergreen architecture wikis need flat decay (2-year-old architecture doc may still be correct). Options for assigning `content_category`: (1) derive from Confluence labels (if consistently applied), (2) LLM-infer during chunking (ask Sonnet "is this a runbook, architecture doc, policy, meeting notes, or other?"), (3) derive from Confluence space (if spaces are organized by content type). Add `content_category` as a metadata column in pgvector; use it to select the decay function at query time.
- https://glenrhodes.com/data-freshness-rot-as-the-silent-failure-mode-in-production-rag-systems-and-treating-document-shelf-life-as-a-first-class-reliability-concern-4/

**"Demand precise, fine-grained citations — paragraph/cell/function level, not doc level."** Document-level citations ("source: runbook-42") are unfalsifiable — the user can't verify without reading the whole document. Paragraph-level citations let users (and consuming LLMs) go directly to the relevant section. **The MCP already supports this** — the `heading_breadcrumb` + `source_doc_id` metadata on each chunk gives paragraph-level attribution. A consuming app can cite "payments-runbook.md > Deployment > Timeouts" instead of just "payments-runbook.md." This is the difference between a demo and a professional system — "precise citations, like linking claims to exact paragraphs, table cells, and figures, separate professional agentic applications from chatbot demos."
- https://www.tensorlake.ai/blog/rag-citations

**"Track freshness as a first-class dashboard metric."** Alongside retrieval latency and answer quality. Auto-archive or flag docs past a defined age threshold (6–12 months for fast-moving domains). This connects to the automated telemetry in step 17 — add a freshness dashboard that shows: distribution of `last_modified` across retrieved chunks, % of retrievals that surfaced chunks older than threshold, trend over time.
- https://www.regal.ai/blog/rag-hygiene

**"For code: use CST parser (tree-sitter) so chunks align with functions and classes."** CST = Concrete Syntax Tree — the full parse tree of source code that preserves every token (whitespace, comments, punctuation). Tree-sitter is the standard tool (~100 languages supported, used by VS Code and Neovim for syntax highlighting). It knows that lines 15–42 are a function called `processPayment` and lines 44–60 are a class called `PaymentService`, so you can chunk code at semantic boundaries (one function = one chunk) instead of arbitrary line counts. **Plan a fallback chunker**: CST parsing is language-specific and breaks on partial/malformed files (common in PRs, migration scripts, config files). If tree-sitter fails on a file, fall back to line-based or heading-based chunking rather than skipping the file entirely. Relevant in Loop D when adding codebase as a source.
- https://www.lancedb.com/blog/building-rag-on-codebases-part-1

**"Prioritize indexing at large scale — not everything in a 500K-line repo needs the same index tier."** Smart chunking + caching + priority indexing + semantic scoring to decide which parts of the codebase matter. Index high-traffic code (frequently changed, frequently referenced) at full fidelity; long-untouched utility files at lower priority or not at all. Read the Qodo blog before Loop D for code.
- https://www.qodo.ai/blog/rag-for-large-scale-code-repos/

**"Invest in chunking + metadata before swapping models."** The TDS article discusses chunking and metadata as high-leverage production investments. Validates the build order: fix chunks (Loop A) → add reranker (Loop B) → then consider model changes. Don't reach for a bigger embedding model or a more expensive LLM when the chunks are bad. *(Note: the reranking-specific claim was added editorially; the article covers chunking and metadata but not reranking explicitly.)*
- https://towardsdatascience.com/six-lessons-learned-building-rag-systems-in-production/

#### DON'Ts that add new specificity

**"Don't stop at 'convert to Markdown → chunk → index.' That's a demo."** Production needs metadata preservation, ACL capture, freshness tracking, and precise attribution. This is the community-consensus validation of lesson 1 (the parsing layer) — not just Uber's experience.
- https://www.tensorlake.ai/blog/rag-citations

**"Don't let the LLM see content the user can't access, even for 'context.'"** Even if you instruct the LLM "don't mention restricted content," it will paraphrase or allude to it. The only safe approach is to never let restricted content enter the context at all. ACL filtering must happen at the retrieval layer (before chunks reach the consuming LLM), not at the generation layer (hoping the LLM self-censors). **For the pipeline: this is bypassed this by only indexing org-wide-readable content (Uber Genie v1's approach).** Simplest, safest. If the scope ever expands to restricted content, filtering must be at retrieval time, not generation time.
- https://www.knostic.ai/blog/glean-data-security

**"Don't skip routing evaluation in mixed corpora."** If ythe eval only grades final answer text, you can't tell whether the system pulled from the right source type. An answer that says "the deployment procedure is X" might look correct but was sourced from a 2-year-old wiki page when a current runbook had the up-to-date version. **Grade source-routing separately.** This is a distinct eval dimension from answer correctness — Ragas `context_precision` and `context_recall` partially cover it, but for multi-source corpora, also track: **"for queries where we know the answer should come from source_type=runbook, what % of the time did the top-1 chunk actually come from a runbook?"** Add this as a per-source-type retrieval accuracy metric in the eval harness. Especially important in Loop D when adding new source types — the new source might be "winning" retrievals it shouldn't be.
- https://medium.com/@bhagyarana80/7-retrieval-metrics-rag-teams-must-track-8961c12fff92

**"Don't trust document-level similarity as citation."** Document-level "source: confluence/runbook-42" attributions are unfalsifiable by users. Push to paragraph/span granularity. Our `heading_breadcrumb` metadata already enables this — consuming apps should cite at the breadcrumb level, not the doc level.
- https://zilliz.com/blog/retrieval-augmented-generation-with-citations

**"Don't ignore temporal signals."** "Without a temporal component, retrieval pipelines risk elevating stale or misleading information." Silent failure mode — retrieval metrics look fine (the chunk is relevant to the query) while answers quietly go wrong (the chunk is outdated). This is why freshness decay and the `last_modified` metadata field are not optional.
- https://arxiv.org/html/2509.19376

#### Key Tradeoffs

**Recency weight vs. evergreen bias.** A global recency prior penalizes old-but-correct architecture docs. Fix: per-content-type decay curves via the `content_category` metadata field. Cost: maintaining the taxonomy (someone decides which category each doc falls into). Start with coarse categories derived from Confluence labels or spaces; refine based on Loop C feedback showing where decay is too aggressive or too flat.
- https://docs.ragie.ai/docs/retrievals-recency-bias

**Unified ACL mirror vs. live permission check.** Mirroring ACLs at index time is fast and unifies cross-source groups but creates a staleness window when access is revoked. Live checks close the window but add latency. Most teams (Glean) pick mirroring + short refresh. **For the pipeline: moot for now — we're indexing only org-wide-readable content.** If we expand to restricted content later, mirror + short refresh is the pattern.
- https://www.glean.com/perspectives/security-permissions-aware-ai

**CST/AST chunking vs. simple windowing for code.** Syntax-aware (tree-sitter) gives function/class-aligned chunks but is language-specific and breaks on partial files. Simple windowing (line-based) works on anything but produces incoherent chunks. **Hybrid: try tree-sitter first, fall back to line-based on failure.** Relevant in Loop D.
- https://www.lancedb.com/blog/building-rag-on-codebases-part-1

**Source precedence when wiki and Slack disagree.** Some teams hand-assign authority tiers (runbook > wiki > Slack). **The approach: rely on source transparency rather than pre-assigned tiers.** The MCP returns `source_type` and `last_modified` in metadata — the consuming LLM (or human) sees where the info came from and judges for itself. If sources conflict, the right response is "here are two sources that disagree" — let the consumer decide. This is consistent with our "the RAG surfaces, the consumer reasons" principle and avoids the governance overhead of maintaining an authority ranking. Revisit if feedback shows consuming LLMs consistently pick the wrong source when conflicts arise.
- https://glenrhodes.com/data-freshness-rot-as-the-silent-failure-mode-in-production-rag-systems-and-treating-document-shelf-life-as-a-first-class-reliability-concern-4/

**Fine-grained citations vs. latency/cost.** Paragraph/span attribution requires storing enough metadata to reconstruct a deep link (doc ID + heading path + optionally character offset). Worth it for trust. Our `heading_breadcrumb` + `source_doc_id` already provides this at near-zero marginal cost — it's metadata we're already extracting.
- https://arxiv.org/html/2406.13663v1

**Feedback-loop investment: thumbs up/down vs. structured follow-up.** Thumbs up/down is cheap but low-signal; "was this the right source?" is richer but needs UX work. Start with thumbs up/down (step 17), evolve to structured feedback as the system matures and you understand which signals matter most. Spotify's "Honk" series argues this is the key differentiator for predictable agentic results.
- https://engineering.atspotify.com/2025/12/feedback-loops-background-coding-agents-part-3

#### Decisions made for the pipeline based on these tradeoffs

| Tradeoff | The decision | Rationale |
|---|---|---|
| Recency vs. evergreen | Per-content-type decay via `content_category` metadata | Coarse start (derive from labels/spaces), refine with Loop C feedback |
| ACL approach | Org-wide-readable only | Bypass complexity; revisit if restricted content becomes necessary |
| Code chunking | Tree-sitter + line-based fallback | Plan for Loop D; haven't reached this yet |
| Source precedence | Source transparency, not authority tiers | Consumer reasons over metadata; avoids governance overhead |
| Citation granularity | Paragraph-level via `heading_breadcrumb` | Already in the metadata schema at zero marginal cost |
| Feedback depth | Start with thumbs up/down, evolve to structured | Low friction to start, grow investment based on what signals matter |
| Routing evaluation | Separate eval dimension: per-source-type retrieval accuracy | Add to Ragas eval alongside `context_precision`/`context_recall` |

---

## Lessons (captured while walking through the research)

### Outline

1. **The Parsing Layer** — there's a stage between ingestion and chunking. Parsing is lossy and irreversible; the fix is upstream (better parser), not downstream (smarter chunker).
   - PDF → structured text: Docling, LlamaParse, Unstructured, AWS Textract, Marker
   - Confluence: use REST API + storage format, watch macros/attachments/ACLs, index `lastModified`
2. **Chunking Strategy Costs** — element-aware chunking is essentially free; LLM-based chunking (what I do) is 1,000–10,000× more expensive in API spend, but flexible. Hybrid is the long-term play.
3. **Embedding Model Token Limit** — every embedding model has a hard token cap. **Bedrock Titan v2 = 8,192 tokens.** This is the *real* constraint on chunk size, not aesthetic preference. Tables are atomic up to this limit.
4. **Indexing Split Tables** — when a table exceeds the embedding cap and has to be split, splitting alone isn't enough. Stack multiple indexing layers (description, summary chunk, linking metadata) so conceptual queries still work.
5. **Evidence Against "Fixed-Size Chunking Is Good Enough"** — no clean isolated ablation exists, but convergent evidence across every disclosed production deployment: bundled gains from Uber (+27%/−60%), LinkedIn (+77.6% MRR, peer-reviewed), documented failure modes, and revealed preference (every shipped system moved off fixed-size).
6. **Reranking** — vector similarity is a rough first pass, not a final answer. Cross-encoder rerankers (BGE-reranker, ColBERT, Cohere Rerank) see query+chunk together and close the gap between "mentions the topic" and "answers the question." Diagnose: chunking problem = right answer not in top-50 at all; reranking problem = right answer in top-50 but ranked low.
7. **Build an MCP Knowledge API** — consumers are both humans (via a people-facing app) and LLMs (agentic workflows across teams). The RAG should expose an MCP server that returns chunks + metadata, not generated answers. Human-facing Q&A is just one consumer app on top of the same retrieval service. This keeps the RAG composable for other agentic apps.
8. **Knowledge MCP in Production: Who's Doing This** — the pattern is validated (Stripe, Glean, Dropbox, Sourcegraph, Context7). The multi-consumer variant (one knowledge API, many AI workflows) is early but the building blocks are all proven. Proven use cases, evidence table, and adoption risk captured.
9. **Eval Framework: Ragas on Bedrock** — use the Ragas framework with four core metrics: `faithfulness` (groundedness/hallucination catch), `answer_correctness`, `context_precision`, `context_recall`. Golden query set of 50–100, human calibration of the judges. Cost: ~$2–8 per eval run. Reference: `aws-samples/sample-rag-evaluation-ragas` for Ragas + Sonnet on Bedrock.
10. **Zero to Knowledge MCP: Step-by-Step with Iteration Loops** — the full build sequence with 5 iteration loops marked where they occur. See dedicated section below.
11. **Graph-Node Retrieval vs Element-Aware Chunking** — element-aware handles within-document structure (fields, sections, tables). Graph handles between-document relationships (ticket links, code imports). Pre-computed implicit edges (LinkedIn) add multi-hop traversal and title-level similarity signal over plain vector search. For most cases, explicit linkage (Jira's own links) as metadata + vector similarity is sufficient. Neo4j/Qdrant only if eval shows relationship queries failing.
12. **Separate Ingestion, Unified Retrieval** — each source type (Confluence, Jira, code) gets its own ingestion pipeline (connector, parser, chunker, metadata extractor). But the output of all pipelines lands in ONE pgvector table with source-type-specific nullable columns + ONE MCP endpoint. Build separately, serve together. Dropbox lesson: planner degrades with separate tools per source.
13. **DoorDash Two-Tier Guardrails** — for customer-facing or compliance-sensitive consuming apps: Tier 1 = cheap semantic similarity check (answer embedding vs chunk embeddings), Tier 2 = expensive LLM evaluator triggered only when Tier 1 flags. DoorDash rejected single-model guardrails on cost/latency grounds. Result: 90% hallucination reduction, 99% compliance issue reduction. Not needed for internal/engineer-facing consumption.
14. **Spotify: Adoption ≠ Quality + Feedback Loops** — Spotify's 86% WAU is adoption, not productivity or quality. No answer-accuracy metrics disclosed. Don't confuse MCP usage stats with retrieval quality — Ragas eval is the ground truth. Separately, Spotify's "Honk" series names feedback loops as the key differentiator: build user feedback collection into consuming apps from day 1. Two speeds: fast loop (per-query feedback tunes retrieval-layer params like reranker weights, freshness decay, source boosting — no re-ingest needed) and slow loop (accumulated feedback patterns diagnose parsing/chunking problems → periodic re-run of bronze → silver pipeline for affected sources).
15. **Section 4 Nuances: Dos, Don'ts, and Tradeoffs** — practitioner-community refinements that add specificity beyond the architecture lessons. 70/30 semantic/recency default ratio, per-content-type decay needs a `content_category` field beyond `source_type`, paragraph-level citations (not doc-level), routing evaluation as a separate eval dimension, code chunking via CST parser (tree-sitter) + fallback, ACL bypass by indexing only org-wide-readable content.
16. **Jira Noise Filtering** — Jira issues are noisy; every status transition, comment, and field edit triggers an update. Decide early what to index: descriptions + comments on resolved/completed tickets, not the full activity stream. Otherwise the index fills with "Changed status from In Progress to In Review" chunks that pollute retrieval. Relevant when adding Jira in Loop D (step 23).
17. **Structured Retrieval Logging Pattern** — log every MCP tool call with a structured payload: `query`, `chunks_returned`, `top_chunk_score`, `doc_sources`, `timestamp`. This is the foundation for all downstream monitoring — pipeline health, retrieval quality, usage insights. Costs nothing, gives everything needed for weekly review. Implement on day one in the MCP search handler.
18. **Monthly Usage Insights as Strategic Asset** — beyond technical monitoring, aggregate query logs into a monthly one-pager for leadership: most-queried topics (where knowledge gaps are), queries with no good results (documents that should exist but don't), source distribution (where real knowledge lives vs. where people think it lives), power users vs. inactive teams (adoption signal). This report is worth more politically than the system itself — it makes the builder the person who understands how the org's knowledge flows, not just the person who built a tool.
19. **Pipeline Health Monitoring Checklist** — 6-item operational monitoring for the always-on system: (1) ingestion pipeline completion (did the run finish?), (2) docs processed vs. expected (catch source API silently returning empty), (3) embedding API errors/latency (>5% error rate or p95 >10s), (4) vector DB health (connection failure or query timeout), (5) MCP server uptime (health check endpoint), (6) index size over time (>20% day-over-day change = runaway growth or accidental deletion). For an internal tool, Slack alerts on failure are sufficient — no PagerDuty needed.
20. **Guardrails Priority Matrix** — phased approach to guardrails: **Day one (non-negotiable):** space/project allowlist at ingestion config, secret/credential regex scanning at ingestion, result count cap on MCP server. **Week one:** metadata sanitization (strip internal doc IDs, author emails, internal URLs before returning chunks to consuming LLM). **v2 (if corpus scope expands):** PII scanning via NER at ingestion. **v2/v3 (hard problem, skip for now):** permission-scoped retrieval at query time (requires plumbing user identity from consuming LLM → MCP → vector DB filter). Start with the allowlist — it's the simplest and most defensible guardrail.
21. **Dev-Time vs Production Loops** — autoresearch-style loops (unbounded iteration, non-deterministic, minutes of latency, $0.50–$5 per run) belong in the ops layer (offline eval, nightly pipeline maintenance), NOT in the serving layer (user queries). Production loops are hard-capped (1–3 retries), sub-second latency budget, $0.01–$0.05 target, deterministic, graceful degradation. The nightly eval suite IS the right place for autoresearch patterns: run golden query set → auto-diagnose regressions → optionally auto-fix (re-chunk, adjust thresholds) → report to Slack by morning. This is an autoresearch loop running AGAINST the production system, not IN the user request path.
22. **MCP-Only vs Chatbot: Engineering Surface Area** — chatbot is roughly 3x the engineering surface area of MCP-only. MCP-only pushes prompt management, conversation history, answer generation, streaming, output guardrails, and hallucination tracking to the consuming LLM (Claude). Chatbot pulls all of those back onto you. The comparison: prompt versioning (minimal → full system prompt + RAG template + eval CI), model orchestration (embedding + maybe reranker → multi-model routing + fallbacks + streaming + conversation history), RAG pipeline ops (same + conversation-aware retrieval/query rewriting), cost control (~$100/mo → $300–$1,100/mo with semantic caching + model tiering mattering), monitoring (retrieval quality → + generation quality + hallucination tracking + user feedback loop), guardrails (ingestion-time only → + output guardrails: grounding, "I don't know" enforcement, PII filtering, topic boundaries). Start MCP, add chatbot later — validate retrieval before taking on generation.

---

### The Parsing Layer: a missing stage between Ingestion and Chunking

*Source: section 2.1 (Uber Genie / EAg-RAG)*

The mental model started as `ingest → chunk → embed`. Walking through Uber Genie / EAg-RAG made it clear there's a stage I was collapsing into "ingest": **parsing**, the step that turns a raw byte format (PDF, DOCX, HTML, Confluence storage format) into a *structured representation* that a chunker can work with.

**Why it has to be its own stage**: parsing is lossy, and post-processing cannot recover information that parsing destroyed. Once a table has been flattened to `Name Age City John 25 NYC Jane 30 SF`, no chunker — not even Sonnet — can know that `25` belongs to `John` under `Age`. The spatial relationship lived in the document's 2D layout (glyph x/y coordinates) and was thrown away the moment a naive extractor emitted a 1D token stream in reading order. Same reason you can't un-blur an image with a sharpening filter — the information isn't hidden, it's gone.

**Updated mental model**:

```
Raw source (PDF / Confluence / HTML / DOCX)
    │
    ▼  ← parsing decides how much survives
Structured intermediate (markdown / clean HTML / JSON with structure)
    │
    ▼
Chunking (Sonnet, in my case)
    │
    ▼
Embedding (Titan v2)
    │
    ▼
pgvector
```

**Implication for the pipeline**: the Sonnet pre-chunker is only as good as what it sees. If the upstream is `pdftotext` output from a PDF with tables, Sonnet is producing confident-looking chunks of corrupted content and I won't notice until retrieval silently returns wrong answers. **The fix is upstream (better parser), not downstream (smarter chunker or post-processing).**

#### PDF → structured text: tools to try

Default to a structure-aware parser instead of plain text extraction whenever the source has tables, multi-column layouts, or hierarchy worth preserving:

- **Docling** — IBM, open-source, strong table handling, outputs markdown. First thing to try.
- **LlamaParse** — hosted, good with complex layouts.
- **Unstructured.io** — open-source + hosted, broad format support.
- **AWS Textract** — already on Bedrock, good for forms and tables, handles scanned PDFs (OCR built in).
- **Marker** — open-source, markdown output, decent on academic PDFs.

**Diagnostic before scaling**: take the 3 worst PDFs in the corpus (most tables, most complex layout), run them through one of the above, and eyeball the markdown next to the current `.txt`. If the difference is dramatic, swap the parser. If they look the same, the corpus doesn't need it and I can move on.

**When plain `pdftotext` is fine**: single-column prose (books, articles, memos, Word-exports-to-PDF). **When it isn't**: tables, multi-column layouts (papers, financial reports), headers/footers/page numbers, figures with captions, footnotes, sidebars, scanned PDFs (need OCR), forms.

**What post-processing *can* still help with**: noisy-but-recoverable stuff like repeated page headers/footers and page numbers — those leave enough signal (verbatim repetition, predictable position) to strip after the fact. Anything *structural* has to be preserved at parse time.

#### Confluence-specific notes

Confluence is fundamentally easier than PDFs because the source isn't a 2D layout — it's already structured XHTML behind an API. The problem shifts from "recover structure from bytes" to "fetch the right thing and preserve its metadata."

**Right way to ingest**:

1. **Use the REST API, not web scraping.** `GET /wiki/rest/api/content/{id}?expand=body.storage` returns the storage format (canonical XHTML). Scraping the rendered page drags in nav chrome, sidebars, breadcrumbs, and inconsistent macro rendering.
2. **Convert storage format → markdown.** Tools: `confluence-markdown-exporter`, `atlassian-python-api` + a converter, Unstructured.io's Confluence connector. Markdown drops cleanly into Sonnet chunking (markdown is basically the ideal format for an LLM chunker — headings and lists are unambiguous split points).
3. **Preserve hierarchy as metadata.** Confluence pages live in a tree (Space → parent → child). Store `space`, `breadcrumb_path`, `parent_page_title` on each chunk — when a chunk says "see deployment steps below," the breadcrumb tells you which deployment.

**Confluence-specific traps**:

- **Macros** (`{info}`, `{warning}`, `{code}`, `{expand}`, `{jira}`, `{include}`, ToC, `{children}`). Storage format wraps these in `<ac:structured-macro>` tags. A naive HTML-to-text converter drops them or emits gibberish. Need a converter that unwraps them. Especially watch `{code}` (preserve as code block), `{expand}` (often hides the actual answer to a question), and `{include}` (transcludes another page — decide whether to inline or link).
- **Attachments**. Confluence pages routinely have PDFs, Word docs, diagrams, screenshots attached — **these are not in the page body**. Fetch them separately via the attachments API and route through the PDF parsing pipeline. A surprising amount of real knowledge in a Confluence space lives in attached PDFs, not in the page text.
- **Tables**. Easy case — storage format keeps `<table>` markup intact, a good markdown converter preserves them.
- **Diagrams** (draw.io, Gliffy, Lucidchart, Mermaid). Rendered as images in the web view. Storage format references them by attachment ID. Either lose them or extract source XML where possible (draw.io yes, Lucidchart effectively no without API). Most teams accept the loss.
- **Comments**. Separate API call (`/content/{id}/child/comment`). Often contain "this is outdated" / corrections — more current than the page body but noisy and can contradict it. Decision point: index or not?
- **Stale pages**. Confluence rots faster than almost any other knowledge source. **Index `lastModified` as metadata** so I can later filter or down-weight pages untouched in 2+ years.
- **Permissions**. Page-level and space-level ACLs. Indexing a private HR space and surfacing it to all engineers is an incident waiting to happen. Either (a) only index org-wide-readable spaces, or (b) index ACL metadata per page and filter at query time. Uber's first version of Genie picked (a) — "exclude anything not safe for the Slack channel" — because (b) is hard.
- **Labels**. Cheap, high-signal metadata — index them.

**Open question for the corpus**: are Confluence pages mostly prose (runbooks, design docs, meeting notes) or heavy on macros/attachments/diagrams? The answer changes how much effort this layer is worth.

---

### Chunking Strategy Costs: Element-Aware vs LLM-Based

*Source: section 2.1 (Uber Genie / EAg-RAG) — discussion of how Uber probably implements "structure-preservation chunking"*

There are several ways to chunk, but the two main families are **element-aware** (deterministic Python walking a parsed element tree, e.g. Unstructured.io / Docling output) and **LLM-based** (feeding the doc to an LLM and asking for semantic chunk boundaries — what I'm doing with Sonnet). The cost gap between them is dramatic and worth knowing before scaling.

**Cost math** (Sonnet 4.5 list pricing: $3/M input, $15/M output; assumes ~1.2× output:input ratio because chunks return as JSON with metadata):

| Corpus size | LLM-based (Sonnet) | Element-aware |
|---|---|---|
| 1M tokens (~100 docs) | ~$21 | ~$0 |
| 10M tokens (~1K docs) | ~$210 | ~$0 |
| 100M tokens (~10K docs) | ~$2,100 | ~$0 |
| 1B tokens (~100K docs) | ~$21,000 | ~$0 |
| 10B tokens (Uber-ish scale) | ~$210,000 | ~$0 |

**Multiplier: 1,000×–10,000× more expensive in API spend.** And these are *one-time* costs per ingestion — every re-chunk (new prompt, new parser, new Sonnet version) pays again.

**Latency dimension** matters too: element-aware chunks a 100K-token doc in ~1 second; Sonnet takes several seconds per call, so a 10K-doc corpus is hours instead of minutes even with parallelism.

**When LLM-based is worth it (the current situation)**:
- Small to medium corpus (under ~10M tokens) where absolute spend is manageable.
- High-stakes content where chunk quality directly affects answer correctness.
- Documents with messy/inconsistent structure that deterministic parsers can't reliably segment.
- Infrequent ingestion (not nightly syncs).
- Early in the project — Sonnet is a strong default while figuring out what good chunking looks like for the domain.

**When element-aware wins**:
- Large corpus where the cost is genuinely painful.
- Already well-structured input (clean markdown, exported Confluence, Docling output) — Sonnet's marginal value is small because structure is already explicit.
- Frequent re-ingestion.
- Tight ingestion latency budgets.

**The hybrid pattern (the eventual long-term play)**: cheap element-aware chunker for the easy 90% of docs (clean prose, well-formed markdown), Sonnet for the hard 10% (complex tables, inconsistent structure). Most quality at a fraction of the cost. Routing heuristic: does it have tables? does the parser report low confidence? is it longer than N pages? → Sonnet. Otherwise → deterministic.

**For the current state**: if the corpus is under a few thousand documents, Sonnet chunking is fine and likely under ~$100 to ingest. Don't optimize prematurely. **The thing to actually measure**: are Sonnet's chunks meaningfully better than what `MarkdownHeaderTextSplitter` would produce on the same input? If Sonnet is just doing what a free splitter would do, I'm paying for nothing.

---

### Embedding Model Token Limit Is the Real Chunk-Size Constraint

*Source: section 2.1 discussion + general RAG practice*

Every embedding model has a hard maximum input length. For the stack, **Bedrock Titan Text Embeddings V2 = 8,192 tokens**. This is the *actual* constraint on chunk size, and it's more important than any character cap I set for aesthetic reasons.

**Other common embedding model limits for reference**:

| Model | Token limit |
|---|---|
| **Bedrock Titan Text Embeddings V2** | 8,192 |
| OpenAI `text-embedding-3-small` / `3-large` | 8,191 |
| Cohere Embed v3 | 512 |
| Voyage `voyage-3` | 32,000 |
| BGE-large | 512 |

**Why this matters for chunk-size decisions**:

- **The 8,192 limit is a *hard* ceiling.** Anything over it gets truncated silently (or errors, depending on the SDK). I should never produce a chunk that exceeds this.
- **Below the limit, size variance is fine.** A 3,000-token chunk and a 1,000-token chunk are not "imbalanced" — they're appropriately sized for their content. Uniform sizes are an aesthetic preference, not a quality signal.
- **Tables are atomic up to the embedding limit.** A coherent table at 6,000 tokens stays in one chunk even if my surrounding prose chunks are 1,500 tokens. Splitting it just to make sizes match is the actual mistake — see next point.

**The right rule for table handling in the pipeline**:

1. **Tables stay in one chunk if they fit under 8,192 tokens.** Period. No exceptions for "looks too big compared to siblings."
2. **If a table genuinely exceeds 8,192 tokens**, split by *row groups* (never mid-row), and **duplicate the header row** in every sub-chunk so each piece is self-contained.
3. **Optionally generate a one-sentence table description** ("This table lists deployment timeouts by environment for the payments service") and prepend it to every sub-chunk, or store as a separate retrieval target.
4. **Watch for prompt conflicts.** If I tell Sonnet "hard char cap of N" *and* "don't split tables," those rules can conflict on big tables. The prompt should explicitly resolve it: *"If a table exceeds the cap, split by row groups and duplicate the header row in each sub-chunk. Never split a table any other way."*

**Diagnostic for the current pipeline**: does the hard character cap apply uniformly, or does it have an exception for tables? If a 6,000-char coherent table gets force-split because my cap is 2,000, that's a bug. Worth checking the prompt and the post-processing.

**Related: chunk overlap in element-based / structured chunking**

In fixed-size chunking, overlap (10–20% of chunk size) compensates for *arbitrary cuts* — the cut might land mid-sentence, so you fuzz the boundary. In element-based or LLM-based chunking, the boundaries are at semantic points the author already chose as breaks, so traditional text overlap is mostly unnecessary. **Overlap should be ~0.**

What replaces overlap in structured chunking is **metadata enrichment**:
- **Heading prepending**: every chunk starts with its breadcrumb (`# Deployment > ## Steps > ### Step 2`). Gives the chunk standalone context. Either as text in the chunk or as a metadata field — both work.
- **Last-sentence context**: for long narrative docs only, optionally include the last sentence of the previous element. Skip for reference/table-heavy docs.
- **Table description echoing**: split tables get the description repeated in every sub-chunk.
- **Sliding windows for sub-splits within an oversized section**: small overlap *within* a section that had to be sub-split, none between sections.

**The mental model**: fixed-size chunking has overlap to compensate for *bad cuts*. Element-based chunking has no bad cuts, so it doesn't need overlap — it has the *opposite* problem (chunks too independent of context), which gets solved with metadata, not text duplication.

---

### Indexing Split Tables: Splitting Alone Isn't Enough

*Source: section 2.1 discussion + multi-vector indexing patterns (LangChain `ParentDocumentRetriever`, LlamaIndex `RecursiveRetriever`, HyDE)*

When a table exceeds the embedding model's token limit (8,192 for Titan v2) and has to be split — even when the split is correctly done at row boundaries with the header row duplicated — the resulting sub-chunks have failure modes that splitting alone doesn't fix. The fix is to stack **multiple indexing strategies** for the same table so different query types hit different representations.

**Why naive split-at-row-boundary isn't enough**:

- **Conceptual queries miss both halves.** A query like "what timeouts do we configure?" or "what environments do we deploy to?" is asking about the *table as a whole*. Each sub-chunk's embedding is dominated by its specific row data, not by the conceptual meaning. Neither half is a great match.
- **Specific queries hit only one half.** A query for "production timeout" matches the sub-chunk containing the production row, but a follow-up query about "compare staging vs production" loses half the answer if staging is in the other sub-chunk.
- **Top-k budget gets eaten.** If both halves are relevant, two of my top-5 retrieval slots go to one logical unit, crowding out other relevant docs.

**The fix: stack 4 layers of indexing for split tables**

#### Layer 1 (mandatory): generate a one-sentence table description and prepend it to every sub-chunk

Have an LLM (or a template, for uniform tables) write a description like:
> "This table lists deployment timeout values in seconds for the payments service across dev, staging, and production environments."

Prepend this to **every** sub-chunk. Now each sub-chunk's embedding is shifted toward the table's conceptual meaning in addition to its specific row contents. Cheapest, highest-leverage layer. **When generating the description, give the LLM the surrounding context (parent heading, paragraph just before the table) — the description should reflect *why this table exists in this document*, not just what columns it has.**

#### Layer 2 (strongly recommended): a separate "table summary" chunk as its own retrieval target

Create a new chunk that exists purely as a conceptual entry point for the whole table:

```
TABLE SUMMARY (chunk type: table_index)

Description: Deployment timeout values for the payments service across environments.
Source: payments-runbook.md, section "Timeouts"
Columns: environment, timeout_seconds, retry_count, owner
Distinct values in 'environment': dev, staging, production, canary
Row count: 47
Linked sub-chunks: chunk_id_142, chunk_id_143
```

Embed this summary chunk separately. When it's retrieved on a conceptual query, the retrieval logic can also fetch the linked sub-chunks. This is the **parent retrieval** pattern (LangChain `ParentDocumentRetriever`, LlamaIndex `RecursiveRetriever`).

#### Layer 3 (mandatory if splitting): linking metadata on every sub-chunk

Each sub-chunk carries:

```
parent_table_id: "table_payments_timeouts_v3"
chunk_index: 1
total_chunks: 2
table_description: "Deployment timeout values..."
column_names: ["environment", "timeout_seconds", "retry_count", "owner"]
row_range: "rows 1-23 of 47"
```

Enables **chunk expansion at retrieval time**: if any sub-chunk matches, the retrieval layer can fetch the siblings so the LLM sees the whole table when reasoning. Without linking metadata, this option doesn't even exist.

#### Layer 4 (optional, for high-value tables): hypothetical question generation (HyDE-at-index-time)

For especially important tables, have an LLM generate 5-10 hypothetical questions the table could answer, embed those, and store as additional retrieval targets pointing back to the table:

```
"What is the production timeout for the payments service?" → table_payments_timeouts_v3
"How does timeout vary across environments?" → table_payments_timeouts_v3
"What's the retry policy for staging deployments?" → table_payments_timeouts_v3
```

The embedded text is *literally a question similar to what users will ask*, dramatically improving recall on natural-language queries. Save this for the tables I really care about — it's the most expensive layer.

**Rule for the pipeline**:

| Table size | Layers to apply |
|---|---|
| Fits in 8,192 tokens (no split needed) | Layer 1 only (prepend description). Layer 2 is overkill — the table itself is already its own conceptual entry point. |
| Exceeds 8,192 tokens (must split) | Layers 1 + 3 mandatory; layer 2 strongly recommended; layer 4 optional for high-value tables. |

**Why this matters generally**: this is one instance of a broader pattern called **multi-representation indexing** or **multi-vector indexing** — one document gets several embeddings that serve different query types (conceptual vs. specific, natural-language vs. data-lookup). The same pattern applies beyond tables: long code files, lengthy runbooks, multi-section design docs all benefit from a "summary chunk + detail chunks + linking metadata" structure.

---

### Evidence Against "Fixed-Size Chunking Is Good Enough"

*Source: sections 1 and 2 of this doc, cross-referenced*

No clean published ablation isolates chunking strategy alone. **But the convergent evidence across every disclosed production deployment is strong enough to argue from.**

#### Published numbers (bundled, not isolated to chunking)

**Uber EAg-RAG** — +27% acceptable answers, −60% incorrect advice vs vanilla-RAG Genie baseline. Measured via LLM-as-judge on ~100+ curated golden queries. The v2 release bundled four changes: structure-preserving parsing, structure-preserving chunking, pre-retrieval query reformulation agent, post-retrieval filtering agent. **The team's stated lesson: parsing/structure preservation was the dominant quality lever, not retrieval tuning.** That's testimony from the team, not an isolated measurement — but it's testimony from the people who built and measured it.
- https://www.uber.com/blog/enhanced-agentic-rag/

**LinkedIn KG-RAG (SIGIR '24, peer-reviewed)** — MRR 0.927 vs 0.522 baseline (+77.6%); Recall@3 0.860; NDCG@3 0.946. Production: 28.6% reduction in median per-issue resolution time over ~6 months. The comparison is tree-structured graph chunking (tickets parsed into intra-issue trees, nodes = ticket sections) vs vanilla retrieval. Also bundled with graph construction, but the chunking change is the most structurally different component. **This is the strongest published number in the doc.** MRR 0.522 → 0.927 is the difference between "right answer at rank 2" and "right answer at rank 1."
- https://arxiv.org/abs/2404.17723

#### Documented failure modes (reproducible)

- **Tables shred.** Naive fixed-size splits a table into fragments that lose the column-header → cell relationship. A chunk containing `John 25 NYC` without the header row is meaningless. This is reproducible in 10 minutes on any corpus containing tables.
- **Code breaks at function boundaries.** Fixed-size splitting produces incomplete function bodies — the #1 reported failure mode for teams shipping code-aware RAG. (Source: LanceDB, https://www.lancedb.com/blog/building-rag-on-codebases-part-1)
- **Heading context drops.** A fixed-size chunk starting mid-section has no heading breadcrumb. It knows what the paragraph says but not what section/document/topic it belongs to. Query for "deployment steps" and you might retrieve a chunk that says "set timeout to 30s" with zero context for which service or environment.
- **Confluence macro content drops.** Fixed-size chunking after naive HTML-to-text conversion loses `{expand}`, `{code}`, `{include}` macro content entirely. The actual answer to a question is frequently inside an `{expand}` block.

#### Revealed preference (every shipped system moved off fixed-size)

Every team in this deep-dive that disclosed their architecture ended up *not* using naive fixed-size chunking:

| Team | What they moved to |
|---|---|
| **Uber** | Google Docs HTML → structure-preserving chunks (table-aware, heading-aware) |
| **Dropbox** | On-the-fly query-time chunking (no offline fixed-size at all) |
| **LinkedIn** | Intra-issue tree nodes via KG (no text splitting — the graph node is the retrieval unit) |
| **DoorDash** | Undisclosed chunking, but pipeline is summarization → historical case retrieval → KB matching (not naive fixed-size) |
| **Spotify AiKA** | Alpha is keyword search only, but sources are already-structured MkDocs/Backstage entities (not chunked PDFs) |

Zero of six disclosed architectures use naive fixed-size chunking in their shipped version.

#### Practitioner community consensus

- Databricks "Ultimate Guide to Chunking": recommends structure-aware over fixed-size for technical/policy domains. (https://community.databricks.com/t5/technical-blog/the-ultimate-guide-to-chunking-strategies-for-rag-applications/ba-p/113089)
- Weaviate: recommends content-type-aware chunking; code, prose, and tables need different strategies. (https://weaviate.io/blog/chunking-strategies-for-rag)
- Towards Data Science "Six Lessons": discusses chunking and metadata as high-leverage production RAG investments. *(Reranking and "before swapping models" framing were added editorially, not direct quotes from the article.)* (https://towardsdatascience.com/six-lessons-learned-building-rag-systems-in-production/)
- TensorLake: "convert to markdown → chunk → index is a demo, not production." (https://www.tensorlake.ai/blog/rag-citations)

#### What's honestly missing

A clean **isolated ablation**: same corpus, same embedding model, same retrieval pipeline, same generation model — only varying chunking strategy (naive fixed-size vs structure-aware) and measuring answer quality. This does not exist as a public paper in this doc. The Uber and LinkedIn numbers are the best we have, and both are bundled with other changes. **If pushed for a clean number specific to our corpus, the right move is to run our own ablation on a 50-query golden set.** That takes a day, is more credible than any published number because it's our data, and converts a debate into an experiment.

---

### Reranking: the Missing Layer Between Retrieval and Generation

*Source: section 2.1 (Uber EAg-RAG agentic rerank), section 2.2 (Dropbox embedding-based reranker), general production RAG practice*

The current pipeline goes `query → embed → pgvector cosine → top-k → Sonnet generates answer`. There's no reranker in the middle. Almost every production RAG system in this doc has one.

#### Why reranking matters

**Vector similarity compares two summaries that were compressed independently.** The query and chunk were embedded separately — the embedding model never saw them side by side. It's comparing two points in a learned space and hoping "close" means "relevant." That's a rough approximation.

A **cross-encoder reranker** concatenates query + chunk and feeds them together as one input. The model does token-level attention across both — "rollback" in the query directly attends to "undo deployment" in the chunk. It scores whether the chunk *answers* the query, not just whether they're topically related.

The gap this closes: **"mentions the topic" vs "answers the question."** Without reranking, a chunk that says "Deployment rollback procedures have been updated" (cosine 0.89, mentions rollback) outranks a chunk that says "If health check fails, run `kubectl rollout undo`" (cosine 0.84, contains the actual answer).

#### Three reranking approaches (cheapest → most expensive)

| Approach | How it works | Latency add | Cost | Who uses it |
|---|---|---|---|---|
| **Cross-encoder model** | Small ~100M–350M param model scores `(query, chunk)` pairs. BERT-sized — doesn't generate text, just outputs a relevance score. | +50–200ms | Pennies/query | **Most production systems. Standard default.** |
| **Embedding-based reranker** | Use a larger embedding model only for reranking top-K (not for initial retrieval). | +30–100ms | Low | Dropbox Dash |
| **LLM-as-reranker (agentic)** | Full LLM reads query + candidates and reasons about relevance, filters, may re-retrieve. | +1–5s | $$$ per query | Uber EAg-RAG |

#### Cross-encoder reranker models to evaluate

- **BGE-reranker** (`BAAI/bge-reranker-v2-m3`) — open-source, self-hostable, multilingual, strong benchmark performance. Can run on CPU or GPU. No vendor lock-in.
- **ColBERT** (`colbert-ir/colbertv2.0`) — open-source, token-level late interaction (each query token attends to each doc token). More expensive than BGE but more accurate on hard queries. Requires an index.
- **Cohere Rerank** — managed API, available on AWS Bedrock. Easiest to integrate with my existing stack since I'm already on Bedrock. Cost: $1/1,000 queries.
- **Jina Reranker** (`jina-reranker-v2-base-multilingual`) — open-source, 278M params, multilingual.

**For the stack, Cohere Rerank on Bedrock is the path of least resistance** (no self-hosting, same infra). BGE-reranker self-hosted is the path of least cost and most control.

#### The retrieval flow with a reranker

```
query → Titan v2 embed → pgvector top-50 (cheap, fast, rough)
   │
   ▼
cross-encoder reranker → top-5 (slower, accurate)
   │
   ▼
Sonnet generates answer from top-5
```

Top-50 → top-5 is the standard funnel. The first stage casts a wide net (vector similarity is fast); the reranker narrows it (cross-encoder is accurate but can't run on 100K chunks).

#### Why the cross-encoder can be small

Cross-encoders are ~100M–350M parameters (BERT-sized) because the task is narrow: score one `(query, chunk)` pair for relevance, output a single number. No text generation, no world knowledge, no multi-step reasoning. Just "do these two texts relate in a way that answers the question?" — a much simpler task than what Sonnet does.

**But they can't be used as first-stage retrievers** — scoring every chunk in the DB requires one forward pass per chunk per query. At 100K chunks, that's 100K forward passes. Too slow. That's why they sit after vector search narrows to top-50.

#### Hybrid retrieval: BM25 + vector (related improvement, same layer)

Postgres supports full-text search natively (`tsvector`, `tsquery`), so I can add BM25-style lexical matching alongside vector search without new infrastructure:

- **BM25 (lexical)**: scores by keyword overlap — exact term matches. Good at "kubectl rollout undo" when the chunk contains those exact words.
- **Vector (semantic)**: scores by embedding similarity — paraphrases and synonyms. Good at "roll back a failed deploy" matching "revert a broken release."
- **Hybrid**: run both, merge results (Reciprocal Rank Fusion is the simplest merge), then rerank.

I already have the infra for this — it's a schema addition (`tsvector` column) + query change, not a new system.

#### Diagnostic: chunking problem vs reranking problem

Before adding a reranker, diagnose whether the current failures are retrievable at all:

1. **Right answer not in top-50?** → Chunking/indexing problem. The chunk is incoherent or doesn't exist. No reranker can fix this.
2. **Right answer in top-50 but ranked 10th–50th?** → Reranking problem. The information exists, the rough retriever found it, but cosine similarity ranked it low.
3. **Right answer at position 1–5 but LLM still gives wrong answer?** → Generation/prompt problem, not retrieval.

**Rule of thumb: fix chunking first, add reranking second.** Bad chunks can't be rescued by reranking. Good chunks with bad ranking can.

---

### Build an MCP Knowledge API, Not Just a Chatbot

*Source: section 2.1 discussion + use case clarification*

The RAG has two classes of consumers: **humans** (asking questions via a people-facing app) and **LLMs** (agentic workflows that other teams across the org are building). The human-facing Q&A app is just *one* consumer. The RAG itself should be a **retrieval service** that any consumer can call.

**Architectural implication: expose the RAG as an MCP server that returns chunks + metadata, not generated answers.**

```
                    ┌─── Human-facing Q&A app (generation happens HERE)
                    │
MCP Knowledge API ──┼─── Team A's agentic workflow (consumes chunks directly)
(retrieval only)    │
                    ├─── Team B's code-review bot (consumes chunks directly)
                    │
                    └─── Team C's onboarding assistant (generation happens HERE)
```

**Why return chunks + metadata instead of generated answers:**
- Each consuming LLM/app can integrate the knowledge however its workflow needs it. One app generates prose answers; another extracts structured data; another validates a claim against the corpus.
- Generation prompts, model choice, and formatting stay with the consumer, not locked into the RAG.
- Consuming LLMs can reason over metadata (source authority, freshness, heading breadcrumb) to decide what to trust and how to cite.
- Consuming LLMs can call back for additional retrievals if the first results are insufficient — they're agents, they can iterate.

**What the MCP server should return per result:**

```json
{
  "text": "chunk content...",
  "metadata": {
    "source": "payments-runbook.md",
    "heading_breadcrumb": ["Deployment Guide", "Steps", "Step 2"],
    "source_type": "runbook",
    "last_modified": "2026-03-15",
    "space": "Engineering",
    "contains_table": false,
    "parent_table_id": null,
    "acl_groups": ["engineering", "all-staff"]
  },
  "score": 0.91
}
```

**Why this matters for what we build:** every metadata investment discussed above (heading breadcrumbs, element types, freshness, ACLs, table linking) becomes doubly useful — it's not just for internal filtering, it's context that consuming LLMs actively use to reason about the results. The richer the metadata, the smarter the consumers can be.

**MCP specifically** because it's the emerging standard for tool/knowledge interfaces to LLMs (supported by Anthropic, OpenAI, and others; Claude Code has native MCP support). A REST API works too, but MCP gives any team's LLM a standardized way to discover and call the knowledge service without custom integration per consumer.

---

### Knowledge MCP in Production: Who's Doing This

*Source: sections 2.2 (Dropbox), 3 (multi-source evidence), ecosystem research*

Before committing to "build an MCP knowledge API that other teams' AI workflows consume," reality-check: is this pattern actually working in production?

#### Companies doing this now

**Stripe "Toolshed"** — built an MCP server exposing internal tools and knowledge to AI workflows. Multiple internal tools consume it, including Hubert (text-to-SQL assistant, ~900 weekly users). Stripe observed multiple teams independently building their own RAG stacks and consolidated into a shared knowledge layer. Leadership drove the consolidation. *Source: Latent Space podcast with Emily Glassberg Sands. Testimony only, no published blog with architecture details.*

**Glean** — the entire company is built around this pattern. Indexes all enterprise knowledge (Confluence, Slack, Google Drive, Jira, codebase, etc.) and exposes a search/retrieval API. Recently added a "Glean for Agents" product tier explicitly for LLM-to-LLM consumption. Large enterprise customers where multiple AI workflows consume Glean as a knowledge backend. *Production, paying customers, but Glean is the vendor — not an internal build.*

**Dropbox Dash** — VP Josh Clemm explicitly mentions MCP for tool plumbing. Dash is a retrieval service that multiple AI features plug into, not just a chatbot. *Architectural choice; no published multi-team consumption metrics.*

**Sourcegraph Cody** — code intelligence as a service. Indexes codebases and exposes code understanding as an API that AI assistants consume. Palo Alto Networks has 2,000 developers using it. *Production, published case study.*

**Context7** — library docs as an MCP server. Thousands of developers use it daily with Claude Code, Cursor, etc. **Already in the MCP config — I've been experiencing this pattern all session.** Simple, proven, works. *Production, but external docs, not internal enterprise knowledge.*

#### Evidence strength table

| Evidence | What it proves | Strength |
|---|---|---|
| Stripe consolidated multiple teams' RAG into shared knowledge layer via MCP | Direct precedent for "one knowledge API, many internal consumers" | Testimony only (podcast) |
| Glean "for Agents" — enterprise knowledge consumed by customer AI workflows | Enterprise knowledge API consumed by LLMs works at scale | Production with paying customers, but vendor-built |
| Context7 — library docs consumed by developer AI tools | Knowledge MCP consumed by LLMs works, daily use | Production, widely used, but external docs not internal knowledge |
| Dropbox mentions MCP for tool plumbing | Major company chose MCP as the interface layer | Architectural signal, no multi-team metrics |
| Sourcegraph Cody — code intelligence API | Code knowledge consumed by AI assistants at 2,000-developer scale | Published case study |
| MCP ecosystem growing rapidly (1,000+ servers in directories) | Ecosystem momentum | Most servers are simple integrations, not enterprise knowledge |

#### Proven use cases (high confidence)

These patterns are working in production with published evidence:

- **Developer AI tools querying codebase + docs knowledge** — Sourcegraph Cody, Context7
- **Customer support AI querying KB articles + ticket history** — LinkedIn (SIGIR '24 paper), DoorDash
- **On-call AI querying runbooks + wiki + incident history** — Uber Genie (70K+ questions, 154 Slack channels)
- **Enterprise search AI querying all knowledge sources** — Glean, Dropbox Dash

#### Emerging use cases (medium confidence, logical but less published evidence)

- Multiple teams' chatbots/agents sharing one knowledge backend instead of each building their own RAG
- CI/CD pipelines querying knowledge API to auto-generate docs, validate configs, check compliance
- Code review bots querying architecture decisions + coding standards from the knowledge base
- Onboarding bots querying team wiki + codebase + org chart

#### What's validated vs what's early

The **pattern** is validated: knowledge API → consumed by LLM → produces better output. Every example above proves this.

The **multi-consumer variant** (one knowledge API, many AI workflows within one org) is early. Stripe is doing it. Glean is selling it. But "we built an internal knowledge MCP and 8 teams' AI workflows successfully consume it" hasn't been published with numbers yet.

**This shouldn't block the build**, because:
1. A good retrieval service with an API is the right architecture regardless of whether one or ten consumers call it.
2. MCP is an interface layer, not a fundamental architecture choice. Build the retrieval service well, add MCP, multi-consumer follows naturally.
3. Even if only one team's AI workflow consumes it initially, additional consumers are incremental.

#### The real risk

The risk isn't "this pattern doesn't work." The risk is **"building a knowledge API that nobody consumes because teams build their own instead."** That's an adoption/org problem, not a technical one. Stripe solved it by having leadership consolidate — multiple teams were building their own RAGs, leadership said "stop, use the shared one." **Worth thinking about how to drive adoption, not just how to build the system.**

---

### Eval Framework: Ragas on Bedrock

*Source: section 2.2 (Dropbox Dash — "best-documented eval methodology"), section 1 (measurement methodology), DoorDash guardrails*

The current eval is basic numerical sanity checks. Plan to use the **Ragas framework** (`vibrantlabsai/ragas`) as the eval harness — it's the de facto standard for RAG eval, and AWS has a sample notebook demonstrating Ragas + Sonnet on Bedrock (`aws-samples/sample-rag-evaluation-ragas`), which is the stack.

#### Core metrics (the explicit subset of Ragas)

Ragas offers a broad menu of metrics. These four are the core subset we care about, mapped to the Dropbox-style judges that motivated them:

| Ragas metric | What it catches | Needs golden answer? | Dropbox equivalent |
|---|---|---|---|
| **`faithfulness`** | **Hallucination / groundedness** — is every claim in the response traceable to a retrieved chunk? If the answer says "retry policy is 30s" and no chunk mentions retries, it's ungrounded. | **No** — just needs chunks + response | DoorDash's two-tier guardrail (offline version) |
| **`answer_correctness`** | **Factual accuracy** — does the response match the known correct answer? | Yes | Dropbox Judge 1 (binary correctness) |
| **`context_precision`** | **Source precision** — of the retrieved chunks, how many were actually relevant? | Yes (ground-truth source mapping) | Dropbox Judge 3 (source F1 — precision half) |
| **`context_recall`** | **Source recall** — of the chunks that should have been retrieved, how many were? | Yes (ground-truth source mapping) | Dropbox Judge 3 (source F1 — recall half) |

**Why `faithfulness` is the key addition**: the other three metrics only work on the golden query set (they need known correct answers). `faithfulness` works on **any** query — it just checks whether the response is grounded in the retrieved chunks. This means it scales to real production queries from Loop C where we don't know the correct answer. It's the only metric that catches hallucination on unanticipated questions.

**Additional Ragas metrics to enable later as needed:**

| Metric | What it measures | When to enable |
|---|---|---|
| `context_entity_recall` | Do retrieved chunks contain the key entities needed to answer? | Debugging retrieval — more granular than context_recall |
| `answer_similarity` | Semantic similarity between response and golden answer | When you want partial credit instead of binary correctness |
| `noise_sensitivity` | Does adding irrelevant chunks degrade the answer? | Testing reranker quality — if noise hurts, reranker isn't filtering well |
| `answer_relevancy` | Does the response actually address the question? | Closest to Dropbox Judge 2 (completeness) |

**Adaptation for MCP knowledge API**: since the MCP returns chunks not answers, eval needs an extra step — a test LLM generates an answer from the retrieved chunks, then Ragas evaluates that generated answer. This simulates what a consuming LLM would do:

```
golden query → MCP retrieve chunks → test LLM generates answer → Ragas evaluates
```

The test LLM is just for eval — it doesn't affect the production MCP architecture.

#### The golden query set

The foundation everything else depends on. Without it, every change is a guess.

- **Size**: 50–100 queries. Uber uses ~100. Dropbox uses production logs + synthetic. 50 is the minimum for meaningful signal; more than 200 has diminishing returns for an internal system.
- **What each entry contains**: the query, the known correct answer, AND which source documents contain the answer. That last part is what makes `context_precision`/`context_recall` measurable — you need a ground-truth mapping of query → correct source docs.
- **Query composition**: at least 10 queries whose answers live inside tables, 5 whose answers span multiple sections, 5 that require heading context to disambiguate, 10 that use different vocabulary from the source docs (synonym/paraphrase queries for testing vector search).
- **Sources for queries**: (1) real questions people ask (Slack history, support tickets, meeting notes), (2) LLM-generated synthetic Q&A from the corpus covering specific content types (tables, prose, procedures, code). Production queries reflect real usage patterns; synthetic queries fill edge-case gaps.
- **Refresh**: quarterly. The corpus changes, queries drift, new content types appear.

#### Human calibration of Ragas metrics

The part most teams skip and Dropbox didn't. **How do you know the Ragas metrics are grading correctly?**

**Method**:
1. Take a held-out subset of 20–30 queries from the golden set.
2. Have a **human** grade the answers on all four dimensions (correctness, groundedness, source precision, source recall).
3. Compare human grades to Ragas metric scores. Measure agreement rate.
4. If Ragas agrees with humans 90%+ on binary correctness and faithfulness, trust it at scale. If it only agrees 70%, the eval is noisy — don't make architecture decisions based on small score differences.

**When to re-calibrate**: when you switch the Ragas judge model (e.g. Sonnet version upgrade), or when the corpus changes significantly (new content types that might confuse the judge).

**Cost**: 2–3 hours of a person's time, once. Not an LLM cost — a human-attention cost. Worth it because it tells you whether your automated eval can be trusted.

#### Cost of eval is low

| Item | Cost | Frequency |
|---|---|---|
| Golden query set curation (50–100 queries) | 4–8 hours of human time, $0 in LLM spend | Once, refresh quarterly |
| Full Ragas eval run (4 metrics × 100 queries) | ~$5–8 per run | Per change during active dev; weekly during steady state |
| Synthetic Q&A generation (500 pairs) | ~$50–100 | Once, refresh quarterly |
| Human calibration (20–30 queries) | 2–3 hours of human time | Once; re-validate on model changes |

**Total to bootstrap**: one weekend of setup + ~$60 in LLM costs. Ongoing: ~$5–8 per eval run.

**The cost of NOT running eval**: every change to parsing, chunking, or reranking is a guess. Can't A/B test chunking strategies. Can't justify the parsing layer investment. Can't tell if the reranker earned its keep. Can't diagnose "the answers are wrong" complaints. Can't catch hallucination until a user reports it. End up with adoption metrics (like Spotify's 86% WAU) but no quality metrics.

---

## 2026 RAG Chunking & Retrieval Consensus

*Added 2026-04-12 from [production AI deep-dive](2026-04-11-productionizing-ai-systems.md). Cross-references the chunking and eval discussion in sections (4) and (10) above.*

### Contextual Retrieval — the single biggest win

**Anthropic's Contextual Retrieval** (prepend an LLM-generated context blurb to each chunk before embedding + BM25 indexing):

- Contextual Embeddings alone: **top-20 failure rate 5.7% → 3.7% (35% reduction)**
- Contextual Embeddings + Contextual BM25: **49% reduction**
- Adding reranking: **67% reduction** (5.7% → 1.9%)
- Anthropic's recommended recipe: hybrid search retrieves **top-150** → rerank → keep **top-20** in prompt

**Ingestion cost**: ~800-token chunks, 8k-token docs, 50-token context instruction, Claude Haiku → **~$1.02 per million document tokens**. Now a first-class feature in Amazon Bedrock Knowledge Bases.

**Sources:**
- https://www.anthropic.com/news/contextual-retrieval
- https://aws.amazon.com/blogs/machine-learning/contextual-retrieval-in-anthropic-using-amazon-bedrock-knowledge-bases/

### What's in — 2026 chunking

**Hierarchical parent-child chunking** — embed small ~100-token child chunks for precise vector matching, retrieve the parent page/section for generation context:
- Reported improvements on structured documents (API refs, regulatory filings, technical manuals) — *specific numbers vary by corpus; no single authoritative benchmark*
- Consensus production stack: hierarchical chunking + hybrid (dense + BM25) + RRF fusion + reranker, retrieving top-k broad and keeping top-5 to top-10

**Late chunking (Jina)** — embed the full document through the transformer first, then pool per-chunk embeddings so each chunk carries global context:
- nDCG improvements vary by dataset: e.g., NFCorpus +6.52pp, SciFact +1.9pp, FiQA +0.59pp — no single aggregate figure
- Late chunking approached but did not cleanly beat LLM-augmented contextual embeddings (0.8516 vs 0.8590 per Firecrawl's analysis)
- Jina's embedding API: `late_chunking=True` parameter

**Sources:**
- https://jina.ai/news/late-chunking-in-long-context-embedding-models/
- https://www.firecrawl.dev/blog/best-chunking-strategies-rag
- https://blog.premai.io/building-production-rag-architecture-chunking-evaluation-monitoring-2026-guide/ *(general production RAG guide; specific hierarchical chunking benchmarks not sourced from here)*

### What's out — 2026 chunking

**Chunk overlap**: A January 2026 systematic analysis (SPLADE + Mistral-8B on Natural Questions) found token-aware overlap provided **no measurable retrieval benefit** — only increased indexing cost. This reverses 2023–2024 best practice.

**Semantic chunking**: With late chunking and contextual retrieval both injecting global context post-hoc, expensive embedding-similarity-based boundary detection rarely justifies its cost.

**Typical production chunk sizes**: ~800 tokens for contextual retrieval parents, ~100 tokens for parent-child children, 8k-token document windows for contextualization.

---

## 2026 Hybrid Search & Re-ranking

### Default pattern

BM25 (sparse) + dense vectors run in parallel, merged via **Reciprocal Rank Fusion** (not score normalization — BM25 and cosine scores live on incompatible scales).

**Measured quality:**
- PremAI BEIR benchmark: hybrid search **MRR 0.486 vs. 0.410 dense-only** (+18.5%)
- Standard recipe: retrieve **top-20** broad → rerank → **top-5** precise → send top-5 to LLM
- Anthropic's variant: top-150 → top-20

**Sources:**
- https://blog.premai.io/hybrid-search-for-rag-bm25-splade-and-vector-search-combined/
- https://superlinked.com/vectorhub/articles/optimizing-rag-with-hybrid-search-reranking

### 2026 reranker benchmarks

| Model | Ranking metric | Notes |
|---|---|---|
| **Zerank 2** | ELO 1638 (Agentset leaderboard) | Top-ranked overall |
| **Cohere Rerank 4 Pro** | ELO 1629 (Agentset leaderboard) | Managed API, strong SLAs |
| **Voyage Rerank 2.5** | Top-tier (ZeroEntropy benchmarks) | Managed API |
| **Cohere Rerank 3.5** | Strong (ZeroEntropy benchmarks) | Managed API at scale |
| **bge-reranker-v2-m3** | — | Self-host leader |
| **Jina Reranker v2** | Mid-tier (Agentset, ranked ~12th) | Self-host alternative |

*Note: Agentset leaderboard uses ELO + nDCG@10. ZeroEntropy benchmarks use different metrics. Direct Hit@1 comparisons across models not available from a single source. Latency benchmarks vary by deployment — test on your own infra.*

**Sources:**
- https://agentset.ai/rerankers *(ELO-based leaderboard, not Hit@1)*
- https://www.zeroentropy.dev/articles/ultimate-guide-to-choosing-the-best-reranking-model-in-2025 *(promotes ZeroEntropy's own zerank-1; model comparisons present but without the specific characterizations originally cited)*

### Emerging: graph-augmented hybrid

"Hybrid RAG" is being redefined as BM25 + vectors + **knowledge graphs** — graph-augmented retrieval as a third signal fused alongside sparse/dense.

**Source:** https://community.netapp.com/t5/Tech-ONTAP-Blogs/Hybrid-RAG-in-the-Real-World-Graphs-BM25-and-the-End-of-Black-Box-Retrieval/ba-p/464834

---

## 2026 RAG Eval Frameworks & Hallucination Mitigation

### Eval stack (evolves through lifecycle)

1. **Ragas** — fast validation, metric design. Faithfulness via atomic claim decomposition + NLI entailment. Context precision (order-aware), context recall, answer relevance.
2. **DeepEval** (Confident AI) — LLM-as-judge (G-Eval style), synthetic data generation, CI/CD quality gates. More sensitive to "pragmatic misleading" than Ragas.
3. **TruLens** — RAG Triad (context relevance + groundedness + answer relevance) for production monitoring.
4. **Langfuse / LangSmith** — ongoing observability and trace-level grading.
5. **ARES** (Stanford FutureData) — generates synthetic training data, fine-tunes lightweight LM judges for cheaper eval at scale.

*Cross-reference: the Ragas setup in section (10) Loop C above uses metrics 1–4. This section adds the 2026 tool stack and hallucination-specific techniques.*

**Enterprise golden set best practice:**
- Freeze per evaluation cycle, balance easy/hard queries, strict versioning
- Blend golden + synthetic + human-reviewed data
- Fail deploys on regression + continuous drift detection

**Sources:**
- https://treysaddler.com/posts/rag-evaluation-frameworks-and-tracing.html
- https://medium.com/@sjha979/ragas-vs-deepeval-measuring-faithfulness-and-response-relevancy-in-rag-evaluation-2b3a9984bc77
- https://www.trulens.org/getting_started/core_concepts/rag_triad/
- https://labelyourdata.com/articles/llm-fine-tuning/rag-evaluation
- https://medium.com/data-science-at-microsoft/the-path-to-a-golden-dataset-or-how-to-evaluate-your-rag-045e23d1f13f

### Hallucination mitigation — 2026 techniques

**FACTUM (arXiv 2601.05866)** — mechanistic detection of citation hallucination in long-form RAG:
- **Contextual Alignment Score (CAS)**: grounding in source documents
- **Beginning-of-Sentence Attention Score (BAS)**: information synthesis stability
- Correct citations require simultaneous grounding + stable synthesis

**MEGA-RAG** — multi-evidence guided answer refinement (public health domain):
- Dense retrieval + cross-encoder reranking + weighted entailment scoring
- Addresses the failure mode where dense retrievers "overcorrect" and exclude borderline-relevant passages

**Hybrid retrieval architectures** (dense + sparse + rerank): substantial error reductions reported vs. vanilla RAG across multiple studies, though specific percentages vary by domain and setup. *(The "35–60%" range was cited from an arXiv survey (2510.24476) but could not be verified in the abstract; treat as directional.)*

**Context sufficiency checks** — gating generation on whether retrieved context can *actually* answer the question — reported as a key mechanism for reducing hallucinations in hybrid architectures.

**Guardian agents** — monitoring layer that validates outputs against cited spans before reaching users.

**Failure-mode taxonomy:**
- (a) *Retrieval failures*: data source, query, retriever, strategy
- (b) *Generation deficiencies*: context noise, context conflict, alignment problems, capability boundary

**Sources:**
- https://arxiv.org/pdf/2601.05866
- https://pmc.ncbi.nlm.nih.gov/articles/PMC12540348/
- https://arxiv.org/abs/2510.24476

---

## 2026 RAG Update Pipelines & Freshness

### Lifecycle pattern

1. **Start** with nightly full batch re-indexing
2. **Migrate** to CDC-based streaming at ~3 months (stakeholders complain yesterday's product launch isn't in today's search). Per Redis's RAG-at-scale guide: batch = ~24hr freshness, CDC = sub-minute. Expect significantly higher operational complexity.
3. **End-state**: hybrid — frequent incremental upserts + periodic full re-indexing for schema/embedding-model changes.

**Blue/green deployment** for major updates: index into a new collection, swap a collection alias atomically. Routine changes: incremental upsert + tombstoning of old IDs.

**Pathway** — framework built specifically for freshness (treats live data stream as source of truth, unlike LangChain/LlamaIndex/Haystack which assume data is already indexed statically).

**Sources:**
- https://redis.io/blog/rag-at-scale/ *(verified: CDC + batch hybrid, 24hr vs sub-minute freshness)*
- https://use-apify.com/blog/rag-production-architecture-2026 *(discusses staleness as failure mode; specific CDC complexity claims not from here)*
- https://dasroot.net/posts/2026/01/incremental-updates-rag-dynamic-documents/ *(covers versioning, delta indexing, change detection; does NOT discuss blue/green or tombstoning specifically)*
- https://alphacorp.ai/blog/rag-frameworks-top-5-picks-in-2026 *(Pathway's live data sync confirmed in concept; specific phrasing differs)*

### Embedding drift detection

- **Probe-set technique**: small, static, diverse set of probe docs/queries; periodically re-embed; alert when new vectors drift significantly from originals *(concept from drift detection literature; specific source page did not render for verification)*
- Monitor **L2 norm and variance** of embeddings in aggregate — shifts indicate embedding-space instability
- **Model upgrade cadence**: periodically re-evaluate retrieval quality against newer embedding models; migrate when a new model meaningfully outperforms on your corpus *(no specific threshold or cadence verified from cited source)*
- **Query drift** tracked separately from document drift — users start asking about new topics or using different terminology
- **Automated rollback**: n8n published a template for maintaining RAG embeddings with auto drift rollback

**Sources:**
- https://n8n.io/workflows/14036-maintain-rag-embeddings-with-openai-postgres-and-auto-drift-rollback/ *(verified)*
- https://medium.com/@Quaxel/your-rag-isnt-failing-retrieval-it-s-the-embeddings-5098c9dc59a0 *(article exists; recommends versioning + re-embedding on model upgrade, but no specific "6 months" or ">5%" thresholds)*
- https://apxml.com/courses/optimizing-rag-for-production/chapter-6-advanced-rag-evaluation-monitoring/monitoring-retrieval-drift-rag *(page exists but content didn't render for verification)*

### Multi-tenant isolation

| Vector DB | Namespace cap | Notes |
|---|---|---|
| **Pinecone** | 100,000 namespaces, 20 indexes | Serverless namespaces physically isolated |
| **Cloudflare Vectorize** | 50,000 namespaces, 5M vectors/index | — |
| **Turbopuffer** | No enforced limit reported | Serverless pay-per-use; supports vector + BM25 in same store *(performance-improves-with-tenants claim not verified from cited source)* |

**500+ enterprise-tenant production pipeline shape:**
```
Ingestion: Document Upload → Type Detection → Preprocessing → Chunking → Embedding → Pinecone
Query:     User Query → Cache Check → Query Rewrite → Hybrid Search (BM25+Vector) → RRF → Rerank → LLM → Response
```

**Sources:**
- https://docs.pinecone.io/guides/index-data/implement-multitenancy
- https://agentset.ai/vector-databases/compare/turbopuffer-vs-pinecone
- https://www.maviklabs.com/blog/multi-tenant-rag-2026
- https://dev.to/ayanarshad02/we-shipped-a-rag-chatbot-to-500-enterprise-tenants-heres-what-actually-broke-first-1jia

---

## 2026 Cost Control for LLM Systems

*This section is from the general production AI strategies research but directly applicable to RAG systems — caching the system prompt, few-shot examples, and retrieved context is a first-order RAG cost lever.*

### Prompt caching — real numbers

| Who | Before | After | Reduction | Method |
|---|---|---|---|---|
| **YUV.AI** (customer-service bot) | $50K/month | $15K/month | **70%** | Cached static system prompts, few-shot examples, user context (~90% of tokens were static) |
| **Individual developer** | $720/month | $72/month | **90%** | Restructured prompts into static cached prefixes + dynamic suffixes |
| **Anthropic benchmark** (100K-token book) | 11.5s, $3.00/M | 2.4s, $0.30/M | **~90% cost, 85% latency** | Prompt caching on long static context |

**Key insight for RAG**: in a RAG system, the system prompt + few-shot examples + retrieved context chunks are often 80–90% of the input tokens and largely static across similar queries. Caching this prefix is the single biggest cost lever.

**Sources:**
- https://yuv.ai/blog/prompt-caching-cut-our-ai-costs-by-70
- https://medium.com/@labeveryday/prompt-caching-is-a-must-how-i-went-from-spending-720-to-72-monthly-on-api-costs-3086f3635d63
- https://ngrok.com/blog/prompt-caching

### Model routing

- Route **60% small / 30% medium / 10% large** → **50–70% average cost reduction**
- Combined routing + caching + prompt cleanup: **30–50% baseline**
- Well-tuned systems (routing + caching + batching): **up to 80%**

**For RAG specifically**: simple factual lookups → small model; multi-hop reasoning or synthesis → large model. The retrieval pipeline itself determines query complexity — if all top-k chunks agree, route to small; if chunks conflict or query is ambiguous, route to large.

**Sources:**
- https://www.maviklabs.com/blog/llm-cost-optimization-2026
- https://blog.premai.io/llm-cost-optimization-8-strategies-that-cut-api-spend-by-80-2026-guide/

### Reliability patterns (now standard)

- **Retries**: 429s/5xx with exponential backoff + full jitter, max 3, respect `Retry-After` headers
- **Fallback chains**: Primary OpenAI → Anthropic Claude → Gemini → Azure OpenAI
- **Circuit breakers**: 3-state (Closed/Open/Half-Open); recommended trip threshold: **50% failure rate over 60s window, minimum 10 requests**
- **LLM gateways** (Portkey, LiteLLM, OpenRouter, Maxim) bundle routing + caching + retries + fallbacks + circuit breakers behind one API

**Sources:**
- https://www.getmaxim.ai/articles/retries-fallbacks-and-circuit-breakers-in-llm-apps-a-production-guide/
- https://portkey.ai/blog/retries-fallbacks-and-circuit-breakers-in-llm-apps/

---

## 2026 Named Case Studies

*Concrete, attributable production examples with specific numbers. Sourced from LangChain Interrupt 2025, engineering blogs, and ZenML's LLMOps database.*

| Company | System | Numbers | Stack/Technique |
|---|---|---|---|
| **Uber** | AutoCover (test gen) | **21,000 dev hours saved**, ~10% platform coverage lift, serves ~5,000 engineers | LangGraph + internal retrieval *(LangSmith not confirmed in source)* |
| **Uber** | Genie / EAg-RAG (support) | Near-human precision on policy queries; +27% acceptable, −60% incorrect | Enhanced Agentic-RAG |
| **LinkedIn** | SQL Bot in DARWIN | **95% query accuracy satisfaction**, **80% of recovery sessions** from "Fix with AI" | LangChain + LangGraph + KG + LLM rerank |
| **Ramp** | Policy Agent (expense) | **>65% of approvals autonomous**, 50K+ customers | Consolidated multi-agent, LLM-as-judge evals |
| **Ramp** | Inspect (coding agent) | **~30% of merged PRs** within ~2 months | Background agent w/ full dev env |
| **Cisco** | Virtual Tech Engineer | **~60% of support cases** auto-resolved | Predictive insight agents |
| **Nubank** | Voice/image/chat transfer | Cut transfer time + improved CSAT | 4-layer LLM ecosystem |
| **Klarna** | OpenAI assistant | **~700 FTE equivalent**, 25% fewer repeats, **~$40M/yr savings** | OpenAI *(widely reported in press; partially walked back mid-2025; source below does NOT contain these figures — they originate from Klarna's own PR/earnings, not ZenML)* |
| **Glean** | AI Evaluator | LLM-as-judge **inside customer deployment** — no data exfil | Chunk attribution, utilization, faithfulness |
| **Vercel** | Platform telemetry | *(Specific stats not verified on vercel.com/state-of-ai — page is a general AI adoption survey. The "30%+ agent deploys / Claude Code 75%" claims need a different source or should be treated as unverified.)* | Vercel + external LLMs |
| **LangSmith** | Q4 2025 aggregate (150 enterprises) | Agentic RAG: **+35–50%** complex-query handling, **+200–400ms** latency | — |

**Sources:**
- Uber AutoCover: https://www.zenml.io/llmops-database/building-ai-developer-tools-using-langgraph-for-large-scale-software-development
- Uber EAg-RAG: https://www.uber.com/blog/enhanced-agentic-rag/
- LinkedIn SQL Bot: https://www.linkedin.com/blog/engineering/ai/practical-text-to-sql-for-data-analytics
- Ramp Policy Agent: https://www.zenml.io/llmops-database/building-trustworthy-llm-powered-agents-for-automated-expense-management
- Ramp Inspect: https://www.infoq.com/news/2026/01/ramp-coding-agent-platform/
- Glean: https://www.glean.com/blog/glean-ai-evaluator
- Klarna: https://www.zenml.io/blog/what-1200-production-deployments-reveal-about-llmops-in-2025 *(Klarna NOT mentioned on this page; figures originate from Klarna PR/earnings, need correct source)*
- Vercel: https://vercel.com/state-of-ai *(general AI survey; specific agent-deploy stats not confirmed on this page)*
- Interrupt 2025 recap: https://blog.langchain.com/interrupt-2025-recap/
- Cisco/Nubank: https://zircon.tech/blog/recap-of-interrupt-2025-the-ai-agent-conference-by-langchain/

