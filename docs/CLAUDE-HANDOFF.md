# Chatbotator — handoff to Claude

Prepared 26 October 2026. Read this alongside `PLAN.md`, `README.md`, `docs/FIRST-LOOK.md`, and the actual source. This is a continuation of an existing learning project, not a request to generate the finished application.

## Purpose and background

Martin Petyrek is a senior engineer with 13+ years of experience, deep React/TypeScript and frontend architecture experience, technical ownership at PwC, and experience on the frontend team that built Tinder Online. He has used Cursor and Claude Code extensively, including their agentic development capabilities. He has not built a custom coding-agent harness and wants practical experience building AI applications himself.

The wider aim is to strengthen his applied AI engineering skills and eventually support credible CV/interview claims with demonstrable work. Do not present planned capabilities as existing experience, or describe this personal project as production employment experience.

We initially considered a coding-agent harness, but narrowed the first project to a more broadly useful business application: a customer-support assistant for a fictional online store. A coding-agent harness is deferred. The authoritative current roadmap is this repository's `PLAN.md`.

## What we are building

**Chatbotator**, embedded in **TrailSupply**, a fictional outdoor equipment store.

The complete bounded workflow is:

1. Answer questions about the store's own documents, with supporting citations and appropriate clarification or abstention.
2. Retrieve the current customer's order data through validated, authorized tools.
3. Check business rules in application code and propose a refund without executing it.
4. Obtain explicit confirmation of a specific proposal, then execute a simulated refund reliably.
5. Evaluate quality and action correctness, inspect failures, and compare quality/latency/cost.

A policy chatbot and an assistant issuing refunds are deliberately separate stages. The latter needs authorization, application-owned rules, confirmation, persistence, transactions, idempotency, recovery, and audit records.

This is a local learning application with synthetic data and simulated refunds. We are not building a real checkout or processing money. The goal is hands-on familiarity with the core concepts quickly, not an enterprise-complete platform.

## Critical collaboration agreement

**Martin implements the core AI and business modules himself.** The assistant builds the surrounding foundation and acts as a coach, reviewer, and debugging partner.

Assistant-owned setup already includes workspace configuration, development scripts, storefront styling, chat shell, backend skeleton, draft documents, fixtures, and onboarding documentation. Further routine setup or UI polish can be delegated when useful.

Martin-owned learning work includes:

- Model API integration, prompting, conversation state, and error handling.
- Document ingestion, chunking, retrieval, grounding, and citations.
- Tool schemas, runtime validation, dispatch, and the model/tool loop.
- Server-owned customer identity, authorization, and deterministic eligibility rules.
- Proposals, confirmation, persistence, transactions, idempotency, and recovery.
- Evaluation cases, graders, failure analysis, traces, usage, and cost measurement.

Work in small exercises: explain the concept and acceptance criteria, let Martin implement, review his work, offer hints/debugging, and have him explain and correct it. Do not silently complete the core learning modules or replace his attempt with a finished solution. Keep framework count and abstractions low. Do not turn this into a multi-agent or custom harness project before the agreed milestones work.

## Repository and Git state

- Local repository: `/Users/mp/w/chatbotator`
- Remote: `https://github.com/petyrek/chatbotator.git`
- Branch: `main`, tracking `origin/main`.
- Initial plan commit already pushed: `a8d9779 docs: add AI engineering learning plan`.

**Important: the application scaffold is currently local, untracked, uncommitted, and unpushed.** A fresh clone currently contains the committed plan, not the application described below. Preserve the local files. Review `git status` before changes. Do not reset/clean the checkout or overwrite existing work. This handoff is also a new local file.

At handoff, the untracked paths are `.env.example`, `.gitignore`, `.nvmrc`, `README.md`, `apps/`, `data/`, `docs/`, `evals/`, `package-lock.json`, `package.json`, and `scripts/`.

No implementation commit or push has been performed. Do not assume subsequent publishing or deployment is requested.

## What has actually been built

### Workspace

An npm workspace with `apps/web` and `apps/api`, TypeScript, a lockfile, Prettier, an environment example, and ignore rules. No shared package is needed yet.

