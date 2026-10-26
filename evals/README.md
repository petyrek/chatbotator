# Your first exercise: define correct behavior

Before connecting a model, review the four documents in `data/knowledge/` and write about ten customer questions.

## Where cases go

- `evals/cases.toml`: development cases. Use these freely while building and tuning prompts.
- `evals/heldout.toml`: 2–3 held-out cases. Don't look at them while tuning prompts; run them only to check the final result.

TOML is easy to write by hand, and Python reads it with the built-in `tomllib`, so the runner you write in Milestone 1 needs no extra package. Each case is a `[[case]]` table, for example:

```toml
[[case]]
id = "returns-001"
question = "..."
answerable = true
expected_facts = ["...", "..."]
source = "returns.md › Return window"
needs_clarification = false
must_not = "..."
```

## What to record for each case

- A stable ID and the customer question.
- Whether the question is answerable from the supplied documents.
- Expected facts (not an exact sentence the model must reproduce).
- Supporting document and section.
- Whether clarification or escalation is required.
- One important thing the assistant must not claim or do.

Include follow-up, missing-information, and adversarial cases. For anything date-related, "today" is the fixed reference date 2026-10-26 (see `data/fixtures/orders.json`).

No answers, graders or runner are written for you here.
