# Part D — Experiments and results

- Run date: 2026-11-17, with `.venv/bin/python run_scenarios.py`.
- Actor: `gpt-5.4-mini-2026-03-17`.
- Evaluator: `gpt-5.4-2026-03-05` in scenarios 1–4. Scenario 5 uses a **mock** evaluator.

Every scenario goes through the same code path as the Gradio chat: `chat.loop.handle_question` for each question, and `app.to_history` for the conversation history.

For each scenario, the saved file holds:

- the input: the question, the history sent to the models, and, in scenario 4, the injected draft;
- the full attempts log: every candidate, the evaluator's decision and its feedback;
- the output shown to the user.

| Scenario | Full record |
|---|---|
| 1 | [`part_d/scenario_1.json`](part_d/scenario_1.json) |
| 2 | [`part_d/scenario_2.json`](part_d/scenario_2.json) |
| 3 | [`part_d/scenario_3.json`](part_d/scenario_3.json) |
| 4 | [`part_d/scenario_4.json`](part_d/scenario_4.json) |
| 5 | [`part_d/scenario_5.json`](part_d/scenario_5.json) |
| All | [`part_d/execution_log.jsonl`](part_d/execution_log.jsonl) — the execution log of every question, in the same format as the app's check log |

## Summary

| # | Scenario | Type | Final status | Attempts | Matched expectation? |
|---|---|---|---|---|---|
| 1 | Question about existing information | LLM | approved | 1 | **Yes** |
| 2 | Follow-up question | LLM | approved, approved | 1, 1 | **Yes** |
| 3 | Detail not in the sources | LLM | approved | 1 | **Yes** |
| 4 | Rejection and improvement | LLM, with an injected flawed first draft | approved | 2 | **Yes** |
| 5 | Exhausting the attempts | **MOCK: control-flow test** | attempts_exhausted | 3 | **Yes** |

---

## Results from the language models (scenarios 1–4)

### Scenario 1 — Question about existing information

**Input:** "איפה אתה עובד היום ומה התפקיד שלך?" ("Where do you work today, and what is your role?"). There is no earlier history.

**Attempts log:**

| Attempt | Source | Candidate answer | Evaluator decision |
|---|---|---|---|
| 1 | Actor | אני עובד היום ב־Via.AI בתפקיד מהנדס QA. אני עוסק בבדיקות ידניות ואוטומטיות של מוצרי תיירות מבוססי בינה מלאכותית, ועובד בשיתוף פעולה עם צוות הפיתוח. | **Approved.** Verbatim feedback: "The answer is supported by both sources: LinkedIn and the personal summary state that Nir works at Via.AI as a QA Engineer, testing AI-powered travel products with manual and automated testing in collaboration with the development/development team. It directly answers the user's question, stays concise, and is written in first-person Hebrew with the correct translated terms." |

**Shown to the user:** the approved answer above.

**Supporting details in the sources:**

| Claim in the answer | Source |
|---|---|
| Works at Via.AI as a QA engineer | `data/linkedin_profile.txt:23-24` ("Via.ai / Quality Assurance Engineer"); `data/personal_summary.txt:7` ("work as a QA Engineer at Via.AI (since August 2026)") |
| Manual and automated testing of AI-powered travel products | `data/linkedin_profile.txt:26` ("developing AI-powered solutions for the travel industry. Responsible for manual and automated software testing"); `data/personal_summary.txt:7` |
| Works with the development team | `data/linkedin_profile.txt:26` ("Collaborating closely with the engineering team") |

**Matched expectation: yes.** The answer was approved, and every claim in it is supported by a specific line in the sources.

### Scenario 2 — Follow-up question

The scenario has two turns in the same conversation.

| Turn | Question | History sent to the models | Attempts | Shown to the user |
|---|---|---|---|---|
| 1 | "איפה אתה לומד?" ("Where do you study?") | none | 1, approved | אני לומד מדעי המחשב באוניברסיטת רייכמן, במסגרת תואר ראשון, ואני סטודנט בשנה השלישית. לפי המקורות, הלימודים שלי החלו באוקטובר 2024 והם צפויים להסתיים ביוני 2027. |
| 2 | "ומתי אתה צפוי לסיים את הלימודים **שם**?" ("And when do you expect to finish your studies **there**?") | turn 1: the question and the approved answer (2 messages) | 1, approved | אני צפוי לסיים את הלימודים ביוני 2027. |

The evaluator's reason for approving turn 2: "It directly answers the follow-up question using the prior context about studying at Reichman University, and the date 'June 2027' is explicitly supported…"

**Context check:** The second question says only "there" and never names the institution. The history sent with turn 2 contained turn 1's question and approved answer. The Actor resolved "there" as Reichman University and answered June 2027, which is supported by `data/linkedin_profile.txt:41` ("October 2024 - June 2027").

**Matched expectation: yes.** The context was kept.

**Note:** Turn 1 had already mentioned June 2027, so this follow-up only shows that the context is kept. It does not show that the Actor can find new information through the context.

### Scenario 3 — Detail not in the sources

**Input:** "מה הממוצע שלך בתואר?" ("What is your degree GPA?")

**Attempts log:**

| Attempt | Source | Candidate answer | Evaluator decision |
|---|---|---|---|
| 1 | Actor | אין לי נתון על הממוצע בתואר במקורות שברשותי, ולכן אני לא יכול למסור מספר מדויק. אם תרצה, אני יכול כן לספר על הלימודים שלי במדעי המחשב באוניברסיטת רייכמן ועל הקורסים והתחומים שבהם אני מתמקד. | **Approved.** "It correctly states that the sources do not provide Nir Dahan's grade average, satisfying C, and … declining to invent a number…" |

