import pytest

from performance import (
    classify_bottleneck,
    estimate_accelerator_cost,
    model_flops_utilization,
    roofline_ceiling,
)


def test_roofline_uses_the_lower_compute_or_bandwidth_ceiling():
    assert roofline_ceiling(100, 2, 30) == pytest.approx(60)
    assert roofline_ceiling(100, 80, 30) == pytest.approx(100)


def test_mfu_compares_observed_work_with_peak_capacity():
    assert model_flops_utilization(400, 4, 200) == pytest.approx(0.5)


def test_bottleneck_classification_uses_ridge_point():
    assert classify_bottleneck(100, 25, 3) == "memory-bound"
    assert classify_bottleneck(100, 25, 5) == "compute-bound"


def test_cost_estimate_accounts_for_device_count_and_runtime():
    assert estimate_accelerator_cost(8, 2.5, 3.0) == pytest.approx(60.0)


@pytest.mark.parametrize(
    "call",
    [
        lambda: roofline_ceiling(0, 2, 3),
        lambda: model_flops_utilization(1, 0, 2),
        lambda: classify_bottleneck(1, 1, -1),
        lambda: estimate_accelerator_cost(-1, 2, 3),
    ],
)
def test_performance_helpers_reject_invalid_inputs(call):
    with pytest.raises(ValueError):
        call()
