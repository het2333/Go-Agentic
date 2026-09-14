"""离线验证真实文件、子进程和 HTTP 消息协议；不消耗模型 token。"""
from contextlib import contextmanager
import gc
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

import coding_agent as agent


def call(name, arguments, call_id="call_1"):
    return {"id": call_id, "type": "function", "function": {
        "name": name, "arguments": json.dumps(arguments)}}


def reply(*calls, content=None):
    return {"role": "assistant", "content": content, "tool_calls": list(calls)}


@contextmanager
def local_server(handler):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        assert not thread.is_alive()


def test_http_loop_repairs_real_file_and_returns_test_observation(tmp_path):
    (tmp_path / "hello.py").write_text("def normalize_username(name):\n    return name\n")
    (tmp_path / "check_hello.py").write_text(
        "from hello import normalize_username\n"
        "assert normalize_username(' alice ') == 'alice'\nprint('PASS')\n")
    requests = []
    responses = iter([
        reply(call("read_file", {"path": "hello.py"})),
        reply(call("write_file", {"path": "hello.py", "content":
              "def normalize_username(name):\n    return name.strip()\n"}, "call_2")),
        reply(call("run_command", {"argv": [sys.executable, "check_hello.py"]}, "call_3")),
        reply(content="修复完成，测试通过。"),
    ])

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            requests.append((self.path, json.loads(self.rfile.read(
                int(self.headers["Content-Length"]))), dict(self.headers.items())))
            body = json.dumps({"choices": [{"finish_reason": "stop",
                                           "message": next(responses)}]}).encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body)

    with local_server(Handler) as server:
        model = agent.ChatModel("test-key", "test-model",
                                f"http://127.0.0.1:{server.server_port}/v1")
        answer = agent.run_agent("修复 hello.py 并验证", model,
                                 agent.Workspace(tmp_path, allow_run=True))

    assert answer == "修复完成，测试通过。"
    assert ".strip()" in (tmp_path / "hello.py").read_text()
    assert all(path == "/v1/chat/completions" for path, _, _ in requests)
    assert all(headers["Authorization"] == "Bearer test-key" for _, _, headers in requests)
    assert all(headers["Content-Type"] == "application/json" for _, _, headers in requests)
    history = requests[-1][1]["messages"]
    assert [m["role"] for m in history] == [
        "system", "user", "assistant", "tool", "assistant", "tool", "assistant", "tool"]
    assert [m["tool_call_id"] for m in history if m["role"] == "tool"] == [
        "call_1", "call_2", "call_3"]
    assert "exit_code=0" in history[-1]["content"]
    assert "PASS" in history[-1]["content"]


def test_tool_errors_return_to_model_and_multiple_calls_keep_their_ids(tmp_path):
    (tmp_path / "ok.txt").write_text("hello")
    def model(messages, tools):
        if len(messages) == 2:
            bad = call("read_file", {}, "bad_json")
            bad["function"]["arguments"] = "{broken"
            return reply(bad, call("missing_tool", {}, "unknown"),
                         call("read_file", {"path": "ok.txt"}, "good"))
        observations = [m for m in messages if m["role"] == "tool"]
        assert [m["tool_call_id"] for m in observations] == ["bad_json", "unknown", "good"]
        assert all(m["content"].startswith("TOOL_ERROR") for m in observations[:2])
        assert observations[-1]["content"] == "hello"
        return reply(content="已恢复")
    assert agent.run_agent("读取文件", model, agent.Workspace(tmp_path)) == "已恢复"


@pytest.mark.parametrize("malformed", [
    {"id": "bad", "type": "function", "function": {}},
    {"id": "bad", "type": "function", "function": {"name": 42, "arguments": "{}"}},
    {"id": "bad", "type": "function", "function": {
        "name": "read_file", "arguments": {}}},
    {"id": "bad", "type": "other", "function": {
        "name": "read_file", "arguments": "{}"}},
])
def test_malformed_tool_call_with_usable_id_becomes_observation(tmp_path, malformed):
    def model(messages, tools):
        observations = [message for message in messages if message["role"] == "tool"]
        if not observations:
            return reply(malformed)
        assert observations == [{
            "role": "tool", "tool_call_id": "bad",
            "content": observations[0]["content"],
        }]
        assert observations[0]["content"].startswith("TOOL_ERROR")
        return reply(content="已处理格式错误")

    assert agent.run_agent("处理错误调用", model, agent.Workspace(tmp_path)) == "已处理格式错误"