```text
PLAN.md
README.md
package.json / package-lock.json
.env.example / .gitignore / .nvmrc
scripts/dev.mjs
apps/web/
  src/App.tsx
  src/ChatWidget.tsx
  src/ProductArt.tsx
  src/knowledge.ts
  src/styles.css
  src/main.tsx
  index.html / vite.config.ts / tsconfig.json / package.json
apps/api/
  src/app.ts
  src/server.ts
  tsconfig.json / package.json
data/knowledge/
  returns.md / shipping.md / warranty.md / faq.md
data/fixtures/
  products.json / customers.json / orders.json / README.md
evals/README.md
docs/FIRST-LOOK.md
docs/CLAUDE-HANDOFF.md
```

### Storefront and help center

React/TypeScript with Vite. A cream/olive outdoor-store visual design, SVG product/landscape artwork, three expandable product cards, hash navigation between Shop and Help, and a footer reflecting API health. Fonts optionally load from Google Fonts with system fallbacks.

Products are Alpine 24 backpack (€89), Ridge Two tent (€189), and Roam 750 bottle (€29). Product specifics live in the fixtures and FAQ.

The help center renders the exact Markdown documents under `data/knowledge` through Vite raw imports and a small renderer. **This is document display, not retrieval or RAG.** Customer and order fixtures are not connected to the browser.

### Chat shell

An accessible open/close panel, input focus, Escape behavior, local message display, and a fixed placeholder response. It explicitly says **“Demo chat · AI not connected.”** Sending a message does not call a model or backend. It does not simulate intelligent answers.

The future connection point is `apps/web/src/ChatWidget.tsx`.

### Backend

A small native Node HTTP server, intentionally without a web framework:

- `GET /api/health` returns status OK, service `chatbotator-api`, and `aiConnected: false`.
- `/api/chat` intentionally returns HTTP **501**, error `NOT_IMPLEMENTED`, and “Your model integration starts here.”
- Other routes return 404.
- Local binding, JSON responses, no-store responses, port validation, and graceful shutdown are present.

The main learning entry point is `apps/api/src/app.ts`.

### Not implemented

No model/provider SDK, model calls, embeddings, retrieval, conversation persistence, tool loop, authentication, authorization enforcement, eligibility logic, proposals, database, refunds, transactions, evaluation runner, graders, or tracing. There is no customer selector yet. Seeded identities will be used later; **they are not real authentication**.

## Fixtures and policy design

Everything is fictional. Review the source documents before writing expected answers; they are drafts, not real commercial/legal policies.

Policies cover:

- Standard return requests within 30 calendar days, including day 30; unused items with original tags. Opening packaging alone does not make an item used; wearing a backpack outdoors does.
- A €6 standard return shipping deduction; defects follow a separate inspection/warranty path. Standard outbound shipping is not refunded. Refunds follow inspection and return to the original payment method.
- EU shipping: €5 below €100, free at/above €100; no express or non-EU delivery. Processing and delivery estimates are distinct and not guaranteed.
- A fictional 24-month manufacturing-defect warranty, with specialist review and no automatic promise of a refund.
- Product facts, unsupported-question handling, and a fictional non-deliverable support address.

Use the files for exact details. Do not infer refund eligibility from a language-model answer.

Seeded customers: Alex Morgan (`customer-alex`) and Sam Rivera (`customer-sam`), with example.test addresses.

Orders use a **fixed reference date of 2026-10-26** so later evaluation cases can be deterministic:

- TS1001: Alex, delivered 15 October, unused backpack, tags present.
- TS1002: Alex, delivered 1 September, used bottle, no tags.
- TS1003: Sam, delivered 20 October, unused tent, tags present.
- TS1004: Alex, processing tent order, no delivery date.

Eligibility has deliberately not been precomputed. Keep test time explicit instead of silently depending on today's clock.

## Agreed roadmap

Budget: approximately **24–40 focused hours across 8–10 sessions**. This is an estimate, not a promise. No concrete day-by-day schedule has been selected.

### 1. Answer with evidence — sessions 1–2, 6–8 hours

Connect one model provider; support conversation; ingest/chunk documents with source metadata; retrieve passages; answer with supporting citations; clarify or abstain when appropriate. Treat retrieved instructions as untrusted input. Start repeatable evaluation cases immediately.

Done when supported answers cite evidence, unsupported questions fall back, document prompt injection does not override application policy, retrieved passages are inspectable, and checks include answerable, unanswerable, follow-up, and adversarial cases.

### 2. Retrieve customer data and propose — sessions 3–4, 6–10 hours

Implement validated order/eligibility tools, dispatch and bounded model/tool execution, step limits/timeouts, server-owned customer identity, ownership checks, code-based business rules, and structured proposals without mutation.

