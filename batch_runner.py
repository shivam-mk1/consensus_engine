#!/usr/bin/env python3
"""
batch_runner.py — Runs all 15 test questions through the full Consensus Engine pipeline
and logs each result to data/runs.jsonl.

Run from the consensus_engine/ directory:
  python batch_runner.py
"""

import sys
import os
import json
import time



from orchestrator import run_debate
from judge import judge_debate
from logger import append_run

# Path to the test questions file
_HERE = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(_HERE, "data", "test_questions.json")


def load_questions() -> list:
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def run_all(questions: list) -> list:
    """
    Run the full pipeline for each question and log results.

    Returns a summary list of dicts with question, agreement_score, parse_errors.
    """
    summary = []
    total = len(questions)

    for i, question in enumerate(questions, 1):
        print(f"\n{'═' * 70}")
        print(f"[{i}/{total}] {question}")
        print("═" * 70)

        parse_errors = []

        # Debate
        try:
            persona_outputs = run_debate(question)
        except Exception as e:
            print(f"  ✗ Debate failed: {e}")
            summary.append({
                "question": question,
                "agreement_score": None,
                "parse_errors": [f"Debate exception: {e}"],
                "status": "error",
            })
            continue

        # Collect parse errors from personas
        for po in persona_outputs:
            if po.get("parse_error"):
                parse_errors.append(f"{po['persona_name']}: {po['parse_error']}")

        # Judge
        try:
            judge_output = judge_debate(question, persona_outputs)
        except Exception as e:
            print(f"  ✗ Judge failed: {e}")
            judge_output = {
                "disagreements": [],
                "synthesis": "",
                "agreement_score": 0,
                "raw_response": "",
                "parse_error": f"Judge exception: {e}",
            }
            parse_errors.append(f"Judge: {e}")

        if judge_output.get("parse_error"):
            parse_errors.append(f"Judge parse: {judge_output['parse_error']}")

        score = judge_output.get("agreement_score", 0)
        print(f"  ✓ Done — agreement_score: {score}/100 | parse_errors: {len(parse_errors)}")

        # Log
        append_run(question, persona_outputs, judge_output)

        summary.append({
            "question":        question,
            "agreement_score": score,
            "parse_errors":    parse_errors,
            "status":          "ok",
        })

        # Brief pause to avoid rate-limiting
        if i < total:
            time.sleep(0.5)

    return summary


def print_summary(summary: list) -> None:
    print(f"\n\n{'═' * 70}")
    print("BATCH RUN COMPLETE — SUMMARY")
    print("═" * 70)
    print(f"{'#':<4} {'Score':>6}  {'Errors':>6}  Question")
    print("─" * 70)
    for i, row in enumerate(summary, 1):
        score = row["agreement_score"]
        score_str = f"{score:>5}" if score is not None else "  N/A"
        err_count = len(row["parse_errors"])
        q = row["question"][:55] + "..." if len(row["question"]) > 55 else row["question"]
        print(f"{i:<4} {score_str}  {err_count:>6}  {q}")

    ok_runs    = [r for r in summary if r["status"] == "ok"]
    error_runs = [r for r in summary if r["status"] == "error"]
    all_errors = [e for r in summary for e in r["parse_errors"]]

    print("─" * 70)
    print(f"Total: {len(summary)} | OK: {len(ok_runs)} | Failed: {len(error_runs)}")
    print(f"Total parse errors: {len(all_errors)}")

    if ok_runs:
        scores = [r["agreement_score"] for r in ok_runs if r["agreement_score"] is not None]
        if scores:
            print(f"Agreement scores — min: {min(scores)} | max: {max(scores)} | avg: {sum(scores)/len(scores):.1f}")

    print(f"\nLog file: data/runs.jsonl")


def main():
    print("=" * 70)
    print("CONSENSUS ENGINE — Batch Runner")
    print("=" * 70)

    questions = load_questions()
    print(f"Loaded {len(questions)} questions from data/test_questions.json\n")

    summary = run_all(questions)
    print_summary(summary)


if __name__ == "__main__":
    main()
