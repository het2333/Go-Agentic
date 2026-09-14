from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

import pytest


def _load_agent_module():
    module_name = "enterprise_execution_agent"
    module_path = Path(__file__).with_name("agent.py")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


agent_module = _load_agent_module()
ApprovalDecision = agent_module.ApprovalDecision
InMemoryAuditLog = agent_module.InMemoryAuditLog
build_demo_system = agent_module.build_demo_system


def _evidence_from(state, source: str):
    return next(record for record in state.evidence if record.source == source)


def _override_facts(source: str, facts: dict[str, object]):
    baseline = build_demo_system().agent.prepare("PO-7")
    original = _evidence_from(baseline, source)
    return agent_module.make_evidence_record(
        source=source,
        record_id=original.record_id,
        observed_at=original.observed_at,
        facts=facts,
    )


def test_prepare_collects_evidence_and_previews_missing_tracking_follow_up() -> None:
    system = build_demo_system()

    state = system.agent.prepare("PO-7")

    assert state.status == "awaiting_approval"
    assert [record.source for record in state.evidence] == [
        "email",
        "erp",
        "contract",
        "logistics",
    ]
    assert state.missing_evidence == ()
    assert state.anomaly is not None
    assert state.anomaly.code == "missing_tracking_number"
    assert state.anomaly.severity == "high"
    assert state.preview is not None
    assert state.preview.action == "send_supplier_follow_up"
    assert state.preview.target == "orders@northstar.example"
    assert state.preview.subject == "Action required: tracking number for PO-7"
    assert "[logistics:SHIP-77:v1]" in state.preview.body
    assert state.preview.idempotency_key == (
        "delivery-anomaly:PO-7:missing_tracking_number"
    )
    assert len(state.preview.action_hash) == 64
    assert system.mail_gateway.sent_messages == ()


def test_send_is_blocked_until_matching_human_approval() -> None:
    system = build_demo_system()
    prepared = system.agent.prepare("PO-7")
    assert prepared.preview is not None

    without_approval = system.agent.execute()
    wrong_scope = system.agent.execute(
        ApprovalDecision(
            approval_id="APR-41",
            actor="buyer@example.com",
            approved=True,
            action_hash="0" * 64,
        )
    )

    assert without_approval.status == "awaiting_approval"
    assert without_approval.last_error == "human approval is required"
    assert wrong_scope.status == "awaiting_approval"
    assert wrong_scope.last_error == "approval does not match the preview"
    assert system.mail_gateway.sent_messages == ()
    assert not any(event.kind == "message_sent" for event in system.audit_log.events)


def test_repeated_approved_execution_sends_once_and_logs_once() -> None:
    system = build_demo_system()
    prepared = system.agent.prepare("PO-7")
    assert prepared.preview is not None
    approval = ApprovalDecision(
        approval_id="APR-42",
        actor="buyer@example.com",
        approved=True,
        action_hash=prepared.preview.action_hash,
    )

    first = system.agent.execute(approval)
    replay = system.agent.execute(approval)

    assert first.status == "completed"
    assert replay.status == "completed"
    assert first.message_id == replay.message_id == "msg-0bc41bc53261"
    assert len(system.mail_gateway.sent_messages) == 1
    sent = system.mail_gateway.sent_messages[0]
    assert sent.recipient == "orders@northstar.example"
    assert sent.idempotency_key == "delivery-anomaly:PO-7:missing_tracking_number"
    sent_events = [
        event for event in system.audit_log.events if event.kind == "message_sent"
    ]
    assert len(sent_events) == 1
    assert sent_events[0].details == {
        "approval_id": "APR-42",
        "idempotency_key": "delivery-anomaly:PO-7:missing_tracking_number",
        "message_id": "msg-0bc41bc53261",
        "order_id": "PO-7",
    }


def test_missing_required_source_stops_before_draft_or_side_effect() -> None:
    system = build_demo_system(missing_sources={"logistics"})

    prepared = system.agent.prepare("PO-7")
    attempted = system.agent.execute()

    assert prepared.status == "needs_evidence"
    assert prepared.missing_evidence == ("logistics",)
    assert prepared.anomaly is None
    assert prepared.preview is None
    assert attempted.status == "needs_evidence"
    assert attempted.last_error == "required evidence is missing: logistics"
    assert system.mail_gateway.sent_messages == ()
    assert any(
        event.kind == "evidence_incomplete"
        and event.details["missing_sources"] == ("logistics",)
        for event in system.audit_log.events
    )


