# Chatbotator

A hands-on business AI engineering project: a support assistant for **TrailSupply**, a fictional outdoor store.

## Starter status

- React/TypeScript storefront with three products, a Markdown-backed help center, and an honest chat preview.
- TypeScript/Node API with a health endpoint.
- Synthetic product/customer/order fixtures and draft policies.
- AI integration and business behavior are intentionally unimplemented for the learning exercises.

## Start

Use Node 24 LTS (see .nvmrc), or another compatible Node version >=22.12.

```sh
npm install
npm run dev
```

Web: http://127.0.0.1:5174 · API: http://127.0.0.1:3001/api/health

```sh
npm run typecheck
npm run build
```

Read [First look](docs/FIRST-LOOK.md), then begin [the evaluation exercise](evals/README.md). The agreed learning roadmap is in [PLAN.md](PLAN.md).

## Structure

```text
apps/web/          React storefront and chat UI
apps/api/          HTTP API and future AI/business logic
data/knowledge/    Shared policy documents
data/fixtures/     Synthetic store data
evals/             Your evaluation work
docs/              Handoff and learning notes
```

No checkout, real payments, public deployment, or automatic AI actions. Keep provider credentials server-side and out of version control. The optional web fonts use Google Fonts with system fallbacks.
