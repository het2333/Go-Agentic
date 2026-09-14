import pytest

from capacity import kv_cache_bytes, max_batch_for_kv_cache


def test_kv_cache_counts_keys_and_values_for_every_layer():
    assert kv_cache_bytes(
        layers=2,
        batch_size=3,
        sequence_length=5,
        kv_heads=4,
        head_dim=8,
        bytes_per_value=2,
    ) == 2 * 2 * 3 * 5 * 4 * 8 * 2


def test_max_batch_uses_only_the_allocated_cache_budget():
    per_request = kv_cache_bytes(2, 1, 5, 4, 8, 2)
    assert max_batch_for_kv_cache(per_request * 7, 2, 5, 4, 8, 2) == 7


def test_kv_cache_rejects_zero_dimensions():
    with pytest.raises(ValueError, match="positive"):
        kv_cache_bytes(2, 1, 0, 4, 8, 2)
