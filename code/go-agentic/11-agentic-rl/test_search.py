import pytest

from search import best_of_n, bounded_best_first, majority_vote


def test_majority_vote_is_deterministic_on_ties():
    assert majority_vote(["B", "A", "A", "B"]) == "B"
    with pytest.raises(ValueError):
        majority_vote([])


def test_best_of_n_returns_first_highest_scoring_candidate():
    candidates = ["draft", "verified", "verbose"]
    assert best_of_n(candidates, [0.2, 0.9, 0.9]) == "verified"


def test_bounded_best_first_respects_expansion_budget():
    graph = {"root": ["a", "b"], "a": ["a1"], "b": ["b1"], "a1": [], "b1": []}
    scores = {"root": 0.0, "a": 0.8, "b": 0.4, "a1": 1.0, "b1": 0.9}
    result = bounded_best_first(graph, scores, "root", max_expansions=2)
    assert result == {"node": "a1", "path": ["root", "a", "a1"], "expansions": 2}
    with pytest.raises(ValueError):
        bounded_best_first(graph, scores, "root", max_expansions=0)

