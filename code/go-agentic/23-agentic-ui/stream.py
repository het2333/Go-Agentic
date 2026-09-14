"""Replayable event-stream contract for Chapter 23."""

from copy import deepcopy
from typing import Any


TERMINAL_TYPES = {"completed", "failed", "cancelled"}
APPROVAL_FIELDS = {"action", "target", "preview", "reversible"}


class StreamLog:
    """Keep a contiguous, idempotent event log suitable for UI replay."""

    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []
        self._event_ids: set[str] = set()
        self._terminal = False

    @property
    def cursor(self) -> int:
        """Return the sequence number of the newest accepted event."""
        return len(self._events)

    def append(self, event: dict[str, Any]) -> bool:
        """Validate and append an event; return False for retransmissions."""
        event_id = event.get("id")
        if not isinstance(event_id, str) or not event_id:
            raise ValueError("event id must be a non-empty string")
        if event_id in self._event_ids:
            return False
        if self._terminal:
            raise ValueError("no event may follow a terminal state")

        expected_sequence = self.cursor + 1
        if event.get("sequence") != expected_sequence:
            raise ValueError(f"sequence must be {expected_sequence}")

        event_type = event.get("type")
        if not isinstance(event_type, str) or not event_type:
            raise ValueError("event type must be a non-empty string")
        if event_type == "approval_requested":
            missing = APPROVAL_FIELDS.difference(event)
            if missing or not isinstance(event["reversible"], bool):
                raise ValueError("approval event lacks a reviewable contract")

        self._events.append(deepcopy(event))
        self._event_ids.add(event_id)
        self._terminal = event_type in TERMINAL_TYPES
        return True

    def replay_after(self, cursor: int) -> list[dict[str, Any]]:
        """Return defensive copies of events newer than an acknowledged cursor."""
        if not isinstance(cursor, int) or cursor < 0 or cursor > self.cursor:
            raise ValueError("cursor is outside the retained event range")
        return deepcopy(self._events[cursor:])
