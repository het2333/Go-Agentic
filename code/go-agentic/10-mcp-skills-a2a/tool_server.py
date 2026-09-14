"""Deterministic protocol-boundary fixture; this is not an MCP implementation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import AbstractSet, Literal, Mapping, TypeAlias


ResultCode: TypeAlias = Literal[
    "OK", "UNKNOWN_TOOL", "INVALID_ARGUMENTS", "PERMISSION_DENIED", "NOT_FOUND"
]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: Mapping[str, object]
    required_permission: str
    read_only: bool


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    code: ResultCode
    message: str
    content: Mapping[str, str] | None = None


ORDER_FIXTURE = {
    "PO-7": {
        "order_id": "PO-7",
        "supplier": "ABB",
        "due_date": "2026-09-11",
        "status": "delayed",
    }
}


class LocalToolServer:
    """Expose one typed, permission-gated tool over an in-memory fixture."""

    def __init__(self) -> None:
        self._tools = (
            ToolDefinition(
                name="lookup_order",
                description="Read one order from the deterministic fixture.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string", "pattern": "^PO-[0-9]+$"}
                    },
                    "required": ["order_id"],
                    "additionalProperties": False,
                },
                required_permission="orders:read",
                read_only=True,
            ),
        )

    def list_tools(self) -> tuple[ToolDefinition, ...]:
        return self._tools

    def call_tool(
        self,
        name: str,
        arguments: object,
        granted_permissions: AbstractSet[str],
    ) -> ToolResult:
        if name != "lookup_order":
            return ToolResult(
                ok=False,
                code="UNKNOWN_TOOL",
                message=f"tool is not registered: {name}",
            )

        if not isinstance(arguments, Mapping):
            return ToolResult(
                ok=False,
                code="INVALID_ARGUMENTS",
                message="arguments must be an object",
            )

        if set(arguments) != {"order_id"}:
            return ToolResult(
                ok=False,
                code="INVALID_ARGUMENTS",
                message="arguments must contain exactly: order_id",
            )

        order_id = arguments["order_id"]
        if not isinstance(order_id, str) or re.fullmatch(r"PO-[0-9]+", order_id) is None:
            return ToolResult(
                ok=False,
                code="INVALID_ARGUMENTS",
                message="order_id must be a string matching ^PO-[0-9]+$",
            )

        required_permission = self._tools[0].required_permission
        if required_permission not in granted_permissions:
            return ToolResult(
                ok=False,
                code="PERMISSION_DENIED",
                message=f"missing permission: {required_permission}",
            )

        order = ORDER_FIXTURE.get(order_id)
        if order is None:
            return ToolResult(
                ok=False,
                code="NOT_FOUND",
                message=f"order not found: {order_id}",
            )

        return ToolResult(
            ok=True,
            code="OK",
            message="order found",
            content=dict(order),
        )
