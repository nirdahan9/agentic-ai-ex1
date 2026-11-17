"""Part B checks that need no API calls: schema, evaluator messages, error handling."""

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from chat.evaluator import Evaluation, EvaluationError, build_messages, evaluate


def fake_client(content=None, refusal=None, error=None):
    def create(**kwargs):
        if error:
            raise error
        message = SimpleNamespace(content=content, refusal=refusal)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


# --- Evaluation schema -------------------------------------------------------

def test_evaluation_has_two_required_fields():
    schema = Evaluation.model_json_schema()
    assert set(schema["required"]) == {"is_acceptable", "feedback"}
    assert schema["properties"]["is_acceptable"]["type"] == "boolean"
    assert schema["properties"]["feedback"]["type"] == "string"


@pytest.mark.parametrize(
    "raw",
    [
        '{"feedback": "ok"}',                                   # missing is_acceptable
        '{"is_acceptable": true}',                              # missing feedback
        '{"is_acceptable": "true", "feedback": "ok"}',          # string, not bool
        '{"is_acceptable": "yes", "feedback": "ok"}',
        '{"is_acceptable": true, "feedback": ""}',              # empty feedback
        '{"is_acceptable": true, "feedback": "ok", "x": 1}',   # unknown field
        'The answer is acceptable.',                            # free text
    ],
)
def test_invalid_outputs_fail_validation(raw):
    with pytest.raises(ValidationError):
        Evaluation.model_validate_json(raw)


# --- Evaluator messages ------------------------------------------------------

def test_evaluator_receives_all_required_material():
    history = [
        {"role": "user", "content": "PREV-QUESTION"},
        {"role": "assistant", "content": "PREV-ANSWER"},
    ]
    system, user = build_messages("THE-QUESTION", "THE-ANSWER", history, "THE-BACKGROUND")
    assert system["role"] == "system" and user["role"] == "user"
    for part in ("THE-QUESTION", "THE-ANSWER", "THE-BACKGROUND", "PREV-QUESTION", "PREV-ANSWER"):
        assert part in user["content"]
    for placeholder in ("{background}", "{history}", "{question}", "{answer}"):
        assert placeholder not in user["content"]


def test_system_evaluator_defines_the_four_criteria():
    system = build_messages("q", "a", [], "b")[0]["content"]
    for criterion in ("Grounding in sources", "Answering the question",
                      "Handling missing information", "Clarity"):
        assert criterion in system


# --- evaluate(): decisions come only from the validated boolean --------------

def test_valid_output_is_parsed():
    client = fake_client('{"is_acceptable": false, "feedback": "Claim X is not in the sources."}')
    result = evaluate("q", "a", [], "b", client=client)
    assert result == Evaluation(is_acceptable=False, feedback="Claim X is not in the sources.")


def test_free_text_mentioning_acceptable_is_not_approval():
    with pytest.raises(EvaluationError):
        evaluate("q", "a", [], "b", client=fake_client("is_acceptable: true"))


@pytest.mark.parametrize(
    "client",
    [
        fake_client('{"is_acceptable": true}'),            # missing required field
        fake_client(None),                                 # empty output
        fake_client(None, refusal="I can't help"),         # model refusal
        fake_client(error=RuntimeError("network down")),   # failed model call
    ],
)
def test_technical_failures_raise_evaluation_error(client):
    with pytest.raises(EvaluationError):
        evaluate("q", "a", [], "b", client=client)


def test_unexpected_response_shape_raises_evaluation_error():
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
        create=lambda **kw: SimpleNamespace(choices=[]))))
    with pytest.raises(EvaluationError):
        evaluate("q", "a", [], "b", client=client)


def test_placeholder_text_inside_materials_is_not_substituted():
    user = build_messages("my {answer} question", "THE-ANSWER", [], "bg {question}")[1]["content"]
    assert "my {answer} question" in user and "bg {question}" in user
