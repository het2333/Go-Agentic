"""Deterministic rank-fusion examples for advanced retrieval lessons."""


def reciprocal_rank_fusion(
    rankings: list[list[str]], *, rank_constant: int = 60
) -> list[tuple[str, float]]:
    if not rankings or rank_constant < 0:
        raise ValueError("rankings are required and rank_constant must be non-negative")
    scores: dict[str, float] = {}
    first_seen: dict[str, int] = {}
    order = 0
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            if doc_id not in first_seen:
                first_seen[doc_id] = order
                order += 1
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rank_constant + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], first_seen[item[0]]))


def _minmax(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    low = min(values.values())
    high = max(values.values())
    if high == low:
        return {key: 1.0 for key in values}
    return {key: (value - low) / (high - low) for key, value in values.items()}


def hybrid_scores(
    lexical: dict[str, float],
    dense: dict[str, float],
    *,
    lexical_weight: float,
) -> list[tuple[str, float]]:
    if not lexical and not dense:
        raise ValueError("at least one retriever must return candidates")
    if not 0 <= lexical_weight <= 1:
        raise ValueError("lexical_weight must be in [0, 1]")
    lexical_norm = _minmax(lexical)
    dense_norm = _minmax(dense)
    documents = list(dict.fromkeys([*lexical, *dense]))
    scores = {
        doc_id: lexical_weight * lexical_norm.get(doc_id, 0.0)
        + (1.0 - lexical_weight) * dense_norm.get(doc_id, 0.0)
        for doc_id in documents
    }
    return sorted(scores.items(), key=lambda item: (-item[1], documents.index(item[0])))

