<div align="right">
  <a href="./第六章%20框架开发实践.md">中文</a> | English
</div>

# Chapter 6: Agent Development Lifecycle and Framework Selection

<figure class="course-hero">
  <img src="../assets/visuals/chapter-06.webp" alt="Specialized runtime vessels approach branching channels for different framework lifecycles." width="1536" height="864" loading="lazy" decoding="async">
  <figcaption><em>Framework choice depends on the lifecycle and controls a system must support.</em></figcaption>
</figure>

An agent project does not become production-ready when a model or harness is selected. Reliable delivery requires a sequence of evidence gates: define the task, design the Environment, select a Model and harness, build a minimal prototype, evaluate outcomes and traces, add observability, complete security review, and deploy through a reversible release. This chapter presents one lifecycle from idea to operating system.

By the end of this chapter, you should be able to:

- turn a product idea into an evaluable task and authority contract;
- design the Environment and success evidence before selecting a Model and harness;
- record technical choices with a capability matrix and task-set evidence;
- build an evaluation set containing success, recovery, denial, and termination cases;
- define traces, metrics, security review, and deployment gates;
- design versioning, canary release, rollback, and continuous evaluation for a deployed agent.

## 6.1 The Lifecycle Is a Set of Evidence Gates

### 6.1.1 Eight Stages


| Stage | Required artifact | Evidence to advance |
| --- | --- | --- |
| Task definition | Task contract, examples, success and stop conditions | A person can independently judge whether an example is complete |
| Environment design | Tools, permissions, fixtures, verifier | Actions validate and results replay |
| Model and harness selection | Capability matrix, candidate prototypes, decision record | Every required capability passes the task set |
| Vertical prototype | One minimal end-to-end path | Success, failure, and termination run locally |
| Evaluation | Dataset, metrics, thresholds, baseline | Frozen set meets release thresholds |
| Observability | Event schema, traces, dashboard, alerts | A failure can be located to a specific layer and step |
| Security review | Threat model, control tests, residual risks | High risks are fixed or explicitly accepted |
| Deployment | Versions, canary, rollback, runbook | Low-volume traffic meets SLOs and a rollback drill passes |

The stages are not a one-way waterfall. An evaluation failure may reveal an ambiguous task definition, security review may narrow Tool authority, and production traces may expose a new task distribution. Returning upstream should update artifacts and thresholds rather than only tune a prompt.

### 6.1.2 Decision Records Matter More Than Technology Preference

Every consequential choice should retain four items: requirements at the time, candidates compared, reproducible evidence, and a trigger for reevaluation. When the model, harness, or retriever changes, the team can then compare it on the same task set and boundaries instead of restarting a preference debate.

## 6.2 Define the Task and Environment First

### 6.2.1 Task Contract

“Build a research assistant” cannot be evaluated. A task contract turns the goal into observable behavior:

```text
Goal: Answer from supplied local sources and cite source locations.
Inputs: Question, allowed source directory, deadline.
Allowed actions: Search, read, produce a cited draft.
Forbidden actions: Network access, writing into sources, invented citations.
Success evidence: Every factual claim maps to a valid excerpt in allowed sources.
Stop conditions: Sufficient evidence; or any of 8 Tool steps, 2 query rewrites, 60 seconds exhausted.
Escalation: Ask for human judgment when sources conflict or critical evidence is absent.
```

The task set must cover the real distribution rather than only happy paths. Include at least common success, boundary input, no answer, conflicting evidence, Tool errors, authority denial, budget exhaustion, and high-impact approval.

### 6.2.2 Environment Contract

Environment design determines what an agent can actually know and change. Record these fields for every Tool:

| Field | Question |
| --- | --- |
| Input schema | Which arguments, types, ranges, and extra fields are allowed? |
| Semantic rules | Which paths, queries, objects, or state combinations are valid? |
| Authority | Who may call it, and which arguments require approval? |
| Side effects | What reads, writes, external messages, or irreversible effects occur? |
| Observation | How are success, empty, partial, and failed results distinguished? |
| Idempotency and compensation | Is replay safe, and how is failure recovered? |
| Fixture | How can behavior be reproduced locally and stably? |
| Verifier | Which independent signal proves the goal is met? |

Complete this table before debating how autonomous the agent should be. Its autonomy is the intersection of allowed Actions, authority, and budgets.

## 6.3 Select the Model and Harness

### 6.3.1 Select a Model with the Task Set

Model selection is not a one-time leaderboard lookup. Against the same frozen task set and Tool schemas, measure typed-call correctness, evidence location in long context, instruction following, refusal behavior, latency, total cost, and availability. A high-capability model may serve difficult routing or recovery, while a cheaper one handles a proven narrow task; the router itself must also be evaluated.

Record model version, parameters, context construction, and Provider Adapter. A model update is a dependency upgrade and requires evaluation reruns; a stable name does not guarantee stable behavior.

### 6.3.2 Select a Harness with a Capability Matrix

Mark each capability as **required**, **useful**, or **irrelevant** before inspecting candidates.

