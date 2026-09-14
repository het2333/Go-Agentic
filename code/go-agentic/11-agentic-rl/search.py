"""Bounded test-time search primitives for Chapter 11."""

from collections import Counter
import heapq


def majority_vote(candidates: list[str]) -> str:
    if not candidates:
        raise ValueError("at least one candidate is required")
    counts = Counter(candidates)
    best_count = max(counts.values())
    return next(candidate for candidate in candidates if counts[candidate] == best_count)


def best_of_n(candidates: list[str], scores: list[float]) -> str:
    if not candidates or len(candidates) != len(scores):
        raise ValueError("candidates and scores must have equal non-zero length")
    best_index = max(range(len(scores)), key=lambda index: (scores[index], -index))
    return candidates[best_index]


def bounded_best_first(
    graph: dict[str, list[str]],
    scores: dict[str, float],
    start: str,
    *,
    max_expansions: int,
) -> dict[str, object]:
    """Expand the highest-scoring discovered node within a fixed budget."""
    if max_expansions <= 0 or start not in graph or start not in scores:
        raise ValueError("a known start and positive expansion budget are required")

    order = 0
    frontier: list[tuple[float, int, str, list[str]]] = [(-scores[start], order, start, [start])]
    visited: set[str] = set()
    best_node = start
    best_path = [start]
    expansions = 0

    while frontier and expansions < max_expansions:
        _, _, node, path = heapq.heappop(frontier)
        if node in visited:
            continue
        visited.add(node)
        expansions += 1
        for child in graph.get(node, []):
            if child not in graph or child not in scores:
                raise ValueError(f"unknown child: {child}")
            child_path = path + [child]
            order += 1
            heapq.heappush(frontier, (-scores[child], order, child, child_path))
            if scores[child] > scores[best_node]:
                best_node = child
                best_path = child_path

    return {"node": best_node, "path": best_path, "expansions": expansions}

