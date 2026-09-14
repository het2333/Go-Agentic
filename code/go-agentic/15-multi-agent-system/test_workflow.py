"""Behavioral tests for the deterministic bounded multi-agent workflow."""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name("workflow.py")
SPEC = importlib.util.spec_from_file_location("bounded_multi_agent_workflow", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
workflow = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = workflow
SPEC.loader.exec_module(workflow)


def approve(prepared: object) -> object:
    preview = prepared.preview
    assert preview is not None
    return workflow.ApprovalDecision(
        approval_id="approval-001",
        actor="course-operator",
        approved=True,
        action_hash=preview.digest,
    )


def test_conflict_case_revises_an_immutable_artifact_through_explicit_handoffs() -> None:
    system = workflow.build_demo_workflow(case_id="conflicting_evidence")

    prepared = system.workflow.prepare()

    assert prepared.status == "awaiting_approval"
    findings = tuple(
        artifact
        for artifact in prepared.artifacts
        if artifact.kind == "research_findings"
    )
    assert [artifact.version for artifact in findings] == [1, 2]
    assert findings[1].parent_ids == (findings[0].artifact_id,)
    assert findings[0].field("resolution") == "unresolved"
    assert findings[1].field("resolution") == "conflict_disclosed"
    with pytest.raises(FrozenInstanceError):
        findings[0].version = 99

    routes = [
        (message.sender, message.recipient, message.kind)
        for message in prepared.messages
    ]
    assert routes == [
        ("planner", "researcher", "handoff"),
        ("researcher", "reviewer", "handoff"),
        ("reviewer", "researcher", "rejection"),
        ("researcher", "reviewer", "handoff"),
        ("reviewer", "executor", "acceptance"),
        ("executor", "human", "approval_request"),
    ]
    assert prepared.metrics.reviewer_rejections == 1
    assert prepared.metrics.retries == 1
    assert prepared.metrics.handoffs == 6


def test_execution_requires_matching_approval_and_replay_has_one_effect() -> None:
    system = workflow.build_demo_workflow(case_id="conflicting_evidence")
    prepared = system.workflow.prepare()
    preview = prepared.preview
    assert preview is not None

    missing = system.workflow.execute(None)
    mismatched = system.workflow.execute(
        workflow.ApprovalDecision(
            "approval-wrong", "course-operator", True, "wrong-hash"
        )
    )

    assert missing.status == "awaiting_approval"
    assert mismatched.status == "awaiting_approval"
    assert mismatched.last_error == "approval does not match the action preview"
    assert [event.kind for event in mismatched.audit_events][-2:] == [
        "approval_missing",
        "approval_mismatch",
    ]
    assert system.gateway.effects == ()

    accepted = approve(prepared)
    completed = system.workflow.execute(accepted)
    replayed = system.workflow.execute(accepted)

    assert completed.status == "completed"
    assert replayed.receipt == completed.receipt
    assert len(system.gateway.effects) == 1
    assert {event.kind for event in replayed.audit_events} >= {
        "approval_recorded",
        "execution_completed",
    }


def test_review_rejection_stops_after_the_retry_budget() -> None:
    system = workflow.build_demo_workflow(
        case_id="conflicting_evidence",
        max_review_retries=1,
        reviewer_policy="always_reject",
    )

    result = system.workflow.prepare()

    assert result.status == "review_rejected"
    assert result.preview is None
    assert result.metrics.reviewer_rejections == 2
    assert result.metrics.retries == 1
    assert result.last_error == "review retry budget exhausted"
    assert system.gateway.effects == ()
    assert result.audit_events[-1].kind == "workflow_stopped"


def test_role_failure_and_cost_exhaustion_are_contained_before_execution() -> None:
    failed_system = workflow.build_demo_workflow(
        case_id="routine", fail_role="researcher"
    )
    failed = failed_system.workflow.prepare()

    assert failed.status == "failed"
    assert failed.last_error == "researcher failed deterministically"
    assert [artifact.kind for artifact in failed.artifacts] == ["plan"]
    assert failed.audit_events[-1].kind == "role_failed"
    assert failed_system.gateway.effects == ()

    budgeted_system = workflow.build_demo_workflow(
        case_id="routine", max_cost_units=2
    )
    exhausted = budgeted_system.workflow.prepare()

    assert exhausted.status == "budget_exhausted"
    assert exhausted.metrics.cost_units <= 2
    assert exhausted.preview is None
    assert exhausted.audit_events[-1].kind == "budget_exhausted"
    assert budgeted_system.gateway.effects == ()


def test_metrics_show_when_coordination_earns_its_extra_cost() -> None:
    routine = workflow.compare_case("routine")
    complex_case = workflow.compare_case("conflicting_evidence")

    assert routine.baseline.quality_score == routine.multi_agent.quality_score == 100
    assert routine.incremental_cost == 2
    assert routine.worth_extra_cost is False

    assert complex_case.baseline.quality_score == 55
    assert complex_case.baseline.safety_violations == 1
    assert complex_case.multi_agent.quality_score == 100
    assert complex_case.multi_agent.safety_violations == 0
    assert complex_case.incremental_quality == 45
    assert complex_case.incremental_cost == 5
    assert complex_case.worth_extra_cost is True


def test_single_agent_baseline_runs_the_same_fixture_and_exposes_trajectory() -> None:
    routine = workflow.run_single_agent("routine")
    conflict = workflow.run_single_agent("conflicting_evidence")

    assert routine.evidence_ids == conflict.evidence_ids == (
        "email",
        "erp",
        "contract",
        "logistics",
    )
    assert [step.action for step in conflict.trajectory] == [
        "collect_evidence_and_draft",
        "create_action_preview",
        "execute_external_effect",
    ]
    assert [step.cost_units for step in conflict.trajectory] == [2, 1, 1]
    assert conflict.status == "completed"
    assert conflict.preview.kind == "action_preview"
    assert conflict.approval.action_hash == conflict.preview.digest
    assert conflict.receipt.action_hash == conflict.preview.digest
    assert [event.kind for event in conflict.audit_events] == [
        "draft_created",
        "preview_created",
        "approval_recorded",
        "execution_completed",
    ]
    assert conflict.metrics.cost_units == 4
    assert routine.action == "record_verified_delivery_update"
    assert conflict.action == "record_verified_delivery_update"
    assert conflict.metrics.quality_score == 55
    assert conflict.metrics.safety_violations == 1


def test_rejected_human_approval_is_terminal_and_audited() -> None:
    system = workflow.build_demo_workflow(case_id="routine")
    prepared = system.workflow.prepare()
    preview = prepared.preview
    assert preview is not None

    result = system.workflow.execute(
        workflow.ApprovalDecision(
            "approval-denied", "course-operator", False, preview.digest
        )
    )

    assert result.status == "approval_rejected"
    assert result.audit_events[-1].kind == "approval_rejected"
    assert system.gateway.effects == ()


def test_expired_approval_cannot_execute() -> None:
    system = workflow.build_demo_workflow(case_id="routine")
    prepared = system.workflow.prepare()
    preview = prepared.preview
    assert preview is not None

    result = system.workflow.execute(
        workflow.ApprovalDecision(
            "approval-expired",
            "course-operator",
            True,
            preview.digest,
            decided_at="2026-09-13T08:00:00+08:00",
            expires_at="2026-09-13T08:30:00+08:00",
        )
    )

    assert result.status == "awaiting_approval"
    assert result.last_error == "approval has expired"
    assert result.audit_events[-1].kind == "approval_invalid"
    assert system.gateway.effects == ()


def test_accepted_approval_survives_execution_budget_exhaustion() -> None:
    system = workflow.build_demo_workflow(case_id="routine", max_cost_units=5)
    prepared = system.workflow.prepare()
    accepted = approve(prepared)

    result = system.workflow.execute(accepted)

    assert result.status == "budget_exhausted"
    assert result.receipt is None
    assert system.gateway.effects == ()
    assert [event.kind for event in result.audit_events][-2:] == [
        "approval_recorded",
        "budget_exhausted",
    ]
    approval_details = dict(result.audit_events[-2].details)
    assert approval_details == {
        "action_hash": accepted.action_hash,
        "actor": accepted.actor,
        "approval_id": accepted.approval_id,
    }


def test_gateway_idempotency_collision_is_contained_and_audited() -> None:
    gateway = workflow.InMemoryActionGateway()
    colliding_preview = workflow.Artifact(
        artifact_id="seed:action_preview:v1",
        version=1,
        kind="action_preview",
        author="executor",
        content=(("idempotency_key", "supplier-delivery:routine"),),
        parent_ids=(),
        digest="different-action-hash",
    )
    existing_receipt = gateway.execute_once(colliding_preview)
    running = workflow.MultiAgentWorkflow(
        case_id="routine",
        gateway=gateway,
        max_review_retries=1,
        max_cost_units=12,
        reviewer_policy="normal",
        fail_role=None,
    )
    prepared = running.prepare()

    result = running.execute(approve(prepared))
    replayed = running.execute(approve(prepared))

    assert result.status == "gateway_failed"
    assert replayed == result
    assert result.receipt is None
    assert gateway.effects == (existing_receipt,)
    assert [event.kind for event in result.audit_events][-2:] == [
        "approval_recorded",
        "gateway_failed",
    ]
    assert dict(result.audit_events[-1].details) == {
        "action_hash": prepared.preview.digest,
        "failure_type": "idempotency_collision",
        "idempotency_key": "supplier-delivery:routine",
        "reason": "idempotency key is bound to another action",
        "recovery": "inspect_existing_receipt",
    }
