# Personal chat with an answer evaluator and an improvement loop

Assignment 1, AI Systems course. This is a Gradio chat that represents Nir Dahan and answers from two background sources. An Actor generates each answer and a separate Critic (evaluator) checks it with structured, Pydantic-validated output. A rejected answer goes back to the Actor with the evaluator's feedback, for up to 3 generation attempts per question. Only approved answers are shown to the user. Architecture diagram: [docs/architecture.md](docs/architecture.md).

## Status

- [x] Part A: background sources and the Actor
- [x] Part B: evaluator with structured output
- [x] Part C: generation, evaluation and correction loop
- [ ] Part D: experiments and results
- [ ] Part E: submission materials and report

## Models

| Role | Model | Setting |
|---|---|---|
| Actor (answer generator) | `gpt-5.4-mini-2026-03-17` (OpenAI) | `ACTOR_MODEL` in `.env` |
| Critic (answer evaluator) | `gpt-5.4-2026-03-05` (OpenAI), JSON-schema structured output | `EVALUATOR_MODEL` in `.env` |

Each role uses its own API call and its own prompts.

## Setup and run

The project needs Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv venv --python 3.12
uv pip install -r requirements.txt
cp .env.example .env        # then fill in OPENAI_API_KEY
.venv/bin/python app.py     # opens the chat at http://127.0.0.1:7860
.venv/bin/python -m pytest -q
```

## Project layout

| Path | Contents |
|---|---|
| `data/linkedin_profile.txt` | Professional information from the LinkedIn profile, exported manually |
| `data/personal_summary.txt` | Personal summary, about half a page |
| `prompts/actor_system.md` | Actor system prompt: role, answer style, grounding in the sources, explicit statement when information is missing |
| `prompts/evaluator_system.md` | System Evaluator: the four criteria (grounding, answering the question, missing information, clarity) and the feedback rules |
| `prompts/evaluator_user.md` | User Evaluator: the check message with the sources, relevant history, question and candidate answer |
| `chat/evaluator.py` | `Evaluation` Pydantic model (`is_acceptable: bool`, `feedback: str`), the evaluator call, and `EvaluationError` for technical failures |
| `prompts/glossary.md` | Hebrew glossary for answers in Hebrew, and the terms kept in English. Used by the Actor and the Evaluator |
| `prompts/actor_revision.md` | Correction request: the rejected answer and the evaluator's feedback, sent to the Actor on attempts 2–3 |
| `chat/actor.py` | Builds every Actor call from the background, the conversation history and the user question (plus the rejected answer and feedback on a correction) |
| `chat/loop.py` | The generate → evaluate → correct loop: at most 3 attempts, and exits on approval, attempts exhausted or technical error |
| `chat/sources.py` | Loads the background sources |
| `chat/check_log.py` | Execution / check log (`logs/check_log.jsonl`), kept separate from the displayed chat history |
| `docs/architecture.md` | Architecture diagram (Mermaid): sources, UI and history, Actor, Evaluator, evaluation result, feedback arc, and the three exit paths |
| `app.py` | Gradio UI in Hebrew (right-to-left). It shows only the user's messages and the final answers. The scenario ID for the log is under "הגדרות בדיקה" |
| `tests/` | pytest checks that make no API calls |
| `results/part_b_manual_check.md` | Manual check of approved answers against the sources, and the evaluator limitations found |
| `results/part_b_evaluator_runs.json`, `results/part_b_controlled_tests.json` | Raw evaluator outputs for the Actor answers and for the hand-written controlled cases |

## Answer language

The UI is in Hebrew. Answers follow the language of the user's question. If the question contains any Hebrew text, the answer is entirely in Hebrew. Otherwise, the answer is in English. Hebrew answers translate professional terms using [`prompts/glossary.md`](prompts/glossary.md). Only names and approved exceptions stay in English: Via.AI, DerbyUp, GroupShield, LinkedIn, GitHub, programming languages and tools, QA, and Full-Stack. The evaluator enforces this rule as part of criterion D (clarity and style). Status messages for attempts exhausted and technical errors follow the same rule.

## Conversation history

The chat window keeps everything that was shown, including the status message of a question that ended without an approved answer. The history passed to the Actor and the Evaluator holds only user messages and approved answers (step 3: an approved answer is added to the history). A question that ended at the attempt limit or with a technical error is left out of that history, together with its status message. As a result, the models never see an answer that did not pass evaluation, and they never see an unanswered question.

## Execution log

Each question is appended to `logs/check_log.jsonl` as one JSON line:

```json
{
  "timestamp": "...", "scenario_id": "manual", "question": "...",
  "actor_model": "...", "evaluator": "...",
  "final_status": "approved | attempts_exhausted | technical_error",
  "attempts": [
    {"attempt": 1, "candidate_source": "actor | injected_test_draft | actor_correction",
     "candidate": "...",
     "evaluation": {"completed": true, "is_acceptable": false, "feedback": "..."}}
  ],
  "shown_to_user": "...",
  "error": "only on technical_error"
}
```

On a technical error, the failed attempt has `"evaluation": {"completed": false, "reason": "..."}` and no content decision.
