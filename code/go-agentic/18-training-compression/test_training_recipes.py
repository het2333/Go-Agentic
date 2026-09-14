import pytest

from training_recipes import completion_mask, lora_trainable_parameters, moe_load_balance, pack_sequences


def test_completion_mask_trains_only_assistant_content():
    roles = ["system", "user", "assistant", "assistant", "tool", "assistant"]
    assert completion_mask(roles) == [0, 0, 1, 1, 0, 1]


def test_pack_sequences_preserves_examples_without_overflow():
    assert pack_sequences([4, 3, 5, 2], 7) == [[4, 3], [5, 2]]
    with pytest.raises(ValueError):
        pack_sequences([8], 7)


def test_lora_parameter_count_excludes_frozen_matrix():
    assert lora_trainable_parameters(4096, 11008, rank=8) == 120832
    with pytest.raises(ValueError):
        lora_trainable_parameters(10, 20, rank=0)


def test_moe_load_balance_exposes_overloaded_experts():
    result = moe_load_balance([0, 0, 0, 1, 2, 3], num_experts=4)
    assert result["fractions"] == [0.5, 1 / 6, 1 / 6, 1 / 6]
    assert result["max_over_mean"] == 2.0
    with pytest.raises(ValueError):
        moe_load_balance([4], num_experts=4)

