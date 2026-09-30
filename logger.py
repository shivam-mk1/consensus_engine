"""
logger.py — Append debate runs to data/runs.jsonl for the Consensus Engine.

Provides:
  append_run(question, persona_outputs, judge_output) -> None

Each JSONL line is a self-contained JSON object with:
  - timestamp
  - question
  - persona_outputs (list of persona result dicts)
  - judge_output (disagreements, synthesis, agreement_score)
"""

import os
import sys
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Path to the JSONL log file (relative to this file's directory)
_LOG_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_LOG_FILE = os.path.join(_LOG_DIR, "runs.jsonl")


def _ensure_log_dir() -> None:
    os.makedirs(_LOG_DIR, exist_ok=True)


def _serialise_persona_output(output: dict) -> dict:
    """Return a clean, serialisable version of a persona output dict."""
    return {
        "persona_name":  output.get("persona_name", ""),
        "persona_id":    output.get("persona_id", ""),
        "parsed":        output.get("parsed"),          # may be None
        "parse_error":   output.get("parse_error"),     # may be None
        # Omit raw_response to keep log files compact; it's recoverable via re-run
    }


def _serialise_judge_output(judge_output: dict) -> dict:
    """Return a clean, serialisable version of a judge output dict."""
    return {
        "disagreements":   judge_output.get("disagreements", []),
        "synthesis":       judge_output.get("synthesis", ""),
        "agreement_score": judge_output.get("agreement_score", 0),
        "parse_error":     judge_output.get("parse_error"),
    }


def append_run(
    question: str,
    persona_outputs: list,
    judge_output: dict,
) -> None:
    """
    Append one debate run to data/runs.jsonl.

    Args:
        question:        The original question.
        persona_outputs: List of dicts from run_debate().
        judge_output:    Dict from judge_debate().
    """
    _ensure_log_dir()

    record = {
        "timestamp":       datetime.now(timezone.utc).isoformat(),
        "question":        question,
        "persona_outputs": [_serialise_persona_output(o) for o in persona_outputs],
        "judge_output":    _serialise_judge_output(judge_output),
    }

    with open(_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_all_runs() -> list:
    """
    Load all logged runs from data/runs.jsonl.

    Returns:
        A list of run dicts, in append order (oldest first).
        Returns [] if the file doesn't exist yet.
    """
    if not os.path.isfile(_LOG_FILE):
        return []
    runs = []
    with open(_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    runs.append(json.loads(line))
                except json.JSONDecodeError:
                    pass  # Skip malformed lines
    return runs
