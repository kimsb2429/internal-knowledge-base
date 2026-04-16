# Demo Prep — Raw Material from Sessions

Extracted moments, narratives, and artifacts from the session that demonstrate RAG pipeline construction capabilities. For both video walkthrough and written case study.

---

## Launch-prep capture checklist

Items to gather or produce as ship-cut work progresses (see `~/consulting-research/docs/rag-demo/README.md` § "Ship-cut v1"). **Future agents: when you complete any of these, append the artifact to this doc as a new `### Ex.` entry and update the relevant raw-stats subsection.**

### Measurement gaps — data exists or is cheap to generate

1. **Per-`query_type` segmented eval numbers** (highest-impact). Aggregates for v2bcr+rerank are captured; the segmented breakdown (lookup, synthesis, cross_source, temporal, contradiction, negative, ambiguous_term, prod_ops, consulting_sme, table_lookup) is not. Produce it + 2–3 representative failures per low-scoring class. The post-eval protocol in `CLAUDE.md` is mandatory — capture the output verbatim.
2. **Before/after on ONE specific query** — pick from the 110-query golden set: a query where baseline retrieval missed and v2bcr+rerank nailed it. Preference order: table-embedded answer > heading-dependent > cross-source synthesis. Capture both top-5 chunks + both generated answers side-by-side. Becomes the *anchor query* for README hero + video cold-open + Reddit lede.
3. **IDK rate / refusal behavior by query type** — golden set has negative queries. Break out IDK rate by class; include 2 examples of correct refusals. Under-documented in public demos, high production signal.
4. **Per-query cost breakdown** — `embed($X) + retrieve($Y) + rerank($Z) + generate($W) = $N`. Extrapolate: 10K queries/month = $M, 1M = $K. Same for ingestion: $12.48 contextualized 6K chunks → project to 1M chunks ≈ $2K one-time. Feeds the pilot-to-prod scaling table directly.
5. **Latency numbers** — p50/p95 retrieval, p50/p95 end-to-end. Langfuse captures once instrumented. Screenshot 1–2 canonical traces.
6. **HyDE-skip reasoning as a standalone demo moment** — the pieces are in Act 24 (k-sweep) but scattered. Promote to a single angle: *"K-sweep showed ranking-bound not index-bound — raising `rerank_from` 20→50 is the better lever than HyDE."* Save as a clean quotable + raw stats block.

### Will exist only after ship-cut build — capture when created

7. **Langfuse trace screenshots** — 3 canonical captures: simple lookup, table-embedded answer, cross-source synthesis. Each showing query → retrieved chunks → generated answer → tokens + cost + timing. Save raw images in `docs/demo-assets/` or similar.
8. **Failing-then-passing PR** — the ship-cut's highest-signal artifact. Capture: PR URL, failing CI run log, the diff of the fix, merged PR URL. Save as `### Ex. [next letter]: Merge-gate blocks a CtxRec regression`.
9. **Guardrail examples** — one rejected input (schema-invalid or obviously malicious), one output validation catching a bad response. Save actual traces / response bodies with explanatory context.
10. **Claude Desktop MCP screen recording** — actual capture of the MCP server being called from Claude Desktop. Run the anchor query end-to-end, tool invocation visible. Raw video + 1–2 still frames.

### Nice to have — not required for launch, capture opportunistically

11. **Concurrency / throughput stress test** — label in demo as "untested at scale; architecture is stateless, MCP layer horizontal-scales." Only run if time allows before launch.
12. **Ingestion throughput** — docs/hour for onboarding a new source. Useful talking point for the pilot-to-prod gap discussion but not load-bearing.

### Already well-covered — do NOT add more

- Reranker methodology and numbers (Act 17–18, Ex. CC–DD)
- Contextual Retrieval letdown data (Act 20, Ex. EE)
- Black-box validation pattern (Acts 11, 12)
- HtmlRAG / LangChain honest critiques (Acts 15, 16, Ex. T, Ex. AA)
- Golden-set methodology + bug audit (Acts 2, 10, Ex. Y, Z)
- Chunking decisions and refactor (Acts 6–9, Ex. Q–R, V–X)

Additional acts or examples in these categories are not needed — 25 demo moments + 40+ Ex. references is already more than 12 months of Tier-2 spoke content.

---

## Narrative Arc

**Setup:** Client has VA Education Service manuals on a JavaScript SPA (KnowVA) and a PDF ICD document. Needs a RAG knowledge base with evaluation.

