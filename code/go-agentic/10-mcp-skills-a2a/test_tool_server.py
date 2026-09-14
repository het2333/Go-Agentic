from __future__ import annotations

import importlib
import importlib.util

import pytest


tool_server = (
    importlib.import_module("tool_server")
    if importlib.util.find_spec("tool_server") is not None
    else None
)


def _server():
    assert tool_server is not None, "the local tool server is not implemented"
    return tool_server.LocalToolServer()


def test_discovery_exposes_a_typed_read_only_tool_contract() -> None:
    definitions = _server().list_tools()

    assert tuple(definition.name for definition in definitions) == ("lookup_order",)
    (definition,) = definitions
    assert definition.description == "Read one order from the deterministic fixture."
    assert definition.input_schema == {
        "type": "object",
        "properties": {"order_id": {"type": "string", "pattern": "^PO-[0-9]+$"}},
        "required": ["order_id"],
        "additionalProperties": False,
    }
    assert definition.required_permission == "orders:read"
    assert definition.read_only is True


def test_valid_call_returns_the_local_order_without_side_effects() -> None:
    server = _server()
    fixture_before = {
        order_id: dict(order) for order_id, order in tool_server.ORDER_FIXTURE.items()
    }

    result = server.call_tool(
        "lookup_order",
        {"order_id": "PO-7"},
        granted_permissions={"orders:read"},
    )

    assert result.ok is True
    assert result.code == "OK"
    assert result.message == "order found"
    assert result.content == {
        "order_id": "PO-7",
        "supplier": "ABB",
        "due_date": "2026-09-11",
        "status": "delayed",
    }
    assert result.content is not tool_server.ORDER_FIXTURE["PO-7"]
    assert tool_server.ORDER_FIXTURE == fixture_before

    assert isinstance(result.content, dict)
    result.content["status"] = "tampered by caller"
    replay = server.call_tool(
        "lookup_order",
        {"order_id": "PO-7"},
        granted_permissions={"orders:read"},
    )

    assert replay.content == fixture_before["PO-7"]
    assert tool_server.ORDER_FIXTURE == fixture_before


def test_unknown_tool_returns_a_stable_structured_error() -> None:
    result = _server().call_tool(
        "run_shell",
        {"command": "echo unsafe"},
        granted_permissions={"orders:read"},
    )

    assert result.ok is False
    assert result.code == "UNKNOWN_TOOL"
    assert result.message == "tool is not registered: run_shell"
    assert result.content is None


@pytest.mark.parametrize(
    "arguments",
    [None, [], ["order_id", "PO-7"], "PO-7", 7, True],
)
def test_non_mapping_arguments_return_a_stable_schema_error(arguments: object) -> None:
    result = _server().call_tool(
        "lookup_order",
        arguments,
        granted_permissions={"orders:read"},
    )

    assert result.ok is False
    assert result.code == "INVALID_ARGUMENTS"
    assert result.message == "arguments must be an object"
    assert result.content is None


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({}, "arguments must contain exactly: order_id"),
        (
            {"order_id": "PO-7", "include_secret": True},
            "arguments must contain exactly: order_id",
        ),
        ({"order_id": 7}, "order_id must be a string matching ^PO-[0-9]+$"),
        ({"order_id": "order-7"}, "order_id must be a string matching ^PO-[0-9]+$"),
    ],
)
def test_schema_errors_are_rejected_before_permission_checks(
    arguments: dict[str, object], message: str
) -> None:
    result = _server().call_tool(
        "lookup_order",
        arguments,
        granted_permissions=set(),
    )

    assert result.ok is False
    assert result.code == "INVALID_ARGUMENTS"
    assert result.message == message
    assert result.content is None


def test_valid_call_without_permission_is_denied() -> None:
    result = _server().call_tool(
        "lookup_order",
        {"order_id": "PO-7"},
        granted_permissions=set(),
    )

    assert result.ok is False
    assert result.code == "PERMISSION_DENIED"
    assert result.message == "missing permission: orders:read"
    assert result.content is None


def test_missing_fixture_record_is_not_invented() -> None:
    result = _server().call_tool(
        "lookup_order",
        {"order_id": "PO-404"},
        granted_permissions={"orders:read"},
    )

    assert result.ok is False
    assert result.code == "NOT_FOUND"
    assert result.message == "order not found: PO-404"
    assert result.content is None
