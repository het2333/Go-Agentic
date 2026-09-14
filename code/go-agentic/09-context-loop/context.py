from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Literal, TypeAlias


TerminationReason: TypeAlias = Literal[
    "verified", "step_budget", "token_budget", "cost_budget"
]
EvidenceStatus: TypeAlias = Literal["current", "changed", "stale", "missing"]


@dataclass(frozen=True)
class ContextBudget:
    window_tokens: int
    instruction_tokens: int
    tool_schema_tokens: int
    output_reserve_tokens: int

    def __post_init__(self) -> None:
        values = (
            self.window_tokens,
            self.instruction_tokens,
            self.tool_schema_tokens,
            self.output_reserve_tokens,
        )
        if self.window_tokens < 1 or any(value < 0 for value in values[1:]):
            raise ValueError("token budgets must be non-negative with a positive window")
        if sum(values[1:]) > self.window_tokens:
            raise ValueError("reserved tokens exceed the context window")

    @property
    def evidence_tokens(self) -> int:
        return self.window_tokens - (
            self.instruction_tokens
            + self.tool_schema_tokens
            + self.output_reserve_tokens
        )


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    summary: str
    detail: str
    token_cost: int
    observed_at: int
    valid_until: int | None
    source: str

    def __post_init__(self) -> None:
        if self.token_cost < 0:
            raise ValueError("token_cost must be non-negative")


@dataclass(frozen=True)
class ContextSelection:
    included: tuple[Evidence, ...]
    used_tokens: int
    remaining_tokens: int
    references: tuple[str, ...]
    rejected: tuple[tuple[str, str], ...]


