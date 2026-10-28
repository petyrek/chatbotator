"""Runs the eval cases through the chat code and grades each reply.

From the repo root:
    npm run eval                        # development cases (evals/cases.yaml)
    npm run eval -- --heldout           # held-out cases: checkpoints only
    npm run eval -- case-003 case-008   # only these cases

Each run gets its own folder in evals/results/:
    summary.json   scores and run settings (committed, for comparing runs)
    traces/        one JSON file per case with every request and response
    trace.md       the same traces, formatted for reading
"""

import argparse
import hashlib
import json
import subprocess
import sys
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from anthropic.types import Message
from grounding import GROUNDING_PROMPT, GroundingResult, check_grounding
from judge import JUDGE_EFFORT, JUDGE_MODEL, JUDGE_PROMPT, Verdict, judge
from report import render_markdown, result_line

from chatbotator.chat import reply as bot
from chatbotator.chat.reply import Citation
from chatbotator.knowledge.documents import DOCUMENTS
from chatbotator.routes.chat import (
    ChatRequest,
    is_complete,
    to_model_message,
    to_response,
)

EVALS_DIR = Path(__file__).parent

# What the bot can see besides the conversation. Update this when retrieval is
# added, so every report says which setup produced it.
BOT_CONTEXT = f"all {len(DOCUMENTS)} policy documents with every question, citations on"

# Groundedness is reported, but doesn't decide pass/fail until its verdicts have
# been checked against a human's on a sample (calibration).
GROUNDING_DECIDES_PASS = False


# --- Recording ----------------------------------------------------------------


def short_hash(text: str) -> str:
    """A fingerprint of a prompt: if it changes between runs, the prompt changed."""
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, cwd=EVALS_DIR
    ).stdout.strip()


def run_settings(split: str, cases_file: Path) -> dict[str, Any]:
    """Everything needed to tell later whether two runs are comparable."""
    return {
        "split": split,
        "bot_context": BOT_CONTEXT,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "git_commit": git("rev-parse", "--short", "HEAD"),
        "uncommitted_changes": bool(git("status", "--porcelain")),
        "cases_file": cases_file.name,
        "cases_sha": short_hash(cases_file.read_text()),
        "bot": {
            "model": bot.MODEL,
            "effort": bot.EFFORT,
            "max_tokens": bot.MAX_TOKENS,
            "system_prompt_sha": short_hash(bot.SYSTEM_PROMPT),
            "system_prompt": bot.SYSTEM_PROMPT,
        },
        "judge": {
            "model": JUDGE_MODEL,
            "effort": JUDGE_EFFORT,
            "prompt_sha": short_hash(JUDGE_PROMPT),
            "prompt": JUDGE_PROMPT,
        },
        "grounding": {
            "model": JUDGE_MODEL,
            "effort": JUDGE_EFFORT,
            "prompt_sha": short_hash(GROUNDING_PROMPT),
            "prompt": GROUNDING_PROMPT,
            "decides_pass": GROUNDING_DECIDES_PASS,
        },
    }


def call_record(
    request: dict[str, Any], response: Message, latency_s: float
) -> dict[str, Any]:
    """One model call as plain JSON: the exact request, the full response, timing."""
    request = dict(request)
    if "output_format" in request:  # a Pydantic class; log the JSON schema it sends
        request["output_format"] = request["output_format"].model_json_schema()
    return {
        "request": request,
        "response": response.model_dump(mode="json"),
        "latency_s": round(latency_s, 2),
    }


# --- Grading ------------------------------------------------------------------


def expected_sources(case: dict[str, Any]) -> set[tuple[str, str]]:
    return {(s["doc"], s["section"]) for s in case["sources"]}


def cited_sources(citations: list[Citation]) -> set[tuple[str, str]]:
    return {(c.document, c.section) for c in citations}


