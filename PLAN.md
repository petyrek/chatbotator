# Chatbotator — learning plan

**Project:** Customer-support assistant for TrailSupply, a fictional outdoor store.
**Time budget:** Approximately 24–40 focused hours across 8–10 sessions.
**Goal:** Personally implement and understand a complete, bounded AI workflow: answer questions, retrieve customer data, propose an action, confirm it, execute it reliably, and evaluate the result.

## Scope

- **Web:** React/TypeScript in `apps/web` (already built: storefront, help center, chat shell).
- **API:** Python/FastAPI in `apps/api/src/chatbotator/`, managed with uv and checked with pytest, mypy and ruff. `apps/api/README.md` maps the Python tools to their TypeScript equivalents.
- **Model:** one provider, called through its official Python SDK.
- **Data:** a handful of policy documents (`data/knowledge/`), synthetic customers and orders (`data/fixtures/`), and SQLite (Python's built-in `sqlite3`) from Milestone 3.

Implement the model/tool loop yourself using the provider’s SDK. Use AI for explanations and review, while ensuring you can explain and modify the core implementation independently.

Refunds are simulated. Customer identities are seeded; authorization is still enforced.

## Next step

Milestone 1 is done. The bot gets all four policy documents with every question (measured instead of retrieval; see `docs/journal.md`), cites the lines it uses, and the eval runner grades every dev case, including an instruction planted in a document (case-011).

Milestone 2, slice 1 is done: the server decides who is signed in (`customers.py`), the bot looks up only that customer's orders with two tools (`assistant/tools.py`), and `assistant/reply.py` runs a bounded loop (5 calls, a 60 s deadline, tool errors returned to the model). Order cases 012–015 cover lookup, another customer's order, an ambiguous order and order + policy.

Slice 2 is done: `returns.py` decides in code whether each item can be returned (window, recorded condition, tags), with `today` as an argument and a test per fixture order. `get_order` includes the result, and the prompt tells the model to report it and never contradict it. Cases 016–017 cover day 31 and a mixed order.

Next: a structured refund proposal (each eligible item's price, minus one €6 return charge per request; outbound shipping never refunded) that changes nothing, validated in code and shown in the chat widget.

Carried over to Milestone 4: measure pass rates over repeated runs, check whether the Haiku judge grades like the Sonnet one did, and the bot sometimes stating policy without citing it.

## Python you'll meet

- **Milestone 1:** Pydantic models (a zod schema and a TS type in one), FastAPI request and response models, `pathlib`, sync vs `async` handlers, pytest.
- **Milestone 2:** `Literal` and union types, raising exceptions vs returning error results, pytest fixtures.
- **Milestone 3:** `sqlite3`, context managers (`with`), transactions.
- **Milestone 4:** `time`, `json` and `logging` for traces and measurements.

## Milestone 1 — Answer with evidence

**Sessions 1–2 · 6–8 hours** · **Code:** `assistant/`, `policies.py`, `routes/chat.py`, `apps/web/src/api.ts`, `evals/`

Build:

- Connect the existing chat widget to `POST /api/chat` and make one model call from the API.
- Import a small collection of policy documents.
- Split documents into retrievable passages with source metadata.
- Retrieve relevant passages and generate answers with citations. Use the simplest retrieval method that meets the done criteria; comparing it with embedding search is deferred.
- Handle follow-up questions, missing information, and unsupported questions.
- Create an initial evaluation set and a small Python runner that calls the chat code directly (not over HTTP).

Learn:

- Prompts, messages, conversation history, and token limits.
- Retrieval-augmented generation: supplying relevant company information to the model.
- Grounding, citations, clarification, and abstention.
- Treating retrieved content as untrusted input.

Done when:

- [x] Answers cite passages that support their claims.
- [x] Unsupported questions receive an explicit fallback.
- [x] Misleading instructions inside a document do not override application policy.
- [x] You can inspect which passages were retrieved.
- [x] One command runs the cases in `evals/` and reports which pass, covering answerable, unanswerable, follow-up, and adversarial questions.

## Milestone 2 — Retrieve customer data and propose an action

**Sessions 3–4 · 6–10 hours** · **Code:** new packages you design (e.g. orders, tools)

Build:

- Tools to retrieve an order and check refund eligibility.
- Tool schemas, argument validation, dispatch, and result handling.
- A bounded model/tool loop with step limits, timeouts, and error handling.
- Authorization based on the application’s seeded customer identity.
- Deterministic eligibility rules.
- A structured refund proposal that performs no mutation.

Learn:

- Tool calling versus tool execution.
- Authentication versus authorization.
- Structured outputs and runtime validation.
- Application-owned business rules.
- Distinguishing retrieval, model, tool-selection, and execution failures.

Done when:

- [ ] The assistant retrieves only the current customer’s orders.
- [ ] Another customer’s order is rejected by application code.
- [ ] Missing information triggers clarification.
- [ ] Eligibility comes from code rather than model judgment.
- [ ] Invalid arguments and failed tools produce controlled outcomes.
- [ ] The interface displays a validated proposal.

## Milestone 3 — Confirm and execute reliably

**Sessions 5–6 · 6–10 hours** · **Code:** a refunds package you design, plus SQLite

Build:

- Persisted proposals with explicit states and expiry.
- Confirmation tied to a specific proposal.
- Simulated refund execution.
- Transactional state changes and idempotency.
- A small audit record.
- A simple escalation record for unsupported or failed cases.

Learn:

- Approval flows and state machines.
- Transactions and idempotency.
- Retry behavior and interrupted requests.
- Revalidation before consequential actions.
- Human escalation.

Done when:

- [ ] No refund occurs without confirmation.
- [ ] Authorization and eligibility are checked again before execution.
- [ ] Repeated confirmation produces exactly one refund.
- [ ] A simulated lost response followed by a retry does not duplicate the refund.
- [ ] Changed or expired proposals require renewed confirmation.
- [ ] Failed cases have a clear status and escalation path.

## Milestone 4 — Measure, diagnose, and improve

**Sessions 7–8 · 6–12 hours** · **Code:** `evals/`, plus tracing in the chat and tool code

Build:

- A consolidated evaluation suite with development and held-out cases.
- Inspectable records of retrieved passages, model/tool calls, validated arguments, execution results, and errors.
- Timing, token-usage, and estimated model-cost measurements.
- A small comparison of two model or retrieval configurations.
- Update the README so another person can reproduce the setup and results.

Learn:

- Retrieval quality versus answer quality versus action correctness.
- Evaluation datasets, graders, and repeated trials.
- Observability and failure analysis.
- Quality, latency, and cost tradeoffs.

Done when:

- [ ] Evaluations cover answers, citations, abstention, permissions, proposals, confirmations, and duplicate-action prevention.
- [ ] Held-out cases remain separate from prompt tuning.
- [ ] You identify and fix at least one weakness using recorded evidence.
- [ ] You repeat selected cases to observe inconsistent behavior.
- [ ] A second person can reproduce the application and evaluation results.
- [ ] You can demonstrate one failure and explain why it happened.

## Working rules

- Add evaluation cases throughout; do not postpone testing until the final milestone.
- Keep credentials out of the browser, model context, and logs.
- Enforce permissions and action rules in application code.
- Validate model outputs before using them.
- Keep model calls and retries bounded.
- Record one design decision and one lesson after each session in `docs/journal.md`.
- Prefer a working vertical slice over additional frameworks or abstractions.

## Deferred scope

Add these only after the four milestones work:

- Custom MCP server.
- Document extraction and OCR.
- Website crawling and incremental synchronization.
- Embedding-search comparison, then hybrid retrieval or reranking if useful.
- Real authentication and external business integrations.
- Background queues, advanced dashboards, and public deployment.
- Reviewer agents or multi-agent orchestration.
- Custom coding-agent harness.

## Final evidence

Retain:

- Working repository and reproducible setup.
- Architecture diagram and short decision notes.
- Evaluation cases and results.
- One documented failure and improvement.
- A short demonstration covering questions, order lookup, confirmation, refund execution, and duplicate prevention.
- A clear account of limitations.

Describe the result as an **independent AI application project**, with claims limited to the capabilities you implemented and demonstrated.
