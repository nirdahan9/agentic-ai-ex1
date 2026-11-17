# Personal chat with an answer evaluator and an improvement loop

Assignment 1, AI Systems course: Lecture 2, slides 19–21.

**Submitted by:** Nir Dahan (ניר דהן), Liav Sarfati (ליאב צרפתי), Eden Malka (עדן מלכה)

This is a Gradio chat that represents Nir Dahan, one of the team members, and answers only from two background sources. For each question, an **Actor** (OpenAI) generates a candidate answer and a separate **Critic (evaluator)** from a different provider (Anthropic Claude) checks it, returning structured output that is validated with Pydantic. A rejected answer goes back to the Actor together with the evaluator's feedback, for up to 3 generation attempts per question. Only approved answers are shown to the user. All drafts, decisions and feedback go to a separate check log.

- **Report:** [report/REPORT.md](report/REPORT.md) (PDF: [report/REPORT.pdf](report/REPORT.pdf))
- **Architecture diagram:** [docs/architecture.png](docs/architecture.png), explained in [docs/architecture.md](docs/architecture.md)
- **Results:** [results/part_d_results.md](results/part_d_results.md) for the five scenarios, and [results/part_b_manual_check.md](results/part_b_manual_check.md) for the manual check of approved answers
- **Screenshots:** [results/screenshots/](results/screenshots/)

## Models and settings used in the experiments

| Role | Provider | Model | Settings (`.env`) |
|---|---|---|---|
| Actor (answer generator): writes every candidate answer and every correction | OpenAI | `gpt-5.4-mini-2026-03-17` | `OPENAI_API_KEY`, `ACTOR_MODEL` |
| Critic (answer evaluator): checks every candidate (the first answer and each corrected version) | Anthropic | `claude-opus-5-5` | `ANTHROPIC_API_KEY`, `EVALUATOR_MODEL` |

- Each role has its own provider, API key, API call and prompts. A different model family judges the Actor, so the two roles do not share one model's blind spots. Prompts: `prompts/actor_system.md` and `prompts/actor_revision.md` for the Actor, `prompts/evaluator_system.md` and `prompts/evaluator_user.md` for the Evaluator.
- These models are the defaults when the variables in `.env` are left empty. The Actor uses a pinned OpenAI snapshot with default sampling parameters (temperature not set).
- The evaluator uses the Anthropic Messages API with structured output (`output_config.format`, a JSON schema mirroring `Evaluation`), effort `high`, and adaptive thinking (the model default). It also sets server-side refusal fallback (`fallbacks: "default"`), so that if a safety classifier declines, the call is retried on a fallback Claude model. The application then validates the output with Pydantic (`strict`, `extra="forbid"`), and only the validated boolean drives the loop.
- At most 3 generation attempts per question, including the first answer (`MAX_ATTEMPTS` in `chat/loop.py`).
- The chat UI and all answers are in Hebrew, as the assignment requires, even when a question is asked in English. Professional terms are translated with [prompts/glossary.md](prompts/glossary.md).
- Language model outputs are not deterministic, so a re-run can produce different wording, and occasionally a different number of attempts.

## Setup and run

