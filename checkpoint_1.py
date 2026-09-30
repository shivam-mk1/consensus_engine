#!/usr/bin/env python3
"""
checkpoint_1.py — CHECKPOINT 1
Runs ONLY the First-Principles Reasoner persona against 3 sample questions
and prints raw output to the terminal. Run from the consensus_engine/ directory.
"""

import sys
import os



from personas import PERSONAS
from orchestrator import call_persona

SAMPLE_QUESTIONS = [
    "Should a company prioritize speed or quality when shipping software?",
    "Is it ever ethical to lie?",
    "What is the most efficient sorting algorithm?",
]

FIRST_PRINCIPLES_PERSONA = next(p for p in PERSONAS if p["id"] == "first_principles")


def main():
    print("=" * 70)
    print("CHECKPOINT 1 — First-Principles Persona: 3 Sample Questions")
    print("=" * 70)

    for i, question in enumerate(SAMPLE_QUESTIONS, 1):
        print(f"\n{'─' * 70}")
        print(f"Question {i}: {question}")
        print("─" * 70)

        result = call_persona(FIRST_PRINCIPLES_PERSONA, question)

        print(f"\n[RAW RESPONSE]\n{result['raw_response']}")
        print()

        if result["parse_error"]:
            print(f"[PARSE ERROR] {result['parse_error']}")
        else:
            p = result["parsed"]
            print("[PARSED JSON]")
            print(f"  Assumptions ({len(p.get('assumptions', []))}):")
            for a in p.get("assumptions", []):
                print(f"    • {a}")
            print(f"\n  Reasoning Steps ({len(p.get('reasoning_steps', []))}):")
            for idx, s in enumerate(p.get("reasoning_steps", []), 1):
                print(f"    {idx}. {s}")
            print(f"\n  Answer:\n    {p.get('answer', '')}")
            print(f"\n  Confidence: {p.get('confidence', '?')}/100")

    print(f"\n{'=' * 70}")
    print("CHECKPOINT 1 COMPLETE — inspect output above before proceeding.")
    print("=" * 70)


if __name__ == "__main__":
    main()