**Shown to the user:** the answer above.

**Check against the sources:** Neither source mentions a GPA. The answer says the information is missing and invents no number. The other factual claim, Computer Science at Reichman University, is supported (`data/linkedin_profile.txt:40-41`). The closing offer, to talk about "הקורסים והתחומים שבהם אני מתמקד" ("the courses and areas I focus on"), stretches the source a little. The sources list foundations, not a focus of studies. This is the same kind of stretch as limitation 5 in [`part_b_manual_check.md`](part_b_manual_check.md). No personal fact was invented.

**Matched expectation: yes.**

### Scenario 4 — Rejection and improvement (controlled)

**Input:** "איפה עבדת לפני Via.AI?" ("Where did you work before Via.AI?")

To trigger the scenario in a controlled way, we fed in a flawed test draft as the first answer, as the assignment allows. The evaluation and the correction that follow were done by the language models.

**Attempts log:**

| Attempt | Source | Candidate answer | Evaluator decision |
|---|---|---|---|
| 1 | **Injected test draft** | לפני Via.AI עבדתי שנתיים כמפתח Backend ב־Wix, ושם הובלתי את המעבר לארכיטקטורת מיקרו־שירותים. (It claims a fabricated job, Backend developer at Wix for two years, and a fabricated achievement, leading a microservices migration.) | **Rejected.** "The answer invents an unsupported role and employer: there is no source stating Nir worked at Wix, as a Backend developer, for two years, or led a microservices migration. According to the sources, before Via.AI he served in the צה״ל as a קצין לוגיסטיקה from August 2019 to July 2024. Correct by answering that before Via.AI he served in the IDF as a Logistics Officer, and mention that the sources do not list any Wix role." |
| 2 | Actor correction, given the rejected draft and the feedback | לפני Via.AI שירתי בצה״ל כקצין לוגיסטיקה, בין אוגוסט 2019 ליולי 2024. אין לי במקורות מידע על עבודה ב־Wix או על תפקיד אחר לפני Via.AI. | **Approved.** "…both the LinkedIn profile and personal summary state that before Via.AI Nir served in the IDF as a Logistics Officer from August 2019 to July 2024. The added clarification that the sources do not mention Wix… is a valid handling of missing information…" |

**Shown to the user:** the corrected version from attempt 2. The injected draft was never shown.

**How the feedback changed the answer:** The rejected draft and the feedback were sent to the Actor through `prompts/actor_revision.md`. The corrected version follows both of the feedback's instructions:

1. It replaced the invented Wix role with the sourced IDF Logistics Officer service (`data/linkedin_profile.txt:29-30`).
2. It stated explicitly that the sources do not mention any Wix role.

**Matched expectation: yes.** The draft was rejected with specific reasons, and the corrected version was evaluated again and approved. The evaluator did not approve the flawed draft, so no change to the evaluator instructions was needed.

**Observations for the report:**

- The approved correction contains a Hebrew spelling mistake: "שירתי" instead of "שירתתי". Criterion D covers clarity, but the evaluator did not catch it.
- The rejection was labelled "Fails A, B, and C", although the real failure is A. The decision was right, but the criterion labels were over-assigned. This was also seen in Part B.

---

## Mock test (scenario 5) — control-flow check, not a language-model result

### Scenario 5 — Exhausting the attempts

**This is explicitly a control-flow test.** The Actor is the real language model. The evaluator is a **mock** (`mock_always_reject` in `run_scenarios.py`). It returns a valid `Evaluation` with `is_acceptable = False` on every attempt, whatever the content. The test checks the attempt limit and the exit path, not answer quality.

**Input:** "מה GroupShield?" ("What is GroupShield?")

**Attempts log:**

| Attempt | Source | Candidate answer (real Actor) | Decision (mock) |
|---|---|---|---|
| 1 | Actor | GroupShield הוא בוט שבניתי שמנטר התנהגות ושפה לא הולמת בקבוצות. מעבר לזה, אין לי במקורות פירוט נוסף על איך הוא עובד או באילו פלטפורמות הוא פועל. | Rejected (mock) |
| 2 | Actor correction | GroupShield הוא בוט שבניתי שמנטר התנהגות ושפה לא הולמת בקבוצות. מעבר לזה, אין לי במקורות פירוט נוסף על אופן הפעולה שלו או על הפלטפורמה שבה הוא פועל. | Rejected (mock) |
| 3 | Actor correction | Same as attempt 2. | Rejected (mock) |

Every rejection had the same feedback: "MOCK REJECTION (control-flow test): this mock evaluator rejects every attempt, regardless of content, to test the attempt limit."

**Shown to the user:** "לא התקבלה תשובה מאושרת במסגרת מגבלת שלושת הניסיונות. אפשר לנסח את השאלה מחדש או לשאול שאלה אחרת." ("No approved answer was obtained within the limit of three attempts. You can rephrase the question or ask another one.")

**Checks:**

- There were exactly 3 attempts, and the loop stopped after the third one.
- `final_status` is `attempts_exhausted`.
- None of the three rejected answers was shown. They appear only in the log.
- Each correction received the previous rejected answer and the feedback. The saved files do not record the Actor's inputs, so this rests on the code (`chat/loop.py`: the rejected answer and feedback are passed to the next Actor call; `chat/actor.py`: the correction request) and on the unit test `test_rejection_sends_rejected_answer_and_feedback_to_next_attempt`.

**Matched expectation: yes.**

**Observation:** Because the mock feedback names no real problem, the Actor had nothing to fix. Attempts 2 and 3 are therefore nearly identical to attempt 1. This shows that the quality of a correction depends on the quality of the feedback.
