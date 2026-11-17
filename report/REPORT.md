# Personal Chat with an Answer Evaluator and an Improvement Loop — Report

**Assignment 1, Agentic AI** · Submitted by: Nir Dahan, Liav Sarfati, Eden Malka  
Actor: OpenAI `gpt-5.4-mini-2026-03-17` · Evaluator: Anthropic `claude-opus-5-5`

## 1. System overview

The chat represents Nir Dahan, one of the team members. It answers only from two background sources about Nir: a LinkedIn export and a half-page personal summary. Every question goes through a generate → evaluate → correct loop (`chat/loop.py`; see the architecture diagram on page 3).

- **Actor (OpenAI).** It receives the sources, the conversation history and the question, and writes a candidate answer.
- **Evaluator (Claude).** It comes from a different provider, with its own call, prompts and API key. It receives the question, the candidate, the sources and the relevant history, and checks four criteria: grounding, answering the question, handling missing information, and clarity and style. It returns structured JSON, which the application validates against a Pydantic model, `Evaluation(is_acceptable: bool, feedback: str)`.
- **Decision.** Only the validated boolean decides what happens next:
    - **Approved:** the answer is shown and added to the history.
    - **Rejected, with attempts left:** the rejected answer and the feedback go back to the Actor (`prompts/actor_revision.md`).
    - **Third answer rejected:** a fixed "no approved answer" message is shown.
    - **Technical error** (failed call, or output that cannot be parsed or validated): handling stops and the log records "evaluation not completed".
- **What the user sees.** Only final answers or status messages. Every draft, decision and piece of feedback goes to a separate JSONL check log.

All five scenarios behaved as expected (`results/part_d_results.md`). Scenarios 1–4 used the real models. Scenario 5 is marked as a control-flow test with a mock evaluator that always rejects.

## 2. How the feedback changed an answer

**Scenario 4 (controlled).** For the question "<bdi>איפה עבדת לפני Via.AI?</bdi>" ("Where did you work before Via.AI?"), we injected a flawed first draft. It claimed two years as a Backend developer at Wix and leading a microservices migration. None of this is in the sources.

The evaluator rejected the draft and its feedback did three things:

- it named the invented employer and the invented achievement;
- it stated what the sources actually say (five years as an IDF Logistics Officer, 2019–2024) and suggested details to add (four roles; קמב״ץ in the Iron Swords war);
- it noted that "Backend" should not stay in English.

The Actor received the draft and this feedback, and its correction followed each point:

> <p dir="rtl">לפני Via.AI שירתי חמש שנים בצה״ל כקצין לוגיסטיקה, בין אוגוסט 2019 ליולי 2024. במהלך השירות החזקתי ארבעה תפקידים ביחידות שטח ובמטה, ובמלחמת חרבות ברזל שימשתי כקמב״ץ במפקדת קצין הלוגיסטיקה הראשי.</p>
>
> ("Before Via.AI I served five years in the IDF as a Logistics Officer, August 2019 – July 2024. I held four roles in field units and at HQ, and in the Iron Swords war I served as Operations Officer at the Chief Logistics Officer HQ.")

The evaluator re-checked this version and approved it.

**A natural case, with no injected draft (scenario 2).** The Actor answered "where do you study?" correctly but wrote "<bdi>לפי המקורות</bdi>" ("according to the sources"). The evaluator rejected the answer because this breaks the first-person voice, and it quoted the phrase with a replacement. The second attempt removed exactly that phrase, kept the facts, and was approved. Only the approved version entered the history used by the follow-up question.

In both cases the correction was targeted: the Actor fixed what the feedback named and kept the rest. The mock run in scenario 5 shows the other side. When the feedback named no concrete problem, attempts 2 and 3 were only rephrasings of attempt 1. The loop is only as useful as the feedback it carries.

## 3. Why schema validity does not guarantee a correct answer

Pydantic validation, together with structured output, guarantees the *form* of the evaluation. It guarantees there are exactly two fields, a real boolean (the string `"true"` is rejected), a non-empty feedback string, and no extra keys. This lets the loop branch on `is_acceptable` instead of searching free text for keywords. A simulated test showed the other direction too: an output of `{"is_acceptable": true}` without feedback failed validation and ended as a technical error, not as an approval.

But a perfectly valid object can still carry a **wrong decision**. Validation never looks at the answer, the sources or the question. It only checks that the evaluator *said something* in the right shape. The `true` comes from another language model's judgment. Our runs include valid evaluations with flawed content:

- The approved correction in scenario 4 says "<bdi>שירתי</bdi>", a misspelling of "<bdi>שירתתי</bdi>" ("I served"), although criterion D covers clarity.
- The same issue, the meta phrase "<bdi>לפי המקורות</bdi>", led to a rejection in three answers and was accepted in a fourth. Each of these decisions was schema-valid.
- With the earlier evaluator (`gpt-5.4`), a correct rejection gave a factually wrong explanation: it translated "<bdi>אלוף־משנה</bdi>" as "Lieutenant Colonel"; it is actually Colonel.

Schema validity means "the judge returned a well-formed verdict", not "the verdict is right". That is why the assignment asks for a manual check against the sources.

## 4. Evaluator limitations found in the manual check

We checked every claim in the approved answers against `data/` (`results/part_b_manual_check.md`). The evaluator caught real problems in the Actor's answers:

- an offer to describe Nir's role in DerbyUp, which the sources do not contain;
- a repeated word ("<bdi>לומד לומד</bdi>");
- a meta phrase that broke the first-person voice.

The limitations we found:

- **Inconsistent standard.** The same phrase was a reason to reject in one run and was accepted in another. A single LLM judgment is not a stable rule.
- **Small stretches pass.** In an approved answer, the source's "impactful teams" became "a strong development team", and general values became job preferences. The evaluator judges grounding by overall meaning, so a plausible rewording that slightly overstates a source is not flagged. Only clearly invented facts, such as a new employer or role, were reliably caught.
- **Language errors are caught only sometimes.** "<bdi>לומד לומד</bdi>" was caught, but "<bdi>שירתי</bdi>" was approved.

We first ran the system with an OpenAI evaluator (`gpt-5.4`; results archived in `results/previous_evaluator_gpt-5.4/`). Moving the evaluator to a different provider made its criterion labels precise and caught the unsupported offer, which the earlier evaluator missed. The stretch and spelling limitations remained with both.

**Possible improvements:**

- Ask the evaluator to list each factual claim with the source line that supports it, which makes stretches visible.
- Add explicit rules for meta phrases and spelling, so these are judged consistently.
- Keep the manual check, because a valid schema cannot replace it.
