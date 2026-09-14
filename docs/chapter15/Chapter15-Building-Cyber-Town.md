# Chapter 15: Multi-Agent Systems Project

<figure class="course-hero">
  <img src="../assets/visuals/chapter-15.webp" alt="Specialized agent workshops exchange tasks through a coordinated cyber-town roundabout." width="1536" height="864" loading="lazy" decoding="async">
  <figcaption><em>Multi-agent systems divide roles while coordinating shared state and resources.</em></figcaption>
</figure>

The previous two chapters established enterprise-execution and deep-research contracts. This chapter composes them into a deliberately bounded multi-agent project: a planner defines the task, a researcher organizes evidence, a reviewer rejects defective artifacts, and an executor acts only after human approval. The legacy filename and Docsify URL remain, although the course project is no longer a cyber town.

The default code uses only the Python standard library. Its data is fixed in memory; it makes no network or model call and needs no API key. The Pi-compatible observation-action-verification loop remains the course's sole continuous practical mainline. Hermes appears only to explain the additional services required by a long-running runtime.

## 15.1 Prove That Multiple Agents Are Needed

### 15.1.1 Problem, Boundary, and Success Criteria

The case remains a supplier delivery anomaly. An email says an order shipped, while the logistics record may still say `pending`. The system may prepare a clarification message, but it cannot modify the purchase order or contract. Success does not mean that every role spoke. It means evidence coverage is complete, disagreement remains visible, review binds to a specific artifact, execution binds to human approval, and replay creates no second business effect.

Multiple agents are not the default answer. They add steps, context, failure points, and cost. Role separation is justified only when it materially improves quality or reduces risk.

### 15.1.2 Single-Agent Baseline

Run a comparable single-agent baseline first. It reads the same fixture, receives the same task, and uses the same scoring rule. Both architectures pass through the same draft, action preview, human approval, gateway execution, and audit safety envelope; the baseline only compresses internal reasoning into one role. It spends two units on reasoning, then one each on preview and execution, for a total cost of four. That is sufficient for the simple case; in the conflict case, it treats “shipped” as settled fact.

| Case | Baseline quality | Safety violations | Baseline cost | Multi-agent quality | Multi-agent cost | Worth the extra cost? |
|---|---:|---:|---:|---:|---:|---|
| `routine` | 100 | 0 | 4 | 100 | 6 | No: quality does not improve |
| `conflicting_evidence` | 55 | 1 | 4 | 100 | 9 | Yes: +45 points and one violation removed |

The teaching rule is that the multi-agent run must complete, gain at least 20 quality points, and have fewer safety violations than the baseline. This threshold belongs to the fixture. A real project must freeze its threshold before deployment using representative tasks, error costs, and available budget.

## 15.2 Four Roles and Verifiable Contracts

### 15.2.1 Responsibility Matrix

| Role | Input | Artifact | Explicitly forbidden |
|---|---|---|---|
| Planner | Task goal, risk, and budget | `plan` | Inventing evidence or causing an external effect |
| Researcher | `plan` and source records | `research_findings` | Hiding disagreement or approving its own result |
| Reviewer | A specific Findings version | `review` | Silently rewriting the reviewed artifact or acting |
| Executor | Accepted Review and Findings | `action_preview`, receipt | Acting without approval or widening scope |

A role name is not a security boundary. The Harness creates the real boundary through input types, permitted recipients, cost limits, artifact digests, the state machine, and Gateway authorization. Writing “you are the reviewer” in a Prompt cannot replace those controls.

### 15.2.2 Messages and Immutable Artifacts

Every cross-role handoff is an explicit `Message` with sender, recipient, kind, artifact IDs, and the next instruction. A recipient reads a fixed version instead of depending on chat history that may later be compacted.

```python
@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    version: int
    kind: str
    author: str
    content: tuple[tuple[str, str], ...]
    parent_ids: tuple[str, ...]
    digest: str
```

A revision creates v2 and places the v1 ID in `parent_ids`. Version 1 remains unchanged, so the audit log can answer what the reviewer rejected and what changed later. The digest covers ID, version, author, content, and parents; approval later binds to the action-preview digest.

## 15.3 The Bounded Orchestration State Machine

### 15.3.1 Normal Data Flow


Execution is split between `prepare()` and `execute(approval)`. The former can create at most an action preview. The latter touches the Gateway only after validating approval. This pause lets a UI, CLI, or ticket display the complete target, action, scope, and hash.

### 15.3.2 Reviewer Rejection and Bounded Retry

Version 1 of the conflict findings records both `email=shipped` and `logistics=pending`, yet recommends confirming shipment. The reviewer returns `rejected` with the issue “contradictory evidence is unresolved.” The default `max_review_retries=1` therefore allows only one v2. That revision narrows the recommendation to requesting clarification without changing the order.

