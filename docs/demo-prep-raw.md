# Demo Prep — Raw Material from Sessions

Extracted moments, narratives, and artifacts from the session that demonstrate RAG pipeline construction capabilities. For both video walkthrough and written case study.

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

### 21. "Three-Tier Eval Cadence" — Making Loop A Actually Feasible
**What happened:** A full eval iteration costs 2 hours and ~$5. After the first few full validation runs, the math killed iteration speed. Built three tiers:

| Tier | Time | Cost | Catches |
|---|---|---|---|
| Fast | 5-10 min | $0.30 | Retrieval recall, ranking, source matches, token cost (no LLM judge) |
| Medium | 30 min | $1.50 | Same + full DeepEval semantic scoring |
| Full | 2h | $4.30 | Same on full 110-query set |

**Talking point:** "Most RAG iterations are retrieval/chunking changes that don't need full DeepEval scoring. A 5-minute fast mode with cheap proxies — keyword recall, IDK rate, token cost — catches the same direction-of-change. Reserve the 2-hour full validation for milestone declarations. 6x faster, 5x cheaper, same final confidence." ([Ex. GG](#ex-gg-fast-mode-output))

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
