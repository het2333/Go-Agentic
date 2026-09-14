# Chapter 16: Midterm Review, Retrospective, and Quick Reference

<figure class="course-hero">
  <img src="../assets/visuals/chapter-16.webp" alt="An opened agent machine is inspected module by module at a midterm review bench." width="1536" height="864" loading="lazy" decoding="async">
  <figcaption><em>The midterm review connects architecture, observed behavior, and evidence.</em></figcaption>
</figure>

Chapters 13–15 put loops, tools, context, memory, protocols, evaluation, and safety into real projects. This chapter adds no new abstraction. It asks a stricter question:

> Did the agent merely work once, or can another person reproduce, evaluate, and inspect it?

## 16.1 Midterm Deliverable

Choose one track:

1. a real-world task-execution Agent;
2. a Deep Research Agent;
3. a bounded multi-agent system.

Submit this minimum package:

```text
midterm/
├── README.md              # one-line task, setup, run, and limits
├── task_contract.md       # inputs, outputs, permissions, stop conditions
├── architecture.md        # Loop, Tool, State, and Environment boundaries
├── eval/
│   ├── cases.jsonl        # at least ten frozen evaluation tasks
│   └── report.md          # baseline, metrics, and failure taxonomy
├── traces/                # successful and failed trajectories
├── security_review.md     # side effects, approvals, and sensitive data
└── reproduction.md        # reproduce from a fresh environment
```

The package must state versions, model identity, environment variables, fixtures, randomness, expected outputs, permissions, and termination conditions. "It works on my machine" is not a passing result.

## 16.2 System Design Canvas

Answer seven questions on one page:

| Area | Required answer |
| --- | --- |
| Task | Who gives which task to the agent, under what conditions? |
| Success | Which observable conditions must hold simultaneously? |
| Environment | What may the agent read and change? |
| Loop | How does it observe, act, validate, and stop? |
| State | What enters context and what persists externally? |
| Safety | Which actions require approval and how are they rolled back? |
| Evidence | What proves that outputs came from execution rather than self-report? |

Every arrow in the canvas should correspond to an observable event: a tool call, environment result, validation result, approval decision, or final artifact.

## 16.3 Evidence, Safety, and Reproducibility

A usable trace contains at least:

```json
{
  "task_id": "case-007",
  "input_version": "fixture-v2",
  "model": "provider/model-version",
  "actions": [],
  "approvals": [],
  "evidence": [],
  "validators": [],
  "final_state": "succeeded",
  "cost": {"tokens": 0, "seconds": 0.0}
}
```

Approval is not merely a confirmation button. It is a semantic state that records the proposed action, target, expected side effect, supporting evidence, decision maker, and expiry time.

## 16.4 100-Point Review Rubric

| Dimension | Points | Full-credit condition |
| --- | ---: | --- |
| Task completion | 25 | Meets the declared threshold on a frozen task set |
| Evidence and provenance | 15 | Every important claim traces to tool or environment evidence |
| Evaluation and baseline | 15 | Includes frozen data, a rule/single-agent baseline, metrics, and error analysis |
| Safety and approval | 20 | Uses least privilege; risky actions can be previewed, approved, rejected, and audited |
| Failure recovery | 15 | Handles timeouts, tool errors, validation failures, and exhausted budgets explicitly |
| Reproducibility | 10 | A fresh environment can run fixtures, evaluation, and representative traces |

A passing score is at least 70, and safety/approval may not score zero. A project with no side effects must explicitly justify that classification instead of leaving the section blank.

## 16.5 Failure Retrospective

Choose the trace that came closest to succeeding but failed, then review it in this order:

1. describe the failure in externally observable terms;
2. locate the first wrong decision instead of only the final exception;
3. classify it as Model, Context, Tool, Loop, Environment, or Runtime;
4. change one cause;
5. rerun the same frozen Task Suite;
6. report improvement, regression, and residual risk.

## 16.6 First-Half Quick Reference

| Symptom | Check first | Do not start with |
| --- | --- | --- |
| Unsupported answer | Whether tool/environment evidence entered context | A larger model |
| Repeated tool calls | Termination, deduplication, and failure classes | Unlimited turns |
| Forgotten constraints | Structured state, compaction, and JIT context | Permanent full history |
| Unstable evaluation | Frozen fixtures, model version, judge, and retry policy | Showing the best run |
| Unexpected side effect | Permissions, dry-run, approval, and idempotency | A warning in the prompt |

## 16.7 Two Routes Forward

**Agent application engineering:** move directly to Chapters 23–25 if your goal is products, enterprise applications, or agent platforms.

**Full-stack Agentic AI:** continue through Chapters 17–25 if you need model internals, training, and efficient serving.

These are two routes, not two quality levels. The application route does not require large-model training, but it still requires evidence, evaluation, safety, and reproducibility.

## 16.8 Exercises and Passing Standard

1. Freeze at least ten tasks and declare the success threshold before changing the agent.
2. Record one success, one tool failure, and one rejected-approval trace.
3. Score the project yourself and ask another reviewer to score it independently; explain disagreements.
4. Reproduce the project in a fresh directory or container using `reproduction.md`.

Proceed only after completing all four exercises, scoring at least 70, and earning a non-zero safety score.
