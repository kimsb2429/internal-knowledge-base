# TODO — internal-knowledge-base

## Completed
- [x] Step 1: Pick first corpus (M22-3, M22-4 from KnowVA + VADIR ICD)
- [x] Step 2: Build golden query set (110 queries, validated)
- [x] Build KnowVA crawler (scripts/crawl_knowva.py)
- [x] Validate golden set (faithfulness 0.93, correctness 0.997, relevance 0.993)

## Zero-to-MCP Progress

Canonical plan: `docs/2026-04-11-engineering-rag-evidence-and-howtos.md` § "From Zero to Knowledge MCP"

> **Public-demo ship-cut (2026-04-15):** optimization paused. The remaining HyDE/CRAG/Loop B / freshness / multi-tenancy work is deferred until *after* the public RAG+MCP demo ships. Current eval scores (Faith 0.95 / AnsRel 0.91 / CtxPrec 0.61 / CtxRec 0.52 / CtxRel 0.56) are already the story. Pre-launch ship-cut (MCP server + eval-in-CI + failing-then-passing PR + Langfuse traces + guardrails + public repo) is tracked in `~/consulting-research/docs/rag-demo/README.md` under "Ship-cut v1". Post-launch spokes listed there map back to specific items parked below. **Exception:** Step 12 k-sweep is diagnostic (not tuning) — still worth doing before launch if a spoke needs the interpretation.

- [x] Step 1: Pick first corpus
- [x] Step 2: Build golden query set
- [x] Step 3: Bronze layer (metadata enrichment)
- [x] Step 4: Guardrails — ship-cut v1 subset: input validation (empty-query reject, MAX_QUERY_CHARS=2000), k clamp (MAX_K=20), rerank_from clamp (MAX_RERANK_FROM=100). Deferred to post-ship: secret/credential regex at ingestion, PII NER, permission-scoped retrieval.
- [x] Step 5: Parsing layer (PDF only — HTML articles skip markdown, go straight to HTMLHeaderTextSplitter)
- [x] Step 6: Metadata schema (pgvector) — Docker, port 5433, mxbai-embed-large 1024 dims
- [x] Step 7: Chunking pipeline — 9,315 chunks (7,113 text, 1,444 table, 758 list), 0 errors. Custom HTML splitter preserves table structure. Generic chunker + `knowva_preprocess.py` for source-specific quirks. Row-group splitting for tables >50K. Max chunk: 49,708 tokens.
  - [x] Row-group splitting for large tables (was Loop A candidate) — all tables >50K now split with repeated headers
- [x] Validate chunks using independent subagents — 4 parallel subagents caught multi-table chunks, misclassified lists, list fragments, threshold-gap; all fixed
- [x] Step 8: Embed and store — 238 documents, 9,315 chunks in pgvector. Heading-only `embed_text` for oversized chunks (title + heading_path). mxbai-embed-large via sentence-transformers. $0 API cost (deferred LLM summary indexing to Loop A if eval shows need).
- [x] Step 9: Eval harness — DeepEval w/ Haiku judge. Scripts: retrieve / generate / run_eval / score_eval / audit_golden_set. Golden set bug-fixed (14 VADIR ID mismatches + 4 query bugs + 2 JSON parse errors). v2b baseline on full 110q: Faith 0.97 / AnsRel 0.83 / CtxPrec 0.40 / CtxRec 0.45 / CtxRel 0.43.
- [x] Loop A iteration: HTML cleanup (lxml-html-clean preserves colspan/rowspan; HtmlRAG strips them)
- [x] Loop A iteration: Option B (BS4 cleanup AFTER chunking) — boundaries identical to v1, -20.6% tokens, recall flat
- [x] Loop A iteration: Contextual Retrieval (Anthropic Batches API, 5,978/6,142 chunks, $12.48). Re-embedded with contextualized embed_text. **v2bcr+rerank scores: Faith 0.95 / AnsRel 0.91 / CtxPrec 0.61 / CtxRec 0.52 / CtxRel 0.56.** Modest incremental lift on top of rerank (AnsRel +4.8pp, CtxPrec +4.1pp); Anthropic's published +35% recall did NOT replicate at our scale.
- [x] Step 11: Reranker — mxbai-rerank-base-v2 with 2K-char input cap (fixes 27GB OOM). Full 110q lift: CtxPrec +16.5pp, CtxRel +11.8pp, CtxRec +5.3pp.
- [x] Eval cadence: fast/medium/full tiers built. `--fast` + `--baseline` flags in run_eval.py with cheap proxies (keyword recall, IDK rate, token cost, source match). 5-10 min vs 2h iteration.
- [ ] **Re-batch the 164 failed contextualization chunks** — small follow-up; --resume flag handles it
- [ ] Loop A candidate: if content-level queries against oversized tables fail at eval, add LLM summary indexing OR `retrieve_full_doc` MCP method
- [ ] Loop A candidate (from random chunk inspection): base64/binary blob detector + image-only chunk filter (~30 lines, surfaces unembeddable noise)
- [ ] Loop A candidate: raise `MERGE_THRESHOLD` from 50 → ~300 to pull median chunk size from 194 → ~500 tokens (60% of chunks currently <300 tokens)
- [ ] **Bench Microsoft `markitdown` vs current PDF/HTML pipeline** — converts PDF/DOCX/PPTX/HTML→Markdown for LLM context (3.6K stars in first week, April 2026). Most relevant for VADIR ICD PDF path (currently `MarkdownHeaderTextSplitter`) and any future DOCX/PPTX corpora. Compare table fidelity (colspan/rowspan preservation) before considering swap — custom HTML splitter exists explicitly because markdown loses table structure, so verify markitdown doesn't regress that. Source: https://github.com/microsoft/markitdown
- [x] **Step 12: K-sweep diagnostic** — ran fast eval at k ∈ {3, 5, 10, 20, 50}. **Verdict: ranking-bound, not index-bound** (top-1 frozen at 0.533; recall climbs monotonically 0.80 → 0.933 at k=50). Decision: hybrid (BM25+dense+RRF) is next Loop A iteration; HyDE deprioritized. Deferred to post-ship.
- [ ] Step 13: Add HyDE (was Step 12)
  - [ ] When doing HyDE, also document production shape in plan doc: boolean MCP parameter `use_hyde: bool = True`, default on, consumer-togglable. Exceptions to flag-gate: doc-voice queries, cached/repeat queries, multi-stage agent queries, ultra-short 1-2 word queries, cost-sensitive consumers. Optional cheap gate: skip HyDE when top-3 cosine scores > 0.8 already.
