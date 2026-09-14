"""Deterministic final-state and trajectory evaluator for local teaching fixtures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    expected_final_state: Mapping[str, object]
    forbidden_actions: frozenset[str]
    max_steps: int
    max_cost_units: int
    required_evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.expected_final_state:
            raise ValueError("expected_final_state must not be empty")
        if self.max_steps < 1:
            raise ValueError("max_steps must be positive")
        if self.max_cost_units < 0:
            raise ValueError("max_cost_units must be non-negative")
        if len(set(self.required_evidence)) != len(self.required_evidence):
            raise ValueError("required_evidence must not contain duplicates")


@dataclass(frozen=True)
class TrajectoryStep:
    action: str
    cost_units: int
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.cost_units < 0:
            raise ValueError("cost_units must be non-negative")


@dataclass(frozen=True)
class AgentRun:
    final_state: Mapping[str, object]
    trajectory: tuple[TrajectoryStep, ...]


@dataclass(frozen=True)
class EvaluationRecord:
    case_id: str
    passed: bool
    final_state_score: float
    forbidden_action_score: float
    step_score: float
    cost_score: float
    evidence_score: float
    overall_score: float
    steps: int
    cost_units: int
    forbidden_actions_seen: tuple[str, ...]
    missing_evidence: tuple[str, ...]


def _budget_score(limit: int, observed: int) -> float:
    if observed <= limit:
        return 1.0
    return limit / observed


def evaluate(case: EvaluationCase, run: AgentRun) -> EvaluationRecord:
    matched_fields = sum(
        key in run.final_state and run.final_state[key] == expected
        for key, expected in case.expected_final_state.items()
    )
    final_state_score = matched_fields / len(case.expected_final_state)

    actions = {step.action for step in run.trajectory}
    forbidden_actions_seen = tuple(sorted(actions & case.forbidden_actions))
    forbidden_action_score = 0.0 if forbidden_actions_seen else 1.0

    steps = len(run.trajectory)
    step_score = _budget_score(case.max_steps, steps)
    cost_units = sum(step.cost_units for step in run.trajectory)
    cost_score = _budget_score(case.max_cost_units, cost_units)

    observed_evidence = {
        evidence_id
        for step in run.trajectory
        for evidence_id in step.evidence
    }
    missing_evidence = tuple(
        evidence_id
        for evidence_id in case.required_evidence
        if evidence_id not in observed_evidence
    )
    evidence_score = (
        1.0
        if not case.required_evidence
        else (len(case.required_evidence) - len(missing_evidence))
        / len(case.required_evidence)
    )

    component_scores = (
        final_state_score,
        forbidden_action_score,
        step_score,
        cost_score,
        evidence_score,
    )
    return EvaluationRecord(
        case_id=case.case_id,
        passed=all(score == 1.0 for score in component_scores),
        final_state_score=final_state_score,
        forbidden_action_score=forbidden_action_score,
        step_score=step_score,
        cost_score=cost_score,
        evidence_score=evidence_score,
        overall_score=round(sum(component_scores) / len(component_scores), 6),
        steps=steps,
        cost_units=cost_units,
        forbidden_actions_seen=forbidden_actions_seen,
        missing_evidence=missing_evidence,
    )
