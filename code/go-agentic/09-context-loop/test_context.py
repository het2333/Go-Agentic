from __future__ import annotations

import context as context_module
import json

import pytest

from context import (
    CompactionRecord,
    ContextBudget,
    Evidence,
    LoopLimits,
    LoopUsage,
    TaskState,
    compact,
    select_context,
    termination_reason,
)


def _state_requiring(*evidence_refs: str) -> TaskState:
    return TaskState(
        goal="Resume a login repair safely.",
        authority=("workspace:read", "tests:run"),
        completion_rule="The focused test passes against the current file.",
        completed=("inspect failure",),
        decisions=(),
        blockers=("test remains unverified",),
        next_actions=("rerun focused test",),
        evidence_refs=evidence_refs,
        usage=LoopUsage(steps=1, input_tokens=40, output_tokens=10, cost_units=2),
        limits=LoopLimits(max_steps=4, max_total_tokens=300, max_cost_units=10),
    )


def test_selection_rejects_stale_and_irrelevant_evidence() -> None:
    budget = ContextBudget(
        window_tokens=100,
        instruction_tokens=20,
        tool_schema_tokens=10,
        output_reserve_tokens=30,
    )
    evidence = (
        Evidence(
            evidence_id="fresh-login",
            summary="login username normalization failure",
            detail="The focused test expects whitespace to be stripped.",
            token_cost=18,
            observed_at=95,
            valid_until=150,
            source="test:login-42",
        ),
        Evidence(
            evidence_id="stale-login",
            summary="old login workaround",
            detail="A workaround bypassed normalization last year.",
            token_cost=12,
            observed_at=10,
            valid_until=80,
            source="incident:old",
        ),
        Evidence(
            evidence_id="fresh-supplier",
            summary="supplier delivery update",
            detail="PO-7 is due September 11.",
            token_cost=10,
            observed_at=99,
            valid_until=150,
            source="erp:PO-7",
        ),
    )

    selection = select_context(
        query="login username",
        candidates=evidence,
        now=100,
        budget=budget,
    )

    assert [item.evidence_id for item in selection.included] == ["fresh-login"]
    assert selection.used_tokens == 18
    assert selection.remaining_tokens == 22
    assert selection.rejected == (
        ("fresh-supplier", "irrelevant"),
        ("stale-login", "stale"),
    )


def test_selection_uses_progressive_summaries_with_stable_budget_accounting() -> None:
    budget = ContextBudget(90, 20, 10, 20)
    evidence = (
        Evidence("broad", "login module overview", "Long details", 35, 90, 150, "tree:1"),
        Evidence("test", "login focused test failure", "Assertion details", 20, 95, 150, "test:1"),
        Evidence("code", "login username strip implementation", "Function body", 20, 96, 150, "file:1"),
    )

    selection = select_context("login username test", evidence, now=100, budget=budget)

    assert [item.evidence_id for item in selection.included] == ["test", "code"]
    assert selection.used_tokens == budget.evidence_tokens == 40
    assert selection.remaining_tokens == 0
    assert selection.references == ("test:1", "file:1")
    assert selection.rejected == (("broad", "over_budget"),)


def test_evidence_rejects_negative_token_cost_without_expanding_budget() -> None:
    with pytest.raises(ValueError, match="token_cost must be non-negative"):
        Evidence(
            "negative",
            "login test",
            "invalid accounting input",
            -1,
            90,
            150,
            "test:negative",
        )

    budget = ContextBudget(60, 10, 10, 20)
    selection = select_context(
        "login",
        (Evidence("valid", "login test", "failure", 12, 90, 150, "test:valid"),),
        now=100,
        budget=budget,
    )

    assert 0 <= selection.used_tokens <= budget.evidence_tokens
    assert selection.remaining_tokens == budget.evidence_tokens - selection.used_tokens


