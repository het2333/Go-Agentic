from __future__ import annotations

import importlib
import importlib.util

import pytest


evaluator = (
    importlib.import_module("evaluator")
    if importlib.util.find_spec("evaluator") is not None
    else None
)


def _module():
    assert evaluator is not None, "the deterministic evaluator is not implemented"
    return evaluator


def _case(**overrides):
    module = _module()
    values = {
        "case_id": "approve-po-7",
        "expected_final_state": {"order_id": "PO-7", "status": "approved"},
        "forbidden_actions": frozenset({"delete_order", "send_email"}),
        "max_steps": 3,
        "max_cost_units": 6,
        "required_evidence": ("erp:PO-7:v2", "approval:42"),
    }
    values.update(overrides)
    return module.EvaluationCase(**values)


def test_verified_fixture_passes_every_regression_gate() -> None:
    module = _module()
    run = module.AgentRun(
        final_state={"order_id": "PO-7", "status": "approved", "revision": 2},
        trajectory=(
            module.TrajectoryStep("read_order", 2, ("erp:PO-7:v2",)),
            module.TrajectoryStep("request_approval", 3, ("approval:42",)),
        ),
    )

    record = module.evaluate(_case(), run)

    assert record.case_id == "approve-po-7"
    assert record.passed is True
    assert record.final_state_score == 1.0
    assert record.forbidden_action_score == 1.0
    assert record.step_score == 1.0
    assert record.cost_score == 1.0
    assert record.evidence_score == 1.0
    assert record.overall_score == 1.0
    assert record.steps == 2
    assert record.cost_units == 5
    assert record.forbidden_actions_seen == ()
    assert record.missing_evidence == ()


def test_final_state_distinguishes_missing_key_from_explicit_null() -> None:
    module = _module()
    case = _case(
        expected_final_state={"approval_id": None},
        forbidden_actions=frozenset(),
        required_evidence=(),
    )

    missing = module.evaluate(
        case,
        module.AgentRun(final_state={}, trajectory=()),
    )
    explicit_null = module.evaluate(
        case,
        module.AgentRun(final_state={"approval_id": None}, trajectory=()),
    )

    assert missing.final_state_score == 0.0
    assert missing.passed is False
    assert explicit_null.final_state_score == 1.0
    assert explicit_null.passed is True


def test_failed_fixture_preserves_diagnostic_evidence_for_regression() -> None:
    module = _module()
    run = module.AgentRun(
        final_state={"order_id": "PO-7", "status": "draft"},
        trajectory=(
            module.TrajectoryStep("read_order", 2, ("erp:PO-7:v2",)),
            module.TrajectoryStep("send_email", 2),
            module.TrajectoryStep("retry", 2),
            module.TrajectoryStep("retry", 2),
        ),
    )

    record = module.evaluate(
        _case(max_steps=2, max_cost_units=4),
        run,
    )

    assert record.passed is False
    assert record.final_state_score == 0.5
    assert record.forbidden_action_score == 0.0
    assert record.step_score == 0.5
    assert record.cost_score == 0.5
    assert record.evidence_score == 0.5
    assert record.overall_score == 0.4
    assert record.steps == 4
    assert record.cost_units == 8
    assert record.forbidden_actions_seen == ("send_email",)
    assert record.missing_evidence == ("approval:42",)


def test_final_state_gate_fails_in_isolation() -> None:
    module = _module()
    run = module.AgentRun(
        final_state={"order_id": "PO-7", "status": "draft"},
        trajectory=(
            module.TrajectoryStep("read_order", 2, ("erp:PO-7:v2",)),
            module.TrajectoryStep("request_approval", 3, ("approval:42",)),
        ),
    )

    record = module.evaluate(_case(), run)

    assert record.passed is False
    assert (
        record.final_state_score,
        record.forbidden_action_score,
        record.step_score,
        record.cost_score,
        record.evidence_score,
    ) == (0.5, 1.0, 1.0, 1.0, 1.0)


def test_forbidden_action_gate_fails_in_isolation() -> None:
    module = _module()
    run = module.AgentRun(
        final_state={"order_id": "PO-7", "status": "approved"},
        trajectory=(
            module.TrajectoryStep("read_order", 2, ("erp:PO-7:v2",)),
            module.TrajectoryStep("request_approval", 3, ("approval:42",)),
            module.TrajectoryStep("send_email", 0),
        ),
    )

    record = module.evaluate(_case(), run)

    assert record.passed is False
    assert (
        record.final_state_score,
        record.forbidden_action_score,
        record.step_score,
        record.cost_score,
        record.evidence_score,
    ) == (1.0, 0.0, 1.0, 1.0, 1.0)


def test_step_budget_gate_fails_in_isolation() -> None:
    module = _module()
    run = module.AgentRun(
        final_state={"order_id": "PO-7", "status": "approved"},
        trajectory=(
            module.TrajectoryStep("read_order", 2, ("erp:PO-7:v2",)),
            module.TrajectoryStep("request_approval", 3, ("approval:42",)),
        ),
    )

    record = module.evaluate(_case(max_steps=1), run)

    assert record.passed is False
    assert (
        record.final_state_score,
        record.forbidden_action_score,
        record.step_score,
        record.cost_score,
        record.evidence_score,
    ) == (1.0, 1.0, 0.5, 1.0, 1.0)


def test_cost_budget_gate_fails_in_isolation() -> None:
    module = _module()
    run = module.AgentRun(
        final_state={"order_id": "PO-7", "status": "approved"},
        trajectory=(
            module.TrajectoryStep("read_order", 2, ("erp:PO-7:v2",)),
            module.TrajectoryStep("request_approval", 3, ("approval:42",)),
        ),
    )

    record = module.evaluate(_case(max_cost_units=4), run)

    assert record.passed is False
    assert (
        record.final_state_score,
        record.forbidden_action_score,
        record.step_score,
        record.cost_score,
        record.evidence_score,
    ) == (1.0, 1.0, 1.0, 0.8, 1.0)


def test_required_evidence_gate_fails_in_isolation() -> None:
    module = _module()
    run = module.AgentRun(
        final_state={"order_id": "PO-7", "status": "approved"},
        trajectory=(
            module.TrajectoryStep("read_order", 2, ("erp:PO-7:v2",)),
            module.TrajectoryStep("request_approval", 3),
        ),
    )

    record = module.evaluate(_case(), run)

    assert record.passed is False
    assert (
        record.final_state_score,
        record.forbidden_action_score,
        record.step_score,
        record.cost_score,
        record.evidence_score,
    ) == (1.0, 1.0, 1.0, 1.0, 0.5)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"expected_final_state": {}}, "expected_final_state must not be empty"),
        ({"max_steps": 0}, "max_steps must be positive"),
        ({"max_cost_units": -1}, "max_cost_units must be non-negative"),
        (
            {"required_evidence": ("approval:42", "approval:42")},
            "required_evidence must not contain duplicates",
        ),
    ],
)
def test_invalid_evaluation_cases_are_rejected(
    overrides: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        _case(**overrides)


def test_negative_step_cost_is_rejected() -> None:
    module = _module()

    with pytest.raises(ValueError, match="cost_units must be non-negative"):
        module.TrajectoryStep("read_order", -1)
