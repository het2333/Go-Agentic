import pytest

from parallelism import (
    data_parallel_sync_bytes,
    parallel_world_size,
    sequence_shard_length,
    training_budget,
)


def test_parallel_world_size_multiplies_independent_dimensions():
    assert parallel_world_size(data=8, tensor=4, pipeline=2, sequence=2) == 128


def test_sequence_parallel_uses_ceiling_for_uneven_lengths():
    assert sequence_shard_length(4097, 4) == 1025


def test_ring_sync_reports_per_device_gradient_traffic():
    assert data_parallel_sync_bytes(1_000, 4) == pytest.approx(1_500)


def test_training_budget_returns_device_hours_and_cost():
    assert training_budget(16, 12.5, 2.0) == {
        "device_hours": 200.0,
        "estimated_cost": 400.0,
    }


@pytest.mark.parametrize(
    "call",
    [
        lambda: parallel_world_size(data=0),
        lambda: sequence_shard_length(10, 0),
        lambda: data_parallel_sync_bytes(-1, 2),
        lambda: training_budget(1, -1, 2),
    ],
)
def test_parallelism_helpers_reject_invalid_inputs(call):
    with pytest.raises(ValueError):
        call()
