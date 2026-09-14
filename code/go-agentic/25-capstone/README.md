# Go Agentic Capstone Contract

Choose either the application-engineering or full-stack systems rubric in Chapter 25. The project must be reproducible from a clean directory and include this exact structure:

```text
capstone/
├── README.md
├── task_contract.md
├── architecture.md
├── eval/
│   ├── dataset.jsonl
│   └── report.md
├── traces/
├── security_review.md
└── reproduction.md
```

## Required evidence

- `task_contract.md` freezes inputs, outputs, exclusions, permissions, budgets, and success/stop/escalation conditions.
- `architecture.md` identifies model, loop, tools, environment, state, verifier, approval, runtime, and UI boundaries.
- `eval/dataset.jsonl` is versioned and never silently edited after results are inspected.
- `eval/report.md` compares a baseline and main system and includes at least one ablation and an error taxonomy.
- `traces/` contains representative success, failure, rejection/cancellation, and recovery traces with secrets removed.
- `security_review.md` covers threats, least privilege, approval, idempotency, rollback/compensation, privacy, and incident handling.
- `reproduction.md` starts from a clean environment, runs offline fixtures first, and states expected metric ranges.

Do not commit credentials, private user data, proprietary source documents, or raw chain-of-thought. Submit observable actions, evidence, decisions, validator results, and final artifacts instead.
