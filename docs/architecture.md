# Architecture

```mermaid
flowchart TD
    subgraph SRC["Background sources (data/)"]
        LI["linkedin_profile.txt"]
        PS["personal_summary.txt"]
    end

    subgraph UI["Gradio chat UI (app.py, Hebrew, RTL)"]
        Q["User question"]
        H[("Conversation history<br/>user messages + approved answers<br/>(passed to the models)")]
        OUT["Message shown to the user"]
    end

    subgraph LOOP["Loop for one question (chat/loop.py) · attempts 1..3, counter reset per question"]
        A["Actor · chat/actor.py<br/>gpt-5.4-mini-2026-03-17<br/>prompts/actor_system.md"]
        C["Candidate answer"]
        E["Evaluator (Critic) · chat/evaluator.py<br/>gpt-5.4-2026-03-05<br/>prompts/evaluator_system.md + evaluator_user.md"]
        V{"Evaluation result<br/>Pydantic-validated<br/>is_acceptable: bool · feedback: str"}
        R{"Attempts left?<br/>(fewer than 3 so far)"}
    end

    LOG[("Check log · logs/check_log.jsonl<br/>scenario_id, question, final_status,<br/>per attempt: candidate, decision, feedback")]

    Q --> A
    H -- "conversation history" --> A
    SRC -- "background" --> A
    A --> C --> E
    Q --> E
    H -- "relevant history" --> E
    SRC -- "background" --> E
    E --> V

    V -- "is_acceptable = True" --> OK(["EXIT: approved<br/>show the answer, add it to the history"])
    V -- "is_acceptable = False" --> R
    R -- "yes" --> FB["Rejected answer + feedback<br/>(prompts/actor_revision.md)"]
    FB == "FEEDBACK ARC: corrected version requested" ==> A
    R -- "no (3rd answer rejected)" --> EX(["EXIT: attempts exhausted<br/>show a 'no approved answer' message"])

    A -. "model call fails" .-> ERR(["EXIT: technical error<br/>evaluation not completed, show an error message"])
    E -. "call fails / output invalid (EvaluationError)" .-> ERR

    OK --> OUT
    EX --> OUT
    ERR --> OUT
    OK --> H

    C -. "every attempt" .-> LOG
    V -. "decision + feedback" .-> LOG
    OK -. "final_status" .-> LOG
    EX -. "final_status" .-> LOG
    ERR -. "final_status + reason" .-> LOG

    classDef exitOk fill:#d4edda,stroke:#2e7d32,color:#1b5e20
    classDef exitEx fill:#fff3cd,stroke:#b8860b,color:#5d4300
    classDef exitErr fill:#f8d7da,stroke:#c62828,color:#7f0000
    class OK exitOk
    class EX exitEx
    class ERR exitErr
    linkStyle 12 stroke:#1565c0,stroke-width:3px
```

## How to read it

- **Inputs.** Every Actor call gets the background sources, the displayed conversation history and the user question. The evaluator gets the same material plus the candidate answer.
- **Evaluation result.** The evaluator returns JSON. The application validates it against the `Evaluation` Pydantic model. Only the validated `is_acceptable` field decides the next step.
- **Feedback arc** (thick blue). When an answer is rejected and attempts remain, the rejected answer and the evaluator's feedback go back to the Actor together with the question, the background and the history. The corrected version is evaluated again.
- **Exit paths:**
  - **Approved:** the answer is shown and added to the history.
  - **Attempts exhausted:** after the third rejected answer, a fixed message is shown. Rejected answers are never shown.
  - **Technical error:** a failed model call, or evaluator output that cannot be parsed or validated. Handling stops, and the log records that the evaluation was not completed.
- **Check log.** All drafts, decisions and feedback go to the check log, never to the displayed chat. When a question ends without an approved answer, it is left out of the history passed to the models.
