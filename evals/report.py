"""Turns one run's traces into trace.md.

Each case starts with what a reader needs (purpose, conversation, expected vs
actual, evidence); every request and response sent along the way is folded below.
"""

import json
from typing import Any

FENCE = "````"  # four backticks, so replies containing ``` can't break the blocks
OK, NOT_OK = "✓", "✗"


# --- Small formatting helpers -------------------------------------------------


def code_block(text: str, language: str = "text") -> str:
    return f"{FENCE}{language}\n{text.rstrip()}\n{FENCE}"


def json_block(value: Any) -> str:
    return code_block(json.dumps(value, indent=2, ensure_ascii=False), "json")


def quote(text: str) -> str:
    return "\n".join(f"> {line}" if line else ">" for line in text.strip().splitlines())


def cell(text: str) -> str:
    """Makes text safe inside a Markdown table cell."""
    return text.replace("|", "\\|").replace("\n", " ").strip()


def folded(summary: str, body: str) -> str:
    return f"<details><summary>{summary}</summary>\n\n{body}\n\n</details>"


# --- One-line results (used by the console and the overview) ------------------


def result_line(case: dict[str, Any], result: dict[str, Any]) -> str:
    if result["status"] == "error":
        last_line: str = result["error"].strip().splitlines()[-1]
        return f"error: {last_line}"
    m = result["metrics"]
    behavior = (
        f"behavior as expected ({m['behavior']})"
        if m["behavior_ok"]
        else f"expected {case['expected_behavior']}, got {m['behavior']}"
    )
    return (
        f"{behavior} · required met {m['required_met']}/{m['required_total']}"
        f" · forbidden found {m['forbidden_detected']}/{m['forbidden_total']}"
    )


# --- One case ------------------------------------------------------------------


def conversation(case: dict[str, Any], reply: str | None) -> str:
    lines = []
    for message in case["messages"]:
        if message["role"] == "user":
            lines.append(f"**Customer:** {message['content']}")
        else:
            lines.append(
                f"**Assistant** *(fixed test history, not generated in this run)*: "
                f"{message['content']}"
            )
    if reply is not None:
        lines.append(f"**Bot reply (this run):** {reply}")
    return quote("\n\n".join(lines))


def evidence(check: dict[str, Any]) -> str:
    text = cell(check["explanation"])
    if check["quote"]:
        text += f" · *“{cell(check['quote'])}”*"
    return text


def checks_table(case: dict[str, Any], verdict: dict[str, Any]) -> str:
    behavior_ok = verdict["behavior"] == case["expected_behavior"]
    rows = [
        "| Check | Expected | Result | Evidence |",
        "|---|---|---|---|",
        f"| Behavior | {case['expected_behavior']} "
        f"| {OK if behavior_ok else NOT_OK} {verdict['behavior']} "
        "| See *Judge's reasoning* below the table. |",
    ]
    for check in verdict["required"]:
        result = f"{OK} met" if check["met"] else f"{NOT_OK} not met"
        rows.append(
            f"| Required | {cell(check['requirement'])} | {result} | {evidence(check)} |"
        )
    for check in verdict["forbidden"]:
        result = f"{NOT_OK} detected" if check["detected"] else f"{OK} not detected"
        rows.append(
            f"| Forbidden | {cell(check['claim'])} | {result} | {evidence(check)} |"
        )
    return "\n".join(rows)


def thinking_summary(response: dict[str, Any]) -> str:
    return "\n\n".join(
        block["thinking"]
        for block in response["content"]
        if block["type"] == "thinking" and block.get("thinking")
    )


def call_details(title: str, record: dict[str, Any], sent: str) -> str:
    request, response = record["request"], record["response"]
    usage = response["usage"]
    thinking = thinking_summary(response)
    effort = request.get("output_config", {}).get("effort", "default")
    return "\n\n".join(
        [
            f"#### {title}",
            f"**Sent to** `{request['model']}` · max_tokens {request['max_tokens']} · "
            f"effort {effort} · system prompt: see *System prompts* at the top",
            sent,
            f"**Received** in {record['latency_s']} s · stop_reason `{response['stop_reason']}` "
            f"· {usage['input_tokens']} input / {usage['output_tokens']} output tokens "
            "(output includes thinking)",
            "**Thinking (summary)**",
            quote(thinking)
            if thinking
            else "*No thinking: the model answered directly.*",
        ]
    )