def test_audit_failure_recovers_without_duplicate_email() -> None:
    system = build_demo_system(fail_audit_once={"message_sent"})
    prepared = system.agent.prepare("PO-7")
    assert prepared.preview is not None
    approval = ApprovalDecision(
        approval_id="APR-42",
        actor="buyer@example.com",
        approved=True,
        action_hash=prepared.preview.action_hash,
    )

    interrupted = system.agent.execute(approval)
    recovered = system.agent.execute(approval)

    assert interrupted.status == "recovery_required"
    assert interrupted.last_error == "audit append failed for message_sent"
    assert recovered.status == "completed"
    assert recovered.message_id == "msg-0bc41bc53261"
    assert len(system.mail_gateway.sent_messages) == 1
    assert len(
        [event for event in system.audit_log.events if event.kind == "message_sent"]
    ) == 1
    assert any(event.kind == "recovered" for event in system.audit_log.events)


def test_completed_task_is_terminal_under_replay_missing_approval_and_denial() -> None:
    system = build_demo_system()
    prepared = system.agent.prepare("PO-7")
    assert prepared.preview is not None
    approval = ApprovalDecision(
        approval_id="APR-42",
        actor="buyer@example.com",
        approved=True,
        action_hash=prepared.preview.action_hash,
    )
    completed = system.agent.execute(approval)
    events_before_replay = system.audit_log.events
    denial = ApprovalDecision(
        approval_id="APR-99",
        actor="buyer@example.com",
        approved=False,
        action_hash=prepared.preview.action_hash,
    )

    without_approval = system.agent.execute()
    after_denial = system.agent.execute(denial)

    assert without_approval == completed
    assert after_denial == completed
    assert system.agent.state == completed
    assert len(system.mail_gateway.sent_messages) == 1
    assert system.audit_log.events == events_before_replay


def test_post_send_recovery_keeps_original_approval_provenance() -> None:
    system = build_demo_system(fail_audit_once={"message_sent"})
    prepared = system.agent.prepare("PO-7")
    assert prepared.preview is not None
    original = ApprovalDecision(
        approval_id="APR-42",
        actor="buyer@example.com",
        approved=True,
        action_hash=prepared.preview.action_hash,
    )
    replacement = ApprovalDecision(
        approval_id="APR-99",
        actor="manager@example.com",
        approved=True,
        action_hash=prepared.preview.action_hash,
    )

    interrupted = system.agent.execute(original)
    recovered = system.agent.execute(replacement)

    assert interrupted.status == "recovery_required"
    assert recovered.status == "completed"
    assert recovered.approval is not None
    assert recovered.approval.approval_id == "APR-42"
    sent_event = next(
        event for event in system.audit_log.events if event.kind == "message_sent"
    )
    assert sent_event.details["approval_id"] == "APR-42"
    assert not any(
        event.details.get("approval_id") == "APR-99"
        for event in system.audit_log.events
    )


def test_reused_approval_id_after_rejection_records_truthful_approval_before_send(
) -> None:
    system = build_demo_system()
    prepared = system.agent.prepare("PO-7")
    assert prepared.preview is not None
    rejected = ApprovalDecision(
        approval_id="APR-REUSED",
        actor="buyer@example.com",
        approved=False,
        action_hash=prepared.preview.action_hash,
    )

    rejected_state = system.agent.execute(rejected)
    prepared_again = system.agent.prepare("PO-7")
    assert prepared_again.preview is not None
    approved = replace(rejected, approved=True)
    completed = system.agent.execute(approved)

    assert rejected_state.status == "rejected"
    assert prepared_again.status == "awaiting_approval"
    assert completed.status == "completed"
    approval_events = [
        event
        for event in system.audit_log.events
        if event.details.get("approval_id") == "APR-REUSED"
    ]
    assert [event.kind for event in approval_events] == [
        "approval_rejected",
        "approval_recorded",
        "message_sent",
    ]
    assert len({event.event_id for event in approval_events}) == 3
    recorded = approval_events[1]
    assert recorded.details == {
        "action_hash": approved.action_hash,
        "actor": "buyer@example.com",
        "approval_id": "APR-REUSED",
        "decided_at": "2026-09-13T08:59:00+08:00",
        "expires_at": "2026-09-13T09:05:00+08:00",
    }
    assert recorded.sequence < approval_events[2].sequence
    assert len(system.mail_gateway.sent_messages) == 1


