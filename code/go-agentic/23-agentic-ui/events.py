"""A tiny event reducer for observable agent interfaces."""

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class UIState:
    status: str = "idle"
    plan: list[str] = field(default_factory=list)
    progress: float = 0.0
    tool_calls: dict[str, dict[str, Any]] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    approval: dict[str, Any] | None = None
    error: str | None = None
    artifact: str | None = None
    history: list[dict[str, Any]] = field(default_factory=list)


def reduce_event(state: UIState, event: dict[str, Any]) -> UIState:
    """Return a new UI state after applying one validated agent event."""
    next_state = deepcopy(state)
    event_type = event.get("type")

    if event_type == "plan":
        next_state.plan = list(event["steps"])
        next_state.status = "running"
    elif event_type == "progress":
        completed, total = event["completed"], event["total"]
        if total <= 0 or completed < 0 or completed > total:
            raise ValueError("invalid progress")
        next_state.progress = completed / total
        next_state.status = "running"
    elif event_type == "tool_call":
        next_state.tool_calls[event["id"]] = {
            "name": event["name"],
            "status": event.get("status", "running"),
        }
        next_state.status = "running"
    elif event_type == "tool_result":
        call = next_state.tool_calls.setdefault(event["id"], {"name": "unknown"})
        call["status"] = event["status"]
    elif event_type == "evidence":
        next_state.evidence.append({key: value for key, value in event.items() if key != "type"})
    elif event_type == "approval_requested":
        next_state.approval = {key: value for key, value in event.items() if key != "type"}
        next_state.status = "waiting_for_approval"
    elif event_type == "approval_resolved":
        next_state.approval = {key: value for key, value in event.items() if key != "type"}
        next_state.status = "running"
    elif event_type == "error":
        next_state.error = event["message"]
        next_state.status = "failed"
    elif event_type == "retry":
        next_state.error = None
        next_state.status = "running"
    elif event_type == "cancelled":
        next_state.status = "cancelled"
    elif event_type == "completed":
        next_state.artifact = event["artifact"]
        next_state.progress = 1.0
        next_state.status = "completed"
    else:
        raise ValueError(f"unknown event type: {event_type}")

    next_state.history.append(deepcopy(event))
    return next_state
