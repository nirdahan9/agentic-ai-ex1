# Part B — manual check of approved answers

Pydantic validation only proves that the evaluator output has the right structure and types. It does not prove that the decision is correct or that the answer is true. To check the decisions, I compared every claim in the approved answers to the background sources by hand.

- Run date: 2026-11-17
- Actor: `gpt-5.4-mini-2026-03-17`
- Evaluator: `gpt-5.4-2026-03-05`
- Each question was asked as a fresh conversation, with no history.
- Raw output (question, answer, decision and feedback): [`part_b_evaluator_runs.json`](part_b_evaluator_runs.json).

The Actor produced 6 answers. The evaluator approved 4 and rejected 2.

## Approved answers, checked claim by claim

### 1. "אילו שפות תכנות וכלים אתה מכיר?" (Which programming languages and tools do you know?)

| Claim in the answer | Source | Supported? |
|---|---|---|
| Java, Python, C, TypeScript | LinkedIn About; personal summary, paragraph 3 | Yes |
| SQL, Node.js | LinkedIn About; personal summary, paragraph 3 | Yes |
| Works in Linux environments with Git | LinkedIn About; personal summary, paragraph 3 | Yes |
| "Experience in Software Development" | LinkedIn Top skills lists "Software Development" | Partly: a skill label is turned into "experience" |
| Strong foundations in Data Structures, Algorithms, Machine Learning | LinkedIn About | Yes |

The approval is correct. One phrase stretches the source a little: a skill label became a claim of experience. The evaluator accepted it without comment.

### 2. "מה אתה לומד ואיפה?" (What do you study, and where?)

| Claim in the answer | Source | Supported? |
|---|---|---|
| Computer Science at Reichman University | LinkedIn Education; summary, paragraph 1 | Yes |
| B.Sc., expected to finish June 2027 | LinkedIn Education (October 2024 – June 2027); summary, paragraph 1 | Yes |
| Third year | LinkedIn About ("Third-year"); summary, paragraph 1 | Yes |

The approval is correct.

### 3. "מה GroupShield?" (What is GroupShield?)

| Claim in the answer | Source | Supported? |
|---|---|---|
| A bot I built that monitors behavior and inappropriate language in groups | Personal summary, "My projects" | Yes, nearly word for word |
| No further details in the sources about its capabilities or implementation | Correct: the sources say nothing more | Yes (criterion C) |

The approval is correct. This also shows criterion C working: the answer states what is missing instead of inventing it.

### 4. "איזה סוג עבודה אתה מחפש?" (What kind of job are you looking for?)

| Claim in the answer | Source | Supported? |
|---|---|---|
| Looking for a job in software development or AI | Personal summary, paragraph 4 | Yes |
| Studies Computer Science at Reichman University | LinkedIn Education | Yes |
| Currently a QA Engineer at Via.AI | LinkedIn Experience | Yes |
| Especially interested in AI and AI agents | Summary: "In my studies I'm most interested in AI and in working with AI agents" | Yes (slightly generalized) |

The approval is correct.

## Rejected answers (real Actor hallucinations)

- **Military experience.** The answer said the citation came from "אלוף־משנה" (Colonel). The source says Brigadier General, which is תת־אלוף. The evaluator caught the wrong rank and gave a concrete fix.
- **DerbyUp.** The answer called it "פלטפורמת ההימור/ניבוי" (betting/prediction platform). The sources describe a prediction competition, not betting. The evaluator rejected the answer and told the Actor to remove the betting reference.

Both are realistic, subtle errors: one wrong rank, one wrong word. They are the kind of mistake the Critic exists to catch.

## Evaluator limitations seen in this check

1. **Small stretches pass.** "Software Development" moved from a skill label to "experience" in an approved answer. The evaluator judges grounding by meaning, so a small exaggeration like this can get through.
2. **Criterion labels are not always precise.** In the controlled tests, a fabricated-facts answer was rejected as "Fails A, B, and C" in both runs. The real problem was only A. The decision was right, but the labels were over-assigned.
3. **Imprecise feedback wording.** The military rejection was correct, but its feedback translated "אלוף־משנה" as "Lieutenant Colonel". It is actually Colonel. The decision was right and the feedback was still slightly wrong, so feedback is not automatically reliable either.
4. **Unhelpful offers are not flagged.** The rejected DerbyUp answer offered to "tell more about my role or how it worked technically" while also saying the sources have no such details. The evaluator did not mention this contradiction. It rejected the answer for another reason.

## Controlled evaluator tests (hand-written candidate answers)

These tests are separate from the Actor runs above. Each candidate answer was written by hand to test one criterion. Raw output: [`part_b_controlled_tests.json`](part_b_controlled_tests.json). I ran the set twice and got the same decisions both times.

| Case | Expected | Evaluator decision |
|---|---|---|
| Grounded answer (Via.AI QA Engineer) | accept | accepted |
| Fabricated role, team size, year and Google job | reject (A) | rejected; listed every invented detail |
| Correct "GPA is not in the sources" | accept (C) | accepted |
| Off-topic answer to "what did you do in the army?" | reject (B) | rejected; pointed to the military facts that should be used |
| Follow-up "how long did you serve?" with history | accept (B, context) | accepted; five years, 2019–2024 |