def test_audit_log_rejects_conflicting_payload_for_an_existing_event_id() -> None:
    audit_log = InMemoryAuditLog()
    first = audit_log.append_once(
        event_id="task-1:approval-recorded:APR-1",
        kind="approval_recorded",
        task_id="task-1",
        details={"approval_id": "APR-1", "actor": "buyer@example.com"},
    )

    replay = audit_log.append_once(
        event_id="task-1:approval-recorded:APR-1",
        kind="approval_recorded",
        task_id="task-1",
        details={"approval_id": "APR-1", "actor": "buyer@example.com"},
    )

    assert replay == first
    with pytest.raises(ValueError, match="audit event ID reused with conflicting payload"):
        audit_log.append_once(
            event_id="task-1:approval-recorded:APR-1",
            kind="approval_rejected",
            task_id="task-1",
            details={"approval_id": "APR-1", "actor": "buyer@example.com"},
        )
    with pytest.raises(ValueError, match="audit event ID reused with conflicting payload"):
        audit_log.append_once(
            event_id="task-1:approval-recorded:APR-1",
            kind="approval_recorded",
            task_id="task-1",
            details={"approval_id": "APR-1", "actor": "manager@example.com"},
        )
    assert audit_log.events == (first,)


@pytest.mark.parametrize("event_index", [0, 1, 2])
def test_preseeded_preparation_audit_conflicts_enter_structured_recovery(
    event_index: int,
) -> None:
    baseline = build_demo_system()
    baseline.agent.prepare("PO-7")
    conflicting_event_id = baseline.audit_log.events[event_index].event_id
    system = build_demo_system()
    system.audit_log.append_once(
        event_id=conflicting_event_id,
        kind="preseeded_conflict",
        task_id="delivery-anomaly:PO-7",
        details={"seeded": True},
    )

    blocked = system.agent.prepare("PO-7")
    replay = system.agent.resume()

    assert blocked.status == "recovery_required"
    assert blocked.recovery_phase == "prepare"
    assert blocked.last_error == (
        "audit event ID reused with conflicting payload: " + conflicting_event_id
    )
    assert replay.status == "recovery_required"
    assert replay.recovery_phase == "prepare"
    assert system.mail_gateway.sent_messages == ()


def test_preseeded_send_audit_conflict_enters_recovery_without_duplicate_email(
) -> None:
    system = build_demo_system()
    prepared = system.agent.prepare("PO-7")
    assert prepared.preview is not None
    approval = ApprovalDecision(
        approval_id="APR-42",
        actor="buyer@example.com",
        approved=True,
        action_hash=prepared.preview.action_hash,
    )
    event_id = f"{prepared.task_id}:message-sent"
    system.audit_log.append_once(
        event_id=event_id,
        kind="preseeded_conflict",
        task_id=prepared.task_id,
        details={"seeded": True},
    )

    blocked = system.agent.execute(approval)
    replay = system.agent.resume()

    assert blocked.status == "recovery_required"
    assert blocked.recovery_phase == "send_audit"
    assert blocked.message_id == "msg-0bc41bc53261"
    assert blocked.last_error == (
        "audit event ID reused with conflicting payload: " + event_id
    )
    assert replay.status == "recovery_required"
    assert replay.recovery_phase == "send_audit"
    assert len(system.mail_gateway.sent_messages) == 1


def test_preseeded_recovery_audit_conflict_enters_completion_recovery_without_resend(
) -> None:
    system = build_demo_system(fail_audit_once={"message_sent"})
    prepared = system.agent.prepare("PO-7")
    assert prepared.preview is not None
    approval = ApprovalDecision(
        approval_id="APR-42",
        actor="buyer@example.com",
        approved=True,
        action_hash=prepared.preview.action_hash,
    )
    interrupted = system.agent.execute(approval)
    assert interrupted.recovery_phase == "send_audit"
    event_id = f"{prepared.task_id}:recovered"
    system.audit_log.append_once(
        event_id=event_id,
        kind="preseeded_conflict",
        task_id=prepared.task_id,
        details={"seeded": True},
    )

    blocked = system.agent.resume()
    replay = system.agent.resume()

    assert blocked.status == "recovery_required"
    assert blocked.recovery_phase == "completion_audit"
    assert blocked.message_id == "msg-0bc41bc53261"
    assert blocked.last_error == (
        "audit event ID reused with conflicting payload: " + event_id
    )
    assert replay.status == "recovery_required"
    assert replay.recovery_phase == "completion_audit"
    assert len(system.mail_gateway.sent_messages) == 1


