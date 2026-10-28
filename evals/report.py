"""Turns one run's traces into trace.md.

The top shows the setup, the scores, and what is sent unchanged with every case
(prompts and documents). Each case shows its result first; below it, folded, are
the JSON messages that passed between the browser, the API, the model and the
graders, in order.
"""

import json
from typing import Any

FENCE = "````"  # four backticks, so replies containing ``` can't break the blocks
OK, NOT_OK = "✓", "✗"

FLOW = """\
| # | From → to | What travels |
|---|---|---|
| ① | Browser → API | `POST /api/chat`: the conversation so far |
| ② | API → Anthropic | the conversation, with all policy documents attached to the latest message, plus the bot's system prompt and its tools |
| ③ | Anthropic → API | either tool calls (`stop_reason: tool_use`), or the reply as text blocks, where the blocks that rest on a document carry citations |
| ②③ | (repeats) | after tool calls, the API runs the tools for the signed-in customer and repeats ② with the model's response and the results added; at most 5 calls |
| ④ | API → Browser | the reply and the policy lines it cites |
| ⑤ | Eval → Anthropic | the judge gets the conversation, the reply and the case's checklist |
| ⑥ | Anthropic → Eval | the judge's verdict, as JSON |
| ⑦ | Eval → Anthropic | the grounding check gets the reply and everything the bot had, including its tool results |
| ⑧ | Anthropic → Eval | each statement in the reply, with the source text that supports it |

Then code decides pass or fail (`grade` in run.py). The evals call the same code
as the API without running an HTTP server, so ① and ④ are built with the API's
own request and response models. In the JSON below, `‹…›` marks something
shortened for this page; `traces/<case>.json` has everything."""


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


def tidy(value: Any) -> Any:
    """Drops null fields and puts "type" first, so each block reads top-down."""
    if isinstance(value, dict):
        keys = sorted(value, key=lambda key: key != "type")
        return {k: tidy(value[k]) for k in keys if value[k] is not None}
    if isinstance(value, list):
        return [tidy(v) for v in value]
    return value


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
    parts = [
        behavior,
        f"required met {m['required_met']}/{m['required_total']}",
        f"forbidden found {m['forbidden_detected']}/{m['forbidden_total']}",
        f"grounded {m['statements_supported']}/{m['statements_total']}",
    ]
    if m["sources_total"]:
        parts.append(
            f"expected sources cited {m['sources_cited']}/{m['sources_total']}"
        )
    if m["tool_checks_total"]:
        parts.append(f"tool checks {m['tool_checks_ok']}/{m['tool_checks_total']}")
    return " · ".join(parts)


# --- The bot's reply, with its citations as numbered markers -------------------


def reply_with_markers(response: dict[str, Any]) -> tuple[str, list[str]]:
    """Rebuilds the reply from its text blocks, putting [n] after each block
    that cites a document, so you can see which sentence rests on which line."""
    text, notes = "", []
    numbers: dict[tuple[int, int], int] = {}
    for block in response["content"]:
        if block["type"] != "text":
            continue
        text += block["text"]
        for cited in block.get("citations") or []:
            key = (cited["search_result_index"], cited["start_block_index"])
            if key not in numbers:
                numbers[key] = len(numbers) + 1
                notes.append(
                    f"[{numbers[key]}] {cited['title']}: *“{cited['cited_text']}”*"
                )
            text += f" [{numbers[key]}]"
    return text, notes


def tool_call(run: dict[str, Any]) -> str:
    """e.g. `get_order({"order_id": "TS-1001"})` ✓, or ✗ with the error."""
    call = f"`{run['name']}({json.dumps(run['arguments'])})`"
    return f"{call} {NOT_OK} {run['output']}" if run["is_error"] else f"{call} {OK}"


def conversation(case: dict[str, Any], bot: dict[str, Any] | None) -> str:
    lines = []
    for message in case["messages"]:
        if message["role"] == "user":
            lines.append(f"**Customer:** {message['content']}")
        else:
            lines.append(f"**Assistant** *(fixed test history)*: {message['content']}")
    if bot is not None:
        runs = [run for step in bot["steps"] for run in step["tool_runs"]]
        if runs:
            lines.append("**Bot's tool calls:** " + " · ".join(map(tool_call, runs)))
        text, notes = reply_with_markers(bot["steps"][-1]["response"])
        lines.append(f"**Bot (this run):** {text}")
        lines.append("\n".join(f"- {note}" for note in notes) or "*Cited nothing.*")
    return quote("\n\n".join(lines))


# --- The graders' findings ------------------------------------------------------


def evidence(check: dict[str, Any]) -> str:
    text = cell(check["explanation"])
    if check["quote"]:
        text += f" · *“{cell(check['quote'])}”*"
    return text