- [ ] Step 14: Add CRAG (was Step 13)
- [ ] Loop B: Tune retrieval (full sweep after HyDE/CRAG, includes latency + cost)
- [x] **Step 16: MCP server (v1)** — FastMCP 3.2.4. `scripts/mcp_server.py` with Tools (`query`), Resources (`document://{source_id}`), Prompts (`cite_from_chunks`). Guardrails, `auth_context` gateway seam, stdio↔HTTP transport toggle. 7/7 smoke tests pass (`scripts/test_mcp_server.py`). OTel→Langfuse Cloud wired with input/output capture on tool-call span.
- [x] **Hybrid-ready schema** — `content_tsv` GENERATED column + GIN index on `document_chunks`. All 6,489 rows auto-populated. Backs the README scaling-table claim without BM25 wiring.
- [x] **pg_dump backup** — 30MB snapshot at `~/ikb-backups/ikb-20260415-1705.dump`. Survives Docker factory reset.
- [x] **Docs-vs-code RAG adjudication** — `docs/deep-dive/2026-04-16-docs-vs-code-rag-adjudication.md`. Subagent-parallel DAG (6 sub-questions). Resolved the tension between Claim A (unified scaffolding) and Claim B (code is different). Surfaced that GrepRAG's baseline set is thin; tightened the repo's own overclaims.
- [ ] **Ship-cut v1 remaining** (see `~/consulting-research/docs/rag-demo/README.md` § "Ship-cut v1" + § "Launch sequence"):
  - **Launch instrumentation** (defined 2026-04-18, refined 2026-04-21): success criteria + hurdle ladder + tracking scaffold live in `~/consulting-research/docs/rag-demo/` (`README.md` § Success criteria, `tracking.md`, `hurdle-playbook.md`). **Phased approach:** Phase 1 GitHub → Phase 2 Medium → Phase 3 coordinated launch → Phase 4 website upgrade (deferred). Pre-launch infra checklist in `tracking.md` is now **minimal v1** (no PostHog, no case page, no Cal.com — all deferred until post-launch signal warrants them).
  - **README scope: ~150 lines (lighter)** — repo-level reference only (hero, quickstart, architecture diagram, eval block, repo structure, link to Medium writeup). The demo's full thinking lives in the Medium writeup, not the README.
  - [x] Eval wired to GitHub Actions as merge gate — **LIVE on main** (commit `f0d912a`, PR #4). FlashRank MiniLM reranker (22M ONNX, ~2s/query), two-phase run_eval.py (serial rerank + parallel Sonnet @ concurrency 8), fixture DB + baseline JSON committed, `scripts/check_regression.py` enforces proxies (top1/topk: −5pp, keyword_recall: −5pp, idk_rate: +10pp). First green CI: 3:53. See docs/demo-prep-raw.md Act 30 Moments 38-42.
  - [x] Failing-then-passing PR (highest-signal artifact) — **merged as PR #5** (squash `6821d26`). Red run 24540768938 (top1 -20pp, rerank dropped), green run 24540937417 (rerank restored + push paths filter added). Net main diff: 6-line paths filter only (regression cancels out in squash). The PR's Actions tab is the forever-artifact.
  - [x] Langfuse public trace link — showcase trace live at `https://us.cloud.langfuse.com/project/cmo0wah7a00pfad071nk6x84c/traces/a574193bbff7d5438f7fae9e27f4bb83`. `scripts/make_trace_public.py` flips any trace ID via Langfuse ingestion API.
  - [ ] Public README with 8-dim scaling table + docs-vs-code caveat + Accenture line
  - [ ] Public GitHub repo (MIT) + `docker compose up` repro + PulseMCP listing (same repo as-is, no fork)
  - [ ] **Polish:** add `_meta = {"anthropic/maxResultSizeChars": 500000}` to `@mcp.tool query` and `@mcp.resource document://{source_id}` responses (Claude Code v2.1.91+, Apr 2 2026). ~2 lines. Fixes silent truncation when a viewer clones the repo and plugs into Claude Desktop on large documents (some VA manuals are 100K+ chars). Verify feature exists at claimed version before adding.
- [ ] **Post-launch spokes added** (park until anchor has SERP data):
  - [ ] "Where the unified RAG pattern stops working: the docs-vs-code retrieval boundary"
  - [ ] "The router that isn't: why LLM-as-router via MCP tool affordances beats explicit query classifiers"
- [ ] Step 17: First consumer app (post-ship)
- [ ] Steps 18-20: Instrument
- [ ] Step 21: Freshness
- [ ] Loop C: Learn
- [ ] Step 23: Validate eval
- [ ] Loop D: Scale sources
- [ ] Loop E: Tune consumers
