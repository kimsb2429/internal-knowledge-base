# Deep Dive: Open-Source Alternatives to Sourcegraph for Cross-Repo AST and Symbol Intelligence

**Date:** 2026-04-23
**Project:** internal-knowledge-base
**Core question:** What OSS tools resolve symbols across repository boundaries — call in repo A → definition in repo B — without paying for Sourcegraph Enterprise? Specifically, what closes the gap left by Serena (LSP-based MCP, single-workspace by construction)?

## Executive Summary

The blunt answer: **no OSS project currently delivers production-grade cross-repo symbol resolution**. The reference algorithm (GitHub's tree-sitter stack-graphs) was archived on 2025-09-09 and is read-only. Sourcegraph's self-hosted server went fully private (not merely BSL) in August 2024. Every multi-repo MCP entrant that has shipped in 2025-2026 either (a) indexes repos separately without true cross-repo resolution, (b) does heuristic qualified-name matching rather than compiler-grade scope resolution, or (c) wraps a paid Sourcegraph backend. The OSS building blocks that matter — SCIP indexers, Zoekt, universal-ctags, tree-sitter grammars — are all Apache-2.0 or similar and together are sufficient to DIY a weekend-MVP for 3-6 languages, but nobody has shipped the "Serena for cross-repo" MCP server that composes them. **That gap is a real, unclaimed opportunity.**

If you need cross-repo code intelligence today, in priority order: (1) run Sourcegraph self-hosted free-tier (≤10 users, proprietary EULA but workable for internal consulting); (2) pay for Sourcegraph Enterprise if scale demands it; (3) build a weekend-MVP over SCIP + DuckDB + MCP if you need OSS-purity. Serena + per-repo "toggling" is the honest fallback — it doesn't solve cross-repo, but it's the highest-quality single-repo answer.

## Findings

### 1. Sourcegraph's License Reality Is Worse Than "BSL"

The common "Sourcegraph went BSL" shorthand understates what happened.

- **June 2023** — core `sourcegraph/sourcegraph` relicensed from Apache-2.0 to a proprietary Sourcegraph Enterprise license. Code remained publicly viewable but was not OSI-approved. ([HN discussion](https://news.ycombinator.com/item?id=36584656))
- **August 22, 2024** — the core repo was made **fully private**. The frozen pre-privatization snapshot lives at [`sourcegraph/sourcegraph-public-snapshot`](https://github.com/sourcegraph/sourcegraph-public-snapshot); everything post-Aug-2024 is not publicly viewable, let alone forkable. ([DevClass, 2024-08-21](https://devclass.com/2024/08/21/sourcegraph-makes-core-repository-private-co-founder-complains-open-source-means-extra-work-and-risk/))
- **No widely-adopted community fork.** Eric Fritz's `efritz/sourcegraph` fork is a reference point, not a live project. ([Sourcegraph went dark](https://www.eric-fritz.com/articles/sourcegraph-went-dark/))

**What remains genuinely open-source (Apache-2.0) and usable in commercial/consulting contexts:**

| Component | License | Use |
|---|---|---|
| **[Cody clients](https://github.com/sourcegraph/cody)** (VS Code, JetBrains, CLI) | Apache-2.0 | IDE AI assistant; backend requires you to roll your own context |
| **[SCIP protocol](https://github.com/sourcegraph/scip)** | Apache-2.0 | Code-intel format (symbols, definitions, references) |
| **scip-* indexers** (see §3) | Apache-2.0 | Per-language SCIP generators |
| **[Zoekt](https://github.com/sourcegraph/zoekt)** | Apache-2.0 | Trigram-based code search engine (committed to stay OSS) |
| **[`scip` CLI](https://github.com/sourcegraph/scip)** | Apache-2.0 | lint / print / stats / experimental SQLite convert |
| **[`src-cli`](https://github.com/sourcegraph/src-cli)** | Apache-2.0 | Sourcegraph API client; needs a server to talk to |

**What's private or gated:**

- Sourcegraph self-hosted server (private since Aug 2024; free-tier capped at ~10 users per historical pricing, verify at [sourcegraph.com/pricing](https://sourcegraph.com/pricing))
- Cody Gateway, enterprise context/embedding services
- Cross-repo code-nav orchestration layer (the query planner that stitches Zoekt + SCIP)

**Consulting takeaway:** you can legally run **Zoekt + SCIP indexers + scip CLI** for commercial work without a Sourcegraph license. What you're missing is the unified UI, permission sync, and the cross-repo query planner — that's what the proprietary server sells.

### 2. Kythe Is a Zombie, Not an Answer

Google's Kythe (github.com/kythe/kythe) has the academic pedigree but has effectively lost the race.

- **Last release:** v0.0.75 on 2025-03-12 — the only 2025 release. Previous cadence (every 2-3 months) collapsed.
- **Team reality:** the US-based Kythe team was laid off in April 2024 and replaced by an India-based maintenance team. ([Wikipedia](https://en.wikipedia.org/wiki/Google_Kythe))
- **Language coverage:** production-grade only for C++, Go, Java. Python/TS/JS are partial; Rust is experimental.
- **External adoption:** 265 stars after ~10 years for an infrastructure project of this ambition — effectively none. Sourcegraph explicitly chose to build SCIP rather than adopt Kythe. ([SCIP announcement](https://sourcegraph.com/blog/announcing-scip))
- **No Kythe → SCIP bridge exists.** Discussed in [sourcegraph/sourcegraph-public-snapshot#42280](https://github.com/sourcegraph/sourcegraph-public-snapshot/issues/42280), never shipped.

**Verdict:** Kythe compiles and Google still uses it internally, but it will keep drifting. Do not build on it in 2026.

### 3. SCIP Indexer Ecosystem: First-Tier Five, Weak Long Tail

SCIP is the real per-language indexer layer. Coverage as of April 2026:

| Language | Repo | Latest release | Status |
|---|---|---|---|
| **Java / Kotlin / Scala** | [scip-java](https://github.com/sourcegraph/scip-java) | v0.12.3 (2026-04-02) | Actively maintained — first tier |
| **Go** | [scip-go](https://github.com/sourcegraph/scip-go) | v0.2.3 (2026-04-22) | Actively maintained — first tier |
| **C / C++** | [scip-clang](https://github.com/sourcegraph/scip-clang) | v0.4.0 (2026-02-23) | Actively maintained — first tier |
| **Ruby** | [scip-ruby](https://github.com/sourcegraph/scip-ruby) | v0.4.7 (2025-11-07) | Moderately active; Sorbet-based |
| **Kotlin** | [scip-kotlin](https://github.com/sourcegraph/scip-kotlin) | v0.6.0 (2025-09-08) | Moderately active |
| **TypeScript / JavaScript** | [scip-typescript](https://github.com/sourcegraph/scip-typescript) | v0.4.0 (2025-10-02) | Slowing — ~6-month commit gap |
| **Python** | [scip-python](https://github.com/sourcegraph/scip-python) | (no tagged release) | Slowing |
| **C#** | [scip-dotnet](https://github.com/sourcegraph/scip-dotnet) | v0.2.12 (2025-03-14) | Lagging |
| **Rust** | rust-analyzer `scip` subcommand | rolling | Not Sourcegraph-owned; upstream |
| **PHP** | [scip-php](https://github.com/davidrjenni/scip-php) (community) | no releases | Active commits, no tags |
| **Dart** | [scip-dart](https://github.com/Workiva/scip-dart) | 1.6.2 (2025-05-28) | Community; low activity |
| **Swift** | no first-party indexer | — | Effectively absent |

**Cross-repo composition with SCIP:** the format is designed for it — SCIP symbol strings are `scheme manager name version descriptor` tuples, globally unique *if* you orchestrate consistent `(project-name, version)` coordinates across repos. The symbol format is a workable cross-repo join key; the missing piece is a query engine. Sourcegraph's own [cross-repo nav docs](https://sourcegraph.com/blog/cross-repository-code-navigation) and [scip-clang/docs/CrossRepo.md](https://github.com/sourcegraph/scip-clang/blob/main/docs/CrossRepo.md) confirm the approach and flag the quadratic-dependency-indexing cost as a real operational concern.

**Query tooling outside Sourcegraph:**
- `scip convert` (experimental) — produces a per-index SQLite database. Stable enough to prototype on.
- No OSS multi-index merge tool exists.
- [`uber/scip-lsp`](https://github.com/uber/scip-lsp) (MIT) — standalone LSP server over a SCIP index; **single-repo only** per its README. The closest reference implementation of "query SCIP without Sourcegraph."
- [Meta Glean](https://glean.software/) consumes SCIP in its code-intel pipeline.
- GitLab has a [standing issue (#412981)](https://gitlab.com/gitlab-org/gitlab/-/issues/412981) for native SCIP support — not yet shipped.

### 4. The OSS Code-Search Stacks Don't Do Symbol Resolution

This is the single most important disambiguation in the landscape. **All of these are cross-repo text search, not cross-repo symbol resolution.**

| Tool | Cross-repo symbol resolution? | Index | License | 2025-26 status |
|---|---|---|---|---|
| **Zoekt** | No — ctags used only for ranking | positional trigram | Apache-2.0 | Active (Sourcegraph fork is upstream) |
| **OpenGrok** | No — within-repo ctags xref, name-only across projects | Lucene + ctags | CDDL-1.0 | Active; 1.14.4 Oct 2025 |
| **Hound** | No — regex only | trigram | MIT | Largely dormant |
| **Livegrep** | No — regex only | suffix array | MIT (BSD-like) | Low activity |
| **Sourcebot** | No — it's Zoekt with a UI | trigram (via Zoekt) + ctags | MIT | Active, growing |

Sourcebot in particular deserves a specific callout: the "open-source Sourcegraph alternative" marketing is **misleading if you need code intelligence**. Sourcebot replaces Sourcegraph's search layer (Zoekt-equivalent) with a genuinely MIT-licensed repackaging plus an MCP server for agent access. It does not ship SCIP indexers and does not do cross-repo jump-to-definition. If your consulting buyer asks "can we replace Sourcegraph with Sourcebot," the honest answer is "only if you only used Sourcegraph for search, not code nav."

([sourcebot-dev/sourcebot](https://github.com/sourcebot-dev/sourcebot), [Show HN: Sourcebot](https://news.ycombinator.com/item?id=41711032))

### 5. The AST-Pattern Tools: Only Stack-Graphs Does Real Resolution, and It's Archived

| Tool | Cross-repo symbol resolution? | Representation | License |
|---|---|---|---|
| **ast-grep** | No — syntactic patterns only | tree-sitter AST + pattern DSL | MIT |
| **Semgrep OSS** | No — OSS is intra-file; cross-file is Pro-gated | Generic AST + dataflow | LGPL-2.1 (Pro is proprietary) |
| **tree-sitter tags queries** | No — flat def/ref labels, no resolution | tree-sitter + Scheme queries | MIT |
| **tree-sitter stack-graphs** | **YES — but archived 2025-09-09** | tree-sitter + graph path-finding | MIT/Apache-2 |
| **universal-ctags** | Name-level only, no scope awareness | regex parsers + flat tags | GPL-2 |

**Critical finding:** [`github/stack-graphs` was archived on September 9, 2025](https://github.com/github/stack-graphs/releases) and is read-only. Stack-graphs was the only OSS tool in this landscape that actually implements cross-repo name resolution as a design goal — GitHub's own precise code nav runs on it. The algorithm (Creager 2022, [arxiv.org/pdf/2211.01224](https://arxiv.org/pdf/2211.01224)) remains sound, and the Rust library still compiles, but:

- Production rulesets existed only for JS/TS/Python/Java
- Even for Python, [issue #430](https://github.com/github/stack-graphs/issues/430) documents that multi-file module resolution never fully worked
- No MCP server wraps it
- No fork has emerged as a live successor (as of this research)

This is the single biggest update from Wave-1 expectations: the obvious "right answer" is abandoned. Any DIY plan built on stack-graphs must fork a dead project.

**Semgrep OSS deserves a note:** Semgrep's "Pro Engine" (closed source, SaaS) does cross-file analysis; Semgrep OSS is explicitly intra-file / intra-procedural only per [Semgrep's own docs](https://semgrep.dev/docs/semgrep-pro-vs-oss). If a buyer conflates "we use Semgrep" with "we do symbol analysis across files," clarify the tier.

### 6. The MCP-Era Landscape: Lots of Entrants, None That Deliver

The MCP ecosystem (late 2025 - early 2026) has produced ~10+ projects claiming code intelligence. None of them deliver production-grade cross-repo symbol resolution.

**Serena ([oraios/serena](https://github.com/oraios/serena))** is the single-repo baseline. LSP-based (wraps rust-analyzer, pyright, gopls, etc. via `multilspy`), 40+ languages, mature. Architecturally single-workspace because LSP servers are workspace-scoped. [Discussion #758](https://github.com/oraios/serena/discussions/758), [Discussion #1088](https://github.com/oraios/serena/discussions/1088), and [Issue #492](https://github.com/oraios/serena/issues/492) document the constraint and the multi-instance workarounds (one Serena per repo, registered under distinct MCP names; or Agentpool for spawning per-repo agents). Neither workaround is true cross-repo resolution — they're toggles.

**The multi-repo MCP entrants:**

| Project | Stars | Last commit | License | Real cross-repo resolution? | Honest assessment |
|---|---|---|---|---|---|
| [**Gortex**](https://github.com/zzet/gortex) | 20 | 2026-04-23 | PolyForm Small Business (not OSI) | **Closest to yes** — qualified-name matching across repos with tiered confidence (lsp_resolved > ast_resolved > text_matched) | 2 weeks old, solo, non-OSI license. Most honest about the cross-repo ambition; brittle and not buildable-on. |
| [**DeusData codebase-memory-mcp**](https://github.com/DeusData/codebase-memory-mcp) | 1,803 | 2026-04-18 | MIT | **No** — per-repo SQLite, no cross-repo resolution | Biggest traction in the space. Real but per-repo; LSP-style type resolution only on Go/C/C++. Claims 66 langs via tier-graded grammars. 83% answer quality on 31-repo benchmark is [self-reported in preprint](https://arxiv.org/abs/2603.27277) — treat as marketing evidence. |
| [**Narsil MCP**](https://github.com/postrv/narsil-mcp) | 137 | 2026-02-25 (stale ~2 months) | Apache-2.0 | No — per-repo scope-hint resolution, not true cross-repo | Rust, 90 tools, 32 langs, SPARQL/RDF output behind `--features graph`. Mature for solo project but going stale. |
| [**Repowise**](https://github.com/repowise-dev/repowise) | 1,251 | 2026-04-22 | custom | **No** — docs/analytics focus, not symbol resolution | Surprisingly high traction but wrong tool for this use case. |
| **jonnydb/code-graph-mcp** (original MRCIS) | — | — | — | **Dead** — repo is 404 | LobeHub listing is stale. Don't rely on. |
| [**sdsrss/code-graph-mcp**](https://github.com/sdsrss/code-graph-mcp) (successor) | 26 | 2026-04-23 | **no license** | No — single-workspace | 6 weeks old, no license = legally unusable. |
| **[Sourcegraph Official MCP](https://sourcegraph.com/mcp)** | — | — | proprietary | **Yes** — but requires paid Sourcegraph backend | Free self-hosted tier appears deprecated per [morphllm's competitive page](https://www.morphllm.com/comparisons/sourcegraph-alternative); pricing starts ~$49/user/month. [najva-ai wrapper](https://github.com/najva-ai/sourcegraph-mcp) is 5 months stale. Only works if you already pay. |
| Stale/toy entrants (ChrisRoyse/CodeGraph, mufasadb/code-grapher, eric050828/graph-codebase-mcp, yohannhommet/mcp-repo-search-server, bobmatnyc/mcp-vector-search, rergards/mempalace-code, Code Pathfinder) | <50 each | varies | none/mixed | No | Abandoned, toy-stage, or wrong scope. |

**LSP protocol ceiling:** LSP 3.17 technically supports `workspaceFolders` and `workspace/didChangeWorkspaceFolders`, and `workspace/symbol` returns results across all roots. But **most production language servers (rust-analyzer, gopls, pyright, clangd) are workspace-scoped in practice** — external package references resolve to package build artifacts, not to another cloned repo. Metals (Scala) is a rare multi-root-aware exception. This is the protocol-level ceiling Serena sits under; patching Serena to be multi-root wouldn't unlock cross-repo resolution unless the dependency graph is inside the workspace.

([LSP 3.17 spec](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/), [Metals workspace folders](http://scalameta.org/metals/blog/2023/07/17/workspace-folders/))

### 7. The DIY Path: SCIP + DuckDB + MCP as a Weekend MVP

With stack-graphs archived and no OSS multi-repo MCP delivering real resolution, the cleanest DIY path is an SCIP-centric pipeline over a query store, exposed as an MCP server. The plumbing is tractable; the hard naming problem is already solved by SCIP symbol strings.

**Weekend MVP (~16 hours):**

1. Shell script: per-repo, run the appropriate `scip-*` indexer (scip-python, scip-typescript, scip-go, scip-java, scip-clang, scip-ruby).
2. `scip convert <index.scip>` → per-repo SQLite.
3. DuckDB `ATTACH` every SQLite DB into one analytical session.
4. MCP server with two tools: `find_definition(symbol)` and `find_references(symbol)`, implemented as `UNION ALL` queries across attached DBs, keyed on SCIP symbol string.
5. Coverage: 3-6 languages (the first-tier SCIP indexers), no tree-sitter fallback, no incremental reindex.

This is the minimum shape that actually delivers "call in repo A resolves to def in repo B" across the languages where SCIP works. It buys a demo and real cross-repo nav.

**Month-scale expansion (~80 hours):**

- Orchestrator that assigns consistent `(package-name, version)` coords to every repo so SCIP symbol strings align
- universal-ctags / tree-sitter-tags fallback for languages without SCIP indexers (Swift, PHP long-tail, etc.)
- Incremental reindex on git push
- More MCP tools: hover, list_symbols_in_file, find_implementations
- Postgres backend if multi-user / concurrent access needed
- Cross-repo dependency-aware scheduler to mitigate quadratic reindexing (scip-clang's CrossRepo.md documents this cost)

**Startup scope (6+ months, team):** solve the quadratic-dependency-indexing problem properly; fill missing-indexer gaps (scip-swift, scip-rust as first-class); enterprise auth; UI; eval harness. This is where Sourcegraph spent engineer-decades. Don't go here solo.

**Storage backend reality:**
- **SQLite + DuckDB ATTACH** is the only path with a working precedent (`scip convert` → SQLite; DuckDB's SQLite extension is stable)
- **Postgres** has zero public code-intel precedent but is plausible
- **Tantivy / Qdrant / Neo4j** — no meaningful precedent; don't add these unless a specific requirement demands them

### 8. Pattern-Level Clustering

Zoom out and the OSS landscape sorts into four patterns, not 20 tools:

| Pattern | What it does | What it doesn't do | Best-of-breed OSS |
|---|---|---|---|
| **Trigram + ctags** | Fast regex code search with name-level symbol ranking across repos | Scope-aware resolution; disambiguation under overloading | Zoekt, OpenGrok, Sourcebot |
| **Pattern matching** | Syntactic shape queries over AST, per file/repo | Any symbol binding at all | ast-grep, Semgrep OSS |
| **LSP wrapper** | Workspace-scoped, compiler-grade resolution | Cross-workspace edges | Serena, uber/scip-lsp |
| **SCIP pipeline** | Per-repo precise index; cross-repo works *if* orchestrated | No OSS query engine for multi-index merge; relies on your plumbing | scip-* indexers + DIY |

The "fifth pattern" — **stack-graphs (cross-repo scope resolution)** — was real until September 2025 and is now abandoned. Nothing has replaced it.

## Named Winners Per Use Case

**"Closest thing to Sourcegraph self-hosted, free, today":**
- For ≤10 users internally: **Sourcegraph self-hosted free tier.** Proprietary EULA but zero-effort, and the feature set is intact at that scale. Verify the current user cap at [sourcegraph.com/pricing](https://sourcegraph.com/pricing).
- For OSI-pure: **Zoekt + SCIP indexers + uber/scip-lsp** — cross-repo text search and symbol indexes without Sourcegraph. Missing the unified query planner.

**"DIY tree-sitter / SCIP path, OSS only":**
- **scip-* indexers + `scip convert` SQLite + DuckDB ATTACH + custom MCP wrapper.** Weekend scope, 3-6 languages, real cross-repo go-to-def.

**"MCP server that beats Serena at cross-repo":**
- **Doesn't exist yet.** Gortex is the closest honest attempt (2 weeks old, non-OSI license). DeusData has traction but is per-repo. Everything else is marketing.
- This is a real ecosystem gap.

**"Commercial fallback if OSS is insufficient":**
- **Sourcegraph Enterprise.** The only thing that works at scale today. Tradeoff: cost, vendor lock-in, political cost with OSS-preferring clients.

## The "Sourcegraph Went BSL" Disambiguation for Consulting Buyers

When a consulting buyer says "we want to move off Sourcegraph because of licensing," clarify what they actually need:

| Capability | OSS replacement exists? |
|---|---|
| Cross-repo regex/text search | **Yes** — Zoekt (Apache-2.0) or Sourcebot (MIT) |
| Per-repo symbol indexing | **Yes** — SCIP indexers (Apache-2.0) + uber/scip-lsp |
| Cross-repo go-to-definition | **No OSS product** — DIY is tractable (~weekend-month scope) or use Sourcegraph's ≤10-user free tier |
| Cody-style AI assistant | **Client yes** (Cody Apache-2.0); **backend no** — you'd build your own context service |
| Code Insights, batch changes, audit logs | No — all enterprise-gated |

The most common buyer confusion is assuming "we need to replace Sourcegraph" means replacing all of it. Most only use the search + code-nav slice; that slice is partially replaceable.

## The Real Gap: "Serena for Cross-Repo" MCP Server

This is the opportunity. An OSS MCP server that:

1. Runs per-repo SCIP indexers (or reuses existing `index.scip` files)
2. Stores indexes in SQLite-per-repo, attaches them in DuckDB for query
3. Exposes MCP tools: `find_definition`, `find_references`, `hover`, `list_symbols`, `find_implementations`
4. Uses SCIP symbol strings as the cross-repo join key
5. Falls back to universal-ctags / tree-sitter-tags for languages without SCIP indexers
6. Ships as a single binary + config

No such project exists as of 2026-04-23. Every multi-repo entrant either took a tree-sitter-only route (loses precision) or a per-repo route (doesn't do cross-repo). The SCIP-native route is unclaimed.

This would be a publishable skill/tool candidate and a concrete differentiator for the Medium follow-up article already promised in the rag-demo piece (*"codebases are better off with a sourcegraph cross-repo tree"*). It also matches the consulting positioning: MCP/RAG for regulated industries, governance-first, OSS-preferring buyers.

**Sizing:** weekend MVP (3-6 langs, 2 tools) is genuinely tractable. A polished release with 10+ languages, incremental reindex, and good docs is a 1-2 month solo effort. "Serena-competitive" across 40+ languages with quality on par is a 6+ month team effort.

## Open Questions

- **Has any fork of `github/stack-graphs` emerged since archival?** Not surfaced in this research. If one has, it could change the DIY-path recommendation significantly.
- **DeusData's 83%/10× benchmark** — methodology in preprint arXiv 2603.27277 wasn't pulled. Worth reading before quoting the number.
- **scip-python's release story** — no tagged GitHub releases but active commits; distribution may be pip-only. Affects how you'd pin versions in a DIY pipeline.
- **Current Sourcegraph free-tier user cap** — historically 10, possibly shifted in 2024-2025. Verify directly at [sourcegraph.com/pricing](https://sourcegraph.com/pricing) before quoting.
- **Meta Glean's public OSS status for code-intel.** Referenced in the SCIP ecosystem writeups but not deeply investigated.
- **Gortex as it matures.** It's 2 weeks old as of this research; its cross-repo approach (qualified-name matching with tiered confidence) is the most honest OSS attempt but the license (PolyForm Small Business) is a real adoption barrier.

## Sources

### Sourcegraph licensing and BSL disambiguation
- [Sourcegraph makes core repository private (DevClass, 2024-08-21)](https://devclass.com/2024/08/21/sourcegraph-makes-core-repository-private-co-founder-complains-open-source-means-extra-work-and-risk/)
- [sourcegraph/sourcegraph-public-snapshot (frozen repo)](https://github.com/sourcegraph/sourcegraph-public-snapshot)
- ["Sourcegraph is no longer open source" — HN](https://news.ycombinator.com/item?id=36584656)
- [Sourcegraph went dark — Eric Fritz](https://www.eric-fritz.com/articles/sourcegraph-went-dark/)
- [Sourcegraph Wikipedia](https://en.wikipedia.org/wiki/Sourcegraph)
- [Sourcegraph handbook — licensing](https://github.com/sourcegraph/handbook/blob/main/content/departments/product/process/gtm/licensing.md)
- [Sourcegraph Pricing](https://sourcegraph.com/pricing)
- [Sourcegraph accepting Zoekt maintainership](https://sourcegraph.com/blog/sourcegraph-accepting-zoekt-maintainership)
- [Guide to Cody](https://www.software.com/ai-index/tools/cody)

### Kythe
- [Kythe releases](https://github.com/kythe/kythe/releases)
- [Kythe repo](https://github.com/kythe/kythe)
- [Kythe overview](https://kythe.io/docs/kythe-overview.html)
- [Google Kythe — Wikipedia (2024 team change)](https://en.wikipedia.org/wiki/Google_Kythe)
- [SCIP announcement — Sourcegraph blog](https://sourcegraph.com/blog/announcing-scip)
- [Investigate approaches for SCIP C++ indexer (Kythe→SCIP)](https://github.com/sourcegraph/sourcegraph-public-snapshot/issues/42280)

### SCIP ecosystem
- [sourcegraph/scip](https://github.com/sourcegraph/scip)
- [scip-java](https://github.com/sourcegraph/scip-java)
- [scip-go](https://github.com/sourcegraph/scip-go)
- [scip-clang](https://github.com/sourcegraph/scip-clang)
- [scip-ruby](https://github.com/sourcegraph/scip-ruby)
- [scip-kotlin](https://github.com/sourcegraph/scip-kotlin)
- [scip-typescript](https://github.com/sourcegraph/scip-typescript)
- [scip-python](https://github.com/sourcegraph/scip-python)
- [scip-dotnet](https://github.com/sourcegraph/scip-dotnet)
- [scip-php (community)](https://github.com/davidrjenni/scip-php)
- [scip-dart (Workiva)](https://github.com/Workiva/scip-dart)
- [uber/scip-lsp](https://github.com/uber/scip-lsp)
- [scip-clang CrossRepo.md](https://github.com/sourcegraph/scip-clang/blob/main/docs/CrossRepo.md)
- [LSIF → SCIP migration docs](https://sourcegraph.com/docs/admin/how-to/lsif-scip-migration)
- [rust-analyzer SCIP/LSIF — DeepWiki](https://deepwiki.com/rust-lang/rust-analyzer/9.2-scip-and-lsif-indexing)
- [GitLab SCIP support issue #412981](https://gitlab.com/gitlab-org/gitlab/-/issues/412981)
- [SCIP sqlite database? — scip#233](https://github.com/sourcegraph/scip/issues/233)
- [Cross-repository code navigation — Sourcegraph](https://sourcegraph.com/blog/cross-repository-code-navigation)

### OSS code search stacks
- [sourcegraph/zoekt](https://github.com/sourcegraph/zoekt)
- [google/zoekt](https://github.com/google/zoekt)
- [oracle/opengrok](https://github.com/oracle/opengrok)
- [OpenGrok Internals Wiki](https://github.com/oracle/opengrok/wiki/Internals)
- [hound-search/hound](https://github.com/hound-search/hound)
- [livegrep/livegrep](https://github.com/livegrep/livegrep)
- [Regular Expression Search with Suffix Arrays — Nelhage](https://blog.nelhage.com/2015/02/regular-expression-search-with-suffix-arrays/)
- [sourcebot-dev/sourcebot](https://github.com/sourcebot-dev/sourcebot)
- [Sourcebot docs overview](https://docs.sourcebot.dev/docs/overview)
- [Show HN: Sourcebot](https://news.ycombinator.com/item?id=41711032)

### AST-pattern and stack-graphs
- [ast-grep](https://github.com/ast-grep/ast-grep)
- [ast-grep MCP server](https://github.com/ast-grep/ast-grep-mcp)
- [Semgrep AppSec vs Community Edition](https://semgrep.dev/docs/semgrep-pro-vs-oss)
- [Semgrep Pro Engine](https://semgrep.dev/docs/semgrep-code/semgrep-pro-engine-intro)
- [Introducing stack graphs — GitHub Blog](https://github.blog/open-source/introducing-stack-graphs/)
- [Stack Graphs paper (Creager 2022)](https://arxiv.org/pdf/2211.01224)
- [github/stack-graphs (ARCHIVED 2025-09-09)](https://github.com/github/stack-graphs)
- [stack-graphs releases](https://github.com/github/stack-graphs/releases)
- [Python multi-file resolution issue #430](https://github.com/github/stack-graphs/issues/430)
- [tree-sitter-stack-graphs crate](https://crates.io/crates/tree-sitter-stack-graphs)
- [universal-ctags](https://github.com/universal-ctags/ctags)
- [Universal Ctags — other projects](https://docs.ctags.io/en/latest/other-projects.html)

### Serena and LSP ceiling
- [Serena repo](https://github.com/oraios/serena)
- [Serena language support](https://oraios.github.io/serena/01-about/020_programming-languages.html)
- [Serena Discussion #758](https://github.com/oraios/serena/discussions/758)
- [Serena Discussion #1088](https://github.com/oraios/serena/discussions/1088)
- [Serena Issue #492 multirepo](https://github.com/oraios/serena/issues/492)
- [Serena cross-repo workaround (Zenn)](https://zenn.dev/dk_/articles/1f558601b4a6c1?locale=en)
- [LSP 3.17 Specification](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/)
- [Metals workspace folders blog](http://scalameta.org/metals/blog/2023/07/17/workspace-folders/)
- [sublimelsp/LSP #33](https://github.com/sublimelsp/LSP/issues/33)

### MCP multi-repo entrants
- [Gortex](https://github.com/zzet/gortex)
- [Gortex origin writeup](https://zzet.org/gortex/from-gitnexus-to-gortex/)
- [DeusData codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp)
- [Codebase-Memory MCP site](https://deusdata.github.io/codebase-memory-mcp/)
- [Narsil MCP](https://github.com/postrv/narsil-mcp)
- [sdsrss/code-graph-mcp](https://github.com/sdsrss/code-graph-mcp)
- [MRCIS LobeHub listing (original repo 404)](https://lobehub.com/mcp/jonnydb-code-graph-mcp)
- [Sourcegraph Official MCP](https://sourcegraph.com/mcp)
- [najva-ai/sourcegraph-mcp](https://github.com/najva-ai/sourcegraph-mcp)
- [repowise-dev/repowise](https://github.com/repowise-dev/repowise)
- [How to Reference Code Across Repositories with Coding Agents — Eric Ma](https://ericmjl.github.io/blog/2025/11/17/how-to-reference-code-across-repositories-with-coding-agents/)
- [Sourcegraph Alternative — Morph comparisons](https://www.morphllm.com/comparisons/sourcegraph-alternative)

### Context
- [AI Coding Assistants Don't Understand Your Code: LSP, SCIP, and Real Code Intelligence](https://machinesdoitbetter.ai/ai-coding-assistants-dont-understand-your-code-lsp-scip-and-real-code-intelligence-2/)
- [DuckDB SQLite Extension](https://duckdb.org/docs/current/core_extensions/sqlite)
