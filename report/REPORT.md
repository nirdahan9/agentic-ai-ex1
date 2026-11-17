# Personal Chat with an Answer Evaluator and an Improvement Loop — Report

**Assignment 1, AI Systems** · Submitted by: Nir Dahan, Liav Sarfati, Eden Malka  
Actor: `gpt-5.4-mini-2026-03-17` · Evaluator: `gpt-5.4-2026-03-05`

## 1. System overview

The chat represents Nir Dahan, one of the team members, and it answers only from two background sources about Nir: a LinkedIn export and a half-page personal summary. Every question goes through a generate → evaluate → correct loop (`chat/loop.py`; see the architecture diagram on page 3).

- **Actor.** It receives the sources, the conversation history and the question, and writes a candidate answer.
- **Evaluator.** It is a separate call with its own prompts. It receives the question, the candidate, the sources and the relevant history, and checks four criteria: grounding, answering the question, handling missing information, and clarity and style. It returns JSON that is validated against a Pydantic model, `Evaluation(is_acceptable: bool, feedback: str)`.
- **Decision.** Only the validated boolean decides what happens next:
    - **Approved:** the answer is shown and added to the history.
    - **Rejected, with attempts left:** the rejected answer and the feedback go back to the Actor (`prompts/actor_revision.md`).
    - **Third answer rejected:** a fixed "no approved answer" message is shown.
    - **Technical error** (failed call, or output that cannot be parsed or validated): handling stops and the log records "evaluation not completed".
- **What the user sees.** Only final answers or status messages. Every draft, decision and piece of feedback goes to a separate JSONL check log.

All five scenarios behaved as expected (`results/part_d_results.md`). Scenarios 1–4 used the real models. Scenario 5 is marked as a control-flow test with a mock evaluator that always rejects.

## 2. How the feedback changed an answer

**Scenario 4 (controlled).** For the question "<bdi>איפה עבדת לפני Via.AI?</bdi>" ("Where did you work before Via.AI?"), we injected a flawed first draft. It claimed two years as a Backend developer at Wix and leading a microservices migration. None of this is in the sources.

The evaluator rejected the draft. Its feedback named each invented claim (Wix, Backend, two years, microservices), quoted what the sources actually say (IDF Logistics Officer, August 2019 – July 2024), and gave a concrete instruction: answer with the IDF service, and say that the sources do not list a Wix role.

The Actor received the rejected draft and this feedback, and its correction followed both instructions:

> <p dir="rtl">לפני Via.AI שירתי בצה״ל כקצין לוגיסטיקה, בין אוגוסט 2019 ליולי 2024. אין לי במקורות מידע על עבודה ב־Wix או על תפקיד אחר לפני Via.AI.</p>
>
> ("Before Via.AI I served in the IDF as a Logistics Officer, August 2019 – July 2024. The sources have no information about work at Wix or another role before Via.AI.")

The evaluator re-checked this version and approved it.

**A natural case from live use.** In a follow-up about the location of Nir's army service, the Actor wrote the military role title with its letters swapped ("<bdi>מקב״ץ</bdi>" instead of "<bdi>קמב״ץ</bdi>"). The evaluator rejected the answer and spelled out the exact fix. The second attempt changed only that word and was approved.

In both cases the correction was targeted: the Actor fixed what the feedback named and kept the rest. The mock run in scenario 5 shows the other side. When the feedback named no concrete problem, attempts 2 and 3 were nearly identical to attempt 1. The loop is only as useful as the feedback it carries.

## 3. Why schema validity does not guarantee a correct answer

Pydantic validation, together with OpenAI's strict JSON schema, guarantees the *form* of the evaluation. It guarantees there are exactly two fields, a real boolean (the string `"true"` is rejected), a non-empty feedback string, and no extra keys. This lets the loop branch on `is_acceptable` instead of searching free text for keywords. A simulated test showed the other direction too: an output of `{"is_acceptable": true}` without feedback failed validation and ended as a technical error, not as an approval.

But a perfectly valid object can still carry a **wrong decision**. Validation never looks at the answer, the sources or the question. It only checks that the evaluator *said something* in the right shape. The `true` comes from another language model reading the sources, with the same kinds of blind spots as the Actor. Our runs include valid evaluations with flawed content:

- An approved answer said "<bdi>שירתי</bdi>", a misspelling of "<bdi>שירתתי</bdi>" ("I served"), although criterion D covers clarity.
- A correct rejection gave a factually wrong explanation. It translated "<bdi>אלוף־משנה</bdi>" as "Lieutenant Colonel"; it is actually Colonel.

Schema validity means "the judge returned a well-formed verdict", not "the verdict is right". That is why the assignment asks for a manual check against the sources.

## 4. Evaluator limitations found in the manual check

We checked every claim in the approved answers against `data/` (`results/part_b_manual_check.md`). The evaluator caught real hallucinations by the Actor:

- a wrong rank: Colonel instead of Brigadier General (תת־אלוף);
- the word "betting" for a prediction competition.

The main limitation is that **small stretches of the sources pass**:

- The skill label "Software Development" became "I have experience in software development".
- "Strong foundations in" data structures, algorithms and ML became "my studies focus on" them.

Both answers were approved. The evaluator judges grounding by overall meaning, so a plausible rewording that slightly overstates a source is not flagged. Only invented entities, such as a new employer or a new rank, are reliably caught.

Smaller issues:

- **Over-labelled criteria.** A fabricated-fact answer was marked "Fails A, B and C" in repeated runs, when only A applies.
- **Missed spelling.** Hebrew spelling mistakes were not caught (above).

**Possible improvements:**

- Ask the evaluator to list each factual claim with the source line that supports it, which makes stretches visible.
- Add an explicit rule against upgrading skills to experience.
- Keep the manual check, because a valid schema cannot replace it.
