"""
judge.py — The Judge model for the Consensus Engine.

Provides:
  judge_debate(question, persona_outputs) ->
    {
      "disagreements": [...],   # list of specific named disagreements (at least 1 if they differ)
      "synthesis":     str,     # synthesized final answer
      "agreement_score": int    # 0-100: how much the personas actually agreed
    }

Backend: same Groq model as orchestrator.
"""

import os
import sys
import json


from groq import Groq

MODEL = "openai/gpt-oss-120b"

JUDGE_SYSTEM_PROMPT = """You are an impartial Judge analyzing a structured debate between three AI reasoning personas.

You will receive:
1. The original question
2. Three persona responses, each with reasoning_steps, assumptions, answer, and confidence

YOUR JOB:
A. Identify SPECIFIC points of disagreement between the personas.
   - You MUST name at least one concrete disagreement if the personas differ in any substantive way.
   - "Disagreement" means: they reach different conclusions, make conflicting assumptions, identify different key constraints, or weight the same factors differently.
   - Do NOT just write "they differ in tone" or "they emphasize different things" — name the SPECIFIC claim where they diverge.
   - A disagreement entry should follow this pattern: "[Persona A] claims X, while [Persona B] claims Y."
   - If the personas genuinely agree on everything substantive, return an empty list.

B. Produce a synthesized final answer that:
   - Incorporates the strongest insights from all three perspectives
   - Resolves or explicitly acknowledges unresolved disagreements
   - Is better than any single persona's answer by surfacing nuances they collectively identified
   - Is written as a clear, direct answer to the original question

C. Score the agreement level (0-100):
   - 100 = all three gave essentially identical answers with the same reasoning
   - 75  = same conclusion but different reasoning paths or minor caveats differ
   - 50  = same general direction but meaningfully different conclusions or key caveats
   - 25  = significant substantive disagreement — different answers or opposite framings
   - 0   = complete contradiction — personas gave mutually exclusive answers

CRITICAL: You MUST respond with ONLY a valid JSON object — no markdown fences, no preamble, no trailing text.
The JSON must have exactly these keys:
{
  "disagreements": ["Persona A claims X while Persona B claims Y.", "..."],
  "synthesis": "your synthesized final answer as a paragraph",
  "agreement_score": <integer 0-100>
}
Any output outside this JSON structure will break the pipeline. Output ONLY the JSON."""


_client = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY environment variable is not set."
            )
        _client = Groq(api_key=api_key)
    return _client


def _format_persona_outputs(persona_outputs: list) -> str:
    """Format all persona outputs into a readable prompt block for the judge."""
    lines = []
    for i, output in enumerate(persona_outputs, 1):
        lines.append(f"--- PERSONA {i}: {output['persona_name']} ---")
        if output["parsed"]:
            p = output["parsed"]
            lines.append(f"Assumptions: {json.dumps(p.get('assumptions', []))}")
            lines.append(f"Reasoning Steps: {json.dumps(p.get('reasoning_steps', []))}")
            lines.append(f"Answer: {p.get('answer', '')}")
            lines.append(f"Confidence: {p.get('confidence', '?')}/100")
        else:
            # Fall back to raw text if parsing failed
            lines.append(f"[Raw response — JSON parse failed]: {output['raw_response']}")
        lines.append("")
    return "\n".join(lines)


def judge_debate(question: str, persona_outputs: list) -> dict:
    """
    Judge the debate between personas and produce a synthesis.

    Args:
        question:        The original question asked.
        persona_outputs: List of dicts from run_debate() (one per persona).

    Returns:
        A dict with keys:
          - disagreements:   list[str]  — specific named disagreement statements
          - synthesis:       str        — synthesized final answer
          - agreement_score: int        — 0-100 agreement level
          - raw_response:    str        — raw judge model output
          - parse_error:     str|None   — error if JSON parsing failed
    """
    client = _get_client()

    user_content = (
        f"ORIGINAL QUESTION: {question}\n\n"
        f"PERSONA RESPONSES:\n\n"
        f"{_format_persona_outputs(persona_outputs)}"
    )

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user",   "content": user_content},
        ],
        temperature=0.3,  # Lower temp for more consistent judging
        max_tokens=2048,
    )

    raw_text = (completion.choices[0].message.content or "").strip()

    # Parse JSON — handle accidental markdown fences
    parsed = None
    parse_error = None
    try:
        clean = raw_text
        if clean.startswith("```"):
            lines = clean.split("\n")
            end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
            clean = "\n".join(lines[1:end])
        parsed = json.loads(clean)
        required = {"disagreements", "synthesis", "agreement_score"}
        missing = required - set(parsed.keys())
        if missing:
            parse_error = f"Missing keys in judge JSON: {missing}"
            parsed = None
    except json.JSONDecodeError as e:
        parse_error = f"JSONDecodeError: {e}"

    if parsed:
        return {
            "disagreements":   parsed.get("disagreements", []),
            "synthesis":       parsed.get("synthesis", ""),
            "agreement_score": int(parsed.get("agreement_score", 0)),
            "raw_response":    raw_text,
            "parse_error":     None,
        }
    else:
        return {
            "disagreements":   [],
            "synthesis":       "",
            "agreement_score": 0,
            "raw_response":    raw_text,
            "parse_error":     parse_error,
        }
