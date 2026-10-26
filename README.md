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

Run a single side with `npm run dev:web` or `npm run dev:api`. `npm run format` fixes formatting for both.

Read [First look](docs/FIRST-LOOK.md), then the roadmap in [PLAN.md](PLAN.md), then begin [the evaluation exercise](evals/README.md).

## Structure

```text
apps/web/src/
  api.ts             Every call from the web app to the API
  app/               App shell: header, footer, hash routing, health check
  features/shop/     Hero, product grid
  features/help/     Help center and Markdown renderer
  features/chat/     Chat widget (connect it to /api/chat)
  styles/global.css  Tokens, resets, shared typography

apps/api/src/chatbotator/
  main.py            Creates the FastAPI app
  routes/            Thin HTTP handlers: health, chat
  chat/              M1: model client, prompts, conversation
  knowledge/         M1: ingestion, chunking, retrieval, citations
                     (M2/M3 packages are yours to design when you get there)
apps/api/tests/      pytest
apps/api/README.md   Python for TypeScript developers

data/knowledge/      Shared policy documents
data/fixtures/       Synthetic store data
evals/               Your evaluation work
docs/                First look, journal, assistant handoff
```

The API is organized by domain, not by layer. Route handlers stay thin so the eval runner can call domain code directly, without HTTP.

No checkout, real payments, public deployment, or automatic AI actions. Keep provider credentials server-side and out of version control. The optional web fonts use Google Fonts with system fallbacks.