def grade(
    case: dict[str, Any],
    verdict: Verdict,
    stop_reason: str | None,
    citations: list[Citation],
    grounding: GroundingResult,
) -> list[str]:
    """Returns the reasons the case failed; an empty list means it passed.
    The judge only reports observations; pass/fail is decided here, in code."""
    # If the judge changed the checklist, its verdict can't be trusted at all.
    if [c.requirement for c in verdict.required] != case["required"]:
        raise ValueError("Judge changed the list of required items")
    if [c.claim for c in verdict.forbidden] != case["forbidden"]:
        raise ValueError("Judge changed the list of forbidden items")

    problems = []
    if stop_reason == "max_tokens":
        problems.append("reply was cut off at max_tokens")
    if verdict.behavior != case["expected_behavior"]:
        problems.append(
            f"behavior: expected {case['expected_behavior']}, got {verdict.behavior}"
        )
    problems += [
        f"required, not met: {c.requirement}" for c in verdict.required if not c.met
    ]
    problems += [
        f"forbidden, detected: {c.claim}" for c in verdict.forbidden if c.detected
    ]
    if GROUNDING_DECIDES_PASS:
        problems += [
            f"unsupported: {s.statement}"
            for s in grounding.statements
            if not s.supported
        ]
    # Checked in code, not by the judge: an answer must cite at least one of the
    # sections the case lists. (Clarify, abstain and decline replies needn't cite.)
    expected = expected_sources(case)
    if case["expected_behavior"] == "answer" and expected:
        if not expected & cited_sources(citations):
            problems.append("cites none of the expected sources")
    return problems


def metrics(
    case: dict[str, Any],
    verdict: Verdict,
    citations: list[Citation],
    grounding: GroundingResult,
) -> dict[str, Any]:
    """Partial credit, reported next to the strict pass/fail."""
    expected = expected_sources(case)
    return {
        "behavior_ok": verdict.behavior == case["expected_behavior"],
        "behavior": verdict.behavior,
        "required_met": sum(c.met for c in verdict.required),
        "required_total": len(verdict.required),
        "forbidden_detected": sum(c.detected for c in verdict.forbidden),
        "forbidden_total": len(verdict.forbidden),
        "statements_supported": sum(s.supported for s in grounding.statements),
        "statements_total": len(grounding.statements),
        "sources_cited": len(expected & cited_sources(citations)),
        "sources_total": len(expected),
    }


