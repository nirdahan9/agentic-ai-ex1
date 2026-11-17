# Personal chat with an answer evaluator and an improvement loop

Assignment 1, AI Systems course. This is a Gradio chat that represents Nir Dahan and answers from two background sources. An Actor generates each answer. The Critic and the correction loop are added in Parts B and C.

## Status

- [x] Part A: background sources and the Actor
- [ ] Part B: evaluator with structured output
- [ ] Part C: generation, evaluation and correction loop
- [ ] Part D: experiments and results
- [ ] Part E: submission materials and report

## Models

| Role | Model | Setting |
|---|---|---|
| Actor (answer generator) | `gpt-5.4-mini-2026-03-17` (OpenAI) | `ACTOR_MODEL` in `.env` |

## Setup and run

The project needs Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv venv --python 3.12
uv pip install -r requirements.txt
cp .env.example .env        # then fill in OPENAI_API_KEY and PERSON_NAME
.venv/bin/python app.py     # opens the chat at http://127.0.0.1:7860
.venv/bin/python -m pytest -q
```

## Project layout

| Path | Contents |
|---|---|
| `data/linkedin_profile.txt` | Professional information from the LinkedIn profile, exported manually |
| `data/personal_summary.txt` | Personal summary, about half a page |
| `prompts/actor_system.md` | Actor system prompt: role, answer style, grounding in the sources, explicit statement when information is missing |
| `chat/actor.py` | Builds every Actor call from the background, the conversation history and the user question |
| `chat/sources.py` | Loads the background sources |
| `chat/check_log.py` | Check log (`logs/check_log.jsonl`), kept separate from the displayed chat history |
| `app.py` | Gradio UI in Hebrew (right-to-left). It shows only the user's messages and the final answers |
| `tests/` | pytest checks that make no API calls |
