"""
app.py — Streamlit UI for the Consensus Engine.

Tab 1: Run a new debate — text input + "Run Debate" button
        Shows 3 persona outputs side-by-side + judge verdict + agreement score

Tab 2: History — table of all logged runs from data/runs.jsonl,
        sortable by agreement_score (lowest first to see most disagreement)

Run with:
  streamlit run app.py
"""

import sys
import os
import json
import time



import streamlit as st

# Page config
st.set_page_config(
    page_title="Consensus Engine",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Global CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark gradient background */
.stApp {
    background: linear-gradient(135deg, #0d0d1a 0%, #111827 40%, #0d1b2a 100%);
    color: #e2e8f0;
}

/* Header */
.ce-header {
    text-align: center;
    padding: 2.5rem 0 1.5rem;
}
.ce-header h1 {
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(90deg, #818cf8, #c084fc, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    letter-spacing: -0.03em;
}
.ce-header p {
    color: #94a3b8;
    font-size: 1.1rem;
    margin-top: 0.5rem;
}

/* Persona cards */
.persona-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 1.4rem;
    height: 100%;
    backdrop-filter: blur(8px);
    transition: border-color 0.2s;
}
.persona-card:hover {
    border-color: rgba(129,140,248,0.4);
}
.persona-name {
    font-size: 0.9rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}
.fp-color  { color: #818cf8; }
.an-color  { color: #34d399; }
.ad-color  { color: #f87171; }

.confidence-badge {
    display: inline-block;
    background: rgba(255,255,255,0.08);
    border-radius: 999px;
    padding: 0.15rem 0.7rem;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 0.8rem;
}
.step-item {
    font-size: 0.82rem;
    color: #cbd5e1;
    margin-bottom: 0.4rem;
    padding-left: 0.6rem;
    border-left: 2px solid rgba(255,255,255,0.15);
}
.assumption-item {
    font-size: 0.8rem;
    color: #94a3b8;
    font-style: italic;
}
.answer-box {
    background: rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin-top: 0.8rem;
    font-size: 0.9rem;
    line-height: 1.6;
    color: #e2e8f0;
}

/* Judge verdict */
.judge-card {
    background: linear-gradient(135deg, rgba(129,140,248,0.08), rgba(196,132,252,0.08));
    border: 1px solid rgba(129,140,248,0.25);
    border-radius: 20px;
    padding: 1.8rem 2rem;
    margin-top: 1.5rem;
}
.judge-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #c084fc;
    margin-bottom: 1rem;
}
.agreement-meter {
    margin: 1rem 0 1.5rem;
}
.disagreement-item {
    background: rgba(248,113,113,0.08);
    border-left: 3px solid #f87171;
    border-radius: 0 8px 8px 0;
    padding: 0.5rem 0.8rem;
    font-size: 0.85rem;
    color: #fca5a5;
    margin-bottom: 0.4rem;
}
.synthesis-box {
    background: rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    font-size: 0.95rem;
    line-height: 1.7;
    color: #e2e8f0;
    border: 1px solid rgba(255,255,255,0.06);
}

/* Run button */
.stButton > button {
    background: linear-gradient(90deg, #818cf8, #c084fc);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.7rem 2.5rem;
    font-size: 1.05rem;
    font-weight: 600;
    letter-spacing: 0.01em;
    cursor: pointer;
    transition: opacity 0.2s, transform 0.1s;
    width: 100%;
}
.stButton > button:hover {
    opacity: 0.9;
    transform: translateY(-1px);
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: transparent;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 8px 8px 0 0;
    color: #94a3b8;
    font-weight: 500;
    padding: 0.6rem 1.5rem;
}
.stTabs [aria-selected="true"] {
    background: rgba(129,140,248,0.12) !important;
    color: #818cf8 !important;
    border-bottom: 2px solid #818cf8;
}

/* Text input */
.stTextArea textarea {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextArea textarea:focus {
    border-color: rgba(129,140,248,0.5) !important;
    box-shadow: 0 0 0 3px rgba(129,140,248,0.1) !important;
}

/* Dataframe */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
}

/* Parse error warning */
.parse-error {
    background: rgba(251,191,36,0.1);
    border: 1px solid rgba(251,191,36,0.3);
    border-radius: 8px;
    padding: 0.5rem 0.8rem;
    font-size: 0.8rem;
    color: #fbbf24;
    margin-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)


# Helper imports (after path setup)
from orchestrator import run_debate
from judge import judge_debate
from logger import append_run, load_all_runs

PERSONA_COLORS = {
    "first_principles": ("fp-color",  "🔵", "#818cf8"),
    "analogical":       ("an-color",  "🟢", "#34d399"),
    "adversarial":      ("ad-color",  "🔴", "#f87171"),
}


# Header
st.markdown("""
<div class="ce-header">
  <h1>⚖️ Consensus Engine</h1>
  <p>Multi-persona LLM debate — does disagreement produce better answers?</p>
</div>
""", unsafe_allow_html=True)


# Tabs
tab_debate, tab_history = st.tabs(["🧠 Run Debate", "📊 History"])


# TAB 1: Run Debate
with tab_debate:
    st.markdown("### Ask a question")
    st.markdown(
        "<p style='color:#94a3b8;font-size:0.9rem;'>Three reasoning personas will debate it, "
        "then a judge synthesises the best answer.</p>",
        unsafe_allow_html=True,
    )

    question = st.text_area(
        label="question_input",
        label_visibility="collapsed",
        placeholder="e.g. Should a company prioritise speed or quality when shipping software?",
        height=100,
        key="question_input",
    )

    run_col, _ = st.columns([1, 3])
    with run_col:
        run_btn = st.button("⚡ Run Debate", key="run_btn", use_container_width=True)

    if run_btn:
        if not question.strip():
            st.warning("Please enter a question first.")
        else:
            # Run pipeline
            with st.spinner("Consulting personas…"):
                progress = st.progress(0, text="Starting debate…")

                progress.progress(10, text="First-Principles Reasoner thinking…")
                persona_outputs = run_debate(question)
                progress.progress(70, text="Personas done — running judge…")

                judge_output = judge_debate(question, persona_outputs)
                progress.progress(90, text="Logging result…")

                append_run(question, persona_outputs, judge_output)
                progress.progress(100, text="Done!")
                time.sleep(0.4)
                progress.empty()

            st.success("Debate complete!", icon="✅")

            # Persona outputs side-by-side
            st.markdown("#### 🗣️ Persona Responses")
            cols = st.columns(3)

            for col, output in zip(cols, persona_outputs):
                pid   = output["persona_id"]
                color_class, icon, hex_color = PERSONA_COLORS.get(
                    pid, ("fp-color", "⚪", "#94a3b8")
                )

                with col:
                    parsed = output.get("parsed") or {}
                    confidence = parsed.get("confidence", "?")

                    st.markdown(f"""
                    <div class="persona-card">
                      <div class="persona-name {color_class}">{icon} {output['persona_name']}</div>
                      <div class="confidence-badge">Confidence: {confidence}/100</div>
                    """, unsafe_allow_html=True)

                    if output.get("parse_error"):
                        st.markdown(
                            f'<div class="parse-error">⚠ Parse error: {output["parse_error"]}</div>',
                            unsafe_allow_html=True,
                        )
                        with st.expander("Raw response"):
                            st.text(output.get("raw_response", ""))
                    else:
                        # Assumptions
                        with st.expander(f"Assumptions ({len(parsed.get('assumptions', []))})"):
                            for a in parsed.get("assumptions", []):
                                st.markdown(
                                    f'<div class="assumption-item">• {a}</div>',
                                    unsafe_allow_html=True,
                                )

                        # Reasoning steps
                        with st.expander(f"Reasoning ({len(parsed.get('reasoning_steps', []))} steps)"):
                            for i, step in enumerate(parsed.get("reasoning_steps", []), 1):
                                st.markdown(
                                    f'<div class="step-item"><strong>{i}.</strong> {step}</div>',
                                    unsafe_allow_html=True,
                                )

                        # Answer
                        st.markdown(
                            f'<div class="answer-box"><strong>Answer:</strong><br>{parsed.get("answer", "")}</div>',
                            unsafe_allow_html=True,
                        )

                    st.markdown("</div>", unsafe_allow_html=True)

            # Judge verdict
            st.markdown("#### ⚖️ Judge Verdict")

            score = judge_output.get("agreement_score", 0)
            # Colour the score bar
            if score >= 75:
                bar_color = "#34d399"
                label = "High agreement"
            elif score >= 50:
                bar_color = "#fbbf24"
                label = "Moderate agreement"
            else:
                bar_color = "#f87171"
                label = "Low agreement — significant divergence"

            st.markdown(f"""
            <div class="judge-card">
              <div class="judge-title">⚖️ Judge Synthesis</div>
              <div class="agreement-meter">
                <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.4rem;">
                  <span style="font-size:0.85rem;color:#94a3b8;">Agreement Score</span>
                  <span style="font-size:1.6rem;font-weight:800;color:{bar_color};">{score}<span style="font-size:1rem;color:#94a3b8;">/100</span></span>
                  <span style="font-size:0.8rem;color:{bar_color};background:rgba(255,255,255,0.05);padding:0.2rem 0.6rem;border-radius:999px;">{label}</span>
                </div>
            """, unsafe_allow_html=True)

            st.progress(score / 100)

            st.markdown("</div>", unsafe_allow_html=True)  # close agreement-meter

            if judge_output.get("parse_error"):
                st.markdown(
                    f'<div class="parse-error">⚠ Judge parse error: {judge_output["parse_error"]}</div>',
                    unsafe_allow_html=True,
                )

            disagreements = judge_output.get("disagreements", [])
            if disagreements:
                st.markdown(f"**Points of Disagreement ({len(disagreements)}):**")
                for d in disagreements:
                    st.markdown(
                        f'<div class="disagreement-item">✗ {d}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown("*No substantive disagreements identified.*")

            st.markdown(
                f'<div class="synthesis-box"><strong>Synthesis:</strong><br><br>{judge_output.get("synthesis", "")}</div>',
                unsafe_allow_html=True,
            )

            st.markdown("</div>", unsafe_allow_html=True)  # close judge-card


# TAB 2: History
with tab_history:
    st.markdown("### 📊 Run History")
    st.markdown(
        "<p style='color:#94a3b8;font-size:0.9rem;'>"
        "All logged debate runs, sortable by agreement score. "
        "Low scores = personas diverged most on that question.</p>",
        unsafe_allow_html=True,
    )

    if st.button("🔄 Refresh", key="refresh_btn"):
        st.rerun()

    runs = load_all_runs()

    if not runs:
        st.info("No runs logged yet. Run a debate in the first tab or execute batch_runner.py.")
    else:
        import pandas as pd

        # Build display table
        rows = []
        for run in runs:
            jo = run.get("judge_output", {})
            po = run.get("persona_outputs", [])
            parse_errors = sum(1 for p in po if p.get("parse_error"))
            parse_errors += (1 if jo.get("parse_error") else 0)
            rows.append({
                "Timestamp":       run.get("timestamp", "")[:19].replace("T", " "),
                "Question":        run.get("question", ""),
                "Agreement Score": jo.get("agreement_score", 0),
                "Disagreements":   len(jo.get("disagreements", [])),
                "Parse Errors":    parse_errors,
                "Synthesis (preview)": (jo.get("synthesis", "") or "")[:120] + "…",
            })

        df = pd.DataFrame(rows)

        # Sort controls
        sort_col, sort_dir_col = st.columns([2, 1])
        with sort_col:
            sort_by = st.selectbox(
                "Sort by",
                ["Agreement Score", "Timestamp", "Disagreements"],
                key="sort_by",
            )
        with sort_dir_col:
            ascending = st.selectbox(
                "Order",
                ["Ascending ↑", "Descending ↓"],
                key="sort_dir",
            ) == "Ascending ↑"

        df_sorted = df.sort_values(sort_by, ascending=ascending).reset_index(drop=True)

        # Colour-code agreement score
        def highlight_score(val):
            if isinstance(val, (int, float)):
                if val < 40:
                    return "color: #f87171; font-weight: 700"
                elif val < 70:
                    return "color: #fbbf24; font-weight: 600"
                else:
                    return "color: #34d399; font-weight: 600"
            return ""

        st.dataframe(
            df_sorted.style.map(highlight_score, subset=["Agreement Score"]),
            use_container_width=True,
            height=500,
        )

        st.markdown(
            f"<p style='color:#64748b;font-size:0.8rem;'>"
            f"Showing {len(df_sorted)} runs | "
            f"Avg agreement: {df['Agreement Score'].mean():.1f} | "
            f"Min: {df['Agreement Score'].min()} | Max: {df['Agreement Score'].max()}"
            f"</p>",
            unsafe_allow_html=True,
        )

        # Detail expander for each run
        st.markdown("#### Run Details")
        for i, run in enumerate(
            sorted(runs, key=lambda r: r.get("judge_output", {}).get("agreement_score", 0),
                   reverse=(not ascending))
        ):
            jo = run.get("judge_output", {})
            score = jo.get("agreement_score", 0)
            q = run.get("question", "")
            label_color = "#f87171" if score < 40 else "#fbbf24" if score < 70 else "#34d399"

            with st.expander(
                f"[{score}/100] {q[:80]}{'…' if len(q) > 80 else ''}",
            ):
                st.markdown(
                    f"<span style='color:{label_color};font-weight:700;font-size:1.3rem;'>"
                    f"{score}/100</span> agreement",
                    unsafe_allow_html=True,
                )
                disagrees = jo.get("disagreements", [])
                if disagrees:
                    st.markdown("**Disagreements:**")
                    for d in disagrees:
                        st.markdown(f"- {d}")
                st.markdown("**Synthesis:**")
                st.markdown(jo.get("synthesis", "*No synthesis available*"))
