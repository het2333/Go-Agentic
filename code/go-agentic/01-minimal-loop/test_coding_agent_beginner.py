"""The beginner agent must remain small while exercising a real tool loop."""
import json
import importlib.util
from pathlib import Path
import sys

import pytest

SOURCE = Path(__file__).with_name("coding_agent_beginner.py")


def load_beginner():
    assert SOURCE.is_file(), "the beginner edition has not been implemented"
    spec = importlib.util.spec_from_file_location("coding_agent_beginner", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def call(name, arguments, call_id):
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(arguments)},
    }


def reply(*calls, content=None):
    return {"role": "assistant", "content": content, "tool_calls": list(calls)}


def test_beginner_agent_repairs_and_verifies_a_real_file(tmp_path):
    beginner = load_beginner()
    (tmp_path / "hello.py").write_text(
        "def normalize_username(username):\n    return username\n",
        encoding="utf-8",
    )
    (tmp_path / "check_hello.py").write_text(
        "from hello import normalize_username\n"
        "assert normalize_username(' Alice ') == 'Alice'\n"
        "print('PASS: 1 case')\n",
        encoding="utf-8",
    )
    responses = iter(
        [
            reply(call("run_command", {"argv": [sys.executable, "check_hello.py"]}, "c1")),
            reply(call("read_file", {"path": "hello.py"}, "c2")),
            reply(
                call(
                    "write_file",
                    {
                        "path": "hello.py",
                        "content": "def normalize_username(username):\n    return username.strip()\n",
                    },
                    "c3",
                )
            ),
            reply(call("run_command", {"argv": [sys.executable, "check_hello.py"]}, "c4")),
            reply(content="已修复 hello.py，并用检查脚本验证通过。"),
        ]
    )

    def model(messages, tools):
        return next(responses)

    workspace = beginner.Workspace(tmp_path, allow_run=True)
    answer, messages = beginner.run_agent(
        "修复 hello.py 并验证", model, workspace, max_rounds=6
    )

    assert answer == "已修复 hello.py，并用检查脚本验证通过。"
    assert "return username.strip()" in (tmp_path / "hello.py").read_text(encoding="utf-8")
    observations = [message for message in messages if message["role"] == "tool"]
    assert [message["tool_call_id"] for message in observations] == ["c1", "c2", "c3", "c4"]
    assert observations[0]["content"].startswith("exit_code=1")
    assert "exit_code=0" in observations[-1]["content"]
    assert "PASS: 1 case" in observations[-1]["content"]


def test_beginner_agent_returns_tool_errors_and_stops_at_round_limit(tmp_path):
    beginner = load_beginner()
    def model(messages, tools):
        return reply(call("read_file", {"path": "missing.py"}, f"c{len(messages)}"))

    with pytest.raises(RuntimeError, match="最大轮数"):
        beginner.run_agent("读取文件", model, beginner.Workspace(tmp_path), max_rounds=2)


def test_beginner_edition_stays_within_the_300_line_learning_contract():
    assert SOURCE.is_file(), "the beginner edition has not been implemented"
    assert len(SOURCE.read_text(encoding="utf-8").splitlines()) <= 300
