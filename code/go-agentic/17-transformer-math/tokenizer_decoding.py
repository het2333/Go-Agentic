"""Small deterministic models for tokenization and decoding lessons."""


def apply_merges(tokens: list[str], merges: list[tuple[str, str]]) -> list[str]:
    """Apply ordered BPE-style pair merges to an existing token sequence."""
    result = list(tokens)
    for left, right in merges:
        merged: list[str] = []
        index = 0
        while index < len(result):
            if index + 1 < len(result) and result[index] == left and result[index + 1] == right:
                merged.append(left + right)
                index += 2
            else:
                merged.append(result[index])
                index += 1
        result = merged
    return result


def top_k_indices(logits: list[float], k: int) -> list[int]:
    if not logits or k <= 0 or k > len(logits):
        raise ValueError("k must select at least one available logit")
    return sorted(range(len(logits)), key=lambda index: (-logits[index], index))[:k]


def top_p_indices(probabilities: list[float], threshold: float) -> list[int]:
    if not probabilities or not 0 < threshold <= 1:
        raise ValueError("threshold must be in (0, 1]")
    if any(value < 0 for value in probabilities) or sum(probabilities) <= 0:
        raise ValueError("probabilities must be non-negative with positive mass")

    ranked = sorted(range(len(probabilities)), key=lambda index: (-probabilities[index], index))
    selected: list[int] = []
    cumulative = 0.0
    target = threshold * sum(probabilities)
    for index in ranked:
        selected.append(index)
        cumulative += probabilities[index]
        if cumulative >= target:
            break
    return selected


def constrained_accepts(
    tokens: list[str],
    transitions: dict[tuple[str, str], str],
    start_state: str,
    accepting_states: set[str],
) -> bool:
    """Evaluate a token path through a finite-state decoding constraint."""
    state = start_state
    for token in tokens:
        next_state = transitions.get((state, token))
        if next_state is None:
            return False
        state = next_state
    return state in accepting_states