def test_recovery_audit_transient_failure_recovers_without_duplicate_email() -> None:
    system = build_demo_system(fail_audit_once={"message_sent", "recovered"})
    prepared = system.agent.prepare("PO-7")
    assert prepared.preview is not None
    approval = ApprovalDecision(
        approval_id="APR-42",
        actor="buyer@example.com",
        approved=True,
        action_hash=prepared.preview.action_hash,
    )

    send_gap = system.agent.execute(approval)
    recovery_gap = system.agent.resume()
    completed = system.agent.resume()

    assert send_gap.recovery_phase == "send_audit"
    assert recovery_gap.status == "recovery_required"
    assert recovery_gap.recovery_phase == "completion_audit"
    assert completed.status == "completed"
    assert len(system.mail_gateway.sent_messages) == 1


def test_pre_send_audit_failure_blocks_send_until_gap_is_repaired() -> None:
    system = build_demo_system(fail_audit_once={"approval_recorded"})
    prepared = system.agent.prepare("PO-7")
    assert prepared.preview is not None
    approval = ApprovalDecision(
        approval_id="APR-42",
        actor="buyer@example.com",
        approved=True,
        action_hash=prepared.preview.action_hash,
    )

    blocked = system.agent.execute(approval)

    assert blocked.status == "recovery_required"
    assert blocked.recovery_phase == "approval_audit"
    assert blocked.message_id is None
    assert system.mail_gateway.sent_messages == ()

    recovered = system.agent.resume()

    assert recovered.status == "completed"
    assert len(system.mail_gateway.sent_messages) == 1
    kinds = [event.kind for event in system.audit_log.events]
    assert kinds.index("approval_recorded") < kinds.index("message_sent")


@pytest.mark.parametrize(
    "failed_kind",
    ["evidence_collected", "anomaly_decided", "draft_prepared"],
)
def test_preparation_audit_failure_blocks_until_gap_is_repaired(
    failed_kind: str,
) -> None:
    system = build_demo_system(fail_audit_once={failed_kind})

    blocked = system.agent.prepare("PO-7")

    assert blocked.status == "recovery_required"
    assert blocked.recovery_phase == "prepare"
    assert system.mail_gateway.sent_messages == ()

    resumed = system.agent.resume()

    assert resumed.status == "awaiting_approval"
    assert resumed.preview is not None
    assert any(event.kind == failed_kind for event in system.audit_log.events)
    assert system.mail_gateway.sent_messages == ()


def test_stale_evidence_stops_before_draft() -> None:
    baseline = build_demo_system().agent.prepare("PO-7")
    stale_logistics = replace(
        _evidence_from(baseline, "logistics"),
        observed_at="2026-09-13T08:30:00+08:00",
    )
    system = build_demo_system(evidence_overrides={"logistics": stale_logistics})

    state = system.agent.prepare("PO-7")
    attempted = system.agent.execute()

    assert state.status == "evidence_blocked"
    assert attempted == state
    assert state.preview is None
    assert state.evidence_issues == (
        "logistics evidence is stale (age 1800s; limit 900s)",
    )
    assert system.mail_gateway.sent_messages == ()


