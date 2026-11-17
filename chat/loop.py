"""Generate → evaluate → correct loop for one user question (at most MAX_ATTEMPTS)."""

from dataclasses import dataclass
from typing import Callable

from chat.actor import generate_answer
from chat.config import ACTOR_MODEL, EVALUATOR_MODEL
from chat.evaluator import Evaluation, EvaluationError, evaluate

MAX_ATTEMPTS = 3  # generation attempts per question, including the first answer

APPROVED = "approved"
ATTEMPTS_EXHAUSTED = "attempts_exhausted"
TECHNICAL_ERROR = "technical_error"

# Messages shown to the user when no approved answer is available (Hebrew UI).
EXHAUSTED_MESSAGE = (
    "לא התקבלה תשובה מאושרת במסגרת מגבלת שלושת הניסיונות. "
    "אפשר לנסח את השאלה מחדש או לשאול שאלה אחרת."
)
ERROR_MESSAGE = (
    "אירעה שגיאה טכנית והטיפול בשאלה הופסק, ולכן לא ניתן להציג תשובה. "
    "אפשר לנסות שוב בעוד רגע."
)
SYSTEM_MESSAGES = (EXHAUSTED_MESSAGE, ERROR_MESSAGE)


@dataclass
class Outcome:
    status: str          # APPROVED | ATTEMPTS_EXHAUSTED | TECHNICAL_ERROR
    reply: str           # what the user sees: the approved answer or a status message
    record: dict         # the execution-log record for this question


def handle_question(
    question: str,
    history: list[dict],
    background: str,
    scenario_id: str,
    actor: Callable[..., str] = generate_answer,
    evaluator: Callable[..., Evaluation] = evaluate,
    first_draft: str | None = None,
    actor_model: str = ACTOR_MODEL,
    evaluator_label: str = EVALUATOR_MODEL,
) -> Outcome:
    """Run the loop for one question. The attempt counter starts at 1 for every question.

    `history` is the conversation shown so far (user messages + approved answers).
    `first_draft` optionally replaces the Actor's first answer with a given test draft
    (controlled test, Part D scenario 4); the evaluator and later corrections still run.
    """
    record = {
        "scenario_id": scenario_id,
        "question": question,
        "actor_model": actor_model,
        "evaluator": evaluator_label,
        "final_status": None,
        "attempts": [],
    }

    def finish(status: str, reply: str, error: str | None = None) -> Outcome:
        record["final_status"] = status
        record["shown_to_user"] = reply
        if error:
            record["error"] = error
        return Outcome(status, reply, record)

    rejected_answer = feedback = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        entry = {"attempt": attempt}
        record["attempts"].append(entry)

        # 1 / 4: generate a candidate (a corrected one after a rejection).
        if attempt == 1 and first_draft is not None:
            candidate, entry["candidate_source"] = first_draft, "injected_test_draft"
        else:
            try:
                candidate = actor(question, history, background,
                                  rejected_answer=rejected_answer, feedback=feedback)
            except Exception as e:
                entry["candidate"] = None
                entry["evaluation"] = {"completed": False, "reason": "no candidate: actor call failed"}
                return finish(TECHNICAL_ERROR, ERROR_MESSAGE, f"actor call failed: {type(e).__name__}: {e}")
            entry["candidate_source"] = "actor" if attempt == 1 else "actor_correction"
        entry["candidate"] = candidate

        # 2: evaluate; the output is validated against Evaluation inside the evaluator.
        try:
            result = evaluator(question, candidate, history, background)
        except Exception as e:  # EvaluationError (call/parse/validation) or any other failure
            reason = str(e) if isinstance(e, EvaluationError) else f"{type(e).__name__}: {e}"
            entry["evaluation"] = {"completed": False, "reason": reason}
            return finish(TECHNICAL_ERROR, ERROR_MESSAGE, f"evaluation not completed: {reason}")
        entry["evaluation"] = {"completed": True, "is_acceptable": result.is_acceptable,
                               "feedback": result.feedback}

        # 3: approved → show it and stop.
        if result.is_acceptable:
            return finish(APPROVED, candidate)

        # 4: rejected → the next attempt gets the rejected answer and the feedback.
        rejected_answer, feedback = candidate, result.feedback

    # 5: the third answer was rejected too.
    return finish(ATTEMPTS_EXHAUSTED, EXHAUSTED_MESSAGE)