def checks_table(
    case: dict[str, Any],
    verdict: dict[str, Any],
    bot: dict[str, Any],
    tool_checks: list[dict[str, Any]],
) -> str:
    behavior_ok = verdict["behavior"] == case["expected_behavior"]
    rows = [
        "| Check | Expected | Result | Evidence |",
        "|---|---|---|---|",
        f"| Behavior | {case['expected_behavior']} "
        f"| {OK if behavior_ok else NOT_OK} {verdict['behavior']} "
        f"| {cell(verdict['reasoning'])} |",
    ]
    for check in verdict["required"]:
        result = f"{OK} met" if check["met"] else f"{NOT_OK} not met"
        rows.append(
            f"| Required | {cell(check['requirement'])} | {result} | {evidence(check)} |"
        )
    for check in verdict["forbidden"]:
        result = f"{NOT_OK} found" if check["detected"] else f"{OK} not found"
        rows.append(
            f"| Forbidden | {cell(check['claim'])} | {result} | {evidence(check)} |"
        )
    expected = [f"{s['doc']} › {s['section']}" for s in case["sources"]]
    cited = {f"{c['document']} › {c['section']}" for c in bot["citations"]}
    if expected and case["expected_behavior"] == "answer":
        hit = [e for e in expected if e in cited]
        result = f"{OK} cited" if hit else f"{NOT_OK} not cited"
        rows.append(
            f"| Sources | {', '.join(expected)} | {result} "
            f"| Checked in code: an answer must cite at least one of these. "
            f"Cited: {', '.join(hit or sorted(cited)) or 'nothing'}. |"
        )
    runs = [run for step in bot["steps"] for run in step["tool_runs"]]
    made = " · ".join(f"`{run['name']} {json.dumps(run['arguments'])}`" for run in runs)
    for check in tool_checks:
        called = check["ok"] if check["kind"] == "expected" else not check["ok"]
        rule = "calls" if check["kind"] == "expected" else "never calls"
        rows.append(
            f"| Tools | {rule} `{check['call']}` "
            f"| {OK if check['ok'] else NOT_OK} {'called' if called else 'not called'} "
            f"| Checked in code. The bot called: {made or 'no tools'}. |"
        )
    return "\n".join(rows)


def grounding_table(grounding: dict[str, Any], decides_pass: bool) -> str:
    statements = grounding["statements"]
    supported = sum(s["supported"] for s in statements)
    role = "decides pass/fail" if decides_pass else "reported only"
    rows = [
        f"**Grounding** ({role}): {supported}/{len(statements)} statements "
        "supported by a quote that code found in the sources",
        "",
        "| Statement in the reply | Supported | Source quote |",
        "|---|---|---|",
    ]
    for s in statements:
        if s["supported"]:
            result = OK
        elif s["grader_says_supported"]:
            result = f"{NOT_OK} the grader's quote isn't in the sources"
        else:
            result = f"{NOT_OK} {cell(s['explanation'])}"
        source = f"*“{cell(s['supporting_quote'])}”*" if s["supporting_quote"] else ""
        rows.append(f"| {cell(s['statement'])} | {result} | {source} |")
    if not statements:
        rows.append("| (no factual statements) | | |")
    return "\n".join(rows)


# --- The data flow: what each hop carried ---------------------------------------


def compact_response(response: dict[str, Any], decode_text: bool) -> dict[str, Any]:
    """The response's content, stop_reason and token counts.
    Graders answer with a JSON object inside a text block; decode_text shows it
    decoded."""
    content = []
    for block in tidy(response["content"]):
        if block["type"] == "thinking":
            block["signature"] = "‹signature›"
        if block["type"] == "text" and decode_text:
            block["text"] = json.loads(block["text"])
        content.append(block)
    usage = response["usage"]
    return {
        "content": content,
        "stop_reason": response["stop_reason"],
        "usage": tidy(
            {
                "input_tokens": usage["input_tokens"],
                "output_tokens": usage["output_tokens"],
                "output_tokens_details": usage.get("output_tokens_details"),
            }
        ),
    }


def bot_request(request: dict[str, Any]) -> dict[str, Any]:
    messages = []
    for message in request["messages"]:
        if isinstance(message["content"], list):
            content = [
                {**b, "content": f"‹{len(b['content'])} passages, see Documents›"}
                if b["type"] == "search_result"
                else b
                for b in message["content"]
            ]
            message = {**message, "content": content}
        messages.append(message)
    return {
        **request,
        "system": "‹the bot's system prompt, see Prompts›",
        "messages": messages,
        "tools": "‹the tool definitions, see Tools›",
    }


def grader_request(
    request: dict[str, Any], prompt_name: str, material: Any
) -> dict[str, Any]:
    message = request["messages"][0]
    return {
        **request,
        "system": f"‹the {prompt_name}, see Prompts›",
        "messages": [{**message, "content": material}],
        "output_format": "‹the JSON schema of the answer›",
    }


