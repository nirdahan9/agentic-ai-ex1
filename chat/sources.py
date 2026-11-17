"""Loads the background sources the chat is grounded in."""

from pathlib import Path

from chat.config import DATA_DIR, PROMPTS_DIR

# Source files, in the order they are presented to the model.
SOURCE_FILES = {
    "LinkedIn profile": "linkedin_profile.txt",
    "Personal summary": "personal_summary.txt",
}


def load_background(data_dir: Path = DATA_DIR) -> str:
    """Return all background sources as one labeled text block."""
    sections = []
    for title, filename in SOURCE_FILES.items():
        text = (data_dir / filename).read_text(encoding="utf-8").strip()
        sections.append(f"## Source: {title} ({filename})\n\n{text}")
    return "\n\n".join(sections)


def load_glossary(prompts_dir: Path = PROMPTS_DIR) -> str:
    """Hebrew glossary used by the Actor and the Evaluator for answers in Hebrew."""
    return (prompts_dir / "glossary.md").read_text(encoding="utf-8").strip()
