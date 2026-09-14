"""Dependency-free calculations for SFT, PEFT, and MoE examples."""


def completion_mask(roles: list[str]) -> list[int]:
    """Return one for assistant tokens and zero for prompt/tool tokens."""
    return [1 if role == "assistant" else 0 for role in roles]


def pack_sequences(lengths: list[int], max_tokens: int) -> list[list[int]]:
    """Pack examples in order with a simple next-fit policy."""
    if max_tokens <= 0 or any(length <= 0 or length > max_tokens for length in lengths):
        raise ValueError("every sequence must fit in a positive token budget")
    packs: list[list[int]] = []
    current: list[int] = []
    used = 0
    for length in lengths:
        if current and used + length > max_tokens:
            packs.append(current)
            current = []
            used = 0
        current.append(length)
        used += length
    if current:
        packs.append(current)
    return packs


def lora_trainable_parameters(in_features: int, out_features: int, rank: int) -> int:
    if min(in_features, out_features, rank) <= 0:
        raise ValueError("matrix dimensions and rank must be positive")
    return rank * (in_features + out_features)


def moe_load_balance(assignments: list[int], num_experts: int) -> dict[str, object]:
    if num_experts <= 0 or not assignments:
        raise ValueError("experts and assignments are required")
    if any(expert < 0 or expert >= num_experts for expert in assignments):
        raise ValueError("assignment references an unknown expert")

    counts = [0] * num_experts
    for expert in assignments:
        counts[expert] += 1
    total = len(assignments)
    fractions = [count / total for count in counts]
    mean = 1 / num_experts
    return {
        "counts": counts,
        "fractions": fractions,
        "max_over_mean": max(fractions) / mean,
    }

