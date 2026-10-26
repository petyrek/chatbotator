# Chatbotator

A hands-on business AI engineering project: a support assistant for **TrailSupply**, a fictional outdoor store.

## Starter status

- React/TypeScript storefront with three products, a Markdown-backed help center, and an honest chat preview.
- Python/FastAPI API with a health endpoint and a placeholder chat endpoint.
- Synthetic product/customer/order fixtures and draft policies.
- AI integration and business behavior are intentionally unimplemented for the learning exercises.

## Start

Requires Node 24 LTS (see .nvmrc; >=22.12 works) and [uv](https://docs.astral.sh/uv/). uv installs the Python version pinned in `apps/api/.python-version`.

```sh
npm run setup
npm run dev
```

Web: http://127.0.0.1:5174 · API: http://127.0.0.1:3001/api/health · API docs: http://127.0.0.1:3001/docs

```sh
npm run typecheck   # tsc (web) + mypy (api)
npm test            # pytest (api)
npm run lint        # ruff (api)
npm run build       # web production build
npm run format:check
```

Read [First look](docs/FIRST-LOOK.md), then begin [the evaluation exercise](evals/README.md). The agreed learning roadmap is in [PLAN.md](PLAN.md).

## Structure

```text
apps/web/src/
  app/               App shell, hash routing, API health hook
  components/        Header, Footer
  features/shop/     Hero, product grid
  features/help/     Help center and Markdown renderer
  features/chat/     Chat widget (connect it to /api/chat)
  styles/global.css  Tokens, resets, shared typography

apps/api/src/chatbotator/
  main.py            FastAPI app factory
  config.py          Server-side settings (credentials go here)
  routes/            Thin HTTP handlers: health, chat
  chat/              M1 — model client, prompts, conversation
  knowledge/         M1 — ingestion, chunking, retrieval, citations
  orders/            M2 — order access, ownership, eligibility rules
  tools/             M2 — tool schemas, dispatch, model/tool loop
  refunds/           M3 — proposals, confirmation, idempotent refunds
apps/api/tests/      pytest

data/knowledge/      Shared policy documents
data/fixtures/       Synthetic store data
evals/               Your evaluation work
docs/                Handoff and learning notes
```

The API is organized by domain, not by layer. Route handlers stay thin so the eval runner can call domain code directly, without HTTP.

No checkout, real payments, public deployment, or automatic AI actions. Keep provider credentials server-side and out of version control. The optional web fonts use Google Fonts with system fallbacks.
