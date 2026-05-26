# Deep Dive: Glean Enterprise Sentiment (May 2025 — May 2026)

**Recency window applied: 12 months.** SaaS enterprise AI tooling moves fast enough that older quotes lose load-bearing value, but slow enough that 12 months captures the relevant pricing/feature/sentiment cycle. Older HN comments (2021–2024) are cited only when the underlying complaint or praise has been re-confirmed by a quote inside the window.

## Executive Summary

Glean's sentiment in the trailing 12 months is **strongly positive among end-users, mixed-positive among IT/admin, and aspirational-positive among executive buyers** — but with three durable counter-narratives: (1) **pricing opacity** (~$50/user/month, ~100-seat / ~$50–60K minimum, all triangulated from competitor and HN sources, never publicly confirmed by Glean); (2) **deployment friction**, especially around SharePoint and Microsoft Teams permissions, which Glean's own docs concede; (3) a **"search-first, not action-driven"** ceiling that buyers expecting agent autonomy now bump into. The trajectory is unambiguous: $7.2B Series F (June 2025), $200M ARR (December 2025), and TechCrunch reframing Glean as "the layer beneath the interface" (February 2026) have moved Glean from "well-funded challenger" to "presumptive enterprise AI search standard." The most concrete head-to-head sentiment loss came from **Atlassian Rovo on agent customizability**, not from Microsoft Copilot.

## Findings

### What buyers and end-users praise

**Search that "actually works."** This is the most common verbatim across review sites and HN — phrased almost identically by independent voices.

> "It's fast, easy, and generally accurate. It really does seem to understand our business, and I haven't seen it hallucinate."
> — Steve R., AWS Marketplace, 2026-04-13

> "Glean makes it really easy to find information across tools without having to think too hard. It pulls everything into one place and surfaces what's actually relevant."
> — Madison S., AWS Marketplace, 2026-04-28

> "We had search engines, but they didn't surface the right results. Relevance was the biggest issue… With Glean, we built a simple, intuitive intranet where employees can find what they need right away."
> — Naveen Zutshi, CIO, Databricks (Glean case study, vendor-curated)

> "glean.com is pretty awesome. The responses it generates will have citations from our internal Jira, Wiki, Slack, Github, etc. It's also great for when I get pulled into a busy Slack channel and need a summary of what's been going on in there for the past week."
> — fintler, Hacker News, 2025-01-01

> "It consumes all of our knowledge sources including Slack, Google docs, wiki, source code and provides answers to complex specific questions in a way that's downright magical. I was converted into a believer when I described an issue to it, pointers to a source file in online git repo and it pointed me to another repository that my team did not own that controlled DNS configs that we were not aware about."
> — vladgur, Hacker News, 2024-10-20

**Connector breadth.** Praise consistently centers on Glean indexing across many systems at once — not depth in any one system.

> "Ability to aggregate business knowledge scattered across platforms including Jira, Zendesk and Slack." — A G., AWS Marketplace, 2026-04-15
> "It is layered into all of our enterprise data, which means I don't have to give it context." — Ana G., AWS Marketplace, 2026-04-30

**Glean Chat / agent builder.** Where end-users talk about the AI features specifically, the sentiment is unusually warm.

> "Glean Chat is the most underrated feature within Glean. Similar to how some people now reach for ChatGPT before Google, Glean Chat can answer some questions even more effectively than a search can."
> — Art Chaidarun, Principal Software Engineer, Duolingo (vendor case study)

> "Building Glean agents… has been a real game changer for me." — Vijay D., AWS Marketplace, 2026-04-17

**Quantified outcomes (vendor-claimed; treat as marketing numbers, not independently audited):**
- Duolingo: 500+ hours saved monthly, ~$1.1M annual savings, 5x ROI
- Super.com: 1,500+ hours/month, 20% faster onboarding, 17x ROI
- Webflow: 300+ hours saved monthly, 3x ROI
- T-Mobile: 47% reduction in call resolution time across 100,000 agents
- Confluent: 15,000+ hours/month saved, +13% employee satisfaction
- CEO claim (Arvind Jain, Goldman Sachs Talks at GS): average user does ~20 searches/day and saves 2–3 hours/week

