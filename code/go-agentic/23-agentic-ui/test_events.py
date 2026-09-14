import pytest

from events import UIState, reduce_event


def apply(state, *events):
    for event in events:
        state = reduce_event(state, event)
    return state


def test_event_stream_builds_plan_progress_tools_and_evidence():
    state = apply(
        UIState(),
        {"type": "plan", "steps": ["search", "verify"]},
        {"type": "progress", "completed": 1, "total": 2},
        {"type": "tool_call", "id": "t1", "name": "search", "status": "running"},
        {"type": "tool_result", "id": "t1", "status": "succeeded"},
        {"type": "evidence", "source": "contract.pdf", "claim": "delivery date"},
    )
    assert state.plan == ["search", "verify"]
    assert state.progress == pytest.approx(0.5)
    assert state.tool_calls["t1"]["status"] == "succeeded"
    assert state.evidence[0]["source"] == "contract.pdf"


def test_approval_error_retry_cancel_and_complete_are_explicit_states():
    waiting = reduce_event(UIState(), {"type": "approval_requested", "id": "a1", "summary": "send"})
    approved = reduce_event(waiting, {"type": "approval_resolved", "id": "a1", "decision": "approved"})
    failed = reduce_event(approved, {"type": "error", "message": "timeout"})
    retried = reduce_event(failed, {"type": "retry"})
    cancelled = reduce_event(retried, {"type": "cancelled"})
    completed = reduce_event(UIState(), {"type": "completed", "artifact": "report.md"})
    assert waiting.status == "waiting_for_approval"
    assert approved.approval["decision"] == "approved"
    assert failed.status == "failed" and failed.error == "timeout"
    assert retried.status == "running" and retried.error is None
    assert cancelled.status == "cancelled"
    assert completed.status == "completed" and completed.artifact == "report.md"


def test_unknown_ui_event_is_rejected():
    with pytest.raises(ValueError, match="unknown event"):
        reduce_event(UIState(), {"type": "magic"})
