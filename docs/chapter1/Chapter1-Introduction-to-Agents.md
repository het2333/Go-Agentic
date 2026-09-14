<div align="right">
  <a href="./第一章%20初识智能体.md">中文</a> | English
</div>

# Chapter 1: Introducing Agentic AI

<figure class="course-hero">
  <img src="../assets/visuals/chapter-01.webp" alt="A decision core exchanges signals and actions across a transparent agent-environment boundary." width="1536" height="864" loading="lazy" decoding="async">
  <figcaption><em>An agent becomes meaningful through a controlled boundary with its environment.</em></figcaption>
</figure>

## Opening Case: How Does an Agent Know the Repair Is Real?

The user supplies one goal: “Run `check_hello.py`, diagnose the failure, change only `hello.py`, and verify again.” The initial function returns a username unchanged, while the check requires surrounding whitespace to be removed. A single-file coding agent receives a workspace and four controlled tools—not a packet containing the answer. New evidence drives the trace:

| Turn | Model choice | What the harness executes | New evidence |
| --- | --- | --- | --- |
| 1 | Run the check | `python3 check_hello.py` | Nonzero exit and a failed assertion |
| 2 | Read the relevant file | `read_file("hello.py")` | Finds `return username` |
| 3 | Write the smallest repair | Change it to `return username.strip()` | The file changed, but correctness is not yet proven |
| 4 | Run the check again | `python3 check_hello.py` | Zero exit; all four cases pass |
| 5 | Return the final explanation | Stop the loop | The answer cites the fresh verification result |

The model never touches the file or terminal directly. It emits structured tool calls; the Python harness validates arguments, performs side effects, and appends each observation to `messages`. Nor does the code hard-wire “read, edit, test.” The model chooses the next step from current evidence, while the check result determines whether the task may finish.

