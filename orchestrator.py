"""
orchestrator.py — Core debate orchestration for the Consensus Engine.

Provides:
  - call_persona(persona, question) -> dict  — calls a single persona, returns parsed JSON
  - run_debate(question) -> list[dict]       — runs all 3 personas, returns all outputs

Backend: Groq API (GROQ_API_KEY from environment)
Model:   openai/gpt-oss-120b  (via Groq)
"""

import os
import sys
import json



from groq import Groq
from personas import PERSONAS

MODEL = "openai/gpt-oss-120b"


_client = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY environment variable is not set. "
                "Please add it to consensus_engine/.env or export it in your shell."
            )
        _client = Groq(api_key=api_key)
    return _client




def call_persona(persona: dict, question: str) -> dict:
    """
    Call a single persona with the given question via Groq.

    Args:
        persona: A dict from PERSONAS with keys 'name', 'id', 'system_prompt'.
        question: The user question string.

    Returns:
        A dict with keys:
          - persona_name: str
          - persona_id:   str
          - raw_response: str          (raw text returned by the model)
          - parsed:       dict | None  (parsed JSON if successful, else None)
          - parse_error:  str | None   (error message if JSON parsing failed)
    """
    client = _get_client()

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": persona["system_prompt"]},
            {"role": "user",   "content": question},
        ],
        temperature=0.7,
        max_tokens=2048,
    )

    raw_text = (completion.choices[0].message.content or "").strip()

    # Handle accidental markdown fences in JSON output
    parsed = None
    parse_error = None
    try:
        clean = raw_text
        if clean.startswith("```"):
            lines = clean.split("\n")
            # Drop first fence line (```json or ```) and last fence line (```)
            end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
            clean = "\n".join(lines[1:end])
        parsed = json.loads(clean)
        required = {"reasoning_steps", "assumptions", "answer", "confidence"}
        missing = required - set(parsed.keys())
        if missing:
            parse_error = f"Missing required keys in JSON: {missing}"
            parsed = None
    except json.JSONDecodeError as e:
        parse_error = f"JSONDecodeError: {e}"

    return {
        "persona_name": persona["name"],
        "persona_id":   persona["id"],
        "raw_response": raw_text,
        "parsed":       parsed,
        "parse_error":  parse_error,
    }




def run_debate(question: str) -> list:
    """
    Run all personas against the given question.

    Args:
        question: The user question string.

    Returns:
        A list of result dicts (one per persona), in PERSONAS order.
    """
    results = []
    for persona in PERSONAS:
        print(f"  → Calling persona: {persona['name']} ...", flush=True)
        result = call_persona(persona, question)
        results.append(result)
        if result["parse_error"]:
            print(
                f"    ⚠  Parse error for {persona['name']}: {result['parse_error']}",
                flush=True,
            )
        else:
            confidence = result["parsed"].get("confidence", "?")
            print(
                f"    ✓  {persona['name']} responded (confidence: {confidence})",
                flush=True,
            )
    return results
