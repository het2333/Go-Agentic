<div align="right">
  <a href="./第三章%20大语言模型基础.md">中文</a> | English
</div>

# Chapter 3: LLM and Systems Foundations for Agents

<figure class="course-hero">
  <img src="./assets/visuals/chapter-03.webp" alt="Abstract token particles flow through attention and reasoning machinery into a concrete tool action." width="1536" height="864" loading="lazy" decoding="async">
  <figcaption><em>Language-model representations become useful when the runtime converts them into controlled actions.</em></figcaption>
</figure>

Building an agent does not require mastering all pretraining mathematics first. It does require knowing why model output varies, how messages enter context, how tool calls cross provider boundaries, and how context, caching, latency, and cost constrain a loop. This chapter keeps only the foundations that directly explain agent behavior.

By the end of this chapter, you should be able to:

- explain model output using Tokens, next-token prediction, Attention, and decoding;
- organize System, User, Assistant, and Tool messages;
- design and validate Tool Schemas and structured outputs;
- calculate a context budget and correctly interpret a Prompt Cache;
- locate observable model, protocol, and loop failures.

## 3.1 Just Enough Generation Theory

### 3.1.1 Tokens and Next-Token Prediction

A language model first encodes text as a sequence of **Tokens**. A token can be a character, part of a word, punctuation, or whitespace. Token count is not character or word count. Code, JSON, paths, and mixed Chinese-English text tokenize differently, so estimate context with the target model's tokenizer or API usage rather than by eye.

Given a sequence (x_{1:t}), an autoregressive model estimates the conditional probability of the next token:

```text
P(x_(t+1) | x_1, x_2, ..., x_t)
```

It repeatedly samples or selects a next token until it emits a stop marker or reaches an output limit. The model generates a conditionally likely continuation; it does not automatically query environment facts. This is why fluent text can still disagree with a repository, database, or the current time.

### 3.1.2 Transformer and Attention

A Transformer maps tokens to vectors and computes context-dependent representations through layers of Attention and feed-forward networks. For agent engineering, retain three facts:

1. **Order needs representation**: positional encoding lets a model distinguish token locations;
2. **Attention is weighted reading**: each position aggregates relevant information from other context positions;
3. **Computation has a window**: the model can use only content actually supplied in this request and not truncated.

Attention does not guarantee that the model finds the critical line. An error can be buried in a long log, conflicting instructions can compete, and facts outside the window are invisible. The harness still needs to select context, highlight evidence, and verify results.

### 3.1.3 Decoding Parameters Change the Trace

The model converts logits into token probabilities. Common decoding controls include:

- **temperature**: changes distribution sharpness; a lower value usually reduces variation but does not guarantee identical requests produce identical output;
- **top-p**: samples only from the candidate set whose cumulative probability reaches the threshold;
- **max output tokens**: limits response length; a low limit can truncate JSON or tool arguments;
- **stop condition**: ends generation at a specified sequence or protocol event.

Deterministic tests should not depend on “temperature=0 is always identical.” Provider implementations, model versions, and server-side updates can change results. Chapter 1 uses a Fake Policy specifically to separate harness tests from model variation.

## 3.2 Messages and the Provider Boundary

### 3.2.1 A Message Sequence Is the Model's Working Input

One agent model request usually contains these logical elements:

| Message | Purpose | Example |
| --- | --- | --- |
| System / Developer | Defines role, rules, and tool constraints | “Run the relevant tests after editing” |
| User | Supplies a goal and new information | “Fix the login failure” |
| Assistant | Stores a prior answer or tool request | `run_tests(...)` |
| Tool | Stores an observation returned by the host | `FAIL ... src/auth/login.py` |

The model has no automatically durable task state. Multi-turn interaction depends on the application resending these elements or a server-side session mechanism reconstructing them. Facts that must persist reliably belong in runtime state, files, or a database rather than only in the model's prose.

### 3.2.2 Define an Internal Protocol, Then Adapt Providers

Model APIs differ in role names, content blocks, tool-call IDs, parallel calls, image inputs, supported schema subsets, and error responses. A portable harness should define internal types first and let a Provider Adapter translate in both directions.


Normalization must preserve important information. Stop reasons, usage, cache hits, tool-call IDs, rate limits, and safety refusals should remain observable fields. Switching providers is a boundary migration that needs contract tests, rather than merely changing a model name.

