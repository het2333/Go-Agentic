import math

import pytest

from tokenizer_decoding import apply_merges, constrained_accepts, top_k_indices, top_p_indices


def test_apply_merges_respects_learned_merge_order():
    tokens = list("lowest")
    merges = [("l", "o"), ("lo", "w"), ("e", "s")]
    assert apply_merges(tokens, merges) == ["low", "es", "t"]


def test_top_k_indices_are_sorted_and_stable():
    assert top_k_indices([0.2, 1.4, 1.4, -1.0], 2) == [1, 2]
    with pytest.raises(ValueError):
        top_k_indices([1.0], 0)


def test_top_p_indices_include_smallest_probability_prefix():
    assert top_p_indices([0.45, 0.30, 0.20, 0.05], 0.7) == [0, 1]
    assert top_p_indices([0.6, 0.4], 1.0) == [0, 1]
    with pytest.raises(ValueError):
        top_p_indices([0.5, -0.1], 0.9)


def test_constrained_accepts_requires_valid_path_and_terminal_state():
    transitions = {
        ("start", "{"): "object",
        ("object", '"ok"'): "key",
        ("key", ":"): "colon",
        ("colon", "true"): "value",
        ("value", "}"): "done",
    }
    assert constrained_accepts(["{", '"ok"', ":", "true", "}"], transitions, "start", {"done"})
    assert not constrained_accepts(["{", '"ok"', ":", "}"], transitions, "start", {"done"})

