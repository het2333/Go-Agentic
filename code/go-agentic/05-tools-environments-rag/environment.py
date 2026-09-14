from __future__ import annotations

import re
from dataclasses import dataclass
from typing import AbstractSet, Literal, Mapping, TypeAlias


ResultCode: TypeAlias = Literal[
    "OK", "UNKNOWN_TOOL", "INVALID_ARGUMENTS", "PERMISSION_DENIED"
]


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: Mapping[str, object]


@dataclass(frozen=True)
class Snippet:
    document_id: str
    title: str
    text: str
    score: int


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    code: ResultCode
    message: str
    snippets: tuple[Snippet, ...] = ()


@dataclass(frozen=True)
class Document:
    document_id: str
    title: str
    body: str
    tags: tuple[str, ...]


LOCAL_CORPUS = (
    Document(
        document_id="loop-control",
        title="Loop control",
        body=(
            "Verification reads environment evidence; retry budgets bound repeated "
            "failures."
        ),
        tags=("verification", "retry", "termination"),
    ),
    Document(
        document_id="tool-contracts",
        title="Tool contracts",
        body=(
            "Typed schemas constrain arguments, permissions gate execution, and "
            "verification evidence returns in observations."
        ),
        tags=("schema", "permission", "verification"),
    ),
    Document(
        document_id="retrieval-design",
        title="Retrieval design",
        body=(
            "Hybrid retrieval combines lexical and metadata signals, then returns "
            "only the context needed for the next decision."
        ),
        tags=("retrieval", "hybrid", "context"),
    ),
)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


class LocalEnvironment:
    def dispatch(
        self,
        call: ToolCall,
        granted_permissions: AbstractSet[str],
    ) -> ToolResult:
        if call.name != "retrieve_context":
            return ToolResult(
                ok=False,
                code="UNKNOWN_TOOL",
                message=f"tool is not registered: {call.name}",
            )

        if set(call.arguments) != {"query", "limit"}:
            return ToolResult(
                ok=False,
                code="INVALID_ARGUMENTS",
                message="arguments must contain exactly: limit, query",
            )

        query = call.arguments["query"]
        limit = call.arguments["limit"]
        if not isinstance(query, str) or not query.strip():
            return ToolResult(
                ok=False,
                code="INVALID_ARGUMENTS",
                message="query must be a non-empty string",
            )
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 3:
            return ToolResult(
                ok=False,
                code="INVALID_ARGUMENTS",
                message="limit must be an integer from 1 to 3",
            )

        required_permission = "corpus:read"
        if required_permission not in granted_permissions:
            return ToolResult(
                ok=False,
                code="PERMISSION_DENIED",
                message=f"missing permission: {required_permission}",
            )

        query_tokens = _tokens(query)
        ranked: list[Snippet] = []
        for document in LOCAL_CORPUS:
            title_hits = len(query_tokens & _tokens(document.title))
            body_hits = len(query_tokens & _tokens(document.body))
            tag_hits = len(query_tokens & set(document.tags))
            score = 2 * title_hits + body_hits + 2 * tag_hits
            if score:
                ranked.append(
                    Snippet(
                        document_id=document.document_id,
                        title=document.title,
                        text=document.body,
                        score=score,
                    )
                )

        ranked.sort(key=lambda snippet: (-snippet.score, snippet.document_id))
        snippets = tuple(ranked[:limit])
        return ToolResult(
            ok=True,
            code="OK",
            message=(
                f"returned {len(snippets)} snippet(s)"
                if snippets
                else "no matching context"
            ),
            snippets=snippets,
        )
