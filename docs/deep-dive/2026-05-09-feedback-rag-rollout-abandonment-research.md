# Deep Dive: Feedback-Driven Iterative Rollout of an Internal RAG Knowledge Base — Is the "Abandonment After Bad First Impression" Worry Real?

**Date:** 2026-05-09
**Recency window applied:** 3 months as primary (per AI/RAG topic class), with explicit fallback to 12 months for organizational practice claims and 3 years for foundational academic work where no fresher source exists. Each citation labeled with publication date.

**Recency caveat:** A targeted 3-month follow-up search (Feb–May 2026) surfaced one materially new primary source (Recon Analytics "AI Choice 2026") that directly addresses the abandonment worry, plus three updates (Atlassian Team '26 May 2026 disclosures, VentureBeat Q1 2026 "retrieval rebuild" data, Klarna IPO context). Notable absence: no new MIT NANDA follow-up, no new trust-repair empirical research, and no fresh Morgan Stanley cohort data — those citations remain 9–18 months old. Conclusions weighted toward the 2026 evidence where it exists.

## Executive Summary

The worry is real and well-documented in the academic literature **and now in 2026 enterprise cohort data** — Recon Analytics' January 2026 study of 150,000+ enterprise users found Copilot accuracy NPS persistently negative (-3.5 in July 2025 → -24.1 in September 2025 → -19.8 in January 2026, a partial recovery that did not return to neutral) and **44.2% of lapsed Copilot users cite distrust of answers as the primary reason they stopped using it**. When users have choice between Copilot and ChatGPT, 76% pick ChatGPT; in three-way environments Copilot's share collapses to 8%. This is the strongest empirical evidence yet that early-experience trust damage in internal AI tools translates to durable abandonment.

The older academic findings still apply — early errors produce **asymmetric, hard-to-repair trust damage** (algorithm-aversion research from Dietvorst 2015; ACM 2024 "Trust Recovery Journey"; PMC October 2025). MIT NANDA's August 2025 finding that 95% of enterprise GenAI pilots fail to deliver measurable ROI is consistent with this pattern, and Klarna's 2025 partial reversal of its AI-first customer support (now stabilized in a hybrid model post-2025 IPO) is the most public single-org cautionary tale.

But the choice is not "iterate and risk abandonment" vs. "delay launch until perfect." The pattern that actually wins is **gated iterative rollout**: a narrow first cohort, evaluation rigor before expansion, citations + calibrated abstention as default behavior, and expectation-setting via beta labeling. Morgan Stanley (6-month internal eval before broad advisor rollout, 98%+ adoption), LinkedIn (measured MRR +77.6% and -28.6% resolution time before scaling), Ramp (shadow mode until accuracy thresholds cleared), and Glean's customer base (monthly retrains driven by citation-click and thumbs feedback) all combine evaluation discipline with limited initial exposure.

The two failure patterns that actually destroy adoption are (a) **iterate-in-production with no quality gates and broad exposure** (Klarna) and (b) **forced rollout that overrides user/admin opt-in** (Atlassian Rovo's auto-activation backlash) — even when the underlying tool is technically capable.

Recommended posture for the question asked: ship iteratively, but gate the iteration. Specifically — narrow initial cohort, beta label, citations + "I don't know" by default, weekly triage of feedback, expand only when measurable quality gates clear.

## Findings

### 1. Reported experience: the adoption curve has a predictable shape

Across LinkedIn (SIGIR 2024 paper, arXiv 2404.17723), Klarna (OpenAI case study Feb 2024; PromptLayer recap 2025), and the ~100 teams kapa.ai aggregated lessons from (kapa.ai blog, 2024), the pattern is consistent:

1. **Sharp early-usage spike** driven by novelty and leadership push.
2. **Trust dip** when users hit hallucinations, stale data, or wrong-document retrieval.
3. **Either recovery** (rerankers, citations, freshness pipelines, feedback capture, fine-tuned embeddings on company language) **or quiet abandonment** (Klarna's AI-first reversal is the public example).

Quantified outcomes when teams executed well:
- LinkedIn customer-service RAG: **MRR +77.6% over vanilla RAG baseline; median per-issue resolution time -28.6%**, after ~6 months in production with their own engineers (arXiv 2404.17723).
- Klarna's customer assistant (reported Feb 2024 via OpenAI): 2.3M conversations in first month, ~700 FTE-equivalent, average resolution 11 min → 2 min. *Caveat:* CEO Sebastian Siemiatkowski publicly admitted "lower quality" in 2025 and the company moved to a hybrid model with human agents (PromptLayer, 2025).
- Klarna internal "Kiki" assistant (2024 reporting): ~2,000 employee questions/day, 85%+ daily-usage adoption in Comms / Marketing / Legal.
- Glean (Jason Liu interview, March 2025): roughly **20% search-quality improvement after six months** of continuous learning from query-click pairs and thumbs feedback.

### 2. Common problems with the feedback-iteration approach

Documented across MIT NANDA's "State of AI in Business 2025" (Aug 2025; reported by Fortune), the OpenAI hallucination paper (arXiv 2509.04664, Sept 2025), Glean's engineering posts, kapa.ai's 100-team aggregation, and the academic trust literature:

- **Feedback signal is sparse.** Explicit thumbs feedback occurs in roughly **<1% of interactions** (Nebuly, 2024). Iteration starves without enough data points unless implicit signals (citation clicks, query reformulations, abandonment) are also instrumented.
- **Feedback is biased toward frustrated users.** Satisfied users rarely click thumbs-up; the explicit channel skews negative and noisy.
- **Context fragmentation in chunked retrieval.** Conditional clauses ("if transaction exceeds €10M") get separated from their predicate, producing dangerous answers in regulated domains (Zeta-Alpha; Faktion).
- **"Garbage in" / corpus coverage gaps that produce hallucinations.** When a query touches knowledge not indexed, the model still answers — and users can't tell which answers are grounded. Trust erosion accelerates from there.
- **Stale data.** Indexes lag the canonical source; high-value users abandon after catching one wrong answer in their domain.
- **Brittle workflows / day-to-day misalignment.** MIT NANDA's primary attribution for the 95% failure rate: tools built for demo scenarios, not embedded in actual user workflows.
- **No standardized evaluation framework.** Generic eval suites (RAGAS, etc.) don't measure integrated systems combining retrieval reweighting + reranker training + embedding fine-tuning + generation policy. Teams iterate without a defensible scoring rubric.
- **Calibration penalty in pretraining.** OpenAI's Sept 2025 hallucination paper argues benchmarks reward confident answers and punish "I don't know," so models are trained against calibration — making "controlled deflection" an explicit choice the deployer must enforce.
- **Forced rollout backlash.** Atlassian Rovo's auto-activation across cloud instances with no admin opt-out drove sustained community pushback (Atlassian Community forums) — even with capable underlying tech. *2026 update:* By Atlassian Team '26 (May 6, 2026), Atlassian disclosed Rovo at 5M+ MAU and 90%+ enterprise-cloud-customer penetration, suggesting the underlying tool recovered after the rollout-mechanics backlash settled (vendor self-report — hedge). The lesson stands: even successful recovery cost Atlassian months of reputational and admin-trust friction that gated cohort rollout would have avoided.

### 3. Yes — your specific worry is well-evidenced (and now has 2026 enterprise cohort data)

**Newest and strongest evidence (Jan 2026 cohort, published 2026): Recon Analytics — "AI Choice 2026: Why Licenses Don't Equal Adoption."** Survey of 150,000+ enterprise users between July 2025 and January 2026:

- Copilot accuracy NPS: **-3.5 (Jul 2025) → -24.1 (Sep 2025) → -19.8 (Jan 2026)** — persistently negative, partial recovery that did not return to neutral.
- **44.2% of lapsed Copilot users cite "distrust of answers" as the primary reason for stopping use.** This is the closest empirical answer in the public record to the question "do users abandon after a bad experience?"
- When users have access to both Copilot and ChatGPT, **76% choose ChatGPT, 18% choose Copilot.**
- When all three (Copilot, ChatGPT, Gemini) are available, Copilot share collapses to **8%.**
- In Copilot-only environments (forced rollout), 68% adoption — but the cross-environment evidence shows that adoption disappears the moment users have an alternative.
- Paid AI subscriber market share (Jan 2026): ChatGPT 55.2%, Gemini 15.7%, Copilot 11.5%.

This is enterprise-scale empirical confirmation of the worry. The forced-rollout adoption number (68%) is also instructive — it tracks the Atlassian Rovo pattern and shows that "adoption" measured under captive conditions overstates real preference.

**The older academic literature established the mechanism: algorithm aversion with asymmetric repair cost.**

- **Foundational result:** Dietvorst, Simmons & Massey (Wharton, 2015, *Journal of Experimental Psychology: General*) — people lose confidence in algorithms more quickly than in humans after seeing them err, even when the algorithm objectively outperforms the human.
- **Timing matters:** ACM 2024 "Trust Recovery Journey" — errors occurring **early** in a session produce sharper, more persistent declines in trust than the same errors later, and trust recovery is materially harder when the first impression is negative.
- **Asymmetric repair cost:** PMC 2025 "Trust Formation, Error Impact, and Repair in Human–AI Financial Advisory" — positive first impressions raise trust more efficiently than later trust-repair efforts can rebuild it after a negative one. Frontiers Psychology 2024 and Nature HSSC 2024 reviews synthesize the same conclusion.
- **Accuracy disclosure / observed accuracy shapes downstream reliance:** Taylor & Francis 2022 and 2025 — including non-return after a poor first encounter.
- **Macro signal (Apr 2026):** Fortune — **>54% of workers bypassed their company's AI tools in the prior 30 days**; ~80% either avoid or reject employer-deployed AI. The number conflates "never tried" with "tried and quit," but is directionally consistent with the Recon Analytics churn pattern above.
- **Q1 2026 RAG state-of-play:** VentureBeat reported that enterprise RAG response correctness, retrieval accuracy, and answer relevance converged at ~53.3% by March 2026; intent to adopt hybrid retrieval tripled from 10.3% to 33.3% in one quarter; 22.2% of qualified respondents reported no production RAG by March 2026 (up from 8.6% in January 2026). The directional shift: enterprises are now **rebuilding** RAG pipelines, not just adding more — consistent with the trust-erosion-then-rework pattern.
- **Historical durability:** Microsoft Clippy is the textbook case — intrusive, low-quality first impression created brand stigma persisting **decades**. Reviewers still invoke Clippy when Copilot misbehaves (Tom's Hardware retrospective).

What the literature does **not** directly answer: cohort-return rates of internal users after a meaningful product upgrade. That precise measurement appears to be a known gap in the published research — companies that pull off recoveries don't typically publish before/after cohort retention.

### 4. What worked (mitigations) and the non-iterative alternative

#### Validated mitigation pattern: gated iterative rollout

The successful named-deployment cases all combine evaluation rigor with **narrow initial exposure**, not zero-user delay:

- **Narrow first cohort + measurable evals before expansion.** Microsoft Azure AI Foundry deployment guidance recommends starting with low-risk pilots (help-desk triage, internal summarization) and measuring hallucination/error rates before broader rollout.
- **Dogfood with a curated internal eval set.** Atlassian's Rovo Chat team built a hybrid-LLM eval set seeded from ~241 hand-curated employee queries, expanded to ~100K training/eval pairs via LLM (Atlassian Engineering blog). Model swaps gated on regression against real internal questions.
- **Calibrated abstention as a first-class behavior.** OpenAI's hallucination paper (Sept 2025) argues for explicit confidence thresholds and rewarding "I don't know." Glean and kapa.ai both ship confidence-aware "I don't know" responses by default.
- **Citations / "show sources" as default UI.** Across Glean, kapa.ai, and Microsoft Copilot guidance, inline citations are non-negotiable — they convert "looks wrong" moments into "let me check the source" moments rather than abandonment events.
- **Continuous evaluation from day 1.** kapa.ai's 100-team aggregation singles this out as the dividing line: evals seeded from real user queries, citation-click signals, and thumbs feedback feeding monthly retrains.
- **Fine-tune embeddings on company language.** Glean's pipeline (continued pretraining on the customer corpus + fine-tunes on click data) directly addresses the failure mode where generic embeddings miss internal jargon and produce visibly-bad early answers.
- **Confidence thresholds + escalation paths.** Azure AI Foundry recommends thresholds that force human review for low-confidence outputs, with logging of every escalation.
- **Real opt-in, real beta labeling.** The Atlassian Rovo forced-rollout backlash is the cautionary control — even good tech gets judged broken when expectation-setting and gating are stripped away.

#### The "non-iterative" alternative is mostly a hybrid

True "private beta for many months with zero users" is rare in published case studies. The closest matches are:

- **Morgan Stanley** announced its OpenAI partnership in **March 2023** but did not roll out the AI @ Morgan Stanley Assistant to advisors until **September 2023** — a **~6-month internal evaluation window** (Morgan Stanley press release; CNBC, June 2024). Built "a robust evaluation framework" with internal datasets for different meeting types before exposure (OpenAI Morgan Stanley case study). Outcome: **98%+ advisor-team adoption** of the Assistant after launch. *Caveat:* still ran a ~600-advisor pilot, so it's a hybrid eval-first + gated cohort approach, not zero-user delay.
- **Ramp** runs new agents in **shadow mode** on real customer transactions — agent decides what it would do, humans still execute — and only enables live actions once shadow accuracy crosses internal thresholds (LangChain case study; ZenML LLMOps database). Ramp self-reports 99% policy-enforcement accuracy and 15× more out-of-policy spend caught (self-reported, hedge accordingly).
- **LinkedIn** measured MRR and resolution-time improvements before scaling beyond their initial customer-service team.

The general industry pattern surfaced in vendor write-ups (treat as convention, not primary evidence): **shadow mode → gradual autonomy / human-in-the-loop → full deployment**, gated by per-stage accuracy thresholds.

#### Direct comparison data is thin

No controlled head-to-head comparison (same org, same use case, delayed-rollout arm vs. iterative arm) exists in public literature. Cross-company comparisons are confounded by domain, scale, and incentive differences. The directional signal is consistent — **eval-first + gated cohort beats unconstrained iterate-in-production** — but it isn't a randomized controlled finding.

### 5. Synthesis: which approach pattern best addresses the abandonment worry

For an internal RAG knowledge base where the first brain is worried about persistent negative perception:

**Reject:** "Ship to everyone day-1 and iterate" (Klarna's pattern). High blast radius for early errors that algorithm-aversion research shows do disproportionate trust damage.

**Reject:** "Hold back launch for 12+ months until perfect." Selection bias hides this in case studies, but the cost is high — no real signal until launch, and the corpus/usage pattern you optimized for in private may not match what real users do.

**Recommended:** **Gated iterative rollout** — the pattern Morgan Stanley, LinkedIn, Ramp, and Glean's well-executed customer rollouts share. Concretely:

1. **Cohort 0 — internal dogfooding** with a curated eval set (Atlassian Rovo's ~241-query seed is a model). Don't expose anyone outside the build team until baseline accuracy clears a written threshold.
2. **Cohort 1 — design partners / champion users** opt-in, beta-labeled, with a direct feedback channel. Set explicit expectations: "this is preview, please flag wrong answers." Algorithm-aversion research suggests that pre-disclosure of accuracy moderates the trust collapse from observed errors.
3. **Default-on safety behaviors** before any cohort touches it: inline citations, calibrated "I don't know" / abstention, confidence-tied escalation to human or to a search fallback, freshness indicators on retrieved docs.
4. **Instrument both explicit and implicit feedback** from day 1: thumbs + reason picker, citation clicks, query reformulations, abandonment, dwell time. Don't depend on the <1% explicit-thumbs signal alone.
5. **Quality gates for cohort expansion** — written before launch — that combine accuracy, citation-click rate, abstention rate, and qualitative feedback. Don't expand to the next cohort until gates clear.
6. **Weekly triage of downvoted examples** into a regression eval set; route "wrong source" / "outdated" tags to content owners; monthly embedding retrains using accumulated click data (Glean's cadence).
7. **Avoid forced/automatic activation** on the broader org — Atlassian Rovo's backlash is the control case showing this destroys trust independent of quality.

The asymmetric trust-repair finding means the cost of letting a bad first impression out into the broader org is real and lasting — but the answer is to control the *blast radius* of iteration, not to refuse to iterate. A six-week gated rollout to 30 design partners with the safety behaviors above is materially safer than either Klarna's day-1-broad-launch or a year of private beta.

## Open Questions

- **Cohort-return rates after relaunch** are still not directly measured in the published literature. Recon Analytics' January 2026 data captures *churn* (44.2% of lapsers cite distrust) but not whether those lapsers later returned after Copilot improvements. The HCI trust-repair research establishes asymmetric repair cost in lab settings; whether enterprise users actually return after a quality upgrade remains an open measurement gap.
- **Why the Atlassian Rovo recovery happened** — the May 2026 Atlassian disclosures show 5M MAU and 90% enterprise penetration, which is at odds with a "forced-rollout backlash kills adoption" thesis. Possible explanations: backlash was vocal but not representative, captive-environment adoption (no alternative tool), or product recovery paired with admin-controls fixes. Not resolvable from the available sources.
- **Ship-gate thresholds** ("we required X% accuracy before launch") are mostly absent from primary sources — companies disclose the framework but not the numbers. Anyone publishing concrete thresholds is doing so as vendor advocacy.
- **Selection bias toward success stories.** The teams that delayed for many months and then quietly abandoned the project don't publish about it. The dataset of public case studies overstates the success rate of any approach.
- **Champion-users / design-partner programs with quantified adoption uplift** are advocated but not numerically validated in the sources surfaced — recommendation is convention-grade, not RCT-grade.
- **Microsoft Copilot retention/abandonment cohort data** is not publicly available; third-party enterprise survey detail (Gartner, Forrester) wasn't surfaced in this search.

## Sources (KEEP, with publication dates)

**Within 3-month window (Feb–May 2026) — strongest sources for the abandonment question**
- AI Choice 2026: Why Licenses Don't Equal Adoption (Recon Analytics, 2026, data through Jan 2026) — https://www.reconanalytics.com/ai-choice-2026-why-licenses-dont-equal-adoption/
- Atlassian Team '26: Rovo agentic execution announcement (Atlassian, May 2026) — https://www.atlassian.com/blog/company-news/rovo-team-26
- Atlassian opens Teamwork Graph at Team '26 (SiliconANGLE, May 6, 2026) — https://siliconangle.com/2026/05/06/atlassian-opens-teamwork-graph-pushes-rovo-agentic-execution-team-26/
- The Retrieval Rebuild: Why Hybrid Retrieval Intent Tripled (VentureBeat, Q1 2026) — https://venturebeat.com/data/the-retrieval-rebuild-why-hybrid-retrieval-intent-tripled-as-enterprise-rag-programs-hit-the-scale-wall
- Most workers rejecting AI (Fortune, Apr 16, 2026) — https://fortune.com/2026/04/16/ai-resistance-running-out-of-time-rebellion-quiet-quitting-trust/
- Atlassian Q3 FY 2026 Earnings (Futurum Group, 2026) — https://futurumgroup.com/insights/atlassian-q3-fy-2026-earnings-show-continued-cloud-and-ai-led-expansion/

**Primary research / first-party engineering (older but still authoritative)**
- Retrieval-Augmented Generation with Knowledge Graphs for Customer Service Question Answering (LinkedIn, SIGIR 2024) — https://arxiv.org/abs/2404.17723
- Why Language Models Hallucinate (Kalai, Nachum et al., OpenAI, Sept 2025) — https://arxiv.org/html/2509.04664v1
- Klarna's AI assistant does the work of 700 full-time agents (OpenAI, Feb 2024) — https://openai.com/index/klarna/
- Morgan Stanley uses AI evals to shape the future of financial services (OpenAI) — https://openai.com/index/morgan-stanley/
- Launch of AI @ Morgan Stanley Debrief (Morgan Stanley press release) — https://www.morganstanley.com/press-releases/ai-at-morgan-stanley-debrief-launch
- Key Milestone in Innovation Journey with OpenAI (Morgan Stanley press release) — https://www.morganstanley.com/press-releases/key-milestone-in-innovation-journey-with-openai
- Learning lessons from building an enterprise AI assistant (Glean blog) — https://www.glean.com/blog/how-to-build-an-ai-assistant-for-the-enterprise
- The definitive guide to AI-based enterprise search for 2025 (Glean) — https://www.glean.com/blog/the-definitive-guide-to-ai-based-enterprise-search-for-2025
- Fine-Tuning Embedding Models for Enterprise RAG: Lessons from Glean (Jason Liu, March 2025) — https://jxnl.co/writing/2025/03/06/fine-tuning-embedding-models-for-enterprise-rag-lessons-from-glean/
- Enhancing Rovo Chat with Hybrid LLM Approach (Atlassian Engineering) — https://www.atlassian.com/blog/atlassian-engineering/hybrid-llm
- Why Does Atlassian Need to Rethink the Forced Rollout Strategy for Rovo AI? (Atlassian Community) — https://community.atlassian.com/forums/Rovo-articles/Why-Does-Atlassian-Need-to-Rethink-the-Forced-Rollout-Strategy/ba-p/3066231
- Best Practices for Mitigating Hallucinations in LLMs (Microsoft Azure AI Foundry blog) — https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/best-practices-for-mitigating-hallucinations-in-large-language-models-llms/4403129
- Microsoft Ignite 2025: Copilot and agents built to power the Frontier Firm (Microsoft 365 blog, Nov 2025) — https://www.microsoft.com/en-us/microsoft-365/blog/2025/11/18/microsoft-ignite-2025-copilot-and-agents-built-to-power-the-frontier-firm/

**Industry data and named aggregations**
- MIT report: 95% of generative AI pilots failing (Fortune, Aug 18, 2025) — https://fortune.com/2025/08/18/mit-report-95-percent-generative-ai-pilots-at-companies-failing-cfo/
- Most workers rejecting AI (Fortune, Apr 16, 2026) — https://fortune.com/2026/04/16/ai-resistance-running-out-of-time-rebellion-quiet-quitting-trust/
- Klarna Customer Service: From AI-First to Human-Hybrid Balance (PromptLayer, 2025) — https://blog.promptlayer.com/klarna-customer-service-from-ai-first-to-human-hybrid-balance/
- RAG Best Practices: Lessons from 100+ Technical Teams (kapa.ai, 2024) — https://www.kapa.ai/blog/rag-best-practices
- Common Challenges with Enterprise RAG (Zeta-Alpha) — https://www.zeta-alpha.com/post/why-genai-pilots-fail-common-challenges-with-enterprise-rag
- Common Failure Modes of RAG (Faktion) — https://www.faktion.com/post/common-failure-modes-of-rag-how-to-fix-them-for-enterprise-use-cases
- LLM Feedback Loop (Nebuly) — https://www.nebuly.com/blog/llm-feedback-loop
- Morgan Stanley wealth advisors are about to get an OpenAI-powered assistant (CNBC, June 2024) — https://www.cnbc.com/2024/06/26/morgan-stanley-openai-powered-assistant-for-wealth-advisors.html
- AI on the trading floor: Morgan Stanley expands OpenAI-powered chatbot (CNBC, Oct 2024) — https://www.cnbc.com/2024/10/23/morgan-stanley-rolls-out-openai-powered-chatbot-for-wall-street-division.html
- Ramp: AI Agent for Automated Merchant Classification (ZenML LLMOps Database) — https://www.zenml.io/llmops-database/ai-agent-for-automated-merchant-classification-and-transaction-matching
- AI Agent Case Study: Ramp's Tour Guide for Financial Ops (LangChain) — https://www.langchain.com/breakoutagents/ramp

**Academic trust / algorithm-aversion literature**
- The Trust Recovery Journey: The Effect of Timing of Errors on the Willingness to Follow AI Advice (ACM, 2024) — https://dl.acm.org/doi/fullHtml/10.1145/3640543.3645167
- Trust Formation, Error Impact, and Repair in Human–AI Financial Advisory (PMC, 2025) — https://pmc.ncbi.nlm.nih.gov/articles/PMC12561693/
- Developing trustworthy AI (Frontiers in Psychology, 2024) — https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2024.1382693/full
- Trust in AI: progress, challenges, and future directions (Nature HSSC, 2024) — https://www.nature.com/articles/s41599-024-04044-8
- Algorithm aversion? On the influence of advice accuracy (T&F, 2022) — https://www.tandfonline.com/doi/full/10.1080/12460125.2022.2070951
- Algorithm appreciation or aversion (T&F, 2025) — https://www.tandfonline.com/doi/full/10.1080/0144929X.2025.2535732
- A Systematic Literature Review of User Trust in AI-Enabled Systems (T&F) — https://www.tandfonline.com/doi/full/10.1080/10447318.2022.2138826

**Historical retrospective**
- Clippy retired 25 years ago today (Tom's Hardware) — https://www.tomshardware.com/software/windows/clippy-microsofts-hapless-office-assistant-was-retired-25-years-ago-today-its-irritating-spirit-lives-on-in-100-copilots

## Excluded Sources

- **Dextralabs, Fram, Intelliarts, TechTez** (Production RAG / Enterprise RAG vendor blogs) — WEAK: vendor SEO without primary attribution. Patterns they describe are echoed in stronger first-party sources, so framing was retained without citation.
- **Brightlume, Cobbai, Hokstad Consulting** (shadow-mode rollout blogs) — WEAK: vendor SEO. Shadow-mode pattern documented from Ramp + LangChain primary sources.
- **Strella** (user abandonment listicle) — WEAK: self-flagged in subagent output as weak source.
- **Klarna recap on Nate's Newsletter** — WEAK: opinion / Substack commentary; Klarna reversal is supported by PromptLayer (more grounded recap) and was widely reported in mainstream press.
- **AIX, Reruption, ctomagazine, emerj, aimodels.fyi** — WEAK: secondary aggregators without independent reporting; superseded by primary sources.
- **Analytics Vidhya, Binariks, AI Accelerator Institute** (RAG failure rate posts) — WEAK: their cited "80% RAG project failure" / "30% reach production" stats lack a citable primary source; MIT NANDA via Fortune used as the primary failure-rate citation instead.
- **Towards Data Science article** on enterprise RAG — WEAK: contributor-blog quality; framings echoed in primary sources.
- **InfoQ LinkedIn Hiring Assistant talk listing** — UNVERIFIED: only the listing was retrieved, not the transcript; LinkedIn deployment claims supported instead from arXiv 2404.17723.
- **Machine Learning Plus, RAIS journal** — UNVERIFIED relative to the specific feedback-loop claims; superseded by OpenAI hallucination paper for the calibration argument.
