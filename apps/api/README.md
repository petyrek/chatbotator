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
  main.py             Creates the FastAPI app and mounts the routers
  routes/             Thin HTTP handlers; real logic lives in domain packages
  chat/               M1: model client, prompts, conversation
  knowledge/          M1: ingestion, chunking, retrieval, citations
tests/                pytest
```

Packages for milestones 2 and 3 (orders, tools, refunds) don't exist yet. You decide their boundaries when you get there.

## Commands (from apps/api)

```sh
uv run pytest
uv run mypy
uv run ruff check
uv run ruff format
```

From the repo root, `npm test`, `npm run typecheck`, `npm run lint` and `npm run format` run the same things.
