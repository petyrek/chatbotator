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
from judge import JUDGE_EFFORT, JUDGE_MODEL, JUDGE_PROMPT, Verdict, judge
from report import render_markdown

from chatbotator.chat import reply as bot

EVALS_DIR = Path(__file__).parent


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


def grade(case: dict[str, Any], verdict: Verdict, stop_reason: str | None) -> list[str]:
    """Returns the reasons the case failed; an empty list means it passed.
    The judge only reports observations; pass/fail is decided here, in code."""
    # If the judge changed the checklist, its verdict can't be trusted at all.
    if [f.fact for f in verdict.facts] != case["expected_facts"]:
        raise ValueError("Judge changed the list of expected facts")
    if [r.rule for r in verdict.must_not] != case["must_not"]:
        raise ValueError("Judge changed the list of must-not rules")

    problems = []
    if stop_reason == "max_tokens":
        problems.append("reply was cut off at max_tokens")
    if verdict.behavior != case["expected_behavior"]:
        problems.append(
            f"behavior {verdict.behavior}, expected {case['expected_behavior']}"
        )
    problems += [f"missing fact: {f.fact}" for f in verdict.facts if not f.present]
    problems += [f"violated: {r.rule}" for r in verdict.must_not if r.violated]
    return problems


def metrics(case: dict[str, Any], verdict: Verdict) -> dict[str, Any]:
    """Partial credit, reported next to the strict pass/fail."""
    return {
        "behavior_ok": verdict.behavior == case["expected_behavior"],
        "facts_present": sum(f.present for f in verdict.facts),
        "facts_total": len(verdict.facts),
        "violations": sum(r.violated for r in verdict.must_not),
    }


# --- Running ------------------------------------------------------------------


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    """Runs one case through every step and records what happened at each."""
    trace: dict[str, Any] = {"case": case, "bot": None, "judge": None}
    try:
        # Step 1: the bot answers, exactly as the /api/chat endpoint would.
        reply = bot.generate_reply(case["messages"])
        trace["bot"] = call_record(reply.request, reply.response, reply.latency_s)
        trace["bot"]["reply"] = reply.text

        # Step 2: the judge reads the reply and reports what it observes.
        judged = judge(case, reply.text)
        trace["judge"] = call_record(judged.request, judged.response, judged.latency_s)
        trace["judge"]["verdict"] = judged.verdict.model_dump()

        # Step 3: code decides pass or fail.
        problems = grade(case, judged.verdict, reply.response.stop_reason)
        trace["result"] = {
            "status": "failed" if problems else "passed",
            "problems": problems,
            "metrics": metrics(case, judged.verdict),
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
    rows: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for trace in traces:
        result = trace["result"]
        for key in (trace["case"]["category"], "total"):
            row = rows[key]
            row["cases"] += 1
            row["errors"] += result["status"] == "error"
            row["passed"] += result["status"] == "passed"
            if "metrics" in result:
                m = result["metrics"]
                row["behavior_ok"] += m["behavior_ok"]
                row["facts_present"] += m["facts_present"]
                row["facts_total"] += m["facts_total"]
                row["violations"] += m["violations"]
    ordered = sorted(rows, key=lambda key: (key == "total", key))
    return {key: dict(rows[key]) for key in ordered}


def print_summary(scores: dict[str, Any]) -> None:
    print(
        f"\n  {'category':<14} {'pass':>6} {'behavior':>9} {'facts':>7} {'violations':>11}"
    )
    for category, row in scores.items():
        graded = row["cases"] - row["errors"]
        print(
            f"  {category:<14} {row['passed']:>2}/{row['cases']:<3}"
            f" {row.get('behavior_ok', 0):>5}/{graded:<3}"
            f" {row.get('facts_present', 0):>3}/{row.get('facts_total', 0):<3}"
            f" {row.get('violations', 0):>7}"
        )
    if scores["total"]["errors"]:
        print(f"\n  {scores['total']['errors']} case(s) errored; see the traces.")


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
        print(f"{result['status'].upper():<6}  {case['id']}  {case['category']}")
        for problem in result["problems"]:
            print(f"        {problem}")
        if result["status"] == "error":
            print(f"        {result['error'].strip().splitlines()[-1]}")

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
                "latency_s": {s: t[s]["latency_s"] for s in ("bot", "judge") if t[s]},
                "usage": {
                    s: t[s]["response"]["usage"] for s in ("bot", "judge") if t[s]
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
