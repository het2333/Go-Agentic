import pytest

from stream import StreamLog


def event(sequence, event_id, event_type="progress", **extra):
    return {"sequence": sequence, "id": event_id, "type": event_type, **extra}


def test_stream_requires_contiguous_sequence_numbers():
    stream = StreamLog()
    stream.append(event(1, "e1"))
    with pytest.raises(ValueError, match="sequence"):
        stream.append(event(3, "e3"))


def test_replay_cursor_returns_only_newer_events():
    stream = StreamLog()
    stream.append(event(1, "e1"))
    stream.append(event(2, "e2"))
    stream.append(event(3, "e3"))
    assert [item["id"] for item in stream.replay_after(1)] == ["e2", "e3"]
    assert stream.cursor == 3


def test_retransmitted_event_id_is_suppressed():
    stream = StreamLog()
    assert stream.append(event(1, "e1")) is True
    assert stream.append(event(1, "e1")) is False
    assert len(stream.replay_after(0)) == 1


def test_no_event_can_follow_a_terminal_state():
    stream = StreamLog()
    stream.append(event(1, "done", "completed", artifact="report.md"))
    with pytest.raises(ValueError, match="terminal"):
        stream.append(event(2, "late"))


def test_approval_event_requires_a_reviewable_contract():
    stream = StreamLog()
    with pytest.raises(ValueError, match="approval"):
        stream.append(event(1, "a1", "approval_requested", action="send"))

    assert stream.append(
        event(
            1,
            "a1",
            "approval_requested",
            action="send email",
            target="supplier@example.com",
            preview="Please confirm the shipment date.",
            reversible=False,
        )
    )


@pytest.mark.parametrize("cursor", [-1, 2])
def test_replay_rejects_invalid_cursors(cursor):
    stream = StreamLog()
    stream.append(event(1, "e1"))
    with pytest.raises(ValueError, match="cursor"):
        stream.replay_after(cursor)
