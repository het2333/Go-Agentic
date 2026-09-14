import pytest

from advanced_retrieval import hybrid_scores, reciprocal_rank_fusion


def test_reciprocal_rank_fusion_rewards_cross_retriever_agreement():
    fused = reciprocal_rank_fusion([["a", "b", "c"], ["b", "d", "a"]], rank_constant=10)
    assert [doc_id for doc_id, _ in fused[:2]] == ["b", "a"]
    assert fused[0][1] > fused[1][1]


def test_hybrid_scores_normalize_incompatible_score_scales():
    result = hybrid_scores(
        lexical={"a": 100.0, "b": 50.0},
        dense={"a": 0.2, "b": 0.9},
        lexical_weight=0.25,
    )
    assert result[0][0] == "b"
    assert dict(result)["a"] == pytest.approx(0.25)
    with pytest.raises(ValueError):
        hybrid_scores({}, {}, lexical_weight=0.5)

