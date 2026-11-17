"""Part C: the generate → evaluate → correct loop, with fake Actor/Evaluator (no API calls)."""

import pytest

from app import to_history
from chat.evaluator import Evaluation, EvaluationError
from chat.loop import (APPROVED, ATTEMPTS_EXHAUSTED, ERROR_MESSAGE, EXHAUSTED_MESSAGE,
                       MAX_ATTEMPTS, TECHNICAL_ERROR, handle_question)


class FakeActor:
    def __init__(self, error_on_call=None):
        self.calls, self.error_on_call = [], error_on_call

    def __call__(self, question, history, background, rejected_answer=None, feedback=None):
        self.calls.append({"rejected_answer": rejected_answer, "feedback": feedback,
                           "history": history, "question": question, "background": background})
        if self.error_on_call == len(self.calls):
            raise RuntimeError("API down")
        return f"draft-{len(self.calls)}"


class FakeEvaluator:
    """Returns the given decisions in order; an exception in the list is raised."""

    def __init__(self, *decisions):
        self.decisions, self.seen = list(decisions), []

    def __call__(self, question, answer, history, background):
        self.seen.append(answer)
        d = self.decisions.pop(0)
        if isinstance(d, Exception):
            raise d
        return Evaluation(is_acceptable=d, feedback=f"feedback on {answer}")


def run(actor, evaluator, **kw):
    return handle_question("שאלה", [{"role": "user", "content": "h"}], "BG", "S1",
                           actor=actor, evaluator=evaluator, **kw)


def test_max_attempts_is_three():
    assert MAX_ATTEMPTS == 3


def test_approved_on_first_attempt():
    actor, ev = FakeActor(), FakeEvaluator(True)
    out = run(actor, ev)
    assert out.status == APPROVED and out.reply == "draft-1"
    assert len(out.record["attempts"]) == 1 and len(actor.calls) == 1
    assert actor.calls[0]["rejected_answer"] is None  # first attempt: no correction input


def test_rejection_sends_rejected_answer_and_feedback_to_next_attempt():
    actor, ev = FakeActor(), FakeEvaluator(False, True)
    out = run(actor, ev)
    assert out.status == APPROVED and out.reply == "draft-2"
    second = actor.calls[1]
    assert second["rejected_answer"] == "draft-1"
    assert second["feedback"] == "feedback on draft-1"
    assert second["question"] == "שאלה" and second["background"] == "BG"
    assert second["history"] == [{"role": "user", "content": "h"}]
    assert ev.seen == ["draft-1", "draft-2"]  # every new answer is re-evaluated


def test_three_rejections_exhaust_attempts_and_show_no_rejected_answer():
    actor, ev = FakeActor(), FakeEvaluator(False, False, False)
    out = run(actor, ev)
    assert out.status == ATTEMPTS_EXHAUSTED and out.reply == EXHAUSTED_MESSAGE
    assert len(actor.calls) == 3 and len(ev.seen) == 3
    assert out.reply not in ("draft-1", "draft-2", "draft-3")
    attempts = out.record["attempts"]
    assert [a["candidate"] for a in attempts] == ["draft-1", "draft-2", "draft-3"]
    assert all(a["evaluation"] == {"completed": True, "is_acceptable": False,
                                   "feedback": f"feedback on draft-{i}"}
               for i, a in enumerate(attempts, 1))
    assert actor.calls[2]["rejected_answer"] == "draft-2"


def test_evaluation_failure_stops_with_error_and_no_decision():
    actor, ev = FakeActor(), FakeEvaluator(False, EvaluationError("invalid evaluation output"))
    out = run(actor, ev)
    assert out.status == TECHNICAL_ERROR and out.reply == ERROR_MESSAGE
    assert len(actor.calls) == 2  # stopped; no third attempt
    last = out.record["attempts"][-1]
    assert last["evaluation"]["completed"] is False and "is_acceptable" not in last["evaluation"]
    assert "evaluation not completed" in out.record["error"]


def test_unexpected_evaluator_exception_is_a_technical_error():
    out = run(FakeActor(), FakeEvaluator(ValueError("boom")))
    assert out.status == TECHNICAL_ERROR


def test_actor_failure_stops_with_error():
    actor, ev = FakeActor(error_on_call=2), FakeEvaluator(False)
    out = run(actor, ev)
    assert out.status == TECHNICAL_ERROR and out.reply == ERROR_MESSAGE
    assert out.record["attempts"][-1]["candidate"] is None
    assert out.record["attempts"][-1]["evaluation"]["completed"] is False
    assert "actor call failed" in out.record["error"]


def test_injected_first_draft_is_evaluated_and_then_corrected_by_actor():
    actor, ev = FakeActor(), FakeEvaluator(False, True)
    out = run(actor, ev, first_draft="FLAWED")
    assert ev.seen[0] == "FLAWED"
    assert out.record["attempts"][0]["candidate_source"] == "injected_test_draft"
    assert actor.calls[0]["rejected_answer"] == "FLAWED"
    assert out.status == APPROVED and out.reply == "draft-1"


def test_record_has_required_log_fields():
    out = run(FakeActor(), FakeEvaluator(True))
    r = out.record
    assert r["scenario_id"] == "S1" and r["question"] == "שאלה" and r["final_status"] == APPROVED
    a = r["attempts"][0]
    assert {"attempt", "candidate", "evaluation"} <= a.keys()


def test_each_question_starts_a_fresh_counter():
    ev = FakeEvaluator(False, False, False, True)
    first = run(FakeActor(), ev)
    second = run(FakeActor(), ev)
    assert first.status == ATTEMPTS_EXHAUSTED
    assert second.status == APPROVED and second.record["attempts"][0]["attempt"] == 1


@pytest.mark.parametrize("notice", [EXHAUSTED_MESSAGE, ERROR_MESSAGE])
def test_history_keeps_approved_answers_and_drops_unanswered_questions(notice):
    shown = [
        {"role": "user", "content": "q1"}, {"role": "assistant", "content": "approved-1"},
        {"role": "user", "content": "q2"}, {"role": "assistant", "content": notice},
        {"role": "user", "content": "q3"}, {"role": "assistant", "content": "approved-3"},
    ]
    assert to_history(shown) == [
        {"role": "user", "content": "q1"}, {"role": "assistant", "content": "approved-1"},
        {"role": "user", "content": "q3"}, {"role": "assistant", "content": "approved-3"},
    ]


def test_status_messages_are_hebrew_even_for_english_questions():
    out = handle_question("Where do you work?", [], "BG", "S", actor=FakeActor(),
                          evaluator=FakeEvaluator(False, False, False))
    assert out.reply == EXHAUSTED_MESSAGE
