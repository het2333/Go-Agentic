"""Small transparent metrics for retrieval, generation, and judge audits."""

from collections import Counter
from math import log2


def mean_reciprocal_rank(rankings: list[list[str]], relevant: list[set[str]]) -> float:
    if not rankings or len(rankings) != len(relevant):
        raise ValueError("rankings and relevance sets must align")
    reciprocal_ranks = []
    for ranking, expected in zip(rankings, relevant):
        first = next((rank for rank, item in enumerate(ranking, start=1) if item in expected), None)
        reciprocal_ranks.append(0.0 if first is None else 1.0 / first)
    return sum(reciprocal_ranks) / len(reciprocal_ranks)


def ndcg_at_k(ranking: list[str], gains: dict[str, float], k: int) -> float:
    if k <= 0 or any(gain < 0 for gain in gains.values()):
        raise ValueError("k must be positive and gains non-negative")

    def dcg(values: list[float]) -> float:
        return sum((2**gain - 1) / log2(index + 2) for index, gain in enumerate(values))

    observed = dcg([gains.get(item, 0.0) for item in ranking[:k]])
    ideal = dcg(sorted(gains.values(), reverse=True)[:k])
    return 0.0 if ideal == 0 else observed / ideal


def token_f1(prediction: str, reference: str) -> float:
    predicted = Counter(prediction.split())
    expected = Counter(reference.split())
    if not predicted and not expected:
        return 1.0
    if not predicted or not expected:
        return 0.0
    overlap = sum((predicted & expected).values())
    precision = overlap / sum(predicted.values())
    recall = overlap / sum(expected.values())
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def categorical_agreement(labels_a: list[str], labels_b: list[str]) -> dict[str, float]:
    if not labels_a or len(labels_a) != len(labels_b):
        raise ValueError("label lists must have equal non-zero length")
    total = len(labels_a)
    observed = sum(left == right for left, right in zip(labels_a, labels_b)) / total
    counts_a = Counter(labels_a)
    counts_b = Counter(labels_b)
    categories = set(counts_a) | set(counts_b)
    expected = sum((counts_a[label] / total) * (counts_b[label] / total) for label in categories)
    kappa = 1.0 if expected == 1.0 else (observed - expected) / (1.0 - expected)
    return {"observed": observed, "kappa": kappa}