def render_case(trace: dict[str, Any]) -> str:
    case, bot, judge, result = (
        trace["case"],
        trace["bot"],
        trace["judge"],
        trace["result"],
    )
    status = result["status"].upper()
    mark = OK if result["status"] == "passed" else NOT_OK
    parts = [
        f'<a id="{case["id"]}"></a>',
        f"## {case['id']} · {case['category']} · {mark} {status}",
        f"**Purpose:** {case['purpose']}",
        "**Conversation**",
        conversation(case, bot["reply"] if bot else None),
    ]

    if result["status"] == "error":
        parts += [
            "**The case errored, so it was not graded:**",
            code_block(result["error"]),
        ]
    else:
        verdict = judge["verdict"]
        parts += [
            checks_table(case, verdict),
            "**Judge's reasoning**",
            quote(verdict["reasoning"]),
            f"**Result: {status}** · {result_line(case, result)}",
        ]

    steps = []
    if bot:
        steps.append(
            call_details(
                "1 · The bot",
                bot,
                "Messages sent (the whole conversation, every time):\n\n"
                + json_block(bot["request"]["messages"]),
            )
        )
    if judge:
        steps.append(
            call_details(
                "2 · The judge",
                judge,
                "Message sent (the case material, JSON-encoded; its output schema is in "
                f"`traces/{case['id']}.json`):\n\n"
                + code_block(judge["request"]["messages"][0]["content"], "json"),
            )
        )
    if steps:
        parts.append(
            folded("Step by step: everything sent and received", "\n\n".join(steps))
        )
    return "\n\n".join(parts)


# --- The whole run --------------------------------------------------------------


def render_markdown(
    settings: dict[str, Any], scores: dict[str, Any], traces: list[dict[str, Any]]
) -> str:
    bot, judge, total = settings["bot"], settings["judge"], scores["total"]
    commit = settings["git_commit"]
    if settings["uncommitted_changes"]:
        commit += " + uncommitted changes"

    overview = "\n".join(
        [
            "| Case | Category | Result | Summary |",
            "|---|---|---|---|",
            *(
                f"| [{t['case']['id']}](#{t['case']['id']}) | {t['case']['category']} "
                f"| {t['result']['status'].upper()} | {cell(result_line(t['case'], t['result']))} |"
                for t in traces
            ),
        ]
    )
    score_rows = "\n".join(
        f"| {category} | {row['passed']}/{row['cases']} "
        f"| {row['behavior_ok']}/{row['cases'] - row['errors']} "
        f"| {row['required_met']}/{row['required_total']} "
        f"| {row['forbidden_detected']}/{row['forbidden_total']} | {row['errors']} |"
        for category, row in scores.items()
    )
    prompts = (
        "**Bot**\n\n"
        + code_block(bot["system_prompt"])
        + "\n\n**Judge**\n\n"
        + code_block(judge["prompt"])
    )
    header = "\n\n".join(
        [
            f"# Eval run · {settings['split']} · {settings['started_at']}",
            f"**{total['passed']}/{total['cases']} passed** · {total['errors']} errors · "
            f"bot context: {settings['bot_context']}",
            "| | |\n|---|---|\n"
            f"| Bot | `{bot['model']}` · effort {bot['effort']} · max_tokens {bot['max_tokens']} "
            f"· prompt fingerprint `{bot['system_prompt_sha']}` |\n"
            f"| Judge | `{judge['model']}` · effort {judge['effort']} "
            f"· prompt fingerprint `{judge['prompt_sha']}` |\n"
            f"| Cases | `{settings['cases_file']}` · fingerprint `{settings['cases_sha']}` |\n"
            f"| Code | `{commit}` |",
            "## Overview",
            overview,
            "## Scores by category",
            "| Category | Passed | Behavior as expected | Required met | Forbidden found | Errors |\n"
            "|---|---|---|---|---|---|\n" + score_rows,
            folded("System prompts (sent unchanged with every case)", prompts),
        ]
    )
    return (
        "\n\n---\n\n".join([header, *(render_case(trace) for trace in traces)]) + "\n"
    )
