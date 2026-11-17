"""Evaluator (Critic): Claude checks the Actor's candidate answer and returns a validated Evaluation."""

import re

import anthropic
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from chat.config import EVALUATOR_MODEL, PERSON_NAME, PROMPTS_DIR
from chat.sources import load_glossary


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
    system = _fill((PROMPTS_DIR / "evaluator_system.md").read_text(encoding="utf-8"),
                   name=PERSON_NAME, glossary=load_glossary())
    user = _fill(
        (PROMPTS_DIR / "evaluator_user.md").read_text(encoding="utf-8"),
        background=background,
        history=format_history(history),
        question=question,
        answer=answer,
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


# JSON schema sent to Claude's structured output (output_config.format). It mirrors the
# Evaluation model; the application still validates the result with Pydantic afterwards.
EVALUATION_SCHEMA = {
    "type": "object",
    "properties": {
        "is_acceptable": {"type": "boolean"},
        "feedback": {"type": "string"},
    },
    "required": ["is_acceptable", "feedback"],
    "additionalProperties": False,
}


def evaluate(
    question: str,
    answer: str,
    history: list[dict],
    background: str,
    client: anthropic.Anthropic | None = None,
    model: str = EVALUATOR_MODEL,
) -> Evaluation:
    """Ask Claude (the Critic) to judge the Actor's answer.

    Returns a validated Evaluation, or raises EvaluationError on any technical failure.
    """
    system, user = build_messages(question, answer, history, background)
    try:
        client = client or anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
        response = client.beta.messages.create(
            model=model,
            max_tokens=16000,
            system=system["content"],
            messages=[user],
            output_config={"effort": "high", "format": {"type": "json_schema", "schema": EVALUATION_SCHEMA}},
            # If a safety classifier declines, the API retries on a fallback model in the same call.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except Exception as e:  # network, auth, rate limit, bad request...
        raise EvaluationError(f"evaluator call failed: {type(e).__name__}: {e}") from e

    if getattr(response, "stop_reason", None) == "refusal":
        raise EvaluationError(f"evaluator refused: {getattr(response, 'stop_details', None)}")
    if getattr(response, "stop_reason", None) == "max_tokens":
        raise EvaluationError("evaluator output was cut off (max_tokens)")
    try:
        text = next((b.text for b in response.content if b.type == "text"), "")
    except (AttributeError, TypeError) as e:
        raise EvaluationError(f"unexpected evaluator response shape: {e}") from e
    if not text:
        raise EvaluationError("evaluator returned empty output")
    try:
        return Evaluation.model_validate_json(text)
    except ValidationError as e:
        raise EvaluationError(f"invalid evaluation output: {e.errors(include_url=False)}") from e
