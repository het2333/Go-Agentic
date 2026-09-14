from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal, TypeAlias


LoopState: TypeAlias = Literal[
    "plan", "execute", "verify", "retry", "succeeded", "terminated"
]
LoopStatus: TypeAlias = Literal[
    "succeeded", "retry_budget_exhausted", "invalid_plan"
]


@dataclass(frozen=True)
class Verification:
    ok: bool
    feedback: str


@dataclass(frozen=True)
class Transition:
    state: LoopState
    attempt: int
    detail: str


@dataclass(frozen=True)
class LoopResult:
    status: LoopStatus
    attempts: int
    final_feedback: str
    transitions: tuple[Transition, ...]


Planner: TypeAlias = Callable[[int, str | None], tuple[str, ...]]
Executor: TypeAlias = Callable[[str], str]
Verifier: TypeAlias = Callable[[tuple[str, ...]], Verification]


def run_loop(
    task: str,
    plan: Planner,
    execute: Executor,
    verify: Verifier,
    retry_budget: int = 1,
) -> LoopResult:
    if retry_budget < 0:
        raise ValueError("retry_budget must be non-negative")

    transitions: list[Transition] = []
    feedback: str | None = None

    for attempt in range(1, retry_budget + 2):
        transitions.append(Transition("plan", attempt, task))
        actions = tuple(plan(attempt, feedback))
        if not actions:
            final_feedback = "planner returned no actions"
            transitions.append(Transition("terminated", attempt, final_feedback))
            return LoopResult(
                status="invalid_plan",
                attempts=attempt,
                final_feedback=final_feedback,
                transitions=tuple(transitions),
            )

        outputs: list[str] = []
        for action in actions:
            output = execute(action)
            outputs.append(output)
            transitions.append(
                Transition("execute", attempt, f"{action} -> {output}")
            )

        verification = verify(tuple(outputs))
        feedback = verification.feedback
        transitions.append(Transition("verify", attempt, feedback))
        if verification.ok:
            transitions.append(Transition("succeeded", attempt, feedback))
            return LoopResult(
                status="succeeded",
                attempts=attempt,
                final_feedback=feedback,
                transitions=tuple(transitions),
            )

        if attempt <= retry_budget:
            transitions.append(Transition("retry", attempt, feedback))
            continue

        transitions.append(Transition("terminated", attempt, feedback))
        return LoopResult(
            status="retry_budget_exhausted",
            attempts=attempt,
            final_feedback=feedback,
            transitions=tuple(transitions),
        )

    raise AssertionError("unreachable")
