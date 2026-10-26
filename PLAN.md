# Business AI Engineering Learning Plan

**Project:** Customer-support assistant for a fictional online store.
**Time budget:** Approximately 24–40 focused hours across 8–10 sessions.
**Goal:** Personally implement and understand a complete, bounded AI workflow: answer questions, retrieve customer data, propose an action, confirm it, execute it reliably, and evaluate the result.

## Scope

Use your familiar React/TypeScript stack, one model provider, a small local database, synthetic customers and orders, and a handful of policy documents.

Implement the model/tool loop yourself using the provider’s SDK. Use AI for explanations and review, while ensuring you can explain and modify the core implementation independently.

Refunds are simulated. Customer identities are seeded; authorization is still enforced.

## Milestone 1 — Answer with evidence

**Sessions 1–2 · 6–8 hours**

Build:

- Minimal chat interface and model API connection.
- Import a small collection of policy documents.
- Split documents into retrievable passages with source metadata.
- Retrieve relevant passages and generate answers with citations.
- Handle follow-up questions, missing information, and unsupported questions.
- Create an initial evaluation set.

Learn:

- Prompts, messages, conversation history, and token limits.
- Retrieval-augmented generation: supplying relevant company information to the model.
- Grounding, citations, clarification, and abstention.
- Treating retrieved content as untrusted input.

Done when:

- [ ] Answers cite passages that support their claims.
- [ ] Unsupported questions receive an explicit fallback.
- [ ] Misleading instructions inside a document do not override application policy.
- [ ] You can inspect which passages were retrieved.
- [ ] Repeatable checks cover answerable, unanswerable, follow-up, and adversarial questions.

## Milestone 2 — Retrieve customer data and propose an action

**Sessions 3–4 · 6–10 hours**

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

**Sessions 5–6 · 6–10 hours**

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

**Sessions 7–8 · 6–12 hours**

Build:

- A consolidated evaluation suite with development and held-out cases.
- Inspectable records of retrieved passages, model/tool calls, validated arguments, execution results, and errors.
- Timing, token-usage, and estimated model-cost measurements.
- A small comparison of two model or retrieval configurations.
- Reproducible local setup and a concise project README.

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
- Record one design decision and one lesson after each session.
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
