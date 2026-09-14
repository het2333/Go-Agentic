from __future__ import annotations

from agent import (
    FakeLoginPolicy,
    FinalAnswer,
    LoginWorkspace,
    ToolCall,
    run_agent,
)


def test_login_loop_reads_failure_inspects_source_and_finishes_verified() -> None:
    workspace = LoginWorkspace()

    result = run_agent(
        task="Find and fix the login failure, then verify the result.",
        policy=FakeLoginPolicy(),
        tools=workspace.tools(),
        max_steps=6,
    )

    assert [item.call.name for item in result.observations] == [
        "run_tests",
        "read_file",
        "replace_text",
        "run_tests",
    ]
    assert result.observations[0].output.startswith("FAIL tests/test_login.py")
    assert result.observations[1].call.arguments == {"path": "src/auth/login.py"}
    assert result.observations[-1].verified is True
    assert result.status == "completed"
    assert result.verified is True
    assert "return username.strip()" in workspace.files["src/auth/login.py"]


def test_tool_error_becomes_an_observation_and_policy_can_recover() -> None:
    workspace = LoginWorkspace()

    class RecoveringPolicy:
        def decide(self, task: str, observations: tuple):
            if not observations:
                return ToolCall("read_file", {"path": "missing.py"})
            if len(observations) == 1:
                return ToolCall("run_tests", {"target": "tests/test_login.py"})
            return FinalAnswer("The error was observed; the task remains unverified.")

    result = run_agent(
        task="Demonstrate recovery from a tool error.",
        policy=RecoveringPolicy(),
        tools=workspace.tools(),
        max_steps=3,
    )

    assert result.observations[0].ok is False
    assert result.observations[0].output == "TOOL_ERROR FileNotFoundError: missing.py"
    assert result.observations[1].output.startswith("FAIL tests/test_login.py")
    assert result.status == "unverified"
    assert result.verified is False


def test_verified_result_on_final_allowed_tool_call_can_finish() -> None:
    workspace = LoginWorkspace()

    result = run_agent(
        task="Find and fix the login failure, then verify the result.",
        policy=FakeLoginPolicy(),
        tools=workspace.tools(),
        max_steps=4,
    )

    assert len(result.observations) == 4
    assert result.observations[-1].verified is True
    assert result.status == "completed"
    assert result.verified is True


def test_max_steps_stops_a_policy_that_never_finishes() -> None:
    workspace = LoginWorkspace()

    class NeverFinishPolicy:
        def decide(self, task: str, observations: tuple):
            return ToolCall("read_file", {"path": "src/auth/login.py"})

    result = run_agent(
        task="Keep reading forever.",
        policy=NeverFinishPolicy(),
        tools=workspace.tools(),
        max_steps=2,
    )

    assert len(result.observations) == 2
    assert result.status == "max_steps"
    assert result.verified is False
    assert result.answer == "Stopped after 2 tool steps without a verified result."
