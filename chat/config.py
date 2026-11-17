"""Runtime configuration: paths and model names (from environment variables)."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
PROMPTS_DIR = ROOT / "prompts"
LOG_PATH = Path(os.getenv("CHECK_LOG_PATH") or ROOT / "logs" / "check_log.jsonl")

# Actor (generator): OpenAI, pinned snapshot so runs are reproducible; override in .env.
ACTOR_MODEL = os.getenv("ACTOR_MODEL") or "gpt-5.4-mini-2026-03-17"
# The Evaluator (Critic) is a different provider: Anthropic's Claude checks every answer
# the OpenAI Actor produces. Separate call, separate prompts, separate API key (ANTHROPIC_API_KEY).
EVALUATOR_MODEL = os.getenv("EVALUATOR_MODEL") or "claude-opus-5-5"

# Name of the person the chat represents (must match the background sources).
PERSON_NAME = os.getenv("PERSON_NAME") or "ניר דהן"
