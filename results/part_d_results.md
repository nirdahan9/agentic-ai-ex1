# Part D — Experiments and results

- Run date: 2026-11-17, with `.venv/bin/python run_scenarios.py`.
- Actor: `gpt-5.4-mini-2026-03-17` (OpenAI).
- Evaluator: `claude-opus-5-5` (Anthropic) in scenarios 1–4. Scenario 5 uses a **mock** evaluator.

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
| All | [`part_d/execution_log.jsonl`](part_d/execution_log.jsonl) — the execution log of every question |

An earlier run with the previous evaluator (`gpt-5.4-2026-03-05`) is archived in [`previous_evaluator_gpt-5.4/`](previous_evaluator_gpt-5.4/).

## Summary

| # | Scenario | Type | Final status | Attempts | Matched expectation? |
|---|---|---|---|---|---|
| 1 | Question about existing information | LLM | approved | 1 | **Yes** |
| 2 | Follow-up question | LLM | approved, approved | 2, 1 | **Yes** |
| 3 | Detail not in the sources | LLM | approved | 1 | **Yes** |
| 4 | Rejection and improvement | LLM, with an injected flawed first draft | approved | 2 | **Yes** |
| 5 | Exhausting the attempts | **MOCK: control-flow test** | attempts_exhausted | 3 | **Yes** |

---

## Results from the language models (scenarios 1–4)

### Scenario 1 — Question about existing information

**Input:** "איפה אתה עובד היום ומה התפקיד שלך?" ("Where do you work today, and what is your role?"). There is no earlier history.

| Attempt | Source | Candidate answer | Evaluator decision (verbatim feedback) |
|---|---|---|---|
| 1 | Actor | אני עובד היום ב־Via.AI בתפקיד מהנדס QA, ומאז אוגוסט 2026. במסגרת התפקיד אני בודק מוצרי תיירות מבוססי בינה מלאכותית, מבצע בדיקות ידניות ואוטומטיות, ועובד בשיתוף פעולה הדוק עם צוות הפיתוח. | **Approved**. Every claim is supported by both the LinkedIn profile and the personal summary: QA Engineer at Via.AI since August 2026, testing AI-powered travel products, manual and automated testing, and close collaboration with the development team. The answer directly addresses both parts of the question (where I work and what my role is). It is in first-person Hebrew with a professional tone and uses the glossary forms (מהנדס QA, מוצרי תיירות מבוססי בינה מלאכותית, בדיקות ידניות ואוטומטיות, צוות הפיתוח). English is kept only for approved terms (Via.AI, QA). The phrasing "ומאז אוגוסט 2026" is slightly awkward, but it does not affect clarity. |

**Shown to the user:** the approved answer above.

**Supporting details in the sources:**

| Claim in the answer | Source |
|---|---|
| Works at Via.AI as a QA engineer since August 2026 | `data/linkedin_profile.txt:23-25` ("Via.ai / Quality Assurance Engineer / August 2026 - Present"); `data/personal_summary.txt:7` |
| Tests AI-powered travel products, manually and with automated tests | `data/linkedin_profile.txt:26` ("developing AI-powered solutions for the travel industry. Responsible for manual and automated software testing") |
| Works closely with the development team | `data/linkedin_profile.txt:26` ("Collaborating closely with the engineering team") |

**Matched expectation: yes.** The answer was approved, and every claim in it is supported by a specific line in the sources. The awkward phrase "ומאז אוגוסט 2026" was noticed by the evaluator and accepted as a minor style issue.

### Scenario 2 — Follow-up question

The scenario has two turns in the same conversation.

**Turn 1:** "איפה אתה לומד?" ("Where do you study?"). There is no earlier history.

