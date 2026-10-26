# First look

A 15-minute tour of what exists. Setup and commands are in the [README](../README.md).

## Review in this order

1. Browse the three products and expand their details.
2. Open the Help center and read all four policies. These pages render the exact Markdown files in `data/knowledge/` that the chatbot will later retrieve from.
3. Open the chat and send a message. It answers with Claude Haiku 5.5 (your API key must be in `.env`). Without policy documents yet, it declines policy questions and points to support.
4. Check that the footer says "API connected". That status comes from the FastAPI health endpoint.
5. Open http://127.0.0.1:3001/docs to see FastAPI's generated API docs.
6. Read `data/fixtures/README.md` and `orders.json`: synthetic orders with a fixed reference date of 2026-10-26.
7. Read `evals/README.md`, run `npm run eval`, and open the `trace.md` it writes to see every step of every case.

## Useful entry points

- `apps/web/src/app/App.tsx`: the app shell. Pages live under `apps/web/src/features/`.
- `apps/web/src/api.ts`: every call from the web app to the API.
- `apps/web/src/features/chat/ChatWidget.tsx`: the chat widget, which sends the whole conversation to `POST /api/chat`.
- `apps/api/src/chatbotator/routes/chat.py`: the chat endpoint (kept thin) and `chat/reply.py`: the model call.
- `apps/api/src/chatbotator/chat/` and `knowledge/`: where your Milestone 1 code goes.
- `apps/api/README.md`: Python concepts mapped to their TypeScript equivalents.

What you implement yourself, milestone by milestone, is in [PLAN.md](../PLAN.md).
