# First look

A 15-minute tour of what exists. Setup and commands are in the [README](../README.md).

## Review in this order

1. Browse the three products and expand their details.
2. Open the Help center and read all four policies. These pages render the exact Markdown files in `data/knowledge/` that the chatbot will later retrieve from.
3. Open the chat and send a message. It should say honestly that it is an unconnected preview.
4. Check that the footer says "API connected". That status comes from the FastAPI health endpoint.
5. Open http://127.0.0.1:3001/docs to see FastAPI's generated API docs.
6. Read `data/fixtures/README.md` and `orders.json`: synthetic orders with a fixed reference date of 2026-10-26.
7. Start the evaluation exercise in `evals/README.md`.

## Useful entry points

- `apps/web/src/app/App.tsx`: the app shell. Pages live under `apps/web/src/features/`.
- `apps/web/src/api.ts`: every call from the web app to the API.
- `apps/web/src/features/chat/ChatWidget.tsx`: the local-only chat preview you will connect.
- `apps/api/src/chatbotator/routes/chat.py`: your future chat endpoint (keep it thin).
- `apps/api/src/chatbotator/chat/` and `knowledge/`: where your Milestone 1 code goes.
- `apps/api/README.md`: Python concepts mapped to their TypeScript equivalents.

What you implement yourself, milestone by milestone, is in [PLAN.md](../PLAN.md).
