"""Part B: evaluator checks with the real models (paid API calls).

Usage:  .venv/bin/python run_evaluator_checks.py

1. Actor runs: the Actor answers six profile questions (fresh conversations, one attempt each)
   and the Evaluator judges each answer. Approved answers are then checked by hand against
   the sources (results/part_b_manual_check.md).
2. Controlled tests: hand-written candidate answers, each targeting one criterion.

Output: results/part_b_evaluator_runs.json, results/part_b_controlled_tests.json
"""

import json

from chat.actor import generate_answer
from chat.config import ACTOR_MODEL, EVALUATOR_MODEL, ROOT
from chat.evaluator import evaluate
from chat.sources import load_background

RESULTS = ROOT / "results"

ACTOR_QUESTIONS = [
    "ספר לי על הניסיון הצבאי שלך",
    "אילו שפות תכנות וכלים אתה מכיר?",
    "ספר לי על DerbyUp",
    "מה אתה לומד ואיפה?",
    "מה GroupShield?",
    "איזה סוג עבודה אתה מחפש?",
]

ARMY_Q = "מה עשית בצבא?"
CONTROLLED = [
    ("grounded", "accept", "איפה אתה עובד היום?", [],
     "אני עובד היום ב־Via.AI בתפקיד מהנדס QA, ובודק מוצרי תיירות מבוססי בינה מלאכותית בבדיקות ידניות ואוטומטיות."),
    ("fabricated", "reject (A)", "איפה אתה עובד היום?", [],
     "אני עובד ב־Via.AI כראש צוות QA של 6 אנשים מאז 2025, ולפני כן עבדתי שנתיים ב־Google."),
    ("missing-info", "accept (C)", "מה הממוצע שלך בתואר?", [],
     "המקורות שלי לא מציינים את הממוצע שלי בתואר, ולכן אני לא יכול למסור אותו."),
    ("off-topic", "reject (B)", ARMY_Q, [],
     "אני סטודנט למדעי המחשב באוניברסיטת רייכמן."),
    ("follow-up", "accept (B, context)", "וכמה זמן שירתת?",
     [{"role": "user", "content": ARMY_Q},
      {"role": "assistant", "content": "שירתתי כקצין לוגיסטיקה בצה״ל."}],
     "שירתתי חמש שנים, מאוגוסט 2019 עד יולי 2024."),
]


def main() -> None:
    background = load_background()

    runs = []
    for q in ACTOR_QUESTIONS:
        answer = generate_answer(q, [], background)
        result = evaluate(q, answer, [], background)
        runs.append({"question": q, "answer": answer, "actor_model": ACTOR_MODEL,
                     "evaluator_model": EVALUATOR_MODEL, **result.model_dump()})
        print(f"[actor run] {result.is_acceptable!s:5} | {q}")
    (RESULTS / "part_b_evaluator_runs.json").write_text(
        json.dumps(runs, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    controlled = []
    for name, expected, q, history, answer in CONTROLLED:
        result = evaluate(q, answer, history, background)
        controlled.append({"case": name, "expected": expected, "question": q, "history": history,
                           "candidate_answer": answer, "evaluator_model": EVALUATOR_MODEL,
                           **result.model_dump()})
        print(f"[controlled] {name:12} expected {expected:20} -> is_acceptable={result.is_acceptable}")
    (RESULTS / "part_b_controlled_tests.json").write_text(
        json.dumps(controlled, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