**Act 1 — Reverse-engineering the data source** (crawler discovery)
- KnowVA is a JavaScript SPA (eGain platform) — no static pages to wget
- Walked through Chrome DevTools together to find the API ([Ex. I](#ex-i-devtools-api-discovery))
- Discovered the eGain v11 XML API by intercepting XHR calls
- Key moment: finding the `$level` parameter that unlocks the full topic tree — no headless browser needed ([Ex. J](#ex-j-level-parameter-discovery))
- XML had namespace prefixes (`ns2:`), article IDs as attributes (not child elements), content as XML-escaped HTML — each required a debug iteration ([Ex. K](#ex-k-xml-namespace-surprises))
- Built a pure-API crawler that politely downloads 237 articles with structure preserved ([Ex. L](#ex-l-crawler-output-structure))

**Act 2 — Building the golden evaluation set** (domain expertise + AI)
- Created 110 queries across 5 personas: VCE (claims examiner), consulting SME, prod ops, new hire, auditor
- Cross-source queries that require stitching M22-3 + M22-4 + VADIR ICD
- Deliberately wrote queries in natural domain language ("the service record shows...") instead of naming systems ("VADIR returns...") — tests semantic retrieval, not keyword matching ([Ex. M](#ex-m-domain-language-rewrites))
- Iteratively refined query voice: textbook → cross-source → consulting SME → prod ops → domain-language ([Ex. N](#ex-n-query-voice-progression))

**Act 3 — Metadata enrichment that the CMS didn't do** (Step 3)
- Audited all metadata requirements from the pipeline docs — gap analysis between what's needed and what exists
- Fixed heading extraction: KnowVA CMS uses `<a name>+<strong>` instead of `<h2>`-`<h6>`. Wrote a fallback parser that handles 3 different HTML patterns including words split across tags ([Ex. B](#ex-b-html-heading-patterns))
- Went from 0% heading coverage to 100% (1,863 headings across 237 articles) ([Ex. C](#ex-c-heading-extraction-beforeafter))
- Added acl, source_authority_tier, content_category — then simplified content_category from 5 categories to 1 (`gov_docs_and_manuals`) after realizing the intra-manual distinctions were over-engineering for content that all decays at the same rate ([Ex. D](#ex-d-enriched-metadata-json))
- Dropped the `keywords` field entirely — KnowVA authors barely tagged anything, and title/breadcrumb/headings carry the signal ([Ex. A](#ex-a-dropped-keywords))

**Act 4 — Parsing to markdown with validation** (Step 5)
- HTML articles: markdownify preserves tables as pipe tables, headings, lists, links ([Ex. E](#ex-e-parsed-markdown-table), [Ex. F](#ex-f-parsed-markdown-prose))
- PDF: Docling with TableFormerMode.ACCURATE — took 15+ minutes on a MacBook Air, but extracted all ICD data tables correctly
- Post-processed PDF to strip cover page OCR junk and tripled Table of Contents (62K of noise) ([Ex. G](#ex-g-pdf-noise-stripped))
- Ran independent black-box validation subagents: 20-article HTML sample + full PDF comparison
- HTML validation caught colspan issue: 54 articles have broken pipe tables from merged cells (445 rows). Community research confirmed no clean fix — deferred to context blurbs in chunking step ([Ex. H](#ex-h-colspan-broken-table))
- PDF validation confirmed all content preserved but found split tables at page breaks and flat heading hierarchy

**Act 5 — "Why are we embedding tables at all?"** (design challenge)
- First brain asked a fundamental question: how does a one-sentence query vector match a paragraph-long chunk vector?
- Followed up: if the context blurb gets averaged into the whole chunk embedding, doesn't its signal get diluted?
- This led to: tables are a fundamentally different retrieval problem than prose — they shouldn't be embedded as text at all
- Proposed: extract tables, store separately, embed a natural-language description instead, leave a pointer in the prose chunk
- Challenged: "I'm confused why this is my idea and not the industry standard" — turns out it IS the standard (LlamaParse, Unstructured, Docling all do element-type separation)
- Deeper challenge: the project's own research docs already identified this pattern but the build plan used "context blurbs" as a shortcut instead ([Ex. O](#ex-o-research-knew-but-plan-didnt))
- Also identified two more gaps: hybrid search and contextual retrieval were in the research and schema but missing from the build steps
- Added HyDE and CRAG to the plan as Steps 12-13 — industry standard post-retrieval improvements deferred to iteration loops ([Ex. P](#ex-p-zero-to-mcp-updated-outline))

**Act 6 — "Just skip the markdown"** (design simplification, Steps 6-7)
- Started with the plan: HTML → markdown → MarkdownHeaderTextSplitter. But why?
- Tables break in markdown (colspan). Prose looks the same. LLMs read HTML fine.
- First brain asked: "is markdown that much better than html for non-tables?" — answer was no
- Killed the markdown conversion for HTML articles entirely. One code path: HTMLHeaderTextSplitter directly on HTML
- But KnowVA uses `<a name>+<strong>` instead of proper heading tags — HTMLHeaderTextSplitter can't split on those
- Built `knowva_heading_fix.py` to pre-process: converts 4,963 anchor patterns to proper `<h2>`/`<h3>`/`<h4>` tags ([Ex. Q](#ex-q-heading-fix-before-after))
- But then discovered LangChain's `HTMLHeaderTextSplitter` **strips all HTML tags** from output — tables come out as `Name Code Army A`. Defeats the entire purpose of staying in HTML ([Ex. T](#ex-t-langchain-strips-tables))
- Built a custom HTML splitter that splits at heading boundaries while preserving raw HTML in chunk content
- Deleted `parse_html_to_markdown.py` — the whole script became obsolete
- Created `docs/preprocessing.md` as a reference manual instead of a monolithic preprocessing script — each source has different quirks, so document what was done rather than pretend one script handles everything

**Act 7 — "That's not element-aware chunking"** (heading-only → true element-aware)
- First run: 3,000 chunks, but mixed-content sections (prose + tables under one heading) stayed as single chunks
- A 187K-token "table" chunk was actually 15 small tables interspersed with 14K chars of prose — `detect_chunk_type` labeled the whole thing as "table" because `<table` appeared anywhere in it
- First brain: "how did we get mixed content in the first place? aren't we doing element-aware chunking?" — we weren't. We were doing heading-aware chunking.
- Added second pass: split at `<table>` and `<ul>`/`<ol>` boundaries within each heading chunk. Tables and lists become their own chunks, prose stays grouped.
- First brain caught a subtlety: splitting small `<ul>` into its own chunk wastes embedding space — but the existing merge step (50-token threshold) handles that automatically
- Oversized prose/lists get split further with `RecursiveCharacterTextSplitter` (800 tokens, 100 overlap). Only oversized tables stay whole for summary indexing.
- Final result: 8,399 chunks (6,890 text, 748 table, 761 list), 548 oversized tables, 0 errors ([Ex. R](#ex-r-chunk-distribution))

**Act 8 — Summary indexing for oversized chunks** (design decision)
- 548 oversized tables, largest at ~175K tokens
- First brain asked "does this work even for that extra large table?" — it doesn't for generation (can't return 175K tokens as context), but the 10 tables over 50K are deferred to Loop A (row-group splitting)
- For the 538 tables in the 1K-50K range: generate an LLM summary, embed the summary (good for retrieval), return the full table to the LLM at query time (good for generation)
- Key insight from first brain: "so we create an intentional mismatch between the embedded vector and the content" — yes, that's the whole point. The vector is optimized for findability, the content for answerability ([Ex. S](#ex-s-summary-index-schema))

**Act 9 — Archived content: historically accurate, not less authoritative** (metadata design)
- 29 articles are archived (superseded policy, kept for historical reference)
- Initial thought: lower `authority_tier` to deprioritize. But first brain caught it: "does authority tier respect historical accuracy? like, the law would have applied to someone in 2018"
- Archived content isn't wrong — it's temporally scoped. A veteran who filed in 2018 was subject to the pre-2019 policy.
- Decision: keep `authority_tier: 1`, add `archived: true` + `archived_date`. Let `last_modified × freshness_decay` naturally deprioritize for current-policy queries. Generation prompt frames it: "this source is archived as of 6/11/19"

**Act 8 — Open-source embedding model** (stack decision)
- Original plan was AWS Bedrock Titan V2 ($0.02/M tokens)
- First brain asked for an open-source equivalent — selected mxbai-embed-large (1024 dims, same as Titan V2) via HuggingFace/sentence-transformers
- Zero API cost, runs locally, no schema changes needed

**Act 9 — pgvector schema** (Step 6)
- Docker Compose with pgvector/pg17, port 5433
- `documents` table (source metadata, raw content, `last_modified` for freshness decay)
- `document_chunks` table (`content` for LLM, `embed_text` for what was embedded, `embedding` vector(1024))
- First brain caught missing `last_modified` field — was in the original plan doc (line 629) but I'd omitted it
- Dropped `contains_table` and `total_chunks` after first brain challenged their purpose — both were speculative

**Act 10 — Catching our own hallucinations** (eval-before-trust)
- Ran 3 parallel validation subagents: faithfulness, correctness, relevance
- Caught a compounding hallucination: fabricated "SAO→SOAR transition Oct 1, 2023" → propagated to 4 other answers
- Fixed all contaminated answers, re-ran validation, scores improved across the board
- The pipeline caught its own errors before they became the benchmark

**Act 11 — "Black-box validate the chunks too"** (validation pattern reused)
- Spun up 4 parallel subagents, each with a single validation mandate and no access to the chunking code — only the 8,399 output chunks
- Agent 1 (table structure): Found 46 chunks with 2+ complete `<table>` blocks — the splitter wasn't handling sibling/nested tables
- Agent 2 (heading paths): PASS — 229 empty heading paths all traced to chunk_index=0 breadcrumb content, no structural issues
- Agent 3 (type classification): Found 22 list chunks with zero list HTML (misclassified) + 25 list fragments missing wrapper tags
- Agent 4 (oversized flagging): Found threshold was effectively `>1024` not `>1000` — 20 chunks in the 1,002–1,024 band unflagged
- Each subagent ran black-box with no knowledge of implementation — same pattern as golden set validation ([Ex. U](#ex-u-blackbox-chunk-validation))

**Act 12 — "Isn't the whole point of element-aware chunking to handle this?"** (the multi-table bug)
- First brain's reaction to the multi-table finding: "I thought each table was small, isn't that intentional?"
- Investigation: zero of the 46 were small-merge cases. All had at least one large sub-table.
- Root cause: `split_chunk_by_elements` iterated `soup.children` — only top-level. When tables were nested inside `<div>` wrappers, the splitter never saw them individually.
- Fix #1: recursive `_extract_boundary_elements` unwraps `<div>` wrappers to surface nested tables ([Ex. V](#ex-v-div-wrapped-tables))
- Fix #2: re-detect `chunk_type` on sub-chunks after oversized splitting — the 22 misclassified lists came from `RecursiveCharacterTextSplitter` stripping HTML from oversized lists, then the pre-split type being applied to fragments that were now just prose
- Result: 46 → 4 sibling-table cases fixed. 42 remaining are table-inside-table (layout nesting, can't split without breaking structure). 0 misclassified lists.

**Act 13 — "Industry standard for large tables?"** (scope of the row-group split)
- 10 tables still over 50K tokens, largest at 175K — summary indexing breaks down because the full content can't be served at generation time
- First brain: "What's the industry standard way of dealing with it?"
- Answer: row-group splitting with repeated headers. Each chunk = header row(s) + a group of data rows, self-contained.
- Built a generic `split_table_by_row_groups()` for any table over 50K tokens
- First brain: "Do we need another metadata field that says 'there's more'?" — no, retrieval handles continuation naturally (multiple row-groups score high together), and parent-linking metadata is overkill until eval proves it matters
- Result: max chunk size dropped from 175K to 49K after row-group splitting

**Act 14 — "How much of this is specific to our source?"** (the refactor)
- First brain caught the creep: "are there any aspects of this chunker that feel very specific to our source docs and not really generalizable?"
- Audit: layout-table detection, `<div>`-wrapper recursion, and `"| ---"` markdown table detection all leaked source-specific logic into the generic chunker
- Correct architecture: generic chunker + source-specific preprocessors. New sources get a thin preprocessor, not a chunker fork.
- Moved all source-specific normalizations into `knowva_preprocess.py` (renamed from `knowva_heading_fix.py`): layout-table unwrapping + `<div>`-table unwrapping
- Chunker simplified: removed `_extract_boundary_elements`, reverted to top-level iteration, removed markdown-table detection, pointed `MD_DIR` at VADIR-only (the 237 parsed markdown files were never on the critical path)
- Max chunk size dropped again to 49,708 tokens — zero chunks over 50K ([Ex. W](#ex-w-preprocessor-vs-chunker-split))

**Act 15 — "Heading-only embed_text, skip LLM summaries"** (cost-aware design)
- 868 oversized chunks would need Claude Sonnet calls for summary indexing — ~$13
- First brain: "do the oversized chunks have descriptive headers?"
- Yes — headings like "14.03. TABLE FOR COMPUTING RATE BASED ON TOTAL CHARGES" fully describe the table's topic
- Decision: use `title + heading_path` as `embed_text` for oversized chunks — free, deterministic, and good enough for a baseline
- Tradeoff accepted: won't match content-level queries ("what's the rate for $500"), will match topic-level queries ("how do I compute rate"). Deferred to MCP-level `retrieve_full_doc` tool if needed.
- Zero API cost. Script stays self-contained.

**Act 16 — "Does the archived flag go on docs or chunks?"** (metadata layering)
- Initial thought: `archived: true` on the parent `documents` row
- First brain: "but the archived sections are chunks not docs" — retrieval returns chunks, not documents. The flag needs to be on `document_chunks.metadata` JSONB, not just the parent row, or every query needs a JOIN.
- Follow-up: archived isn't a blanket penalty — historical accuracy queries *want* archived content. The synthesis prompt has to reason about currency vs. history.
- Final observation: every archived chunk already has "ARCHIVED:" in the `heading_path` (e.g., `"ARCHIVED: M22-4, Part II, Chapter 7 – Education Letters"`). The LLM sees the signal without extra metadata plumbing.
- No enrichment needed — the source content is already self-describing.

**Act 17 — Step 9 eval harness + the broken golden set audit** (eval credibility before tuning)
- Built `scripts/retrieve.py` (vanilla pgvector cosine), `scripts/generate.py` (Sonnet 4.6, system-prompt-grounded), `scripts/run_eval.py` (110-query orchestrator), `scripts/score_eval.py` (DeepEval w/ Haiku judge)
- Discovered the golden set was malformed JSON — two missing commas, file unparseable since creation. Caught only because eval scripts tried to load it ([Ex. Y](#ex-y-golden-set-malformed-json))
- Built a structural audit (`scripts/audit_golden_set.py`) — checks each `expected_source_id` exists in DB, distinctive query terms appear in expected source, suggests alternate sources
- Audit caught: **14 queries pointed at `VADIR_ICD` but the DB stored it as `VADIR_CH33_LTS_WS_V2.1.1_ICD_20220509`** — pure ID mismatch from creator-friendly shorthand. Auto-fixed across all 14
- Found 4 real golden-set bugs: query #9 asked about "bartending" (zero corpus mentions), #10 expected one source for private-pilot training but 20 chunks across 5 articles cover it, #19/#45 had wrong expected source
- Pattern enforced: **only fix golden set on structural checks, never on "our system missed it"** — protects against overfitting the eval to the system. Documented the pattern in [Ex. Z](#ex-z-golden-set-audit-pattern)
- First baseline (110q, v1 chunks, no rerank): Faithfulness 0.97, AnsRel 0.85, **CtxPrec 0.40, CtxRec 0.45, CtxRel 0.43** — generation production-grade, retrieval is the weak link

**Act 18 — HtmlRAG vs lxml-html-clean** (research-first paid off twice)
- HTML chunks are cluttered with `<span style="font-size: 16px"><span style="font-family: arial">…</span></span>` MS-Word noise. ~35-75% of chunk tokens were tag overhead.
- Per the global research-first rule: dispatched two parallel subagents (broad + recent) to find existing solutions before custom code
- Found **HtmlRAG** (WWW 2025 paper, `pip install htmlrag`) — purpose-built for RAG, claims "Lossless HTML Cleaning" preserving colspan/rowspan
- Spike test on a synthetic table proved the paper wrong: HtmlRAG strips colspan, rowspan, AND the `<table>` tag itself ([Ex. AA](#ex-aa-htmlrag-vs-lxml-clean))
- Fallback: **`lxml-html-clean` with explicit `safe_attrs={'href','src','alt','colspan','rowspan'}`** — passes all checks, 65% size reduction on tables, table semantics intact
- First brain noted this as a candidate for the public Claude skill repo: "lightweight wrapper around lxml-html-clean that strips decorative HTML while preserving structural tags including tables with colspan/rowspan" — added to global TODO

**Act 19 — Option B: chunk boundaries vs content separation** (the v1→v2→v2b investigation)
- Applied lxml cleanup BEFORE chunking. Re-embedded. Ran 10-query subset eval.
- Result: **Contextual Recall dropped from 0.75 → 0.50** (-25pp). Cleaning REGRESSED retrieval.
- Root cause investigation: cleanup was unwrapping `<span>` tags that the heading-splitter used as structural boundaries. Different chunk boundaries → different embeddings → different retrieval order.
- Designed the controlled experiment (Option B): apply BS4 cleanup AFTER `split_html_by_headings` instead of before. Boundaries stay identical; only chunk content cleaned post-hoc.
- Dispatched a subagent to run Option B end-to-end while main thread researched reranker libraries in parallel
- **Result: chunk count back to 6,489 (identical to v1, vs 5,355 in v2). Recall: 0.75 → 0.75 (perfectly preserved). Token cost: -20.6%** ([Ex. BB](#ex-bb-option-b-results))
- First brain framing of the underlying lesson: "is it cuz the noisy tags are actually helping?" — answer: tags don't help embeddings semantically, but they helped as structural anchors for the chunker. Boundaries vs content was the wrong axis to bundle together.

**Act 20 — Reranker integration + the 27GB OOM** (Step 11)
- Picked **mxbai-rerank-base-v2** (0.5B params, Apache 2.0, MPS-compatible) — same vendor as embedder, peer-reviewed lift over BGE on BEIR
- First eval attempt with rerank crashed the system — Python process hit 27GB RAM, macOS suspended every other app (Activity Monitor, Xcode, Docker GUI)
- Built `scripts/debug_rerank_mem.py` to instrument each pipeline stage with RSS deltas. Confirmed: rerank alone fine (1.7GB), embedder + rerank together fine (2.4GB)
- The failure mode: a 5K-token chunk fed through cross-encoder attention allocated **13.84 GiB**. Our v2b corpus has chunks up to 47K tokens — O(n²) attention math = 27GB ([Ex. CC](#ex-cc-rerank-oom-reproducer))
- Fix: cap rerank input at 2,000 chars per chunk. Cross-encoders are trained on ≤512-token passages anyway — long inputs don't help ranking, just blow memory
- After fix: 4GB peak even with 47K-token chunks. Full 110-query rerank eval ran cleanly
- **Headline rerank lift on full 110: CtxPrec 0.40 → 0.57 (+16.5pp), CtxRel 0.43 → 0.55 (+11.8pp), CtxRec 0.45 → 0.51 (+5.3pp)** ([Ex. DD](#ex-dd-rerank-headline-comparison))

**Act 21 — Deep-dive: top RAG teams don't use the frameworks we considered** (the surprising research finding)
- After hand-rolling a chunker, found base64 binary blobs leaking into chunks as garbage text + image-only chunks with no retrievable content. Signaled we might be missing entire layers other people had solved.
- Invoked `/deep-dive` skill — DAG-decomposed into 4 parallel research subagents covering Unstructured.io, Docling, LlamaIndex, and what top production RAG teams actually use
- **The unexpected finding:** Uber Genie, Dropbox Dash, LinkedIn RAG, Atlassian Rovo, Notion AI, Spotify AiKA — **none use Unstructured or Docling for HTML ingestion**. All custom or native-API.
- Anthropic's cookbook doesn't even prescribe a parser. The chunking-strategy battles are mostly noise; the real lever is **Contextual Retrieval** — Anthropic's own pattern with documented +35% recall lift from prepending LLM-generated context per chunk before embedding
- Synthesis report saved to `docs/deep-dive/2026-04-14-html-rag-ingestion-state-of-art.md` ([Ex. EE](#ex-ee-deep-dive-decision-table))
- Decision: stay custom (validated by what works in production), adopt Contextual Retrieval as the next Loop A intervention

**Act 22 — Contextual Retrieval via Batches API** (cost-aware bulk processing)
- Built async live-API contextualizer first. Hit Haiku rate limits hard: at concurrency=8 → 205/347 chunks failed with 429s; at concurrency=3 with max_retries=10 → 5/347 still failed. Effective rate: **0.9 chunks/sec, ~$14, 2 hours for 6,489 chunks**.
- First brain: "what's the batches api?" — pivoted to Anthropic Message Batches: 50% discount, no per-request rate limits, async background processing
- First batch attempt: 400 BadRequestError because VADIR source_id `VADIR_CH33_LTS_WS_V2.1.1_ICD_20220509` contains dots — violates Anthropic's `^[a-zA-Z0-9_-]{1,64}$` custom_id pattern. Smoke test missed it (only had digit-IDs). ~1 hour lost to debug ([Ex. FF](#ex-ff-batch-custom-id-bug))
- Fixed: sanitize source_id → token via regex, persist token mapping in batch state file for poll-resume
- Second batch: 5,978/6,142 success in **~4 minutes wall time, $12.48** (97% success, half-cost vs live API). Combined with smoke test = 6,325/6,489 chunks contextualized.

**Act 24 — "Are all the failing queries technical?"** (the failure-class realization)
- After v2bcr+rerank eval, Contextual Recall sat at 0.52. Proposed "increase k" as the obvious next move. First brain asked a targeted question: are these low-recall failures all technical-term queries?
- Segmented the 33 worst-recall queries by query characteristics: **82% were exact-token precision misses** (EPC 240, VADIR code 9GY, $45,000, Muskogee) — queries where a specific literal string needed to appear in the answer chunk, but dense embeddings buried it under semantic neighbors. **18% were multi-source synthesis queries** (prod-ops / consulting-SME questions requiring stitching across sections) — a totally different failure mode ([Ex. HH](#ex-hh-failure-class-segmentation))
- Realization: the two classes want different treatments. Hybrid retrieval (BM25 + dense + RRF) is the textbook fix for exact-token precision. HyDE + query decomposition is the fix for synthesis queries. Neither alone solves the other.
- The bigger lesson: **"loop on one metric at a time" was a shorthand that masked the real principle**. Interventions don't target metrics — they target failure classes. Aggregate metrics average across heterogeneous query populations, hiding bimodal distributions.
- First brain's correction: "the fact that this insight only surfaced after I asked the question is problematic." Codified a standing rule: after every eval, segment by query_type, pull representative failures, name patterns, map to levers — before proposing next steps. Added to plan doc step 9, project CLAUDE.md, and global lessons. ([Ex. II](#ex-ii-post-eval-analysis-protocol))
- Revised iteration principle: **pick the largest unresolved failure class, choose the single intervention most likely to resolve it, ship, measure on that class specifically, then reassess.** Preserves one-change-at-a-time discipline without conflating metrics with failure classes.

**Act 25 — k-sweep, HyDE, CRAG, hybrid: triaging the roadmap**
- Full discussion of the four remaining retrieval-layer techniques, priorities aligned to failure classes:
  1. K-sweep diagnostic (1 afternoon) — is retrieval ranking-bound or index-bound? Cheap answer before investing.
  2. Hybrid retrieval (~100 lines) — BM25 + dense + RRF. Targets exact-token precision (82% of low-Recall failures). Biggest lever for smallest effort.
  3. HyDE + query decomposition — targets vocabulary mismatch and multi-source synthesis. Smaller slice but the remaining class.
  4. CRAG — quality gate for the remaining edge cases + "say IDK" discipline for production.
- Key decision aid: hybrid moves BEFORE HyDE in the plan because the failure analysis showed which class dominates in our corpus specifically ([Ex. JJ](#ex-jj-hybrid-over-hyde-reasoning)).

**Act 26 — K-sweep diagnostic + metric prioritization in the long-context era** (2026-04-15 session)
- Ran the k-sweep before investing in HyDE: 5 fast-mode runs at k ∈ {3, 5, 10, 20, 50}, **no rerank** to isolate pure index recall. 25 min total, ~$1.50 ([Ex. LL](#ex-ll-k-sweep-table))
- Source recall climbed monotonically 0.80 → 0.87 → 0.87 → 0.90 → 0.93 — **gold docs ARE in the index**, just ranked 21-50 for ~3-7% of queries. Signal: ranking-bound, not index-bound.
- top1 frozen at 0.533 across every k — the best chunk isn't the gold source half the time regardless of pool size. Not fixable by widening retrieval; fixable only by ranking or chunking quality.
- Generator lift was huge: IDK 0.367 → 0.100, keyword recall 0.731 → 0.958. Long-context models genuinely filter junk, as long as the gold chunk is in the bag.
- **Discussion that followed — when the 5 DeepEval metrics actually matter:** mapped each metric to the effect of raising k (Faith ~flat, AnsRel ↑, CtxPrec ↓, CtxRec ↑↑, CtxRel ↓). Raising k is a Pareto trade: buys CtxRec + AnsRel at cost of CtxPrec + CtxRel. The interesting levers are ranking ones (HyDE, better reranker, hybrid) because they lift CtxPrec/CtxRel without the trade.
- **Priority reshuffle for the long-context era:** with modern LLMs filtering noise well, **CtxRec > CtxPrec > CtxRel**. CtxPrec still matters for cost/latency/distractors, not for answer quality alone. CtxRel is most useful as a **pipeline health diagnostic** — low CtxRel + high CtxRec = noisy index (duplicates, base64 blobs, over-fine chunking) ([Ex. MM](#ex-mm-metric-priority-long-context-era))
- Decision aid confirmed: raising `rerank_from` from 20 to 50 is in-bounds with current best practice (Anthropic's own CR paper uses 150→20; Cohere 100→10) and directly addresses the 3-7% of queries where gold sits at rank 21-50.

**Act 23 — Three-tier eval cadence** (making Loop A actually feasible)
- Each full validation run = ~2h wall + $4-5. Unsustainable for iterative experimentation.
- Designed three tiers based on what each catches:
  - **Fast (5-10 min, $0.30)** — 30q subset + 4 cheap proxies (top-K source match, **answer-keyword recall** approximating Contextual Recall without LLM judge, IDK rate, token cost). For retrieval/chunking iterations.
  - **Medium (30 min, $1.50)** — 30q subset + full DeepEval. For generation-side iterations (system prompt, model swap).
  - **Full (2h, $4.30)** — 110q + full DeepEval. For milestone validation only.
- Built `--fast` mode + `--baseline` flag in `run_eval.py` — automatically prints proxy deltas vs prior run, with ✓/✗ markers respecting sign convention (lower IDK = better) ([Ex. GG](#ex-gg-fast-mode-output))
- **Speedup math:** 10 chunker tweaks at 2h each = 20h, $50. Same 10 tweaks at 8 min fast each + 1 full validation = 3.5h, $10. **6x faster, 5x cheaper, same final confidence.**

---

## Key Demo Moments (for video)

### 1. "Show me the API" — DevTools Discovery
**What happened:** Opened Chrome DevTools on the KnowVA page, found the eGain API endpoints by watching network requests.

**Screen recording needed:**
- KnowVA page loading with SPA spinner
- DevTools Network tab → filter to Fetch/XHR
- Click a chapter → see the API call appear
- Copy the URL → test it

**Talking point:** "The data lived behind a JavaScript app with no public API documentation. We reverse-engineered the endpoint structure in 5 minutes using Chrome DevTools."

### 2. "No Playwright Needed" — The $level Parameter
**What happened:** Initial approach used Playwright headless browser. After debugging, discovered the `$level=5` query parameter that returns the full topic tree in one API call — eliminated the browser dependency entirely.

**Before/after:**
- Before: Playwright → navigate SPA → click links → intercept responses → complex, fragile
- After: Single httpx GET with `$level=5` → full tree of 170 topics in one call

**Talking point:** "The first approach was a headless browser crawling a JavaScript app. After inspecting the actual API, we found a single parameter that returned the entire topic tree — reducing the crawler from Playwright dependency to pure HTTP requests."

### 3. The 237-Article Crawl
**What happened:** Ran the crawler live — Phase 1 (topic discovery), Phase 2 (article enumeration), Phase 3 (content download). All with 2-second polite delays.

**Stats for screen:**
```
Topics:              170
Articles discovered: 237
Articles downloaded: 237
M22-3 articles:      8
M22-4 articles:      229
With tables:         126 (53%)
Total size:          27 MB
```

**Talking point:** "237 articles with full HTML structure preserved — headings, tables, lists intact for downstream element-aware chunking. 53% contain tables, which is why the pipeline uses Docling with TableFormerMode.ACCURATE."

### 4. Golden Query Evolution — From Textbook to Real
**What happened:** Started with standard lookup queries, then the first brain pushed for more realistic voices:
- "how about consulting SME perspective?" → system gap analysis queries
- "how about prod ops?" → incident triage queries  
- "are there queries where we say 'VADIR' but don't have to?" → domain-language rewrites

**Query progression (show 4 examples):**

Textbook:
> "What does VADIR Character of Service code 'J' mean?"

Cross-source:
> "How does a VCE determine Chapter 33 eligibility when a veteran has both ROTC service and later active duty?"

Consulting SME:
> "What are the single points of failure in the Chapter 33 claims pipeline from service record lookup through payment?"

Prod ops (no system names):
> "The service record lookups are timing out intermittently — some claims get through, others hang. VCEs are seeing locked records they didn't open. How do I triage this?"

**Talking point:** "The golden set evolved from 50 textbook lookups to 110 queries across 5 personas. The hardest ones don't name the systems — they describe the problem in domain language and require the RAG to figure out which sources to retrieve."

### 5. "The CMS Lied About Its Headings" — Metadata Gap Analysis
**What happened:** Crawler extracted `heading_outline` for every article — all empty. Investigation revealed KnowVA CMS doesn't use semantic heading tags (`<h2>`-`<h6>`). Instead, headings are `<a name="901"><strong>9.01 PURPOSE</strong></a>` — and some words are split across tags (`<strong>ENTITLEMENT C</strong><strong>ODES</strong>`).

**Before/after:**
- Before: 0/237 articles had heading outlines
- After: 237/237 articles, 1,863 total headings (avg 7.9/article)

**Talking point:** "The CMS stored headings as bold text with anchor links, not semantic HTML. And in one case, it literally split the word 'CODES' across two tags. We wrote a parser that handles three different heading patterns and went from zero to full heading coverage — which is critical because the chunker uses headings to decide where to split."

### 6. "One Category, Not Five" — Simplifying content_category
**What happened:** Initially classified articles into 5 categories (policy, procedure, reference, quality_management, overview) for freshness decay. Then realized: these are all VA government manuals that change at the same rate. Collapsed to `gov_docs_and_manuals`.

**Talking point:** "We built a 5-category taxonomy, then deleted it. These are all authoritative government manuals updated infrequently — differentiating 'policy' from 'procedure' was over-engineering. The real category distinctions come when we add Confluence wikis and Jira tickets, which genuinely decay at different rates."

### 7. "Black-Box Validation Catches What We Missed" — Parsing Validation
**What happened:** Spun up independent subagents to validate parsing quality. They compared original HTML/PDF against parsed markdown without knowing how the parsing worked. Results:
- HTML: 14/20 pass, 6 fail (all failures from colspan/merged cells — a fundamental markdown limitation)
- PDF: All content preserved, but found tripled Table of Contents (62K of noise), cover page OCR junk, and tables split at page breaks

**Talking point:** "We didn't just parse and move on — we ran black-box validation subagents that compared the original against the output. They caught issues we wouldn't have noticed: a Table of Contents tripled by the PDF parser, and 54 articles with structurally broken tables from HTML merged cells. The merged cell issue has no clean fix in markdown — community consensus is to handle it with LLM-generated context descriptions during chunking."

### 8. "Why Are We Embedding Tables?" — First Principles Challenge
**What happened:** First brain questioned whether embedding tables as text makes sense at all. Started with "how does a short query match a long chunk?" — valid but answered by asymmetric training. Then escalated: "if the context blurb gets averaged into everything else, doesn't it get diluted?" — which is correct. This led to proposing table separation: don't embed tables, embed descriptions of tables. Turned out this is the industry standard pattern (LlamaParse, Unstructured, Docling all do it). The project's own research docs had identified the pattern but the build plan used a shortcut.

**Before/after:**
- Before: Bake context blurb into chunk text → embed everything together → diluted signal
- After: Extract tables → generate natural-language description → embed description (pure prose, embeds well) → store actual table as retrievable artifact

**Talking point:** "The first brain asked a simple question — 'why would a one-sentence query match a paragraph full of pipe-delimited numbers?' — and it unraveled our entire table handling strategy. The fix was already in our research docs. We just hadn't promoted it to the build plan."

### 9. "What Else Are We Missing?" — Plan Audit Against Industry Standards
**What happened:** Table separation discussion triggered a broader audit. Found that hybrid search (BM25 + vector) and Anthropic's contextual retrieval were both in the research docs and even had schema columns allocated — but neither appeared in the actual build steps. Also added HyDE (hypothetical document embeddings) and CRAG (corrective RAG) as new iteration steps.

**Talking point:** "We audited our own plan against industry standards and found three components that our research had identified but our build steps had silently dropped. The research-to-plan gap is its own failure mode."

### 10. The Hallucination Catch — Eval Saves the Benchmark
**What happened:** Three parallel subagents validated the golden set. Faithfulness agent scored Q27 at 0.0 — completely fabricated claim.

**The chain:**
```
Q27: "SAO→SOAR transition, October 1, 2023" ← FABRICATED (score: 0.0)
  ↓ referenced as fact in:
Q80: "13 questions" (wrong — actually 16) + SOAR reference
  ↓ referenced in:
Q94: SOAR in policy change examples
Q109: "13-question scorecard"
```

**Before/after scores:**
| Metric | v1 | v2 |
|--------|----|----|
| Faithfulness | 0.936 (one 0.0) | 0.930 (floor: 0.75) |
| Correctness | 0.951 | 0.997 |
| Relevance | 0.987 | 0.993 |

**Talking point:** "The AI that wrote the answers also hallucinated. One fabricated claim — 'SAO to SOAR transition' — propagated to four other answers. The validation subagents caught it before it became the benchmark we'd measure everything against. This is exactly why the Zero-to-MCP plan puts eval before production."

### 11. "Validate the Chunks Too" — Four Parallel Black-Box Agents
**What happened:** After 8,399 chunks came out of the pipeline, spun up 4 parallel subagents — each given a single validation mandate and the JSON file, no access to the chunking code. Same pattern as the golden set validation, reused.

**The four mandates:**
- Table HTML structure (tags present, not truncated, one table per chunk)
- Heading path correctness (types, empty paths, progression across chunks)
- Chunk type classification (list chunks actually have `<ul>/<ol>`, etc.)
- Oversized flagging (threshold consistency, distribution, extreme chunks)

**Findings:**
| Check | Issues Found |
|---|---|
| Multi-table chunks | 46 chunks with 2+ `<table>` blocks |
| Misclassified list chunks | 22 marked "list" with zero list HTML |
| List fragments | 25 chunks starting with bare `<li>` (no wrapper) |
| Oversized threshold gap | 20 chunks in the 1,002–1,024 band unflagged |

**Talking point:** "The same black-box validation pattern we used on the golden set caught real chunking bugs. Four parallel subagents, no code access, just the output and a spec. The multi-table finding led to a deeper refactor."

### 12. "How Much of This Is Specific to Our Source?" — The Refactor That Saves Future Work
**What happened:** First brain caught source-specific logic creeping into the generic chunker: layout-table detection, `<div>`-wrapper recursion, markdown-table fallbacks. All compensating for KnowVA CMS quirks.

**The architecture principle:** Generic chunker + source-specific preprocessors. New sources get a thin preprocessor, not a chunker fork.

**Before:**
- `chunk_documents.py` has `_extract_boundary_elements` recursion for `<div>` wrappers
- `detect_chunk_type` checks for markdown `"| ---"` alongside HTML
- `_find_splittable_table` handles layout-wrapper detection
- Works, but every new source quirk bloats the chunker

**After:**
- `knowva_preprocess.py` (renamed from `knowva_heading_fix.py`) handles all KnowVA quirks: heading fix, layout-table unwrap, `<div>`-table unwrap
- Chunker reverts to clean top-level iteration, HTML-only type detection
- Max chunk size: 175K → 49K tokens

**Talking point:** "The chunker was quietly absorbing every CMS quirk we found. A 5-minute architectural audit — 'is this generalizable?' — pulled three source-specific things out of the chunker and into a preprocessor. New sources now just need their own preprocessor. The chunker stays a chunker."

### 13. "Row-Group Splitting — The Boring Industry Standard"
**What happened:** 10 tables over 50K tokens (largest: 175K) — too big to serve at generation time even with summary indexing. First brain: "What's the industry standard way of dealing with it?"

**The answer (no new research needed):** Split large tables into row-groups, repeat the header row(s) in each chunk. Each chunk = self-contained mini-table.

**The 50K ceiling:**
- Sonnet 200K context window
- 50K-token chunk + query + system prompt + other chunks + response = usable
- 175K-token chunk = practically unusable

**Result:** Max chunk dropped to 49,708 tokens. Zero chunks over 50K. No parent-linking metadata added — deferred until eval proves it's needed.

**Talking point:** "Fancy approaches exist — table-as-structured-data, table-to-natural-language — but the boring industry standard is row-group splitting with repeated headers. It handles 95% of real-world tables and survives retrieval naturally. We added 40 lines of code and solved the problem."

### 14. "Heading-Only embed_text — Skip the $13 Summary Bill"
**What happened:** 868 oversized chunks would need Claude Sonnet summary generation (~$13 for the corpus). Before spending it, first brain asked: "Do the oversized chunks have descriptive headers?"

**The headings already describe the content:**
```
"14.03. TABLE FOR COMPUTING RATE BASED ON TOTAL CHARGES"
"Part II, Chapter 2, Section D, Topics 11-15: Chapter 33 Processing Screens in DGI"
"9.05 EDUCATIONAL..."
```

**Decision:** For oversized chunks, `embed_text = title + heading_path`. Free, deterministic, good enough for baseline.

**The tradeoff accepted:**
- Wins at: "find me the table about computing rate" (topic-level queries)
- Loses at: "what's the rate for $500" (content-level queries)
- Escape valve: add a `retrieve_full_doc` MCP tool later if eval shows content queries failing

**Talking point:** "Summary indexing costs real money per chunk. Before spending it, we checked if the free alternative — just the heading — was already descriptive enough. It was. If eval catches the gap, we add a `retrieve_full_doc` MCP method. Design against what you've measured, not what you fear."

### 15. "The Library Lied About Its Own Paper" — HtmlRAG Spike Test
**What happened:** Found `htmlrag` on PyPI — a WWW 2025 paper claiming "Lossless HTML Cleaning" preserving colspan/rowspan. Spike-tested it on a synthetic table with colspan/rowspan/style attributes. The library stripped colspan, rowspan, AND the `<table>` tag itself.

**Talking point:** "Always validate library claims with a 5-minute spike test. Especially when the claim is the only reason you're reaching for the library. Switched to `lxml-html-clean` with an explicit attribute whitelist — passed every check, 65% size reduction on real chunks." ([Ex. AA](#ex-aa-htmlrag-vs-lxml-clean))

### 16. "The Tags Were Holding Up the Boundaries" — Option B
**What happened:** First attempt at HTML cleanup ran lxml + BS4 *before* chunking. Re-embedded. Eval showed Contextual Recall dropped from 0.75 → 0.50 (-25pp). The cleanup was unwrapping `<span>` tags that the heading-splitter used as structural markers — chunk boundaries shifted, embeddings changed, retrieval order broke.

**Before/after:**
- v1 (no clean): 6,489 chunks, CtxRec 0.75, avg 3,330 input tokens/query
- v2 (clean before chunk): 5,355 chunks, CtxRec 0.50, boundaries shifted everywhere
- **v2b (clean AFTER chunk): 6,489 chunks identical to v1, CtxRec 0.75, avg 2,643 tokens (-20.6%)**

**Talking point:** "We almost shipped a 20% cost optimization that destroyed retrieval. The fix wasn't to undo the cleanup — it was to apply it AFTER chunk boundaries were set. Boundary preservation and content cleanup are independent dimensions; bundle them and you can't tell which one regressed." ([Ex. BB](#ex-bb-option-b-results))

### 17. "27GB Python and macOS Suspended Every App" — Reranker OOM
**What happened:** First eval with mxbai-rerank-base-v2 spiked Python to 27 GB RAM. macOS auto-suspended Activity Monitor, Xcode, Docker GUI, every other app to keep the foreground alive. Built a memory reproducer. Found cross-encoder attention is O(n²) — a 47K-token oversized table chunk needs 8.8 GB just for the attention matrix. Top-20 of those = 27 GB.

**Fix shown on screen:** Cap rerank input at 2,000 chars per chunk. Cross-encoders are trained on ≤512-token passages anyway.

**Result:** 4 GB peak even with the 47K-token chunks in the rerank set. Full 110-query rerank eval ran cleanly.

**Talking point:** "Cross-encoders look at every (query, chunk) pair with full attention. That's their power and their failure mode. Truncate inputs aggressively — they don't help ranking quality and they'll murder your RAM." ([Ex. CC](#ex-cc-rerank-oom-reproducer))

### 18. "+16.5pp Precision, +11.8pp Relevancy" — The Reranker Headline
**What happened:** Full 110-query DeepEval comparison, same chunks, same generation, same scoring. Only difference: cosine top-5 vs cosine top-20 → mxbai-rerank → top-5.

**Headline numbers on slide:**
| Metric | No rerank | With rerank | Δ |
|---|---|---|---|
| Contextual Precision | 0.40 | 0.57 | **+16.5pp** |
| Contextual Relevancy | 0.43 | 0.55 | **+11.8pp** |
| Contextual Recall | 0.45 | 0.51 | +5.3pp |
| Faithfulness | 0.97 | 0.96 | flat |
| Answer Relevancy | 0.83 | 0.86 | +0.03 |

**Talking point:** "k=5 cosine retrieval pulls 60-70% noise. A 0.5B-parameter cross-encoder reranker fixes that. 17pp Precision lift, 12pp Relevancy lift, no Faithfulness regression. Same model family as our embedder, runs locally, no API cost." ([Ex. DD](#ex-dd-rerank-headline-comparison))

### 19. "None of the Top RAG Teams Use the Frameworks You Considered" — Deep Dive Surprise
**What happened:** Used the `/deep-dive` skill to research what production RAG teams actually use for HTML ingestion. 4 parallel subagents researched Unstructured, Docling, LlamaIndex, and 7 named teams (Uber, Dropbox, LinkedIn, Atlassian, Notion, Spotify, Anthropic).

**The finding on screen:** None of the seven teams use Unstructured.io or Docling for HTML ingestion. All custom or native-API. Anthropic's cookbook doesn't even prescribe a parser. The actual production playbook is **custom parsers + Contextual Retrieval (the next thing we adopted)**.

**Talking point:** "We were second-guessing ourselves for hand-rolling a chunker. Turns out every production RAG team that's published their architecture also hand-rolled. The chunking-strategy battles are mostly noise. The real lever — Anthropic's Contextual Retrieval — is published with +35% recall lift." ([Ex. EE](#ex-ee-deep-dive-decision-table))

### 20. "Submit and Walk Away" — Batches API for Bulk Contextualization
**What happened:** Adopting Contextual Retrieval needed 6,489 LLM calls to generate per-chunk context strings. Live API was throttled to 0.9 chunks/sec by Haiku rate limits — would take 2 hours and $14. Switched to Anthropic's Message Batches API: 50% discount, no rate limits, async background processing.

**Demo arc:**
1. First batch attempt failed at request 6,074: VADIR source_id had dots, violated `^[a-zA-Z0-9_-]{1,64}$` pattern. Smoke test missed it (only digit IDs). Lost 1 hour to debug ([Ex. FF](#ex-ff-batch-custom-id-bug)).
2. Fixed with reversible token map. Second batch: **5,978/6,142 success in 4 minutes wall time, $12.48** — half the live-API cost.

**Talking point:** "When you have thousands of independent LLM calls and don't need real-time, the Batches API is a no-brainer — half the cost, no rate limits, runs in the background. Just sanitize your custom IDs."

### 22. "Aggregates Were Hiding Two Diseases" — The Failure-Class Insight
**What happened:** After CR eval, Contextual Recall sat at 0.52. Proposed increasing k as the obvious next move. First brain asked: "are the failing queries all technical?" Segmented the 33 low-recall queries — **82% were exact-token precision misses (EPC 240, 9GY, Muskogee); 18% were multi-source synthesis queries.** Different diseases needing different treatments.

**Talking point:** "Aggregate metrics average across heterogeneous query populations and hide bimodal distributions. 'Contextual Recall 0.52' was actually 'lookup queries 0.80 + synthesis queries 0.20' — two failure classes with two different fixes. Hybrid retrieval attacks one class; HyDE attacks the other. Without segmentation, we'd have picked the wrong lever." ([Ex. HH](#ex-hh-failure-class-segmentation))

### 23. "Metrics → Failure Classes → Levers" — The Revised Iteration Principle
**What happened:** Codified a standing rule: after every eval, segment by query_type, pull 2-3 representative failures per cluster, name the patterns with specific mechanisms, map to levers — before proposing the next step. Captured in plan doc step 9, project CLAUDE.md, and global lessons.

**Talking point:** "The shorthand 'loop on one metric at a time' masked the real principle. Interventions don't target metrics — they target failure classes. An intervention with zero aggregate-metric movement isn't a failed iteration if it resolved a specific class. The right question is 'which failure class is this treatment curing,' not 'did the average go up.'" ([Ex. II](#ex-ii-post-eval-analysis-protocol))

### 21. "Three-Tier Eval Cadence" — Making Loop A Actually Feasible
**What happened:** A full eval iteration costs 2 hours and ~$5. After the first few full validation runs, the math killed iteration speed. Built three tiers:

| Tier | Time | Cost | Catches |
|---|---|---|---|
| Fast | 5-10 min | $0.30 | Retrieval recall, ranking, source matches, token cost (no LLM judge) |
| Medium | 30 min | $1.50 | Same + full DeepEval semantic scoring |
| Full | 2h | $4.30 | Same on full 110-query set |

**Talking point:** "Most RAG iterations are retrieval/chunking changes that don't need full DeepEval scoring. A 5-minute fast mode with cheap proxies — keyword recall, IDK rate, token cost — catches the same direction-of-change. Reserve the 2-hour full validation for milestone declarations. 6x faster, 5x cheaper, same final confidence." ([Ex. GG](#ex-gg-fast-mode-output))

### 24. "Recall Climbs, Top1 Frozen" — The K-Sweep Diagnosis
**What happened:** Instead of picking HyDE by vibes, ran a 25-min diagnostic: 5 fast-mode evals at k ∈ {3, 5, 10, 20, 50}, no rerank. Recall climbed monotonically 0.80 → 0.93. Top1 stayed frozen at 0.533 at every k.

**Before/after framing:** The question "is retrieval ranking-bound or index-bound?" has two opposite fixes. Ranking-bound → HyDE / better rerank / hybrid. Index-bound → chunking, embeddings, more sources. The sweep answered: **ranking-bound.** Gold docs are in the index, just ranked 21-50 for 3-7% of queries. Top1 being stuck regardless of pool size says the best-scoring chunk isn't the gold one half the time — a ranking/chunking problem, not a recall problem.

**Talking point:** "You don't pick your next lever from vibes. A 25-minute k-sweep tells you whether you're ranking-bound or index-bound before you sink 2 days into the wrong intervention. Gold docs climbing into reach as k grows + top1 frozen = ranking is the weak link. That rules out HyDE-before-hybrid, confirms wider rerank pool, and retires the 'just raise k' instinct."  ([Ex. LL](#ex-ll-k-sweep-table))

### 25. "Which Metric Do I Defend?" — Priority in the Long-Context Era
**What happened:** After the k-sweep, first brain asked how the 5 DeepEval metrics would each move with higher k, then: "is there a typical k or every man for himself?" — followed by "contextual precision isn't really necessary if the client LLM can handle the extra info?" Mapped out the metric tradeoff, landed on a priority order.

**The mapping on screen:**

| Metric | Raising k effect | Why |
|---|---|---|
| Faithfulness | ~flat | Grounding doesn't care about pool size if gold chunk is present |
| Answer Relevancy | ↑ | IDK halved 0.37 → 0.10; generator filters noise well |
| **Contextual Precision** | ↓ or flat | Rank-weighted; top1 frozen, extra chunks dilute the ranked list |
| **Contextual Recall** | ↑↑ | Direct: source recall 0.80 → 0.93 |
| **Contextual Relevancy** | ↓ | More chunks, same # gold → ratio drops |

**Talking point:** "The hierarchy of RAG metrics has shifted with long-context models. CtxRec > CtxPrec > CtxRel. Modern LLMs filter noise well — CtxPrec matters now for cost, latency, and distractor risk, not answer quality. CtxRel is most useful as a *debugging lens*: low CtxRel + high CtxRec means your index is noisy (duplicates, blobs, over-fine chunks). Optimize recall aggressively, accept lower precision, watch CtxRel as a signal that something junky got indexed." ([Ex. MM](#ex-mm-metric-priority-long-context-era))

---

## Key Demo Artifacts

| Artifact | Path | What it shows |
|----------|------|---------------|
| Crawler script | `scripts/crawl_knowva.py` | Pure API, no browser, resume support, polite crawling, heading extraction with CMS-specific fallback |
| Enrichment script | `scripts/enrich_metadata.py` | Batch metadata enrichment (headings, acl, authority tier, content_category) |
| Source-specific preprocessor | `scripts/knowva_preprocess.py` | KnowVA normalizations: heading fix + layout-table unwrap + div-table unwrap (renamed from `knowva_heading_fix.py`) |
| Chunking script | `scripts/chunk_documents.py` | Source-agnostic: heading split + element-boundary split + row-group split for tables >50K. Re-detects chunk_type on sub-chunks. |
| Embed + store script | `scripts/embed_and_store.py` | mxbai-embed-large → pgvector. Resume-safe. Heading-only `embed_text` for oversized chunks (no LLM summary). |
| Preprocessing reference | `docs/preprocessing.md` | Per-source transform documentation (not a script — a reference manual) |
| Docker Compose | `docker-compose.yml` | pgvector/pg17 on port 5433 |
| Schema SQL | `scripts/init_schema.sql` | documents + document_chunks tables with HNSW index |
| ~~Parsing script~~ | ~~`scripts/parse_html_to_markdown.py`~~ | ~~Deleted — HTML articles skip markdown, go straight to HTMLHeaderTextSplitter~~ |
| Retrieval | `scripts/retrieve.py` | Vanilla pgvector cosine, lazy model load, CLI + module API |
| Generation | `scripts/generate.py` | Sonnet 4.6 grounded by system prompt, dotenv-loaded API key |
| Eval orchestrator | `scripts/run_eval.py` | 110-query loop, supports `--rerank-from`, `--fast`, `--baseline` deltas, cheap proxies |
| Eval scoring | `scripts/score_eval.py` | DeepEval w/ Haiku judge, 5 metrics async, JSON output |
| Golden set audit | `scripts/audit_golden_set.py` | Structural checks: source IDs exist, key terms present, alternate sources |
| HTML cleaner | `scripts/chunk_documents.py:_HTML_CLEANER` | `lxml-html-clean` w/ explicit safe_attrs preserving colspan/rowspan |
| BS4 post-pass | `scripts/chunk_documents.py:_bs4_post_pass` | Per-chunk cleanup AFTER boundaries set, drops empty tags, unwraps `<span>` |
| Reranker | `scripts/rerank.py` | mxbai-rerank-base-v2 cross-encoder, MPS-compatible, 2K-char input cap |
| Memory debugger | `scripts/debug_rerank_mem.py` | RSS instrumentation per pipeline stage; reproduces 27GB OOM |
| Contextual Retrieval | `scripts/contextualize_chunks.py` | Anthropic Batches API, prompt caching, sanitized custom_ids, resume-safe |
| Deep dive report | `docs/deep-dive/2026-04-14-html-rag-ingestion-state-of-art.md` | DAG-based research synthesis: HTML RAG ingestion state of the art |
| Sample article HTML | `data/knowva_manuals/articles/554400000073486.html` | Structure-preserving output (tables, headings, metadata in `<meta>` tags) |
| Sample article JSON | `data/knowva_manuals/articles/554400000060851.json` | Enriched metadata: heading_outline with 12 headings, acl, authority tier, content_category |
| Sample parsed markdown | `data/knowva_manuals/parsed/554400000073086.md` | 68 tables converted to pipe format, headings preserved, nav links stripped |
| VADIR ICD parsed | `data/knowva_manuals/parsed/VADIR_CH33_LTS_WS_V2.1.1_ICD_20220509.md` | Docling output: data element tables, revision history, cover junk + tripled ToC stripped |
| Topic tree | `data/knowva_manuals/_topic_tree.json` | Full 170-node parent→child hierarchy |
| Golden query set | `data/golden_query_set.json` | 110 queries, 10 types, source references, answers |
| Eval results | `data/eval_faithfulness_v2.json` | Per-query claim decomposition + grounding scores |
| VADIR ICD original | `data/VADIR_CH33_LTS_WS_V2.1.1_ICD_20220509.pdf` | Real VA interface control document |
| **MCP server** | `scripts/mcp_server.py` | FastMCP 3.x wrapping retrieve+rerank. Tools + Resources + Prompts. `auth_context` gateway seam. `--transport stdio`/`http` switch. 185 LOC. |
| **MCP smoke test** | `scripts/test_mcp_server.py` | In-process `fastmcp.Client` test, 5 assertions incl. guardrails (empty-query reject, k-clamp). |
| **Hybrid-ready schema** | `scripts/init_schema.sql` | `content_tsv` GENERATED column + GIN index — BM25-ready, no rewrite. |
| **Backup snapshot** | `~/ikb-backups/ikb-20260415-1705.dump` | 30MB `pg_dump -Fc` of the live pgvector volume (238 docs, 6,489 chunks). |
| **Trace-public helper** | `scripts/make_trace_public.py` | Sidecar flip of Langfuse trace visibility via `/api/public/ingestion` `trace-create` event. 40 lines stdlib + dotenv. Works around the OTel-attribute-on-child-span gotcha. |
| **Baseline reconfirm output** | `data/eval_v2bcr_rerank_postship.fast.raw.json` | 30q fast eval post-tsvector. Zero drift vs `eval_v2bcr_rerank.raw.json`. Also serves as the Option A CI gate baseline. |

---

## Write-Up Angles

### Angle 1: "From SPA to RAG in One Session"
- JavaScript SPA with no API docs → reverse-engineered API → structured corpus → validated golden set
- Timeline: ~3 hours from "show me the zero to MCP" to "110 queries validated"
- Emphasis: the approach works on any knowledge base, not just VA

### Angle 2: "Why Your RAG Benchmark Might Be Lying"
- Focus on the hallucination catch
- AI wrote 110 answers → AI validated them → found fabricated claims propagating through the set
- Without validation, 4 "ground truth" answers would have been wrong
- Ties to Anthropic's contextual retrieval research: eval quality determines pipeline quality

### Angle 3: "Multi-Persona Golden Sets"
- Standard RAG evals use factoid questions
- Real users ask in different voices: VCE ("how do I process this"), SME ("where are the gaps"), ops ("it's broken, how do I triage")
- Domain-language queries (no system names) test semantic understanding, not keyword matching
- The consulting SME queries are the hardest retrieval challenge

### Angle 4: "Zero-to-MCP Step by Step"
- Full walkthrough of the plan execution
- Step 1: corpus selection + crawling
- Step 2: golden set construction + validation
- Step 3: metadata enrichment (heading extraction, acl, authority tier, content_category)
- Step 5: parsing to markdown (markdownify for HTML, Docling for PDF, black-box validation)
- Step 6: pgvector schema (Docker, HNSW index, summary indexing support)
- Step 7: chunking (HTMLHeaderTextSplitter with heading pre-processing, 3,000 chunks)
- What's next: embedding (mxbai-embed-large), summary indexing for oversized chunks, eval harness, MCP server
- Position as replicable methodology for any organization

### Angle 5: "Why Metadata Enrichment Is a Whole Step"
- The CMS gave us bare-minimum metadata — empty heading outlines, useless keywords, no access control tags
- Had to audit every metadata requirement across 3 research docs, cross-reference with what existed, and fill the gaps
- content_category started as 5 categories, simplified to 1 when we realized the distinctions didn't serve the decay model
- Keywords dropped entirely — title + breadcrumb + headings carry the signal
- This isn't glamorous work but it directly determines retrieval quality: without heading outlines, the chunker can't split intelligently; without content_category, the ranking can't apply freshness decay

### Angle 6: "Parsing Isn't Just Format Conversion"
- HTML tables are already structured — no AI needed, just markdownify
- PDF tables have no markup — need Docling's TableFormer deep learning model (15+ min on MacBook Air)
- Right tool for the right source: don't over-engineer (Docling for HTML) or under-engineer (regex for PDF)
- Black-box validation caught issues the parser couldn't fix: colspan in markdown is a fundamental limitation, not a bug
- Community research confirmed: prepend LLM-generated semantic descriptions to handle merged cells, don't try to fix the pipe table

### Angle 7: "The Best Code Is the Code You Delete"
- Built an HTML→markdown parser (Step 5). Then realized markdown conversion was lossy and unnecessary.
- Deleted the entire script. Switched to HTMLHeaderTextSplitter directly on HTML.
- But the CMS used non-standard headings — needed a pre-processor to fix them first.
- The colspan problem that plagued 54 articles? Dissolved. HTML tables stay as HTML — no conversion, no breakage.
- Preprocessing documented in a reference doc, not a monolithic script — because each new source will have different quirks.
- Lesson: sometimes the right engineering move is removing a pipeline step, not adding one.

### Angle 8: "Your Chunking Library Might Be Destroying Your Data"
- LangChain's `HTMLHeaderTextSplitter` silently strips all HTML tags from chunk content
- A table with 298 rows and proper `<th>`/`<td>` structure becomes `Name Code Army A` — flat text with no column relationships
- The whole point of staying in HTML was to preserve table structure. The library silently destroyed it.
- Had to write a custom splitter (simple: split at heading tags, keep everything else as raw HTML)
- Three-pass chunking: headings → element boundaries (table/list) → size-based for oversized prose
- Lesson: test your chunking library's output format, not just its splitting logic

### Angle 9: "Summary Indexing — Intentional Mismatch by Design"
- Tables are great for answering questions but terrible for matching queries.
- Summary indexing: embed a human-readable summary (good match target), but return the full table to the LLM (good answer source).
- The vector and the content deliberately don't match — the vector is for finding, the content is for answering.
- This is parent document retrieval (LlamaIndex calls it DocumentSummaryIndex). Not new, but rarely explained this clearly.

### Angle 10: "Source-Specific Code Doesn't Belong in the Chunker"
- Every new source brings its own HTML quirks — layout tables, div wrappers, non-semantic headings
- Easy mistake: add special-case handling to the generic chunker each time
- Correct approach: generic chunker + one preprocessor per source
- The refactor moved 3 source-specific behaviors out of the chunker. New sources now get a ~50-line preprocessor, not a chunker fork.
- Lesson: when the same kind of logic keeps leaking into a "generic" component, the component isn't generic yet

### Angle 11: "Black-Box Validation Is a Reusable Pattern"
- Same pattern that caught hallucinations in the golden set also caught bugs in the chunker output
- Each subagent gets a single validation mandate + the artifact, no code access
- Parallel — 4 agents in one message, results come back as independent reports
- Scales: works for eval sets, chunker output, API responses, anything with a spec and an artifact
- The pattern is the real deliverable, not the individual check

### Angle 12: "Design Against Measured Gaps, Not Feared Ones"
- $13 to generate LLM summaries for 868 oversized chunks — seemed like the "right" thing to do
- But the headings already described the tables well enough for topic-level retrieval
- Deferred summary indexing until eval actually shows content-level queries failing
- Added an escape valve (`retrieve_full_doc` MCP tool for later) instead of spending money preemptively
- Lesson: prove the need before paying the cost. Every "best practice" should earn its slot against measured data.

### Angle 9: "Your Research Docs Know More Than Your Build Plan"
- Research identified table separation, hybrid search, contextual retrieval, multi-representation indexing
- Build plan used shortcuts (context blurbs baked into chunks) or silently omitted them (no step for hybrid search)
- First brain's first-principles questioning exposed the gap — "why would a query vector match a table?"
- The research-to-plan gap is a failure mode worth talking about: organizations do the research, then build something simpler and hope eval catches it
- Lesson: audit your build plan against your own research before starting, not after

### Angle 13: "Label the Seams, Don't Half-Build"
- Every ship-cut v1 item follows the same discipline: ship the thing the demo needs; label everything else with a real pointer, not a stub.
- Five concrete seams labeled so far: `auth_context` parameter (SSO/ACL), tsvector column with no BM25 wiring yet, the `document://` resource as the "retrieve_full_doc" escape valve, Option C (two-tier CI gate) described in README but only Option A shipped, and the Langfuse showcase-trace link (no custom dashboard viewer built).
- The failure mode on the other side: half-built SSO, a fake BM25 scorer, a no-op gateway — all of which *look* like production features in a screenshot but don't hold up under a second question.
- Honest stub > plausible fake. A paragraph describing how Option C extends from Option A is more credible than a flaky nightly job that fails on half the PRs.
- Connects to Thesis A (production scaffolding as differentiator): scaffolding isn't only "what I built." It's also "what I deliberately didn't build, and why, and where it slots in when you need it."

---

## Quotable Moments from Session

> "make sure you preserve the parent-child structure, the headings, etc. we want to use this to build an element-aware chunking for rag vector db"

> "is m22-4 an updated version of m22-3, or are they separate" — (shows domain learning in real-time)

> "are there queries where we say 'VADIR' but don't have to? want to test if the vadir source would be brought up under the right context, without explicitly mentioning 'vadir'"

> "what if we don't even say 'DoD'? does that muddle it too much?"

> "hmm it's kind of a guided question isn't it? names the sources basically. do we have one that's trickier?"

> "so maybe a little less from the POV of the VCE, but from a consulting SME point of view"

> "yea the 25 we generated are fine. let's get 10 additional ones like this" — (iterative refinement of the eval set)

**From 2026-04-13 session (Steps 3 + 5):**

> "let's do a once-over to make sure we capture them all" — (metadata audit across all pipeline docs before enriching)

> "since we'll add confluence/jira later, let's set the field to just 'gov_docs_and_manuals'" — (simplifying content_category from 5 to 1)

> "In fact, what's the reason we say content_category and not freshness_decay? is it multi-purpose?" — (understanding metadata design: decay, filtering, chunking strategy)

> "but i guess the question is, doesn't the element-aware chunking strategy already take care of this kind of division? do we need it in metadata?" — (challenging whether benefit_chapter metadata is needed when chunking preserves heading context)

> "since this is an important step, should we add some independent subagent validation after parsing is done, for some blackbox testing?" — (initiating the validation pattern)

> "do some research into how others handle merged cells" — (research-before-build on the colspan problem)

**From 2026-04-14 session (design challenge + plan audit):**

> "so i have a fundamental question about how a one-sentence vector (the query) can be similar to a paragraph-long vector, and how the context blurb helps there when it's averaged out with everything else"

> "But then shouldn't we just treat tables separately? Like, where tables were, just leave some kind of pointer message or whatever. And then pull up the table completely separately?"

> "I'm confused why this is my idea and not the industry standard."

> "So the research got halfway there to the industry standard."

> "Is this really all for, like, tables? Regular paragraphs don't have this problem right?"

> "Any other industry standards that we're missing?"

**From 2026-04-14 session (Steps 6-7, design simplification):**

> "is markdown that much better than html for non-tables?" — (the question that killed an entire pipeline step)

> "can't we just use HTMLHeaderTextSplitter later directly against the html?" — (simplifying the architecture)

> "so we create an intentional mismatch between the embedded vector and the content even though they're in the same row" — (grasping summary indexing)

> "i just think that during the parsing step, some of these large ones should be dealt with" — (identifying the oversized table problem before being told)

> "i guess let's think about the pipeline once it's in production... preprocessing.py is not so much python code as just a reference manual of what we did" — (pragmatic architecture: document quirks, don't pretend one script handles everything)

> "how many scripts do we have for preprocessing?" — (catching scattered processing logic across crawler, parser, chunker)

> "how did we get mixed content in the first place? aren't we doing element-aware chunking?" — (exposing that heading-based splitting ≠ element-aware chunking)

> "would that be ok even if ul/ol is small?" — (thinking through merge implications before implementing)

> "does authority tier respect historical accuracy? like, the law would have applied to someone in 2018" — (challenging metadata design: archived ≠ less authoritative)

> "i guess the topic breadcrumb would handle the element-aware structural hierarchy of all the archived content being under one header?" — (connecting existing metadata to the archival problem without needing new infrastructure)

**From 2026-04-14 session (chunk validation + chunker refactor):**

> "hmm i thought #1 was a choice — because each table was very small, like <50 tokens? or is this a different issue?" — (checking whether the validation finding was a bug or the documented intentional merge behavior)

> "are there any aspects of this chunker that feel very specific to our source docs and not really generalizable? i want the chunker to be able to handle new docs with some degree of robustness." — (catching source-specific creep before it metastasized)

> "yea, and i'm guessing that would matter to the large table challenge we're tackling as well?" — (connecting architecture to the specific problem at hand)

> "when a table is the content being served for generation, how does the client llm know to render it as a table?" — (first-principles question about the generation contract)

> "what's the system prompt called again in rag lingo?" — (vocabulary catch: synthesis prompt)

> "do mcps ever work with the consumer llm interactively? and do knowledge base mcps ever serve actual docs?" — (probing MCP surface area beyond basic search)

> "ohhh so it's just confirming the chunk json structure matches that" — (grasping schema-as-contract, not vectors-as-everything)

> "what's the industry standard way of dealing with it?" — (before inventing a custom solution)

> "and i'm guessing we don't want to bloat the synthesis prompt" — (context budget awareness)

> "do the oversized chunks have descriptive headers?" — (the question that saved $13 in API calls)

> "but the archived sections are chunks not docs" — (retrieval-time metadata granularity — chunks, not docs, are the unit returned)

> "but the issue is there will be queries where freshness is more important and queries where historical accuracy is more important" — (archived content isn't a blanket penalty)

> "does the header for that chunk say something about 'archived'" — (checking whether the signal is already in the content)

> "wasn't there a #3 in your list of concerns" — (catching a dropped item)

> "let's do heading-only, and then we can deal with it by having the mcp serve a method like retrieve_full_doc or something later" — (deferral with an explicit escape valve)

**From 2026-04-15 session (k-sweep + metric prioritization):**

> "let's do k sweep first" — (picking diagnostic before intervention, per the post-eval protocol)

> "show me our 5 scores again? prior to this experiment" — (grounding a new diagnostic in the existing metric baseline before interpreting)

> "so the improvement we're seeing with increased k would improve which of the 5 metrics?" — (pushing past the proxy numbers to the DeepEval metrics that actually define quality)

> "is there a typical k or really every man for himself?" — (checking industry convergence before defaulting to custom)

> "hmmm so contextual precision is not really necessary if the client llm / user can handle the extra info?" — (the question that re-ordered the metric priority hierarchy for the long-context era)

> "and what about contextual relevancy" — (finishing the metric reprioritization sweep)

**From 2026-04-16 session 9 (ship-cut polish):**

> "does it say why we're doing this? what's the point of this in the context of the demo we're building" — (reaching for the purpose when a checklist item felt abstract — reframed from "dashboard share link" to "one clickable observability proof point")

> "so at some point we discussed how the demo should live. did we ever decide that? is it a github repo? is it more than that?" — (pulling up to the artifact level before going further on any single item)

> "same repo as-is is fine. and i agree that link per trace is fine" — (two decisions in one line: public repo cutover + Langfuse sharing model)

> "so in simple terms, what is eval in ci merge gate" — (checking understanding before authorizing build — the load-bearing ship-cut item)

> "so what we would need to run this on is like new prompt versions... what else, give me a few realistic use cases" — (pushing from abstract to concrete before committing to the gate design)

> "since this is all geared toward demo let's do option A, but mention option C in the demo" — (the exact "label the seams" discipline applied at the CI-gate design level)

---

## Raw Stats for Demo Slides

### Corpus & Crawling (Steps 1-2)
- **Source documents:** 3 (M22-3, M22-4, VADIR ICD)
- **Articles crawled:** 237 (from JavaScript SPA via reverse-engineered API)
- **Total corpus size:** 27 MB raw HTML
- **Articles with tables:** 126 (53%)
- **Topic tree nodes:** 170

### Golden Evaluation (Step 2)
- **Golden queries:** 110
- **Query types:** 10 (table lookup, policy rule, cross-source, consulting SME, prod ops, contradiction, temporal, negative, ambiguous term, synthesis)
- **Queries using domain language (no system names):** 18
- **Validation scores (v2):** faithfulness 0.93, correctness 0.997, relevance 0.993
- **Hallucinations caught:** 1 fabrication → 4 contaminated answers → all fixed
- **Parallel eval subagents:** 3 (ran simultaneously)

### Metadata Enrichment (Step 3)
- **Heading extraction:** 0% → 100% coverage (1,863 headings, avg 7.9/article)
- **HTML heading patterns handled:** 3 (anchor-wraps-strong, anchor-then-strong, text-inside-open-strong)
- **Fields added:** acl, source_authority_tier, content_category
- **Fields removed:** keywords (low signal)
- **content_category evolution:** 5 categories → 1 (over-engineering eliminated)

### Parsing (Step 5)
- **HTML articles parsed:** 237 → 7.5 MB markdown
- **PDF parsed:** 1 (VADIR ICD) → 103K chars (after stripping 62K of noise)
- **Tables preserved:** 68 tables in largest article alone, all converted to pipe format
- **Validation sample:** 20 articles (14 pass, 6 fail on colspan — known markdown limitation)
- **PDF noise removed:** cover page OCR fragments + tripled Table of Contents
- **Colspan-affected articles:** 54 (445 broken rows) — dissolved by staying in HTML
- **Scripts written Steps 3+5 session:** 2 (enrich_metadata.py, parse_html_to_markdown.py — latter now deleted)

### Chunk Validation & Refactor (2026-04-14 session)
- **Validation subagents (parallel):** 4 — table structure, heading paths, type classification, oversized flagging
- **Issues caught by validation:** 46 multi-table chunks + 22 misclassified lists + 25 list fragments + 20 threshold-gap chunks
- **Code that moved from chunker to preprocessor:** 3 (layout-table unwrap, div-table unwrap, markdown-table detection removal)
- **Max chunk size before refactor:** 175,593 tokens
- **Max chunk size after refactor:** 49,708 tokens (71% reduction)
- **Chunks > 50K after row-group splitting:** 0 (was 10)
- **Layout-wrapper tables detected in corpus:** 9 articles (all in M22-4 addendums)
- **Div-wrapped table articles:** 8
- **Embedding strategy decision:** heading-only `embed_text` for 868 oversized chunks (saved ~$13 in Sonnet API calls)

### Database & Chunking (Steps 6-7)
- **Database:** pgvector/pg17 in Docker, port 5433, HNSW index
- **Embedding model:** mxbai-embed-large (1024 dims, open-source via HuggingFace) — replaces Titan V2
- **Total chunks:** 8,399 (237 HTML articles + 1 PDF)
- **Chunk types:** 6,890 text | 748 table | 761 list
- **Oversized chunks (>1024 tokens):** 548 — all tables, flagged for summary indexing
- **50K+ tables (deferred to Loop A):** 10
- **Largest table:** ~175K tokens
- **Token distribution:** <256: 3,042 | 256-512: 1,381 | 512-1024: 3,426 | >1024: 550
- **Heading patterns converted:** 4,963 section anchors, 178 subchapter anchors, 44 topic anchors
- **Articles with proper heading tags:** 31 (already had `<h2>`-`<h6>`)
- **Articles needing heading fix:** 164 (anchor-only `<a name>+<strong>`)
- **Articles with no heading structure:** 42 (single-chunk articles)
- **Archived articles:** 29 (tagged `archived: true`, keep `authority_tier: 1`)
- **Scripts deleted:** 1 (parse_html_to_markdown.py — entire markdown conversion step removed)
- **LangChain HTMLHeaderTextSplitter:** tested and rejected — strips HTML tags, destroys table structure. Replaced with custom splitter.
- **Chunking errors:** 0 (down from 19 before fixing pre-processor)
- **Splitting passes:** 3 (headings → element boundaries → size-based for oversized prose/lists)

### Step 9 Eval Harness + Loop A iterations (2026-04-14/15 session)
- **Golden set bugs caught by audit:** 14 ID mismatches (`VADIR_ICD` → full PDF basename) + 4 query-level issues (1 corpus-absent term, 2 wrong source IDs, 1 multi-source under-specification) + 2 missing-comma JSON parse errors
- **First baseline (v1, no rerank, full 110q):** Faithfulness 0.97, Answer Relevancy 0.85, Contextual Precision 0.40, Contextual Recall 0.45, Contextual Relevancy 0.43
- **HtmlRAG `clean_html()` test:** strips `<table>`, colspan, rowspan despite paper's "Lossless" claim — rejected
- **lxml-html-clean test:** preserves all structural attrs in safe_attrs allowlist — adopted, 65% size reduction on table chunks
- **Option B (BS4 cleanup AFTER chunking):** 6,489 chunks (boundaries identical to v1), Contextual Recall 0.75 → 0.75, **avg input tokens -20.6%**
- **Reranker memory bug:** O(n²) attention on 47K-token chunk → 13.84 GiB single allocation, full pipeline → 27 GB Python RSS
- **Reranker truncation cap (2K chars):** peak RSS 4 GB even with oversized chunks
- **Reranker lift (full 110q v2b):** Contextual Precision **+16.5pp** (0.40→0.57), Contextual Relevancy **+11.8pp** (0.43→0.55), Contextual Recall +5.3pp (0.45→0.51)
- **Deep-dive research:** 4 parallel subagents, 7 production teams researched — **none use Unstructured.io or Docling for HTML ingestion**
- **Contextual Retrieval via Anthropic Batches API:** 5,978/6,142 chunks (97% success), 4 min wall time, **$12.48** (50% off live API), 38.9M cache read tokens
- **Eval cadence tiers built:** Fast (5-10 min, $0.30, no DeepEval, 30q + cheap proxies), Medium (30 min, $1.50, 30q + DeepEval), Full (2h, $4.30, 110q + DeepEval)
- **Session-to-date Anthropic spend:** ~$30 (most of which is one-time contextualization)

### K-sweep diagnostic (2026-04-15 session)
- **Config:** 5 fast-mode runs, 30 queries each, varying `--k` ∈ {3, 5, 10, 20, 50}, **no rerank** (isolates pure index recall)
- **Wall time:** ~25 min total serial, **cost ~$1.50**
- **Source recall (gold doc in top-k):** 0.800 → 0.867 → 0.867 → 0.900 → **0.933** (monotonic climb — ranking-bound, not index-bound)
- **top1_source_match_rate:** **0.533 across every k** (best chunk is not the gold chunk half the time — ranking/chunking problem, not recall)
- **IDK rate:** 0.367 → 0.367 → 0.200 → 0.100 → 0.100 (long-context generator uses extra chunks well)
- **Keyword recall (proxy for CtxRec):** 0.731 → 0.757 → 0.873 → 0.917 → **0.958**
- **Avg input tokens:** 1.3k → 2.1k → 4.4k → 8.5k → 22.7k (10× cost from k=5 to k=50 — caps k somewhere around 10-20 in practice)
- **Decision unlocked:** raise `rerank_from` from 20 → 50 targets the 3-7% of queries where gold is rank 21-50 (in-bounds with Anthropic CR paper's 150→20 and Cohere's 100→10)

---

## Example Reference

### Ex. A: Dropped keywords

The `keywords` field from the KnowVA CMS was nearly useless — most articles had just the manual name with a trailing comma:

```json
"keywords": "m22-3,"
```

```json
"keywords": "m22-4, manual, overview, references, benefits, law, cfr. service"
```

Meanwhile `title`, `topic_breadcrumb`, and `heading_outline` already carry richer signal. Field removed from all 237 JSONs.

### Ex. B: HTML heading patterns

KnowVA CMS uses three non-semantic patterns instead of `<h2>`-`<h6>`:

**Pattern A — anchor wraps strong** (M22-4, most common):
```html
<a name="901"><strong>9.01  PURPOSE</strong></a>
```

**Pattern B — anchor then strong** (subchapter headings):
```html
<a id="SI" name="SI"></a> <strong>Subchapter I.   General Codes</strong>
```

**Pattern C — text after anchor, inside already-open strong** (M22-3):
```html
<a id="501" name="501"></a>5.01  SCOPE</span></span></strong>
```

**Bonus — word split across tags:**
```html
<a name="907"><strong>9.07  ENTITLEMENT C</strong></a><strong>ODES</strong>
```

The parser strips inline tags without inserting spaces (so `C` + `ODES` → `CODES`), then splits at block-level tag boundaries to avoid capturing body text.

### Ex. C: Heading extraction before/after

**Before** (from crawler output, all 237 articles):
```json
"heading_outline": [],
"heading_count": 0
```

**After** (M22-3 Chapter 5 — Quantitative Measurement):
```json
"heading_outline": [
  {"level": 1, "text": "CHAPTER 5. QUANTITATIVE MEASUREMENT"},
  {"level": 2, "text": "5.01 SCOPE"},
  {"level": 2, "text": "5.02 TYPES AND PURPOSES OF QUANTITATIVE MEASUREMENT"},
  {"level": 2, "text": "5.03 MEASUREMENT UNITS AND STANDARDS"},
  {"level": 2, "text": "5.04 AREAS OF QUANTITATIVE MEASUREMENT AND CURRENT REPORTS"},
  {"level": 2, "text": "5.05 UNMEASURED HOURS AND OTHER MEASURED HOURS"},
  {"level": 2, "text": "5.06 BORROWED/LOANED HOURS AND BROKERED WORK"},
  {"level": 2, "text": "5.07 CONCEPT OF CLASSIFICATION OF CLAIMS AND ACTIONS"},
  {"level": 2, "text": "5.08 GENERAL END PRODUCT CODE PRINCIPLES"},
  {"level": 2, "text": "5.09 END PRODUCT CODE GROUPS"},
  {"level": 2, "text": "5.10 SPECIFIC END PRODUCT CODE DETERMINATIONS"},
  {"level": 2, "text": "5.11 ANNOTATING END PRODUCTS"}
],
"heading_count": 12
```

Source: `data/knowva_manuals/articles/554400000060851.json`

Git command to see the "before" state (pre-enrichment):
```bash
git show cb55724~1:data/knowva_manuals/articles/554400000060851.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps({k: d[k] for k in ['heading_outline','heading_count','content_category','keywords']}, indent=2))"
```

### Ex. D: Enriched metadata JSON

Full enriched metadata for M22-3 Chapter 5 (showing all fields added in Step 3):

```json
{
  "article_id": "554400000060851",
  "source_type": "va_manual",
  "source_system": "knowva.ebenefits.va.gov",
  "topic_breadcrumb": ["M22-3", "Chapter 05 – Quantitative Measurement"],
  "manual_name": "M22-3",
  "title": "CHAPTER 5. QUANTITATIVE MEASUREMENT",
  "description": "This chapter reviews quantitative measurement, current reports, and end product classification.",
  "last_modified": "2017-06-28T19:37:53.000Z",
  "heading_outline": [{"level": 1, "text": "CHAPTER 5. QUANTITATIVE MEASUREMENT"}, "...11 more..."],
  "heading_count": 12,
  "contains_table": false,
  "content_category": "gov_docs_and_manuals",
  "acl": "public",
  "source_authority_tier": 1
}
```

Fields added this session: `acl`, `source_authority_tier`, `content_category`, populated `heading_outline`.
Fields removed: `keywords`.

### Ex. E: Parsed markdown — table

Branch of Service Codes from M22-4 Chapter 9 (article `554400000073086`). HTML `<table>` tags converted to markdown pipe format:

```markdown
**a.**  The following codes apply in chapter 32 claims:

|  |  |
| --- | --- |
| **[BDN] Code** | **Service** |
| A(Army) | Army |
| N(Navy) | Navy |
| M | Marine Corps |
| CG | Coast Guard |
| PHS | U.S. Public Health Service |
| AF | Air Force |
| WAC | Women's Army Corps |
| NOAA | Coast and Geodetic Survey, National Oceanic and Atmospheric Administration (formerly ESSA) |
```

This article alone has 68 tables, all preserved.

### Ex. F: Parsed markdown — prose

Overview of benefits from M22-4 Chapter 1 (article `554400000063441`). Links to U.S. Code preserved:

```markdown
**1.01 OVERVIEW OF BENEFITS**
(Updated: February 26, 2020)

---

This manual provides implementing instructions for the following education benefit
programs assigned to the Education Service within the Veterans Benefits Administration (VBA):

a. [Chapter 30, title 38, U. S. Code](https://uscode.house.gov/browse/prelim@title38/part3/chapter30&edition=prelim),
   All-Volunteer Force Educational Assistance Program (also known as the Montgomery GI Bill -
   Active Duty or MGIB).

b. [Chapter 32, title 38, U. S. Code](https://uscode.house.gov/browse/prelim@title38/part3/chapter32&edition=prelim),
   Post-Vietnam Era Veterans' Educational Assistance (also known as VEAP).
```

### Ex. G: PDF noise stripped

**Before** (Docling raw output — cover page OCR junk from VA seal):
```
RIMENT

DEP

UNITED STATES

AFFAIRS

## Department of Veterans Affairs Chapter 33 Long Term Solution...
```

**Before** (tripled Table of Contents — 62K of noise):
```markdown
| Introduction...1 | Introduction...1 | Introduction...1 |
|------------------|------------------|------------------|
| 1.1. Purpose...1 | 1.1. Purpose...1 | 1.1. Purpose...1 |
| 1.2. Scope.....1 | 1.2. Scope.....1 | 1.2. Scope.....1 |
```

**After** (clean — straight to content):
```markdown
## Department of Veterans Affairs Chapter 33 Long Term Solution (LTS) Web Service...

## Demographics

Interface Control Document

## Version 2.1.1 March 2022

## Revision History

| Date          | Version | Description                        | Author        |
|---------------|---------|------------------------------------|---------------|
| March 2022    | 2.1.1   | Renamed MGAB table to MGIB...     | Patrick Lewis |
```

### Ex. H: Colspan broken table

Rate tables in M22-4 Part 5 (article `554400000073756`) have merged header cells (`colspan`). Markdown can't represent cell merging, so when the column count changes mid-table, the pipe structure breaks:

```markdown
| FULL | $528.00 | $449.00 |              ← 3 pipes (correct)
| THREE-QUARTER | $396.00 | $336.75 |    ← 3 pipes (correct)
| **FLIGHT TRAINING:** Flight training... ← continuation row
|  | | | |                                ← 4 pipes (broken — colspan header)
| **TYPE OF TRAINING** | **PL 102-25  10-1-1991** | **PL 98-525  7-1-1985** |  | ← 5 pipes (broken)
| FULL | $275.00 | $250.00 |  |           ← 5 pipes (new rate period)
```

54 articles affected, 445 broken rows total. Community consensus: don't fix the pipe table — prepend an LLM-generated semantic description during chunking (Step 7) that captures what the merged header conveyed.

### Ex. I: DevTools API discovery

The KnowVA page renders as a JavaScript SPA — raw HTML is just a loading spinner. The API endpoint was discovered by watching XHR calls in Chrome DevTools Network tab:

```
https://www.knowva.ebenefits.va.gov/system/ws/v11/ss/article?$attribute=&$lang=en-us&$rangesize=1&$rangestart=0&portalId=554400000001018&topicId=554400000016107&usertype=customer
```

This returned XML (not JSON) — an eGain v11 self-service API. The article content endpoint:
```
https://www.knowva.ebenefits.va.gov/system/ws/v11/ss/article/554400000059318?$lang=en-us&portalId=554400000001018&usertype=customer
```

### Ex. J: $level parameter discovery

The topic API without `$level` always returned root-level topics regardless of `parentTopicId`. The SPA's own XHR calls revealed the missing parameter:

**Without $level** (returns root topics, useless for subtree discovery):
```
/ss/topic?parentTopicId=554400000016104&portalId=...
→ Returns: Burial & Memorial, Compensation and Pension, eBenefits... (root topics)
```

**With $level=5** (returns full subtree — the breakthrough):
```
/ss/topic/554400000016106?$level=3&$pagesize=1000&portalId=...
→ Returns: M22-4 with all 12 parts, all chapters within each part = 161 topics in one call
```

This eliminated Playwright entirely. The crawler went from "navigate SPA, click links, intercept responses" to "one HTTP GET per manual."

### Ex. K: XML namespace surprises

Three bugs from assuming standard XML structure:

**Bug 1 — Namespace prefixes:** Expected `<name>`, got `<ns2:name>`
```xml
<!-- Expected -->
<topic><name>M22-3</name><articleCount>0</articleCount></topic>

<!-- Actual -->
<ns2:topic childCount="8" id="554400000016105">
    <ns2:name>M22-3</ns2:name>
    <ns2:articleCount>0</ns2:articleCount>
</ns2:topic>
```

**Bug 2 — ID as attribute, not element:** Expected `<id>...</id>`, got `id="..."` on the tag
```xml
<!-- Expected -->
<ns2:article><id>554400000059318</id><ns2:name>CHAPTER 1...</ns2:name></ns2:article>

<!-- Actual -->
<ns2:article alternateId="KMPR-59318" id="554400000059318">
    <ns2:name>CHAPTER 1.  GENERAL</ns2:name>
</ns2:article>
```

**Bug 3 — Content as XML-escaped HTML:** Expected CDATA or raw HTML, got entity-encoded
```xml
<!-- Expected -->
<content><![CDATA[<p>The purpose of this manual...</p>]]></content>

<!-- Actual -->
<ns2:content>&lt;p style="text-align: center"&gt;&lt;strong&gt;CHAPTER 1...&lt;/strong&gt;&lt;/p&gt;</ns2:content>
```

Each required a separate debug iteration. Lesson: dump the raw response before writing any parser.

### Ex. L: Crawler output structure

Per-article output — HTML preserves all structure (headings, tables, lists, anchor links) with metadata in `<meta>` tags:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta name="source-system" content="KnowVA (knowva.ebenefits.va.gov)">
  <meta name="source-type" content="va_manual">
  <meta name="manual-name" content="M22-4">
  <meta name="article-id" content="554400000073486">
  <meta name="last-modified" content="2025-03-06T15:33:49.000Z">
  <meta name="topic-breadcrumb" content="M22-4 &gt; Part 03 – Claims Processing &gt; 01 – Administrative Issues">
  <meta name="content-category" content="Policy or Procedure">
</head>
<body>
<nav class="topic-breadcrumb">M22-4 / Part 03 – Claims Processing / 01 – Administrative Issues</nav>
<h1>PART 01, GENERAL. CHAPTER 1 - OVERVIEW OF THE MANUAL</h1>
<!-- original HTML content with tables, headings, lists intact -->
</body>
</html>
```

Companion JSON metadata aligned to pgvector schema:
```json
{
  "article_id": "554400000073486",
  "source_type": "va_manual",
  "topic_breadcrumb": ["M22-4", "Part 03 – Claims Processing", "01 – Administrative Issues"],
  "manual_name": "M22-4",
  "contains_table": true,
  "contains_list": true,
  "heading_outline": [{"level": 2, "text": "1.01 PURPOSE"}, "..."],
  "heading_count": 10,
  "content_category": "Policy or Procedure",
  "attachments": []
}
```

### Ex. M: Domain-language rewrites

Same query, before and after removing system names — tests whether RAG retrieves VADIR docs from domain context alone:

**Before** (names the system):
> "A VADIR getServicePeriods response shows purpleHeartIndCd = 'Y'. What benefit level does this veteran receive under Chapter 33?"

**After** (domain language only):
> "This veteran received a Purple Heart but only served 4 months. Does that affect their benefit percentage?"

The RAG must connect "Purple Heart" → VADIR purpleHeart data element AND "benefit percentage" → M22-4 benefit level chart (100% for Purple Heart recipients regardless of service length).

**Before:**
> "The VADIR resultsHash field changed between two getServicePeriods calls for the same veteran. What does this mean?"

**After:**
> "We pulled the same veteran's military service data twice and got different results. What could have changed and what should the system do?"

### Ex. N: Query voice progression

The golden set evolved through 5 voice levels, each pushed by the first brain:

**Level 1 — Textbook lookup** (50 queries):
> "What End Product Code is used for an original Chapter 35 claim?" → EPC 240

**Level 2 — Cross-source** (25 queries):
> "The veteran's record shows a Character of Service code 'H'. What does that mean for Chapter 33 eligibility?"

**Level 3 — Consulting SME** (10 queries):
> "Where could a valid military service code produce a wrong eligibility determination? What are the data quality risks in the handoff between service records and benefits policy?"

**Level 4 — Prod ops** (10 queries):
> "Since yesterday the service record system keeps returning transformation errors. What does that mean and what's the playbook?"

**Level 5 — Synthesis** (3 queries):
> "Walk me through what happens end-to-end from when a veteran submits a Chapter 33 application to when they receive their first housing allowance payment."

Each level requires retrieving from more sources and reasoning across more documents to answer.

### Git commands for live demo

Pull up "before" states from git history during a demo:

```bash
# Steps 1-2 commit (crawler + articles)
git show 784fed8 --stat | head -10

# Golden query set commit
git show c6de724 --stat

# Hallucination fix commit — show what changed
git show 99b79df --stat

# Eval v1 vs v2 — show the improvement
diff <(python3 -c "import json; d=json.load(open('data/eval_correctness.json')); print(d.get('average_score',0))") \
     <(python3 -c "import json; d=json.load(open('data/eval_correctness_v2.json')); print(d.get('average_score',0))")

# Show the hallucination propagation chain in the golden set diff
git diff 99b79df~1 99b79df -- data/golden_query_set.json | head -80

# Metadata before enrichment (Step 3) — empty headings, keywords present
git show cb55724~1:data/knowva_manuals/articles/554400000060851.json | python3 -m json.tool | head -30

# Metadata after enrichment — headings populated, keywords gone, new fields
git show a72f0f9:data/knowva_manuals/articles/554400000060851.json | python3 -m json.tool | head -30

# Diff showing keywords removal + heading addition for one article
git diff cb55724 a72f0f9 -- data/knowva_manuals/articles/554400000060851.json

# Step 3 commit (enrichment)
git show cb55724 --stat

# Step 5 commit (parsing)
git show a72f0f9 --stat
```

### Ex. O: Research knew but plan didn't

The buy-vs-build doc already had multi-representation indexing as a known pattern:

```
Source: docs/2026-04-12-rag-pipeline-buy-vs-build.md, line 287
```
> Multi-representation indexing for split tables (description prepended, summary chunks, HyDE questions, link metadata) — **None.** Discussed in blog posts (Microsoft Azure chunk enrichment; Unstructured insights) but not codified. **Build custom.**

The engineering evidence doc already said content types need separate handling:

```
Source: docs/2026-04-11-engineering-rag-evidence-and-howtos.md, line 302
```
> Use content-type-aware chunking. Code, prose, and tables behave very differently in retrieval. Real-world systems mix strategies per content type rather than applying one chunker to everything.

And the ingestion skills research had Docling's table export as a known capability:

```
Source: docs/2026-04-11-rag-ingestion-skills-research.md, lines 119-120
```
> Table handling: `export_tables.py` exports each PDF table as CSV/HTML/Markdown — directly enabling the "tables atomic + multi-representation" strategy you want.

Yet the Step 7 plan said: "Context blurbs must specifically address: (a) merged-cell tables — LLM description should capture the semantic meaning the colspan header conveyed." The research found the right answer; the plan took a shortcut.

### Ex. P: Zero-to-MCP updated outline

After the plan audit, two new steps added and downstream renumbered:

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
Loop D:       SCALE SOURCES    → one at a time, stabilize each
Loop E:       TUNE CONSUMERS   → as consumer base grows
```

Also identified hybrid search and contextual retrieval as gaps — both were in research docs and schema columns but missing from build steps. These are baseline components, not iteration improvements, so they need to be folded into Steps 6-8 rather than deferred.

### Ex. Q: Heading fix before/after

KnowVA HTML before pre-processing (article 554400000072991):
```html
<span style="font-size: 16px"><span style="font-family: arial, helvetica, sans-serif">
<a name="SI"></a><strong>SUBCHAPTER I.  OVERVIEW OF NOTICES OF EXCEPTION PROCESSING</strong>
</span></span>

<span style="font-size: 16px"><span style="font-family: arial, helvetica, sans-serif">
<a name="801"><strong>8.01 GENERAL</strong></a>
</span></span>
```

After `knowva_heading_fix.py`:
```html
<h2 id="SI">SUBCHAPTER I.  OVERVIEW OF NOTICES OF EXCEPTION PROCESSING</h2>

<h3 id="801">8.01 GENERAL</h3>
```

HTMLHeaderTextSplitter can now split on these. Across the corpus: 4,963 section anchors + 178 subchapter anchors converted.

Source: `scripts/knowva_heading_fix.py`, `data/knowva_manuals/preprocessed/`

### Ex. R: Chunk distribution

Final token distribution across 8,399 chunks after three-pass splitting (237 HTML articles + 1 PDF):
```
<256 tokens:    3,042  (36%)  — paragraph-sized, embed directly
256-512:        1,381  (16%)  — ideal range for embedding
512-1024:       3,426  (41%)  — large sections, embed directly
>1024:            550   (7%)  — oversized tables, need summary indexing
```

Chunk types: 6,890 text | 748 table | 761 list

Oversized breakdown (all tables):
```
1K-5K:    374  — summary index, full content fits in generation context
5K-10K:   107  — summary index, full content fits in generation context
10K-50K:   57  — summary index, may need truncation for generation
50K+:      10  — deferred to Loop A (row-group splitting needed)
```

Source: `data/knowva_manuals/chunks/all_chunks.json`

### Ex. S: Summary index schema design

The `document_chunks` table supports both regular and summary-indexed chunks in the same schema:

```sql
CREATE TABLE document_chunks (
    id              SERIAL PRIMARY KEY,
    document_id     INTEGER NOT NULL REFERENCES documents(id),
    chunk_index     INTEGER NOT NULL,
    content         TEXT NOT NULL,          -- full chunk (sent to LLM at query time)
    embed_text      TEXT NOT NULL,          -- what was embedded:
                                           --   regular: same as content
                                           --   oversized: LLM-generated summary
    embedding       vector(1024),          -- mxbai-embed-large
    heading_path    TEXT[],
    chunk_type      TEXT NOT NULL DEFAULT 'text',
    token_count     INTEGER,
    metadata        JSONB DEFAULT '{}'
);
```

The intentional mismatch: `embedding` is computed from `embed_text`, but `content` is what the LLM reads. For a 298-row rate table, the summary might be "Monthly benefit rates for Chapter 30 veterans by training type and enrollment status, effective dates from 1985-2023" — that's what the query matches against. The full table is what the LLM uses to answer "what's the full-time Chapter 30 rate?"

Source: `scripts/init_schema.sql`

### Ex. T: LangChain HTMLHeaderTextSplitter strips tables

Testing `HTMLHeaderTextSplitter` with a simple table:

```python
html = """
<h2>Section A</h2>
<p>Some intro text.</p>
<table><tr><th>Name</th><th>Code</th></tr><tr><td>Army</td><td>A</td></tr></table>
"""

splitter = HTMLHeaderTextSplitter(headers_to_split_on=[("h2", "h2")])
docs = splitter.split_text(html)
print(docs[1].page_content)
```

**Output (HTML tags stripped, table structure destroyed):**
```
Some intro text.
Name
Code
Army
A
```

**Expected (raw HTML preserved):**
```html
<p>Some intro text.</p>
<table><tr><th>Name</th><th>Code</th></tr><tr><td>Army</td><td>A</td></tr></table>
```

This is why we built a custom splitter. The column-header → cell relationship (`Name` maps to `Army`, `Code` maps to `A`) is gone in the stripped version. For the 748 table chunks in this corpus, that relationship is the entire point.

Source: tested in session, led to `split_html_by_headings()` in `scripts/chunk_documents.py`

### Ex. U: Black-box chunk validation

Four parallel subagents, each with a single mandate. Prompt shape (agent 1):

```
You are a black-box validator for a document chunking pipeline. You have NO
access to the chunking code — only the output.

File: data/knowva_manuals/chunks/all_chunks.json

Your job: Validate that all chunks with chunk_type: "table" have well-formed
HTML table structure. Check these things across ALL 748 table chunks:
  1. Every table chunk must contain <table> and </table> tags.
  2. No table chunks should contain MULTIPLE complete <table>...</table> blocks.
  3. No <table> tags should appear in non-table chunks. Sample 200 text and 200 list.
  4. Table HTML should not be truncated mid-tag.

Report: totals, pass/fail per check, up to 5 specific failure examples, verdict.
```

Excerpt from agent 1's verdict:

```
CHECK 2 — No table chunk contains multiple complete <table> blocks
FAIL — 46 of 748 table chunks contain 2+ <table> opens.

Top 5 examples:
| source_id            | chunk_index | # tables | Notes |
| 554400000073649      | 1           | 10       | Entire page's tables lumped together |
| 554400000308110      | 1           | 21       | Worst case — 21 tables in one chunk |
| 554400000263561      | 1           | 12       | Long VADIR-style document, 12 tables |
```

The black-box format forces the agent to reason from the artifact, not from the code's intent. Same pattern as the golden set validation subagents.

### Ex. V: Div-wrapped tables (the root cause of multi-table chunks)

Before preprocessor, KnowVA HTML delivered tables inside layout wrappers:

```html
<body>
  <h1>Article Title</h1>
  <div>                            <!-- wrapper -->
    <table>...table 1...</table>
  </div>
  <div>                            <!-- wrapper -->
    <table>...table 2...</table>
  </div>
</body>
```

The chunker iterated `soup.children` — saw two `<div>` elements, not two `<table>` elements. Both tables ended up in the same chunk.

After `unwrap_div_tables()` in the preprocessor:

```html
<body>
  <h1>Article Title</h1>
  <table>...table 1...</table>     <!-- now top-level -->
  <table>...table 2...</table>     <!-- now top-level -->
</body>
```

Now the chunker's element-boundary split sees each table individually.

Layout tables were similar but worse — the outer `<table>` had one mega-row containing all the data in nested tables:

```html
<table>                              <!-- layout wrapper -->
  <tr><td>Title</td></tr>
  <tr><td>
    <table>...actual data, 30 rows...</table>
    <table>...actual data, 30 rows...</table>
    ...20 more tables...
  </td></tr>
</table>
```

`unwrap_layout_tables()` detects these (one row has >90% of the table's tokens) and replaces the outer `<table>` with its cell contents as block-level `<div>`s — surfacing the 20 nested tables as top-level elements the chunker can split on.

Source: `scripts/knowva_preprocess.py`

### Ex. W: Preprocessor vs chunker split

Before refactor (everything in the chunker):

```python
# chunk_documents.py
def _extract_boundary_elements(element):
    """Recursively unwrap <div> wrappers to find nested tables."""
    ...

def detect_chunk_type(content):
    """Classify chunk as text/table/list."""
    if "<table" in content.lower() or "| ---" in content:  # <-- markdown fallback leaked in
        return "table"
    ...

def _find_splittable_table(soup):
    """Handle layout-wrapper tables: if outer has few rows..."""  # <-- CMS quirk
    ...
```

After refactor (source-specific logic in the preprocessor):

```python
# knowva_preprocess.py
def unwrap_layout_tables(html):
    """Replace layout <table> wrappers with their content as block elements."""
    # KnowVA-specific: outer table with one mega-row holds all content
    ...

def unwrap_div_tables(html):
    """Lift <table> elements out of <div> wrappers."""
    ...

# chunk_documents.py
def detect_chunk_type(content):
    if "<table" in content.lower():  # HTML only
        return "table"
    ...

def _find_splittable_table(soup):
    """Find the largest table with enough rows to split."""
    # no layout-wrapper handling — preprocessor handled it
    ...
```

New sources get their own `<source>_preprocess.py`. The chunker stays generic.

Source: `scripts/knowva_preprocess.py`, `scripts/chunk_documents.py`

### Ex. X: Heading-only embed_text for oversized chunks

For a 12,310-token table in article 554400000061193 ("APPENDIX A - EDUCATION END PRODUCT CODES FOR QUANTITATIVE MEASUREMENT"), the chunker flags it oversized. Instead of sending it to Claude Sonnet for a summary, `embed_text` is built from metadata:

```python
def build_embed_text(chunk):
    if not chunk["oversized"]:
        return chunk["content"]  # regular chunk: embed the content

    title = chunk["source_metadata"]["title"]
    heading_parts = [h for h in chunk["heading_path"] if h and h != title]
    heading = " > ".join(heading_parts)
    return " | ".join(p for p in [title, heading] if p)
```

Result for the APPENDIX A table:
```
embed_text: "APPENDIX A - EDUCATION END PRODUCT CODES FOR QUANTITATIVE MEASUREMENT"
content:    "<table>...12,310 tokens of end-product-code rows...</table>"
```

At query time: the embedding matches "education end product codes" queries via the descriptive title. The full table gets served to the LLM for answering.

Tradeoff: content-level queries ("what EPC is used for Chapter 35 original claims?") won't match via the summary alone — they'd need either the title to mention the EPC number (it doesn't) or a retrieval-time fallback. Escape valve: add a `retrieve_full_doc` MCP tool later.

Cost: $0 (vs. ~$13 for Sonnet-generated summaries on 868 oversized chunks).

Source: `scripts/embed_and_store.py`

### Ex. Y: Golden set malformed JSON

`data/golden_query_set.json` had been unparseable since creation — two missing commas between query objects. Caught only when the eval scripts tried to load it.

Before (lines 511-516):
```json
      "tags": ["VADIR", "LTS", "eligibility_flow", "cross_source"]
    }
  ],
    {
      "id": 51,
```

After:
```json
      "tags": ["VADIR", "LTS", "eligibility_flow", "cross_source"]
    },
    {
      "id": 51,
```

Two such errors (lines 513 and 738). Auto-fixed via Python loop that detects `}` followed by `{` on consecutive non-empty lines and inserts the comma.

Result: file now parses to 110 queries matching the summary `total_queries: 110`.

Source: `data/golden_query_set.json`

### Ex. Z: Golden set audit pattern

`scripts/audit_golden_set.py` enforces structural checks against the corpus — never against retrieval results.

Audit found **14 queries** with `expected_source_id: "VADIR_ICD"` that doesn't exist in the DB:

```
--- 14 queries with missing expected_source_id ---
  id= 28 expected=['VADIR_ICD'] type=table_lookup
    Q: What are the five VADIR web service operations available through VSCH33Service?WSDL?
  id= 29 expected=['VADIR_ICD'] type=technical_spec
  ...
```

DB stores the full PDF basename: `VADIR_CH33_LTS_WS_V2.1.1_ICD_20220509`. Auto-fixed all 14 to use the actual ID.

The discipline rule (committed to plan doc):
- ✅ Allowed: "expected_source_id doesn't exist in DB" → fix
- ✅ Allowed: "key terms from expected answer don't appear anywhere in expected source article" → mark for rewrite
- ✅ Allowed: "multiple corpus articles equally cover the topic" → expand `expected_source_ids` list
- ❌ Forbidden: "our retrieval missed it, so loosen the check" → that's overfitting

Source: `scripts/audit_golden_set.py`

### Ex. AA: HtmlRAG vs lxml-html-clean colspan test

HtmlRAG's published paper claims "Lossless HTML Cleaning" preserving colspan/rowspan. Synthetic test proved otherwise:

Input:
```html
<table border="1" class="MsoTableGrid" style="width: 600px">
<tbody>
<tr><th rowspan="2">Year</th><th colspan="2">Enrollment</th></tr>
<tr><td>Full-time</td><td>Part-time</td></tr>
<tr><td>2024</td><td>100</td><td>50</td></tr>
</tbody></table>
```

`htmlrag.clean_html()` output:
```html
<tbody>
<tr><th>Year</th><th>Enrollment</th></tr>
<tr><td>Full-time</td><td>Part-time</td></tr>
<tr><td>2024</td><td>100</td><td>50</td></tr>
</tbody>
```

Verdict: `<table>` stripped. `colspan` stripped. `rowspan` stripped. **Fails the only invariant we cared about.**

`lxml_html_clean.Cleaner(safe_attrs={'href','src','alt','colspan','rowspan'})` output on same input:
```html
<table>
<tbody>
<tr><th rowspan="2">Year</th><th colspan="2">Enrollment</th></tr>
<tr><td>Full-time</td><td>Part-time</td></tr>
<tr><td>2024</td><td>100</td><td>50</td></tr>
</tbody></table>
```

All three preserved. Used `lxml_html_clean`. Achieved 65% size reduction on real table chunks.

Source: `scripts/chunk_documents.py:_HTML_CLEANER`

### Ex. BB: Option B — boundaries vs content separation

The wrong move (BS4 cleanup BEFORE chunking):

| Metric | v1 (no clean) | v2 (clean before chunk) | Δ |
|---|---|---|---|
| Chunk count | 6,489 | 5,355 | -17% (boundaries shifted) |
| **Contextual Recall (10q subset)** | **0.75** | **0.50** | **-25pp** 🔴 |

Cleanup unwrapped `<span>` tags that the heading-splitter was using as structural anchors. Different boundaries → different embeddings → demoted right chunks.

The right move (Option B: BS4 cleanup AFTER chunking, per-chunk on final content):

| Metric | v1 | v2b (clean after chunk) | Δ |
|---|---|---|---|
| Chunk count | 6,489 | 6,489 | identical (boundaries preserved) |
| Contextual Recall | 0.75 | 0.75 | flat ✅ |
| Avg input tokens / query | 3,330 | 2,643 | **-20.6%** ✅ |

Code change in `chunk_documents.py:chunk_html_file`:
```python
chunks = finalize_chunks(element_chunks, source_id, metadata)
# Apply BS4 post-pass AFTER chunk boundaries are set, so cleanup doesn't
# shift boundaries. Recompute token_count + oversized flag from cleaned content.
for c in chunks:
    cleaned = _bs4_post_pass(c["content"])
    c["content"] = cleaned
    c["token_count"] = count_tokens(cleaned)
    c["oversized"] = c["token_count"] > OVERSIZE_THRESHOLD
return chunks
```

Lesson: boundary preservation and content cleanup are independent dimensions. Bundle them and you can't tell which one caused a regression.

Source: `scripts/chunk_documents.py`

### Ex. CC: Reranker OOM reproducer

`scripts/debug_rerank_mem.py` instruments each pipeline stage with RSS deltas:

```
device=mps  with_embedder=False  n_docs=20  doc_tokens=500
[   0.0s] RSS=    21 MB  (Δ +0 MB)  startup
[   2.9s] RSS=   436 MB  (Δ +415 MB)  before rerank load
[   6.0s] RSS=  1676 MB  (Δ +1240 MB)  after rerank load
[  13.7s] RSS=  1676 MB  (Δ +0 MB)  after rerank call 1/3
[  20.0s] RSS=  1676 MB  (Δ +0 MB)  after rerank call 2/3
[  26.4s] RSS=  1676 MB  (Δ +0 MB)  after rerank call 3/3
Peak RSS: 1676 MB
```

Same test with 5K-token docs:
```
RuntimeError: Invalid buffer size: 13.84 GiB
```

In production, our v2b corpus has chunks up to 47K tokens (oversized tables). 47,000² × 4 bytes (fp32 attention matrix) = 8.8 GB *per chunk*. Top-20 of those = 27 GB.

Fix in `scripts/rerank.py`:
```python
RERANK_MAX_CHARS = int(os.environ.get("IKB_RERANK_MAX_CHARS", "2000"))

def _rerank_text(c: dict) -> str:
    heading = " > ".join(c.get("heading_path") or [])
    content = c["content"][:RERANK_MAX_CHARS]
    return f"{heading}\n\n{content}" if heading else content
```

Cross-encoders are trained on ≤512-token passages anyway. Truncating doesn't hurt ranking quality.

Result: peak 4 GB even with 47K-token chunks in the rerank set. No OOM.

Source: `scripts/rerank.py`, `scripts/debug_rerank_mem.py`

### Ex. DD: Reranker headline lift (full 110-query baseline)

Same chunks (v2b post Option B), same generation (Sonnet 4.6 temp=0), same scoring (Haiku DeepEval). Only difference: with rerank, retrieval pulls top-20 from cosine then mxbai-rerank-base-v2 picks top-5.

| Metric | v2b baseline (cosine top-5) | v2b + rerank (cosine top-20 → rerank top-5) | Δ |
|---|---|---|---|
| Faithfulness | 0.969 | 0.961 | -0.008 (within noise) |
| Answer Relevancy | 0.832 | 0.857 | +0.025 |
| **Contextual Precision** | **0.400** | **0.565** | **+0.165 🚀** |
| Contextual Recall | 0.453 | 0.506 | **+0.053** |
| **Contextual Relevancy** | **0.434** | **0.552** | **+0.118 🚀** |

Cost & wall time:
- Generation: $1.13 vs $1.32 with rerank
- Generation time: 583s vs 4,497s (rerank adds ~30s/query for 20-doc cross-encoder pass)
- Scoring: ~$3, 55 min, identical for both

The CtxPrec/CtxRel jumps validated the "k=5 has 60-70% noise" diagnosis from earlier sessions — reranker is the proper fix.

Source: `data/eval_v2b.scores.json`, `data/eval_v2b_rerank.scores.json`

### Ex. EE: Deep-dive decision table

The unexpected finding from `/deep-dive` skill research (4 parallel subagents):

| Team | HTML parser | Chunking strategy |
|---|---|---|
| Uber Genie | Custom: Google Docs API → HTML, custom loader | Structure-aware; Post-Processor Agent re-orders by source position |
| Dropbox Dash | In-house | **Query-time chunking** — docs NOT pre-chunked at index time |
| LinkedIn RAG (arXiv 2404.17723) | Custom: tickets → trees → knowledge graph | Hierarchical; chunks within graph nodes |
| Atlassian Rovo | Native Confluence/Jira connectors | Hybrid retrieval, Llama-Nemotron-Embed-1B |
| Notion AI | Apache Hudi + Kafka + Debezium CDC data lake | Not disclosed |
| Spotify AiKA | Backstage plugins | Not disclosed |
| Anthropic cookbook | No parser prescribed | **Fixed-size ~800 + Contextual Retrieval** |

**None use Unstructured.io or Docling for HTML ingestion.** Six of seven teams went custom. Anthropic doesn't even prescribe a parser.

The biggest lever surfaced: Anthropic's Contextual Retrieval — published −35% retrieval failure rate from prepending LLM-generated context per chunk.

Lesson: framework dismissals based on "covers ~60% of needs" weren't wrong — they were normal. The production-RAG playbook is custom parsers + smart augmentation (CR, reranker, hybrid).

Source: `docs/deep-dive/2026-04-14-html-rag-ingestion-state-of-art.md`

### Ex. FF: Batches API custom_id pattern bug

Smoke test on 2 docs (both with pure-digit source IDs) passed cleanly. Full submission failed at request 6,074:

```
anthropic.BadRequestError: Error code: 400 - {'type': 'error', 'error': 
{'type': 'invalid_request_error', 
'message': "requests.6074.custom_id: String should match pattern 
'^[a-zA-Z0-9_-]{1,64}$'"}}
```

The offending source_id: `VADIR_CH33_LTS_WS_V2.1.1_ICD_20220509` — contains dots from the version suffix.

Fix (`scripts/contextualize_chunks.py`): build a reversible token map, persist in batch state for the poll-resume phase:

```python
def _sid_token(source_id: str) -> str:
    if source_id in _SID_TO_TOKEN:
        return _SID_TO_TOKEN[source_id]
    safe = re.sub(r"[^a-zA-Z0-9]+", "_", source_id).strip("_")[:50]
    base = safe; n = 1
    while safe in _TOKEN_TO_SID and _TOKEN_TO_SID[safe] != source_id:
        safe = f"{base}_{n}"[:50]; n += 1
    _SID_TO_TOKEN[source_id] = safe
    _TOKEN_TO_SID[safe] = source_id
    return safe
```

Lesson: smoke tests need at least one of every weird input class. Pure-digit IDs masked the dot bug entirely. Cost: ~1 hour debug, $0 (failed before any cost incurred).

Successful resubmit: 5,978/6,142 chunks (97% success), $12.48, 4 min wall time.

Source: `scripts/contextualize_chunks.py`

### Ex. GG: Fast mode CLI output

`run_eval.py --fast --baseline eval_v2b_rerank.raw.json` runs 30 queries with no DeepEval, prints cheap proxies + delta vs baseline:

```
Running 30 queries (k=5)  rerank_from=20...
  [  1/30] id=  1  top1_match=True  topk_match=True  tokens_in= 2770 out=124
  [  2/30] id=  2  top1_match=True  topk_match=True  tokens_in= 5244 out= 83
  ...

============================================================
  FAST PROXIES  (n=30)
============================================================
  top1_source_match_rate           0.567     vs base 0.500     Δ +0.067 ▲ ✓
  topk_source_match_rate           0.733     vs base 0.667     Δ +0.067 ▲ ✓
  answer_keyword_recall_mean       0.612     vs base 0.554     Δ +0.058 ▲ ✓
  idk_rate                         0.300     vs base 0.367     Δ -0.067 ▼ ✓
  avg_input_tokens                 2643      vs base 3330      Δ -687.000 ▼ ✓

  baseline: eval_v2b_rerank.raw.json  matched n=30
  (fast mode: DeepEval scoring skipped — run scripts/score_eval.py for full metrics)
```

Sign convention: ▲ = increase, ▼ = decrease. ✓ = better-by-direction (lower IDK and tokens = better). 5 minutes wall time, ~$0.30 cost.

Source: `scripts/run_eval.py:cheap_proxies`, `scripts/run_eval.py:print_proxies_with_delta`

### Ex. HH: Failure-class segmentation — the "not a single failure mode" finding

Aggregate Contextual Recall on v2bcr+rerank: 0.52 (33 of 110 queries scored ≤ 0.15).

Segmenting those 33 failures by query characteristics surfaced **two distinct failure classes**:

**Class 1 — Exact-token precision loss (27/33 = 82%):**
| id | Query (excerpt) | Missing token |
|----|----|----|
| 24 | "What End Product Code is used for an original Chapter 35 claim?" | "240" (EPC 240) |
| 34 | "What does VADIR project code '9GY' represent?" | "9GY" |
| 39 | "What does the VADIR exclusionPeriod 'exclusionPerdTyp' field contain?" | "exclusionPerdTyp" |
| 40 | "What VADIR error code means 'Invalid Search Criteria'?" | specific error code |
| 46 | "What transaction code in Benefits Manager represents a work study allowance?" | specific transaction code |
| 60 | "ServicePeriod shows svcCd = 'F' and statute = '9B7'..." | specific field values |

Pattern: the answer is a specific literal token. Dense embeddings treat "EPC 240" and "EPC 250" chunks as near-identical. BM25 discriminates instantly.

**Class 2 — Multi-source synthesis (6/33 = 18%):**
| id | Query (excerpt) | Why hard |
|----|----|----|
| 81 | "Service record lookups are regularly taking longer than they should. What downstream processes break?" | Requires stitching SLA spec + downstream failure modes across sections |
| 84 | "How would we catch it if a veteran has been getting the wrong benefit level for years...?" | Detection mechanisms span 4+ layers |
| 91 | "Military service record responses doubled in size over the past month. Should we be concerned?" | Payload semantics + freshness + DMDC patterns |
| 93 | "Fail over to DR environment. What changes?" | ICD Section 5.1 + Section 7.4 |
| 95 | "Scheduled maintenance window for eMPWR. Impact on in-flight work?" | Transition timeline + BT lifecycle |
| 106 | "When someone says 'the master record,' what system?" | Time-and-chapter disambiguation |

Pattern: no single chunk contains the answer. Requires retrieving, then synthesizing across 2-4 sources.

**Different diseases. Different treatments.** Hybrid retrieval (BM25 + dense + RRF) fixes Class 1 almost entirely. Query decomposition + HyDE fixes Class 2. Neither alone fixes both.

Source: analysis output of `data/eval_v2bcr_rerank.scores.json`

### Ex. II: Post-eval analysis protocol

Added to plan doc step 9 + project CLAUDE.md as a mandatory practice after every eval — baseline, Loop iteration, or production measurement.

```
Post-eval analysis protocol:
(a) Segment by query_type — compute per-metric means. Aggregates hide
    bimodal distributions.
(b) Pull 2-3 representative failures per cluster — query + expected +
    retrieved chunks + judge reasoning.
(c) Name failure patterns — specific mechanism ("exact-code-in-table
    buried by dense embedding noise"), not generic ("retrieval issue").
(d) Map patterns to levers — which plan step / intervention targets each.

Anti-pattern: proposing next intervention directly from aggregate deltas.
That tunes blindly. Reranker lifted Precision 16.5pp AND masked that 33
queries still had Recall ≈ 0 — the kind of thing aggregates can't show.
```

Captured in:
- `docs/2026-04-11-engineering-rag-evidence-and-howtos.md` § "From Zero to Knowledge MCP" step 9
- `CLAUDE.md` (project) — always loaded
- `~/.claude/lessons.md` + `lessons-detail.md` — generalizes beyond RAG

### Ex. JJ: Why hybrid retrieval was promoted above HyDE in the plan

**Before failure-class analysis** (plan doc original order): Step 11 Reranker → Step 12 HyDE → Step 13 CRAG → Loop B (included hybrid).

**After failure-class analysis:**

| Failure class | Size | Best lever | Effort |
|---|---|---|---|
| Exact-token precision | 27 queries | **Hybrid retrieval (BM25 + dense + RRF)** | ~100 lines, no API cost |
| Multi-source synthesis | 6 queries | HyDE + query decomposition | ~200 lines, +$0.001/query |
| Vocabulary mismatch | Few | HyDE | Same as above |
| Image-content gap | 1-2 queries | OCR / vision (big lift, narrow) | High effort, narrow scope |
| Corpus-absent | 1-2 queries | Expand corpus (Loop D) or mark unanswerable | Outside current scope |

Hybrid targets the largest class with the smallest footprint. HyDE addresses a smaller class at ~2x the code and a per-query API cost. **Easy prioritization call, invisible without the class segmentation.**

Revised order:
```
Step 11. Reranker              ✓ done
Step 12. K-sweep diagnostic     — ranking-bound vs index-bound?
Step 13. Hybrid retrieval       — promoted: targets largest failure class
Step 14. HyDE + query decomposition
Step 15. CRAG
Loop B.  Full retrieval tuning
```

Source: this session's analysis of `data/eval_v2bcr_rerank.scores.json`

### Ex. KK: Metric evolution across Loop A iterations — the ups and downs

Full-110-query DeepEval scores across every iteration. Shows that every intervention was evaluated head-to-head (same queries, same judge) and promoted only if it earned its keep.

| Iteration | Chunks | Retrieval | Faith | AnsRel | CtxPrec | CtxRec | CtxRel | Tokens/q |
|---|---|---|---|---|---|---|---|---|
| v1 baseline | 6,489 | cosine top-5 | 0.97 (subset) | 0.85 (subset) | 0.50 (subset) | 0.75 (subset) | 0.54 (subset) | 3,330 |
| v2 (BS4 pre-chunk) | 5,355 | cosine top-5 | 0.99 (subset) | 0.89 (subset) | 0.47 (subset) | **0.50** (subset) | 0.52 (subset) | n/a |
| **v2b** (Option B: BS4 post-chunk) | **6,489** | cosine top-5 | 0.97 | 0.83 | 0.40 | 0.45 | 0.43 | **2,643 (-21%)** |
| **v2b + rerank** | 6,489 | cosine top-20 → rerank top-5 | 0.96 | 0.86 | **0.57 (+17pp)** | 0.51 (+5pp) | **0.55 (+12pp)** | 2,800 |
| **v2bcr + rerank** | 6,489 | contextualized embed + rerank | 0.95 | **0.91 (+5pp)** | 0.61 (+4pp) | 0.52 (+1pp) | 0.56 (+1pp) | 2,693 |

Notes on the trajectory:
- **v2 was REVERTED** — BS4-before-chunking shifted heading splitter boundaries and crashed Recall -25pp. Rollback restored v1 state. The eval caught this before it became the baseline.
- **v2b Option B** recovered boundary preservation while keeping the token savings. Recall held flat, cost dropped 20%. Kept.
- **Reranker** delivered the biggest single-iteration lift. Precision +16.5pp, Relevancy +11.8pp.
- **Contextual Retrieval** delivered a modest lift on top of rerank (AnsRel +5pp). Anthropic's published +35% recall claim did NOT replicate at our scale — CR overlaps with what reranker already does.

**Cumulative effect (v1 → v2bcr+rerank):** AnsRel +9%, CtxPrec +52%, CtxRec +14%, CtxRel +28%. Two interventions (Option B, reranker) delivered the bulk; CR was incremental.

Source: `data/eval_v2b.scores.json`, `data/eval_v2b_rerank.scores.json`, `data/eval_v2bcr_rerank.scores.json`

### Ex. LL: K-sweep diagnostic table

Five fast-mode runs, 30 queries each, **no rerank** to isolate pure index recall. Varied `--k` only. 25 minutes total, ~$1.50.

| k | topk recall | top1 | ans-kw recall | idk rate | avg_in_tokens |
|---|---|---|---|---|---|
| 3  | 0.800 | 0.533 | 0.731 | 0.367 | 1,272 |
| 5  | 0.867 | 0.533 | 0.757 | 0.367 | 2,149 |
| 10 | 0.867 | 0.533 | 0.873 | 0.200 | 4,363 |
| 20 | 0.900 | 0.533 | 0.917 | 0.100 | 8,506 |
| 50 | **0.933** | 0.533 | **0.958** | 0.100 | 22,682 |

Two key signals:

1. **Source recall climbs monotonically (0.80 → 0.93).** Gold docs ARE in the index — just ranked 21-50 for ~3-7% of queries. Not a plateau = not index-bound.
2. **top1 frozen at 0.533 across every k.** The best-scoring chunk is not the gold source half the time, regardless of pool size. Widening retrieval doesn't fix this — it's a ranking or chunking problem.

**Diagnosis:** ranking-bound. Levers that help: wider rerank pool (20 → 50), HyDE (better query vectors), hybrid retrieval (BM25 rescues exact-token queries). Levers that don't: bigger corpus, different embedder, more chunks.

Source: `data/ksweep_k{3,5,10,20,50}.raw.json`, logs in `data/ksweep_logs/`

### Ex. MM: Metric priority in the long-context era

The five DeepEval metrics don't all matter equally anymore. As LLM context windows grew (100K+) and filtering got stronger, the hierarchy shifted. This table maps each metric to:
- How raising `k` changes it (proxy for retrieval breadth)
- How much it matters for **answer quality**
- Whether it has a separate role (cost, diagnostics)

| Metric | Effect of ↑k | Quality impact | Other role |
|---|---|---|---|
| Faithfulness | ~flat | **Still #1** — hallucination gate | — |
| Answer Relevancy | ↑ | High — this is what users feel | — |
| **Contextual Recall** | ↑↑ | **High** — if gold chunk is missing, nothing else matters | — |
| **Contextual Precision** | ↓ or flat | **Lower than it used to be** — LLMs filter junk well | **Cost, latency, distractor risk** |
| **Contextual Relevancy** | ↓ | Lowest — non-rank-weighted signal-to-noise | **Pipeline health diagnostic** |

**Revised priority for long-context RAG:** Faith = AnsRel > CtxRec > CtxPrec > CtxRel.

**CtxPrec is still useful** — just not as a quality metric. It governs:
- **Cost** — k=50 is ~$0.07/query vs k=5 at ~$0.006 (10× at scale)
- **Latency** — input tokens dominate gen latency for most models
- **Distractor failure mode** — semantically-similar-but-wrong chunks in repetitive domain corpora (VA manuals with shared boilerplate) pull answers off-topic. Faithfulness regressions live here.
- **Downstream consumers** — if MCP serves another agent, cluttered context = cluttered citations

**CtxRel is most useful as a debugging lens, not a quality metric:**
- Low CtxRel + high CtxRec = **index is noisy** (near-duplicates, base64 blobs, image-only chunks, over-fine chunking). Cue to run Loop A cleanup.
- Low CtxRel + low CtxRec = **index is broken** (wrong corpus, bad embeddings).
- High CtxRel + low CtxRec = **index is clean but missing content** (need more/better sources).

On our dataset, CtxRel tracked CtxPrec closely (0.43 → 0.55 → 0.56) — queries narrow enough that "relevant at all" and "relevant at top" line up.

**Industry convergence confirms this:** two-stage retrieval (retrieve wide 20-100, rerank narrow 3-10) is now the default. Anthropic CR paper: 150 → 20. Cohere: 100 → 10. Pre-long-context dogma of k=3-5 was a context-window limitation, not a quality principle.

Source: discussion in 2026-04-15 session; k-sweep data in Ex. LL; prior eval scores in Ex. KK

---

## Act 27: The MCP Gateway Layer (framework ≠ enterprise scaffolding)

### Moment 26: "The framework is a commodity. The gateway is the enterprise story."

**Context:** During ship-cut planning we evaluated whether FastMCP 3.x could scale for enterprise. The research answered a sharper question — the framework choice barely matters; the **gateway layer** sitting in front of it is where enterprise scaling actually lives.

**The architectural split:**

```
[Claude Desktop / Claude Code / Agent platform]   ← consumer LLM
         ↓
[MCP Gateway]  ← Kong Enterprise MCP, Lunar MCPX, TrueFoundry, MintMCP
   - OAuth / SAML / SSO
   - Rate limits, audit trail, policy enforcement
   - Multi-tenant routing, secrets management
   - Aggregated OTel / observability
         ↓
[FastMCP server]  ← business logic only
   - tools / resources / prompts
   - retrieval, domain logic
         ↓
[pgvector / your data]
```

**The key insight:** the gateway eats the cross-cutting concerns that make enterprise MCP expensive to build from scratch — SSO, SOC2 audit, multi-tenancy, rate limits, secret injection. All the major gateways treat the underlying MCP server as pluggable.

**Gartner signal worth quoting:** by 2026, 75% of API gateway vendors will ship MCP features. Kong already has. Lunar.dev is tracked as a Representative Vendor in the MCP Gateways category, SOC2 at Enterprise tier. This is the "API Management 2.0" consolidation — same shape as the 2014 API-gateway wave.

**Named players to cite:** Kong Enterprise MCP, Lunar MCPX, TrueFoundry MCP Gateway, MintMCP. Pick based on existing API gateway stack.

**TrueFoundry published numbers worth citing if asked:** 3–4ms gateway latency, 350+ req/s on a single vCPU.

**The anti-pattern worth naming:** "Per-server auth becomes a maintenance burden past ~3 servers." Teams that build SSO/audit/policy into each individual MCP server end up rebuilding it per server and break at scale. The whole point of the gateway pattern is *not* to do that.

### Example NN — Why the ship-cut deliberately doesn't build a gateway

Ship-cut discipline: **label the seams, don't half-build.** The `auth_context` parameter lives in the FastMCP tool signature (the seam). The gateway populates it in production. In the demo, it's `None`. Same rule applies to SSO, multi-tenancy, blue/green index, namespace isolation.

**Why not build a gateway for v1:**
- Buyers watching the video don't type into the demo, they book a call. Gateway adds zero narrative value pre-call.
- Kong / Lunar / TrueFoundry are paid/licensed or SaaS. Standing one up for the demo is 2–3 days of infra work that ships nothing new.
- Credibility comes from **labeling the seam correctly**, not building it. That's the thesis of the scaling table.
- Same category as SSO, multi-tenancy, blue/green — README stubs with named production paths.

**What would pull gateway into scope (not now):**
- A first consulting client specifically asking "can you show me gateway integration?" — that becomes billable discovery work, not demo work.
- Post-launch: if Show HN / Reddit comments consistently ask "but how do you handle SSO?" — that's the signal to build a second demo repo showing Kong or Lunar wiring. Different asset, not v1.

### Talking point — "Why FastMCP, not a custom server"

"The framework-selection research hit a fork: it wasn't really about frameworks. Python MCP frameworks are converging — FastMCP 1.0 was merged back into the official SDK, they share the same primitives. The real enterprise scaling question is the gateway in front of it. So we picked FastMCP 3.x for the server — fastest to ship, decorator-based, async-first, OpenTelemetry built in — and left the gateway as a labeled seam. Enterprise path: Kong, Lunar, or TrueFoundry. Same FastMCP server underneath."

### Talking point — "Why no gateway in v1"

"A gateway is a 2–3 day infra lift that doesn't change the narrative. Buyers watching this don't care whether SSO is wired — they care that I know *where* SSO goes. Naming the seam is stronger than half-building it. The `auth_context` parameter is the seam. Kong, Lunar, or TrueFoundry is the production fill. Same discipline as multi-tenancy, blue/green indexing, namespace isolation — labeled, not built."

### Quotables

- "The framework is a commodity. The gateway is the enterprise story."
- "Per-server auth becomes a maintenance burden past three servers. The gateway exists so you don't rebuild SSO seven times."
- "Gartner tracks MCP Gateways as a category now. SOC2-certified vendors exist. This is API Management 2.0."
- "Label the seams. Don't half-build them."
- "FastMCP was merged into the official SDK. Picking one over the other is a non-decision. Picking a gateway isn't."

### Stats block

- Gartner: **75% of API gateway vendors will ship MCP features by end of 2026**
- TrueFoundry published benchmark: **3–4ms gateway latency, 350+ req/s / vCPU**
- FastMCP Python single-pod ceiling: **~1,200 concurrent connections on 8GB RAM**
- Streamable HTTP shared-session throughput: **290–300 req/s** (vs 30–36 req/s unique-session — 10× penalty)
- Python vs Java/Go on MCP benchmark: **Python ≈ 18% of high-perf tier** — fine when retrieval latency dominates (our pgvector + rerank = 200–800ms)

Source: research + discussion in 2026-04-15 session (ikb-session-8); FastMCP framework evaluation, gateway landscape research

---

## Act 28: The MCP Server Ships (Tools + Resources + Prompts, 200 lines)

### Moment 27: "Most MCP servers only ship Tools. This one ships all three."

**Context:** After locking framework (FastMCP 3.x) and scoping out the gateway, the v1 MCP server was built as a thin wrapper over the existing `retrieve.py` + `rerank.py` pipeline. Intentionally exposed **Tools + Resources + Prompts** — the three most-used MCP capabilities — because 90% of public MCP servers only ship Tools, which is the reason critics call MCP "a REST API wrapper with extra steps."

**What the server offers ([Ex. OO](#ex-oo-mcp-server-core)):**
- **Tool `query(query, k, rerank_from, auth_context)`** — pgvector cosine → mxbai-rerank cross-encoder → top-k chunks with metadata
- **Resource `document://{source_id}`** — full raw HTML fetch for the `retrieve_full_doc` escape valve (designed in Ex. X, now real)
- **Prompt `cite_from_chunks`** — citation-heavy answer template, portable across any MCP client (Claude Desktop, Cursor, Windsurf)

**Production-scaling knobs baked in:**
- `--transport stdio` (default, for Claude Desktop / Code) ↔ `--transport http` (Streamable HTTP, gateway-fronted) — one-flag switch, no rewrite
- Logging routed to stderr only (stdout is reserved for JSON-RPC on stdio transport — a 2026 gotcha that breaks naive implementations)
- `auth_context: dict | None = None` on every tool — the enterprise gateway seam, typed and documented, does nothing in v1
- Hard guardrails: `MAX_K=20`, `MAX_QUERY_CHARS=2000`, empty-query rejection, k-clamping
- Every response carries `trace_id` + `latency_ms` — ready for OTel/Langfuse wiring next

**Smoke test (in-process via `fastmcp.Client`) — all 5 assertions green ([Ex. PP](#ex-pp-smoke-test-output)):**
1. Tools/resources/prompts register cleanly
2. `query` returns 3 chunks with full metadata (rerank=7.812, latency=26s incl. first-call model load)
3. `document://554400000073486` returns 52,875 chars of raw HTML
4. `cite_from_chunks` renders with citation rules
5. Guardrails: empty query → ToolError; k=999 clamped to 20

### Moment 28: "Label the seams. Data residency is a schema column, not a roadmap item."

Two infrastructure moves happened in the same session that quietly strengthen the pilot-to-prod scaling table without chasing new features:

**(a) Hybrid-ready schema ([Ex. QQ](#ex-qq-tsvector-migration)).** Added a `content_tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED` column + GIN index to `document_chunks`. All 6,489 existing rows populated automatically (Postgres back-fills generated columns on write, no migration script needed). BM25 wiring stays a post-launch spoke — but the README's "100k–1M docs" row of the scaling table is now truthful: *"Same schema. Scale via pgvector IVFFlat/HNSW indexes. No rewrite."*

**(b) Backup discipline.** 30MB `pg_dump -Fc` snapshot at `~/ikb-backups/ikb-20260415-1705.dump` — survives Docker Desktop factory reset, `docker compose down -v`, or Mac disk failure. Re-ingest cost if the volume is ever lost: ~1 hour machine time + $12.48 Anthropic Batches API spend. The backup takes 30 seconds and caps that risk.

### Moment 29: "There's no AWS-native Langfuse. The category exists for a reason."

**Context:** Before wiring observability, verified that no cloud-native equivalent obviated the need for a dedicated LLM observability tool. Research answered the question sharply.

**AWS's LLM-observability surface (2026):**
- **CloudWatch Application Signals for Bedrock** — auto-instruments Bedrock SDK calls, tracks latency/cost/tokens. Great if you're all-in on Bedrock; useless for multi-provider stacks.
- **Bedrock AgentCore Observability** — purpose-built for agent applications on Bedrock, emits OTel.
- **Pattern AWS itself recommends:** AgentCore → OTel → ship to Langfuse (per AWS-samples repo). AWS is implicitly acknowledging the gap by making AgentCore OTel-native rather than CloudWatch-locked.

**The gap ([Ex. RR](#ex-rr-aws-vs-langfuse-gap)):** Bedrock-only observability covers 60–70% of Langfuse. The LLM-native primitives (prompt versioning, LLM-as-judge evals attached to traces, golden-set datasets, shareable public dashboards) are missing from every cloud-native option.

**Decision:** Langfuse Cloud for v1 (multi-provider reality: Anthropic Batches + Haiku judge + local mxbai = not on Bedrock; free tier; shareable public link is on-brand for the demo's observability row).

**Portability safety net:** FastMCP 3.x emits OTel natively. If we ever swap Langfuse → Datadog / Honeycomb / Grafana Tempo, it's a config change, not a refactor. The README can honestly claim "standards-based instrumentation, not vendor-locked."

### Talking point — "Why Tools + Resources + Prompts"

"Most of the 12,000 MCP servers on PulseMCP ship Tools only. That's why the loudest MCP critique is 'it's just a REST API wrapper.' Tools + Resources + Prompts is a 2-hour differentiator that reframes the whole value prop — the server ships *affordances*, not just function calls. Consuming LLMs get a URI template for fetching full documents and a reusable citation-heavy prompt template for free. Same FastMCP server. Same pgvector. Three first-class protocol features instead of one."

### Talking point — "The tsvector column costs nothing and proves the architecture claim"

"A generated column is one ALTER TABLE away. Postgres auto-populates it on write — zero app-code changes. The GIN index builds in seconds at our 6K chunks. But the narrative return is outsized: the README's scaling table can now claim 'Same schema, scale via IVFFlat/HNSW, no rewrite' and point to a live column that proves it. That's the whole discipline — label the seams, but make sure the seams are real."

### Talking point — "Why not AWS App Signals"

"CloudWatch App Signals auto-instruments Bedrock. That's the entire value prop. Our stack has Anthropic direct (Batches API for Contextual Retrieval), Anthropic Haiku for the eval judge, and mxbai running locally for embeddings — zero of that traffic is visible to App Signals. Langfuse is provider-agnostic, which matches the reality of enterprise AI stacks in 2026: mixed Bedrock, direct API calls, and local models. AWS's own samples repo recommends piping AgentCore traces to Langfuse — which tells you everything."

### Quotables

- "Most MCP servers only ship Tools. That's why MCP gets called a REST API wrapper."
- "Tools + Resources + Prompts is a 2-hour differentiator that reframes the value prop."
- "The generated column is a seam you can point at. That's stronger than a roadmap bullet."
- "Backup takes 30 seconds. Losing the volume costs 1 hour and twelve dollars. Do the backup."
- "AWS's own docs route you through Langfuse. There's no shame in picking the right-shaped tool."
- "FastMCP speaks OTel. Langfuse speaks OTel. Swapping backends is a config change, not a refactor."
- "Label the seams. `auth_context=None` today is a gateway-populated dict tomorrow."

### Stats block

- **MCP server LOC:** 185 lines (`scripts/mcp_server.py`)
- **Smoke test:** 5/5 assertions pass, in-process via `fastmcp.Client`
- **First-call latency:** 26s (model load); steady-state ~3–4s / query (pgvector + rerank)
- **Guardrail ceilings:** `MAX_K=20`, `MAX_QUERY_CHARS=2000`
- **Schema addition:** `content_tsv` GENERATED column + GIN index, 6,489 rows back-filled automatically
- **Backup:** 30MB `pg_dump -Fc`, survives Docker factory reset
- **Re-ingest cost if volume lost:** ~1h machine time + $12.48 Anthropic Batches spend
- **FastMCP version:** 3.2.4 (released post-Jan-2026; FastMCP 1.0 was merged into the official Python MCP SDK)

---

### Ex. OO: MCP server core

**File:** `scripts/mcp_server.py` (excerpted)

```python
from fastmcp import FastMCP

mcp = FastMCP(
    "internal-knowledge-base",
    instructions=(
        "Retrieval over the VA Education corpus (M22-3, M22-4, VADIR ICD). "
        "Use `query` for question-answering; results come pre-reranked by "
        "cross-encoder. Use the `document://{source_id}` resource to fetch a "
        "full source document when chunk-level context is insufficient. Use "
        "the `cite_from_chunks` prompt to get a citation-heavy answer format."
    ),
)

# --- Tool -------------------------------------------------------------
@mcp.tool
def query(
    query: str,
    k: int = 5,
    rerank_from: int = 20,
    auth_context: dict[str, Any] | None = None,   # <-- the gateway seam
) -> dict:
    """Retrieve the top-k most relevant chunks for a natural-language query..."""
    t0 = time.time()
    q = _validate_query(query)
    k_out = _clamp_k(k)
    k_pool = max(k_out, min(MAX_K * 5, int(rerank_from)))

    candidates = retrieve(q, k=k_pool)            # pgvector cosine
    top = rerank(q, candidates, top_k=k_out)      # mxbai cross-encoder

    chunks = [ { ...flatten... } for c in top ]
    latency_ms = int((time.time() - t0) * 1000)
    trace_id = f"ikb-{int(t0 * 1000)}"
    log.info("query trace_id=%s k=%d ... top_score=%.3f auth=%s",
             trace_id, k_out, chunks[0]["rerank_score"], bool(auth_context))
    return {"query": q, "k": k_out, "chunks": chunks,
            "latency_ms": latency_ms, "trace_id": trace_id}

# --- Resource ---------------------------------------------------------
@mcp.resource("document://{source_id}")
def get_document(source_id: str) -> dict:
    """Return the full raw content + metadata for a source document."""
    with _get_conn().cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT ... FROM documents WHERE source_id = %s", (source_id,))
        row = cur.fetchone()
    if not row:
        raise ValueError(f"document not found: {source_id}")
    return dict(row)

# --- Prompt -----------------------------------------------------------
@mcp.prompt
def cite_from_chunks(user_question: str) -> str:
    """Answer the user's question using retrieved chunks with paragraph-level citations."""
    return (
        "You are answering a question over the VA Education corpus. Use the "
        "`query` tool to retrieve relevant chunks, then answer with these rules:\n"
        "1. Cite every non-trivial claim using `[source_id > heading_path]`.\n"
        "2. If the retrieved chunks don't contain the answer, say so plainly.\n"
        "3. Prefer direct quotes for regulatory or numeric content.\n"
        "4. If a chunk has `chunk_type: table`, preserve the table's structure.\n\n"
        f"User question: {user_question}"
    )

# --- Entrypoint (one-flag transport switch) --------------------------
if args.transport == "stdio":
    mcp.run()                                             # Claude Desktop / Code
else:
    mcp.run(transport="http", host=args.host, port=args.port)   # gateway-fronted
```

**Why this snippet matters:** the full production-scaling narrative fits in ~60 lines. Decorators do schema generation, sync-in-threadpool, URI routing, and JSON-RPC protocol handling. The three capabilities (Tools + Resources + Prompts) stack visibly. `auth_context` is the named seam. `mcp.run(transport=...)` is the stdio↔HTTP switch.

---

### Ex. PP: Smoke test output

**File:** `scripts/test_mcp_server.py` — runs the server in-process via `fastmcp.Client` and verifies 5 properties.

```
[PASS] registration: tools=['query'] prompts=['cite_from_chunks'] resources=['document://{source_id}']
[PASS] query: 3 chunks, top rerank=7.812 latency_ms=25995 trace_id=ikb-1776286503414
[PASS] resource: document://554400000073486 -> 52875 chars raw_content
[PASS] prompt: cite_from_chunks rendered with citation rules
[PASS] empty-query guard: ToolError
[PASS] k-clamp: requested 999, served 20

All smoke tests passed.
```

**Why this snippet matters:** real MCP server, real pgvector query, real rerank, real guardrail enforcement — all verified before involving the first brain. The `k-clamp: requested 999, served 20` line is the guardrail in action; the `top rerank=7.812` is a real cross-encoder score on a real VA Education query.

---

### Ex. QQ: tsvector migration + GIN index (honest "hybrid-ready" claim)

**Before** (`scripts/init_schema.sql`, `document_chunks` table):
```sql
embedding       vector(1024),                  -- mxbai-embed-large
heading_path    TEXT[],
chunk_type      TEXT NOT NULL DEFAULT 'text',
```

**After:**
```sql
embedding       vector(1024),                  -- mxbai-embed-large
content_tsv     tsvector GENERATED ALWAYS AS (to_tsvector('english', coalesce(content, ''))) STORED,
heading_path    TEXT[],
chunk_type      TEXT NOT NULL DEFAULT 'text',
...
-- GIN index for BM25/lexical search (hybrid-ready; wiring deferred to post-launch spoke)
CREATE INDEX idx_chunks_content_tsv ON document_chunks USING gin (content_tsv);
```

**Live migration (applied to ikb_pgvector container):**
```
docker exec ikb_pgvector psql -U ikb -d ikb -c "ALTER TABLE document_chunks
  ADD COLUMN content_tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', coalesce(content, ''))) STORED;"
ALTER TABLE

docker exec ikb_pgvector psql -U ikb -d ikb -c "CREATE INDEX IF NOT EXISTS idx_chunks_content_tsv
  ON document_chunks USING gin (content_tsv);"
CREATE INDEX

SELECT count(*) AS rows_with_tsv FROM document_chunks WHERE content_tsv IS NOT NULL;
 rows_with_tsv
---------------
          6489
```

**Why this snippet matters:** zero app-code changes, zero migration script, zero downtime. All 6,489 existing chunks populated automatically by Postgres (generated columns back-fill on write, and the generation expression is `STORED` so existing rows are evaluated at ALTER time). The README's "100k–1M docs scaling row" is now backed by a real column. Label-the-seam discipline, executed.

---

### Ex. RR: AWS-native vs. Langfuse — the observability gap table

| Feature | CloudWatch App Signals / AgentCore | Langfuse |
|---|---|---|
| Trace storage + viewer | ✅ | ✅ |
| Cost + token metrics | ✅ (Bedrock only) | ✅ (any provider) |
| OTel ingest | ✅ | ✅ |
| **Works with non-Bedrock LLMs** | ❌ | ✅ |
| **Prompt versioning / management** | ❌ | ✅ |
| **LLM-as-judge evals attached to traces** | ❌ (build with Lambda) | ✅ (built-in) |
| **Golden dataset management** | ❌ | ✅ |
| **Shareable public dashboard link** | ❌ (needs IAM) | ✅ |
| Free tier | CloudWatch free tier | Yes (50K obs/mo) |

**Tell:** AWS's own samples repo (`aws-samples/genai-llm-application-monitoring-on-aws`) routes AgentCore OTel traces to Langfuse or Grafana. When the cloud vendor's official pattern is "ship our traces to a third-party backend," the category gap is real.

**Implication for the demo:** Langfuse isn't a compromise choice — it's the correct-shaped tool for a multi-provider stack (Anthropic Batches + Haiku judge + local mxbai, none of which are on Bedrock). The FastMCP-emits-OTel → Langfuse-ingests-OTel pattern is vendor-neutral; swapping backends is a config change.

Source: 2026-04-15 session (ikb-session-8) — MCP server build, schema migration, observability research.

---

## RAG-or-Not-RAG: The Codebase-Context Discussion (2026-04-16)

A multi-turn exploration triggered by the question *"everyone is ingesting codebase into an LLM — what's the actual best way?"* The conversation started with skepticism of the two obvious answers (RAG MCP over code, static documentation), ran two deep-dive research waves, corrected a wrong mental model midway, and landed on a concrete architectural recommendation for a realistic enterprise use case. Captured here as a single demo narrative because the arc — naive question → nuanced taxonomy → self-correction against primary sources → conditional answer → deployable blueprint — mirrors exactly the kind of reasoning a consulting engagement on this topic should produce.

### Arc of the conversation

1. **Opening question:** How are teams efficiently feeding codebase context to LLMs in early 2026? Obvious answers (RAG, static docs) felt insufficient.
2. **First deep-dive (2026-04-15):** DAG of 6 sub-questions, parallel subagents. Produced taxonomy of 14 approaches, landed on *"agentic exploration + structural substrate (LSP/tree-sitter/graph) + agent-writable memory"* as the 2026 synthesis.
3. **Serena/Cody/Augment walkthrough:** discussed what each is, when each fits, pricing, and the Navigation Paradox (CodeCompass finding that agents skip graph tools 58% of the time despite explicit prompting).
4. **Error and correction:** offered a clean "Pattern A (unified index) vs Pattern B (federated MCP retrieval)" framing. First brain caught it by pointing at this repo's own research. Dropbox Dash explicitly rejected federated per-source tools after finding they caused context rot — they consolidated into a unified index with a knowledge-graph overlay. The Pattern A/B framing was oversimplified; production converges on Pattern A.
5. **Second deep-dive (2026-04-16):** DAG of 6 sub-questions on code-in-RAG specifically. Key new finding: **GrepRAG (arXiv 2601.23254, Feb 2026)** — naive LLM-driven grep matches sophisticated graph-based retrievers on repo-level code completion, and with light post-processing beats SOTA by 7–15.6% exact match. Default answer: don't put code in RAG; use agentic grep + LSP. Code-RAG earns its keep in four specific conditions.
6. **Use-case landing:** first brain specified the realistic enterprise shape — developers/analysts asking *"how does our code handle scenario X"* and *"will this change break the production pipeline"*, multi-repo, cannot afford on-demand scanning. This use case hits two of the four escape-hatch conditions simultaneously.
7. **Final recommendation:** minimal-SCIP + semantic-RAG hybrid exposed as two MCP tools on existing Postgres/pgvector infrastructure. See highlighted blueprint below.

### Corroborations from this repo's prior research

The repo's existing research (`docs/2026-04-11-engineering-rag-evidence-and-howtos.md`, `docs/deep-dive/2026-04-14-html-rag-ingestion-state-of-art.md`) already establishes:

- **"Codebase + wiki + on-call docs together" is ubiquitously assumed but never benchmarked.** HERB benchmark shows heterogeneous-source retrieval is the *unsolved* bottleneck (best agentic RAG 32.96/100).
- **Uber's +27% EAg-RAG numbers are agentic-vs-traditional RAG, NOT multi-source-vs-single-source.** Explicit misattribution warning.
- **Dropbox Dash consolidated into a unified search index** because federating tools caused context rot. Direct quote: *"More tools often meant slower, less accurate decision making... limiting tool definitions by consolidating retrieval through a universal search index, filtering context using a knowledge graph."*
- **Top production RAG teams ingest docs/tickets/Slack, not monorepo code.** Code intelligence lives in a separate system (internal Sourcegraph equivalents, LSP-based tools, grep-over-monorepo) — never confirmed to be in the primary RAG.

What this repo did not have, and the 2026-04-16 deep-dive added:

- GrepRAG (arXiv 2601.23254) — direct ablation that grep matches graph-based retrievers.
- cAST (arXiv 2506.15655) — tree-sitter AST chunking measured at +4.3 Recall@5 / +2.67 Pass@1 vs naive.
- SPLADE-Code (arXiv 2603.22008) — learned sparse retrieval for code.
- The explicit verdict that production teams don't put source code in their primary RAG (the corroborating evidence was present; the verdict wasn't made explicit).

Full write-up with sources: `docs/deep-dive/2026-04-16-code-ingestion-into-rag.md`.

### Ex. SS: Minimal-SCIP + semantic-RAG blueprint for FedRAMP multi-repo code intelligence (the highlighted final answer)

**Use case:** developers/analysts asking *"how does our code handle scenario X?"* or *"if I do this, will I break the production pipeline?"* across an estate of multiple repos. Must be efficient (no LLM scanning all repos on every query). FedRAMP-High constraint with only Claude Sonnet 4.5 available via Bedrock. No Cursor / Cody Cloud / Augment / GitHub Copilot non-gov.

**Why this is the case where code-RAG earns its keep:** the use case hits two of the four escape-hatch conditions from the deep-dive:
1. Semantic/intent queries with low lexical overlap ("scenario X" rarely matches identifiers).
2. Cross-language/cross-repo impact analysis (LSP and tree-sitter don't span repo boundaries reliably).

Pure-agentic Claude Code fails on efficiency (multi-repo scan per query) and on intent queries. Pure-RAG fails on impact analysis. The answer is **two pre-built indexes, two MCP tools, one agent**.

**Architecture:**

```
                ┌─ Semantic Code RAG (pgvector) ─────────┐
                │  tree-sitter AST chunks at symbol      │
                │  Contextual Retrieval prefix per chunk │
                │  hybrid: mxbai-embed-large + BM25      │
                │  cross-encoder rerank                  │
                │  metadata: repo, path, symbol, is_test │
                │                                        │
Query ──► Agent ┤   MCP tool: search_code(intent_query)  │
(Sonnet 4.5 on  │                                        │
 Bedrock, via   ├─ Code Graph (Postgres, SCIP) ──────────┤
 Claude Code)   │  .scip per repo → Postgres tables      │
                │  cross-repo references resolved        │
                │                                        │
                │   MCP tool: find_callers(symbol)       │
                │   MCP tool: trace_impact(file)         │
                └────────────────────────────────────────┘
```

**Agent routing by question type:**
- *"How does X work" / "where is scenario Y handled"* → `search_code` (semantic RAG). Intent query, Contextual Retrieval, hybrid, reranked.
- *"If I change X, what breaks"* → `trace_impact` / `find_callers` (graph). Deterministic, exact, fast.
- Compound questions → agent calls both and composes.

**Why SCIP (and not tree-sitter-only) for the graph:**
- "Will I break the pipeline" requires precise cross-repo reference resolution (e.g., `payments.api.process` in repo A called by `pipeline.ingest` in repo B through an npm/pip/go module import).
- Tree-sitter is per-repo; it cannot resolve imports across repo boundaries.
- SCIP is compiler-accurate and the indexers (`scip-typescript`, `scip-python`, `scip-java`, etc.) are open-source, standalone CLIs — no Sourcegraph required.

**Why not self-hosted Sourcegraph OSS:** viable option, but building the two narrow MCP surfaces you actually need is less operational overhead than running Sourcegraph's full stack. SCIP is an open protobuf format; Sourcegraph publishes `scip` parsing libraries in Go/Rust. The DIY pipeline is ~2–3 weeks of engineering.

**Minimal SCIP pipeline:**

1. Per-repo CI step on merge-to-main: `scip-<lang> --output index.scip`.
2. Upload `.scip` to shared artifact store (S3 / internal bucket / direct Postgres write).
3. Ingestion service parses `.scip` protobuf using the Sourcegraph `scip` library (Go or Rust).
4. Writes symbols, occurrences (definition/reference), and cross-repo relationships into Postgres tables.
5. MCP server wraps SQL queries: `find_definition(symbol)`, `find_callers(symbol)`, `trace_impact(file)`, `list_symbols(path)`.

**Why this reuses this repo's existing infrastructure:**
- pgvector + Postgres + mxbai-embed-large stack already operating for VA docs. Adding a `code_chunks` table and a parallel `scip_symbols` / `scip_occurrences` table schema reuses the same ops surface.
- Claude Sonnet 4.5 on Bedrock (FedRAMP-High authorized) is already the generation model in scope.
- No new cloud dependencies. No third-party code intelligence vendor.
- MCP server pattern already adopted for the docs RAG — two more MCP tools fit cleanly alongside the existing `search_docs` tool.

**Why this matters for Sonnet 4.5 specifically:**
- Sonnet 4.5 trails Opus 4.6 by 5–10pp on agentic coding benchmarks. Graph/symbol substrates matter *more* with weaker models — they do work the model otherwise has to do unreliably.
- The Navigation Paradox (58% tool-skip rate) is more severe on weaker models. Pre-built indexes with clean MCP interfaces reduce the number of decisions the model has to make right.

**Recommended build order:**
1. **Semantic Code RAG side first.** Same pgvector infrastructure, same mxbai embedder, same Contextual Retrieval pattern proven on VA docs. Add tree-sitter chunking + `code_chunks` table + BM25 hybrid + rerank. One MCP tool (`search_code`). Answers 60–70% of "how does X work" queries alone.
2. **Measure on realistic queries.** See what fails — likely the "what depends on this" impact questions.
3. **Add the SCIP graph when value of #1 is proven.** Build only if impact analysis queries are demonstrably failing against pure RAG.
4. **Three MCP tools total** across docs-RAG + code-RAG + code-graph. Well under the Dropbox context-rot threshold.

**What this replaces:**
- The need to self-host full Sourcegraph OSS.
- The need for Cursor / Cody Cloud / Augment / Copilot (none FedRAMP-High authorized).
- The need to give up and tell users to grep manually across N repos.

**Demo talking point:** "The usual answer to 'how do we give LLMs codebase context' is either *dump it into RAG* or *use Cursor/Cody*. For FedRAMP-constrained environments with Sonnet 4.5 available, neither is viable. The research-backed answer is a thin purpose-built intelligence layer — two pre-built indexes exposed as MCP tools, reusing the same Postgres/pgvector infrastructure that powers the docs RAG. SCIP indexers are open-source standalone CLIs; the pipeline is 2–3 weeks of engineering, not a vendor contract."

Source: 2026-04-16 session — two deep-dive research waves (saved to `docs/deep-dive/2026-04-15-codebase-context-for-llms.md` and `docs/deep-dive/2026-04-16-code-ingestion-into-rag.md`), cross-checked against this repo's existing engineering-rag-evidence and HTML-ingestion research, synthesized into the blueprint above.

---

## Act 29: The Router That Isn't (2026-04-16, continued)

A follow-up discussion during ship-cut v1 planning. Triggered by the natural question *"if different retrieval pipelines handle different query types, don't you need a router?"* — and answered by flipping the frame: **the consuming LLM is the router; no classifier layer exists as a distinct component.** This is the 2026 architectural story for heterogeneous RAG that most public demos still get wrong.

### Moment 30: "The router is the LLM reading your tool docstrings."

**The anti-pattern** (what most 2023-era RAG tutorials still show): a query-classification step in front of retrieval. Classify query → dispatch to `search_docs` OR `search_code` OR `search_jira`. A separate model + separate prompt + separate latency + separate failure mode. Dropbox Dash rejected this explicitly after discovering federated per-source tools caused context rot — the planner LLM wasted tokens deciding which retriever to use and got it wrong.

**The pattern that works:**

```
[Consuming LLM: Claude / Cursor / agent]
         ↓ reads tool docstrings; picks per question
[Small number of qualitatively-different @mcp.tool decorators]
  - search_docs(query, k)        # for NL/conceptual questions
  - search_code(query, k)        # for intent queries over code
  - find_callers(symbol)         # for structural graph queries
  - trace_impact(file)           # for transitive dependency queries
         ↓ each tool does hybrid retrieval internally
[Grep + dense + graph, fused, reranked — one pipeline, three retrievers in parallel]
```

**Three layers, three different kinds of routing:**
1. **LLM-level** (between tools) — happens inside Claude, driven by your docstrings. You "build" it by writing good docstrings.
2. **MCP server-level** (tool → implementation) — function dispatch, handled by the `@mcp.tool` decorator.
3. **Hybrid retrieval within one tool** (between methods) — **always run all retrievers in parallel + fuse**. Never sub-route.

**No component labeled "router" anywhere.**

**The Dropbox distinction worth calling out in the demo:**
- ❌ **Same capability × different sources = bad.** `search_slack`, `search_jira`, `search_confluence`. Planner degrades.
- ✅ **Different capabilities = good.** `search_docs`, `search_code`, `find_callers`. Planner handles easily.
- **What differentiates tools is what matters.** Same capability split across sources = federation anti-pattern. Qualitatively different capabilities = clean separation.

### Moment 31: Three retrievers, three different questions. Same query, three different answers.

**RAG ≠ vectors.** Retrieval-Augmented Generation is a *pattern*; the retrieval method behind it can be vector, lexical, graph, or all three fused. A key demo clarification because most audiences conflate "RAG" with "vector search."

**The three retrieval methods in a code-RAG tool:**

| Method | What it stores | Query style | Best for |
|---|---|---|---|
| **Grep / BM25 (lexical)** | Inverted index: token → files containing it | Exact word match, regex, operator-aware | "Show me all files mentioning `StripeWebhook`" |
| **Vector (dense)** | Chunk embeddings in pgvector | Semantic similarity | "Where does the code handle failed webhook retries" (the word "retry" may not appear) |
| **Graph (structural)** | Nodes (symbols) + edges (`calls`, `imports`, `inherits`) from SCIP | Deterministic traversal, exact connections | "What calls `process_payment`?" |

**The demo-worthy example — same query, three answers:**

Query: *"What calls `process_payment`?"*

- **Grep** returns: every file mentioning the literal string `process_payment` — including comments, TODOs, string literals, unrelated variables. **Noisy but fast.**
- **Vector** returns: functions semantically similar to `process_payment` — could return `charge_credit_card`, `handle_checkout`, etc. **Misses the exact callers.**
- **Graph** returns: the exact 7 functions in 4 files that have a `calls` edge to this specific `process_payment`. **Zero false positives, zero false negatives.**

**Only graph answers correctly.** This is why Sourcegraph keeps the graph layer, why SCIP exists, and why the FedRAMP blueprint (Ex. SS) calls for SCIP + semantic-RAG together. Vector alone is insufficient for structural questions. Grep alone is noisy for anything beyond literal matches. Graph alone can't answer intent queries. **Hybrid is the production answer.**

### Moment 32: Mapping the router insight to v1 demo code

**What the v1 MCP server already demonstrates architecturally, even with only one tool:**

- The `query` tool's docstring includes the affordance — "Use for question-answering over the VA Education corpus; results come pre-reranked."
- The `document://{source_id}` resource handles a different kind of retrieval — full-document fetch instead of chunk search.
- The `cite_from_chunks` prompt template hands the consumer a citation-heavy answer format.

Three MCP capabilities → three affordances → LLM picks. **The v1 demo already shows the pattern at small scale.** When the blueprint adds code-RAG later, it's more `@mcp.tool` decorators on the same FastMCP server — no router component to add.

### Talking point — "No router. That's the feature."

"Most 2023-era RAG tutorials still show you a query classification step in front of retrieval. Don't build that. In 2026, the consuming LLM IS the router, and it routes by reading your MCP tool docstrings. You build routing by writing good tool signatures. No classifier model, no dispatch layer, no extra latency, no extra failure mode. Small number of qualitatively-different tools plus hybrid retrieval inside each gets you there."

### Talking point — "Grep, vector, graph — three retrievers, same query, three different answers."

"RAG doesn't mean vectors. RAG is the pattern; the retrieval method is an orthogonal choice. A production code-retrieval tool runs grep, dense, and graph in parallel, fuses, and reranks. Each retriever answers a different kind of question — grep for literal matches, dense for intent, graph for structural connections. Only one of them correctly answers 'what calls process_payment' — and it's not the vector one. Hybrid retrieval is the 2026 production answer for any source type where no single retriever covers all query shapes."

### Talking point — "Same capability, different sources = bad. Different capabilities = good."

"Dropbox Dash rejected federated per-source tools — separate `search_slack`, `search_jira`, `search_confluence` caused context rot because the planner LLM wasted tokens choosing between qualitatively-identical tools. The right split is by *capability*, not *source*. One `search_docs` that spans Slack+Jira+Confluence internally, plus a `search_code` for qualitatively different retrieval, plus `find_callers` for graph operations. Three tools, three capabilities, LLM picks. That's the lesson most public demos still miss."

### Quotables

- "The router is the LLM reading your tool docstrings."
- "In 2026, you build routing by writing good docstrings, not by adding a classifier."
- "Same capability × different sources = federation anti-pattern. Different capabilities = clean separation."
- "RAG doesn't mean vectors. Retrieval is an orthogonal choice from the RAG pattern."
- "Grep, vector, graph — same query, three different answers. Only one is right, and which one depends on the question."
- "Hybrid retrieval is the 2026 production answer. Sub-routing inside a tool re-creates the Dropbox mistake at a smaller scale."
- "The v1 MCP server already shows the pattern at small scale. Tools + Resources + Prompts is three capabilities, not three sources."

### Stats block (from 2026-04-16 adjudication deep-dive)

- **Glean:** maintains separate lexical + semantic indexes for code; general Glean Search matches code only on PR descriptions and file names (not contents)
- **Sourcegraph:** removed embeddings from Cody Enterprise — multi-repo scale forced retreat to graph + trigram
- **GitHub Blackbird:** custom Rust trigram index, architecturally separate from Copilot retrieval inside one company
- **HERB benchmark:** best agentic heterogeneous retrieval **32.96/100 average**; heterogeneous retrieval is unsolved
- **CodeRAG-Bench (NAACL 2025):** modern code-specific dense embedders **beat BM25 on code** — reverses classic BEIR result. Code-specific matters; generic dense loses to BM25.
- **CodeCompass:** graph wins architectural queries by **+20 ACS** over BM25; BM25 wins semantic queries by 10 ACS over vanilla. Task-type-dependent.
- **Dropbox Dash (Ramon Martinez talk):** "more tools often meant slower, less accurate decision making" — consolidated federated tools into unified search + knowledge graph overlay

Source: 2026-04-16 session, deep-dive adjudication research (`docs/deep-dive/2026-04-16-docs-vs-code-rag-adjudication.md`) — subagent-parallel DAG exploration over 6 sub-questions + stress-test of GrepRAG/cAST findings.

### Ex. TT: The three-retriever trifecta — same query, three answers

**Query:** *"What calls `process_payment` in this codebase?"*

**Grep result (lexical, BM25 / tsvector):**
```
payments/tests/test_api.py:47:     result = process_payment(mock_req)   # unit test
payments/README.md:12:             The `process_payment` function handles...  # doc comment
payments/api.py:42:                def process_payment(req):               # the definition
checkout/flow.py:89:              return process_payment(validated)      # real caller
webhooks/stripe.py:156:           process_payment(webhook.payload)       # real caller
legacy/migration.py:8:             # TODO: migrate process_payment calls  # stale comment
```
Six hits. Two are real callers; four are noise (test, docs, definition, TODO). Fast (<10ms). Would need LLM post-filtering to find actual callers.

**Vector result (dense, mxbai or voyage-code-3):**
```
[rerank=8.1] payments/api.py:42:    def process_payment(req):            # self-match
[rerank=7.3] payments/api.py:85:    def charge_credit_card(req):         # semantic sibling
[rerank=6.9] invoices/api.py:24:    def handle_invoice_payment(inv):     # semantic sibling
[rerank=6.2] refunds/core.py:31:    def issue_refund(txn):               # distantly related
```
Four hits. **Zero of them actually call process_payment.** Dense retrieval found semantically-similar code, not structural relationships. Useful for "what other functions are in this domain," useless for "who calls this."

**Graph result (SCIP, deterministic traversal):**
```sql
SELECT caller_file, caller_function, call_line
FROM scip_references
WHERE target_symbol = 'payments/api.py:process_payment';
```
```
checkout/flow.py::checkout_handler         line 89
webhooks/stripe.py::handle_stripe_webhook  line 156
```
Exact answer. Two real callers, zero false positives. ~1ms query (indexed SQL).

**The demo takeaway:** no single retriever handles all query types. Grep is noisy on structural questions. Dense is wrong on structural questions. Graph is unavailable for semantic questions. **Hybrid running all three in parallel, fused + reranked, is the production answer.** This is why Sourcegraph's architecture is "grep + graph + embeddings, in that order of trust," not "pick one."

Source: synthesized from 2026-04-16 adjudication; mirrors LinkedIn KG-RAG, Sourcegraph Cody, and Augment Context Engine architectures documented in the research.

---

## Act 30: Labeling the seams (shipping the observability + quality proof points) (2026-04-16, session 9)

Three ship-cut polish beats from one session, unified by the thesis: **label the seams with real artifacts — don't half-build features the demo doesn't need.**

### Moment 33: The Langfuse "public dashboard share link" doesn't exist

The ship-cut v1 checklist said *"Langfuse Cloud traces on dev queries — shareable read-only dashboard link in README."* The natural read: flip a project-level toggle, paste the dashboard URL. Reality: **Langfuse Cloud has per-trace public sharing but not dashboard-level public sharing.** Trace-level sharing is documented in a 2023 changelog; custom dashboards only mention "team collaboration." The feature described in the checklist was aspirational — no matching toggle exists.

**Re-scoping the goal, not the feature:** what a reader actually needs from the README is *a clickable link that proves observability is wired up.* That's served equally well by one canonical public trace. Goal dissolves.

### Moment 34: The documented OTel attribute didn't promote

Langfuse's OTel integration docs list `langfuse.trace.public` (boolean) as the attribute that marks a trace public. Added it to the tool-call span alongside the existing `input.value` / `output.value`:

```python
_parent_span = _otel_trace.get_current_span()
_parent_span.set_attribute("input.value", q)
_parent_span.set_attribute("langfuse.trace.public", True)   # docs said this would work
```

After running the smoke test, **the trace came back `public: false`.** ([Ex. UU](#ex-uu-langfuse-otel-attribute-table))

**The debugging loop:**
1. Queried the authenticated Langfuse API — confirmed the trace exists, `public: False`, also missing `input` at trace level.
2. Queried observations for the trace — found `langfuse.trace.public: true` landed, but on a **child** span (our tool function's span), not the root.
3. The root span is the one FastMCP creates when wrapping the tool call — our `_otel_trace.get_current_span()` inside `query()` returns the *child* of FastMCP's wrapper, not the true OTel root.
4. Langfuse only promotes `langfuse.trace.*` attributes from the root span. Child-span attributes become observation metadata, never trace fields.

([Ex. VV](#ex-vv-debugging-the-span-hierarchy))

### Moment 35: Sidecar ingestion API — the reliable path

Rather than fight OTel's span hierarchy or reach into FastMCP internals, **use the Langfuse ingestion API directly.** POST a `trace-create` event with the same trace ID and `public: true` as a sidecar call. Works regardless of which span has which attributes.

Result: `scripts/make_trace_public.py <otel_trace_id>` — 40 lines, no dependencies beyond stdlib + dotenv. Confirmed anonymous-viewer access via trpc query with no auth: `"public":true`. ([Ex. WW](#ex-ww-sidecar-helper-and-anonymous-access-check))

**Reverted the OTel attribute code change** — dead weight that didn't achieve the goal. Kept one small addition: logging the 32-char OTel trace ID alongside our internal `ikb-<epoch>` trace_id so any server log line pairs to a Langfuse URL.

### Moment 36: CI gate — pick what the demo needs, label what production needs

The handoff's eval-in-CI plan called for DeepEval-scored gate on CtxRec + Faith. Walked through three options:

| Option | What | Time/PR | Cost/PR |
|---|---|---|---|
| **A** — fast proxies on every PR | top1/topk match, keyword recall, IDK rate | ~20 min | $0.30 |
| **B** — full 110q + DeepEval on every PR | Faith/AnsRel/CtxPrec/CtxRec/CtxRel | ~80 min | ~$2 |
| **C** — two-tier: fast on every PR, full nightly | Blocking gate + full coverage | 20 min PR / nightly full | $0.30 PR + nightly |

**Decision: ship Option A. Mention Option C as the production evolution in the demo itself.** Reasons:
- Proxies are tight — baseline re-confirmation showed zero drift, and proxies move together with DeepEval metrics in practice (top1_source_match ≈ context recall signal).
- The demo's job is *"CI blocks regressions"* — proven by the failing-then-passing PR artifact, not by breadth of gated metrics.
- 20 min / $0.30 is a reasonable gate for every PR; 80 min / $2 discourages frequent PRs.
- Option C is the honest production story: ship A, label C for scaling up. Same "label the seams" pattern as the `auth_context` gateway seam and the tsvector-but-no-BM25-wiring schema.

### Moment 37: Zero drift after the tsvector schema change (good ops hygiene)

An open question from the handoff: *the tsvector GENERATED column was added after the last full eval; could the schema change have perturbed retrieval?* Ran `run_eval.py --fast` against the v2bcr+rerank baseline to confirm.

Result: **zero drift across every proxy.** ([Ex. XX](#ex-xx-baseline-reconfirm-zero-drift))

| Metric | Now | Baseline | Δ |
|---|---|---|---|
| top1_source_match | 0.733 | 0.733 | 0.000 |
| topk_source_match | 0.867 | 0.867 | 0.000 |
| answer_keyword_recall | 0.768 | 0.768 | 0.000 |
| idk_rate | 0.167 | 0.167 | 0.000 |
| avg_input_tokens | 2489 | 2489 | 0.000 |
| avg_output_tokens | 178 | 180 | -2 (Sonnet nondeterminism) |

Confirms the GENERATED column is truly inert until BM25 is wired against it. **This is also the baseline file the Option A gate compares against** — built into the v2bcr+rerank eval artifact, reusable.

### Talking point — "The supported feature, not the feature name"

"The original plan said 'public dashboard share link.' Langfuse doesn't have that. But the reader only needs a clickable artifact that proves observability is wired up — a public trace link serves that identically. Matching to the supported feature (per-trace public via ingestion API) beats half-building a custom dashboard viewer. Rule: when docs don't match the plan, rescope the goal to the closest supported primitive."

### Talking point — "Documented attribute, wrong span"

"The Langfuse docs list `langfuse.trace.public` as the canonical OTel attribute for marking a trace public. It works — just not from inside a FastMCP tool function, because FastMCP wraps your tool call in an outer span that is the true OTel root. Your code's span is a child, and Langfuse only promotes trace-level attributes from the root. The sidecar ingestion API call sidesteps the whole issue in 40 lines of stdlib."

### Talking point — "Ship the gate the demo needs, label the gate production needs"

"For the public demo, the merge gate is Option A — fast proxies, 20 minutes, thirty cents per PR. Proxies move together with the scored metrics in practice, and the demo artifact (the failing-then-passing PR in Actions history) doesn't require DeepEval scoring to be convincing. Option C — fast on every PR, full DeepEval nightly — is the production evolution. Same pattern as the `auth_context` stub and the tsvector-without-BM25-wiring schema: label the seams, don't half-build."

### Talking point — "Schema change verified, not assumed"

"Added a tsvector GENERATED column for hybrid-readiness. Then re-ran the fast eval to confirm it didn't perturb retrieval — zero drift across every proxy, down to token counts. Schema changes that *shouldn't* affect retrieval need to be *verified* not to affect retrieval. That's the habit CI is meant to enforce every PR."

### Quotables

- "The supported feature, not the feature name."
- "The documented attribute promotes from root. FastMCP makes your span a child of its wrapper. Those two facts don't meet."
- "Sidecar ingestion API, forty lines of stdlib — works regardless of which span has which attributes."
- "For v1, ship Option A. For production, label Option C. Same pattern as the auth_context seam."
- "Schema changes that shouldn't affect retrieval need to be verified not to affect retrieval."
- "Proxies move together with scored metrics in practice. The demo artifact is the blocked PR, not the breadth of gated metrics."

### Stats block

- Langfuse public trace URL: `https://us.cloud.langfuse.com/project/cmo0wah7a00pfad071nk6x84c/traces/a574193bbff7d5438f7fae9e27f4bb83`
- Anonymous trpc verification: `"public":true` returned without auth headers (confirmed after ingestion API sidecar call landed)
- Fast eval baseline reconfirm: 30 queries, 21 min, $0.30. Zero drift across all proxies.
- CI gate Option A cost projection: $0.30/PR × 20 PRs/mo ≈ $6/mo
- Same-repo-as-is decision: no sanitized fork; flip GitHub visibility to public when eval-in-CI is green on main

Source: 2026-04-16 session 9, post-PR-#3 ship-cut polish. Debugging journey logged in memory at `~/.claude/projects/-Users-jaekim-internal-knowledge-base/memory/rag-pipeline-status.md` ("Langfuse OTel gotcha" section).

### Ex. UU: Langfuse OTel attribute table (what docs promised)

From the Langfuse OpenTelemetry integration docs:

| Langfuse Field | OTel Attribute |
|---|---|
| name | `langfuse.trace.name` |
| userId | `langfuse.user.id` |
| sessionId | `langfuse.session.id` |
| **public** | **`langfuse.trace.public` (boolean)** |
| tags | `langfuse.trace.tags` (string[]) |
| input | `langfuse.trace.input` |
| output | `langfuse.trace.output` |

Unstated in the table: **these promote to trace-level only when set on the root span of the OTel trace.** When a framework like FastMCP wraps your tool call in an outer span, your tool's span becomes a child — attributes set inside the tool function land on the child, not the root, and don't promote.

Source: `https://langfuse.com/integrations/native/opentelemetry`

### Ex. VV: Debugging the span hierarchy

**Step 1 — authenticated query showed `public: false` at trace level:**

```
=== trace-level ===
public: False
name: tools/call query
input.present: False
output.present: False
=== root-span attributes (first 4) ===
rpc.system: mcp
rpc.method: tools/call
mcp.method.name: tools/call
fastmcp.component.key: query
```

Zero `langfuse.*` attributes on root. FastMCP's wrapper span owns the root; only its own `rpc.*` / `mcp.*` / `fastmcp.*` attributes appear.

**Step 2 — observations query showed the attribute on a child span:**

```
name=rerank            id=796fcb30  parent=47db0e43
name=retrieve          id=85d0a690  parent=47db0e43
name=tools/call query  id=47db0e43  parent=25f280c2    ← our tool function's span (CHILD)
  ikb.k: 3
  ikb.rerank_from: 20
  langfuse.trace.public: true        ← landed here, not promoted
  ikb.latency_ms: 26663
name=tools/call query  id=25f280c2  parent=            ← FastMCP's wrapper (ROOT, no attributes)
```

Same `name=tools/call query` shows up twice. The outer one (25f280c2, no parent) is the true OTel root — FastMCP's instrumentation wrapper. The inner one (47db0e43) is our tool function's execution span. Everything we `set_attribute` inside `query()` lands on the inner span.

**Step 3 — anonymous trpc query confirmed the practical consequence:**

```
$ curl "...api/trpc/traces.byIdWithObservationsAndScores?...traceId=a574193b..."
[{"error":{"json":{"message":"User is not a member of this project and this trace is not public",
 "code":-32001,"data":{"code":"UNAUTHORIZED","httpStatus":401}}}}]
```

Trace exists (error says "not public," not "not found") but anonymous viewer is blocked. **The attribute didn't promote; the trace isn't public; the ship-cut goal isn't met.**

Source: `scripts/mcp_server.py` query function, inspected via Langfuse public API `/api/public/traces/{id}` and `/api/public/observations?traceId=...` (authenticated) and anonymous trpc to confirm end-user view.

### Ex. WW: Sidecar helper and anonymous access check

**`scripts/make_trace_public.py` — 40 lines of stdlib (+ dotenv):**

```python
def make_public(trace_id: str) -> None:
    pk = os.environ["LANGFUSE_PUBLIC_KEY"]
    sk = os.environ["LANGFUSE_SECRET_KEY"]
    host = os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com").rstrip("/")

    auth = base64.b64encode(f"{pk}:{sk}".encode()).decode()
    payload = {
        "batch": [{
            "id": str(uuid.uuid4()),
            "type": "trace-create",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "body": {"id": trace_id, "public": True},
        }]
    }
    req = urllib.request.Request(
        f"{host}/api/public/ingestion",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        print(f"HTTP {resp.status} — {resp.read().decode()[:300]}")
```

**Run:**
```
$ .venv/bin/python -m scripts.make_trace_public a574193bbff7d5438f7fae9e27f4bb83
HTTP 207 — {"successes":[{"id":"f5660d8e-5b4f-4e02-a24a-e845d56ee3ff","status":201}],"errors":[]}
public URL: https://us.cloud.langfuse.com/project/cmo0wah7a00pfad071nk6x84c/traces/a574193bbff7d5438f7fae9e27f4bb83
```

**Verification (anonymous, no headers):**
```
$ curl ".../api/trpc/traces.byIdWithObservationsAndScores?..."
...("public":true)...
```

One flag flipped via ingestion API; anonymous trpc now returns the trace without auth. The 207 Multi-Status response with `"successes":[...],"errors":[]` is Langfuse's standard ingestion batch response — idempotent, can re-run safely.

Source: `scripts/make_trace_public.py`; Langfuse ingestion API docs at `https://api.reference.langfuse.com/`.

### Ex. XX: Baseline reconfirm — zero drift after tsvector column

```
============================================================
  FAST PROXIES  (n=30)
============================================================
  top1_source_match_rate           0.733     vs base 0.733     Δ +0.000
  topk_source_match_rate           0.867     vs base 0.867     Δ +0.000
  answer_keyword_recall_mean       0.768     vs base 0.768     Δ +0.000
  idk_rate                         0.167     vs base 0.167     Δ +0.000
  avg_input_tokens                 2489      vs base 2489      Δ +0.000
  avg_output_tokens                178       vs base 180       Δ -2.000 ▼ ✓

  baseline: eval_v2bcr_rerank.raw.json  matched n=30
```

Six proxies, five identical to the character, one down by 2 output tokens (Sonnet nondeterminism). The `content_tsv GENERATED ALWAYS AS (...) STORED` column + GIN index were added to 6,489 rows in the same Docker container — and the retrieval pipeline didn't notice. Which is exactly the guarantee GENERATED columns are supposed to offer, **now verified empirically.**

Cost: $0.30 (Sonnet 4.6 generation, 30 queries). Elapsed: 21 min. Same cost/speed profile projected for the Option A CI gate.

Source: `data/eval_v2bcr_rerank_postship.fast.raw.json` vs. `data/eval_v2bcr_rerank.raw.json` (baseline from 2026-04-15). Run via `scripts/run_eval.py --fast --k 5 --rerank-from 20 --baseline eval_v2bcr_rerank.raw.json`.


