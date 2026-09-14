from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal, Mapping, Protocol, TypeAlias


ToolName: TypeAlias = Literal["run_tests", "read_file", "replace_text"]
RunStatus: TypeAlias = Literal["completed", "unverified", "max_steps"]


@dataclass(frozen=True)
class ToolCall:
    name: ToolName
    arguments: Mapping[str, str]


@dataclass(frozen=True)
class FinalAnswer:
    answer: str


Decision: TypeAlias = ToolCall | FinalAnswer


@dataclass(frozen=True)
class ToolOutput:
    content: str
    verified: bool = False


@dataclass(frozen=True)
class Observation:
    step: int
    call: ToolCall
    ok: bool
    output: str
    verified: bool = False


@dataclass(frozen=True)
class AgentResult:
    status: RunStatus
    answer: str
    verified: bool
    observations: tuple[Observation, ...]


class Policy(Protocol):
    def decide(
        self, task: str, observations: tuple[Observation, ...]
    ) -> Decision: ...


Tool: TypeAlias = Callable[[Mapping[str, str]], ToolOutput]


class LoginWorkspace:
    def __init__(self) -> None:
        self.files = {"src/auth/login.py": "def normalize_username(username):\n    return username\n"}

    def tools(self) -> Mapping[ToolName, Tool]:
        return {
            "run_tests": self._run_tests,
            "read_file": self._read_file,
            "replace_text": self._replace_text,
        }

    def _run_tests(self, arguments: Mapping[str, str]) -> ToolOutput:
        target = arguments.get("target")
        if target != "tests/test_login.py":
            raise ValueError(f"unknown test target: {target}")
        if "return username.strip()" in self.files["src/auth/login.py"]:
            return ToolOutput(
                "PASS tests/test_login.py::test_username_is_trimmed", verified=True
            )
        return ToolOutput(
            "FAIL tests/test_login.py::test_username_is_trimmed\n"
            "AssertionError: expected 'alice', got ' alice '\n"
            "at src/auth/login.py:2"
        )

    def _read_file(self, arguments: Mapping[str, str]) -> ToolOutput:
        path = arguments.get("path", "")
        if path not in self.files:
            raise FileNotFoundError(path)
        return ToolOutput(self.files[path])

    def _replace_text(self, arguments: Mapping[str, str]) -> ToolOutput:
        path = arguments.get("path", "")
        old = arguments.get("old", "")
        new = arguments.get("new", "")
        if path not in self.files:
            raise FileNotFoundError(path)
        if not old or old not in self.files[path]:
            raise ValueError("old text was not found")
        self.files[path] = self.files[path].replace(old, new, 1)
        return ToolOutput(f"UPDATED {path}")


class FakeLoginPolicy:
    def decide(
        self, task: str, observations: tuple[Observation, ...]
    ) -> Decision:
        if not observations:
            return ToolCall("run_tests", {"target": "tests/test_login.py"})

        latest = observations[-1]
        if not latest.ok:
            return FinalAnswer(f"Stopped after tool error: {latest.output}")
        if latest.output.startswith("FAIL "):
            return ToolCall("read_file", {"path": "src/auth/login.py"})
        if latest.call.name == "read_file":
            return ToolCall(
                "replace_text",
                {
                    "path": "src/auth/login.py",
                    "old": "return username",
                    "new": "return username.strip()",
                },
            )
        if latest.call.name == "replace_text":
            return ToolCall("run_tests", {"target": "tests/test_login.py"})
        if latest.verified:
            return FinalAnswer("Login normalization fixed; the focused test passes.")
        return FinalAnswer("Stopped without a verified result.")


def run_agent(
    task: str,
    policy: Policy,
    tools: Mapping[ToolName, Tool],
    max_steps: int = 6,
) -> AgentResult:
    if max_steps < 1:
        raise ValueError("max_steps must be at least 1")

    observations: list[Observation] = []
    tool_steps = 0
    while True:
        decision = policy.decide(task, tuple(observations))
        if isinstance(decision, FinalAnswer):
            verified = bool(observations and observations[-1].verified)
            return AgentResult(
                status="completed" if verified else "unverified",
                answer=decision.answer,
                verified=verified,
                observations=tuple(observations),
            )

        if tool_steps >= max_steps:
            return AgentResult(
                status="max_steps",
                answer=f"Stopped after {max_steps} tool steps without a verified result.",
                verified=False,
                observations=tuple(observations),
            )

        tool_steps += 1
        try:
            tool_output = tools[decision.name](decision.arguments)
            observation = Observation(
                step=tool_steps,
                call=decision,
                ok=True,
                output=tool_output.content,
                verified=tool_output.verified,
            )
        except Exception as error:
            observation = Observation(
                step=tool_steps,
                call=decision,
                ok=False,
                output=f"TOOL_ERROR {type(error).__name__}: {error}",
            )
        observations.append(observation)
