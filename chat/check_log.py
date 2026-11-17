"""Execution / check log: every attempt, decision and feedback, kept separate from the chat history."""

import json
from datetime import datetime, timezone
from pathlib import Path

from chat.config import LOG_PATH


def append_record(record: dict, path: Path = LOG_PATH) -> None:
    """Append one question's record as a JSON line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), **record}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