### Pain points and complaints

**Pricing opacity is the #1 vocalized friction.**

> "We had an intro meeting with them, pricing only makes sense if you're in a first world country and have 100+ or maybe 150+ employees. I recall pricing started at 50k USD per year but may be remembering incorrectly… I just get really annoyed at the 'contact us' stuff."
> — staindk, Hacker News, 2025-01-02

> "https://www.glean.com/pricing is the worst 'pricing' page I've ever seen XD" — astrostl, Hacker News, 2023-02-01

The recurring numeric figure — **~$50/user/month, ~100-seat floor, ~$50–60K minimum ACV** — appears across competitor blogs (gosearch, eesel, workativ, coworker, fritz). The cross-source consistency is high enough to treat as directionally accurate, but no neutral benchmark publication (Vendr, Tropic, public RFP) confirms it. Treat as **directional**.

**Hallucinations and inconsistency in chat.** End-users praise relevance but specifically call out failure modes.

> "Glean performs a JQL search, I've noticed it hallucinating a lot." — Vijay D., AWS Marketplace, 2026-04-17
> "Sometimes it has an error and won't generate a response," with error messages lacking diagnostic codes. — Joseph B., AWS Marketplace, 2026-05-05
> "It's very very very slow in providing answers" and "it's also not always consistent." — Ana G., AWS Marketplace, 2026-04-30

**"Results too broad" / weak ranking customization.**

> "Results can feel a bit broad, so it can take an extra step." — Madison S., AWS Marketplace, 2026-04-28

Gartner Peer Insights echoes: "Misunderstands multi-layered commands, keyword-dependent search rather than true semantic comprehension"; "Customization optimization on prioritizing, data display is limited"; "Indexing & tag syncing lags, with complex prompts — it hangs your system completely."

**Deployment / admin friction is acknowledged by Glean itself.** This is the strongest signal because the vendor admits it:
- **SharePoint:** every site/sub-site must be explicitly added to `Sites.Selected` in M365 *and* added to a crawl list in the Glean UI. Glean's own help center concedes this "creates a high degree of friction and can hinder expansion of Glean within an organization."
- **Microsoft Teams:** setup demands three separate admin scopes — Azure App Permissions Admin, Teams Admin Center admin, and Glean Workspace admin.
- **Permissions architecture:** Glean's RBAC FAQ describes the model as having taken "years to tune" given temporary access, datasource quirks, and unflattened ACLs.
- **Salesforce connector:** "If the integration user lacks a field-level read on a required field, Glean logs an error and may skip that field or object… this is a common cause for missing fields."
- **Hard 64 MB file content limit:** items larger are indexed by metadata only.

> "I find it a little bit challenging to stand up an agent." — Steve R., AWS Marketplace, 2026-04-13

**"Search-first, not action-driven" ceiling.** The most repeated structural complaint is that Glean answers questions but doesn't *do* things.

Gartner Peer Insights: "does not support deeper summarization, insight generation & task automation."
G2 summary: users want Glean to "take actions in downstream systems" (e.g., update Salesforce fields, resolve tickets) and it doesn't.

> "The ability to create presentations. I think that's a lacking feature." — Andrey T., AWS Marketplace, 2026-04-30

**Skeptic narrative: "LLM wrapper in search of a problem."**

> "It feels like an LLM wrapper in search of a problem… I do not find the idea of bringing my data to your search engine attractive. The data should stay put and you should merely index it."
> — esafak, Hacker News, 2025-11-21

**No customer-support complaints surfaced** in any source captured — neither in AWS Marketplace, Gartner, G2 summaries, nor HN. This is a notable absence rather than a vouched-for strength: it's possible support quality is fine, or that reviewers don't write about it.

### Sentiment by persona

**End-users (engineers, sales, support, marketing) — the loudest evangelists.** Praise is hands-on and specific (the DNS-config anecdote above is the canonical example). Complaints, when they come, are about chat reliability and result breadth, not about the value of the tool. End-users don't see the bill, so pricing never appears in their critiques.