def test_compaction_round_trip_restores_authority_completion_and_budget_state() -> None:
    limits = LoopLimits(max_steps=5, max_total_tokens=500, max_cost_units=20)
    usage = LoopUsage(steps=2, input_tokens=120, output_tokens=30, cost_units=6)
    state = TaskState(
        goal="Fix login normalization and verify it.",
        authority=("workspace:read", "workspace:edit", "tests:run"),
        completion_rule="The focused login test passes against the current file.",
        completed=("read failing test", "inspect src/auth/login.py"),
        decisions=("strip surrounding username whitespace",),
        blockers=("focused test still failing",),
        next_actions=("edit login.py", "rerun focused test"),
        evidence_refs=("test:login-42", "file:src/auth/login.py"),
        usage=usage,
        limits=limits,
    )
    events = (
        Evidence("e1", "test failed", "full output", 30, 90, 150, "test:login-42"),
        Evidence("e2", "file inspected", "full source", 40, 95, 150, "file:src/auth/login.py"),
    )

    record = compact(events=events, state=state, summary_token_limit=40)
    serialized = record.to_json()
    copied_record = CompactionRecord.from_json(serialized)
    restored = context_module.restore_compaction(
        copied_record,
        current_evidence=events,
        now=100,
    )

    assert copied_record.resume_state is not state
    assert restored.ready is True
    assert restored.state is not None
    assert restored.state.authority == (
        "workspace:read",
        "workspace:edit",
        "tests:run",
    )
    assert restored.state.completion_rule == (
        "The focused login test passes against the current file."
    )
    assert restored.state.usage == usage
    assert restored.state.limits == limits
    assert restored.remaining_budget.remaining_steps == 3
    assert restored.remaining_budget.remaining_tokens == 350
    assert restored.remaining_budget.remaining_cost_units == 14
    assert restored.evidence_status == (("e1", "current"), ("e2", "current"))
    assert copied_record.source_event_ids == ("e1", "e2")
    assert copied_record.original_tokens == 70
    assert copied_record.compacted_tokens <= 40
    assert "Goal: Fix login normalization and verify it." in copied_record.summary
    assert "Next: edit login.py; rerun focused test" in copied_record.summary


def test_compaction_rejects_required_evidence_without_snapshot() -> None:
    state = _state_requiring("test:required")

    with pytest.raises(
        ValueError,
        match="required evidence has no snapshot: test:required",
    ):
        compact(events=(), state=state, summary_token_limit=20)


def test_compaction_rejects_partial_required_evidence_coverage() -> None:
    state = _state_requiring("test:required", "file:required")
    events = (
        Evidence(
            "e1",
            "focused login test",
            "failure",
            10,
            90,
            150,
            "test:required",
        ),
    )

    with pytest.raises(
        ValueError,
        match="required evidence has no snapshot: file:required",
    ):
        compact(events=events, state=state, summary_token_limit=20)


def test_restore_marks_uncovered_required_evidence_missing() -> None:
    state = _state_requiring("test:required", "file:required")
    events = (
        Evidence("e1", "focused login test", "failure", 10, 90, 150, "test:required"),
        Evidence("e2", "login source", "return username", 12, 95, 150, "file:required"),
    )
    payload = json.loads(compact(events, state, summary_token_limit=20).to_json())
    payload["source_event_ids"] = payload["source_event_ids"][:1]
    payload["evidence_snapshots"] = payload["evidence_snapshots"][:1]
    incomplete_record = CompactionRecord.from_json(json.dumps(payload))

    restored = context_module.restore_compaction(
        incomplete_record,
        current_evidence=(events[0],),
        now=100,
    )

    assert restored.ready is False
    assert restored.state is None
    assert restored.evidence_status == (
        ("e1", "current"),
        ("file:required", "missing"),
    )


def test_compaction_and_restore_accept_complete_required_evidence_coverage() -> None:
    state = _state_requiring("test:required", "file:required")
    events = (
        Evidence("e1", "focused login test", "failure", 10, 90, 150, "test:required"),
        Evidence("e2", "login source", "return username", 12, 95, 150, "file:required"),
    )
    copied_record = CompactionRecord.from_json(
        compact(events, state, summary_token_limit=20).to_json()
    )

    restored = context_module.restore_compaction(
        copied_record,
        current_evidence=events,
        now=100,
    )

    assert restored.ready is True
    assert restored.state is not None
    assert restored.state.evidence_refs == ("test:required", "file:required")
    assert restored.evidence_status == (("e1", "current"), ("e2", "current"))


def test_restore_flags_changed_and_stale_evidence_before_resume() -> None:
    state = TaskState(
        goal="Resume a login repair.",
        authority=("workspace:read", "tests:run"),
        completion_rule="The focused test passes.",
        completed=("inspect failure",),
        decisions=(),
        blockers=("test remains unverified",),
        next_actions=("rerun focused test",),
        evidence_refs=("test:login-42", "file:src/auth/login.py"),
        usage=LoopUsage(steps=1, input_tokens=40, output_tokens=10, cost_units=2),
        limits=LoopLimits(max_steps=4, max_total_tokens=300, max_cost_units=10),
    )
    original = (
        Evidence("e1", "login failure", "expected alice", 20, 90, 150, "test:login-42"),
        Evidence("e2", "login source", "return username", 20, 90, 120, "file:src/auth/login.py"),
    )
    copied_record = CompactionRecord.from_json(
        compact(original, state, summary_token_limit=30).to_json()
    )
    current = (
        Evidence("e1", "login failure", "expected bob", 20, 90, 150, "test:login-42"),
        Evidence("e2", "login source", "return username", 20, 90, 99, "file:src/auth/login.py"),
    )

    restored = context_module.restore_compaction(
        copied_record,
        current_evidence=current,
        now=100,
    )

    assert restored.ready is False
    assert restored.state is None
    assert restored.evidence_status == (("e1", "changed"), ("e2", "stale"))
    assert restored.remaining_budget.remaining_steps == 3
    assert restored.remaining_budget.remaining_tokens == 250
    assert restored.remaining_budget.remaining_cost_units == 8


