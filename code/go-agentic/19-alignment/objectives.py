"""Numerically stable scalar objectives for Chapter 19."""

from math import exp, log, sqrt


def _softplus(value: float) -> float:
    if value > 0:
        return value + log(1.0 + exp(-value))
    return log(1.0 + exp(value))


def dpo_loss(
    chosen_logp: float,
    rejected_logp: float,
    reference_chosen_logp: float,
    reference_rejected_logp: float,
    *,
    beta: float = 0.1,
) -> float:
    """Compute the one-pair DPO negative log-sigmoid loss."""
    if beta <= 0:
        raise ValueError("beta must be positive")
    policy_margin = chosen_logp - rejected_logp
    reference_margin = reference_chosen_logp - reference_rejected_logp
    return _softplus(-beta * (policy_margin - reference_margin))


def grpo_advantages(rewards: list[float], *, epsilon: float = 1e-8) -> list[float]:
    """Normalize rewards within one sampled group."""
    if not rewards:
        raise ValueError("rewards cannot be empty")
    mean = sum(rewards) / len(rewards)
    variance = sum((reward - mean) ** 2 for reward in rewards) / len(rewards)
    standard_deviation = sqrt(variance)
    if standard_deviation < epsilon:
        return [0.0 for _ in rewards]
    return [(reward - mean) / standard_deviation for reward in rewards]
