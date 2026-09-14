import pytest

from distributed_memory import fsdp_shard_bytes, zero_memory_per_device


def test_zero_stages_partition_the_expected_states():
    stage0 = zero_memory_per_device(100, 4, stage=0)
    stage2 = zero_memory_per_device(100, 4, stage=2)
    stage3 = zero_memory_per_device(100, 4, stage=3)
    assert stage0["total"] == 1_600
    assert stage2["total"] == 550
    assert stage3["total"] == 400


def test_fsdp_full_shard_partitions_parameters_gradients_and_optimizer():
    assert fsdp_shard_bytes(1_600, 4) == 400


@pytest.mark.parametrize("stage", [-1, 4])
def test_zero_rejects_unknown_stage(stage):
    with pytest.raises(ValueError, match="stage"):
        zero_memory_per_device(100, 4, stage=stage)