@pytest.mark.parametrize(
    ("observed_at", "expected_status"),
    [
        ("2026-09-13T08:45:00+08:00", "awaiting_approval"),
        ("2026-09-13T08:44:59+08:00", "evidence_blocked"),
    ],
)
def test_evidence_freshness_accepts_exact_limit_and_rejects_one_second_over(
    observed_at: str,
    expected_status: str,
) -> None:
    baseline = build_demo_system().agent.prepare("PO-7")
    logistics = _evidence_from(baseline, "logistics")
    boundary_record = agent_module.make_evidence_record(
        source="logistics",
        record_id=logistics.record_id,
        observed_at=observed_at,
        facts=logistics.facts,
    )
    system = build_demo_system(evidence_overrides={"logistics": boundary_record})

    state = system.agent.prepare("PO-7")

    assert state.status == expected_status
    if expected_status == "awaiting_approval":
        assert state.evidence_issues == ()
        assert state.preview is not None
    else:
        assert state.evidence_issues == (
            "logistics evidence is stale (age 901s; limit 900s)",
        )
        assert state.preview is None
    assert system.mail_gateway.sent_messages == ()


@pytest.mark.parametrize(
    ("source", "fact_changes", "expected_issue"),
    [
        (
            "logistics",
            {"status": "not_collected"},
            "email claims shipment but logistics status is not_collected",
        ),
        (
            "erp",
            {"contract_id": "CTR-OTHER"},
            "ERP and contract records disagree on contract_id",
        ),
        (
            "email",
            {"order_id": "PO-8"},
            "email evidence belongs to PO-8, not PO-7",
        ),
        (
            "contract",
            {"supplier_id": "SUP-OTHER"},
            "evidence sources disagree on supplier_id",
        ),
    ],
)
def test_conflicting_evidence_stops_before_draft(
    source: str,
    fact_changes: dict[str, object],
    expected_issue: str,
) -> None:
    baseline = build_demo_system().agent.prepare("PO-7")
    original = _evidence_from(baseline, source)
    conflicting = agent_module.make_evidence_record(
        source=source,
        record_id=original.record_id,
        observed_at=original.observed_at,
        facts={**original.facts, **fact_changes},
    )
    system = build_demo_system(evidence_overrides={source: conflicting})

    state = system.agent.prepare("PO-7")

    assert state.status == "evidence_blocked"
    assert state.preview is None
    assert state.evidence_issues == (expected_issue,)
    assert system.mail_gateway.sent_messages == ()


def test_tampered_evidence_content_stops_before_draft() -> None:
    baseline = build_demo_system().agent.prepare("PO-7")
    logistics = _evidence_from(baseline, "logistics")
    tampered = replace(
        logistics,
        facts={**logistics.facts, "tracking_number": "UNHASHED-CHANGE"},
    )
    system = build_demo_system(evidence_overrides={"logistics": tampered})

    state = system.agent.prepare("PO-7")

    assert state.status == "evidence_blocked"
    assert state.preview is None
    assert state.evidence_issues == ("logistics evidence content hash mismatch",)


def test_missing_source_field_is_blocked_and_audited_before_policy() -> None:
    baseline = build_demo_system().agent.prepare("PO-7")
    logistics = _evidence_from(baseline, "logistics")
    facts = dict(logistics.facts)
    del facts["shipped_at"]
    malformed = _override_facts("logistics", facts)
    system = build_demo_system(evidence_overrides={"logistics": malformed})

    state = system.agent.prepare("PO-7")

    assert state.status == "evidence_blocked"
    assert state.preview is None
    assert state.evidence_issues == (
        "logistics evidence field shipped_at is required",
    )
    blocked_event = next(
        event for event in system.audit_log.events if event.kind == "evidence_blocked"
    )
    assert blocked_event.details["issues"] == state.evidence_issues
    assert system.mail_gateway.sent_messages == ()


@pytest.mark.parametrize(
    ("source", "field", "invalid_value", "expected_issue"),
    [
        (
            "email",
            "shipment_claimed",
            "yes",
            "email evidence field shipment_claimed must be a boolean",
        ),
        (
            "erp",
            "supplier_id",
            ["SUP-21"],
            "erp evidence field supplier_id must be a non-empty string",
        ),
        (
            "logistics",
            "tracking_number",
            77,
            "logistics evidence field tracking_number must be null or a non-empty string",
        ),
    ],
)
def test_wrong_source_field_types_are_blocked_before_policy(
    source: str,
    field: str,
    invalid_value: object,
    expected_issue: str,
) -> None:
    baseline = build_demo_system().agent.prepare("PO-7")
    original = _evidence_from(baseline, source)
    malformed = _override_facts(
        source,
        {**original.facts, field: invalid_value},
    )
    system = build_demo_system(evidence_overrides={source: malformed})

    state = system.agent.prepare("PO-7")

    assert state.status == "evidence_blocked"
    assert state.preview is None
    assert state.evidence_issues == (expected_issue,)
    assert system.mail_gateway.sent_messages == ()


