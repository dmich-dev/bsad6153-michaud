# 4.3 Implementation Brief: Should This Use AI?

David Michaud | AI Implementations | Module 4 | November 18, 2026

AI-use note: Hermes Agent assisted with source research, drafting and document checks. Final judgments and review remain my responsibility.

## Your workflow

I choose AI models daily for coding and homelab automation. My M1 log documents a preference for Sol in Hermes because of cost and compatibility. The project notes flag stale model information and stalled agent runs as problems. The log does not capture the full comparison process, what sources I checked, or how long the decision took. There is no measured M1 baseline (Project records, 2026).

## Should this use AI?

A. No new technology: Keep my existing workflow and add a model-selection checklist to my notes. This costs no new subscription, but still requires manual checking; stale information and unmeasured time remain risks.

B. Data without AI: Use saved SQL and a dashboard to compare advertised price, context and tool metadata. Cash cost is $0 within the planned free allowances, plus unmeasured maintenance. Incomplete endpoints, aliases or misunderstood units can still produce misleading comparisons.

C. LLM chatbot/agent: In Milestones 5–6, translate a task description into approved filters and explain returned SQL results. The budget below is $1.05–$2.10/month for inference, plus development and review time. Hallucinations, private prompts and repeated calls are added risks.

Start with B. SQL and Python can handle joins, filters, arithmetic and freshness checks without a language model. Test C only for requests that are hard to express as filters or for explanations of SQL results. Neither approach can establish coding quality or Hermes compatibility from catalog claims alone; that takes a real task test.

## Value hypothesis

Target: cut median elapsed selection time by 20% without lowering the rate of correct selections. Starting in M4, use the usage log to establish the missing baseline: time from opening the first source to committing to a model, and note interruptions separately. Then time comparable decisions with the dashboard. For each task, define the budget and required capabilities up front. Keep failed decisions in the results and compare both median time and pass rate. Test C against B, not just against the original workflow.

## Early cost estimate

Rates checked November 18: 10 questions/day for 30 days, one call each with 2,000 input and 300 billable output tokens. At standard rates per million input/output tokens, OpenAI GPT-6.1 Terra ($1/$5) costs $0.0035/question or $1.05/month; Anthropic Claude Sonnet 5.5 ($2/$10) costs $0.007/question or $2.10/month (Anthropic, n.d.; OpenAI, n.d.-a). These are alternative budgets for direct global APIs, without caching, batch discounts, paid tools or tax. In M5 I will replace the estimates with measured cost per successful answer, including retry costs.

Supabase Free, standard public GitHub Actions and Render Free add $0 within their allowances; Render sleeps after 15 idle minutes. Quotas, overages and account settings need checking, and labor is unpriced. Thus the modeled monthly cash total is $1.05–$2.10, not a guaranteed bill (Supabase, n.d.; GitHub, n.d.; Render, n.d.). App API billing is separate from ChatGPT Plus (OpenAI, n.d.-b).

Before M5, the plan is to fund a dedicated API account with at most $20 and leave auto-reload off. Provider cutoff can lag (OpenAI, n.d.-c), so the app would decline any call that takes settled charges, pending charges and the new call's maximum cost above $18. Record that reservation before sending; keep uncertain charges reserved. Limit each call to 4,000 input and 1,000 billable output tokens and allow at most two calls per question. If the cost cannot be verified or the next call would exceed the limit, return SQL results only.

## Risks and governance

Wrong prices could cost visitors money, and a bad recommendation could break a bot workflow. Show the source, timestamp and pricing units; flag data older than 24 hours and distinguish advertised features from tested ones. The public site stays SQL-only. Only the owner can use C or disable it after an incident. Prompts and access logs may identify people, so reject secrets, do not retain raw prompts and delete diagnostics after 30 days. Treat catalog text as untrusted. The app's model must not buy credit, change plans, execute commands, alter project data, reveal credentials or publish anything. Check redistribution rights before displaying catalog data publicly.

## Scorecard self-assessment (version 1)

Real user and workflow: Yellow; daily use is documented, but timed steps are missing.
Data access: Yellow; loading was verified, but continuing access and display rights need review.
Data understanding: Yellow; aliases, nulls and endpoint coverage can mislead.
Freshness and monitoring: Red; retained M3 proof is local, not an operational hosted schedule.
Grounding: Yellow; SQL references exist, but chatbot answers are unevaluated.
Bounded autonomy: Yellow; application permissions and spending controls are still proposals.
Evaluation: Red; authentic question provenance and student-reviewed results remain incomplete.
Measured value and cost: Red; neither selection savings nor app charges are measured.
Adoption: Red; no website usage or classmate test is documented in this packet.
Governance and accountability: Yellow; ownership and incident rules have not been exercised.

The weakest areas are Evaluation and Measured value and cost. For evaluation, use real logged questions to build an answer key from SQL, including cases where there is not enough evidence to recommend a model. For value and cost, collect M4 times and outcomes, then reconcile actual M5 charges. Keep the SQL-only dashboard if C does not improve decisions enough to justify its cost.

## References

Anthropic. (n.d.). [Claude API pricing](https://platform.claude.com/docs/en/about-claude/pricing).
OpenAI. (n.d.-a). [API pricing](https://developers.openai.com/api/docs/pricing.md).
OpenAI. (n.d.-b). [What is ChatGPT Plus?](https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus).
OpenAI. (n.d.-c). [Prepaid API billing](https://help.openai.com/en/articles/8264644-setting-up-and-managing-prepaid-api-billing).
Supabase. (n.d.). [Pricing](https://supabase.com/pricing).
GitHub. (n.d.). [Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions).
Render. (n.d.). [Deploy for Free](https://render.com/docs/free).
Project records. (2026). Baseline log and retained M2/M3 review evidence.