| Capability | Requirement question | Evidence to observe in the prototype |
| --- | --- | --- |
| Loop control | Are loops, branches, retries, and custom termination needed? | States and transitions are inspectable; budgets are enforced |
| Tool boundary | Are schemas, permissions, approvals, and structured errors sufficient? | Invalid and unauthorized calls are rejected before execution |
| State lifetime | Is state request-local, session-resumable, or a durable workflow? | Checkpoints resume and have a version-migration strategy |
| Human participation | Which Actions must pause for a decision? | Approval binds exact arguments; rejection leaves consistent state |
| Concurrency | Are parallel Tools or multiple executors required? | Dependencies, order, cancellation, and partial failure are visible |
| Observability | Which traces, metrics, and evaluation hooks are needed? | Stable IDs correlate model, Tool, and verifier events |
| Deployment | CLI, background job, API service, or distributed workers? | Isolation, queues, limits, health checks, and rollback can be exercised |
| Portability | Must models or data providers be interchangeable? | Adapter contract tests preserve required semantics |

Specific project names and current features change quickly, so they appear only in the standalone [bilingual selection matrix](../../code/go-agentic/06-lifecycle/selection_matrix.md). The chapter uses stable selection vocabulary; names in the matrix are current examples that require verification.

### 6.3.3 Build, Buy, and the Smallest Core

Building a minimal harness provides transparent control and a small dependency surface, while taking responsibility for sessions, tracing, approvals, concurrency, and deployment. Existing components can shorten delivery, but their abstractions must preserve the task's required state, authority, and error semantics. Select the smallest maintainable system that satisfies every required capability.

## 6.4 Prototype and Evaluation

### 6.4.1 Start with a Vertical Slice

The first prototype needs one real end-to-end path: a representative task, a minimal Tool set, a deterministic Environment fixture, a verifier, and a termination budget. Prove harness semantics with a fixed policy before connecting a model to measure decision quality. This separates control defects from model variation.

The prototype must run at least four trace classes:

1. success with evidence;
2. recovery after a correctable failure;
3. denial of an invalid or unauthorized Action;
4. budget termination when completion is impossible.

The course's first three code directories form this growth path: minimal loop, loop patterns, then Tool and retrieval Environment. They are independent fixtures with consistent vocabulary and boundaries.

### 6.4.2 Evaluate Outcomes, Traces, and the System

| Level | Core question | Example metric |
| --- | --- | --- |
| Task outcome | Was the goal completed with valid evidence? | Verified success rate, correctness, citation validity |
| Trace | Was an allowed and effective path used? | Invalid Tool rate, repeated Actions, recovery rate, steps |
| Safety | Were authority and data boundaries respected? | Unauthorized executions, sensitive-data leaks, approval bypass rate |
| System | Did it operate reliably within resource targets? | p50/p95 latency, cost per task, timeouts, availability |
| Human factors | Can users understand, correct, and trust the result? | Escalation quality, denial clarity, handling time |

The denominator of `verified success rate` is the full task set, not only examples the agent claims to have completed. Cost should also be measured per verified task rather than only per model call.

### 6.4.3 Datasets and Thresholds

Use a development set for iteration, a frozen regression set to stop degradation, and a challenge set to discover new failures. Before production examples enter a dataset, remove sensitive data, confirm use rights, and label provenance. Each example stores input, Environment version, allowed Actions, success criteria, and expected stop class. Do not require one unique “golden trace” unless the path itself is a compliance requirement.

Write release thresholds before running the frozen set. For example: verified success on critical tasks at least 95%, unauthorized executions exactly 0, p95 below 8 seconds, and cost per task below a stated cap. Stratify thresholds by risk so a large number of easy cases cannot hide a few high-impact failures.

## 6.5 Observability and Security Review

### 6.5.1 One Correlated Trace

Connect every event with stable `run_id`, `step_id`, and `parent_id` fields:

```text
task_version, environment_version, model_version,
state, route, tool_name, argument_digest,
permission_decision, observation_code, verifier_result,
latency, token_usage, tool_cost, output_reference
```

A trace answers “which layer and step failed, and on what evidence?” Logs capture discrete events, metrics aggregate trends, traces show causal paths across components, and artifacts store large outputs. None should substitute for all the others.

Alerts should identify actionable conditions such as falling verified success, rising repeated errors, an unusual increase in authority denials, p95 violations, or cost drift. Do not alert on every model hesitation or normal empty retrieval.

### 6.5.2 Security Review Starts with the Authority Graph

The threat model should draw trust boundaries among the user, model, harness, Tools, data sources, external systems, and human approval.