| Attempt | Source | Candidate answer | Evaluator decision (verbatim feedback) |
|---|---|---|---|
| 1 | Actor | אני לומד לתואר ראשון במדעי המחשב באוניברסיטת רייכמן. לפי המקורות, אני סטודנט בשנה השלישית, עם צפי סיום ביוני 2027. | **Rejected**. Criterion D fails. The facts are correct and supported by both sources: a BSc in Computer Science at Reichman University, third-year student, expected completion June 2027. The question is answered directly and the Hebrew terminology follows the glossary. However, the phrase "לפי המקורות" breaks the first-person persona, because Nir would not cite 'the sources' when describing his own studies. Remove "לפי המקורות" and state it directly, e.g. "אני סטודנט בשנה השלישית, וצפוי לסיים ביוני 2027." |
| 2 | Actor correction (given the rejected answer and the feedback) | אני לומד לתואר ראשון במדעי המחשב באוניברסיטת רייכמן. אני סטודנט בשנה השלישית, וצפוי לסיים ביוני 2027. | **Approved**. The answer is acceptable. Every claim is supported by both sources. He is studying for a BSc in Computer Science at Reichman University (LinkedIn Education section and the personal summary). He is a third-year student (LinkedIn About section and the personal summary). He is expected to finish in June 2027 (LinkedIn: October 2024 - June 2027; summary: 'expected June 2027'). The answer directly addresses where he studies. It is written in the first person, entirely in Hebrew, and is concise. It uses the glossary terms correctly: לומד לתואר ראשון, מדעי המחשב, אוניברסיטת רייכמן and סטודנט בשנה השלישית. |

**Turn 2:** "ומתי אתה צפוי לסיים את הלימודים שם?" ("And when do you expect to finish your studies **there**?"). The history sent to the models contained turn 1's question and its **approved** answer (2 messages).

| Attempt | Source | Candidate answer | Evaluator decision (verbatim feedback) |
|---|---|---|---|
| 1 | Actor | אני צפוי לסיים ביוני 2027. | **Approved**. The answer meets all four criteria. A: The expected graduation date of June 2027 is supported by the LinkedIn profile ("BSc (in progress), Computer Science (October 2024 - June 2027)") and by the personal summary ("B.Sc., expected June 2027"). B: It directly answers the follow-up, correctly reading "שם" as Reichman University from the earlier turn. Although the date was already mentioned in the previous answer, a short confirmation is appropriate and does not needlessly repeat other details. C: Not applicable, since the information exists in the sources. D: The answer is concise, entirely in Hebrew, written in the first person, and professional in tone. |

**Shown to the user:** turn 1 showed the approved correction, and turn 2 showed "אני צפוי לסיים ביוני 2027."

**Context check:** The second question says only "there" and never names the institution. The Actor resolved "there" as Reichman University and answered June 2027, which is supported by `data/linkedin_profile.txt:41` ("October 2024 - June 2027"). The evaluator also confirmed this in its feedback.

**Matched expectation: yes.** The context was kept.

**Additional observation:** Turn 1 contains a *natural* rejection and correction, with no injected draft. The evaluator rejected the meta phrase "לפי המקורות" ("according to the sources"), and the Actor removed exactly that phrase on attempt 2. Turn 2 also shows that only the approved version, not the rejected draft, entered the history.

### Scenario 3 — Detail not in the sources

**Input:** "מה הממוצע שלך בתואר?" ("What is your degree GPA?")

| Attempt | Source | Candidate answer | Evaluator decision (verbatim feedback) |
|---|---|---|---|
| 1 | Actor | אין לי במקורות מידע על ממוצע הציונים שלי בתואר, ולכן אני לא יכול למסור מספר מדויק. אם תרצה, אני יכול כן לספר על תחומי הלימוד שלי או על הפרויקטים והניסיון הרלוונטי שלי. | **Approved**. Neither the LinkedIn profile nor the personal summary mentions a GPA or grades, so correctly stating that the information is missing meets criterion C. The answer adds no invented numbers or claims (A) and answers the GPA question directly (B). It is short, in first person, entirely in Hebrew, and professional and friendly in tone (D). Offering to talk about my studies or projects instead is a reasonable, grounded follow-up. |

**Shown to the user:** the answer above.

