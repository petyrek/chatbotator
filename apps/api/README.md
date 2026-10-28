# API (Python + FastAPI)

Run it from the repo root with `npm run dev:api`, or `npm run dev` for both apps. Interactive API docs: http://127.0.0.1:3001/docs

## Coming from TypeScript

| Python                       | Closest TS/Node equivalent                                               |
| ---------------------------- | ------------------------------------------------------------------------ |
| `uv`                         | npm + nvm: installs Python 3.14 and dependencies into `.venv/`           |
| `uv sync`                    | `npm install`                                                            |
| `uv run X`                   | `npx X`, run inside the project's environment                            |
| `pyproject.toml` / `uv.lock` | `package.json` / `package-lock.json`                                     |
| `__init__.py`                | Marks a folder as an importable package (like `index.ts`, usually empty) |
| Pydantic `BaseModel`         | A zod schema and its TS type in one; FastAPI validates and serializes it |
| mypy (strict)                | `tsc --strict`                                                           |
| ruff                         | eslint + prettier                                                        |
| pytest                       | vitest/jest; tests are `test_*` functions using plain `assert`           |

Python names use `snake_case` for variables, functions and fields, and `PascalCase` for classes. Ruff enforces this.

## Layout

```text
src/chatbotator/      The importable package. src/ keeps tests importing the
                      installed package rather than the raw folder.
  main.py             Creates the FastAPI app and mounts each endpoint's router
  settings.py         Where the data lives, and the demo's fixed date (TODAY)
  routes/             HTTP only: one module per endpoint, with its request and
                      response models; handlers stay thin
    health.py         GET /api/health
    chat.py           POST /api/chat: calls the assistant, maps model errors
                      to HTTP errors
  assistant/          Everything about talking to the model
    prompt.py         The system prompt
    reply.py          The model and its settings, and the bounded loop of
                      model calls and tool calls that produces a reply
    tools.py          The tools the model can call: schemas, validation, running
    citations.py      Turns the model's citations into policy lines
  policies.py         Loads data/knowledge/*.md into titles and passages
  customers.py        current_customer(): who is signed in (set by the server)
  orders.py           The fixture orders, looked up per customer
tests/                pytest: test_<package>_<module>.py per module, e.g.
                      test_routes_chat.py, test_assistant_reply.py
```

Planned for milestones 2 and 3, so new code has an obvious home:

```text
  orders.py           M2: return eligibility, computed in code
                      (becomes an orders/ package if eligibility grows)
  routes/refunds.py   M3: the endpoint that confirms a refund proposal
  refunds/            M3: proposals and executing them; db.py holds SQLite
```

How they connect: only routes call `current_customer()`. The route passes the customer to `generate_reply`, which passes it to the tools, so the model can never choose whose orders it sees. Eligibility takes `today` as an argument instead of importing `TODAY`, so tests can set any date.

There are no "services" or "repositories" layers: a package exists only when it holds something. A response model sits next to its route until a second route needs it.

## Commands (from apps/api)

```sh
uv run pytest
uv run mypy
uv run ruff check
uv run ruff format
```

From the repo root, `npm test`, `npm run typecheck`, `npm run lint` and `npm run format` run the same things.