@pytest.mark.parametrize("malformed", [
    {},
    {"id": ""},
    {"id": 42, "type": "function", "function": {
        "name": "list_files", "arguments": "{}"}},
    "not-an-object",
])
def test_tool_call_without_usable_id_fails_clearly(tmp_path, malformed):
    def model(messages, tools):
        return reply(malformed)

    with pytest.raises(RuntimeError, match="工具调用缺少可用 ID"):
        agent.run_agent("拒绝无 ID 调用", model, agent.Workspace(tmp_path))


@pytest.mark.parametrize("message", [
    None,
    [],
    {"role": "tool", "content": "wrong role"},
    {"role": "assistant", "content": None, "tool_calls": {}},
])
def test_invalid_assistant_message_fails_without_raw_type_errors(tmp_path, message):
    def model(messages, tools):
        return message

    with pytest.raises(RuntimeError, match="assistant 消息"):
        agent.run_agent("拒绝错误消息", model, agent.Workspace(tmp_path))


def test_run_command_tool_is_omitted_without_opt_in(tmp_path):
    observed = []

    def model(messages, tools):
        observed.extend(item["function"]["name"] for item in tools)
        return reply(content="完成")

    assert agent.run_agent("查看工具", model, agent.Workspace(tmp_path)) == "完成"
    assert "run_command" not in observed


def test_round_limit_stops_infinite_model(tmp_path):
    count = 0
    def model(messages, tools):
        nonlocal count
        count += 1
        return reply(call("list_files", {"path": "."}))
    with pytest.raises(RuntimeError, match="轮数"):
        agent.run_agent("不停读取", model, agent.Workspace(tmp_path), max_rounds=2)
    assert count == 2


@pytest.mark.parametrize("path", ["../outside.txt", "/etc/passwd"])
def test_file_tools_reject_paths_outside_workspace(tmp_path, path):
    result = agent.Workspace(tmp_path).execute(call("read_file", {"path": path}))
    assert result.startswith("TOOL_ERROR")


def test_file_tools_reject_symlink_escape(tmp_path):
    (tmp_path / "escape").symlink_to(tmp_path.parent, target_is_directory=True)
    result = agent.Workspace(tmp_path).execute(call("write_file", {
        "path": "escape/should-not-exist.txt", "content": "oops"}))
    assert result.startswith("TOOL_ERROR")
    assert not (tmp_path.parent / "should-not-exist.txt").exists()


def test_file_tools_use_safe_regular_files_and_create_parents(tmp_path):
    workspace = agent.Workspace(tmp_path)
    assert workspace.execute(call("write_file", {
        "path": "nested/deeper/value.txt", "content": "hello"})) == "已写入 nested/deeper/value.txt（5 字符）"
    assert workspace.execute(call("read_file", {
        "path": "nested/deeper/value.txt"})) == "hello"
    assert workspace.execute(call("list_files", {"path": "nested"})) == "deeper/"


@pytest.mark.parametrize(("name", "arguments"), [
    ("list_files", {"path": "escape"}),
    ("read_file", {"path": "escape/secret.txt"}),
    ("write_file", {"path": "escape/new.txt", "content": "oops"}),
])
def test_all_file_tools_reject_parent_symlinks(tmp_path, name, arguments):
    outside = tmp_path.parent / f"{tmp_path.name}-outside-parent"
    outside.mkdir()
    (outside / "secret.txt").write_text("secret")
    (tmp_path / "escape").symlink_to(outside, target_is_directory=True)
    try:
        result = agent.Workspace(tmp_path).execute(call(name, arguments))
        assert result.startswith("TOOL_ERROR")
        assert not (outside / "new.txt").exists()
    finally:
        (tmp_path / "escape").unlink()
        for child in outside.iterdir():
            child.unlink()
        outside.rmdir()