**Check against the sources:** Neither source mentions a GPA. The answer says the information is missing, invents no number, and offers to talk about topics that the sources do cover.

**Matched expectation: yes.**

### Scenario 4 — Rejection and improvement (controlled)

**Input:** "איפה עבדת לפני Via.AI?" ("Where did you work before Via.AI?")

To trigger the scenario in a controlled way, we fed in a flawed test draft as the first answer, as the assignment allows. The draft claims an invented job (Backend developer at Wix for two years) and an invented achievement (leading a microservices migration). The evaluation and the correction that follow were done by the language models.

| Attempt | Source | Candidate answer | Evaluator decision (verbatim feedback) |
|---|---|---|---|
| 1 | **Injected test draft** | לפני Via.AI עבדתי שנתיים כמפתח Backend ב־Wix, ושם הובלתי את המעבר לארכיטקטורת מיקרו־שירותים. | **Rejected**. Fails A: the claim that I worked two years as a Backend developer at Wix and led a move to a microservices architecture appears nowhere in the sources. Both the employer and the achievement are fabricated. Remove the claim entirely. Fails B: the sources do answer the question. Before Via.AI (since August 2026), my only listed role is five years in the IDF as a Logistics Officer (August 2019 – July 2024). Answer with that: 'שירתתי חמש שנים בצה״ל כקצין לוגיסטיקה'. You may briefly add details from the sources, such as four roles in field units and at HQ, or serving as קמב״ץ at the Logistics Command HQ during the Iron Swords war. Fails D: 'Backend' is left in English and is not on the Keep in English list. This becomes moot once the fabricated claim is removed. |
| 2 | Actor correction (given the rejected answer and the feedback) | לפני Via.AI שירתי חמש שנים בצה״ל כקצין לוגיסטיקה, בין אוגוסט 2019 ליולי 2024. במהלך השירות החזקתי ארבעה תפקידים ביחידות שטח ובמטה, ובמלחמת חרבות ברזל שימשתי כקמב״ץ במפקדת קצין הלוגיסטיקה הראשי. | **Approved**. Every claim is supported by the sources. The LinkedIn Experience section and the personal summary both state five years as an IDF Logistics Officer (August 2019 – July 2024), four roles across field units and HQ, and service as Operations Officer at the Logistics Command HQ during the Iron Swords war. The answer addresses the question directly by naming the prior role before Via.AI. It is concise, written in the first person, entirely in Hebrew, and uses the glossary terms correctly (קצין לוגיסטיקה, יחידות שטח, מטה, קמב״ץ, מפקדת קצין הלוגיסטיקה הראשי, מלחמת חרבות ברזל). |

**Shown to the user:** the corrected version from attempt 2. The injected draft was never shown.

**How the feedback changed the answer:** The rejected draft and the feedback were sent to the Actor through `prompts/actor_revision.md`. The correction follows the feedback point by point:

- it removed the Wix claim;
- it answered with the sourced IDF service (`data/linkedin_profile.txt:29-33`);
- it added the details that the feedback suggested: four roles, and קמב״ץ during the Iron Swords war.

**Matched expectation: yes.** The draft was rejected with specific reasons, and the corrected version was evaluated again and approved. The evaluator did not approve the flawed draft, so no change to the evaluator instructions was needed.

**Observation for the report:** The approved correction contains a Hebrew spelling mistake, "שירתי" instead of "שירתתי". The evaluator did not catch it.

---

## Mock test (scenario 5) — control-flow check, not a language-model result

### Scenario 5 — Exhausting the attempts

**This is explicitly a control-flow test.** The Actor is the real language model. The evaluator is a **mock** (`mock_always_reject` in `run_scenarios.py`). It returns a valid `Evaluation` with `is_acceptable = False` on every attempt, whatever the content. The test checks the attempt limit and the exit path, not answer quality.

**Input:** "מה GroupShield?" ("What is GroupShield?")

