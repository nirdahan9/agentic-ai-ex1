"""Gradio chat UI (Hebrew). Run: python app.py"""

import gradio as gr

from chat.actor import generate_answer
from chat.check_log import append_record
from chat.config import ACTOR_MODEL, PERSON_NAME
from chat.sources import load_background

BACKGROUND = load_background()


def _text(content) -> str:
    """Gradio may pass message content as a string or as a list of parts."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return str(content)


def to_history(gradio_history: list[dict]) -> list[dict]:
    """The displayed history: user messages and the final answers shown to the user."""
    return [
        {"role": m["role"], "content": _text(m["content"])}
        for m in gradio_history
        if m.get("role") in ("user", "assistant")
    ]


def respond(message: str, gradio_history: list[dict]) -> str:
    history = to_history(gradio_history)
    answer = generate_answer(message, history, BACKGROUND)
    append_record(
        {"question": message, "actor_model": ACTOR_MODEL, "attempts": [{"attempt": 1, "candidate": answer}]}
    )
    return answer


demo = gr.ChatInterface(
    fn=respond,
    chatbot=gr.Chatbot(rtl=True, height=520, placeholder=f"שאלו אותי על הלימודים, הניסיון, המיומנויות והפרויקטים של {PERSON_NAME}"),
    textbox=gr.Textbox(placeholder="כתבו שאלה...", rtl=True, submit_btn="שליחה"),
    title=f"צ׳אט אישי – {PERSON_NAME}",
    description="הצ׳אט עונה על בסיס פרופיל LinkedIn וסיכום אישי בלבד.",
)

if __name__ == "__main__":
    demo.launch()
