# Evaluations

An eval dataset is a fixed set of conversations, each paired with what a good reply must (and must not) contain. It is written before the model is connected, so "correct" is decided from the policies rather than from whatever the model happens to say.

In Milestone 1 you write a small Python runner. It loads each case, sends `messages` to your chat code (directly, not over HTTP) and grades the reply. Rerun it after every prompt, chunking or retrieval change to see what improved and what broke.

## Files

- `cases.yaml`: development cases. Use them freely while building and tuning.
- `heldout.yaml`: 2–3 cases you write yourself and don't tune against. If the dev cases pass and these fail, the prompts have been fitted to the dev cases.

YAML is one of the usual formats for hand-written eval datasets (JSONL is the other, better for generated or exported data). The runner will need the `pyyaml` package.

## Case schema

| Field               | Type                                         | Purpose                                                                                                                                                                          |
| ------------------- | -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`                | string                                       | Unique and never reused or renumbered, so a case can be compared across runs.                                                                                                    |
| `category`          | string                                       | The behaviour being tested (see below). Lets the runner report results per category.                                                                                             |
| `tags`              | list of strings                              | Free labels (topic, feature) for filtering.                                                                                                                                      |
| `messages`          | list of `{role, content}`                    | The conversation, in the same shape as model APIs. The last message is the user turn being tested. Earlier assistant turns are fixed, so every run starts from the same history. |
| `expected_behavior` | `answer` · `clarify` · `abstain` · `decline` | What the reply should do overall (see below).                                                                                                                                    |
| `expected_facts`    | list of strings                              | Small, checkable facts the reply must contain. Not an exact sentence: wording varies between runs.                                                                               |
| `sources`           | list of `{doc, section}`                     | The passages that support the answer. Empty when the documents don't answer it.                                                                                                  |
| `must_not`          | list of strings                              | The most important wrong things to avoid: invented policy, promised actions, obeyed injections.                                                                                  |

### `expected_behavior`

- `answer`: answer from the documents, with citations.
- `clarify`: ask the customer for missing information before answering.
- `abstain`: say the information isn't available, without guessing.
- `decline`: refuse a request that breaks policy or instructions, and explain what does apply.

### `category`

`answerable`, `boundary` (edge of a rule: day 30, the €6 charge, the €100 threshold), `multi_turn`, `unanswerable`, `clarification`, `adversarial`. Add more when a new kind of behaviour needs testing.

### `sources`

`{doc, section}` matches the `##` sections in `data/knowledge/`. Once you decide how to chunk documents, each source should correspond to chunk IDs your retriever returns, so citation checks become plain set comparisons.

## How the fields get graded

- **By code:** whether the cited sources overlap `sources`, and whether the reply's behaviour matches `expected_behavior`.
- **By an LLM judge:** whether the reply contains each of the `expected_facts` and avoids every item in `must_not`. Before trusting a judge, check its verdicts against your own on a sample.

## Growing the set

Ten cases is a starting point that covers each category once. It is too few to measure small changes reliably: with 10 cases, one case is 10%. Every failure you find later becomes a new case. That is how production eval sets grow from dozens to hundreds of cases.
