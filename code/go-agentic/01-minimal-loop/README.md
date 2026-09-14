# Deterministic Minimal Agent Loop

This fixture supports Chapters 1–3 of Go Agentic. It demonstrates the smallest useful contract among a policy, a harness, tools, and an environment without calling a model API.

**Want a real model and real files?** See [单文件原生 Coding Agent（中文运行与阅读指南）](./CODING_AGENT.md). Start with the 266-line `coding_agent_beginner.py`, then compare it with the 444-line hardened `coding_agent.py`. Both use only the standard library and add a Chat Completions tool loop, file tools, and opt-in command execution alongside this deterministic fixture.

## Run

```bash
python3 -m pytest code/go-agentic/01-minimal-loop/test_agent.py -q
```

The production fixture uses only the Python standard library. The tests need pytest. No API key, network connection, or external service is used.

## Files

- `agent.py` defines typed decisions and observations, the bounded loop, a deterministic fake model policy, and an in-memory login workspace.
- `test_agent.py` proves the successful trace, conversion of tool exceptions into observations, and maximum-step termination.
- `coding_agent_beginner.py` keeps a real model-and-tools loop within 300 lines for a first code reading.
- `test_coding_agent_beginner.py` runs that loop against real temporary files and a real Python check process.
- `coding_agent.py` and `test_coding_agent.py` add stricter production-oriented boundaries and broader failure coverage.

## Canonical Trace

```text
run_tests("tests/test_login.py")
  → FAIL ... at src/auth/login.py:2
read_file("src/auth/login.py")
  → defective source
replace_text(..., "return username.strip()")
  → UPDATED
run_tests("tests/test_login.py")
  → PASS, verified=True
FinalAnswer(...)
  → completed
```

The fake policy may request an action, but only the harness dispatches a tool. A tool exception becomes a `TOOL_ERROR` observation. A final answer is marked `completed` only when the immediately preceding observation is verified; otherwise it is `unverified`. A policy that does not finish within `max_steps` returns `max_steps`.

This is Pi-style teaching code, not an implementation of Pi's API. Pi becomes the course's real runtime mainline in Chapter 7.
