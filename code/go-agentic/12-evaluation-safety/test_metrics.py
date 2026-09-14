import pytest

from metrics import categorical_agreement, mean_reciprocal_rank, ndcg_at_k, token_f1


def test_mean_reciprocal_rank_uses_first_relevant_hit():
    rankings = [["x", "a", "b"], ["c", "d"], ["z"]]
    relevant = [{"a"}, {"d"}, {"missing"}]
    assert mean_reciprocal_rank(rankings, relevant) == pytest.approx((0.5 + 0.5 + 0.0) / 3)


def test_ndcg_rewards_correct_order():
    gains = {"a": 3.0, "b": 1.0, "c": 0.0}
    assert ndcg_at_k(["a", "b", "c"], gains, 3) == pytest.approx(1.0)
    assert ndcg_at_k(["b", "a", "c"], gains, 3) < 1.0


def test_token_f1_handles_duplicate_tokens_and_empty_text():
    assert token_f1("a a b", "a b b") == pytest.approx(2 / 3)
    assert token_f1("", "") == 1.0


def test_categorical_agreement_reports_observed_and_kappa():
    result = categorical_agreement(["pass", "pass", "fail", "fail"], ["pass", "fail", "fail", "fail"])
    assert result["observed"] == 0.75
    assert result["kappa"] == pytest.approx(0.5)
    with pytest.raises(ValueError):
        categorical_agreement(["pass"], [])

