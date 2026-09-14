> This chapter is part of the bilingual Go Agentic course. For project attribution and third-party notices, see [Sources and Acknowledgements](../Sources-and-Acknowledgements.md).

# Chapter 7: Modern Agent Runtimes: Pi as the Mainline

<figure class="course-hero">
  <img src="../assets/visuals/chapter-07.webp" alt="A layered control citadel coordinates scheduling, tools, state, and telemetry around execution." width="1536" height="864" loading="lazy" decoding="async">
  <figcaption><em>A custom runtime needs a control plane that governs every execution boundary.</em></figcaption>
</figure>

The first six chapters built a vocabulary for Tasks, Environments, Tools, loops, verification, and lifecycle decisions. This chapter puts those ideas inside one real coding harness: [Pi](https://pi.dev/). Pi owns the executable learning path because its small default surface makes the control loop visible. DeepSeek Harness and Hermes appear only at the end as architectural comparisons.

By the end of the chapter, you should be able to run one safe Pi session, explain every Tool transition in a login repair, branch and resume a session, distinguish compaction from history deletion, and choose among Skills, Extensions, and Packages.

## 7.1 Pi Is a Small Harness Around a Large Responsibility

Pi describes itself as a minimal terminal coding harness. Its default Agent surface is easy to draw:

```text
task + project instructions + session history
                    ↓
             model decision
                    ↓
          read / write / edit / bash
                    ↓
          observation returned to model
                    ↓
        continue, compact, or terminate
```

The model proposes Tool calls; Pi owns session assembly, Tool execution, streaming, interruption, and persistence. The operating system and project remain the Environment. A test result or file read is an Observation. A model sentence such as “the bug is fixed” is only a claim until an Environment check verifies it.

Pi can run interactively, print or JSON output, RPC, or as an embedded SDK. This chapter uses interactive mode because it exposes the trace directly.

### 7.1.1 The four default Tools

| Tool | Capability | Main risk | Good evidence |
| --- | --- | --- | --- |
| `read` | Inspect a file or image | Reading irrelevant or sensitive data | Exact path and bounded content |
| `write` | Create or replace a file | Overwriting valid work | Diff plus a downstream check |
| `edit` | Replace a precise text region | Editing the wrong occurrence | Small diff plus focused test |
| `bash` | Run a command | Arbitrary side effects | Exit code and bounded output |

Four Tools are enough for a complete coding loop because `bash` can inspect the repository and run verification, while `read`, `write`, and `edit` make file changes explicit. More Tools may improve ergonomics, but they also enlarge the schema, authority, and failure surface.

### 7.1.2 The invariant inside the UI

Pi may stream reasoning, collapse Tool output, or accept steering messages, but the engineering invariant remains:

```python
while not terminated:
    decision = model(context, tools)
    if decision.is_tool_call:
        observation = environment.execute(decision)
        context.append(observation)
    else:
        terminate_with(decision)
```

Real implementations must additionally validate arguments, control authority, handle Tool failures, reserve output tokens, and prevent an unverified loop from running forever.

## 7.2 Install and Authenticate with a Deliberate Trust Boundary

The official Pi README currently recommends:

```bash
npm install -g --ignore-scripts @earendil-works/pi-coding-agent@0.85.1
pi
```

> **Version contract (verified 2026-09-13):** `npm view @earendil-works/pi-coding-agent name version dist-tags repository --json` returned package `@earendil-works/pi-coding-agent`, version and `latest` both `0.85.1`, and repository `earendil-works/pi`. Copyable course commands pin that exact version; recheck the official documentation and npm registry before real adoption.

`--ignore-scripts` disables dependency lifecycle scripts; Pi states that normal npm installation does not require them. The official installer is an alternative:

```bash
curl -fsSL https://pi.dev/install.sh | sh
```

An installer fetched into a shell can execute code immediately. In controlled environments, download and inspect it first, pin an approved version, and record the installed version. Review the current [official installation instructions](https://github.com/earendil-works/pi/tree/main/packages/coding-agent#quick-start) before use because package names and setup details can change.

Pi can authenticate through `/login` for a supported subscription or through provider API-key configuration. Authentication is an external prerequisite for the live Pi path; the deterministic course fixture in Section 7.6 requires neither a network connection nor an API key.

### 7.2.1 Start in a safe workspace

For a first run:

1. Use a small disposable Git repository with no production secrets.
2. Inspect `git status` and make a recoverable baseline commit.
3. Grant only the credentials and directories required by the task.
4. Read project instructions and review commands before allowing high-impact actions.
5. Treat third-party Extensions and Packages as executable code.

Pi asks for a project trust decision before loading untrusted project-local settings, resources, extensions, and package-managed extensions. Context files can still influence the model, so trust is one control among several; it does not make repository content safe.

## 7.3 One Complete Login-Fix Trajectory

Use the course’s recurring defect:

```python
def normalize_username(username: str) -> str:
    return username  # should remove surrounding whitespace
```

The task contract is:

```text
Find and fix the login normalization failure.
Change only the implicated code.
Finish only after the focused test passes.
```

### 7.3.1 Observe before editing

A reliable Pi trajectory begins with Environment evidence:

```text
1. bash  → run the focused login test
2. read  → inspect the failing test and src/auth/login.py
3. edit  → replace `return username` with `return username.strip()`
4. bash  → rerun the focused test
5. stop  → report the diff and passing test
```

The corresponding state flow is:

```text
TASK
  ↓
OBSERVE failure ──→ INSPECT source ──→ EDIT minimal cause
                                              ↓
                                      VALIDATE focused test
                                         │           │
                                      fail          pass
                                         │           │
                                         └─ retry    └─ complete
```

The first test run prevents speculative editing. The source read grounds the change. The final test is independent evidence. If the test still fails, its new output becomes the next Observation; the Agent must adapt rather than repeat the same edit.

### 7.3.2 Give Pi an outcome, constraints, and a verifier

A useful live prompt is:

```text
Fix the failing username-normalization login test in this repository.
First run the narrowest relevant test and inspect the implicated code.
Keep the edit minimal, preserve unrelated work, rerun the focused test,
and finish with the changed path and exact verification result.
```

The prompt does not prescribe every command. It defines the outcome, authority boundary, and completion evidence while leaving the loop room to respond to observations.

## 7.4 Sessions Turn a Trace into Recoverable State

Pi sessions auto-save as JSONL and form a tree: entries have identifiers and parent links. A session is therefore more than a flat transcript.

| Operation | Meaning | Use it when |
| --- | --- | --- |
| `/resume` or `pi -r` | Open a prior session | Continue interrupted work |
| `pi -c` | Continue the most recent session | Re-enter the current task quickly |
| `/tree` | Move to a prior point in the same session tree | Inspect or continue another branch |
| `/fork` | Create a new session from a prior user message | Try a changed task without altering the source session |
| `/clone` | Copy the active branch into a new session | Preserve the full current path before experimentation |

Branching is useful when two hypotheses require different edits. Each branch should carry its own verification evidence; a passing result on one branch does not validate another.

### 7.4.1 Compaction is a lossy handoff

Long sessions eventually approach the model’s context window. Pi can compact automatically or through `/compact`: older messages are summarized while recent messages remain. The complete session history remains in the JSONL file and can be revisited through the tree, but the model receives the compacted representation on later turns.

Compaction must preserve the state needed to continue:

```text
goal
completed work
decisions and constraints
unresolved failures
relevant paths and evidence IDs
next action
```

It should remove repeated searches, superseded hypotheses, and bulky Tool output. Because summarization is lossy, inspect the compacted state after a critical decision and keep durable project facts in versioned files or external systems. Chapter 9 develops this contract in detail.

## 7.5 Skills, Extensions, and Packages Change Different Layers

Pi keeps its core small and offers three different customization boundaries.

| Mechanism | What it changes | Typical use |
| --- | --- | --- |
| Skill | Instructions and task resources loaded on demand | A review checklist or deployment procedure |
| Extension | Runtime behavior implemented in TypeScript | A Tool, command, permission gate, UI component, or compaction policy |
| Pi Package | Distribution bundle for Extensions, Skills, prompts, and themes | Share a versioned team workflow through npm or Git |

Use a Skill when the Agent needs a repeatable method. Use an Extension when execution semantics must change. Use a Package when those assets need installation, versioning, and reuse. A Package may contain executable Extensions, so installation is a supply-chain decision.

Progressive disclosure keeps context lean: Pi initially exposes Skill names and descriptions, then loads full instructions only when a Skill applies. This is the same context principle Chapter 9 applies to files and evidence.

## 7.6 The Executable Learning Path

First run the deterministic login fixture from the repository root:

```bash
python3 -m pytest code/go-agentic/01-minimal-loop/test_agent.py -q
```

It uses a fake policy and in-memory workspace. No provider, API key, package installation, network call, or real file mutation is required. Inspect `agent.py` and map its `run_tests → read_file → replace_text → run_tests` trace to Pi’s `bash → read → edit → bash` path.

Then, if you have a configured provider and a disposable repository, repeat the task in Pi. Compare:

- the Tool order;
- the first failed Observation;
- the exact edit;
- the final verification evidence;
- the session state needed to resume.

The deterministic fixture teaches the contract. The live run shows how a model navigates uncertainty inside that contract.

## 7.7 Architectural Comparison: DeepSeek Harness

Verified against its official repository on September 13, 2026, [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) describes an “everything is a plugin” architecture built on Cordis. Model adapters, Tools, context contributors, approval policies, persistence, sandboxes, and even Agent-loop behavior can meet at plugin boundaries. This is useful when the main design problem is composition and replacement of runtime services.

Pi gives this course a smaller executable surface; DeepSeek Harness shows what happens when the Harness itself becomes a plugin graph. Its official README labels the project a developer preview with expected compatibility-breaking changes and links a separate safety notice. Treat its architecture as a dated comparison and recheck official documentation before adoption.

## 7.8 Architectural Comparison: Hermes Agent

Verified against official documentation on September 13, 2026, [Hermes Agent](https://github.com/NousResearch/hermes-agent) combines a terminal Agent with persistent memory, session search, Skills, scheduled tasks, messaging gateways, MCP integrations, and isolated subagents. It is a useful comparison when tasks must continue across sessions, platforms, and scheduled wakeups.

Pi’s session tree and extensibility remain the chapter’s learning path. Hermes illustrates the additional runtime services needed around a long-lived Agent. Chapter 8 returns briefly to its memory design; feature and command claims should be rechecked in the [Hermes documentation](https://hermes-agent.nousresearch.com/docs/) before deployment.

## 7.9 Chapter Summary

- Pi makes the Observation—Action—Verification loop visible through four default Tools.
- Safe installation and project trust reduce supply-chain and workspace risk, but do not replace least privilege and review.
- A login repair is complete only after a focused Environment check passes.
- Sessions preserve the trace; branching preserves alternatives; compaction creates a lossy continuation state.
- Skills teach methods, Extensions change runtime behavior, and Packages distribute both.
- DeepSeek Harness and Hermes illustrate broader composition and long-running-runtime concerns without displacing the Pi workflow.

## Exercises

1. For the login trajectory, label each item as Task, Action, Observation, Validation, or Termination.
2. Explain why a successful `edit` result does not prove the login defect is fixed.
3. Design two session branches for competing login hypotheses and state what evidence selects the winner.
4. Write a compaction record that could resume the task after the first post-edit test still fails.
5. Classify each customization as a Skill, Extension, or Package: review checklist, custom database Tool, shared team bundle.
6. Compare Pi with either DeepSeek Harness or Hermes using one architectural boundary rather than a feature-count table.

## Mastery Standard

You have mastered this chapter when you can safely start a Pi task, narrate the `read/write/edit/bash` loop, recover or branch a session, audit a compaction handoff, and finish only with Environment evidence. You should also be able to explain why a Skill, an Extension, and a Package solve different problems.

## Primary Sources

1. [Pi official site and documentation](https://pi.dev/docs/latest)
2. [Pi Coding Agent official README](https://github.com/earendil-works/pi/tree/main/packages/coding-agent)
3. [Pi session format](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/session-format.md)
4. [Pi compaction internals](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/compaction.md)
5. [Pi Extensions documentation](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md)
6. [DeepSeek Harness official repository](https://github.com/deepseek-ai/deepseek-harness)
7. [DeepSeek Harness architecture](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md)
8. [DeepSeek Harness safety notice](https://github.com/deepseek-ai/deepseek-harness/blob/master/SAFETY.md)
9. [Hermes Agent official repository](https://github.com/NousResearch/hermes-agent)
10. [Hermes Agent official documentation](https://hermes-agent.nousresearch.com/docs/)
