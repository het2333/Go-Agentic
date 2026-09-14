from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import AbstractSet, Literal, TypeAlias


MemoryKind: TypeAlias = Literal["working", "episodic", "semantic", "procedural"]
Privacy: TypeAlias = Literal["public", "internal", "secret"]


@dataclass(frozen=True)
class MemoryCandidate:
    memory_id: str
    kind: MemoryKind
    content: str
    source: str
    created_at: int
    importance: int
    expires_at: int | None = None
    privacy: Privacy = "internal"
    source_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class WriteResult:
    accepted: bool
    reason: str


@dataclass(frozen=True)
class MemoryHit:
    record: MemoryCandidate
    matched_terms: tuple[str, ...]
    score: int


@dataclass(frozen=True)
class ProvenanceSnapshot:
    memory_id: str
    kind: MemoryKind
    source: str
    created_at: int
    content_hash: str


def _terms(text: str) -> set[str]:
    terms: set[str] = set()
    for raw in re.findall(r"[a-z0-9]+", text.lower()):
        terms.add(raw[:-1] if len(raw) > 3 and raw.endswith("s") else raw)
    return terms


class MemoryStore:
    def __init__(self) -> None:
        self._records: list[MemoryCandidate] = []
        self._provenance: dict[str, ProvenanceSnapshot] = {}

    @property
    def records(self) -> tuple[MemoryCandidate, ...]:
        return tuple(self._records)

    def write(self, candidate: MemoryCandidate) -> WriteResult:
        if candidate.privacy == "secret":
            return WriteResult(False, "secret content is not stored")
        if not candidate.source.strip():
            return WriteResult(False, "source provenance is required")
        if not candidate.memory_id.strip() or not candidate.content.strip():
            return WriteResult(False, "memory id and content are required")
        if not 1 <= candidate.importance <= 5:
            return WriteResult(False, "importance must be from 1 to 5")
        if candidate.memory_id in self._provenance:
            return WriteResult(False, "memory id already exists")

        self._records.append(candidate)
        self._provenance[candidate.memory_id] = ProvenanceSnapshot(
            memory_id=candidate.memory_id,
            kind=candidate.kind,
            source=candidate.source,
            created_at=candidate.created_at,
            content_hash=hashlib.sha256(candidate.content.encode("utf-8")).hexdigest(),
        )
        return WriteResult(True, "stored")

    def retrieve(
        self,
        query: str,
        now: int,
        limit: int,
        allowed_privacy: AbstractSet[Privacy],
    ) -> tuple[MemoryHit, ...]:
        if not query.strip():
            raise ValueError("query must be non-empty")
        if limit < 1:
            raise ValueError("limit must be at least 1")

        query_terms = _terms(query)
        hits: list[MemoryHit] = []
        for record in self._records:
            if record.privacy not in allowed_privacy:
                continue
            if record.expires_at is not None and record.expires_at <= now:
                continue
            matched = tuple(sorted(query_terms & _terms(record.content)))
            if not matched:
                continue
            age = max(0, now - record.created_at)
            score = len(matched) * 100 + record.importance * 10 - age
            hits.append(MemoryHit(record, matched, score))

        hits.sort(key=lambda hit: (-hit.score, hit.record.memory_id))
        return tuple(hits[:limit])

    def consolidate(
        self,
        memory_id: str,
        source_ids: tuple[str, ...],
        content: str,
        created_at: int,
        importance: int,
    ) -> MemoryCandidate:
        if len(set(source_ids)) < 2:
            raise ValueError("consolidation requires at least two source memories")

        indexed = {record.memory_id: record for record in self._records}
        try:
            sources = tuple(indexed[source_id] for source_id in source_ids)
        except KeyError as error:
            raise ValueError(f"unknown source memory: {error.args[0]}") from error
        if any(source.kind != "episodic" for source in sources):
            raise ValueError("consolidation sources must be episodic memories")

        consolidated = MemoryCandidate(
            memory_id=memory_id,
            kind="semantic",
            content=content,
            source=f"consolidated:{','.join(source_ids)}",
            created_at=created_at,
            importance=importance,
            privacy="internal",
            source_ids=source_ids,
        )
        result = self.write(consolidated)
        if not result.accepted:
            raise ValueError(result.reason)
        return consolidated

    def resolve_provenance(
        self, memory_id: str
    ) -> tuple[ProvenanceSnapshot, ...]:
        record = next(
            (record for record in self._records if record.memory_id == memory_id),
            None,
        )
        if record is None:
            raise KeyError(memory_id)

        source_ids = record.source_ids or (record.memory_id,)
        try:
            return tuple(self._provenance[source_id] for source_id in source_ids)
        except KeyError as error:
            raise RuntimeError(
                f"provenance snapshot is missing: {error.args[0]}"
            ) from error

    def forget(self, now: int, max_records: int) -> tuple[str, ...]:
        if max_records < 0:
            raise ValueError("max_records must be non-negative")

        expired = [
            record
            for record in self._records
            if record.expires_at is not None and record.expires_at <= now
        ]
        expired_ids = {record.memory_id for record in expired}
        active = [
            record for record in self._records if record.memory_id not in expired_ids
        ]
        overflow = max(0, len(active) - max_records)
        low_value = sorted(
            active,
            key=lambda record: (record.importance, record.created_at, record.memory_id),
        )[:overflow]
        removed_ids = expired_ids | {record.memory_id for record in low_value}
        self._records = [
            record for record in self._records if record.memory_id not in removed_ids
        ]
        return tuple(record.memory_id for record in (*expired, *low_value))


@dataclass(frozen=True)
class StateRecord:
    key: str
    value: str
    revision: int


class StateConflict(RuntimeError):
    pass


class ExternalState:
    def __init__(self) -> None:
        self._records: dict[str, StateRecord] = {}

    def read(self, key: str) -> StateRecord | None:
        return self._records.get(key)

    def write(self, key: str, value: str, expected_revision: int) -> StateRecord:
        current = self._records.get(key)
        current_revision = current.revision if current else 0
        if expected_revision != current_revision:
            raise StateConflict(
                f"expected revision {expected_revision}, found {current_revision}"
            )
        if not key.strip() or not value.strip():
            raise ValueError("state key and value are required")

        updated = StateRecord(key, value, current_revision + 1)
        self._records[key] = updated
        return updated
