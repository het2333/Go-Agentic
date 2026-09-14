"""Simple KV-cache capacity calculations for Chapter 21."""


def kv_cache_bytes(
    layers: int,
    batch_size: int,
    sequence_length: int,
    kv_heads: int,
    head_dim: int,
    bytes_per_value: int,
) -> int:
    """Return K and V cache storage for a decoder-only model."""
    dimensions = [layers, batch_size, sequence_length, kv_heads, head_dim, bytes_per_value]
    if any(value <= 0 for value in dimensions):
        raise ValueError("all KV-cache dimensions must be positive")
    return 2 * layers * batch_size * sequence_length * kv_heads * head_dim * bytes_per_value


def max_batch_for_kv_cache(
    memory_budget_bytes: int,
    layers: int,
    sequence_length: int,
    kv_heads: int,
    head_dim: int,
    bytes_per_value: int,
) -> int:
    """Return the largest integer batch fitting in a dedicated cache budget."""
    if memory_budget_bytes < 0:
        raise ValueError("memory_budget_bytes cannot be negative")
    per_request = kv_cache_bytes(layers, 1, sequence_length, kv_heads, head_dim, bytes_per_value)
    return memory_budget_bytes // per_request
