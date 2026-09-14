from __future__ import annotations

import pytest

from memory import (
    ExternalState,
    MemoryCandidate,
    MemoryStore,
    StateConflict,
)


def test_retrieval_excludes_expired_and_irrelevant_records_and_keeps_provenance() -> None:
    store = MemoryStore()
    for candidate in (
        MemoryCandidate(
            memory_id="login-fresh",
            kind="episodic",
            content="The login fix strips whitespace from usernames.",
            source="test-run:login-42",
            created_at=90,
            importance=3,
            expires_at=160,
            privacy="internal",
        ),
        MemoryCandidate(
            memory_id="login-stale",
            kind="episodic",
            content="An old login workaround skipped username normalization.",
            source="incident:old-login",
            created_at=10,
            importance=5,
            expires_at=80,
            privacy="internal",
        ),
        MemoryCandidate(
            memory_id="supplier-irrelevant",
            kind="semantic",
            content="ABB purchase order PO-7 is delayed by three days.",
            source="erp:PO-7",
            created_at=99,
            importance=5,
            privacy="internal",
        ),
    ):
        assert store.write(candidate).accepted is True

    hits = store.retrieve(
        query="login username normalization",
        now=100,
        limit=3,
        allowed_privacy={"internal"},
    )

    assert [hit.record.memory_id for hit in hits] == ["login-fresh"]
    assert hits[0].record.source == "test-run:login-42"
    assert hits[0].matched_terms == ("login", "username")


def test_write_policy_rejects_secrets_and_unprovenanced_candidates() -> None:
    store = MemoryStore()

    secret = store.write(
        MemoryCandidate(
            memory_id="credential",
            kind="semantic",
            content="The production password is swordfish.",
            source="user-message:8",
            created_at=10,
            importance=5,
            privacy="secret",
        )
    )
    unprovenanced = store.write(
        MemoryCandidate(
            memory_id="guess",
            kind="semantic",
            content="The supplier probably prefers email.",
            source=" ",
            created_at=10,
            importance=2,
            privacy="internal",
        )
    )

    assert (secret.accepted, secret.reason) == (False, "secret content is not stored")
    assert (unprovenanced.accepted, unprovenanced.reason) == (
        False,
        "source provenance is required",
    )
    assert store.records == ()


def test_consolidation_creates_semantic_memory_with_source_ids() -> None:
    store = MemoryStore()
    for candidate in (
        MemoryCandidate(
            memory_id="po-7-email-1",
            kind="episodic",
            content="ABB moved PO-7 delivery from September 8 to September 11.",
            source="email:1001",
            created_at=10,
            importance=4,
            privacy="internal",
        ),
        MemoryCandidate(
            memory_id="po-7-email-2",
            kind="episodic",
            content="ABB confirmed that raw material shortage caused the PO-7 delay.",
            source="email:1008",
            created_at=12,
            importance=4,
            privacy="internal",
        ),
    ):
        assert store.write(candidate).accepted is True

    consolidated = store.consolidate(
        memory_id="po-7-status",
        source_ids=("po-7-email-1", "po-7-email-2"),
        content="ABB PO-7 is due September 11 after a raw material delay.",
        created_at=13,
        importance=5,
    )

    assert consolidated.kind == "semantic"
    assert consolidated.source == "consolidated:po-7-email-1,po-7-email-2"
    assert consolidated.source_ids == ("po-7-email-1", "po-7-email-2")
    assert [record.memory_id for record in store.records] == [
        "po-7-email-1",
        "po-7-email-2",
        "po-7-status",
    ]


def test_forgetting_removes_expired_then_low_value_records() -> None:
    store = MemoryStore()
    for candidate in (
        MemoryCandidate("expired", "working", "temporary login trace", "trace:1", 1, 1, 5),
        MemoryCandidate("low", "episodic", "minor login observation", "trace:2", 20, 1),
        MemoryCandidate("medium", "semantic", "login normalization rule", "test:2", 30, 3),
        MemoryCandidate("high", "procedural", "run login tests before completion", "policy:1", 10, 5),
    ):
        assert store.write(candidate).accepted is True

    removed = store.forget(now=50, max_records=2)

    assert removed == ("expired", "low")
    assert [record.memory_id for record in store.records] == ["medium", "high"]


def test_forgetting_consolidated_sources_keeps_resolvable_provenance_tombstones() -> None:
    store = MemoryStore()
    for candidate in (
        MemoryCandidate(
            "po-7-email-1",
            "episodic",
            "ABB moved PO-7 delivery.",
            "email:1001",
            10,
            1,
        ),
        MemoryCandidate(
            "po-7-email-2",
            "episodic",
            "Raw material shortage caused the delay.",
            "email:1008",
            12,
            1,
        ),
    ):
        assert store.write(candidate).accepted is True
    semantic = store.consolidate(
        memory_id="po-7-status",
        source_ids=("po-7-email-1", "po-7-email-2"),
        content="ABB PO-7 was delayed by a raw material shortage.",
        created_at=13,
        importance=5,
    )

    removed = store.forget(now=50, max_records=1)
    reused_id = store.write(
        MemoryCandidate(
            "po-7-email-1",
            "episodic",
            "An unrelated event tried to reuse a forgotten ID.",
            "email:9999",
            20,
            5,
        )
    )
    provenance = store.resolve_provenance(semantic.memory_id)

    assert removed == ("po-7-email-1", "po-7-email-2")
    assert (reused_id.accepted, reused_id.reason) == (
        False,
        "memory id already exists",
    )
    assert [record.memory_id for record in store.records] == ["po-7-status"]
    assert semantic.source_ids == ("po-7-email-1", "po-7-email-2")
    assert [
        (item.memory_id, item.source, item.created_at, item.content_hash)
        for item in provenance
    ] == [
        (
            "po-7-email-1",
            "email:1001",
            10,
            "b122114e67788857aa277ff52b02472e106667e662832737039e078613eac9a6",
        ),
        (
            "po-7-email-2",
            "email:1008",
            12,
            "bca2b84f3b9221feb4b5778a03200997d7c4a897a89790767f8f5966a0024426",
        ),
    ]


def test_external_state_is_versioned_and_never_appears_in_memory_retrieval() -> None:
    store = MemoryStore()
    state = ExternalState()

    current = state.write(
        key="purchase-order:PO-7",
        value="delayed until September 11",
        expected_revision=0,
    )

    assert current.revision == 1
    assert state.read("purchase-order:PO-7") == current
    assert store.retrieve("PO-7", now=20, limit=3, allowed_privacy={"internal"}) == ()
    with pytest.raises(StateConflict, match="expected revision 0, found 1"):
        state.write(
            key="purchase-order:PO-7",
            value="shipped",
            expected_revision=0,
        )