@pytest.mark.parametrize(("name", "path"), [
    ("list_files", "linked-directory"),
    ("read_file", "linked-file"),
    ("write_file", "linked-file"),
])
def test_all_file_tools_reject_final_symlinks(tmp_path, name, path):
    outside = tmp_path.parent / f"{tmp_path.name}-outside-final"
    outside.mkdir()
    outside_file = outside / "value.txt"
    outside_file.write_text("unchanged")
    (tmp_path / "linked-directory").symlink_to(outside, target_is_directory=True)
    (tmp_path / "linked-file").symlink_to(outside_file)
    arguments = {"path": path}
    if name == "write_file":
        arguments["content"] = "oops"
    try:
        result = agent.Workspace(tmp_path).execute(call(name, arguments))
        assert result.startswith("TOOL_ERROR")
        assert outside_file.read_text() == "unchanged"
    finally:
        (tmp_path / "linked-directory").unlink()
        (tmp_path / "linked-file").unlink()
        outside_file.unlink()
        outside.rmdir()


def test_symlink_swap_after_parent_open_cannot_redirect_write(tmp_path, monkeypatch):
    workspace_root = tmp_path / "workspace"
    safe = workspace_root / "safe"
    held = workspace_root / "held"
    outside = tmp_path / "outside"
    safe.mkdir(parents=True)
    outside.mkdir()
    workspace = agent.Workspace(workspace_root)
    real_open = os.open
    swapped = False

    def racing_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if path == "escaped.txt" and dir_fd is not None and not swapped:
            safe.rename(held)
            safe.symlink_to(outside, target_is_directory=True)
            swapped = True
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(agent.os, "open", racing_open)
    assert workspace.write_file("safe/escaped.txt", "inside") == "已写入 safe/escaped.txt（6 字符）"
    assert swapped
    assert not (outside / "escaped.txt").exists()
    assert (held / "escaped.txt").read_text() == "inside"


def test_workspace_root_descriptor_survives_root_path_replacement(tmp_path):
    workspace_root = tmp_path / "workspace"
    held = tmp_path / "held"
    outside = tmp_path / "outside"
    workspace_root.mkdir()
    outside.mkdir()
    workspace = agent.Workspace(workspace_root)
    workspace_root.rename(held)
    workspace_root.symlink_to(outside, target_is_directory=True)

    assert workspace.write_file("bound.txt", "inside") == "已写入 bound.txt（6 字符）"
    assert (held / "bound.txt").read_text() == "inside"
    assert not (outside / "bound.txt").exists()


def test_workspace_root_construction_survives_ancestor_swap(tmp_path, monkeypatch):
    ancestor = tmp_path / "ancestor"
    held = tmp_path / "held"
    intended_root = ancestor / "workspace"
    outside = tmp_path / "outside"
    outside_root = outside / "workspace"
    intended_root.mkdir(parents=True)
    outside_root.mkdir(parents=True)
    root_argument = intended_root.absolute()
    real_open = os.open
    swapped = False

    def racing_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        opening_old_absolute_root = dir_fd is None and os.fspath(path) == os.fspath(root_argument)
        opening_new_final_component = dir_fd is not None and path == "workspace"
        if not swapped and (opening_old_absolute_root or opening_new_final_component):
            ancestor.rename(held)
            ancestor.symlink_to(outside, target_is_directory=True)
            swapped = True
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(agent.os, "open", racing_open)
    monkeypatch.setattr(agent.os, "supports_dir_fd", os.supports_dir_fd | {racing_open})
    workspace = agent.Workspace(root_argument)
    assert swapped
    assert workspace.write_file("bound.txt", "inside") == "已写入 bound.txt（6 字符）"
    assert (held / "workspace/bound.txt").read_text() == "inside"
    assert not (outside_root / "bound.txt").exists()


