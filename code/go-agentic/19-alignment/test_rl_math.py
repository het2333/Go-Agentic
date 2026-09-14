import math

import pytest

from rl_math import (
    bradley_terry_probability,
    discounted_returns,
    generalized_advantages,
    preference_losses,
)


def test_discounted_returns_accumulate_future_reward():
    assert discounted_returns([1.0, 2.0, 3.0], gamma=0.5) == [2.75, 3.5, 3.0]


def test_generalized_advantages_matches_hand_calculation():
    values = [0.5, 1.0, 1.5]
    result = generalized_advantages([1.0, 0.0, 2.0], values, gamma=0.9, lam=0.8)
    assert result == pytest.approx([1.9112, 0.71, 0.5])
    with pytest.raises(ValueError):
        generalized_advantages([1.0], [], gamma=0.9, lam=0.8)


def test_bradley_terry_probability_is_symmetric():
    forward = bradley_terry_probability(2.0, 1.0)
    backward = bradley_terry_probability(1.0, 2.0)
    assert forward > 0.5
    assert forward + backward == pytest.approx(1.0)


def test_preference_losses_distinguish_objective_geometry():
    better = preference_losses(policy_margin=2.0, reference_margin=0.0, beta=0.5)
    worse = preference_losses(policy_margin=-1.0, reference_margin=0.0, beta=0.5)
    assert better["dpo"] < worse["dpo"]
    assert better["kto_desirable"] < worse["kto_desirable"]
    assert better["ipo"] == pytest.approx(1.0)
    with pytest.raises(ValueError):
        preference_losses(1.0, 0.0, beta=0.0)