# --- Running ------------------------------------------------------------------


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    """Runs one case through every step and records what happened at each."""
    trace: dict[str, Any] = {
        "case": case,
        "api": None,
        "bot": None,
        "judge": None,
        "grounding": None,
    }
    try:
        # Step 1: the bot answers, through the same code as the /api/chat
        # endpoint (no HTTP server runs): the request body the browser would
        # send, converted for the model, and the response body it would get.
        request = ChatRequest.model_validate({"messages": case["messages"]})
        history = [to_model_message(message) for message in request.messages]
        reply = bot.generate_reply(history)
        trace["api"] = {
            "request": request.model_dump(),
            # The endpoint answers 502 instead of an incomplete reply.
            "status": 200 if is_complete(reply) else 502,
            "response": to_response(reply).model_dump(),
        }
        trace["bot"] = call_record(reply.request, reply.response, reply.latency_s)
        trace["bot"]["reply"] = reply.text
        trace["bot"]["citations"] = [vars(c) for c in reply.citations]

        # Step 2: the judge reads the reply and reports what it observes.
        judged = judge(case, reply.text)
        trace["judge"] = call_record(judged.request, judged.response, judged.latency_s)
        trace["judge"]["verdict"] = judged.verdict.model_dump()

        # Step 3: a second grader checks each statement against the sources (the
        # documents, the bot's instructions and the conversation), and
        # code confirms every supporting quote really exists in them.
        grounding = check_grounding(case["messages"], reply.text)
        trace["grounding"] = call_record(
            grounding.request, grounding.response, grounding.latency_s
        )
        trace["grounding"]["statements"] = [
            {**vars(s), "supported": s.supported} for s in grounding.statements
        ]

        # Step 4: code decides pass or fail.
        problems = grade(
            case, judged.verdict, reply.response.stop_reason, reply.citations, grounding
        )
        trace["result"] = {
            "status": "failed" if problems else "passed",
            "problems": problems,
            "metrics": metrics(case, judged.verdict, reply.citations, grounding),
        }
    except Exception:  # a broken case is recorded as an error, not a failure
        trace["result"] = {
            "status": "error",
            "problems": [],
            "error": traceback.format_exc(),
        }
    return trace


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Scores per category: strict pass rate plus the partial-credit metrics."""
    counted = ["behavior_ok", "required_met", "required_total"]
    counted += ["forbidden_detected", "forbidden_total"]
    counted += ["statements_supported", "statements_total"]
    counted += ["sources_cited", "sources_total"]
    rows: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for trace in traces:
        result = trace["result"]
        for key in (trace["case"]["category"], "total"):
            row = rows[key]
            row["cases"] += 1
            row["errors"] += result["status"] == "error"
            row["passed"] += result["status"] == "passed"
            for name in counted:
                row[name] += result.get("metrics", {}).get(name, 0)
    ordered = sorted(rows, key=lambda key: (key == "total", key))
    return {key: dict(rows[key]) for key in ordered}


def print_summary(scores: dict[str, Any]) -> None:
    columns = ["category", "passed", "behavior", "required", "forbidden", "grounded"]
    columns += ["sources", "errors"]
    line = "  {:<14} {:>7} {:>9} {:>9} {:>10} {:>12} {:>8} {:>7}"
    print("\n" + line.format(*columns))
    for category, row in scores.items():
        graded = row["cases"] - row["errors"]
        print(
            line.format(
                category,
                f"{row['passed']}/{row['cases']}",
                f"{row['behavior_ok']}/{graded}",
                f"{row['required_met']}/{row['required_total']}",
                f"{row['forbidden_detected']}/{row['forbidden_total']}",
                f"{row['statements_supported']}/{row['statements_total']}",
                f"{row['sources_cited']}/{row['sources_total']}",
                row["errors"],
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--heldout", action="store_true", help="run heldout.yaml")
    parser.add_argument("ids", nargs="*", help="only run these case ids")
    args = parser.parse_args()

    split = "heldout" if args.heldout else "dev"
    cases_file = EVALS_DIR / ("heldout.yaml" if args.heldout else "cases.yaml")
    cases = yaml.safe_load(cases_file.read_text())
    if args.ids:
        unknown = set(args.ids) - {c["id"] for c in cases}
        if unknown:
            parser.error(
                f"no such case in {cases_file.name}: {', '.join(sorted(unknown))}"
            )
        cases = [c for c in cases if c["id"] in args.ids]

    settings = run_settings(split, cases_file)
    run_dir = EVALS_DIR / "results" / f"{datetime.now():%Y-%m-%d-%H%M%S}-{split}"
    (run_dir / "traces").mkdir(parents=True)

    traces = []
    for case in cases:
        trace = run_case(case)
        traces.append(trace)
        (run_dir / "traces" / f"{case['id']}.json").write_text(
            json.dumps(trace, indent=2, ensure_ascii=False) + "\n"
        )
        result = trace["result"]
        print(
            f"{result['status'].upper():<6}  {case['id']}  {case['category']}  {result_line(case, result)}"
        )
        for problem in result["problems"]:
            print(f"        - {problem}")

    scores = summarize(traces)
    print_summary(scores)

    summary = {
        **settings,
        "scores": scores,
        "cases": [
            {
                "id": t["case"]["id"],
                "category": t["case"]["category"],
                **t["result"],
                "latency_s": {
                    s: t[s]["latency_s"] for s in ("bot", "judge", "grounding") if t[s]
                },
                "usage": {
                    s: t[s]["response"]["usage"]
                    for s in ("bot", "judge", "grounding")
                    if t[s]
                },
            }
            for t in traces
        ],
    }
    (run_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    (run_dir / "trace.md").write_text(render_markdown(settings, scores, traces))
    print(f"\nSaved {run_dir.relative_to(EVALS_DIR.parent)}/  (read trace.md)")

    if scores["total"]["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
