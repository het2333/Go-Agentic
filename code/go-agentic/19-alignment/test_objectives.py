import math

import pytest

from objectives import dpo_loss, grpo_advantages


def test_dpo_loss_rewards_a_stronger_preference_margin():
    weak = dpo_loss(-1.0, -1.2, -1.0, -1.0, beta=0.5)
    strong = dpo_loss(-0.3, -2.0, -1.0, -1.0, beta=0.5)
    assert strong < weak
    assert math.isfinite(strong)


def test_grpo_advantages_are_centered_and_ordered():
    advantages = grpo_advantages([1.0, 2.0, 4.0])
    assert sum(advantages) == pytest.approx(0.0)
    assert advantages[2] > advantages[1] > advantages[0]
    assert sum(value * value for value in advantages) / 3 == pytest.approx(1.0)


def test_grpo_advantages_handle_equal_rewards_without_division_by_zero():
    assert grpo_advantages([3.0, 3.0]) == [0.0, 0.0]