def test_malformed_source_timestamp_is_blocked_before_policy() -> None:
    baseline = build_demo_system().agent.prepare("PO-7")
    logistics = _evidence_from(baseline, "logistics")
    malformed = _override_facts(
        "logistics",
        {**logistics.facts, "shipped_at": "13 September tomorrow"},
    )
    system = build_demo_system(evidence_overrides={"logistics": malformed})

    state = system.agent.prepare("PO-7")

    assert state.status == "evidence_blocked"
    assert state.preview is None
    assert state.evidence_issues == (
        "logistics evidence field shipped_at must be an ISO 8601 timestamp with timezone",
    )
    assert system.mail_gateway.sent_messages == ()


@pytest.mark.parametrize("invalid_hours", [0, -1, True, "24"])
def test_invalid_contract_hours_are_blocked_before_policy(
    invalid_hours: object,
) -> None:
    baseline = build_demo_system().agent.prepare("PO-7")
    contract = _evidence_from(baseline, "contract")
    malformed = _override_facts(
        "contract",
        {
            **contract.facts,
            "tracking_required_within_hours": invalid_hours,
        },
    )
    system = build_demo_system(evidence_overrides={"contract": malformed})

    state = system.agent.prepare("PO-7")

    assert state.status == "evidence_blocked"
    assert state.preview is None
    assert state.evidence_issues == (
        "contract evidence field tracking_required_within_hours "
        "must be a positive integer",
    )
    assert system.mail_gateway.sent_messages == ()


def test_expired_approval_cannot_send() -> None:
    system = build_demo_system()
    prepared = system.agent.prepare("PO-7")
    assert prepared.preview is not None
    expired = ApprovalDecision(
        approval_id="APR-OLD",
        actor="buyer@example.com",
        approved=True,
        action_hash=prepared.preview.action_hash,
        decided_at="2026-09-13T08:00:00+08:00",
        expires_at="2026-09-13T08:30:00+08:00",
    )

    state = system.agent.execute(expired)

    assert state.status == "awaiting_approval"
    assert state.last_error == "approval has expired"
    assert system.mail_gateway.sent_messages == ()
    assert not any(event.kind == "approval_recorded" for event in system.audit_log.events)


@pytest.mark.parametrize(
    ("field", "changed_value"),
    [
        ("target", "attacker@example.net"),
        ("subject", "Changed subject"),
        ("body", "Changed body"),
    ],
)
def test_idempotency_key_rejects_changed_payload(
    field: str,
    changed_value: str,
) -> None:
    system = build_demo_system()
    prepared = system.agent.prepare("PO-7")
    assert prepared.preview is not None
    approval = ApprovalDecision(
        approval_id="APR-42",
        actor="buyer@example.com",
        approved=True,
        action_hash=prepared.preview.action_hash,
    )
    system.agent.execute(approval)
    changed = replace(prepared.preview, **{field: changed_value})

    with pytest.raises(
        ValueError,
        match="idempotency key reused with a different request payload",
    ):
        system.mail_gateway.send_once(changed)

    assert len(system.mail_gateway.sent_messages) == 1
    assert system.mail_gateway.sent_messages[0].recipient == (
        "orders@northstar.example"
    )


def test_missing_evidence_can_be_supplied_and_resume_same_task() -> None:
    complete = build_demo_system().agent.prepare("PO-7")
    fresh_logistics = _evidence_from(complete, "logistics")
    system = build_demo_system(missing_sources={"logistics"})
    missing = system.agent.prepare("PO-7")

    attempted = system.agent.execute()

    assert attempted.last_error == "required evidence is missing: logistics"
    assert system.agent.state is not None
    assert system.agent.state.last_error == attempted.last_error

    resumed = system.agent.supply_evidence(fresh_logistics)

    assert resumed.task_id == missing.task_id
    assert resumed.status == "awaiting_approval"
    assert resumed.missing_evidence == ()
    assert resumed.preview is not None
    assert len(
        [event for event in system.audit_log.events if event.kind == "evidence_collected"]
    ) == 2
    assert system.mail_gateway.sent_messages == ()
