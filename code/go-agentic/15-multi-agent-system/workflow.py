"""Deterministic bounded multi-agent workflow teaching fixture.

The module deliberately uses only the Python standard library. It models role
boundaries, immutable artifacts, review retries, approval, containment, and
comparative metrics without a model call, network request, or API key.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Mapping, TypeAlias


CaseId: TypeAlias = Literal["routine", "conflicting_evidence"]
Role: TypeAlias = Literal[
    "planner", "researcher", "reviewer", "executor", "single_agent", "human"
]
WorkflowStatus: TypeAlias = Literal[
    "created",
    "awaiting_approval",
    "approval_rejected",
    "review_rejected",
    "budget_exhausted",
    "gateway_failed",
    "failed",
    "completed",
]
ReviewerPolicy: TypeAlias = Literal["normal", "always_reject"]
DEMO_NOW = datetime.fromisoformat("2026-09-13T09:00:00+08:00")


ROLE_COSTS: Mapping[str, int] = {
    "planner": 1,
    "researcher": 2,
    "reviewer": 1,
    "executor": 1,
    "external_effect": 1,
}

CASE_EVIDENCE: Mapping[CaseId, tuple[tuple[str, str], ...]] = {
    "routine": (
        ("email", "shipped"),
        ("erp", "open"),
        ("contract", "tracking_required"),
        ("logistics", "in_transit:ZX-42"),
    ),
    "conflicting_evidence": (
        ("email", "shipped"),
        ("erp", "open"),
        ("contract", "tracking_required"),
        ("logistics", "pending:no_tracking"),
    ),
}


def _digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    version: int
    kind: str
    author: Role
    content: tuple[tuple[str, str], ...]
    parent_ids: tuple[str, ...]
    digest: str

    def field(self, name: str) -> str:
        try:
            return dict(self.content)[name]
        except KeyError as error:
            raise KeyError(f"artifact field not found: {name}") from error


@dataclass(frozen=True)
class Message:
    message_id: str
    sender: Role
    recipient: Role
    kind: str
    artifact_ids: tuple[str, ...]
    instruction: str


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    sequence: int
    kind: str
    role: str
    details: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class ApprovalDecision:
    approval_id: str
    actor: str
    approved: bool
    action_hash: str
    decided_at: str = "2026-09-13T08:59:00+08:00"
    expires_at: str = "2026-09-13T09:05:00+08:00"


@dataclass(frozen=True)
class ExecutionReceipt:
    receipt_id: str
    idempotency_key: str
    action_hash: str


@dataclass(frozen=True)
class RunMetrics:
    approach: str
    quality_score: int
    safety_violations: int
    completed: bool
    steps: int
    cost_units: int
    handoffs: int
    retries: int
    reviewer_rejections: int


@dataclass(frozen=True)
class TrajectoryStep:
    action: str
    cost_units: int
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class BaselineResult:
    case_id: CaseId
    evidence_ids: tuple[str, ...]
    action: str
    status: WorkflowStatus
    artifacts: tuple[Artifact, ...]
    audit_events: tuple[AuditEvent, ...]
    preview: Artifact
    approval: ApprovalDecision
    receipt: ExecutionReceipt
    trajectory: tuple[TrajectoryStep, ...]
    metrics: RunMetrics


@dataclass(frozen=True)
class WorkflowResult:
    case_id: CaseId
    status: WorkflowStatus
    artifacts: tuple[Artifact, ...]
    messages: tuple[Message, ...]
    audit_events: tuple[AuditEvent, ...]
    metrics: RunMetrics
    preview: Artifact | None = None
    receipt: ExecutionReceipt | None = None
    last_error: str | None = None


@dataclass(frozen=True)
class Comparison:
    case_id: CaseId
    baseline: RunMetrics
    multi_agent: RunMetrics
    incremental_quality: int
    incremental_cost: int
    worth_extra_cost: bool


@dataclass(frozen=True)
class DemoSystem:
    workflow: "MultiAgentWorkflow"
    gateway: "InMemoryActionGateway"


class BudgetExhausted(RuntimeError):
    pass


class RoleFailed(RuntimeError):
    pass


class GatewayFailure(RuntimeError):
    def __init__(self, message: str, *, failure_type: str, recovery: str) -> None:
        super().__init__(message)
        self.failure_type = failure_type
        self.recovery = recovery


class InMemoryActionGateway:
    """A deterministic idempotent boundary standing in for a real side effect."""

    def __init__(self) -> None:
        self._effects: dict[str, ExecutionReceipt] = {}

    @property
    def effects(self) -> tuple[ExecutionReceipt, ...]:
        return tuple(self._effects.values())

    def execute_once(self, preview: Artifact) -> ExecutionReceipt:
        idempotency_key = preview.field("idempotency_key")
        existing = self._effects.get(idempotency_key)
        if existing is not None:
            if existing.action_hash != preview.digest:
                raise GatewayFailure(
                    "idempotency key is bound to another action",
                    failure_type="idempotency_collision",
                    recovery="inspect_existing_receipt",
                )
            return existing
        receipt = ExecutionReceipt(
            receipt_id="receipt-" + _digest({"key": idempotency_key})[:12],
            idempotency_key=idempotency_key,
            action_hash=preview.digest,
        )
        self._effects[idempotency_key] = receipt
        return receipt


class MultiAgentWorkflow:
    def __init__(
        self,
        *,
        case_id: CaseId,
        gateway: InMemoryActionGateway,
        max_review_retries: int,
        max_cost_units: int,
        reviewer_policy: ReviewerPolicy,
        fail_role: str | None,
    ) -> None:
        if case_id not in {"routine", "conflicting_evidence"}:
            raise ValueError(f"unknown case: {case_id}")
        if max_review_retries < 0:
            raise ValueError("max_review_retries must be non-negative")
        if max_cost_units < 1:
            raise ValueError("max_cost_units must be positive")
        if reviewer_policy not in {"normal", "always_reject"}:
            raise ValueError(f"unknown reviewer policy: {reviewer_policy}")
        if fail_role not in {None, "planner", "researcher", "reviewer", "executor"}:
            raise ValueError(f"unknown fail role: {fail_role}")
        self.case_id = case_id
        self._gateway = gateway
        self._max_review_retries = max_review_retries
        self._max_cost_units = max_cost_units
        self._reviewer_policy = reviewer_policy
        self._fail_role = fail_role
        self._status: WorkflowStatus = "created"
        self._artifacts: list[Artifact] = []
        self._messages: list[Message] = []
        self._audit_events: list[AuditEvent] = []
        self._cost_units = 0
        self._steps = 0
        self._retries = 0
        self._reviewer_rejections = 0
        self._preview: Artifact | None = None
        self._receipt: ExecutionReceipt | None = None
        self._last_error: str | None = None

    def _audit(self, kind: str, role: str, **details: object) -> None:
        sequence = len(self._audit_events) + 1
        self._audit_events.append(
            AuditEvent(
                event_id=f"{self.case_id}:event:{sequence}",
                sequence=sequence,
                kind=kind,
                role=role,
                details=tuple(
                    sorted((key, str(value)) for key, value in details.items())
                ),
            )
        )

    def _invoke(self, role: Role) -> None:
        cost = ROLE_COSTS[role]
        if self._cost_units + cost > self._max_cost_units:
            raise BudgetExhausted(f"cost budget exhausted before {role}")
        self._cost_units += cost
        self._steps += 1
        self._audit("role_started", role, cost_units=cost)
        if self._fail_role == role:
            raise RoleFailed(f"{role} failed deterministically")

    def _artifact(
        self,
        *,
        kind: str,
        author: Role,
        content: Mapping[str, str],
        parent_ids: tuple[str, ...] = (),
    ) -> Artifact:
        version = 1 + sum(item.kind == kind for item in self._artifacts)
        artifact_id = f"{self.case_id}:{kind}:v{version}"
        frozen_content = tuple(sorted(content.items()))
        artifact = Artifact(
            artifact_id=artifact_id,
            version=version,
            kind=kind,
            author=author,
            content=frozen_content,
            parent_ids=parent_ids,
            digest=_digest(
                {
                    "artifact_id": artifact_id,
                    "author": author,
                    "content": frozen_content,
                    "kind": kind,
                    "parents": parent_ids,
                    "version": version,
                }
            ),
        )
        self._artifacts.append(artifact)
        self._audit(
            "artifact_created",
            author,
            artifact_id=artifact.artifact_id,
            digest=artifact.digest,
            version=version,
        )
        return artifact

    def _message(
        self,
        sender: Role,
        recipient: Role,
        kind: str,
        artifacts: tuple[Artifact, ...],
        instruction: str,
    ) -> None:
        sequence = len(self._messages) + 1
        message = Message(
            message_id=f"{self.case_id}:message:{sequence}",
            sender=sender,
            recipient=recipient,
            kind=kind,
            artifact_ids=tuple(item.artifact_id for item in artifacts),
            instruction=instruction,
        )
        self._messages.append(message)
        self._audit(
            "message_sent",
            sender,
            message_id=message.message_id,
            recipient=recipient,
            artifact_ids=message.artifact_ids,
        )

    def _result(self) -> WorkflowResult:
        successful_review = self._preview is not None
        quality, safety_violations = (
            _evaluate_action(self.case_id, self._preview.field("action"))
            if successful_review
            else (0, 0)
        )
        if self._status == "review_rejected":
            quality = 20
        return WorkflowResult(
            case_id=self.case_id,
            status=self._status,
            artifacts=tuple(self._artifacts),
            messages=tuple(self._messages),
            audit_events=tuple(self._audit_events),
            metrics=RunMetrics(
                approach="multi_agent",
                quality_score=quality,
                safety_violations=safety_violations,
                completed=self._status == "completed",
                steps=self._steps,
                cost_units=self._cost_units,
                handoffs=len(self._messages),
                retries=self._retries,
                reviewer_rejections=self._reviewer_rejections,
            ),
            preview=self._preview,
            receipt=self._receipt,
            last_error=self._last_error,
        )

    def _stop(
        self,
        status: WorkflowStatus,
        error: str,
        event: str,
        **details: object,
    ) -> WorkflowResult:
        self._status = status
        self._last_error = error
        self._audit(event, "orchestrator", reason=error, **details)
        return self._result()

    def prepare(self) -> WorkflowResult:
        if self._status != "created":
            return self._result()
        try:
            self._invoke("planner")
            plan = self._artifact(
                kind="plan",
                author="planner",
                content={
                    "goal": "resolve supplier delivery status",
                    "required_evidence": "email,erp,contract,logistics",
                    "risk": "external supplier communication",
                },
            )
            self._message(
                "planner",
                "researcher",
                "handoff",
                (plan,),
                "Collect the required evidence and preserve disagreements.",
            )

            self._invoke("researcher")
            findings = self._research(plan, revision=False)
            self._message(
                "researcher",
                "reviewer",
                "handoff",
                (findings,),
                "Check evidence coverage, conflicts, and action scope.",
            )

            while True:
                self._invoke("reviewer")
                accepted, review = self._review(findings)
                if accepted:
                    self._message(
                        "reviewer",
                        "executor",
                        "acceptance",
                        (review, findings),
                        "Prepare the bounded action preview; do not execute it.",
                    )
                    break
                self._reviewer_rejections += 1
                if self._retries >= self._max_review_retries:
                    return self._stop(
                        "review_rejected",
                        "review retry budget exhausted",
                        "workflow_stopped",
                    )
                self._message(
                    "reviewer",
                    "researcher",
                    "rejection",
                    (review, findings),
                    "Resolve the stated issue in a new artifact version.",
                )
                self._retries += 1
                self._invoke("researcher")
                findings = self._research(plan, revision=True, previous=findings)
                self._message(
                    "researcher",
                    "reviewer",
                    "handoff",
                    (findings,),
                    "Review the revised evidence artifact.",
                )

            self._invoke("executor")
            self._preview = self._action_preview(findings, review)
            self._message(
                "executor",
                "human",
                "approval_request",
                (self._preview,),
                "Approve or reject this exact action hash.",
            )
            self._status = "awaiting_approval"
            self._audit(
                "approval_required",
                "orchestrator",
                action_hash=self._preview.digest,
            )
            return self._result()
        except BudgetExhausted as error:
            return self._stop("budget_exhausted", str(error), "budget_exhausted")
        except RoleFailed as error:
            return self._stop("failed", str(error), "role_failed")

    def _research(
        self,
        plan: Artifact,
        *,
        revision: bool,
        previous: Artifact | None = None,
    ) -> Artifact:
        evidence_text = "; ".join(
            f"{source}={value}" for source, value in CASE_EVIDENCE[self.case_id]
        )
        if self.case_id == "routine":
            content = {
                "coverage": "4/4",
                "evidence": evidence_text,
                "recommendation": "record the verified delivery update",
                "resolution": "consistent",
            }
        elif revision:
            content = {
                "coverage": "4/4",
                "evidence": evidence_text,
                "recommendation": "request clarification without changing the order",
                "resolution": "conflict_disclosed",
            }
        else:
            content = {
                "coverage": "4/4",
                "evidence": evidence_text,
                "recommendation": "record shipment as confirmed",
                "resolution": "unresolved",
            }
        return self._artifact(
            kind="research_findings",
            author="researcher",
            content=content,
            parent_ids=(previous.artifact_id,) if previous else (plan.artifact_id,),
        )

    def _review(self, findings: Artifact) -> tuple[bool, Artifact]:
        accepted = (
            self._reviewer_policy == "normal"
            and findings.field("resolution") != "unresolved"
        )
        decision = "accepted" if accepted else "rejected"
        issue = "none" if accepted else "contradictory evidence is unresolved"
        review = self._artifact(
            kind="review",
            author="reviewer",
            content={
                "decision": decision,
                "issue": issue,
                "reviewed_digest": findings.digest,
            },
            parent_ids=(findings.artifact_id,),
        )
        return accepted, review

    def _action_preview(self, findings: Artifact, review: Artifact) -> Artifact:
        action = (
            "record_verified_delivery_update"
            if self.case_id == "routine"
            else "send_supplier_clarification_request"
        )
        return self._artifact(
            kind="action_preview",
            author="executor",
            content={
                "action": action,
                "idempotency_key": f"supplier-delivery:{self.case_id}",
                "scope": "one fixture order; no contract or PO mutation",
                "review_digest": review.digest,
                "source_digest": findings.digest,
                "target": "supplier@example.invalid",
            },
            parent_ids=(findings.artifact_id, review.artifact_id),
        )

    def execute(self, approval: ApprovalDecision | None) -> WorkflowResult:
        if self._status in {
            "completed",
            "approval_rejected",
            "review_rejected",
            "budget_exhausted",
            "gateway_failed",
            "failed",
        }:
            return self._result()
        if self._status != "awaiting_approval" or self._preview is None:
            raise RuntimeError("prepare must produce an action preview before execute")
        if approval is None:
            self._last_error = "human approval is required"
            self._audit("approval_missing", "orchestrator", action_hash=self._preview.digest)
            return self._result()
        if approval.action_hash != self._preview.digest:
            self._last_error = "approval does not match the action preview"
            self._audit(
                "approval_mismatch",
                "orchestrator",
                approval_id=approval.approval_id,
                expected_hash=self._preview.digest,
                received_hash=approval.action_hash,
            )
            return self._result()
        approval_error = self._approval_error(approval)
        if approval_error is not None:
            self._last_error = approval_error
            self._audit(
                "approval_invalid",
                "orchestrator",
                approval_id=approval.approval_id,
                reason=approval_error,
            )
            return self._result()
        if not approval.approved:
            self._status = "approval_rejected"
            self._last_error = None
            self._audit(
                "approval_rejected",
                "human",
                actor=approval.actor,
                approval_id=approval.approval_id,
                action_hash=approval.action_hash,
            )
            return self._result()
        self._audit(
            "approval_recorded",
            "human",
            actor=approval.actor,
            approval_id=approval.approval_id,
            action_hash=approval.action_hash,
        )
        try:
            cost = ROLE_COSTS["external_effect"]
            if self._cost_units + cost > self._max_cost_units:
                raise BudgetExhausted("cost budget exhausted before external effect")
            self._cost_units += cost
            self._steps += 1
            self._receipt = self._gateway.execute_once(self._preview)
            self._status = "completed"
            self._last_error = None
            self._audit(
                "execution_completed",
                "executor",
                action_hash=self._preview.digest,
                receipt_id=self._receipt.receipt_id,
            )
            return self._result()
        except BudgetExhausted as error:
            return self._stop("budget_exhausted", str(error), "budget_exhausted")
        except GatewayFailure as error:
            return self._stop(
                "gateway_failed",
                str(error),
                "gateway_failed",
                action_hash=self._preview.digest,
                failure_type=error.failure_type,
                idempotency_key=self._preview.field("idempotency_key"),
                recovery=error.recovery,
            )

    @staticmethod
    def _approval_error(approval: ApprovalDecision) -> str | None:
        try:
            decided_at = datetime.fromisoformat(approval.decided_at)
            expires_at = datetime.fromisoformat(approval.expires_at)
        except ValueError:
            return "approval timestamps are invalid"
        if decided_at.tzinfo is None or expires_at.tzinfo is None:
            return "approval timestamps must include a timezone"
        if expires_at <= decided_at:
            return "approval expiry must be after its decision time"
        if decided_at > DEMO_NOW:
            return "approval decision time is in the future"
        if expires_at <= DEMO_NOW:
            return "approval has expired"
        return None


def build_demo_workflow(
    *,
    case_id: CaseId,
    max_review_retries: int = 1,
    max_cost_units: int = 12,
    reviewer_policy: ReviewerPolicy = "normal",
    fail_role: str | None = None,
) -> DemoSystem:
    gateway = InMemoryActionGateway()
    return DemoSystem(
        workflow=MultiAgentWorkflow(
            case_id=case_id,
            gateway=gateway,
            max_review_retries=max_review_retries,
            max_cost_units=max_cost_units,
            reviewer_policy=reviewer_policy,
            fail_role=fail_role,
        ),
        gateway=gateway,
    )


def _evaluate_action(case_id: CaseId, action: str) -> tuple[int, int]:
    expected = {
        "routine": "record_verified_delivery_update",
        "conflicting_evidence": "send_supplier_clarification_request",
    }[case_id]
    if action == expected:
        return 100, 0
    if case_id == "conflicting_evidence" and action == "record_verified_delivery_update":
        return 55, 1
    return 0, 1


def run_single_agent(case_id: CaseId) -> BaselineResult:
    try:
        evidence = CASE_EVIDENCE[case_id]
    except KeyError as error:
        raise ValueError(f"unknown case: {case_id}") from error
    evidence_ids = tuple(source for source, _ in evidence)
    # The deliberately simple reasoner trusts the email's shipment claim first.
    action = "record_verified_delivery_update"
    quality_score, safety_violations = _evaluate_action(case_id, action)
    draft_id = f"{case_id}:single_agent_draft:v1"
    draft_content = tuple(
        sorted(
            {
                "action": action,
                "evidence": "; ".join(
                    f"{source}={value}" for source, value in evidence
                ),
            }.items()
        )
    )
    draft = Artifact(
        artifact_id=draft_id,
        version=1,
        kind="action_draft",
        author="single_agent",
        content=draft_content,
        parent_ids=(),
        digest=_digest(
            {
                "artifact_id": draft_id,
                "author": "single_agent",
                "content": draft_content,
                "kind": "action_draft",
                "parents": (),
                "version": 1,
            }
        ),
    )
    preview_id = f"{case_id}:action_preview:v1"
    preview_content = tuple(
        sorted(
            {
                "action": action,
                "idempotency_key": f"supplier-delivery:{case_id}",
                "scope": "one fixture order; no contract or PO mutation",
                "source_digest": draft.digest,
                "target": "supplier@example.invalid",
            }.items()
        )
    )
    preview = Artifact(
        artifact_id=preview_id,
        version=1,
        kind="action_preview",
        author="single_agent",
        content=preview_content,
        parent_ids=(draft.artifact_id,),
        digest=_digest(
            {
                "artifact_id": preview_id,
                "author": "single_agent",
                "content": preview_content,
                "kind": "action_preview",
                "parents": (draft.artifact_id,),
                "version": 1,
            }
        ),
    )
    approval = ApprovalDecision(
        approval_id=f"baseline-approval:{case_id}",
        actor="fixture-human",
        approved=True,
        action_hash=preview.digest,
    )
    if approval.action_hash != preview.digest:
        raise RuntimeError("baseline approval does not match the action preview")
    approval_error = MultiAgentWorkflow._approval_error(approval)
    if approval_error is not None or not approval.approved:
        raise RuntimeError(approval_error or "baseline approval was rejected")
    audit_events = [
        AuditEvent(
            f"{case_id}:baseline:event:1",
            1,
            "draft_created",
            "single_agent",
            (("artifact_id", draft.artifact_id), ("digest", draft.digest)),
        ),
        AuditEvent(
            f"{case_id}:baseline:event:2",
            2,
            "preview_created",
            "single_agent",
            (("action_hash", preview.digest), ("artifact_id", preview.artifact_id)),
        ),
        AuditEvent(
            f"{case_id}:baseline:event:3",
            3,
            "approval_recorded",
            "human",
            (
                ("action_hash", approval.action_hash),
                ("actor", approval.actor),
                ("approval_id", approval.approval_id),
            ),
        ),
    ]
    gateway = InMemoryActionGateway()
    receipt = gateway.execute_once(preview)
    audit_events.append(
        AuditEvent(
            f"{case_id}:baseline:event:4",
            4,
            "execution_completed",
            "single_agent",
            (("action_hash", preview.digest), ("receipt_id", receipt.receipt_id)),
        )
    )
    trajectory = (
        TrajectoryStep("collect_evidence_and_draft", 2, evidence_ids),
        TrajectoryStep(
            "create_action_preview", ROLE_COSTS["executor"], (draft.artifact_id,)
        ),
        TrajectoryStep(
            "execute_external_effect",
            ROLE_COSTS["external_effect"],
            (preview.artifact_id,),
        ),
    )
    return BaselineResult(
        case_id=case_id,
        evidence_ids=evidence_ids,
        action=action,
        status="completed",
        artifacts=(draft, preview),
        audit_events=tuple(audit_events),
        preview=preview,
        approval=approval,
        receipt=receipt,
        trajectory=trajectory,
        metrics=RunMetrics(
            approach="single_agent",
            quality_score=quality_score,
            safety_violations=safety_violations,
            completed=True,
            steps=len(trajectory),
            cost_units=sum(step.cost_units for step in trajectory),
            handoffs=0,
            retries=0,
            reviewer_rejections=0,
        ),
    )


def compare_case(case_id: CaseId) -> Comparison:
    baseline_result = run_single_agent(case_id)
    baseline = baseline_result.metrics
    system = build_demo_workflow(case_id=case_id)
    prepared = system.workflow.prepare()
    if prepared.preview is None:
        multi = prepared.metrics
    else:
        multi = system.workflow.execute(
            ApprovalDecision(
                approval_id=f"comparison-approval:{case_id}",
                actor="fixture-human",
                approved=True,
                action_hash=prepared.preview.digest,
            )
        ).metrics
    incremental_quality = multi.quality_score - baseline.quality_score
    incremental_cost = multi.cost_units - baseline.cost_units
    worth_extra_cost = (
        multi.completed
        and incremental_quality >= 20
        and multi.safety_violations < baseline.safety_violations
    )
    return Comparison(
        case_id=case_id,
        baseline=baseline,
        multi_agent=multi,
        incremental_quality=incremental_quality,
        incremental_cost=incremental_cost,
        worth_extra_cost=worth_extra_cost,
    )


def main() -> None:
    for case_id in ("routine", "conflicting_evidence"):
        comparison = compare_case(case_id)
        print(
            f"{case_id}: baseline_quality={comparison.baseline.quality_score} "
            f"multi_quality={comparison.multi_agent.quality_score} "
            f"baseline_cost={comparison.baseline.cost_units} "
            f"multi_cost={comparison.multi_agent.cost_units} "
            f"worth_extra_cost={comparison.worth_extra_cost}"
        )


if __name__ == "__main__":
    main()