def hop(title: str, value: Any, note: str = "") -> str:
    heading = f"**{title}**" + (f" · {note}" if note else "")
    return f"{heading}\n\n{json_block(value)}"


def bot_steps(steps: list[dict[str, Any]]) -> list[str]:
    """② and ③ for each model call. After the first, a request is the previous
    one plus two messages (the model's tool calls and our results), so only
    those two are shown."""
    hops = []
    for number, step in enumerate(steps, start=1):
        label = f" · call {number} of {len(steps)}" if len(steps) > 1 else ""
        request = bot_request(step["request"])
        if number == 1:
            hops.append(
                hop(f"② API → Anthropic{label} · client.messages.create(…)", request)
            )
        else:
            added = {
                "‹…›": f"‹the request of call {number - 1}, with these messages added›",
                "messages": tidy(request["messages"][-2:]),
            }
            hops.append(hop(f"② API → Anthropic{label}", added))
        note = f"{step['latency_s']:.1f} s"
        if step["response"]["stop_reason"] == "tool_use":
            note += " · asks for tools: the API runs them and calls the model again"
        hops.append(
            hop(
                f"③ Anthropic → API{label}",
                compact_response(step["response"], decode_text=False),
                note,
            )
        )
    return hops


def data_flow(trace: dict[str, Any]) -> str:
    api, bot, judge, grounding = (
        trace["api"],
        trace["bot"],
        trace["judge"],
        trace["grounding"],
    )
    decoded = "`content` is sent as a JSON string, shown decoded"
    # The graders get the same reply that ④ shows; repeating it adds nothing.
    reply = api["response"]["reply"] if api else None
    same_reply = "‹the reply from ④›"
    answer = "the text block holds a JSON string, shown decoded"
    hops = []
    if api:
        hops.append(hop("① Browser → API · POST /api/chat", api["request"]))
    if bot:
        hops += bot_steps(bot["steps"])
    if api:
        status = api["status"]
        note = (
            "200 OK · built from ③: the text blocks joined, thinking dropped, and "
            "each citation's section looked up from its search_result_index and "
            "start_block_index"
            if status == 200
            else f"{status}: the reply was incomplete, so the browser gets an error"
        )
        hops.append(hop("④ API → Browser", api["response"], note))
    if judge:
        material = json.loads(judge["request"]["messages"][0]["content"])
        if material["final_reply"] == reply:
            material["final_reply"] = same_reply
        hops += [
            hop(
                "⑤ Eval → Anthropic · the judge · client.messages.parse(…)",
                grader_request(judge["request"], "judge prompt", material),
                decoded,
            ),
            hop(
                "⑥ Anthropic → Eval",
                compact_response(judge["response"], decode_text=True),
                f"{judge['latency_s']:.1f} s · {answer}",
            ),
        ]
    if grounding:
        material = json.loads(grounding["request"]["messages"][0]["content"])
        material["sources"]["policy_documents"] = (
            "‹the same documents as plain text, one “Section: line” per line›"
        )
        material["sources"]["assistant_instructions"] = (
            "‹the bot's system prompt, see Prompts›"
        )
        if material["reply"] == reply:
            material["reply"] = same_reply
        hops += [
            hop(
                "⑦ Eval → Anthropic · the grounding check · client.messages.parse(…)",
                grader_request(grounding["request"], "grounding prompt", material),
                decoded,
            ),
            hop(
                "⑧ Anthropic → Eval",
                compact_response(grounding["response"], decode_text=True),
                f"{grounding['latency_s']:.1f} s · {answer}",
            ),
        ]
    calls = [*(bot["steps"] if bot else []), *(r for r in (judge, grounding) if r)]
    seconds = sum(call["latency_s"] for call in calls)
    tokens_in = sum(call["response"]["usage"]["input_tokens"] for call in calls)
    tokens_out = sum(call["response"]["usage"]["output_tokens"] for call in calls)
    summary = (
        f"Data flow: every JSON sent and received, in order · {len(calls)} model "
        f"calls · {seconds:.1f} s · {tokens_in:,} input / {tokens_out:,} output tokens"
    )
    return folded(summary, "\n\n".join(hops))


# --- One case ------------------------------------------------------------------


