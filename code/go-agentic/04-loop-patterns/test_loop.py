from __future__ import annotations

import pytest

from loop import Verification, run_loop


def test_failed_verification_replans_then_finishes_with_evidence() -> None:
    plans: list[tuple[int, str | None]] = []

    def plan(attempt: int, feedback: str | None) -> tuple[str, ...]:
        plans.append((attempt, feedback))
        return ("draft",) if attempt == 1 else ("revise", "check")

    def execute(action: str) -> str:
        return {
            "draft": "candidate:v1",
            "revise": "candidate:v2",
            "check": "tests:pass",
        }[action]

    def verify(outputs: tuple[str, ...]) -> Verification:
        if "tests:pass" in outputs:
            return Verification(ok=True, feedback="focused tests pass")
        return Verification(ok=False, feedback="missing test evidence")

    result = run_loop(
        task="produce a verified candidate",
        plan=plan,
        execute=execute,
        verify=verify,
        retry_budget=1,
    )

    assert [transition.state for transition in result.transitions] == [
        "plan",
        "execute",
        "verify",
        "retry",
        "plan",
        "execute",
        "execute",
        "verify",
        "succeeded",
    ]
    assert plans == [(1, None), (2, "missing test evidence")]
    assert result.status == "succeeded"
    assert result.attempts == 2
    assert result.final_feedback == "focused tests pass"


def test_retry_budget_terminates_repeated_verification_failure() -> None:
    result = run_loop(
        task="demonstrate bounded failure",
        plan=lambda attempt, feedback: (f"attempt:{attempt}",),
        execute=lambda action: f"ran:{action}",
        verify=lambda outputs: Verification(ok=False, feedback="still failing"),
        retry_budget=2,
    )

    assert result.status == "retry_budget_exhausted"
    assert result.attempts == 3
    assert [transition.state for transition in result.transitions].count("retry") == 2
    assert result.transitions[-1].state == "terminated"
    assert result.final_feedback == "still failing"


def test_loop_rejects_empty_plans_instead_of_spinning() -> None:
    result = run_loop(
        task="reject an unusable plan",
        plan=lambda attempt, feedback: (),
        execute=lambda action: action,
        verify=lambda outputs: Verification(ok=True, feedback="unreachable"),
        retry_budget=3,
    )

    assert result.status == "invalid_plan"
    assert result.attempts == 1
    assert [transition.state for transition in result.transitions] == [
        "plan",
        "terminated",
    ]
    assert result.final_feedback == "planner returned no actions"


def test_loop_rejects_a_negative_retry_budget() -> None:
    with pytest.raises(ValueError, match="retry_budget must be non-negative"):
        run_loop(
            task="invalid configuration",
            plan=lambda attempt, feedback: ("work",),
            execute=lambda action: action,
            verify=lambda outputs: Verification(ok=True, feedback="done"),
            retry_budget=-1,
        )