def test_compaction_round_trip_rejects_negative_persisted_usage() -> None:
    state = TaskState(
        goal="Resume safely.",
        authority=("workspace:read",),
        completion_rule="Current evidence validates completion.",
        completed=(),
        decisions=(),
        blockers=(),
        next_actions=("inspect current evidence",),
        evidence_refs=("test:1",),
        usage=LoopUsage(),
        limits=LoopLimits(max_steps=2, max_total_tokens=100, max_cost_units=5),
    )
    record = compact(
        (Evidence("e1", "login test", "passing", 10, 90, 150, "test:1"),),
        state,
        summary_token_limit=20,
    )
    payload = json.loads(record.to_json())
    payload["resume_state"]["usage"]["input_tokens"] = -1
    payload["remaining_budget"]["remaining_tokens"] = 101

    with pytest.raises(ValueError, match="loop usage must be non-negative"):
        CompactionRecord.from_json(json.dumps(payload))


def test_compaction_round_trip_rejects_tampered_remaining_budget() -> None:
    state = TaskState(
        goal="Resume within the original budget.",
        authority=("workspace:read",),
        completion_rule="Current evidence validates completion.",
        completed=(),
        decisions=(),
        blockers=(),
        next_actions=("inspect current evidence",),
        evidence_refs=("test:1",),
        usage=LoopUsage(steps=1, input_tokens=30, output_tokens=20, cost_units=2),
        limits=LoopLimits(max_steps=3, max_total_tokens=200, max_cost_units=8),
    )
    record = compact(
        (Evidence("e1", "login test", "passing", 10, 90, 150, "test:1"),),
        state,
        summary_token_limit=20,
    )
    payload = json.loads(record.to_json())
    payload["remaining_budget"]["remaining_steps"] = 3

    with pytest.raises(
        ValueError,
        match="persisted remaining budget does not match usage and limits",
    ):
        CompactionRecord.from_json(json.dumps(payload))


def test_restore_withholds_state_when_persisted_usage_exhausts_budget() -> None:
    state = TaskState(
        goal="Stop an exhausted repair loop.",
        authority=("workspace:read",),
        completion_rule="Current evidence validates completion.",
        completed=(),
        decisions=(),
        blockers=("step budget exhausted",),
        next_actions=(),
        evidence_refs=("test:1",),
        usage=LoopUsage(steps=2, input_tokens=30, output_tokens=20, cost_units=2),
        limits=LoopLimits(max_steps=2, max_total_tokens=200, max_cost_units=8),
    )
    evidence = (
        Evidence("e1", "login test", "still failing", 10, 90, 150, "test:1"),
    )
    copied_record = CompactionRecord.from_json(
        compact(evidence, state, summary_token_limit=20).to_json()
    )

    restored = context_module.restore_compaction(
        copied_record,
        current_evidence=evidence,
        now=100,
    )

    assert restored.ready is False
    assert restored.state is None
    assert restored.remaining_budget.remaining_steps == 0
    assert restored.evidence_status == (("e1", "current"),)
    assert restored.budget_status == "step_budget"


def test_loop_termination_uses_validation_and_economic_limits() -> None:
    limits = LoopLimits(max_steps=3, max_total_tokens=200, max_cost_units=10)
    usage = LoopUsage().record(input_tokens=80, output_tokens=20, cost_units=4)

    assert termination_reason(verified=False, usage=usage, limits=limits) is None
    assert termination_reason(verified=True, usage=usage, limits=limits) == "verified"

    exhausted = usage.record(input_tokens=70, output_tokens=40, cost_units=7)
    assert exhausted.steps == 2
    assert exhausted.total_tokens == 210
    assert exhausted.cost_units == 11
    assert termination_reason(False, exhausted, limits) == "token_budget"

    cost_only = LoopUsage().record(input_tokens=10, output_tokens=5, cost_units=10)
    assert termination_reason(False, cost_only, limits) == "cost_budget"


def test_step_limit_stops_an_unverified_loop_at_the_boundary() -> None:
    limits = LoopLimits(max_steps=2, max_total_tokens=1_000, max_cost_units=100)
    usage = LoopUsage().record(10, 5, 1).record(10, 5, 1)

    assert termination_reason(False, usage, limits) == "step_budget"
