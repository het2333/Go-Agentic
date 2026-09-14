from __future__ import annotations

import pytest

import environment as environment_module
from environment import LocalEnvironment, ToolCall


def test_dispatch_rejects_invalid_arguments_before_execution() -> None:
    environment = LocalEnvironment()

    result = environment.dispatch(
        ToolCall("retrieve_context", {"query": "retry"}),
        granted_permissions=set(),
    )

    assert result.ok is False
    assert result.code == "INVALID_ARGUMENTS"
    assert result.message == "arguments must contain exactly: limit, query"
    assert result.snippets == ()


def test_dispatch_rejects_an_unregistered_tool() -> None:
    environment = LocalEnvironment()

    result = environment.dispatch(
        ToolCall("shell", {"command": "echo unsafe"}),
        granted_permissions={"corpus:read"},
    )

    assert result.ok is False
    assert result.code == "UNKNOWN_TOOL"
    assert result.message == "tool is not registered: shell"
    assert result.snippets == ()


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"query": " ", "limit": 1}, "query must be a non-empty string"),
        ({"query": "retry", "limit": True}, "limit must be an integer from 1 to 3"),
        ({"query": "retry", "limit": 4}, "limit must be an integer from 1 to 3"),
    ],
)
def test_dispatch_rejects_values_outside_the_schema(
    arguments: dict[str, object], message: str
) -> None:
    environment = LocalEnvironment()

    result = environment.dispatch(
        ToolCall("retrieve_context", arguments),
        granted_permissions={"corpus:read"},
    )

    assert result.ok is False
    assert result.code == "INVALID_ARGUMENTS"
    assert result.message == message
    assert result.snippets == ()


def test_dispatch_denies_a_valid_call_before_retrieval_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    environment = LocalEnvironment()
    tokenization_calls: list[str] = []

    def record_tokenization(text: str) -> set[str]:
        tokenization_calls.append(text)
        return set()

    monkeypatch.setattr(environment_module, "_tokens", record_tokenization)

    result = environment.dispatch(
        ToolCall("retrieve_context", {"query": "retry", "limit": 1}),
        granted_permissions=set(),
    )

    assert result.ok is False
    assert result.code == "PERMISSION_DENIED"
    assert result.message == "missing permission: corpus:read"
    assert result.snippets == ()
    assert tokenization_calls == []


def test_retrieval_returns_ranked_jit_snippets_from_the_local_corpus() -> None:
    environment = LocalEnvironment()

    result = environment.dispatch(
        ToolCall(
            "retrieve_context",
            {"query": "verification retry", "limit": 2},
        ),
        granted_permissions={"corpus:read"},
    )

    assert result.ok is True
    assert result.code == "OK"
    assert [snippet.document_id for snippet in result.snippets] == [
        "loop-control",
        "tool-contracts",
    ]
    assert result.snippets[0].text == (
        "Verification reads environment evidence; retry budgets bound repeated failures."
    )


def test_retrieval_reports_no_match_without_inventing_context() -> None:
    environment = LocalEnvironment()

    result = environment.dispatch(
        ToolCall("retrieve_context", {"query": "astronomy", "limit": 2}),
        granted_permissions={"corpus:read"},
    )

    assert result.ok is True
    assert result.code == "OK"
    assert result.message == "no matching context"
    assert result.snippets == ()
