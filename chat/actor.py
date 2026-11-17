"""Actor (answer generator): builds the request and calls the language model."""

from openai import OpenAI

from chat.config import ACTOR_MODEL, PERSON_NAME, PROMPTS_DIR


def actor_system_prompt(background: str) -> str:
    """The Actor system prompt with the background sources embedded."""
    template = (PROMPTS_DIR / "actor_system.md").read_text(encoding="utf-8")
    # str.replace (not str.format) so braces inside the sources are left untouched.
    return template.replace("{name}", PERSON_NAME).replace("{background}", background)


def revision_request(rejected_answer: str, feedback: str) -> str:
    """Correction request: the rejected answer and the evaluator's feedback."""
    template = (PROMPTS_DIR / "actor_revision.md").read_text(encoding="utf-8")
    # Split on the first placeholder so text inside the answer is never substituted.
    head, tail = template.split("{rejected_answer}", 1)
    return head + rejected_answer + tail.replace("{feedback}", feedback, 1)


def build_messages(
    question: str,
    history: list[dict],
    background: str,
    rejected_answer: str | None = None,
    feedback: str | None = None,
) -> list[dict]:
    """Every Actor call gets: background sources, conversation history, user question.

    `history` is the conversation so far: user messages and approved answers (questions that
    ended without an approved answer are left out, see app.to_history).
    On a correction attempt, the rejected answer and the feedback are added after the question.
    """
    messages = [{"role": "system", "content": actor_system_prompt(background)}]
    messages += [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": question})
    if rejected_answer is not None:
        messages.append({"role": "user", "content": revision_request(rejected_answer, feedback or "")})
    return messages


def generate_answer(
    question: str,
    history: list[dict],
    background: str,
    rejected_answer: str | None = None,
    feedback: str | None = None,
    client: OpenAI | None = None,
    model: str = ACTOR_MODEL,
) -> str:
    """Produce a candidate answer (or a corrected one, when given a rejected answer + feedback)."""
    client = client or OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=build_messages(question, history, background, rejected_answer, feedback),
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise ValueError("actor returned an empty answer")
    return content.strip()