def render_case(trace: dict[str, Any], grounding_decides_pass: bool) -> str:
    case, bot, result = trace["case"], trace["bot"], trace["result"]
    status = result["status"].upper()
    mark = OK if result["status"] == "passed" else NOT_OK
    parts = [
        f'<a id="{case["id"]}"></a>',
        f"## {case['id']} · {case['category']} · {mark} {status}",
        f"*{case['purpose']}*",
        conversation(case, bot),
    ]
    if bot and case.get("extra_documents"):
        parts.append(
            folded(
                "Added for this case only, after the store's documents: "
                + ", ".join(case["extra_documents"]),
                documents_block(search_results(trace, extra=True)),
            )
        )
    if result["status"] == "error":
        parts += ["**Error, so the case was not graded:**", code_block(result["error"])]
    else:
        parts += [
            checks_table(case, trace["judge"]["verdict"], bot, result["tool_checks"]),
            grounding_table(trace["grounding"], grounding_decides_pass),
        ]
        decision = "**Decision** (code, `grade` in run.py): "
        if result["problems"]:
            decision += f"{NOT_OK} failed because:\n" + "\n".join(
                f"- {problem}" for problem in result["problems"]
            )
        else:
            decision += f"{OK} passed: no check failed"
        parts.append(decision)
    parts.append(data_flow(trace))
    return "\n\n".join(parts)


# --- The whole run --------------------------------------------------------------


def search_results(
    trace: dict[str, Any], extra: bool
) -> list[tuple[int, dict[str, Any]]]:
    """The documents the bot got in this case, with the search_result_index that
    citations use: the store's own (extra=False), or the ones this case added."""
    # The documents are attached to the customer's message, the last one in the
    # first call's request.
    blocks = trace["bot"]["steps"][0]["request"]["messages"][-1]["content"]
    results = [b for b in blocks if b["type"] == "search_result"]
    added = trace["case"].get("extra_documents", [])
    return [(i, r) for i, r in enumerate(results) if (r["source"] in added) == extra]


def documents_block(results: list[tuple[int, dict[str, Any]]]) -> str:
    """Numbered the way citations point at them: search_result_index picks the
    document, start/end_block_index the lines (end exclusive)."""
    lines = []
    for index, result in results:
        lines.append(f"search_result_index {index} · {result['source']}")
        lines += [
            f"  {i:>2}  {passage['text']}"
            for i, passage in enumerate(result["content"])
        ]
    return code_block("\n".join(lines))


def render_markdown(
    settings: dict[str, Any], scores: dict[str, Any], traces: list[dict[str, Any]]
) -> str:
    bot, judge, grounding = settings["bot"], settings["judge"], settings["grounding"]
    total = scores["total"]
    commit = settings["git_commit"]
    if settings["uncommitted_changes"]:
        commit += " + uncommitted changes"

    setup = "\n".join(
        [
            "| | Model | Effort | Prompt fingerprint |",
            "|---|---|---|---|",
            f"| Bot | `{bot['model']}` | {bot['effort']} | `{bot['system_prompt_sha']}` |",
            f"| Judge | `{judge['model']}` | {judge['effort']} | `{judge['prompt_sha']}` |",
            f"| Grounding check | `{grounding['model']}` | {grounding['effort']} "
            f"| `{grounding['prompt_sha']}` |",
        ]
    )
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
        f"| {row['forbidden_detected']}/{row['forbidden_total']} "
        f"| {row['statements_supported']}/{row['statements_total']} "
        f"| {row['sources_cited']}/{row['sources_total']} "
        f"| {row['tool_checks_ok']}/{row['tool_checks_total']} | {row['errors']} |"
        for category, row in scores.items()
    )
    prompts = "\n\n".join(
        [
            "**The bot's system prompt**",
            code_block(bot["system_prompt"]),
            "**The judge prompt**",
            code_block(judge["prompt"]),
            "**The grounding prompt**",
            code_block(grounding["prompt"]),
        ]
    )
    parts = [
        f"# Eval run · {settings['split']} · {settings['started_at']}",
        f"**{total['passed']}/{total['cases']} passed** · {total['errors']} errors · "
        f"cases `{settings['cases_file']}` (`{settings['cases_sha']}`) · code `{commit}`",
        setup,
        f"The bot gets {settings['bot_context']}.",
        "## Overview",
        overview,
        "## Scores",
        "| Category | Passed | Behavior as expected | Required met | Forbidden found "
        "| Grounded statements | Expected sources cited | Tool checks | Errors |\n"
        "|---|---|---|---|---|---|---|---|---|\n" + score_rows,
        "## How a case runs",
        FLOW,
        folded("Prompts (sent unchanged with every case)", prompts),
    ]
    if any(t["bot"] for t in traces):
        first = next(t for t in traces if t["bot"])
        parts.append(
            folded(
                "Tools (sent with every call to the bot; reply.py runs them)",
                json_block(first["bot"]["steps"][0]["request"]["tools"]),
            )
        )
        parts.append(
            folded(
                "Documents (attached to every question, as the bot sees them)",
                documents_block(
                    search_results(next(t for t in traces if t["bot"]), extra=False)
                ),
            )
        )
    return (
        "\n\n---\n\n".join(
            [
                "\n\n".join(parts),
                *(render_case(t, grounding["decides_pass"]) for t in traces),
            ]
        )
        + "\n"
    )
