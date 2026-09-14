# Chapter 25: Graduation Project, Review, and Future Directions

<figure class="course-hero">
  <img src="../assets/visuals/chapter-25.webp" alt="A complete transparent agent machine integrates perception, planning, tools, memory, safety, approval, and telemetry." width="1536" height="864" loading="lazy" decoding="async">
  <figcaption><em>The capstone unifies the course into one inspectable, controlled agent system.</em></figcaption>
</figure>

The graduation project is not a longer demo. It proves that you can turn an ambiguous need into an operable, evaluable, auditable, recoverable, and releasable Agentic AI system.

## 25.1 Topic and Task Contract

A strong topic has an observable environment, multi-step decisions, external tools, verifiable outcomes, and explicit risk boundaries. Freeze users, triggers, inputs, outputs, exclusions, permissions, success/failure/stop/escalation conditions, budgets, approvals, and rollback.

## 25.2 Baseline and Architecture

Implement at least one non-agent baseline: rules, one-shot LLM, or fixed workflow. Multi-agent projects also require a single-agent baseline. Document only boundaries that change quality, safety, latency, or operations: task contract, runtime, loop, tools/environment/memory, verifier/approval, artifacts, audits, and metrics.

## 25.3 Milestones and Change Control

Freeze six milestones: task and evaluation contract; minimal observe-act-verify-stop loop; reproducible failures; safety and idempotency; baseline/main/ablation evaluation; and a release candidate with UI, runtime, runbook, and rollback. Version changes to datasets, thresholds, and safety policy instead of overwriting prior contracts.

## 25.4 Evaluation, Ablation, and Error Analysis

Measure completion, evidence correctness, tool success and redundancy, latency and cost, approval accuracy and unauthorized side effects, interruption, recovery, and replay consistency. Remove one mechanism per ablation. Classify the first cause of failure instead of labeling every defect "hallucination."

## 25.5 Security Review

Document actors, assets, trust boundaries, prompt injection, excessive tool authority, data leakage, supply-chain risk, least privilege, sandboxing, input/output validation, approval and undo, secret/PII/trace retention, and incident response. Red-team tests must cross real tool/runtime boundaries rather than asking the model whether it would leak data.

## 25.6 Reproducibility Pack

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

Record installation, fixture and model versions, offline tests, optional live tests, expected metric ranges, and known limits. Never submit API keys, user data, or unredacted traces.

## 25.7 Five-Minute Demo and Release

Show why the task needs an agent, one successful trace with evidence, one real failure and recovery, one approval/rejection/cancellation, and quality/cost/risk against the baseline. Before release verify version pins, migrations, secret rotation, alerts, runbooks, rollback, deletion, and cost limits.

## 25.8 Two Review Rubrics

### 25.8.1 Agent Application Engineering Route

| Dimension | Points |
| --- | ---: |
| Task value and completion | 20 |
| Loop, tool, context, and runtime design | 20 |
| Evidence, evaluation, baseline, and ablation | 20 |
| Safety, approval, audit, and privacy | 20 |
| UI, failure recovery, and operability | 10 |
| Reproducibility pack and communication | 10 |

### 25.8.2 Full-Stack Agentic AI Route

| Dimension | Points |
| --- | ---: |
| Agent system value and completion | 15 |
| Model, training, or inference question | 15 |
| Mathematical, capacity, and topology evidence | 15 |
| Experiment, baseline, ablation, and error analysis | 20 |
| Safety, approval, audit, and privacy | 15 |
| Runtime, fault tolerance, observability, and SLOs | 10 |
| Reproducibility pack and communication | 10 |

Both routes require at least 75 points and may not omit evidence, safety, failure recovery, or reproducibility.

## 25.9 Portfolio and Reviewer Pack

Provide a one-page summary, architecture diagram, one- and five-minute demos, evaluation table, one failure case, security boundary, and reproduction entry point. Explain work as task, baseline, change, evidence, and residual risk—not as a list of technologies.

## 25.10 Future Directions

Continue into verifiable rewards and generated environments; long-term memory conflict and forgetting; recoverable computer use; cross-agent identity and capability discovery; joint model-harness-environment evaluation; or optimization across compute, latency, energy, and task value.

Final mastery means answering why the system needs an agent, where its evidence lives, how it fails, who can stop it, and how another person reproduces the result.
