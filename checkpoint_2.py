#!/usr/bin/env python3
"""
checkpoint_2.py — CHECKPOINT 2
Runs full 3-persona debate + judge on 1 test question and prints full output.
Run from the consensus_engine/ directory.
"""

import sys
import os
import json



from orchestrator import run_debate
from judge import judge_debate

TEST_QUESTION = "Should a company prioritize speed or quality when shipping software?"


def print_persona_result(result: dict, idx: int) -> None:
    print(f"\n{'━' * 70}")
    print(f"PERSONA {idx}: {result['persona_name']}")
    print("━" * 70)
    print(f"[RAW RESPONSE]\n{result['raw_response']}\n")
    if result["parse_error"]:
        print(f"⚠  PARSE ERROR: {result['parse_error']}")
    else:
        p = result["parsed"]
        print(f"[PARSED]")
        print(f"  Assumptions ({len(p.get('assumptions', []))}):")
        for a in p.get("assumptions", []):
            print(f"    • {a}")
        print(f"\n  Reasoning Steps ({len(p.get('reasoning_steps', []))}):")
        for i, s in enumerate(p.get("reasoning_steps", []), 1):
            print(f"    {i}. {s}")
        print(f"\n  Answer: {p.get('answer', '')}")
        print(f"  Confidence: {p.get('confidence', '?')}/100")


def print_judge_result(judge_result: dict) -> None:
    print(f"\n{'═' * 70}")
    print("JUDGE VERDICT")
    print("═" * 70)
    print(f"\n[RAW RESPONSE]\n{judge_result['raw_response']}\n")
    if judge_result["parse_error"]:
        print(f"⚠  PARSE ERROR: {judge_result['parse_error']}")
    else:
        print(f"Agreement Score: {judge_result['agreement_score']}/100\n")
        print(f"Disagreements ({len(judge_result['disagreements'])}):")
        for d in judge_result["disagreements"]:
            print(f"  ✗ {d}")
        print(f"\nSynthesis:\n  {judge_result['synthesis']}")


def main():
    print("=" * 70)
    print("CHECKPOINT 2 — Full Debate + Judge on 1 Question")
    print("=" * 70)
    print(f"\nQuestion: {TEST_QUESTION}\n")

    # Step 1: Run all 3 personas
    print("Running debate...")
    persona_outputs = run_debate(TEST_QUESTION)

    # Step 2: Print each persona result in full
    for i, result in enumerate(persona_outputs, 1):
        print_persona_result(result, i)

    # Step 3: Run judge
    print(f"\n{'─' * 70}")
    print("Running judge...")
    judge_result = judge_debate(TEST_QUESTION, persona_outputs)

    # Step 4: Print judge verdict
    print_judge_result(judge_result)

    print(f"\n{'=' * 70}")
    print("CHECKPOINT 2 COMPLETE.")
    print("=" * 70)


if __name__ == "__main__":
    main()
