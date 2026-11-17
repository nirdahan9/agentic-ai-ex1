"""Part D: run the five assignment scenarios and save their input, attempts log and output.

Usage:  .venv/bin/python run_scenarios.py [scenario numbers...]   (default: all)

Scenarios 1–4 use the real language models (Actor and Evaluator).
Scenario 5 is a CONTROL-FLOW TEST: the real Actor with a MOCK evaluator that rejects
every attempt. Its results are kept and reported separately from the LLM results.

Each conversation goes through the same code path as the Gradio app:
chat.loop.handle_question for each question, and app.to_history for the history.
"""

import json
import sys
from datetime import datetime, timezone

from app import to_history
from chat.check_log import append_record
from chat.config import ACTOR_MODEL, EVALUATOR_MODEL, ROOT
from chat.evaluator import Evaluation
from chat.loop import APPROVED, ATTEMPTS_EXHAUSTED, EXHAUSTED_MESSAGE, handle_question
from chat.sources import load_background

OUT_DIR = ROOT / "results" / "part_d"
LOG_PATH = OUT_DIR / "execution_log.jsonl"

MOCK_LABEL = "MOCK evaluator (control-flow test): rejects every attempt"


def mock_always_reject(question, answer, history, background) -> Evaluation:
    """Mock evaluator for scenario 5. It returns a validated Evaluation that always rejects."""
    return Evaluation(
        is_acceptable=False,
        feedback="MOCK REJECTION (control-flow test): this mock evaluator rejects every "
                 "attempt, regardless of content, to test the attempt limit.",
    )


SCENARIOS = {
    1: {
        "title": "Question about existing information",
        "kind": "LLM",
        "expected": "An approved answer that is supported by a specific detail in the sources.",
        "turns": [{"question": "איפה אתה עובד היום ומה התפקיד שלך?"}],
    },
    2: {
        "title": "Follow-up question",
        "kind": "LLM",
        "expected": "Two turns in one conversation. The second relies on the first answer "
                    "('there'), and the answer keeps the context: Reichman University, June 2027.",
        "turns": [{"question": "איפה אתה לומד?"},
                  {"question": "ומתי אתה צפוי לסיים את הלימודים שם?"}],
    },
    3: {
        "title": "Detail not in the sources",
        "kind": "LLM",
        "expected": "An answer stating there is not enough information (the GPA is not in "
                    "the sources), with no invented personal fact. It is approved.",
        "turns": [{"question": "מה הממוצע שלך בתואר?"}],
    },
    4: {
        "title": "Rejection and improvement",
        "kind": "LLM (injected flawed first draft)",
        "expected": "The injected draft with an invented personal fact is rejected with a "
                    "reasoned feedback. The Actor's corrected version is evaluated again "
                    "and approved.",
        "turns": [{
            "question": "איפה עבדת לפני Via.AI?",
            "first_draft": "לפני Via.AI עבדתי שנתיים כמפתח Backend ב־Wix, ושם הובלתי את "
                           "המעבר לארכיטקטורת מיקרו־שירותים.",
        }],
    },
    5: {
        "title": "Exhausting the attempts",
        "kind": "MOCK (control-flow test)",
        "expected": "Three attempts, all rejected, then a stop after the third and the "
                    "'no approved answer' message. No rejected answer is shown.",
        "turns": [{"question": "מה GroupShield?", "mock_evaluator": True}],
    },
}


def run_scenario(number: int, background: str) -> dict:
    spec = SCENARIOS[number]
    scenario_id = f"scenario-{number}"
    shown: list[dict] = []          # what the Gradio chat would display
    turns = []
    for turn in spec["turns"]:
        history = to_history(shown)
        kwargs = {}
        if turn.get("first_draft"):
            kwargs["first_draft"] = turn["first_draft"]
        if turn.get("mock_evaluator"):
            kwargs["evaluator"] = mock_always_reject
            kwargs["evaluator_label"] = MOCK_LABEL
        outcome = handle_question(turn["question"], history, background, scenario_id, **kwargs)
        append_record(outcome.record, LOG_PATH)
        shown += [{"role": "user", "content": turn["question"]},
                  {"role": "assistant", "content": outcome.reply}]
        turns.append({
            "input": {"question": turn["question"], "history_sent_to_models": history,
                      **({"injected_first_draft": turn["first_draft"]} if turn.get("first_draft") else {})},
            "attempts_log": outcome.record["attempts"],
            "final_status": outcome.status,
            "shown_to_user": outcome.reply,
        })
    return {
        "scenario": number,
        "scenario_id": scenario_id,
        "title": spec["title"],
        "kind": spec["kind"],
        "actor_model": ACTOR_MODEL,
        "evaluator": MOCK_LABEL if spec["kind"].startswith("MOCK") else EVALUATOR_MODEL,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "expected": spec["expected"],
        "turns": turns,
        "displayed_conversation": shown,
        "automatic_check": automatic_check(number, turns),
    }


def automatic_check(number: int, turns: list[dict]) -> dict:
    """Mechanical checks of the expected flow. Content is reviewed by hand in part_d_results.md."""
    t = turns[-1]
    attempts = t["attempts_log"]
    if number in (1, 2, 3):
        ok = all(x["final_status"] == APPROVED for x in turns)
        detail = "every turn ended approved" if ok else "a turn did not end approved"
    elif number == 4:
        first, last = attempts[0], attempts[-1]
        ok = (first.get("candidate_source") == "injected_test_draft"
              and first["evaluation"].get("is_acceptable") is False
              and len(attempts) >= 2 and t["final_status"] == APPROVED
              and last["candidate_source"] == "actor_correction")
        detail = ("injected draft rejected, then a corrected version approved" if ok else
                  "flow differs: the injected draft was approved, or no corrected version was approved")
    else:
        ok = (t["final_status"] == ATTEMPTS_EXHAUSTED and len(attempts) == 3
              and all(a["evaluation"].get("is_acceptable") is False for a in attempts)
              and t["shown_to_user"] == EXHAUSTED_MESSAGE)
        detail = ("3 rejected attempts, then a stop with the exhausted message" if ok
                  else "flow differs from expected")
    return {"flow_as_expected": ok, "detail": detail}


def main(numbers: list[int]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    background = load_background()
    for n in numbers:
        result = run_scenario(n, background)
        path = OUT_DIR / f"scenario_{n}.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        check = result["automatic_check"]
        print(f"scenario {n} [{result['kind']}]: {result['turns'][-1]['final_status']} "
              f"({len(result['turns'][-1]['attempts_log'])} attempts) — "
              f"{'OK' if check['flow_as_expected'] else 'MISMATCH'}: {check['detail']}")


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or sorted(SCENARIOS))