Requirements: **Python 3.12** and [uv](https://docs.astral.sh/uv/). Versions are pinned in `requirements.txt`: anthropic 2.9.0, gradio 6.32.0, openai 3.52.0, pydantic 2.14.3, python-dotenv 1.2.4, pytest 9.2.0.

```bash
# 1. Install the dependencies
uv venv --python 3.12
uv pip install -r requirements.txt

# 2. Set up the environment
cp .env.example .env          # then set OPENAI_API_KEY=... and ANTHROPIC_API_KEY=... in .env
                              # (the other variables are optional, see .env.example)

# 3. Start the chat, then open http://127.0.0.1:7860
.venv/bin/python app.py

# 4. Run the tests
.venv/bin/python -m pytest -q          # unit tests: the full loop with fake models, no API calls
.venv/bin/python run_scenarios.py      # the five Part D scenarios with the real models (paid API calls)
.venv/bin/python run_scenarios.py 4    # or a single scenario
.venv/bin/python run_evaluator_checks.py   # Part B: evaluator on Actor answers + controlled cases (paid)
.venv/bin/python run_error_checks.py       # technical-error exit: 2 real failures + 1 mock (cheap)
```

The scenario ID for the check log can be set in the chat UI under **"הגדרות בדיקה"** (test settings). The default is `manual`.

## How it works

1. **Actor (OpenAI).** Every call gets the background sources, the conversation history and the user's question (`chat/actor.py`). On a correction attempt, it also gets the rejected answer and the evaluator's feedback (`prompts/actor_revision.md`).
2. **Evaluator (Claude).** It gets the question, the candidate answer, the sources and the relevant history. It checks four criteria: grounding in the sources, answering the question, handling missing information, and clarity and style. It returns `Evaluation(is_acceptable: bool, feedback: str)`.
3. **Loop** (`chat/loop.py`). The decision rests only on the validated boolean. There are three ways out:
   - **approved:** the answer is shown and added to the history;
   - **attempts exhausted:** after the third rejection, a fixed message is shown and no rejected answer is ever shown;
   - **technical error:** the model call failed, or the evaluator output was invalid. The log records that the evaluation was not completed, and an error message is shown.
4. **Conversation history.** The chat window keeps everything that was shown. The history passed to the models holds only user messages and approved answers. A question that ended without an approved answer is left out, together with its status message.

## Check / execution log

The chat appends one JSON line per question to `logs/check_log.jsonl`. This file is local and git-ignored. The logs for the scenarios are in `results/part_d/execution_log.jsonl`.

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

## Project layout

| Path | Contents |
|---|---|
| `app.py` | Gradio UI (Hebrew, right-to-left); runs the loop for every question |
| `chat/config.py` | Paths, model names and the person's name, read from the environment |
| `chat/sources.py` | Loads the background sources and the glossary |
| `chat/actor.py` | Actor call: background + history + question, plus the rejected answer and feedback on a correction |
| `chat/evaluator.py` | `Evaluation` Pydantic model, the Claude evaluator call (structured output), and `EvaluationError` for technical failures |
| `chat/loop.py` | Generate → evaluate → correct loop; the three exit paths |
| `chat/check_log.py` | Appends one JSON line per question to the check log |
| `prompts/` | Actor prompts (`actor_system.md`, `actor_revision.md`), evaluator prompts (`evaluator_system.md`, `evaluator_user.md`), and the Hebrew glossary (`glossary.md`) |
| `data/linkedin_profile.txt` | Background source: professional information exported manually from the LinkedIn profile (real profile; contact e-mail omitted) |
| `data/personal_summary.txt` | Background source: personal summary, about half a page |
| `tests/` | pytest unit tests: Actor messages, evaluator schema and errors, and every loop path. No API calls |
| `run_evaluator_checks.py` | Part B: evaluator decisions on six Actor answers and five hand-written controlled cases |
| `run_error_checks.py` | Three runs of the technical-error exit (two real failures, one mock) |
| `run_scenarios.py` | Runs the five Part D scenarios. Scenario 5 uses a mock evaluator that always rejects (control-flow test) |
| `results/part_d_results.md`, `results/part_d/` | Part D: per-scenario input, attempts log and shown output, the execution log, and whether each matched expectation |
| `results/technical_error_runs.jsonl` | Extra runs of the technical-error exit (two real, one mock) |
| `results/previous_evaluator_gpt-5.4/` | Archived results from the earlier evaluator (`gpt-5.4-2026-03-05`), kept for comparison |
| `results/part_b_manual_check.md`, `results/part_b_*.json` | Manual check of approved answers against the sources, evaluator limitations, and raw evaluator outputs |
| `results/screenshots/` | Screenshots of the conversation and the checking process |
| `docs/architecture.svg` / `.png` / `.md` | Architecture diagram |
| `report/` | Short report (Markdown and PDF) |
| `.env.example` | Environment variable names only (no values) |

## Conversation history

The chat window keeps everything that was shown, including the status message of a question that ended without an approved answer. The history passed to the Actor and the Evaluator holds only user messages and approved answers (step 3: an approved answer is added to the history). A question that ended at the attempt limit or with a technical error is left out of that history, together with its status message. As a result, the models never see an answer that did not pass evaluation, and they never see an unanswered question.