def _terms(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def select_context(
    query: str,
    candidates: tuple[Evidence, ...],
    now: int,
    budget: ContextBudget,
) -> ContextSelection:
    if not query.strip():
        raise ValueError("query must be non-empty")

    query_terms = _terms(query)
    ranked: list[tuple[int, Evidence]] = []
    rejected: list[tuple[str, str]] = []
    for evidence in candidates:
        if evidence.valid_until is not None and evidence.valid_until <= now:
            rejected.append((evidence.evidence_id, "stale"))
            continue
        relevance = len(query_terms & _terms(evidence.summary))
        if relevance == 0:
            rejected.append((evidence.evidence_id, "irrelevant"))
            continue
        ranked.append((relevance, evidence))

    ranked.sort(key=lambda item: -item[0])
    included: list[Evidence] = []
    used_tokens = 0
    for _, evidence in ranked:
        if used_tokens + evidence.token_cost > budget.evidence_tokens:
            rejected.append((evidence.evidence_id, "over_budget"))
            continue
        included.append(evidence)
        used_tokens += evidence.token_cost

    rejected.sort(key=lambda item: item[0])
    return ContextSelection(
        included=tuple(included),
        used_tokens=used_tokens,
        remaining_tokens=budget.evidence_tokens - used_tokens,
        references=tuple(evidence.source for evidence in included),
        rejected=tuple(rejected),
    )


@dataclass(frozen=True)
class TaskState:
    goal: str
    authority: tuple[str, ...]
    completion_rule: str
    completed: tuple[str, ...]
    decisions: tuple[str, ...]
    blockers: tuple[str, ...]
    next_actions: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    usage: LoopUsage
    limits: LoopLimits

    def __post_init__(self) -> None:
        if not self.goal.strip():
            raise ValueError("task goal is required")
        if not self.authority or any(not item.strip() for item in self.authority):
            raise ValueError("at least one authority rule is required")
        if not self.completion_rule.strip():
            raise ValueError("completion rule is required")


@dataclass(frozen=True)
class RemainingBudget:
    remaining_steps: int
    remaining_tokens: int
    remaining_cost_units: int


@dataclass(frozen=True)
class EvidenceSnapshot:
    evidence_id: str
    source: str
    observed_at: int
    valid_until: int | None
    fingerprint: str


@dataclass(frozen=True)
class CompactionRecord:
    summary: str
    resume_state: TaskState
    source_event_ids: tuple[str, ...]
    original_tokens: int
    compacted_tokens: int
    remaining_budget: RemainingBudget
    evidence_snapshots: tuple[EvidenceSnapshot, ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, payload: str) -> CompactionRecord:
        raw = json.loads(payload)
        state_raw = raw["resume_state"]
        state = TaskState(
            goal=state_raw["goal"],
            authority=tuple(state_raw["authority"]),
            completion_rule=state_raw["completion_rule"],
            completed=tuple(state_raw["completed"]),
            decisions=tuple(state_raw["decisions"]),
            blockers=tuple(state_raw["blockers"]),
            next_actions=tuple(state_raw["next_actions"]),
            evidence_refs=tuple(state_raw["evidence_refs"]),
            usage=LoopUsage(**state_raw["usage"]),
            limits=LoopLimits(**state_raw["limits"]),
        )
        persisted_remaining = RemainingBudget(**raw["remaining_budget"])
        expected_remaining = calculate_remaining_budget(state.usage, state.limits)
        if persisted_remaining != expected_remaining:
            raise ValueError("persisted remaining budget does not match usage and limits")

        snapshots = tuple(
            EvidenceSnapshot(**snapshot) for snapshot in raw["evidence_snapshots"]
        )
        source_event_ids = tuple(raw["source_event_ids"])
        if source_event_ids != tuple(snapshot.evidence_id for snapshot in snapshots):
            raise ValueError("source event IDs do not match evidence snapshots")

        return cls(
            summary=raw["summary"],
            resume_state=state,
            source_event_ids=source_event_ids,
            original_tokens=raw["original_tokens"],
            compacted_tokens=raw["compacted_tokens"],
            remaining_budget=persisted_remaining,
            evidence_snapshots=snapshots,
        )


@dataclass(frozen=True)
class ResumeResult:
    ready: bool
    state: TaskState | None
    remaining_budget: RemainingBudget
    evidence_status: tuple[tuple[str, EvidenceStatus], ...]
    budget_status: TerminationReason | None


def _evidence_fingerprint(evidence: Evidence) -> str:
    content = f"{evidence.summary}\0{evidence.detail}\0{evidence.token_cost}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _snapshot(evidence: Evidence) -> EvidenceSnapshot:
    return EvidenceSnapshot(
        evidence_id=evidence.evidence_id,
        source=evidence.source,
        observed_at=evidence.observed_at,
        valid_until=evidence.valid_until,
        fingerprint=_evidence_fingerprint(evidence),
    )


def _missing_evidence_refs(
    state: TaskState,
    snapshots: tuple[EvidenceSnapshot, ...],
) -> tuple[str, ...]:
    covered_refs = {snapshot.source for snapshot in snapshots}
    return tuple(
        evidence_ref
        for evidence_ref in dict.fromkeys(state.evidence_refs)
        if evidence_ref not in covered_refs
    )


def compact(
    events: tuple[Evidence, ...],
    state: TaskState,
    summary_token_limit: int,
) -> CompactionRecord:
    if summary_token_limit < 1:
        raise ValueError("summary_token_limit must be at least 1")

    sections = (
        f"Goal: {state.goal}",
        f"Authority: {'; '.join(state.authority)}",
        f"Completion: {state.completion_rule}",
        f"Next: {'; '.join(state.next_actions) or 'none'}",
        f"Decisions: {'; '.join(state.decisions) or 'none'}",
        f"Blockers: {'; '.join(state.blockers) or 'none'}",
        f"Done: {'; '.join(state.completed) or 'none'}",
        f"Evidence: {'; '.join(state.evidence_refs) or 'none'}",
    )
    accepted: list[str] = []
    tokens_used = 0
    for section in sections:
        section_tokens = section.split()
        if tokens_used + len(section_tokens) <= summary_token_limit:
            accepted.append(section)
            tokens_used += len(section_tokens)

    if not accepted:
        accepted = [" ".join(sections[0].split()[:summary_token_limit])]
        tokens_used = len(accepted[0].split())

    snapshots = tuple(_snapshot(event) for event in events)
    if len({snapshot.evidence_id for snapshot in snapshots}) != len(snapshots):
        raise ValueError("evidence IDs must be unique")
    missing_refs = _missing_evidence_refs(state, snapshots)
    if missing_refs:
        raise ValueError(
            f"required evidence has no snapshot: {', '.join(missing_refs)}"
        )

    return CompactionRecord(
        summary="\n".join(accepted),
        resume_state=state,
        source_event_ids=tuple(snapshot.evidence_id for snapshot in snapshots),
        original_tokens=sum(event.token_cost for event in events),
        compacted_tokens=tokens_used,
        remaining_budget=calculate_remaining_budget(state.usage, state.limits),
        evidence_snapshots=snapshots,
    )


@dataclass(frozen=True)
class LoopLimits:
    max_steps: int
    max_total_tokens: int
    max_cost_units: int

    def __post_init__(self) -> None:
        if min(self.max_steps, self.max_total_tokens, self.max_cost_units) < 1:
            raise ValueError("loop limits must be positive")


@dataclass(frozen=True)
class LoopUsage:
    steps: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_units: int = 0

    def __post_init__(self) -> None:
        if min(self.steps, self.input_tokens, self.output_tokens, self.cost_units) < 0:
            raise ValueError("loop usage must be non-negative")

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def record(
        self, input_tokens: int, output_tokens: int, cost_units: int
    ) -> LoopUsage:
        if min(input_tokens, output_tokens, cost_units) < 0:
            raise ValueError("step usage must be non-negative")
        return LoopUsage(
            steps=self.steps + 1,
            input_tokens=self.input_tokens + input_tokens,
            output_tokens=self.output_tokens + output_tokens,
            cost_units=self.cost_units + cost_units,
        )


def calculate_remaining_budget(
    usage: LoopUsage,
    limits: LoopLimits,
) -> RemainingBudget:
    return RemainingBudget(
        remaining_steps=max(0, limits.max_steps - usage.steps),
        remaining_tokens=max(0, limits.max_total_tokens - usage.total_tokens),
        remaining_cost_units=max(0, limits.max_cost_units - usage.cost_units),
    )


def termination_reason(
    verified: bool,
    usage: LoopUsage,
    limits: LoopLimits,
) -> TerminationReason | None:
    if verified:
        return "verified"
    if usage.steps >= limits.max_steps:
        return "step_budget"
    if usage.total_tokens >= limits.max_total_tokens:
        return "token_budget"
    if usage.cost_units >= limits.max_cost_units:
        return "cost_budget"
    return None


def restore_compaction(
    record: CompactionRecord,
    current_evidence: tuple[Evidence, ...],
    now: int,
) -> ResumeResult:
    expected_remaining = calculate_remaining_budget(
        record.resume_state.usage,
        record.resume_state.limits,
    )
    if record.remaining_budget != expected_remaining:
        raise ValueError("persisted remaining budget does not match usage and limits")

    current_by_id = {evidence.evidence_id: evidence for evidence in current_evidence}
    if len(current_by_id) != len(current_evidence):
        raise ValueError("current evidence IDs must be unique")

    statuses: list[tuple[str, EvidenceStatus]] = []
    for snapshot in record.evidence_snapshots:
        current = current_by_id.get(snapshot.evidence_id)
        if current is None:
            status: EvidenceStatus = "missing"
        elif current.valid_until is not None and current.valid_until <= now:
            status = "stale"
        elif (
            current.source != snapshot.source
            or current.observed_at != snapshot.observed_at
            or current.valid_until != snapshot.valid_until
            or _evidence_fingerprint(current) != snapshot.fingerprint
        ):
            status = "changed"
        else:
            status = "current"
        statuses.append((snapshot.evidence_id, status))
    statuses.extend(
        (evidence_ref, "missing")
        for evidence_ref in _missing_evidence_refs(
            record.resume_state,
            record.evidence_snapshots,
        )
    )

    budget_status = termination_reason(
        verified=False,
        usage=record.resume_state.usage,
        limits=record.resume_state.limits,
    )
    ready = budget_status is None and all(
        status == "current" for _, status in statuses
    )
    return ResumeResult(
        ready=ready,
        state=record.resume_state if ready else None,
        remaining_budget=expected_remaining,
        evidence_status=tuple(statuses),
        budget_status=budget_status,
    )