- [Run the single-file native coding agent](https://github.com/het2333/Go-Agentic/blob/main/code/go-agentic/01-minimal-loop/CODING_AGENT.md): connect a real tool-calling model and complete the same task in a temporary exercise directory.
- [Inspect the complete `coding_agent.py`](https://github.com/het2333/Go-Agentic/blob/main/code/go-agentic/01-minimal-loop/coding_agent.py): read `run_agent()` first, then the model, workspace, and tool boundaries.

No API key is required to begin. Section 1.4 supplies a deterministic offline version of the same class of failure so that you can inspect the loop and evidence first. [Appendix C](../appendices/Appendix-C-Labs-and-Troubleshooting.md) then turns this minimal agent into a progressive lab covering tools, context, evaluation, and a production runtime.

This case exposes the boundary between a chat model and an agent: a chat model generates an answer; an agent advances a task in an environment. Both may use the same kind of large language model, but an agent also needs tools, state, a control loop, authority boundaries, and a verifiable stopping condition. This chapter establishes the course vocabulary and dissects a minimal login-failure loop without an API key or network access.

By the end of this chapter, you should be able to:

- distinguish a Model, Agent, Framework, Harness, Runtime, and Environment;
- state an agent's task, authority, and termination boundaries;
- explain the Observation—Action—Verification loop;
- decide when a fixed Workflow or an autonomous Loop fits a task;
- run and interpret the course's deterministic minimal example, then map it to the opening coding-agent trace.

## 1.1 Agent Boundaries

### 1.1.1 Six Concepts That Must Stay Separate

In this course, an **Agent** is a goal-directed system: it chooses an action from the current state, affects an environment through tools, reads the result, and repeats until a success or stopping condition is met. An LLM may be the decision component, but one model call alone is not an agent.

| Concept | Responsibility | What it does not do |
| --- | --- | --- |
| Model | Generates text or a structured decision from input messages | Does not read files or execute commands by itself |
| Agent | Chooses the next step toward a goal and adapts to observations | Is not the complete software system that hosts it |
| Framework | Supplies code abstractions for building agents | Does not define success for a particular task |
| Harness | Assembles the model, tools, context, loop, and safety controls | Does not choose the content of every step for the model |
| Runtime | Keeps the harness running and manages sessions, processes, and resources | Is not the external world of the task |
| Environment | The observable and changeable files, terminal, browser, APIs, or business systems | Does not reason |

A **Tool** is a controlled interface through which the agent crosses a system boundary. Reading a file, querying a database, and running a test are tool calls. A model statement such as “I fixed it” is only text until the environment changes and returns evidence.

### 1.1.2 Four Kinds of Boundary

A controllable task defines at least four boundaries:

1. **Task boundary**: the goal and what is outside this task;
2. **Environment boundary**: which systems the agent can observe and which state remains unknown;
3. **Authority boundary**: available tools and actions that require human approval;
4. **Termination boundary**: evidence of success and limits on steps, cost, time, or errors.

“Find why login fails, fix it, and run the relevant tests” states a goal, but it still needs an allowed directory, the relevant test command, a maximum number of attempts, and success evidence. Autonomy is the room to choose within boundaries, not unlimited authority.

## 1.2 The Minimal Agent Loop

### 1.2.1 Environment and Observation

An agent cannot see the complete environment at the start. It obtains partial information through tools: command exit codes, test output, file excerpts, search results, or API responses. The harness wraps each result as an **Observation** and adds it to the next decision context.

An observation must preserve facts that can change the next decision. For a failed test, the test name, error type, relevant path, and exit status are usually more useful than the complete log. Truncation, summarization, and formatting must never turn failure into success.

### 1.2.2 Action, Verification, and Termination

An **Action** is a structured tool request with a name and arguments. The harness validates it, executes the corresponding tool, and converts the result into a new observation. **Verification** uses independent evidence to test whether the goal is met. “The file was edited” proves an action occurred; only the relevant passing test proves the goal in this example.


A minimal loop can be written as:

```python
observations = []
for step in range(1, max_steps + 1):
    decision = policy.decide(task, tuple(observations))
    if isinstance(decision, FinalAnswer):
        return finish_only_if_verified(decision, observations)
    observations.append(dispatch_and_observe(decision))
return stop_at_step_limit(observations)
```

This loop has three essential properties:

- every iteration executes at most one recordable action;
- tool errors become observations instead of silently destroying control flow;
- the loop stops at the step limit, and a final answer cannot replace verification evidence.

## 1.3 Workflow and Autonomous Loop

### 1.3.1 Split Control at the Point of Uncertainty

Start from the evidence required at the end. For “publish a patch release,” success means that the candidate passes its required checks, an approval is recorded, the expected artifact is published, and a post-release health check passes. Those conditions reveal which decisions can be fixed in advance and which require interpretation.

| Loop stage | Fixed Workflow responsibility | Autonomous Loop responsibility |
| --- | --- | --- |
| Observe | Collect named CI checks, artifact digest, approval state, and deployment health | Inspect an unexpected failure using only permitted logs, files, and tests |
| Decide | Follow predefined branches for pass, fail, approval, publish, and rollback | Choose the next diagnostic probe from the latest evidence |
| Act | Run approved build, publish, or rollback operations | Read, search, test, or prepare a bounded repair inside the workspace |
| Verify | Compare recorded checks and deployed state with the release contract | Produce evidence for the Workflow; never waive the release gate |

Suppose the artifact checksum passes while a smoke test fails on an unfamiliar route. The Workflow stops before publication and hands the failure Observation to the Agent. The Agent decides to inspect the failing request, reads its bounded log, and observes a stale environment-key reference. It repairs the reference and reruns the smoke test. Only when that new Observation is a pass does the Workflow request approval, publish the artifact, and verify service health. The Agent resolves uncertainty; the Workflow retains release authority.

### 1.3.2 Test the Choices, Not a Particular Model's Wording

The autonomous part can still be deterministic in a Harness test. A fake policy can map `smoke_failed` to `read_log`, `stale_key_found` to `read_file`, `repair_ready` to an edit, and `candidate_updated` to `run_smoke`. The Fixture controls every returned Observation, including a Tool error and a failed Verification. Assertions then cover the selected Action, the evidence passed into the next decision, the approval boundary, and the step budget.

A real model may phrase its rationale differently or choose another permitted probe. The contract remains testable because authority, observations, Verification, and Termination belong to the Harness.

## 1.4 Five-Minute Practice: Diagnose a Login Failure

### 1.4.1 Run the Offline Fixture

The chapter code is in `code/go-agentic/01-minimal-loop/`. It uses only the Python standard library; its pytest tests do not access the network or environment variables.

```bash
python3 -m pytest code/go-agentic/01-minimal-loop/test_agent.py -q
```

The fixture simulates a login defect in which a username is not stripped of surrounding whitespace. It is not a reimplementation of the Pi API. It is a **Pi-style** teaching harness: the model policy chooses only the next step, while the harness owns tool execution, observation recording, error handling, verification, and termination. Pi is the course's sole continuous practical mainline; Chapter 7 enters the real Pi runtime.

### 1.4.2 Typed Tool Protocol

The policy cannot mutate the environment directly. It can return only two decision forms:

```python
ToolCall(
    name="read_file",
    arguments={"path": "src/auth/login.py"},
)

FinalAnswer("Login normalization fixed; the focused test passes.")
```

The three tool contracts are:

| Tool | Required arguments | Successful observation | Possible error |
| --- | --- | --- | --- |
| `run_tests` | `target` | `PASS ...` or `FAIL ...`; only PASS is marked verified | Unknown test target |
| `read_file` | `path` | File contents | `FileNotFoundError` |
| `replace_text` | `path`, `old`, `new` | `UPDATED ...` | Missing file or unmatched old text |

A tool exception becomes `TOOL_ERROR <type>: <message>`. The policy can recover on the next iteration, and tests and audit logs can see the failure.

### 1.4.3 Trace from Failure to Evidence

The deterministic policy produces this trace:

| Step | Action | Observation | Meaning |
| --- | --- | --- | --- |
| 1 | `run_tests(tests/test_login.py)` | FAIL pointing to `src/auth/login.py` | Read the real failure first |
| 2 | `read_file(src/auth/login.py)` | Returns the defective implementation | Inspect the relevant file |
| 3 | `replace_text(...strip())` | UPDATED | Take the smallest action |
| 4 | `run_tests(tests/test_login.py)` | PASS with `verified=True` | Verify with environment evidence |
| 5 | `FinalAnswer(...)` | Stop | Complete only after a verified observation |

The tests cover two failure paths as well: a missing file becomes a recoverable observation, and a policy that never finishes stops with status `max_steps`. The fixture's exact sequence—“run the focused test → read the relevant file → replace the defective text → rerun the focused test → stop from the verified result”—is therefore executable and assertable, rather than merely descriptive.

## 1.5 Minimal Agent Design Checklist

Before adding memory, multiple agents, or elaborate planning, answer:

- Are the goal, allowed scope, and success evidence explicit?
- Does each tool define a name, argument schema, return value, and error semantics?
- Does each observation contain the environment facts needed for the next decision?
- Is verification independent from the model's own claim?
- Are there limits for steps, time, cost, and human approval?
- Can the complete trace be saved and key failures replayed?

If these questions have no answers, adding more model reasoning usually amplifies uncertainty.

## 1.6 Chapter Summary

- A Model generates decisions; an Agent uses tools under a Harness to interact with an Environment; a Runtime hosts continued execution.
- The minimal semantics are Observation—Action—Verification: observe the environment, take a structured action, and verify with new evidence.
- A Workflow fixes the path in advance; an autonomous Loop chooses a path at runtime. Production systems often combine them.
- Tool errors must be observable, success needs evidence, and loops need termination budgets.
- The offline login fixture proves the complete path from failure through inspection and modification to verification.

## Exercises

1. For the task “organize the Downloads folder,” write the task, environment, authority, and termination boundaries. Identify one action that needs human approval.
2. Split “generate a sales report every day at 09:00” into a fixed Workflow and an autonomous Loop. State who owns each decision.
3. Change the minimal fixture policy so that it first reads a missing file and then recovers to the correct path. Predict the trace, then run the tests.
4. Design an error result for a timed-out `run_tests` process. State which fields the Observation must preserve and when the agent should retry or stop.

## Mastery Standard

You meet this chapter's standard when you can draw an agent's boundaries and loop without vague phrases such as “it figures things out”; identify the executor of every action, the source of every observation, the success evidence, and the stopping condition; and independently run and explain all four fixture tests.

## Evidence Map

The chapter's loop draws on three kinds of evidence:

| Loop concern | Source used | What the source supports here |
| --- | --- | --- |
| Observe and act in an environment | Russell and Norvig, 4th edition, [AIMA agent resources](https://aima.cs.berkeley.edu/) | The relationship among percepts, actions, environments, and goal-directed behavior |
| Decide between observations | Yao et al. (2022), [arXiv record 2210.03629](https://arxiv.org/abs/2210.03629) | Alternating language-based reasoning with externally executed actions |
| Verify and continue under a harness | Pi maintainers, [coding-agent documentation](https://github.com/earendil-works/pi/tree/main/packages/coding-agent) | The concrete tool, session, and extension boundaries used by the executable course path |
