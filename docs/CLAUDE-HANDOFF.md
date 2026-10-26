# Chatbotator — brief for the assistant

Read this first, then `PLAN.md` (roadmap and next step) and `README.md` (setup, commands, layout). Those two are the source of truth; this file only holds background and the working agreement.

## Background

Martin Petyrek is a senior engineer (13+ years; deep React/TypeScript and frontend architecture; technical ownership at PwC; frontend team behind Tinder Online). He has used Cursor and Claude Code extensively but has not built AI applications himself. This project is for hands-on applied AI engineering practice, and later for credible CV/interview evidence.

Do not present planned capabilities as existing experience, or describe this personal project as production employment experience. A coding-agent harness was considered and deferred.

**Chatbotator** is a support assistant for **TrailSupply**, a fictional outdoor store: answer policy questions with citations, look up the current customer's orders through authorized tools, propose a refund, confirm and execute it (simulated) reliably, and evaluate all of it. Local only, synthetic data, no real money.

## Working agreement

**Martin implements the core AI and business modules himself.** The assistant builds the surrounding foundation (setup, scripts, UI, skeletons, draft documents, fixtures, docs) and acts as coach, reviewer and debugging partner.

Martin's work:

- Model API integration, prompting, conversation state, error handling.
- Ingestion, chunking, retrieval, grounding, citations.
- Tool schemas, runtime validation, dispatch, the model/tool loop.
- Server-owned customer identity, authorization, deterministic eligibility rules.
- Proposals, confirmation, persistence, transactions, idempotency, recovery.
- Evaluation cases, graders, failure analysis, traces, usage and cost.

Work in small exercises: explain the concept and acceptance criteria, let Martin implement, review, give hints, and have him explain and correct his code. Don't silently complete core modules or replace his attempt with a finished one. That includes designing the chat request/response contract and the milestone 2/3 package boundaries.

Martin's priorities are **clarity first, then simplicity**. He is fluent in TypeScript and newer to Python, so explain Python idioms in TypeScript terms when they come up. Keep frameworks and abstractions few.

## Practical notes

- Remote: `https://github.com/petyrek/chatbotator.git`, branch `main`. Don't push unless asked.
- Port 5173 is used by an unrelated process on Martin's machine; the web app uses 5174. Don't kill it.
- Use current official SDK docs for the model provider; don't guess APIs or prices. Never ask Martin to paste secrets into chat. Credentials go in the repo-root `.env` (gitignored), read by the API only.
- Order IDs look like `TS-1001`. The evaluation clock is the fixed `referenceDate` 2026-10-26; don't depend on today's date.
- Policies were clarified on 26 October 2026: delivery date is day 0, one €6 charge per return request, partial returns allowed. `data/fixtures/README.md` says what each order tests.
- Record decisions and lessons in `docs/journal.md`.

## Evidence to keep for later

A reproducible repo, a short architecture diagram and decision notes, eval datasets and results, one explained failure and fix, and a demo of: policy questions, authorized order lookup, a proposal, confirmation, simulated execution, and duplicate prevention. State limitations clearly.