## 3.3 Tool Schemas and Structured Outputs

### 3.3.1 A Schema Describes Available Actions

A Tool Schema places a tool's name, purpose, and argument constraints in model context. This JSON Schema matches the Chapter 1 `read_file` action:

```python
READ_FILE_SCHEMA = {
    "name": "read_file",
    "description": "Read one UTF-8 text file from the allowed workspace.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Workspace-relative file path.",
            }
        },
        "required": ["path"],
        "additionalProperties": False,
    },
}
```

Names should be stable, descriptions should state when to use a tool, and arguments should be narrow. Disguising an arbitrary shell string as “one tool” expands authority and the test space. A schema constrains structure only; the harness must still check path boundaries, user authority, and operation safety before execution.

### 3.3.2 Follow a Tool Request Through Four Gates

Suppose the current Observation says that order `A-18` has an approved refund limit of 87.00 CNY. The model then decides to request this structurally valid Action:

```json
{
  "tool": "issue_refund",
  "arguments": {
    "order_id": "A-18",
    "amount_minor": 870000,
    "currency": "CNY"
  }
}
```

JSON parsing answers whether the request can be read. Schema validation checks the required fields, types, and currency enum. Neither check notices that `870000` minor units exceed the observed authorization by a factor of one hundred. Before execution, the Harness must compare the request with order state, amount limits, idempotency rules, and caller authority. It rejects this candidate Action and returns a decision-ready Observation:

```json
{
  "ok": false,
  "error_type": "AMOUNT_EXCEEDS_AUTHORIZATION",
  "authorized_minor": 8700,
  "requested_minor": 870000,
  "retryable": true,
  "verified": false
}
```

The next decision may correct the amount, but execution is still not proof of success. After an authorized refund call returns a transaction ID, Verification must reread the order or payment record and confirm the amount, currency, order ID, and transaction status. The four gates are therefore: observe the governing facts, decide on a typed request, validate and act within authority, then verify the external postcondition.

Structured Outputs strengthen the Model-to-Harness boundary. The Harness still owns semantic checks and execution, and only environment evidence can set `verified=true`.

## 3.4 Context Budget and Caching

### 3.4.1 Budget Input and Output Together

Approximate one request's context use as:

```text
T_total =
  T_instructions + T_tool_schemas + T_history
  + T_tool_results + T_user_input + T_reserved_output
```

`T_total` must fit the selected model and API limit. In practice, reserve headroom for output, growing tool results, and provider counting differences.

| Content | Retention rule | Common treatment |
| --- | --- | --- |
| Task boundaries and safety rules | Always visible | Stable prefix |
| Current plan and recent observations | High priority | Original text or short structure |
| Large tool outputs | Keep decision evidence only | Extract relevant ranges and retain a raw reference |
| Completed old trace | Keep conclusions and open risks | Compaction |
| Files that can be reread | Include on demand | JIT Context |

A larger window does not mean more content is always better. Context engineering supplies enough evidence at the right time while keeping omissions and compression traceable.

### 3.4.2 A Prompt Cache Is a Compute Optimization

Providers can cache repeated input prefixes to reduce processing latency or billed input on later requests. To improve hits, place stable system instructions and tool schemas first, place changing observations later, and inspect cache usage returned by the API.

Caching has three boundaries:

- hit conditions, retention, and pricing depend on the provider;
- changing any content in the prefix can reduce hits;
- a cache does not store task facts for you or enlarge the Context Window.

Prompt Cache, session state, long-term memory, and Compaction are four different concepts.

## 3.5 Latency, Cost, and Provider Choice

### 3.5.1 Measure the Whole Loop's Critical Path

Agent task latency includes more than the first model response:

```text
L_task ≈ Σ L_model_calls + Σ L_tool_calls + L_queue + L_retries
```

Serial tool calls accumulate latency; only reads proven independent should run in parallel. Removing irrelevant context, limiting tool output, avoiding repeated failures, and terminating early often matter more than faster decoding in one response.

If a provider charges by token, estimate model cost as follows. Let `T_input` be total input tokens and `T_cached` the cached subset, with the guard `0 ≤ T_cached ≤ T_input`:

```text
C_model ≈ (T_input - T_cached) × P_input
        + T_cached × P_cached
        + T_output × P_output
```

