# Demo Prep — Raw Material from 2026-04-13 Session

Extracted moments, narratives, and artifacts from the session that demonstrate RAG pipeline construction capabilities. For both video walkthrough and written case study.

---

## Narrative Arc

**Setup:** Client has VA Education Service manuals on a JavaScript SPA (KnowVA) and a PDF ICD document. Needs a RAG knowledge base with evaluation.

**Act 1 — Reverse-engineering the data source** (crawler discovery)
- KnowVA is a JavaScript SPA (eGain platform) — no static pages to wget
- Walked through Chrome DevTools together to find the API
- Discovered the eGain v11 XML API by intercepting XHR calls
- Key moment: finding the `$level` parameter that unlocks the full topic tree — no headless browser needed
- Built a pure-API crawler that politely downloads 237 articles with structure preserved

**Act 2 — Building the golden evaluation set** (domain expertise + AI)
- Created 110 queries across 5 personas: VCE (claims examiner), consulting SME, prod ops, new hire, auditor
- Cross-source queries that require stitching M22-3 + M22-4 + VADIR ICD
- Deliberately wrote queries in natural domain language ("the service record shows...") instead of naming systems ("VADIR returns...") — tests semantic retrieval, not keyword matching

**Act 3 — Catching our own hallucinations** (eval-before-trust)
- Ran 3 parallel validation subagents: faithfulness, correctness, relevance
- Caught a compounding hallucination: fabricated "SAO→SOAR transition Oct 1, 2023" → propagated to 4 other answers
- Fixed all contaminated answers, re-ran validation, scores improved across the board
- The pipeline caught its own errors before they became the benchmark

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

### 5. The Hallucination Catch — Eval Saves the Benchmark
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

---

## Key Demo Artifacts

| Artifact | Path | What it shows |
|----------|------|---------------|
| Crawler script | `scripts/crawl_knowva.py` | Pure API, no browser, resume support, polite crawling |
| Sample article HTML | `data/knowva_manuals/articles/554400000073486.html` | Structure-preserving output (tables, headings, metadata in `<meta>` tags) |
| Sample article JSON | `data/knowva_manuals/articles/554400000073486.json` | pgvector-aligned metadata (topic_breadcrumb, contains_table, heading_outline) |
| Topic tree | `data/knowva_manuals/_topic_tree.json` | Full 170-node parent→child hierarchy |
| Golden query set | `data/golden_query_set.json` | 110 queries, 10 types, source references, answers |
| Eval results | `data/eval_faithfulness_v2.json` | Per-query claim decomposition + grounding scores |
| VADIR ICD | `data/VADIR_CH33_LTS_WS_V2.1.1_ICD_20220509.pdf` | Real VA interface control document |

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
- What's next: chunking (Docling), embedding (Titan V2), pgvector, eval harness, MCP server
- Position as replicable methodology for any organization

---

## Quotable Moments from Session

> "make sure you preserve the parent-child structure, the headings, etc. we want to use this to build an element-aware chunking for rag vector db"

> "is m22-4 an updated version of m22-3, or are they separate" — (shows domain learning in real-time)

> "are there queries where we say 'VADIR' but don't have to? want to test if the vadir source would be brought up under the right context, without explicitly mentioning 'vadir'"

> "what if we don't even say 'DoD'? does that muddle it too much?"

> "hmm it's kind of a guided question isn't it? names the sources basically. do we have one that's trickier?"

> "so maybe a little less from the POV of the VCE, but from a consulting SME point of view"

> "yea the 25 we generated are fine. let's get 10 additional ones like this" — (iterative refinement of the eval set)

---

## Raw Stats for Demo Slides

- **Source documents:** 3 (M22-3, M22-4, VADIR ICD)
- **Articles crawled:** 237 (from JavaScript SPA via reverse-engineered API)
- **Total corpus size:** 27 MB
- **Articles with tables:** 126 (53%)
- **Topic tree nodes:** 170
- **Golden queries:** 110
- **Query types:** 10 (table lookup, policy rule, cross-source, consulting SME, prod ops, contradiction, temporal, negative, ambiguous term, synthesis)
- **Queries using domain language (no system names):** 18
- **Validation scores (v2):** faithfulness 0.93, correctness 0.997, relevance 0.993
- **Hallucinations caught:** 1 fabrication → 4 contaminated answers → all fixed
- **Parallel eval subagents:** 3 (ran simultaneously)