If the second review also fails, the state becomes `review_rejected` and no action preview exists. The budget means “at most this many extra revisions,” not unlimited self-reflection. A reviewer veto must change control flow; it cannot leave advice and then permit execution.

### 15.3.3 Failure Containment, Budgets, and Approval

| Trigger | Terminal or paused state | Downstream effect | Audit evidence |
|---|---|---|---|
| Role raises an error | `failed` | Later roles do not run | `role_failed` |
| Next role would exceed cost | `budget_exhausted` | That role does not run | `budget_exhausted` |
| Reviewer retries exhausted | `review_rejected` | No preview or execution | `workflow_stopped` |
| Approval absent, expired, or hash differs | `awaiting_approval` | No execution | Rejection reason and `last_error` |
| Human rejects | `approval_rejected` | Terminal, with no execution | `approval_rejected` |
| Execution budget ends after approval | `budget_exhausted` | Gateway is not called | `approval_recorded`, then `budget_exhausted` |
| Gateway or idempotency-key collision | `gateway_failed` | No duplicate execution | Failure type, action hash, and recovery hint |
| Approval matches | `completed` | One idempotent execution | Approval, receipt, completion events |

Approval is valid for one `action_hash` and one time window. Timestamps must include a time zone, and approval must remain unexpired. If the target, action, scope, or source digest changes, the system must create a new preview and seek approval again. The Gateway binds its idempotency key to the preview digest. A replay returns the same receipt; a changed payload under the same key fails.

## 15.4 Run the Offline Project

### 15.4.1 Default Path

Run from the repository root:

```bash
python3 code/go-agentic/15-multi-agent-system/workflow.py
python3 -m pytest code/go-agentic/15-multi-agent-system/test_workflow.py -q
```

The output is fixed:

```text
routine: baseline_quality=100 multi_quality=100 baseline_cost=4 multi_cost=6 worth_extra_cost=False
conflicting_evidence: baseline_quality=55 multi_quality=100 baseline_cost=4 multi_cost=9 worth_extra_cost=True
```

This path installs nothing and reads no environment variable. The `.invalid` recipient is a fictional identifier; the in-memory Gateway sends no real message.

### 15.4.2 Read the Tested Behaviors

The tests run the real Workflow rather than asserting that a mock was called. They cover v1/v2 conflict revision, failure to mutate a frozen artifact, the six-handoff sequence, one review retry, no execution with missing approval or a wrong hash, one effect on approved replay, exhausted reviewer rejection, role failure, cost exhaustion, human rejection, post-approval execution-budget exhaustion, a real idempotency-key collision, and shared metrics over the same safety envelope in both designs.

```python
system = build_demo_workflow(case_id="conflicting_evidence")
prepared = system.workflow.prepare()
approval = ApprovalDecision(
    approval_id="approval-001",
    actor="operator",
    approved=True,
    action_hash=prepared.preview.digest,
)
completed = system.workflow.execute(approval)
assert completed.status == "completed"
assert len(system.gateway.effects) == 1
```

## 15.5 Shared Evaluation Instead of Role Counting

### 15.5.1 Metric Definitions

| Metric | Definition | Purpose |
|---|---|---|
| `quality_score` | Task-result score from 0 to 100 | Compare correctness and evidence handling |
| `safety_violations` | Unauthorized actions, hidden conflicts, or unapproved executions | Prevent a high score from hiding a dangerous trajectory |
| `steps` | Role calls plus external executions | Measure trajectory length |
| `cost_units` | Sum of frozen per-role costs | Create a reproducible budget |
| `handoffs` | Number of explicit Messages | Measure coordination load |
| `retries` | Extra revisions after reviewer rejection | Verify the bound |
| `reviewer_rejections` | Actual reviewer vetoes | Distinguish review presence from review effectiveness |

The same case must use the same input, scorer, forbidden-action set, and draft, preview, approval, execution, and audit envelope. After fixing the envelope cost, compare only differences caused by reasoning and role coordination. Do not give the multi-agent design more complete evidence and then claim that its architecture is better. Do not compare completion alone while ignoring whether a system completed through the wrong action.

### 15.5.2 When to Upgrade the Architecture

Prefer one agent for simple, low-risk, single-domain work with fast verification. Consider a multi-agent experiment when at least two conditions hold: evidence crosses permission domains; independent contradiction search is needed; separation of duties is required; one error is costly; the task divides into clearly acceptable artifacts; or evaluation shows that one agent repeatedly fails at a specific boundary.