def test_relative_workspace_root_binds_current_directory_before_ancestor_swap(tmp_path, monkeypatch):
    ancestor = tmp_path / "ancestor"
    held = tmp_path / "held"
    intended_root = ancestor / "workspace"
    outside = tmp_path / "outside"
    outside_root = outside / "workspace"
    intended_root.mkdir(parents=True)
    outside_root.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    real_open = os.open
    swapped = False

    def racing_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        opening_old_absolute_root = dir_fd is None and os.fspath(path) == os.fspath(intended_root)
        opening_new_final_component = dir_fd is not None and path == "workspace"
        if not swapped and (opening_old_absolute_root or opening_new_final_component):
            ancestor.rename(held)
            ancestor.symlink_to(outside, target_is_directory=True)
            swapped = True
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(agent.os, "open", racing_open)
    monkeypatch.setattr(agent.os, "supports_dir_fd", os.supports_dir_fd | {racing_open})
    workspace = agent.Workspace("ancestor/workspace")
    assert swapped
    assert workspace.write_file("bound.txt", "inside") == "已写入 bound.txt（6 字符）"
    assert (held / "workspace/bound.txt").read_text() == "inside"
    assert not (outside_root / "bound.txt").exists()


def test_workspace_root_rejects_symlink_components_and_parent_traversal(tmp_path):
    actual = tmp_path / "actual"
    workspace_root = actual / "workspace"
    workspace_root.mkdir(parents=True)
    (tmp_path / "linked-ancestor").symlink_to(actual, target_is_directory=True)
    with pytest.raises(OSError):
        agent.Workspace(tmp_path / "linked-ancestor/workspace")
    with pytest.raises(ValueError, match="父目录"):
        agent.Workspace("../outside")


def test_concurrent_parent_creation_is_reopened_without_following_links(tmp_path, monkeypatch):
    workspace = agent.Workspace(tmp_path)
    real_open = os.open
    raced = False

    def racing_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal raced
        if path == "raced" and flags & os.O_DIRECTORY and dir_fd is not None and not raced:
            os.mkdir("raced", dir_fd=dir_fd)
            raced = True
            raise FileNotFoundError("forced creation race")
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(agent.os, "open", racing_open)
    assert workspace.write_file("raced/value.txt", "safe") == "已写入 raced/value.txt（4 字符）"
    assert raced
    assert (tmp_path / "raced/value.txt").read_text() == "safe"


def test_concurrent_final_creation_is_reopened_and_bound(tmp_path, monkeypatch):
    workspace = agent.Workspace(tmp_path)
    real_open = os.open
    raced = False

    def racing_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal raced
        if path == "value.txt" and dir_fd is not None and not flags & os.O_CREAT and not raced:
            descriptor = real_open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                                   0o666, dir_fd=dir_fd)
            os.write(descriptor, b"racer")
            os.close(descriptor)
            raced = True
            raise FileNotFoundError("forced creation race")
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(agent.os, "open", racing_open)
    assert workspace.write_file("value.txt", "safe") == "已写入 value.txt（4 字符）"
    assert raced
    assert (tmp_path / "value.txt").read_text() == "safe"


@pytest.mark.parametrize(("name", "arguments"), [
    ("list_files", {"path": "value.txt"}),
    ("read_file", {"path": "directory"}),
    ("write_file", {"path": "directory", "content": "oops"}),
])
def test_file_tools_reject_wrong_target_types(tmp_path, name, arguments):
    (tmp_path / "value.txt").write_text("value")
    (tmp_path / "directory").mkdir()
    assert agent.Workspace(tmp_path).execute(call(name, arguments)).startswith("TOOL_ERROR")


def test_close_is_idempotent_and_file_operations_fail_after_close(tmp_path):
    workspace = agent.Workspace(tmp_path)
    workspace.close()
    workspace.close()
    result = workspace.execute(call("list_files", {"path": "."}))
    assert result == "TOOL_ERROR RuntimeError: 工作目录已关闭"


