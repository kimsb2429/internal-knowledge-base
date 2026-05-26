# Deep Dive: Measuring Internal Knowledge Base ROI (Leadership Brief)

*Compiled 2026-05-18 — Recency window: 12 months strict (May 2025–May 2026), with select pre-2025 foundational sources retained and date-flagged.*

---

## Executive Summary

1. **Stop leading with "% productivity uplift."** It's the single most-dismissed framing in 2025-2026 CFO/board reviews. The peer-reviewed gap between self-reported and measured productivity gains is now ~4-10x (METR May 2026, MIT field experiments 2024-2025), and boards know it.
2. **Lead with unit economics on a named workflow.** Cost-per-resolved-ticket, hours-back-to-client, cost-per-RFP, FTE-equivalents redeployed (not "saved"). These survive scrutiny because they tie to a P&L line and a baseline.
3. **The one rigorous public number that holds up:** Harvard/BCG randomized field experiment of 758 BCG consultants — **+12.2% tasks completed, −25.1% time, +40% quality** on tasks inside the AI frontier (Dell'Acqua et al., Sept 2023). Older than 12 months but still the most-cited measured study and the only one with a real control group.
4. **Set expectations against the failure base rate.** 80%+ of enterprise AI projects fail to deliver business value (RAND 2024); 42% of companies have abandoned at least one initiative with average $7.2M sunk cost (Deloitte 2025); 61% of approved AI projects had no formal post-deployment measurement (MIT Sloan 2025). The board has heard these — be the team that pre-commits to measurement.
5. **Anchor on a recognized framework.** Forrester TEI (Benefits / Costs / Flexibility / Risk) for the business case; KCS v6 (Content Standard Checklist + PAR 2.0) for content/quality governance; APQC 5-level maturity model for the trajectory.

---

## Findings

### 1. Benchmark Numbers — What's Actually Citable

**Top-down projections (use sparingly; everyone has seen them):**
- McKinsey: GenAI could add **$2.6T–$4.4T annually** across 63 use cases; **~75%** of value concentrates in customer ops, marketing/sales, software engineering, R&D. *(McKinsey, Jun 2023 — foundational, dated.)*
- McKinsey "Superagency" 2025: **92%** of companies plan to increase GenAI investment over 3 years; only **1%** describe their deployments as mature. *(McKinsey, Jan 2025.)*

**Measured / commissioned-study numbers:**
- **Harvard/BCG RCT (758 consultants, Dell'Acqua et al., Sept 2023):** +12.2% tasks completed, −25.1% time, ~+40% quality on in-frontier tasks; **−19pp accuracy** on out-of-frontier tasks. ⚠️ *Older than 12 months but the canonical measured study; still re-cited by McKinsey, BCG, Gartner.*
- **Gartner HR research (Mar 2025):** Employees in adoption-focused orgs are up to **8% more productive** and **2.7×** as likely to experience speed/quality gains.
- **MIT field experiments (Cui et al., 2024-2025) on Copilot at Microsoft + Accenture:** **8-22% more PRs/week** (objectively measured) — vs **70-88% self-reported gains** in the same population. This gap is the single most-quoted critique against vendor TEI numbers.
- **METR (May 2026):** Technical workers overestimate AI's effect on their own time by ~40 percentage points vs. measured.

**Vendor-commissioned TEI studies (flag as such):**
- **Forrester TEI of Microsoft 365 Copilot for SMB (Oct 2024):** **132%–353%** 3-year ROI.
- **Forrester TEI of Microsoft Dynamics 365 Customer Service (Mar 2024):** **315%** 3-year ROI, **<6-month** payback on $3.54M investment.
- **Forrester TEI of Glean (commissioned by Glean):** Composite of 10,000-employee, $13B-revenue org at $40/user. *Specific 3-year ROI%/NPV/payback are in the PDF (linked below) but should be pulled directly before being put on a slide — not extracted into this brief.*

**Consulting-firm internal AI assistants (self-reported, no independent measurement public):**
- **McKinsey Lilli:** ~**70-72% firm-wide active**, **~500K prompts/month**, "up to **~30% time savings**" on search/synthesis (McKinsey self-reported, 2024).
- **Deloitte PairD, EY.ai, PwC ChatPwC, KPMG Workbench/Clara:** Investment dollars and seat counts disclosed; **no published productivity/ROI numbers**. The Big-4 are holding outcome metrics internal.

**Customer-service / external-facing comparators (use carefully):**
- **Klarna AI assistant (Feb 2024 PR):** 2.3M conversations in month 1, equivalent to 700 FTE agents, 25% drop in repeat inquiries, projected +$40M profit. ⚠️ *Walked back in late 2024-2025 as Klarna began rehiring humans — present as a cautionary tale of overclaiming, not a benchmark.*
- **Morgan Stanley AI @ MS Assistant (OpenAI, 2024):** 98% advisor adoption; retrieval efficiency reportedly 20% → 80%; query times "30+ minutes to seconds" across a 350K-doc corpus. Self-reported.
- **JPMorgan internal coding assistant:** CIO Lori Beer publicly stated **10-20% productivity gain** across "tens of thousands" of engineers (public remarks, 2024-2025). Primary URL not isolated; treat as directional.

---

### 2. Framework — What to Anchor the Brief On

Use three established frameworks together so the brief reads as governance-grade, not improvised.

**Forrester TEI (Total Economic Impact)** — the business-case structure
- Four equally weighted pillars: **Benefits / Costs / Flexibility / Risk**.
- Outputs risk-adjusted NPV, ROI, and payback over typically 3 years.
- "New Tech TEI" variant exists specifically for emerging tech (including GenAI) when there isn't enough customer history for a retrospective study — same four pillars, projected.

**KCS v6 (Knowledge-Centered Service) — Consortium for Service Innovation** — content/quality governance
- **Content Standard Checklist** (renamed from "Article Quality Index" / AQI in KCS v6) — sampled scoring against the org's content standard; <90% triggers coaching, <80% sustained → loss of KCS license.
- **Process Adherence Review (PAR 2.0, released July 2025)** — workflow-adherence instrument paired with content scoring.
- **Content Health Indicators (Technique 5.10)** — article state distribution (WIP/Approved/Published), reuse, link rate to incidents, age, views, self-service success, self-service vs. assisted ratio.
- Individual licensing ladder: Candidate → KCS I (Contributor) → II (Publisher) → III (Coach) → IV (Domain Expert).

**APQC Levels of KM Maturity** — the trajectory
- 5 levels modeled on CMMI: **Initial → Repeatable → Defined → Managed → Optimizing**.
- Core principle: link **adoption metrics** (participation) with **business outcomes** (efficiency). Different metrics apply at different levels.

**Gartner KM Maturity Model** — referenced widely but largely paywalled; cite Forrester + KCS + APQC for an unencumbered public-source brief.

---

### 3. Leading vs Lagging Indicators — Defensible vs Vanity

| Dimension | Leading (predict) | Lagging (confirm) | Vanity (avoid in board deck) |
|---|---|---|---|
| **Usage** | WAU / licensed users, depth-of-use (sessions per active user/week), repeat-user rate at **week 4 and week 8** (novelty-fade survival), share of queries answered without follow-up | Sustained WAU after 8 weeks, share of target workflows where the KB is the first port of call | Total queries, total page views, total articles, cumulative chat sessions, "users who logged in once" |
| **Quality** | Content Standard Checklist (AQI) score trend, PAR 2.0 pass rate, % answers with valid citations, retrieval **precision@k / recall@k** on a held-out eval set, **faithfulness/groundedness** score (Ragas-style), freshness-SLA compliance, coverage gap rate (queries with no relevant doc) | Hallucination/incident rate in production, thumbs-down rate, escalation rate from KB to human expert, content reuse rate, self-service success rate | Total articles in KB, average article length, "% reviewed this quarter" without checklist scoring, raw star ratings absent volume |
| **Productivity** | Time-to-first-answer per query, measured task-completion time on a **fixed task panel** (A/B or diff-in-diff), duplicate-question rate, expert-interrupt rate | Cycle time on instrumented end-to-end workflows (onboarding ramp, ticket handle time, proposal turnaround) **measured from system logs, not survey**; new-hire time-to-productivity | Self-reported "hours saved per week," survey-based "% more productive," NPS of the tool, exec testimonials |
| **Financial** | Cost-per-resolved-query trend, marginal infra cost per active user, license utilization %, attach rate of KB usage to revenue-bearing workflows | Forrester TEI Benefits realized (deflected labor, revenue lift); risk-adjusted NPV / payback; auditable **FTE redeployed** (not "saved") | Gross deflection count without channel-switch correction, undiscounted projected savings, "value of time saved" using fully-loaded rates on self-reported minutes |

**Leading → Lagging pairs to instrument from day one:**

| Leading | Predicted lagging outcome |
|---|---|
| Content Standard Checklist trend | Self-service success rate; hallucination/escalation rate |
| Coverage gap rate (zero-result queries) | Repeat-question rate; expert-interrupt volume |
| Retrieval precision@k + faithfulness score | Thumbs-down rate; downstream rework |
| % articles within freshness SLA | Wrong-answer incidents; trust-driven WAU decline |
| Repeat-user rate at week 4 | WAU sustained past week 8 |
| Measured task-completion delta on fixed panel | Cycle-time reduction in instrumented workflows |
| License utilization + depth-of-use | Realized TEI Benefits (deflected labor + revenue) |

---

### 4. Measurement Methods — How to Actually Gather the Numbers

**Log analytics**
- Pull queries from the search/retrieval layer (Elastic/Algolia/Glean/Coveo/ServiceNow KB). Track top-N "hot" queries, query volume trend, zero-result rate, repeat-query within session (proxy for "first answer didn't work"), CTR, dwell time.
- **Pitfalls:** synonyms inflate uniqueness; long-tail noise; PII risk in raw query strings; dwell time is confounded by article length; high CTR ≠ "good ranking" (can mean "users click anything and bounce"); zero-result can be a synonym problem, not a content gap.

**Deflection counting (handle with care)**
- Common formula: `Deflection rate = sessions with KB view AND no ticket / total sessions`. Vendor "15-30% healthy, 40%+ best-in-class" benchmarks are marketing, not science.
- **False positives:** user re-opens issue under new session ID; user gave up and Slacked a colleague (channel-switch); user "browsed" without an issue (drive-by Google traffic); bot traffic / internal QA inflating the denominator.
- **Correctives:** repeat-contact rate within 30 days as a counter-metric; explicit in-page "did this solve your problem? Y/N + filed-ticket flag"; **channel-switch-corrected deflection** (did the user re-ask in another channel within 24-72h?); cost-to-serve per resolved issue as the bottom-line proxy.

**Surveys (NPS / CSAT / productivity self-report / escape rate)**
- Standard: identical baseline + 30/60/90-day post.
- **Pitfalls — self-report inflation is the dominant risk:** 70-88% of Copilot users self-report gains vs. **8-22% measured** in MIT field experiments at Microsoft and Accenture; METR May 2026 confirms ~40pp overestimate. Mechanisms: confirmation bias, demand characteristics (employees know leadership funded it), recall bias, sunk-cost defense.
- **Mitigation:** triangulate self-report with at least one objective metric; ask about *specific incidents* ("the last time you used the KB"), not weekly aggregates.

**Time-motion / diary studies**
- Shadowed observation or experience-sampling (ESM) prompts during the workday.
- **Pitfalls:** observer effect (Hawthorne); diary fatigue → survivorship bias; small samples (n<50 typical); task heterogeneity makes pre/post comparison hard unless you fix the task set; cost is high → studies tend short → entangled with novelty effects.

**Quasi-experimental designs (the gold standard for AI tool ROI)**
- **Cluster-randomized rollout by team/region** (what the Microsoft and Accenture Copilot field experiments used).
- **Stepped-wedge / staggered rollout** — teams onboard in waves, randomized order; politically easier than withholding access.
- **Difference-in-differences** on objective metrics (tickets/agent, resolution time, PRs merged).
- **Pitfalls from MIT working paper:** low statistical power (uptake among the treatment group was low); spillover/contamination (at Microsoft, control-group developers were granted access partway through, collapsing the comparison); non-compliance (license granted ≠ tool used; use ITT vs ATT carefully); selection bias in voluntary rollouts.

**Bias considerations to pre-empt in the brief**
- **Hawthorne effect** — observed users change behavior; biases short-window measurements upward.
- **Novelty effect** — engagement and self-reported satisfaction spike in the first ~8 weeks then decay. Any ROI claim with a <60-day post-window overstates sustained impact.
- **Selection bias** — voluntary adopters expected the tool to help; pilot teams are typically high-performing or tech-forward; their results don't generalize.
- **Mitigations the literature consistently recommends:** stepped-wedge over voluntary opt-in, intent-to-treat analysis, ≥90-day observation, system-log metrics over self-report, **pre-register** the metrics so they can't be cherry-picked post hoc.

---

### 5. Leadership Framing — What Actually Moves Budget in 2026

**The framings that get funded:**

1. **"Relief now, transformation later."** Slide 1 names a specific pain point with a dollar figure. ("$4.2M/yr spent on Tier-1 support; pilot shows 38% deflection = $1.6M run-rate.") Vision-led decks are being deferred.
2. **Hard cost-out, not generic "productivity %."** Reduced manual hours, error rates, cycle time, lead time, cost-per-output (cost-per-ticket, cost-per-deal, cost-per-claim), and **headcount avoidance** (open reqs not backfilled, contractor spend eliminated). Tie every number to a P&L line.
3. **FTE-equivalents redeployed, not FTEs cut.** BCG May 2025 frames AI cost-out as **~20% FTE capacity gain in ops, ~20-30% in maintenance** — *capacity unlocked*, not bodies removed. Klarna is the cautionary tale.
4. **"Defensive AI."** "Our top 3 competitors are removing $X from cost-to-serve; we're 18 months behind." Competitive cost-structure framing has eclipsed innovation/future-proofing framing in 2025-2026.
5. **"Talent leverage."** Keep senior staff senior; AI absorbs junior-grade work. Particularly effective with services firms where pyramid economics drive margin.
6. **"Margin defense in a flat-revenue year."** When growth is hard, ops-cost takeout from AI funds itself.
7. **"Data foundation as prerequisite."** Frame the KB/RAG investment as the data layer that makes all future AI work cheaper — amortize across the broader AI roadmap.
8. **Pre-committed measurement.** Every approved use case ships with a baseline measurement, a target, and a **kill criterion**. This is the explicit antidote to the MIT-flagged 61% finding (no post-deployment measurement).

**The dismissal triggers — what gets you cut:**

- Generic "productivity uplift %" with no baseline.
- "Employee satisfaction" / NPS-only justifications.
- Vendor-commissioned TEI without internal replication or shadow-baseline.
- "Innovation" / "future-proofing" framings absent unit economics.
- Pilot demos without a production cost model.
- "We'll figure out value after we deploy."

**The contrarian numbers boards are now quoting back at vendors:**

| Statistic | Source |
|---|---|
| **80.3%** of AI projects fail to deliver business value (33.8% abandoned pre-prod, 28.4% complete-but-no-value, 18.1% can't justify cost) | RAND, 2024 — flagged as foundational base-rate |
| **42%** of companies abandoned ≥1 AI initiative; avg sunk cost **$7.2M** | Deloitte, 2025 |
| Only **~25%** of AI initiatives deliver expected ROI | IBM IBV, 2025 |
| **95%** of GenAI pilots fail to reach production ("the GenAI Divide") | MIT NANDA "State of AI in Business 2025" |
| **61%** of approved enterprise AI projects had no formal post-deployment measurement | MIT Sloan, 2025 |
| Self-report overstates measured productivity by **~40pp** | METR, May 2026; MIT field experiments 2024-2025 |
| Gartner: even adoption-focused orgs see **~8%** productivity gain (not the McKinsey headline) | Gartner HR Research, Mar 2025 |
| Gartner: **60%** of AI projects without AI-ready data will be abandoned through 2026 | Gartner, Apr 2026 |

The deck needs to acknowledge these explicitly — boards will. Pair each with a specific mitigation in the program plan.

---

## Recommended Brief Structure (Leadership-Ready)

Suggested 6-slide spine for the leadership conversation:

1. **The pain in dollars.** Current cost-to-serve / cost-per-output on one specific workflow. Baseline number, source, audit trail.
2. **What's plausible at the measured level.** Cite the Harvard/BCG RCT (+25% time, +40% quality on in-frontier tasks) and Gartner's 8% adoption-driven floor. Frame as the *defensible range*, not the McKinsey headline.
3. **What we will measure, before launch.** Lead/lag table (above), with the specific instruments. Name the 3-5 leading indicators and the 2-3 lagging outcomes they predict.
4. **How we will measure it.** Stepped-wedge rollout, 90-day post-window, system-log metrics, channel-switch-corrected deflection, fixed task panel for cycle-time deltas. Pre-register the metrics now.
5. **The base rate and how we beat it.** Quote the RAND 80% / Deloitte 42% / MIT 61% numbers and the program-design choices that mitigate each one (pre-committed measurement, data-foundation-first sequencing, kill criteria, redeployment-not-RIF language).
6. **The financial structure.** Forrester TEI four pillars — Benefits / Costs / Flexibility / Risk — with risk-adjusted NPV, payback, and an explicit sensitivity range on the Benefits pillar (because that's where overclaiming happens).

---

## Open Questions

- **Forrester TEI of Glean specifics** (ROI%, NPV, payback months) require a direct fetch of the PDF before being placed on a slide. The composite-org structure ($13B-rev, 10K-employee, $40/user) is known; the precise multipliers were not extracted in this pass.
- **Big-4 internal AI assistants (Deloitte PairD, EY.ai, PwC ChatPwC, KPMG Workbench/Clara)** publish investment dollars and seat counts but not productivity/ROI numbers. Worth a targeted outreach to peer programs if the brief needs peer benchmarks.
- **APQC named metrics with definitions** from the 2025 KM Benchmarks report — the maturity-model structure is clear, but the specific metric names per level were not extracted. Worth a direct APQC fetch if the framing leans on APQC.
- **JPMorgan 10-20% engineer productivity** — attributed to CIO Lori Beer in public remarks; primary URL not isolated. Pull primary before citing in any final deck.
- **HDI / SDI specific KM metrics** and **Gartner KM Maturity Model stages** were not surfaced (mostly paywalled). Forrester + KCS + APQC cover the same ground for the public-source version of the brief.
- **Channel-switch-corrected deflection methodology** — discussed in practitioner threads but no canonical published spec located. May need to define internally.

---

## Sources (KEEP — credible, within 12-month window unless flagged)

**Analyst / research:**
- McKinsey, *Superagency in the workplace: AI in the workplace 2025* — https://www.mckinsey.com/capabilities/tech-and-ai/our-insights/superagency-in-the-workplace-empowering-people-to-unlock-ais-full-potential-at-work — Jan 2025
- Gartner press release, *HR Research Identifies Four Myths That Are Hampering Employee Productivity* — https://www.gartner.com/en/newsroom/press-releases/2025-03-26-gartner-hr-research-identifies-four-myths-that-are-hampering-employee-productivity — Mar 2025
- Gartner press release, *Top Predictions for IT Organizations and Users in 2025 and Beyond* — https://www.gartner.com/en/newsroom/press-releases/2024-10-22-gartner-unveils-top-predictions-for-it-organizations-and-users-in-2025-and-beyond — Oct 2024
- Gartner press release, *AI Projects in I&O Stall Ahead of Meaningful ROI Returns* — https://www.gartner.com/en/newsroom/press-releases/2026-04-07-gartner-says-artificial-intelligence-projects-in-infrastructure-and-operations-stall-ahead-of-meaningful-roi-returns — Apr 2026
- Deloitte, *Q4 2025 CFO Signals: Tech Transformation Top Priority for 2026* — https://www.deloitte.com/us/en/about/press-room/deloitte-q4-2025-cfo-signals-survey.html — Q4 2025
- Deloitte, *CFO Insights for AI: Cost, Risk, and ROI* — https://www.deloitte.com/us/en/programs/chief-financial-officer/articles/cfo-insights-ai-cost-risk-roi.html — 2025
- Deloitte, *State of AI in the Enterprise (2026 report)* — https://www.deloitte.com/us/en/what-we-do/capabilities/applied-artificial-intelligence/content/state-of-ai-in-the-enterprise.html — 2026
- World Economic Forum, *How CFOs can secure solid ROI from business AI investments* — https://www.weforum.org/stories/2025/10/cost-productivity-gains-cfo-ai-investment/ — Oct 2025
- CFO.com, *So far, few CFOs see substantial ROI from AI spending* — https://www.cfo.com/news/so-far-few-cfos-see-substantial-roi-from-ai-spending-RPG/808249/ — 2025
- BCG, *Executive Perspectives May 2025: Driving Sustainable Cost Advantage with AI* — https://www.bcg.com/assets/2025/executive-perspectives-driving-sustainable-cost-advantage-with-ai-20may.pdf — May 2025
- MIT NANDA, *State of AI in Business 2025* — https://mlq.ai/media/quarterly_decks/v0.1_State_of_AI_in_Business_2025_Report.pdf — 2025
- Menlo Ventures, *2025: The State of Generative AI in the Enterprise* — https://menlovc.com/perspective/2025-the-state-of-generative-ai-in-the-enterprise/ — 2025
- Knowledge at Wharton, *2025 AI Adoption Report* — https://knowledge.wharton.upenn.edu/special-report/2025-ai-adoption-report/ — 2025

**Academic / measurement:**
- Cui et al., *The Effects of Generative AI on High-Skilled Work* (Copilot field experiments at Microsoft + Accenture, MIT working paper) — https://economics.mit.edu/sites/default/files/inline-files/draft_copilot_experiments.pdf — 2024-2025
- MIT GenAI, *The Productivity Effects of Generative AI: Evidence from a Field Experiment with GitHub Copilot* — https://mit-genai.pubpub.org/pub/v5iixksv — 2024
- Microsoft Research (Lee et al.), *The Impact of Generative AI on Critical Thinking: Self-Reported...* — https://www.microsoft.com/en-us/research/wp-content/uploads/2025/01/lee_2025_ai_critical_thinking_survey.pdf — Jan 2025
- Microsoft Research, *New Future of Work Report 2025* — https://www.microsoft.com/en-us/research/wp-content/uploads/2025/12/New-Future-Of-Work-Report-2025.pdf — Dec 2025
- METR, *Measuring the Self-Reported Impact of Early-2026 AI on Technical Worker Productivity* — https://metr.org/blog/2026-05-11-ai-usage-survey/ — May 2026
- International Center for Law & Economics, *AI, Productivity, and Labor Markets: A Review of the Empirical Evidence* — https://laweconcenter.org/resources/ai-productivity-and-labor-markets-a-review-of-the-empirical-evidence/ — 2025
- *The Hawthorne Effect: a randomised, controlled trial* (J Clin Epidemiol, PMC) — https://pmc.ncbi.nlm.nih.gov/articles/PMC1936999/ — 2007 (foundational, classic)
- Oxford CEBM Catalog of Bias, *Hawthorne effect* — https://catalogofbias.org/biases/hawthorne-effect/ — updated 2024

**Frameworks:**
- Consortium for Service Innovation, *AQI is now Content Standard Checklist (KCS v6)* — https://www.serviceinnovation.org/aqi-is-content-standard-checklist/ — KCS v6 era
- Consortium for Service Innovation, *KCS v6 Practices Guide — Content Health Indicators (Technique 5.10)* — https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/040/010/065 — KCS v6
- Consortium for Service Innovation, *KCS v6 Practices Guide — Process Adherence Review (PAR 2.0)* — https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/040/020/060 — PAR 2.0 update Jul 2025
- Consortium for Service Innovation, *Glossary of Measurements (KCS v6)* — https://library.serviceinnovation.org/KCS/KCS_v6/Measurement_Matters_v6/99_Glossary_of_Measurements — KCS v6
- Forrester, *Methodologies: Total Economic Impact* — https://www.forrester.com/policies/tei/ — current
- Forrester, *TEI Methodology For New Technologies* (GenAI applicability) — https://www.forrester.com/blogs/tei-methodology-new-technologies/ — current
- APQC, *Levels of Knowledge Management Maturity* — https://www.apqc.org/resource-library/resource-listing/apqcs-levels-knowledge-management-maturity — current
- APQC, *2025 KM Program Benchmarks and Metrics* — https://www.apqc.org/resource-library/resource-collection/2025-km-program-benchmarks-and-metrics — 2025

**Case studies (vendor / self-reported — flagged as such in body):**
- Forrester, *Total Economic Impact of Microsoft 365 Copilot* — https://tei.forrester.com/go/microsoft/365Copilot/ — 2024-2025
- Microsoft blog, *M365 Copilot drives up to 353% ROI for SMB* (Forrester TEI summary) — https://www.microsoft.com/en-us/microsoft-365/blog/2024/10/17/microsoft-365-copilot-drove-up-to-353-roi-for-small-and-medium-businesses-new-study/ — Oct 2024
- Microsoft blog, *Forrester TEI shows 315% ROI for Microsoft Dynamics 365 Customer Service* — https://www.microsoft.com/en-us/dynamics-365/blog/business-leader/2024/03/27/forrester-tei-study-shows-315-roi-when-modernizing-customer-service-with-microsoft-dynamics-365-customer-service/ — Mar 2024
- Forrester, *Total Economic Impact of Glean* — https://tei.forrester.com/go/Glean/workAIplatform/docs/TheTEIofGlean.pdf — vendor-commissioned
- McKinsey, *Rewiring the way McKinsey works with Lilli* — https://www.mckinsey.com/capabilities/tech-and-ai/how-we-help-clients/rewiring-the-way-mckinsey-works-with-lilli — 2024
- McKinsey, *Meet Lilli: McKinsey's custom-built gen AI platform* — https://www.mckinsey.com/capabilities/tech-and-ai/our-insights/what-mckinsey-learned-while-creating-its-generative-ai-platform — 2024
- ICAEW, *Deloitte launches co-pilot PairD* — https://www.icaew.com/insights/viewpoints-on-the-news/2024/jan-2024/deloitte-launches-copilot-paird — Jan 2024
- Accenture, *GenWizard product page* — https://www.accenture.com/us-en/services/cloud/application-transformation/genwizard — accessed 2026
- Accenture, *Technology Vision 2025 (press release)* — https://newsroom.accenture.com/news/2025/accenture-technology-vision-2025-new-age-of-ai-to-bring-unprecedented-autonomy-to-business — Jan 2025
- OpenAI, *Morgan Stanley case study* — https://openai.com/index/morgan-stanley/ — 2024 (self-reported)

**Foundational / dated (pre-12-month window, kept for canonical role):**
- McKinsey, *The economic potential of generative AI: The next productivity frontier* — https://www.mckinsey.com/capabilities/tech-and-ai/our-insights/the-economic-potential-of-generative-ai-the-next-productivity-frontier — Jun 2023
- Dell'Acqua et al. (HBS/BCG), *Navigating the Jagged Technological Frontier* — https://www.hbs.edu/faculty/Pages/item.aspx?num=64700 — Sept 2023

---

## Excluded Sources (audit trail)

The following surfaced in searches but were dropped from the brief for cause:

- **digitaldefynd.com, klover.ai, aiexpert.network, ctomagazine.com, illuminateai.co.uk, reruption.com, makebot.ai, businessmodelcanvastemplate.com, consulting-huber.com, plusai.com, futureofconsulting.ai, roadtooffer.com, scrumlaunch.com, freshworks.com (blog), aigovernancetoday.com, pertamapartners.com, terminal-x.ai, beam.ai, folio3.ai, valuebound.com, sranalytics.io, fullstack.com, trantorinc.com, dextralabs.com, joelcomm.com, techclass.com, vassardigital.ai, encodedots, damcogroup, houseblend.io, sequencr.ai, statsig.com (blog), aimagicx, FunBlocks, Oreate, Document360 blog, Pylon blog, Higher Logic blog, Larridin, UC Today, Worklytics, Rudi Kershaw, BusinessWire/ResearchAndMarkets press releases, Spotsaas, Ariglad, ServiceTarget** — SEO content farms, vendor marketing blogs, or unattributed AI-generated listicles. None offered unique primary data; numeric claims in them all traced to one of the KEEP-tier sources above.
- **BCG "AI at Work 2025" 1.5 hr/day per employee figure** — only available via a LinkedIn third-party summary; the primary BCG PDF was not pulled. Dropped pending direct fetch.
- **BCG Deckster "~40% weekly associate use"** — sourced only to consulting-huber.com / plusai.com SEO blogs; not corroborated by a BCG primary source. Dropped.
- **Morgan Stanley "21% of S&P 500 cite measurable AI benefit"** — surfaced only in aigovernancetoday.com derivative blog; not traceable to MS Research primary. Dropped.
- **Klarna Feb 2024 headline numbers** — kept in the brief but presented as a cautionary "initial month, since walked back" rather than a benchmark.

The exclusions above are why the brief reads conservatively. Boards will respect a number that survives audit more than one that doesn't.
