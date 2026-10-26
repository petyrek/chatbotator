"""Turns one run's traces into trace.md: every step of every case, readable top to bottom."""

import json
from typing import Any

FENCE = "````"  # four backticks, so replies containing ``` can't break the blocks


def code_block(text: str, language: str = "text") -> str:
    return f"{FENCE}{language}\n{text.rstrip()}\n{FENCE}"


def json_block(value: Any) -> str:
    return code_block(json.dumps(value, indent=2, ensure_ascii=False), "json")


def quote(text: str) -> str:
    return "\n".join(f"> {line}" if line else ">" for line in text.strip().splitlines())


def cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def thinking_summary(response: dict[str, Any]) -> str:
    return "\n\n".join(
        block["thinking"]
        for block in response["content"]
        if block["type"] == "thinking" and block.get("thinking")
    )


def call_header(record: dict[str, Any]) -> str:
    request = record["request"]
    thinking = request.get("thinking", {})
    effort = request.get("output_config", {}).get("effort", "default")
    return (
        f"`{request['model']}` · max_tokens {request['max_tokens']} · "
        f"thinking {thinking.get('type')} ({thinking.get('display', 'omitted')}) · "
        f"effort {effort} · system prompt: see *Prompts* at the top"
    )


def response_header(record: dict[str, Any]) -> str:
    response = record["response"]
    usage = response["usage"]
    return (
        f"{record['latency_s']} s · stop_reason `{response['stop_reason']}` · "
        f"{usage['input_tokens']} input / {usage['output_tokens']} output tokens "
        "(output includes thinking)"
    )


def render_case(trace: dict[str, Any]) -> str:
    case, bot, judge, result = (
        trace["case"],
        trace["bot"],
        trace["judge"],
        trace["result"],
    )
    parts = [
        f"## {case['id']} · {case['category']} · {result['status'].upper()}",
        f"**Expected behavior:** {case['expected_behavior']}",
    ]

    if bot:
        parts += [
            "### Step 1 · Request to the bot",
            call_header(bot),
            "Messages sent (the whole conversation, every time):",
            json_block(bot["request"]["messages"]),
            "### Step 2 · Bot response",
            response_header(bot),
        ]
        thinking = thinking_summary(bot["response"])
        if thinking:
            parts += ["**Thinking (summary)**", quote(thinking)]
        parts += [
            "**Reply** (only the text blocks; this is what the customer sees)",
            quote(bot["reply"]),
        ]

    if judge:
        verdict = judge["verdict"]
        parts += [
            "### Step 3 · Request to the judge",
            call_header(judge),
            "Message sent (the case material, JSON-encoded):",
            code_block(judge["request"]["messages"][0]["content"], "json"),
            "<details><summary>Output format the judge must follow (JSON schema)</summary>\n\n"
            + json_block(judge["request"]["output_format"])
            + "\n\n</details>",
            "### Step 4 · Judge response",
            response_header(judge),
        ]
        thinking = thinking_summary(judge["response"])
        if thinking:
            parts += ["**Thinking (summary)**", quote(thinking)]
        parts += [
            "**Reasoning**",
            quote(verdict["reasoning"]),
            f"**Behavior:** {verdict['behavior']}",
            "| Expected fact | Present |\n|---|---|\n"
            + "\n".join(
                f"| {cell(f['fact'])} | {'yes' if f['present'] else 'no'} |"
                for f in verdict["facts"]
            ),
            "| Must not | Violated |\n|---|---|\n"
            + "\n".join(
                f"| {cell(r['rule'])} | {'YES' if r['violated'] else 'no'} |"
                for r in verdict["must_not"]
            ),
        ]

    parts.append("### Step 5 · Grading (in code)")
    if result["status"] == "error":
        parts += ["The case errored, so it is not graded:", code_block(result["error"])]
    elif result["problems"]:
        parts.append("\n".join(f"- {problem}" for problem in result["problems"]))
    else:
        parts.append(
            "- No problems: behavior matches, every fact is present, no rule is violated."
        )
    parts.append(f"**Result: {result['status'].upper()}**")
    return "\n\n".join(parts)


def render_markdown(
    settings: dict[str, Any], scores: dict[str, Any], traces: list[dict[str, Any]]
) -> str:
    bot, judge, total = settings["bot"], settings["judge"], scores["total"]
    commit = settings["git_commit"] + (
        " + uncommitted changes" if settings["uncommitted_changes"] else ""
    )
    score_rows = "\n".join(
        f"| {category} | {row['passed']}/{row['cases']} | {row.get('behavior_ok', 0)} "
        f"| {row.get('facts_present', 0)}/{row.get('facts_total', 0)} | {row.get('violations', 0)} "
        f"| {row['errors']} |"
        for category, row in scores.items()
    )
    header = f"""\
# Eval run · {settings["split"]} · {settings["started_at"]}

| | |
|---|---|
| Result | {total["passed"]}/{total["cases"]} passed · {total["errors"]} errors |
| Bot | `{bot["model"]}` · effort {bot["effort"]} · max_tokens {bot["max_tokens"]} · prompt `{bot["system_prompt_sha"]}` |
| Judge | `{judge["model"]}` · effort {judge["effort"]} · prompt `{judge["prompt_sha"]}` |
| Cases | `{settings["cases_file"]}` · `{settings["cases_sha"]}` |
| Code | `{commit}` |

## Scores

| Category | Passed | Behavior right | Facts present | Violations | Errors |
|---|---|---|---|---|---|
{score_rows}

## Prompts

Each case below sends these system prompts unchanged.

### Bot system prompt

{code_block(bot["system_prompt"])}

### Judge system prompt

{code_block(judge["prompt"])}"""
    return (
        "\n\n---\n\n".join([header, *(render_case(trace) for trace in traces)]) + "\n"
    )