def test_close_and_access_cannot_duplicate_a_reused_descriptor(tmp_path, monkeypatch):
    intended = tmp_path / "intended"
    unrelated = tmp_path / "unrelated"
    intended.mkdir()
    unrelated.mkdir()
    (intended / "intended.txt").write_text("inside")
    (unrelated / "unrelated.txt").write_text("outside")
    workspace = agent.Workspace(intended)
    real_dup = os.dup
    real_open = os.open
    entered_dup = threading.Event()
    release_dup = threading.Event()
    close_done = threading.Event()
    blocked_descriptor = []
    outcome = {}

    def blocking_dup(descriptor):
        if not entered_dup.is_set():
            blocked_descriptor.append(descriptor)
            entered_dup.set()
            assert release_dup.wait(timeout=2)
        return real_dup(descriptor)

    def access_workspace():
        try:
            outcome["result"] = workspace.list_files(".")
        except Exception as error:
            outcome["error"] = error

    def close_workspace():
        workspace.close()
        close_done.set()

    monkeypatch.setattr(agent.os, "dup", blocking_dup)
    access_thread = threading.Thread(target=access_workspace)
    access_thread.start()
    assert entered_dup.wait(timeout=1)
    close_thread = threading.Thread(target=close_workspace)
    close_thread.start()
    rebound = False
    try:
        if close_done.wait(timeout=0.2):
            unrelated_descriptor = real_open(unrelated, agent._directory_flags())
            os.dup2(unrelated_descriptor, blocked_descriptor[0])
            if unrelated_descriptor != blocked_descriptor[0]:
                os.close(unrelated_descriptor)
            rebound = True
        release_dup.set()
        access_thread.join(timeout=2)
        close_thread.join(timeout=2)
        assert not access_thread.is_alive()
        assert not close_thread.is_alive()
        assert close_done.is_set()
        assert outcome == {"result": "intended.txt"}
    finally:
        release_dup.set()
        if rebound:
            try:
                os.close(blocked_descriptor[0])
            except OSError:
                pass


def test_manual_close_prevents_finalizer_from_closing_a_reused_descriptor(tmp_path):
    workspace = agent.Workspace(tmp_path)
    original_descriptor = workspace._root_handle.descriptor
    workspace.close()
    source_descriptor = os.open(tmp_path, agent._directory_flags())
    os.dup2(source_descriptor, original_descriptor)
    if source_descriptor != original_descriptor:
        os.close(source_descriptor)
    del workspace
    gc.collect()
    try:
        assert os.fstat(original_descriptor).st_ino == tmp_path.stat().st_ino
    finally:
        os.close(original_descriptor)


def test_workspace_fails_closed_when_safe_primitives_are_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "_safe_file_support_error", lambda: "forced missing primitive",
                        raising=False)
    with pytest.raises(RuntimeError, match="forced missing primitive"):
        agent.Workspace(tmp_path)


def test_commands_require_opt_in_and_failures_are_observations(tmp_path):
    command = call("run_command", {"argv": [sys.executable, "-c", "raise SystemExit(7)"]})
    assert agent.Workspace(tmp_path).execute(command).startswith("TOOL_ERROR")
    assert "exit_code=7" in agent.Workspace(tmp_path, allow_run=True).execute(command)


def test_command_timeout_becomes_observation(tmp_path):
    result = agent.Workspace(tmp_path, allow_run=True, command_timeout=0.1).execute(
        call("run_command", {"argv": [sys.executable, "-c", "import time; time.sleep(10)"]}))
    assert "超时" in result