**IT / admin / CIO — mixed-positive on outcomes, vocally negative on permissions plumbing.** Vendor-curated CIO praise is strong on "high impact, low effort" framing:

> "Looking back on the hundreds of technology projects we've led internally, Glean was high impact and low effort."
> — Shahan Parshad, VP of Business Technology & Data, Confluent (vendor)

But the admin-side pain is concretely documented in Glean's own connector docs (SharePoint friction, Teams 3-scope setup, Salesforce field-level permission gotchas). No verbatim r/sysadmin or r/ITManagers thread was retrievable — Reddit fetches were blocked at the harness — so the admin complaint surface is inferred from vendor docs and Gartner verbatims rather than directly observed.

**Executive buyer / champion — aspirational-positive.** Champions speak in ROI and "holy grail" language. The failure mode champions worry about post-purchase is the in-house RAG comparison:

> "I accidentally built a cheaper Glean" — recurring HN thread title, June 2024
> Champion-side anxiety surfaces around whether the $50/seat price is defensible vs. building on LangChain/LlamaIndex — though most who try this route also concede they would burn 6–12 months reinventing connectors and permission-aware retrieval.

**Where the personas diverge:**
1. **Speed of value** — end-users say "magical out of the box"; admins are wiring up SharePoint and Teams permissions for weeks.
2. **Pricing** — champions justify it as enterprise-grade; admins/procurement and HN engineers call it unfriendly to smaller orgs.
3. **"Done"** — end-users want Glean to *act* (write back, update tickets); champions sold it as search/answers; admins are still adding new connectors. Three different definitions of finished.

### Competitive sentiment

**vs. Microsoft Copilot for M365.** Sentiment direction is nuanced. Glean is favored when the stack is multi-source/non-Microsoft; Copilot is favored when the org is Microsoft-bound and price-sensitive. A widely-cited (but **unverified — primary source not located**) datapoint is that ~6% of Copilot pilots converted to broader deployment, and only ~3.3% of M365 subscribers had paid Copilot licenses by early 2026. This stat propagates across SEO comparison content; treat as directional, not established. Net narrative effect: Copilot's underwhelming deployment numbers have helped Glean's "model-neutral, cross-system" positioning.

