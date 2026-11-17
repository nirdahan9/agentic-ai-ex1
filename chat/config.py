"""Runtime configuration: paths and model names (from environment variables)."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
PROMPTS_DIR = ROOT / "prompts"
LOG_PATH = Path(os.getenv("CHECK_LOG_PATH") or ROOT / "logs" / "check_log.jsonl")

# Pinned model snapshot so that runs are reproducible; override in .env.
ACTOR_MODEL = os.getenv("ACTOR_MODEL") or "gpt-5.4-mini-2026-03-17"
# Separate call and prompts for the evaluator; a larger model for stricter checking.
EVALUATOR_MODEL = os.getenv("EVALUATOR_MODEL") or "gpt-5.4-2026-03-05"

# Name of the person the chat represents (must match the background sources).
PERSON_NAME = os.getenv("PERSON_NAME") or "ניר דהן"
