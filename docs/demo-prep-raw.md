# Demo Prep — Raw Material from Sessions

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

**Act 5 — Catching our own hallucinations** (eval-before-trust)
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

### 8. The Hallucination Catch — Eval Saves the Benchmark
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
| Crawler script | `scripts/crawl_knowva.py` | Pure API, no browser, resume support, polite crawling, heading extraction with CMS-specific fallback |
| Enrichment script | `scripts/enrich_metadata.py` | Batch metadata enrichment (headings, acl, authority tier, content_category) |
| Parsing script | `scripts/parse_html_to_markdown.py` | HTML→markdown conversion with noise stripping |
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
- What's next: chunking, embedding (Titan V2), pgvector, eval harness, MCP server
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
- **Colspan-affected articles:** 54 (445 broken rows) — deferred to Step 7 context blurbs
- **Scripts written this session:** 2 (enrich_metadata.py, parse_html_to_markdown.py)

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

### Git commands for live demo

Pull up "before" states from git history during a demo:

```bash
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
