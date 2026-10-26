# First look

## Run it

From the repository root:

```sh
npm run setup
npm run dev
```

Open http://127.0.0.1:5174. The API runs at http://127.0.0.1:3001/api/health. Stop both with Ctrl+C. The web dev server proxies /api to the API, so the browser needs no CORS setup.

## Review in this order

1. Browse the three products and expand their details.
2. Open Help center and read all four policies. These pages render the exact Markdown files you will later retrieve for the chatbot.
3. Open the chat, submit a message, and confirm it honestly identifies itself as an unconnected preview.
4. Confirm API connected appears in the footer.
5. Review synthetic orders and their fixed reference date.
6. Start the question-set exercise in evals/README.md.

## What is intentionally yours

- Model API integration, prompts, conversation state, and error handling.
- Ingestion/retrieval/citations and the evaluation dataset/graders.
- Tool schemas and the model/tool execution loop.
- Authentication/authorization, eligibility rules, refunds, persistence and idempotency.
- Traces, usage and cost measurement.

No model provider package, credentials, model calls, retrieval, eligibility logic, or refund actions are connected. /api/chat returns 501. Do not put secrets in VITE_ variables: those are client-visible.

## Useful entry points

- apps/web/src/app/App.tsx — app shell; features live under apps/web/src/features/.
- apps/web/src/features/chat/ChatWidget.tsx — local-only preview; replace its stub during your exercise.
- apps/api/src/chatbotator/routes/chat.py — your future chat endpoint (keep it thin).
- apps/api/src/chatbotator/chat/ and knowledge/ — where your milestone 1 code goes.
- data/knowledge/ — draft source-of-truth policies; review and change these before writing expected answers.
- data/fixtures/ — synthetic data for later tool exercises.

## Check it

```sh
npm run typecheck
npm test
npm run build
curl http://127.0.0.1:3001/api/health
```

The API is Python/FastAPI, managed with uv. Run Python commands from apps/api with `uv run ...` (for example `uv run pytest`). No shared package is needed yet.
