import math

import pytest

from attention import causal_attention


def test_causal_attention_rows_are_probabilities():
    weights = causal_attention([[1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [1.0, 2.0, 3.0]])
    assert all(sum(row) == pytest.approx(1.0) for row in weights)


def test_causal_attention_masks_future_positions():
    weights = causal_attention([[1.0, 9.0, 9.0], [1.0, 2.0, 9.0], [1.0, 2.0, 3.0]])
    assert weights[0] == pytest.approx([1.0, 0.0, 0.0])
    assert weights[1][2] == 0.0
    assert weights[2][2] > weights[2][1] > weights[2][0]
    assert all(math.isfinite(value) for row in weights for value in row)


def test_causal_attention_rejects_non_square_scores():
    with pytest.raises(ValueError, match="square"):
        causal_attention([[1.0, 2.0]])