Actual prices, cache discounts, and reasoning charges come from the official price page and usage fields at call time. Also record search, browser, database, and human approval costs. Evaluate “total cost per verified task,” rather than only price per million tokens.

### 3.5.2 The Provider Boundary Must Be Observable

A Provider Adapter should expose at least:

- model identifier and traceable version information;
- request ID, stop reason, and error type;
- input, output, and cached-token usage;
- original Tool Call IDs and normalized results;
- latency, retry count, rate limits, and refusal information.

Choose models with task-set tests: tool-call correctness, long-context behavior, latency, total cost, and availability. A leaderboard or marketing description cannot replace your own traces and verification results.

## 3.6 Observable Failure Modes

| Symptom | Boundary | Harness response |
| --- | --- | --- |
| JSON cannot parse or lacks a required field | Model / Provider | Record the original stop reason; repair or retry a bounded number of times |
| Tool name does not exist | Model → Harness | Reject dispatch and return the allowlist |
| Arguments are structurally valid but path escapes scope | Harness → Environment | Fail authorization and do not execute |
| Tool times out or returns a partial result | Environment | Mark error type, retryability, and partial evidence |
| Critical failure log was truncated | Context | Keep a raw reference and reread the relevant range |
| The same action repeats | Loop | Detect repetition and stop after the retry budget |
| Model announces success without evidence | Verification | Return `unverified`; verify or stop |
| Tool results cannot be correlated after provider migration | Provider Adapter | Contract-test call IDs and preserve raw responses |

Observability is not “print more logs.” It means the input, output, error, and decision at each boundary can be correlated within one trace.

## 3.7 Chapter Summary

- An LLM generates from token sequences and next-token prediction; Attention uses only information that enters the window.
- Decoding parameters affect the output distribution and cannot replace deterministic harness tests.
- Messages form each request's working input; persistent state belongs in a runtime or external store.
- A Tool Schema constrains structure, while the harness owns semantics, authority, execution, and verification.
- Context Budget, Prompt Cache, Latency, and Cost must be managed across the complete loop.
- Provider differences require an Adapter, contract tests, and observable fields.

## Exercises

1. List every message in the complete Chapter 1 trace: System, User, Assistant Tool Call, and Tool Observation. Mark which content can be compacted.
2. Write a JSON Schema for `replace_text` that requires string fields `path`, `old`, and `new`. Explain two risks the schema cannot prevent.
3. Assume a 32,000-token context limit: fixed instructions and tools use 6,000, history uses 14,000, the latest tool result uses 5,000, and 4,000 is reserved for output. Calculate the remaining headroom and propose one compaction.
4. Design a three-step failure trace containing an invalid Tool Call, a tool timeout, and a model finishing without evidence. Write the observable fields and termination decision for each step.

## Mastery Standard

You meet this chapter's standard when you can derive the messages, tool schema, context use, cache boundary, critical-path latency, and total cost from a real agent trace; locate a failure in the Model, Provider Adapter, Harness, or Environment; and explain why structured output still needs semantic verification.

## Evidence Map for a Model Step

| Stage in the loop | Source used | Claim checked against it |
| --- | --- | --- |
| Encode the observation | Kudo and Richardson (2018), [ACL Anthology record D18-2012](https://aclanthology.org/D18-2012/) | How text is segmented into model input units |
| Decide the next token or action | Vaswani et al. (2017), [arXiv record 1706.03762](https://arxiv.org/abs/1706.03762); Holtzman et al. (2019), [arXiv record 1904.09751](https://arxiv.org/abs/1904.09751) | Attention architecture and the effect of decoding policy on generated traces |
| Express a typed action | [JSON Schema specification](https://json-schema.org/specification); OpenAI [function-calling](https://platform.openai.com/docs/guides/function-calling) and [structured-output](https://platform.openai.com/docs/guides/structured-outputs) guides; Anthropic [tool-use overview](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview) | Structural contracts at the Model-to-Harness boundary |
| Preserve evidence for the next decision | OpenAI [prompt-caching guide](https://platform.openai.com/docs/guides/prompt-caching); Anthropic [context-window guide](https://docs.anthropic.com/en/docs/build-with-claude/context-windows) | Provider-specific cache and context behavior that the Harness must observe |