Done when cross-customer access is rejected in code, missing information prompts clarification, invalid arguments/tool failures are controlled, and validated proposals are displayed.

### 3. Confirm and execute reliably — sessions 5–6, 6–10 hours

Persist proposals with states and expiry; tie confirmation to a specific proposal; simulate refunds with transactional state and idempotency; record audit/escalation information.

Done when execution requires confirmation, permissions/rules are rechecked, duplicate confirmation or a lost-response retry cannot duplicate a refund, changed/expired proposals need renewed approval, and failures have a clear state and recovery/escalation path.

### 4. Measure and improve — sessions 7–8, 6–12 hours

Consolidate development and held-out evaluations; trace retrieved evidence, model/tool calls, validated arguments, results, and errors; measure latency/tokens/estimated cost; compare two configurations; document reproducible setup and limitations.

Done when tests cover both answers and actions, selected cases are repeated, at least one weakness is fixed from evidence, and another person can reproduce results. Keep held-out cases separate from tuning.

Evaluation work grows throughout; it does not wait until milestone 4. Record one design decision and one lesson per session.

## Deliberately deferred

Custom MCP server; OCR/document extraction; crawling and incremental sync; embedding-search comparison and hybrid/reranking; real authentication; external business integrations; queues; advanced dashboards; public deployment; multi-agent orchestration; custom coding-agent harness.

Do not add these merely to collect buzzwords. Choose one provider and a small local database when needed. No model provider, model, API budget, retrieval algorithm, or database has been selected yet.

## Run and inspect

```sh
cd /Users/mp/w/chatbotator
npm ci
npm run dev
```

- Web: `http://127.0.0.1:5174`
- API health: `http://127.0.0.1:3001/api/health`
- Vite proxies `/api` to the API.
- Port 5174 was chosen because 5173 was occupied by an unrelated process; do not kill that process.
- Ctrl+C stops both development processes.

A development server was started in the previous session; inspect ports before starting another. Do not assume that process survives the handoff.

`.nvmrc` recommends Node 24 LTS; engines permit >=22.12. The starter was actually checked with Node 25.8.1 and npm 11.11.0. Use the lockfile for reproducibility. Some package manifests use `latest`, so avoid unnecessary dependency updates.

```sh
npm run typecheck
npm run build
npm run format:check
```

Keep credentials on the server and out of version control, browser bundles, prompts, and logs. `VITE_` environment variables are client-visible. No API credentials are present or needed to inspect the starter.

## Verification already performed

Passed typecheck, API/web production build, and Prettier checks. Installation audit reported zero vulnerabilities at that time. HTTP checks verified web 200, health 200 (including through Vite), and the intentional chat 501.

Desktop browser inspection covered the storefront, product expansion, all four help topics, chat placeholder, Escape/focus restoration, and API-connected footer. A trailing empty Markdown bullet and a navigation/focus issue were corrected.

Mobile styles exist, but device-size browser verification has not been completed. No automated unit/integration/E2E suite is installed yet. No AI behavior has been tested because it has not been implemented. Do not overstate these checks.

## Next session: start here

1. Inspect the repository and preserve local changes. Read the roadmap and onboarding files.
2. Let Martin review the storefront, policy wording, product details, and seeded orders. Correct policy ambiguities before they become evaluation expectations.
3. Have Martin write approximately ten initial evaluation questions, using `evals/README.md`. Record ID, question, answerability, expected facts, supporting document/section, clarification/escalation needs, and an important forbidden claim/action. Include follow-up, missing-information, and adversarial examples; reserve a few held-out cases.
4. Review his cases for coverage without simply writing the entire dataset and answers for him.
5. Select one provider/model and a modest API budget with Martin, then coach him through his first backend model call and one end-to-end chat exchange. Use current official SDK documentation when implementing; do not guess APIs or prices. Never ask him to paste secrets into chat.
6. Add retrieval and citations as the next vertical slice; continue the roadmap incrementally.

The immediate goal is for Martin to inspect the foundation and make his first learning contribution, not to receive a completed AI application.

## Evidence to retain for later interviews/CV

A reproducible repository, concise architecture diagram and decisions, evaluation datasets/results, an explained failure and improvement, and a short demonstration of policy questions, authorized order lookup, a proposal, confirmation, simulated execution, and duplicate prevention. State limitations clearly. Describe only what Martin implemented and can explain as an independent AI application project.
