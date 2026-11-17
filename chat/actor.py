"""Actor (answer generator): builds the request and calls the language model."""

from openai import OpenAI

from chat.config import ACTOR_MODEL, PERSON_NAME, PROMPTS_DIR


def actor_system_prompt(background: str) -> str:
    """The Actor system prompt with the background sources embedded."""
    template = (PROMPTS_DIR / "actor_system.md").read_text(encoding="utf-8")
    # str.replace (not str.format) so braces inside the sources are left untouched.
    return template.replace("{name}", PERSON_NAME).replace("{background}", background)


def build_messages(question: str, history: list[dict], background: str) -> list[dict]:
    """Every Actor call gets: background sources, conversation history, user question.

    `history` holds only what the user saw: their messages and the final answers.
    """
    messages = [{"role": "system", "content": actor_system_prompt(background)}]
    messages += [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": question})
    return messages


def generate_answer(
    question: str,
    history: list[dict],
    background: str,
    client: OpenAI | None = None,
    model: str = ACTOR_MODEL,
) -> str:
    """Produce a candidate answer for the user's question."""
    client = client or OpenAI()
    response = client.chat.completions.create(
        model=model, messages=build_messages(question, history, background)
    )
    return response.choices[0].message.content.strip()