def test_subprocess_environment_uses_documented_allowlist(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", "/expected/path")
    monkeypatch.setenv("HOME", "/expected/home")
    monkeypatch.setenv("LANG", "C.UTF-8")
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-leak")
    monkeypatch.setenv("SENTINEL_SECRET", "must-not-leak")
    script = (
        "import json, os; print(json.dumps({key: os.getenv(key) for key in "
        "['PATH', 'HOME', 'LANG', 'OPENAI_API_KEY', 'SENTINEL_SECRET']}))"
    )
    result = agent.Workspace(tmp_path, allow_run=True).execute(
        call("run_command", {"argv": [sys.executable, "-c", script]}))
    assert result.startswith("exit_code=0\n")
    environment = json.loads(result.split("\n", 1)[1])
    assert environment == {
        "PATH": "/expected/path",
        "HOME": "/expected/home",
        "LANG": "C.UTF-8",
        "OPENAI_API_KEY": None,
        "SENTINEL_SECRET": None,
    }


def test_file_and_command_outputs_are_truncated(tmp_path):
    oversized = "x" * (agent.OUTPUT_LIMIT + 100)
    (tmp_path / "large.txt").write_text(oversized)
    workspace = agent.Workspace(tmp_path, allow_run=True)
    file_result = workspace.execute(call("read_file", {"path": "large.txt"}))
    command_result = workspace.execute(call("run_command", {
        "argv": [sys.executable, "-c", f"print('x' * {agent.OUTPUT_LIMIT + 100})"]}))
    assert file_result == oversized[:agent.OUTPUT_LIMIT] + "\n[输出已截断]"
    assert command_result.startswith("exit_code=0\n")
    assert command_result.endswith("\n[输出已截断]")
    assert len(command_result) == agent.OUTPUT_LIMIT + len("\n[输出已截断]")


def test_chat_model_rejects_non_https_remote_endpoint_and_allows_loopback_http():
    with pytest.raises(ValueError, match="HTTPS"):
        agent.ChatModel("test-key", "test-model", "http://example.com/v1")
    with pytest.raises(ValueError, match=r"HTTP\(S\)"):
        agent.ChatModel("test-key", "test-model", "ftp://example.com/v1")
    assert agent.ChatModel("test-key", "test-model", "http://localhost:8080/v1").url == (
        "http://localhost:8080/v1/chat/completions")


@pytest.mark.parametrize("timeout", [0, -1, True, "60"])
def test_chat_model_rejects_invalid_request_timeout(timeout):
    with pytest.raises(ValueError, match="超时必须是正数"):
        agent.ChatModel("test-key", "test-model", request_timeout=timeout)


def test_chat_model_turns_http_errors_into_runtime_errors():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            self.send_response(401)
            self.end_headers()

    with local_server(Handler) as server:
        model = agent.ChatModel("bad-key", "test-model",
                                f"http://127.0.0.1:{server.server_port}/v1")
        with pytest.raises(RuntimeError, match="HTTP 401"):
            model([], [])


def test_chat_model_transport_timeout_is_bounded_and_server_is_released():
    handler_started = threading.Event()
    release_handler = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            handler_started.set()
            release_handler.wait(timeout=2)
            try:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{}')
            except BrokenPipeError:
                pass

    with local_server(Handler) as server:
        model = agent.ChatModel("test-key", "test-model",
                                f"http://127.0.0.1:{server.server_port}/v1",
                                request_timeout=0.05)
        try:
            with pytest.raises(RuntimeError, match="连接失败或超时"):
                model([], [])
            assert handler_started.wait(timeout=1)
        finally:
            release_handler.set()


def test_chat_model_rejects_redirect_without_contacting_target():
    target_requests = []

    class TargetHandler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _record(self):
            target_requests.append(dict(self.headers.items()))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"choices": [{
                "finish_reason": "stop", "message": reply(content="redirected")
            }]}).encode())

        do_GET = _record
        do_POST = _record

    with local_server(TargetHandler) as target_server:
        target_url = f"http://127.0.0.1:{target_server.server_port}/v1/chat/completions"

        class RedirectHandler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(302)
                self.send_header("Location", target_url)
                self.end_headers()

        with local_server(RedirectHandler) as redirect_server:
            model = agent.ChatModel("redirect-secret", "test-model",
                                    f"http://127.0.0.1:{redirect_server.server_port}/v1")
            with pytest.raises(RuntimeError, match="拒绝重定向.*302"):
                model([], [])

    assert target_requests == []


@pytest.mark.parametrize("body", [
    b"{",
    b"{}",
    b'{"choices": []}',
    b'{"choices": "not-a-list"}',
    b'{"choices": [null]}',
    b'{"choices": [{"finish_reason": "stop", "message": {"role": "tool"}}]}',
])
def test_chat_model_rejects_malformed_json_and_response_shapes(body):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

    with local_server(Handler) as server:
        model = agent.ChatModel("test-key", "test-model",
                                f"http://127.0.0.1:{server.server_port}/v1")
        with pytest.raises(RuntimeError, match="无法识别的 Chat Completions 响应"):
            model([], [])


@pytest.mark.parametrize(("name", "arguments"), [
    ("list_files", []),
    ("list_files", {"path": 42}),
    ("list_files", {"path": ".", "extra": "oops"}),
    ("write_file", {"path": "value.txt", "content": 42}),
    ("run_command", {"argv": []}),
    ("run_command", {"argv": [sys.executable, 42]}),
    ("missing_tool", {}),
])
def test_invalid_arguments_are_observations(tmp_path, name, arguments):
    assert agent.Workspace(tmp_path).execute(call(name, arguments)).startswith("TOOL_ERROR")