| Threat | Entry | Primary controls | Verification method |
| --- | --- | --- | --- |
| Prompt / retrieval injection | User input, web, documents, Tool output | Instruction-data separation, provenance, least privilege | Adversarial fixture attempts to expand authority |
| Excess authority | Broad Tools, shared credentials | Fine-grained capabilities, short-lived credentials, argument-bound approval | Unauthorized call must fail before execution |
| Data leakage | Prompt, trace, errors, outbound calls | Data classification, masking, egress policy, retention | Canary data and log audit |
| Unsafe side effect | File write, message, transaction, deployment | Sandbox, idempotency, approval, compensating action | Replay, partial-failure, and rollback tests |
| Supply-chain change | Model, dependency, Tool, index upgrade | Version pinning, source verification, regression set | Differential evaluation before and after upgrade |
| Resource exhaustion | Infinite loop, large output, parallel storm | Step/time/cost budgets, concurrency limit | Load and budget-termination tests |

The security-review output is not a sentence saying “secure.” It is a list of threats, controls, test evidence, owners, and residual risks.

## 6.6 Deployment and Continued Operation

### 6.6.1 Release Gates

Before release, check that:

- prompts, Tool schemas, model configuration, Environment, and evaluation set are versioned;
- production authority is no broader than authority tested during evaluation;
- timeout, retry, idempotency, cancellation, checkpoint, and recovery have been exercised;
- dashboards and alerts expose success, safety, latency, and cost;
- the runbook names owners for degradation, Tool disablement, traffic pause, and rollback;
- data retention, deletion, audit, and user notice meet organizational requirements.

### 6.6.2 Canary, Rollback, and State Migration

Start with shadow traffic or a small volume of low-risk tasks, then expand gradually. A canary comparison must use task outcomes rather than process health alone. A rollback unit includes mutually compatible prompt, model configuration, Tool schema, and state versions.

With durable sessions, old code may not read new state, so use forward compatibility, a migration, or draining after stopping new work. Code rollback cannot automatically undo external side effects; those need idempotency keys, transactions, or explicit compensation.

### 6.6.3 Continuous Evaluation

Production should record only the governed minimum. Sample failures, human escalations, low-confidence cases, and new task types; after redaction and labeling, add them to the challenge set. When degradation appears, first locate whether task distribution, model, harness, Tool, data, or deployment changed, then update the corresponding control and regression example.

## 6.7 Lifecycle Anti-Patterns

| Anti-pattern | Consequence | Alternative |
| --- | --- | --- |
| Select technology before defining the task | Candidate capabilities rewrite the requirement | Freeze the task contract and required capabilities first |
| Treat a demo as evaluation | Happy paths hide denial and termination defects | Build a stratified task set and thresholds |
| Score final text only | Unauthorized or wasteful paths stay invisible | Score outcome, trace, safety, and system together |
| Tune only the prompt | Control, Tool, or data defects are hidden | Locate the responsible layer, then change the smallest component |
| Release to all traffic | Rare, high-impact faults reach users directly | Canary, kill switch, and rollback drill |
| Record everything | Sensitive data leaks and cost rises | Minimize by purpose, mask, and set retention |
| Keep unversioned state | Upgrades cannot resume or compare | Version every input and durable state |

## 6.8 Chapter Summary

- Agent development starts with the task and Environment, using evaluable boundaries to constrain autonomy.
- Model and harness selection must be supported by a frozen task set and capability matrix.
- A vertical prototype proves success, recovery, denial, and termination before scope expands.
- Evaluation covers outcome, trace, safety, system, and human factors, with release thresholds stratified by risk.
- Observable traces connect model, Tool, authority, Observation, and verifier; security review tests trust boundaries.
- Deployment requires versions, canary, rollback, state migration, and continuous evaluation beyond the initial release.

## Exercises

1. Write a Task Contract for “draft a reply from local support tickets,” including allowed Actions, forbidden Actions, success evidence, budgets, and escalation.
2. Complete the Environment table in 6.2.2 for that task and design a deterministic authority-denial fixture.
3. Mark the eight capabilities in the selection matrix as required, useful, or irrelevant. State the evidence two candidate prototypes must provide without selecting by name.
4. Design a 12-example evaluation set covering success, boundaries, no answer, conflict, Tool errors, authority, and budgets. Set a separate threshold for the high-risk subset.
5. Write one failed trace and explain how the dashboard, alert, and runbook each help handle it.
6. Design a 5% canary, kill switch, idempotency key, and compensation flow for an agent with an external write side effect.

## Mastery Standard

You meet this chapter's standard when you can turn an ambiguous product goal into Task and Environment contracts; select a Model and harness through task-set evidence and a capability matrix; define outcome, trace, safety, and system thresholds; locate a failure from a trace; and produce a security-reviewed release design with canary, rollback, and continuous evaluation.

## Primary Sources

1. NIST. [AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework).
2. NIST. [Secure Software Development Framework](https://csrc.nist.gov/Projects/ssdf).
3. OWASP. [Top 10 for Large Language Model Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/).
4. OpenTelemetry. [Tracing specification](https://opentelemetry.io/docs/specs/otel/trace/).
5. Google. [Site Reliability Engineering](https://sre.google/books/).
6. Breck, E. et al. (2017). [The ML Test Score: A Rubric for ML Production Readiness and Technical Debt Reduction](https://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/).
