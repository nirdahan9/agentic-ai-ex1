"""Evaluator (Critic): checks a candidate answer and returns a validated Evaluation."""

import re

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from chat.config import EVALUATOR_MODEL, PERSON_NAME, PROMPTS_DIR


class Evaluation(BaseModel):
    """Structured evaluation result. Both fields are required."""

    # strict: no coercion (e.g. the string "true" is not accepted as a bool);
    # forbid: unknown fields are rejected.
    model_config = ConfigDict(strict=True, extra="forbid")

    is_acceptable: bool = Field(description="Whether the answer meets all the criteria.")
    feedback: str = Field(
        min_length=1,
        description="Short justification; on rejection, the problem and a practical fix.",
    )


class EvaluationError(Exception):
    """Technical failure: the evaluation was not completed (no content decision)."""


def _fill(template: str, **values: str) -> str:
    # Single pass over the template only, so braces or placeholder-like text inside
    # the materials (sources, question, answer) are never substituted.
    return re.sub(r"\{(\w+)\}", lambda m: values.get(m.group(1), m.group(0)), template)


def format_history(history: list[dict]) -> str:
    if not history:
        return "(no earlier messages)"
    labels = {"user": "User", "assistant": PERSON_NAME}
    return "\n\n".join(f"{labels[m['role']]}: {m['content']}" for m in history)


def build_messages(question: str, answer: str, history: list[dict], background: str) -> list[dict]:
    """System Evaluator (criteria) + User Evaluator (answer and the material to check it)."""
    system = _fill((PROMPTS_DIR / "evaluator_system.md").read_text(encoding="utf-8"), name=PERSON_NAME)
    user = _fill(
        (PROMPTS_DIR / "evaluator_user.md").read_text(encoding="utf-8"),
        background=background,
        history=format_history(history),
        question=question,
        answer=answer,
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _response_format() -> dict:
    """Ask the model for JSON matching the Evaluation schema."""
    return {
        "type": "json_schema",
        "json_schema": {"name": "Evaluation", "schema": Evaluation.model_json_schema(), "strict": True},
    }


def evaluate(
    question: str,
    answer: str,
    history: list[dict],
    background: str,
    client: OpenAI | None = None,
    model: str = EVALUATOR_MODEL,
) -> Evaluation:
    """Return a validated Evaluation, or raise EvaluationError on any technical failure."""
    try:
        client = client or OpenAI()
        response = client.chat.completions.create(
            model=model,
            messages=build_messages(question, answer, history, background),
            response_format=_response_format(),
        )
    except Exception as e:  # network, auth, rate limit, bad request...
        raise EvaluationError(f"evaluator call failed: {type(e).__name__}: {e}") from e

    try:
        message = response.choices[0].message
    except (AttributeError, IndexError, TypeError) as e:
        raise EvaluationError(f"unexpected evaluator response shape: {e}") from e
    if getattr(message, "refusal", None):
        raise EvaluationError(f"evaluator refused: {message.refusal}")
    if not message.content:
        raise EvaluationError("evaluator returned empty output")
    try:
        return Evaluation.model_validate_json(message.content)
    except ValidationError as e:
        raise EvaluationError(f"invalid evaluation output: {e.errors(include_url=False)}") from e