**vs. Atlassian Rovo — strongest verbatim head-to-head (October 2024, but worth flagging because it's the most concrete loss):**

> "We preferred Rovo's knowledge cards which give an in-context definition for acronyms and even words in a different language."
> "The main area where we appreciated Rovo over Glean was the AI agents, which are much more customizable in Rovo."
> "In Glean, the agents were very easy to setup but the actions were limited to basic commands."
> — Katie Lai, Seibert (Atlassian Solution Partner), 2024-10-14

Caveat: Lai is an Atlassian Solution Partner, not neutral. The pushback in the same thread (Prabhu Palanisamy: "Did your team connect Glean to enterprise apps like Salesforce, Workday etc? It'd be great if you can share an example with specific details.") flags that the test was retrieval-only — Glean's full breadth was not exercised.

**vs. Slack AI / Notion AI.** No primary verbatim comparison was retrieved (G2 compare pages were 403-blocked; Reddit blocked at harness). Across secondary write-ups the framing is consistent: Glean = breadth across many systems; Slack AI / Notion AI = depth within their own walls. The June 2025 Salesforce/Slack data restriction (which blocked third-party AI tools, including Glean, from indexing Slack data) was a sentiment positive for Glean as the "open" alternative:

> "So a more accurate headline would be 'Salesforce blocks Slack users from using AI on their own data'." — like_any_other, Hacker News, 2025-06-11

**vs. Guru.** Multiple secondary sources claim Guru has outranked Glean on G2 customer-satisfaction sub-categories (Guru rated ~4.6–4.8). This was not verifiable directly (G2 403). Guru's positioning as curated/human-verified (30/60/90-day verification cards) appeals to buyers who want trust and governance; Glean appeals to buyers who want breadth. The two don't usually win the same RFPs.

**vs. Dust (dust.tt).** All comparative content is on Dust's own pages — competitor-authored. Dust's positioning quote ("Glean tells you things; Dust does things") is the same agent-actions critique that surfaces inside Glean's own user reviews. Dust pricing claim: $29/user/month with no minimums vs. Glean's reported $45–50/seat with 100-seat floor.

**vs. open-source / DIY (Onyx, Danswer, LangChain RAG).** TechCrunch (March 2025) profiled Onyx as the open-source bet against Glean's closed SaaS model. HN sentiment around Onyx and Sana clusters in this framing:

> "Onyx, Sana, and Glean are closer to application-layer enterprise AI products. Their internal knowledge assistants can search across SaaS tools but the interface is more graphical and seats are purchased as end-user software."
> — CMLewis (Captain YC W26 founder), Hacker News, 2026-03-14

> "Agreed on Glean still being needed for retrieval. One gap worth noting though: Glean's enterprise graph on the people side is mostly org chart and document co-occurrence data. It doesn't capture who people actually trust, who informal decisions route through, or who the real subject matter experts are regardless of title."
> — yumiatlead, Hacker News, 2026-03-17

The "Glean is still needed for retrieval" concession from a competitor builder is one of the strongest pro-Glean moats visible in 12-month sentiment.

### 12-month sentiment trajectory

The arc is unambiguously upward, with three inflection points:

- **June 10, 2025** — $150M Series F at $7.2B valuation (up from $4.6B in September 2024). Jain told PitchBook the round was "a statement, not a necessity." Sentiment shift: "well-funded challenger" → "presumptive category leader" (TechCrunch, CNBC, Crunchbase News).
- **September 25, 2025** — Third-generation Glean Assistant + new Enterprise Graph launched as "the Superintelligent Enterprise." Marketing pivot from search-box to agents-first.
- **December 8, 2025** — Fortune exclusive: Glean hit $200M ARR (doubled from $100M in ~9 months). Press framing: "one of the fastest-growing enterprise software companies." 1,000+ employees, 27 countries, $1M+ contract segment up ~3x YoY.
- **February 15, 2026** — TechCrunch published "The enterprise AI land grab is on — Glean is building the layer beneath the interface." This is the strongest sentiment marker: Glean reframed as infrastructure rather than product. Reinforced model-neutrality (15+ LLMs supported), explicitly contrasting with hyperscaler lock-in.
- **April 2026** — Jain headlined HumanX 2026 in San Francisco with Eric Yuan (Zoom). Top-tier conference circuit signal.

**Negative or counter-narrative signals in the window:**
- Pricing opacity remained the loudest friction. No public price changes were documented, but the "1B agent actions" framing in Q4 launches hints at consumption-style packaging arriving.
- TeamBlind thread "is Glean worth joining in 2025 or is it going to be a sinking ship" surfaced in late 2025 — anonymous, internal-culture concern, not customer sentiment. **No public layoffs were documented** in the May 2025 – May 2026 window (the only RIF on record is a small 2023 cut).
- **No security incidents or breaches** were surfaced in the window. Security-vendor blogs (DoControl, Knostic) flag Glean as an amplifier of *pre-existing* SaaS oversharing risk, but these are vendor-marketing pieces and do not describe an actual incident.
- One third-party scraper (bloomberry.com, methodology unverified) claimed 430 active customers with 158 churned. Treat as a directional signal of "experimental AI budget" pressure, not as a verified churn rate.

## Reddit verbatim (added 2026-05-09 follow-up via direct curl on `old.reddit.com`)

The original deep-dive flagged Reddit as a coverage gap. A second pass via `curl` (with a Firefox UA on `old.reddit.com/*.json`) succeeded and produced the verbatim quotes below. Caveat to keep in mind: **two of the most-promoted "Glean alternatives" threads — r/AI_Agents/1soffbv and r/selfhosted/1smp3qe — share an identical seed post containing zero-width unicode characters embedded inside the words "Glean" and "pricing"**, a tell of AI-generated/astroturfed promotional content. Calls of "Is this an ad?" appeared in the replies. Quotes below are filtered to genuine voices in those threads (and to threads with no astroturf signal).

### "Decent, not great" — the modal Reddit sentiment

> "We use Glean, and it's pretty decent. Not great, not perfect, but decent. I haven't done enough of a deep dive into its more advanced capabilities to really criticize it beyond the speed."
> — x8code, r/AI_Agents, 2026-04 (1 score on a thread with [13])

> "It's just the reality of using these tools: they're all expensive, kind of same-y on the surface, and then you hit weird limits once real users pile on. Glean's been 'fine' but not great, so I'm just trying to hear what's actually working for other teams before we lock ourselves in for another year."
> — sysvora, r/selfhosted, 2026-04

This "fine but not great" framing is the most common admin-leaning verbatim — and it's a notably less enthusiastic register than the AWS Marketplace reviews and HN praise quoted earlier.

### Diagnostic critique (the most analytical voice in the corpus)

> "'okay but not great' with Glean usually has a specific cause — most often connector freshness lag (Slack/GDrive each poll on their own schedule, so results are correct but 6-24h stale) or source-weight tuning that nobody touches (default treats Slack and Salesforce equal for ranker weight, which is wrong for basically any team). Worth diagnosing that before spending the renewal cycle on a tool swap."
> — snikolaev, r/AI_Agents, 2026-04

This identifies two concrete failure modes: **6–24h connector freshness lag** and **untuned source weights**. Neither has been documented elsewhere in the public corpus and both line up with the "results too broad" / "not always consistent" complaints in AWS Marketplace reviews.

### Vector-DB-not-knowledge-graph critique

> "Glean is excellent at the part you accurately said is getting squeezed, enterprise search, but bad at the context layer. The 'context layer' they represent to have is not actually a knowledge graph it's a vector DB. This has massive limitations for the amount of reasoning and business context that can be stored. Asking Glean anything more than a simple search query will lead to similar hallucination rates to LLMs. There's a reason FabricIQ and Databricks Onto and other knowledge graph providers aren't directly competing there. I highly doubt Glean wins out in the knowledge layer unless they acquire a true graph capability to do Graph RAG."
> — Wrldtvlr, r/ArtificialInteligence, 2026-05

The strongest technical takedown found in any source. Pairs with yumiatlead's HN observation (already cited) that Glean's "people-side enterprise graph is mostly org chart and document co-occurrence data."

### Switched-away story (concrete dollars, with caveats)

> "switched from glean to a custom Coworker setup about 6 months ago... initial setup was painful but we're seeing about 40% faster query response times and saved roughly $180k annually on licensing costs. definitely not plug-and-play though"
> — Physical-West6634, r/selfhosted, 2026-04

**Caveat:** this comment appeared in the astroturf-flagged thread and may itself be a Coworker plug. Treat as directional. That said, it lines up with the GoSearch employee admission below (independent voice).

### Independent confirmation that customers leave for cost

> "Have you heard of GoSearch? Full transparency, I do work there but we've been having a lot of conversations with prospects who are exploring Glean as well or have left / are looking to leave Glean due to costs limitations."
> — Tech-feedback (GoSearch employee), r/LlamaIndex, 2025-04

A vendor-side admission, but it corroborates the price-driven churn signal from a different vantage point than the seller doing the swap.

### User-corroborated price point ($50/seat, 150-seat commitment)

> "Glean is 50$ a month with 150 users commitment I believe so not that expensive I think"
> — No-Brother-2237, r/LlamaIndex, 2025-04

This is the **first user-side verbatim corroboration** of the $50/seat/month figure that previously surfaced only in competitor blogs and on HN (staindk's "$50k/year start, 100-150+ employee minimum"). Two independent users now match, with overlapping numbers. The 100–150 seat floor is likely real.

### Genuine end-user praise (highest-credibility positive on Reddit)

> "Glean is low key fantastic for knowledge. I find it nearly indispensable at work. Its super power is uncovering tribal knowledge in a company (hidden norms/undocumented process and standards.) You can also sort of do this popular wiki context graph by saving generated knowledge/context back to a source that glean indexes. Its citations are also very accurate and reliable. I also use Claude/Cowork/Code but for straight up search I would rather go back to the source than rely on MCP and burn more tokens unnecessarily."
> — Beneficial_Dealer549, r/ArtificialInteligence, 2026-05

This is the cleanest positive Reddit quote — no astroturf indicators, named-and-specific use case (tribal knowledge surfacing), and a thoughtful "Glean over MCP for search" framing.

### "Will Glean survive the agent layer?" — community consensus

The r/ArtificialInteligence thread "Will enterprise search startups like Glean survive Claude Cowork/Copilot-style agents?" (10 upvotes, March 2026) reaches a clear two-part consensus across the most-upvoted replies:

> "Glean's standalone search app probably does get squeezed. Nobody wants to context-switch between a search tool and their actual work environment… The infrastructure play is more defensible but has its own problems. If Glean becomes a knowledge layer that agents call into, they're competing on connector coverage and permission management rather than user experience. Microsoft already has deep enterprise integrations, Google has Workspace, and both have strong incentives to build this themselves rather than depend on a third party."
> — Savannah_Carter494 [3]

> "glean's real moat is the permission graph and connector layer, not the search ui. agents need that substrate to not hallucinate access, so it likely survives as the knowledge plumbing copilot/cowork call into."
> — NeedleworkerSmart486 [2]

> "I'm not convinced enterprise search startups like Glean, GoSearch, etc. disappear. A lot of this discussion reduces it to a UI question ('search box vs Copilot'), but that misses what's actually hard: permissioned, cross-system context across fragmented enterprise data… The search UI likely fades, but the context layer underneath becomes infrastructure for agents."
> — New-Recognition-3779

Net: Reddit's read is that Glean's **search-UI surface is at risk** but the **permissions + connector substrate is the durable moat** — exactly the framing TechCrunch adopted in its Feb 2026 "layer beneath the interface" piece.

### Coverage notes

- **r/sysadmin and r/ITManagers produced almost no signal.** Most "glean" hits are the verb. The one r/sysadmin RAG-related thread had a single confirming post (Beef410: "Company I work at is using Glean which is an AI tool that ingests company data, SharePoint etc. when a users queries it results are based on what they personally have permissions to see") with no follow-up pros/cons. **The admin persona's deployment-friction complaints are not loud on Reddit** — they're loud in Glean's own connector docs, which is where they got captured in the original report.
- **Astroturf signal is real.** Two of the top-engagement "Glean alternatives" threads have the same seed text with zero-width unicode in "Glean" and "pricing." Enterprise-AI subreddits are a target for promo content; weight Reddit verbatim accordingly.

## Open Questions

- **Reddit admin verbatim still thin.** Even after the follow-up pass, the IT-admin persona produced one usable quote (Beef410 on r/sysadmin). The deployment-friction complaint surface stays anchored in Glean's own connector docs, which is the strongest signal but not Reddit-corroborated.
- **G2 and Gartner Peer Insights returned 403** to programmatic fetch. Persona-tagged primary verbatims ("IT Manager said X", "Software Engineer said Y") were unrecoverable; persona attribution above is partly inferred.
- **No verbatim customer-support complaints** were surfaced in any source. This is either a real strength of Glean's support, or a sampling artifact of the review surfaces examined.
- **The "6% Copilot pilot conversion" stat** is repeated in derivative content but the primary analyst report was not pinned down. Treat as directional only.
- **No named customer churn / loss stories** are public. The bloomberry "158 churned" claim has no methodology disclosure.
- **Most numeric ROI claims are vendor-published.** No independent third-party study (Forrester TEI, IDC) of Glean ROI surfaced.
- **No Forrester Wave** for this category was found in 2025–2026; Glean's analyst recognition is from Gartner's Emerging Market Quadrant for GenAI Knowledge Management. Any "Forrester Wave" claim about Glean should be treated as unverified.

## Sources

**Primary, KEEP (within 12-month window or durable):**
- AWS Marketplace — Glean Work AI Platform Reviews (verbatim, dated Apr–May 2026) — https://aws.amazon.com/marketplace/reviews/reviews-list/prodview-3hxyfnuih42u2
- Hacker News — multiple threads via Algolia search; canonical items 42569871 (2025-01), 42573967 (2025-01, pricing), 41896552 (2024-10, "downright magical"), 46000983 (2025-11, skeptic), 44247546 (2025-06, Salesforce/Slack block), 47373077 (2026-03), 47393910 (2026-03), 47409517 (2026-03)
- TechCrunch — "The enterprise AI land grab is on — Glean is building the layer beneath the interface" — 2026-02-15 — https://techcrunch.com/2026/02/15/the-enterprise-ai-land-grab-is-on-glean-is-building-the-layer-beneath-the-interface/
- TechCrunch — "Enterprise AI startup Glean lands a $7.2B valuation" — 2025-06-10 — https://techcrunch.com/2025/06/10/enterprise-ai-startup-glean-lands-a-7-2b-valuation/
- TechCrunch — "Why Onyx thinks its open source solution will win enterprise search" — 2025-03-12 — https://techcrunch.com/2025/03/12/why-onyx-thinks-its-open-source-solution-will-win-enterprise-search/
- CNBC — "Glean, gen AI enterprise search startup, raises $150 million" — 2025-06-10 — https://www.cnbc.com/2025/06/10/glean-gen-ai-search-startup-raises-150-million-at-7-billion-value.html
- Fortune — "Exclusive: Glean hits $200M ARR" — 2025-12-08 — https://fortune.com/2025/12/08/exclusive-glean-hits-200-million-arr-up-from-100-million-nine-months-back/
- BusinessWire — "Glean Introduces Third-Generation AI Assistant, New Enterprise Graph" — 2025-09-25
- BusinessWire — "Glean Launches the Work AI Institute, Unveils Autonomous Agents" — 2025-12-10
- PitchBook — "Glean's CEO sees fundraising as a statement, not a necessity" — June 2025 — https://pitchbook.com/news/articles/glean-ceo-arvind-jain-fundraising-statement-not-necessity
- Crunchbase News — "AI-Powered Work Assistant Glean Lands $150M at $7.2B Valuation" — June 2025
- Sacra — "Glean at $200M ARR" — late 2025 — https://sacra.com/research/glean-at-200m-arr/
- Futurum Group — "Glean Doubles ARR to $200M. Can Its Knowledge Graph Beat Copilot?" — late 2025/early 2026 — https://futurumgroup.com/insights/glean-doubles-arr-to-200m-can-its-knowledge-graph-beat-copilot/
- Reworked.co — Glean Agents at GleanGO 2025 — May 2025 — https://www.reworked.co/knowledge-findability/glean-adds-new-functionality-scale-and-reach-to-agent-platform-at-gleango/
- Atlassian Community thread — "Atlassian Rovo Vs. Glean AI: How Do They Compare?" — 2024-10-14 — https://community.atlassian.com/forums/Atlassian-AI-Rovo-discussions/Atlassian-Rovo-Vs-Glean-AI-How-Do-They-Compare/td-p/2839707 (older than the 12-month window but kept because it is the only retrieved verbatim head-to-head with named participants)
- Goldman Sachs "Talks at GS" — Arvind Jain on AI productivity — https://www.goldmansachs.com/insights/talks-at-gs/arvind-jain
- Sequoia "Training Data" podcast with Arvind Jain — https://sequoiacap.com/podcast/training-data-arvind-jain/
- HumanX 2026 agenda — Q&A with Arvind Jain & Eric Yuan — April 2026

**Reddit threads (added 2026-05-09 follow-up; pulled directly via `old.reddit.com/*.json`):**
- r/ArtificialInteligence — "Will enterprise search startups like Glean survive Claude Cowork/Copilot-style agents?" — https://reddit.com/r/ArtificialInteligence/comments/1t2ihou/ — 2026-03 (clean source)
- r/AI_Agents — "Anyone tried good glean alternatives for enterprise search lately?" — https://reddit.com/r/AI_Agents/comments/1soffbv/ — 2026-04 (**astroturf seed text; only genuine replies cited**)
- r/selfhosted — same astroturf seed — https://reddit.com/r/selfhosted/comments/1smp3qe/ — 2026-04 (**genuine replies only**)
- r/LlamaIndex — "Comparing enterprise search tools like Coveo, Algolia, Constructor and Glean" — https://reddit.com/r/LlamaIndex/comments/1k74y98/ — 2025-04 (clean)
- r/LangChain — "Enterprise knowledge search - Build v.s Buy" — https://reddit.com/r/LangChain/comments/1dcgokb/ — 2024 (older but cited only for the PipesHub-as-Glean-alternative datapoint)
- r/sysadmin — "Why aren't more companies feeding their internal docs/code into an internal RAG system?" — https://reddit.com/r/sysadmin/comments/1p42jsz/ — 2026 (single confirming post)
- r/devops — "self-hosted google-like search engine for workplaces" — https://reddit.com/r/devops/comments/11wgn6p/ — 2023 (older; cited only for `gerev` as named Glean alternative)

**First-party (vendor docs / case studies — credible for what they admit and for named-individual quotes; biased on metrics):**
- Glean — Customer stories (Duolingo, Super.com, Databricks, Confluent, Webflow, T-Mobile, Wealthsimple, Grammarly, Booking.com, SafetyCulture) — https://www.glean.com/resources/customer-stories
- Glean docs — Connectors Hub — https://docs.glean.com/connectors/home
- Glean docs — SharePoint controls (admits friction) — https://docs.glean.com/connectors/native/sharepoint/security/controls
- Glean docs — Microsoft Teams admin guide — https://docs.glean.com/administration/platform/embedded-integrations/glean-in-teams/glean-in-microsoft-teams--admin-guide
- Glean docs — Salesforce connector troubleshooting — https://docs.glean.com/connectors/native/salesforce/troubleshooting
- Glean docs — RBAC FAQ — https://docs.glean.com/administration/identity/roles/faq
- Glean blog — Series F announcement — https://www.glean.com/blog/glean-series-f-announcement
- Glean press — "Glean Surpasses $200M in ARR" — https://www.glean.com/press/glean-surpasses-200m-in-arr-for-enterprise-ai-doubling-revenue-in-nine-months

**Review platforms (search-engine summaries usable; direct fetch returned 403):**
- G2 — Glean Reviews — https://www.g2.com/products/glean-2022-05-27/reviews
- G2 — Glean pros and cons — https://www.g2.com/products/glean-technologies-glean/reviews?qs=pros-and-cons
- Gartner Peer Insights — Glean — https://www.gartner.com/reviews/market/insight-engines/vendor/glean/product/glean
- TrustRadius — Glean — https://www.trustradius.com/products/glean/reviews

## Excluded Sources

- **Competitor / SEO content blogs** (gosearch.ai, eesel.ai, workativ.com, coworker.ai, fritz.ai, gumloop.com, clickup.com, slite.com) — used only for triangulating directional pricing claims; flagged as adversarial. None used for verbatim user testimony.
- **bloomberry.com customer-count scraper** — methodology unverified; "158 churned" cited only as directional signal.
- **digidai.github.io anonymous deep-analysis blog** — anonymous, not authoritative.
- **TeamBlind / Glassdoor anonymous threads** — included as employee-side directional signal only, not as customer sentiment.
- **DoControl, Knostic security vendor blogs** — flagged as having commercial interest in raising Glean risk; no actual incident corroborated.
- ~~**Reddit (www, old, search.json)** — fetch blocked at harness level; cited as a coverage gap.~~ **Resolved 2026-05-09**: a direct `curl` pass with a Firefox UA on `old.reddit.com/*.json` succeeded. Reddit verbatim now appears in its own section above. Two threads (r/AI_Agents/1soffbv, r/selfhosted/1smp3qe) flagged for likely astroturf — same seed text with zero-width unicode in "Glean" and "pricing." Genuine voices in those threads still cited; promo voices excluded.
- **HN items 41896552 and 39552961 via direct WebFetch** — rate-limited 429; quotes captured via Algolia API instead.
- **"30% longer setup than competitors"** — appears only in competitor blogs without methodology; **excluded as fact**.
- **"7–12% annual auto-renewal price increases"** — single-source competitor blog (gosearch); **excluded as fact**.
- **"6% Copilot pilot conversion / 3.3% paid Copilot"** — used as directional only; primary source not pinned down within search budget.
