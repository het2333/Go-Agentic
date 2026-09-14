"""Small, dependency-free attention calculations used by Chapter 17."""

from math import exp


def _softmax(values: list[float]) -> list[float]:
    maximum = max(values)
    exponentials = [exp(value - maximum) for value in values]
    denominator = sum(exponentials)
    return [value / denominator for value in exponentials]


def causal_attention(scores: list[list[float]]) -> list[list[float]]:
    """Apply a causal mask and row-wise softmax to a square score matrix."""
    size = len(scores)
    if size == 0 or any(len(row) != size for row in scores):
        raise ValueError("scores must be a non-empty square matrix")

    weights: list[list[float]] = []
    for row_index, row in enumerate(scores):
        visible = _softmax(row[: row_index + 1])
        weights.append(visible + [0.0] * (size - len(visible)))
    return weights
