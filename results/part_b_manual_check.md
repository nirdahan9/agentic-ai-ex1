# Part B — manual check of approved answers

Pydantic validation only proves that the evaluator output has the right structure and types. It does not prove that the decision is correct or that the answer is true. To check the decisions, we compared every claim in the approved answers to the background sources by hand.

- Run date: 2026-11-17, with `.venv/bin/python run_evaluator_checks.py`.
- Actor: `gpt-5.4-mini-2026-03-17` (OpenAI).
- Evaluator: `claude-opus-5-5` (Anthropic).
- Each question was asked as a fresh conversation, with no history, and got one attempt.
- Raw output (question, answer, decision and feedback): [`part_b_evaluator_runs.json`](part_b_evaluator_runs.json).

The Actor produced 6 answers. The evaluator approved 4 and rejected 2.

## Approved answers, checked claim by claim

### 1. "ספר לי על הניסיון הצבאי שלך" ("Tell me about your military experience")

| Claim in the answer | Source | Supported? |
|---|---|---|
| Five years in the IDF as a Logistics Officer, August 2019 – July 2024 | `linkedin_profile.txt:29-30`; summary, paragraph 1 | Yes |
| Four roles in field units and at HQ | `linkedin_profile.txt:31` | Yes |
| Led teams under pressure | `linkedin_profile.txt:35`; summary, paragraph 2 | Yes |
| Supported senior officers with data-driven briefings and operational planning | LinkedIn About ("supported senior commanders in decision-making and operational planning"); `linkedin_profile.txt:32` | Yes. The answer says "קצינים בכירים" (senior officers), where the glossary has "מפקדים בכירים" (senior commanders). The evaluator noticed this and accepted it. |
| קמב״ץ at the Logistics Command HQ during the Iron Swords war; coordinated plans and set priorities quickly | `linkedin_profile.txt:33` | Yes |
| Recognized for excellence three times, including a citation from a תת־אלוף (Brigadier General) | `linkedin_profile.txt:36` | Yes. The rank is correct. |

The approval is correct.

### 2. "אילו שפות תכנות וכלים אתה מכיר?" ("Which programming languages and tools do you know?")

| Claim in the answer | Source | Supported? |
|---|---|---|
| Java, Python, C, TypeScript, SQL, Node.js | LinkedIn About; summary, paragraph 3 | Yes |
| Works in Linux environments with Git | LinkedIn About; summary, paragraph 3 | Yes |
| QA experience, including manual and automated testing | `linkedin_profile.txt:26` (Via.ai) | Yes |

The approval is correct. The answer has a small typo, a stray space in "ב- QA". The evaluator noticed it and called it insignificant.

### 3. "מה GroupShield?" ("What is GroupShield?")

| Claim in the answer | Source | Supported? |
|---|---|---|
| A bot I built that monitors behavior and inappropriate language in groups | `personal_summary.txt:11` | Yes, nearly word for word |
| One of my personal projects | Summary, "My projects" | Yes |
| The sources do not say how it works or which platforms it runs on | Correct: the sources say nothing more | Yes (criterion C) |

The approval is correct on the facts. The answer includes the phrase "לפי המקורות" ("according to the sources"). See limitation 1.

### 4. "איזה סוג עבודה אתה מחפש?" ("What kind of job are you looking for?")

| Claim in the answer | Source | Supported? |
|---|---|---|
| Looking for a job in software development or AI | Summary, paragraph 4 | Yes |
| Especially interested in building reliable software and solving complex problems | Summary: "I care about reliable software and enjoy solving complex problems" | Partly. The source describes general values. The answer turns them into job preferences. |
| …and in growing as part of a **strong** development team | LinkedIn About: "growing as a software engineer through **impactful** teams" | Partly. "Impactful" became "strong". |

The approval is acceptable, but this answer stretches the sources a little. See limitation 2.

## Rejected answers

- **"ספר לי על DerbyUp" ("Tell me about DerbyUp").** The facts were grounded, but the evaluator rejected the answer for two reasons:
  - The phrase "לפי המקורות" breaks the first-person voice.
  - The answer closed with an offer, "אני יכול גם לספר איך תרמתי לפרויקט" ("I can also tell you how I contributed to the project"). That offer promises details that the sources do not contain.

  The feedback quoted both phrases and suggested a replacement.
- **"מה אתה לומד ואיפה?" ("What do you study, and where?")** The facts were correct, but the evaluator caught a repeated word, "אני לומד לומד", as well as the meta phrase "לפי המקורות". It gave the exact corrected wording.

## Evaluator limitations found in this check

1. **Inconsistent standard.** The meta phrase "לפי המקורות" was a reason to reject the DerbyUp and studies answers. In scenario 2 of Part D it caused a rejection too. In the GroupShield answer, the same phrase was noticed and accepted ("slightly meta… does not breach the criteria"). The same issue therefore got different decisions in different runs.
2. **Small stretches pass.** In the job-search answer, "impactful teams" became "a strong development team", and general values became job preferences. The evaluator approved it. It judges grounding by overall meaning, so a plausible rewording that slightly overstates a source is not flagged.
3. **Language errors are caught only sometimes.** The repeated word "לומד לומד" was caught here. A spelling mistake in Part D scenario 4 was approved: "שירתי" instead of "שירתתי".

## Controlled evaluator tests (hand-written candidate answers)

These tests are separate from the Actor runs above. Each candidate answer was written by hand to test one criterion. Raw output: [`part_b_controlled_tests.json`](part_b_controlled_tests.json).

| Case | Expected | Evaluator decision |
|---|---|---|
| Grounded answer (Via.AI QA engineer) | accept | accepted |
| Fabricated role, team size, year and Google job | reject (A) | rejected. Marked "Criterion A fails" and listed each invented detail. |
| Correct "GPA is not in the sources" | accept (C) | accepted |
| Off-topic answer to "what did you do in the army?" | reject (B) | rejected. Marked "Fails B" and listed the military facts that should be used. |
| Follow-up "how long did you serve?" with history | accept (B, context) | accepted: five years, 2019–2024 |

## Comparison with the earlier evaluator

Before we switched to Claude, the evaluator was `gpt-5.4-2026-03-05` (OpenAI). We ran the same checks with it. Its results are archived in [`previous_evaluator_gpt-5.4/`](previous_evaluator_gpt-5.4/).

| Observation | `gpt-5.4` evaluator | `claude-opus-5-5` evaluator |
|---|---|---|
| Criterion labels on the fabricated answer | Over-assigned ("Fails A, B, and C" in two runs) | Precise ("Criterion A fails") |
| Unsupported closing offer ("I can tell you more about my role…") | Not flagged | Flagged and rejected |
| Repeated word or meta phrase in the answer | Not checked | Caught (but inconsistently, see limitation 1) |
| Spelling mistake "שירתי" in an approved correction | Missed | Missed |
| Factual errors in its own feedback | One: "אלוף־משנה" translated as "Lieutenant Colonel" | None found |

The evaluator now comes from a different provider than the Actor (Anthropic rather than OpenAI). In these runs it was stricter and more precise. It still shows the same limitation as its predecessor: it can miss small stretches and spelling errors.