Even after the multi-agent design wins, ablate each role. Does removing the reviewer restore the contradiction failure? Can planner and researcher merge without reducing quality? If a role contributes no measured value, remove it.

## 15.6 Pi Mainline and Long-Running Runtime Comparison

### 15.6.1 Pi-Compatible Practical Mainline

Pi's small Harness keeps the chapter's core visible: reading a task or artifact is an Observation; role policy chooses the next step; files, commands, or custom Tools are Actions; tests and review are Verification; and the session tree plus files can carry handoffs. In a real Pi integration, place role protocols and review rules in versioned Skills, Extensions, or file contracts instead of allowing four unbounded chat processes to prompt one another.

The local Python fixture is an executable miniature of those concepts, not a reimplementation of the Pi SDK. It deliberately removes the model so the control structure can be verified first.

### 15.6.2 Hermes as the Long-Running Runtime Comparison

According to official material checked **as of 2026-09-13**, Hermes Agent combines persistent memory, cron scheduling, messaging gateways, MCP integrations, and isolated subagents in a long-running runtime. These capabilities change deployment questions: how state survives sessions, when work wakes, which channel receives it, how external systems are called, and how subtasks are isolated.

| Long-running need | Chapter's Pi-compatible fixture | Question raised by Hermes |
|---|---|---|
| Memory | Artifacts and audit live in one process | Writes, retrieval, expiry, and tenant isolation |
| Cron | No background wakeup | Re-entry, missed schedules, time zones, duplicate triggers |
| Gateways | In-memory effect | Channel authentication, rate limits, receipt correlation |
| MCP | Conceptual boundary only | Server authority, source trust, Tool versioning |
| Subagents | Sequential role objects | Sandboxing, quotas, cancellation, result collection |

Hermes does not become an executable course mainline. Before migrating this example to a long-running runtime, persist state, artifacts, approvals, and idempotency semantics. DeepSeek Harness remains only the pluginized-Harness comparison; this chapter does not expand a second implementation path.

## 15.7 From Fixture to Production

### 15.7.1 Security and Operations Contracts

A production system needs at least role- and tenant-scoped authorization; durable artifacts and audit logs with integrity checks; sensitive-field minimization and retention limits; untrusted-input isolation; Tool argument schemas; concurrent idempotency and provider-receipt lookup; approval identity, expiry, and revocation; timeout, cancellation, and compensation; plus metrics, tracing, alerting, and incident response.

Multiple agents amplify prompt-injection and permission-chaining risk. A page read by the researcher cannot direct the executor. Reviewer acceptance cannot enlarge Gateway authority. Shared memory cannot become a cross-tenant data channel. Give each role only the capabilities required by its contract.

### 15.7.2 Limitations

A fixture score of 100 is not real-world accuracy. Handwritten cases and scoring prove only that control flow, versions, boundaries, and metric calculations are repeatable. They do not prove that a model understands a real contract, that evidence semantically entails a claim, that concurrent writes are safe, or that distributed exactly-once delivery exists. Production conclusions require private evaluation sets, blind review, failure taxonomy, stress tests, and continuous monitoring.

## 15.8 Exercises, Mastery, and Sources

### 15.8.1 Exercises

1. Add a `missing_evidence` case: the researcher must stop, then create a new version in the same task after evidence arrives.
2. Add an approval-revocation record, with a test proving an unexpired but revoked approval cannot execute.
3. Set `max_review_retries` to 0, 1, and 2; plot quality, cost, and latency.
4. Run an ablation without the planner or reviewer and explain the change under the same scorer.
5. Sketch a Hermes deployment with persistence and authority boundaries for memory, cron, gateways, MCP, and subagents, while retaining the local fixture as the semantic verifier.

### 15.8.2 Mastery Standard

You have mastered this chapter when you can establish a single-agent baseline first, explain every handoff through explicit messages and immutable artifacts, make reviewer rejection alter control flow, stop downstream execution on budget or role failure, bind human approval to an action hash, and use shared metrics to prove when coordination earns its cost.

### 15.8.3 Sources

1. Pi Coding Agent, [README](https://github.com/earendil-works/pi/tree/main/packages/coding-agent), [Extensions](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md), and [Session format](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/session-format.md).
2. Model Context Protocol, [Architecture](https://modelcontextprotocol.io/docs/learn/architecture) and [Security best practices](https://modelcontextprotocol.io/specification/draft/basic/security_best_practices).
3. OpenAI, [Safety in building agents](https://platform.openai.com/docs/guides/agent-builder-safety).
4. AWS Builders' Library, [Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/).
5. Nous Research, [Hermes Agent repository](https://github.com/NousResearch/hermes-agent) and [documentation](https://hermes-agent.nousresearch.com/docs/).
6. NIST, [AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework).
