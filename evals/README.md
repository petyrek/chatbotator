# Evaluations

An eval dataset is a fixed set of conversations, each paired with what a good reply must (and must not) contain. It is written before the model is connected, so "correct" is decided from the policies rather than from whatever the model happens to say.

`npm run eval` runs every case: it sends `messages` to the chat code (directly, not over HTTP), has an LLM judge grade the reply, and decides pass or fail in code. Rerun it after every prompt, chunking or retrieval change to see what improved and what broke.

- `run.py`: runs the cases, grades them, writes the results.
- `judge.py`: the judge: behaviour and the `required` / `forbidden` checklist.
- `grounding.py`: the grounding check: is every statement in the reply backed by a source?
- `report.py`: formats the traces as Markdown.

## Reading a run

Each run gets a folder in `results/`, named by time and split:

- `trace.md`: start here. The setup, the scores, how a case runs, and (once) the prompts and documents; then every case, result first.
- `traces/<case-id>.json`: the same, as raw JSON (full API requests and responses).
- `summary.json`: scores and the settings that produced them (models, effort, prompt fingerprints, git commit). Only this file is committed; two runs are comparable only if their prompt fingerprints and judge match.

Each case in `trace.md` starts with its purpose, the conversation (the bot's reply marks each cited policy line as [n]), a table of expected vs actual with the judge's evidence, and the grounding check. Folded below are the eight JSON messages of the data flow, in order: browser → API → model → API → browser, then the judge and the grounding check.

Scores have a strict **pass** (everything right) plus partial credit: **behavior as expected**, **required met**, **forbidden found**, **grounded statements** and **expected sources cited**. A case that crashes counts as an **error**, not a failure.

## Files

- `cases.yaml`: development cases. Use them freely while building and tuning.
- `heldout.yaml`: 2–3 cases you write yourself and don't tune against. If the dev cases pass and these fail, the prompts have been fitted to the dev cases.

YAML is one of the usual formats for hand-written eval datasets (JSONL is the other, better for generated or exported data).

## Case schema

| Field               | Type                                         | Purpose                                                                                                                                                                          |
| ------------------- | -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`                | string                                       | Unique and never reused or renumbered, so a case can be compared across runs.                                                                                                    |
| `category`          | string                                       | The behaviour being tested (see below). Lets the runner report results per category.                                                                                             |
| `tags`              | list of strings                              | Free labels (topic, feature) for filtering.                                                                                                                                      |
| `messages`          | list of `{role, content}`                    | The conversation, in the same shape as model APIs. The last message is the user turn being tested. Earlier assistant turns are fixed, so every run starts from the same history. |
| `expected_behavior` | `answer` · `clarify` · `abstain` · `decline` | What the reply should do overall (see below).                                                                                                                                    |
| `purpose`           | string                                       | One sentence: what this case checks. Shown first in the report.                                                                                                                  |
| `required`          | list of strings                              | Things a good reply must state or do. One small claim each, and only what this question needs. Not exact wording: replies vary between runs.                                     |
| `sources`           | list of `{doc, section}`                     | The passages that support the answer. Empty when the documents don't answer it.                                                                                                  |
| `forbidden`         | list of strings                              | Things the reply must never claim or do: invented policy, promised actions, obeyed injections.                                                                                   |

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

- **By an LLM judge** (`claude-haiku-5-5`, the same model as the bot to keep runs cheap; models tend to grade their own writing kindly, so switch to a stronger model if scores look too kind): the reply's behaviour, whether each `required` item is met, and whether any `forbidden` item appears. For every item it quotes the words in the reply its decision rests on and explains it in one sentence. It only reports observations.
- **By a grounding check** (same model, a separate call with one job): it splits the reply into factual statements and, for each, copies the supporting text from the sources (the policy documents, the bot's instructions, and what the customer said). **Code then checks that every quote really exists in the sources**, so "supported" always points at real text. It is reported, but doesn't decide pass/fail until calibrated (`GROUNDING_DECIDES_PASS` in `run.py`).
- **By code:** pass or fail, from the judge's observations and `expected_behavior`; and for `answer` cases, whether the reply cites at least one of the case's `sources` (from the API's citations).

Before trusting a judge, check its verdicts against your own on a sample, and again whenever the judge prompt changes.

## Growing the set

Ten cases is a starting point that covers each category once. It is too few to measure small changes reliably: with 10 cases, one case is 10%. Every failure you find later becomes a new case. That is how production eval sets grow from dozens to hundreds of cases.
