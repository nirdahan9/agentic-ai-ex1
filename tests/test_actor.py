"""Part A checks that need no API calls: sources, prompt, conversation context."""

from types import SimpleNamespace

from app import to_history
from chat.actor import build_messages, generate_answer
from chat.sources import load_background


def test_background_contains_both_sources():
    background = load_background()
    assert "LinkedIn profile" in background and "Personal summary" in background


def test_every_call_has_background_history_and_question():
    history = [
        {"role": "user", "content": "Where did you study?"},
        {"role": "assistant", "content": "Previous answer"},
    ]
    messages = build_messages("And what did you study there?", history, "BACKGROUND-TEXT")
    assert messages[0]["role"] == "system"
    assert "BACKGROUND-TEXT" in messages[0]["content"]
    assert messages[1:3] == history  # follow-up can refer to the previous answer
    assert messages[-1] == {"role": "user", "content": "And what did you study there?"}


def test_system_prompt_requires_grounding_and_missing_info_statement():
    system = build_messages("q", [], "B")[0]["content"]
    assert "background sources" in system
    assert "Never invent" in system
    assert "say so explicitly" in system
    assert "Hebrew" in system


def test_system_prompt_requires_using_history_for_follow_ups():
    system = build_messages("q", [], "B")[0]["content"]
    assert "# Conversation context" in system
    assert "answer the user's new question" in system
    assert "earlier questions or answers" in system


def test_braces_in_sources_do_not_break_prompt():
    system = build_messages("q", [], "skills: {python}")[0]["content"]
    assert "skills: {python}" in system


def test_generate_answer_sends_built_messages():
    captured = {}

    def create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=" answer "))])

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    assert generate_answer("q", [], "B", client=client, model="m") == "answer"
    assert captured["model"] == "m"
    assert captured["messages"][-1]["content"] == "q"


def test_gradio_history_keeps_only_displayed_messages():
    gradio_history = [
        {"role": "user", "content": [{"type": "text", "text": "hi"}]},
        {"role": "assistant", "content": "final answer"},
    ]
    assert to_history(gradio_history) == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "final answer"},
    ]


def test_correction_call_includes_rejected_answer_and_feedback():
    history = [{"role": "user", "content": "PREV-Q"}, {"role": "assistant", "content": "PREV-A"}]
    messages = build_messages("THE-QUESTION", history, "B",
                              rejected_answer="REJECTED-DRAFT", feedback="FIX-THIS")
    assert messages[1:3] == history
    assert messages[3] == {"role": "user", "content": "THE-QUESTION"}
    revision = messages[4]["content"]
    assert messages[4]["role"] == "user"
    assert "REJECTED-DRAFT" in revision and "FIX-THIS" in revision
    assert "{rejected_answer}" not in revision and "{feedback}" not in revision


def test_first_attempt_has_no_correction_request():
    assert len(build_messages("q", [], "B")) == 2


def test_actor_prompt_has_language_rule_and_glossary():
    system = build_messages("q", [], "B")[0]["content"]
    assert "always answer entirely in Hebrew" in system
    assert "מדעי המחשב" in system and "Keep in English" in system
    assert "{glossary}" not in system
