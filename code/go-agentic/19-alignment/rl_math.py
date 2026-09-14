"""Scalar reinforcement-learning calculations for Chapter 19."""

from math import exp, log


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + exp(-value))
    positive = exp(value)
    return positive / (1.0 + positive)


def _softplus(value: float) -> float:
    if value > 0:
        return value + log(1.0 + exp(-value))
    return log(1.0 + exp(value))


def discounted_returns(rewards: list[float], *, gamma: float) -> list[float]:
    if not 0 <= gamma <= 1:
        raise ValueError("gamma must be in [0, 1]")
    result = [0.0] * len(rewards)
    running = 0.0
    for index in range(len(rewards) - 1, -1, -1):
        running = rewards[index] + gamma * running
        result[index] = running
    return result


def generalized_advantages(
    rewards: list[float],
    values: list[float],
    *,
    gamma: float,
    lam: float,
    terminal_value: float = 0.0,
) -> list[float]:
    if len(rewards) != len(values) or not 0 <= gamma <= 1 or not 0 <= lam <= 1:
        raise ValueError("rewards/values must align and gamma/lambda must be in [0, 1]")
    result = [0.0] * len(rewards)
    running = 0.0
    for index in range(len(rewards) - 1, -1, -1):
        next_value = terminal_value if index == len(rewards) - 1 else values[index + 1]
        delta = rewards[index] + gamma * next_value - values[index]
        running = delta + gamma * lam * running
        result[index] = running
    return result


def bradley_terry_probability(chosen_reward: float, rejected_reward: float) -> float:
    return _sigmoid(chosen_reward - rejected_reward)


def preference_losses(
    policy_margin: float,
    reference_margin: float,
    *,
    beta: float,
) -> dict[str, float]:
    """Compare DPO, an IPO squared target, and a KTO desirable surrogate."""
    if beta <= 0:
        raise ValueError("beta must be positive")
    relative_margin = policy_margin - reference_margin
    return {
        "dpo": _softplus(-beta * relative_margin),
        "ipo": (relative_margin - 1.0 / (2.0 * beta)) ** 2,
        "kto_desirable": 1.0 - _sigmoid(beta * relative_margin),
    }

