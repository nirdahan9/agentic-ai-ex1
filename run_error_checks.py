"""Technical-error exit (Part C, step 6): three runs through the real loop.

Usage:  .venv/bin/python run_error_checks.py

1. error-actor-call-fails          — real call: the Actor uses an invalid OpenAI key (401).
2. error-evaluator-call-fails      — real call: the Evaluator asks for a Claude model that does not exist (404).
3. error-evaluator-invalid-output  — MOCK: the Evaluator returns {"is_acceptable": true} without `feedback`.

Output: results/technical_error_runs.jsonl
"""

import json
from types import SimpleNamespace

import anthropic
from openai import OpenAI

from chat.actor import generate_answer
from chat.config import ROOT
from chat.evaluator import evaluate
from chat.loop import handle_question
from chat.sources import load_background

OUT = ROOT / "results" / "technical_error_runs.jsonl"


def main() -> None:
    background = load_background()
    bad_openai = OpenAI(api_key="invalid-key-for-error-test")
    mock_claude = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(
        create=lambda **kw: SimpleNamespace(stop_reason="end_turn", content=[
            SimpleNamespace(type="text", text='{"is_acceptable": true}')]))))

    runs = [
        handle_question(
            "מה אתה לומד?", [], background, "error-actor-call-fails",
            actor=lambda q, h, b, **kw: generate_answer(q, h, b, client=bad_openai, **kw)),
        handle_question(
            "איפה אתה עובד היום?", [], background, "error-evaluator-call-fails",
            evaluator=lambda q, a, h, b: evaluate(q, a, h, b, model="claude-does-not-exist"),
            evaluator_label="claude-does-not-exist"),
        handle_question(
            "ספר לי על GroupShield", [], background, "error-evaluator-invalid-output",
            evaluator=lambda q, a, h, b: evaluate(q, a, h, b, client=mock_claude),
            evaluator_label='MOCK (simulated): returns {"is_acceptable": true} without feedback'),
    ]
    with OUT.open("w", encoding="utf-8") as f:
        for out in runs:
            f.write(json.dumps(out.record, ensure_ascii=False) + "\n")
            print(f"{out.record['scenario_id']:32} {out.status:16} {out.record.get('error', '')[:110]}")


if __name__ == "__main__":
    main()
