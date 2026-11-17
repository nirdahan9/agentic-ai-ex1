"""Gradio chat UI (Hebrew). Run: python app.py"""

import gradio as gr

from chat.check_log import append_record
from chat.config import PERSON_NAME
from chat.loop import SYSTEM_MESSAGES, handle_question
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
    """Conversation history for the models: user messages and the approved answers.

    Questions that ended without an approved answer (attempt limit or technical error)
    are left out together with their status message, so the history holds only
    answers that passed the evaluator.
    """
    messages = [
        {"role": m["role"], "content": _text(m["content"])}
        for m in gradio_history
        if m.get("role") in ("user", "assistant")
    ]
    history = []
    for m in messages:
        if m["role"] == "assistant" and m["content"] in SYSTEM_MESSAGES:
            if history and history[-1]["role"] == "user":
                history.pop()  # drop the unanswered question
            continue
        history.append(m)
    return history


def respond(message: str, gradio_history: list[dict], scenario_id: str) -> str:
    outcome = handle_question(
        message, to_history(gradio_history), BACKGROUND,
        scenario_id=(scenario_id or "").strip() or "manual",
    )
    append_record(outcome.record)  # drafts, decisions and feedback go to the check log only
    return outcome.reply


demo = gr.ChatInterface(
    fn=respond,
    chatbot=gr.Chatbot(rtl=True, height=520, placeholder=f"שאלו אותי על הלימודים, הניסיון, המיומנויות והפרויקטים של {PERSON_NAME}"),
    textbox=gr.Textbox(placeholder="כתבו שאלה...", rtl=True, submit_btn="שליחה"),
    additional_inputs=[gr.Textbox(value="manual", label="מזהה תרחיש (נרשם ביומן הבדיקה)", rtl=True)],
    additional_inputs_accordion=gr.Accordion("הגדרות בדיקה", open=False),
    title=f"צ׳אט אישי – {PERSON_NAME}",
    description="הצ׳אט עונה על בסיס פרופיל LinkedIn וסיכום אישי בלבד. כל תשובה נבדקת על ידי מעריך לפני שהיא מוצגת.",
)

if __name__ == "__main__":
    demo.launch()
