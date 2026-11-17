"""Part B checks that need no API calls: schema, evaluator messages, error handling."""

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from chat.evaluator import Evaluation, EvaluationError, build_messages, evaluate


def fake_client(content=None, refusal=None, error=None, stop_reason="end_turn"):
    """A stand-in for anthropic.Anthropic(): client.beta.messages.create(...)."""
    def create(**kwargs):
        if error:
            raise error
        if refusal:
            return SimpleNamespace(stop_reason="refusal", stop_details=refusal, content=[])
        blocks = [SimpleNamespace(type="thinking", thinking="")]
        if content is not None:
            blocks.append(SimpleNamespace(type="text", text=content))
        return SimpleNamespace(stop_reason=stop_reason, stop_details=None, content=blocks)

    return SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=create)))


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
    client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(
        create=lambda **kw: SimpleNamespace(stop_reason="end_turn", content=None))))
    with pytest.raises(EvaluationError):
        evaluate("q", "a", [], "b", client=client)


def test_truncated_output_raises_evaluation_error():
    with pytest.raises(EvaluationError):
        evaluate("q", "a", [], "b", client=fake_client('{"is_acceptable": tr', stop_reason="max_tokens"))


def test_evaluator_request_uses_claude_with_structured_output():
    captured = {}

    def create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(stop_reason="end_turn", content=[
            SimpleNamespace(type="text", text='{"is_acceptable": true, "feedback": "ok"}')])

    client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=create)))
    evaluate("q", "a", [], "b", client=client)
    assert captured["model"].startswith("claude-")
    schema = captured["output_config"]["format"]["schema"]
    assert schema["required"] == ["is_acceptable", "feedback"]
    assert schema["additionalProperties"] is False
    assert captured["messages"][0]["role"] == "user" and "Criteria" in captured["system"]


def test_placeholder_text_inside_materials_is_not_substituted():
    user = build_messages("my {answer} question", "THE-ANSWER", [], "bg {question}")[1]["content"]
    assert "my {answer} question" in user and "bg {question}" in user


def test_evaluator_checks_language_rule_with_glossary():
    system = build_messages("q", "a", [], "b")[0]["content"]
    assert "entirely in Hebrew, whatever the language of the question" in system
    assert "מדעי המחשב" in system and "{glossary}" not in system