| Attempt | Source | Candidate answer | Evaluator decision (verbatim feedback) |
|---|---|---|---|
| 1 | Actor | GroupShield הוא בוט שבניתי שמנטר התנהגות ושפה לא הולמת בקבוצות. זה אחד מהפרויקטים שלי, אבל אין לי במקורות פירוט נוסף על איך הוא עובד בפועל או באילו טכנולוגיות השתמשתי בו. | **Rejected**. MOCK REJECTION (control-flow test): this mock evaluator rejects every attempt, regardless of content, to test the attempt limit. |
| 2 | Actor correction (given the rejected answer and the feedback) | GroupShield הוא בוט שבניתי שמנטר התנהגות ושפה לא הולמת בקבוצות. אין לי במקורות פירוט נוסף על אופן הפעולה שלו או על הטכנולוגיות ששימשו בו. | **Rejected**. MOCK REJECTION (control-flow test): this mock evaluator rejects every attempt, regardless of content, to test the attempt limit. |
| 3 | Actor correction (given the rejected answer and the feedback) | GroupShield הוא בוט שבניתי שמנטר התנהגות ושפה לא הולמת בקבוצות. אין לי במקורות פירוט נוסף על איך הוא עובד או באילו טכנולוגיות השתמשתי בו. | **Rejected**. MOCK REJECTION (control-flow test): this mock evaluator rejects every attempt, regardless of content, to test the attempt limit. |

**Shown to the user:** "לא התקבלה תשובה מאושרת במסגרת מגבלת שלושת הניסיונות. אפשר לנסח את השאלה מחדש או לשאול שאלה אחרת." ("No approved answer was obtained within the limit of three attempts. You can rephrase the question or ask another one.")

**Checks:**

- There were exactly 3 attempts, and the loop stopped after the third one.
- `final_status` is `attempts_exhausted`.
- None of the three rejected answers was shown. They appear only in the log.
- Each correction received the previous rejected answer and the feedback. The saved files do not record the Actor's inputs, so this rests on the code (`chat/loop.py`: the rejected answer and feedback are passed to the next Actor call; `chat/actor.py`: the correction request) and on the unit test `test_rejection_sends_rejected_answer_and_feedback_to_next_attempt`.

**Matched expectation: yes.**

**Observation:** Because the mock feedback names no real problem, the Actor had nothing to fix, and attempts 2 and 3 are only rephrasings of attempt 1. This shows that the quality of a correction depends on the quality of the feedback.

---

## Appendix — technical-error path (extra runs, not one of the five scenarios)

These runs show exit 6 of Part C ("technical error"). They were produced with `.venv/bin/python run_error_checks.py` through the same loop, and each one is saved as a full log record in [`technical_error_runs.jsonl`](technical_error_runs.jsonl).

| Scenario ID | How it was produced | Type | Logged `error` | Shown to the user |
|---|---|---|---|---|
| `error-actor-call-fails` | Actor called with an invalid OpenAI API key | Real (OpenAI rejected the call: 401) | `actor call failed: AuthenticationError: Error code: 401 …` | Hebrew error message |
| `error-evaluator-call-fails` | Evaluator asked for the Claude model `claude-does-not-exist`. The Actor answered normally | Real (Anthropic rejected the call: 404) | `evaluation not completed: evaluator call failed: NotFoundError: Error code: 404 …` | Hebrew error message |
| `error-evaluator-invalid-output` | Evaluator returns `{"is_acceptable": true}` without `feedback` | **MOCK (simulated)**, labelled in the record's `evaluator` field | `evaluation not completed: invalid evaluation output: … 'feedback' Field required` | Hebrew error message |

In all three runs:

- `final_status` is `technical_error`.
- The failed attempt is logged as `"evaluation": {"completed": false, "reason": …}`, with no content decision.
- No candidate answer was shown to the user.
- The loop stopped after one attempt.

In the third run, the output contained `"is_acceptable": true` but failed validation. The answer was still **not** approved, because a validation failure is never treated as content approval.
