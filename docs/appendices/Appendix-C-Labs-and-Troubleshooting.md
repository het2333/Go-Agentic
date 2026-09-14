# Appendix C: Labs and Troubleshooting Index

The labs use the Python standard library and deterministic local data wherever possible. They run on CPU without a model, API, or network. Run the full suite with:

```bash
cd code/go-agentic
python3 -m pytest -q
```

## C.1 Complete Lab Index

| No. | Directory | Core capability | Acceptance focus |
| --- | --- | --- | --- |
| 01 | `01-minimal-loop` | Minimal observe–decide–act loop | State update, termination, step budget |
| 04 | `04-loop-patterns` | ReAct/planned loop patterns | Evidence drives the next action; failures terminate |
| 05 | `05-tools-environments-rag` | Tool and environment boundaries | Schema, permissions, trusted/untrusted separation |
| 06 | `06-lifecycle` | Selection matrix | Compare with constraints/evidence, not popularity |
| 08 | `08-memory-rag` | Memory, multi-query, HyDE, RRF | Write policy, fusion, normalization, regressions |
| 09 | `09-context-loop` | JIT context and compaction | Token budget, structured notes, fidelity |
| 10 | `10-mcp-skills-a2a` | Tool server and protocol boundary | Discovery, validation, error semantics |
| 11 | `11-agentic-rl` | Best-of-N, ToT, MCTS | Search budget, deterministic evaluator, stopping |
| 12 | `12-evaluation-safety` | Evaluators and retrieval metrics | MRR/nDCG/F1, agreement, safety regressions |
| 13 | `13-enterprise-execution-agent` | Enterprise execution | Approval, idempotency, audit, compensation |
| 14 | `14-deep-research-agent` | Deep research | Query decomposition, evidence alignment, citations |
| 15 | `15-multi-agent-system` | Multi-Agent workflow | Handoff contract, acceptance, escalation |
| 17 | `17-transformer-math` | Attention, tokenization, decoding | Mask, numerics, top-k/top-p/constrained output |
| 18 | `18-training-compression` | Training/compression ledger | SFT masks/packing, LoRA, MoE, resources |
| 19 | `19-alignment` | RL and preference objectives | Return/GAE, PPO/DPO/KTO/RLVR boundaries |
| 20 | `20-gpu-topology` | Roofline, MFU, fabric, cost | Units, bottleneck, ring traffic, budget |
| 21 | `21-inference-capacity` | KV-cache capacity | K/V factor, GQA dimensions, maximum batch |
| 22 | `22-distributed-training` | ZeRO/FSDP and parallel plan | Shards, world size, sync, device-hours |
| 23 | `23-agentic-ui` | UI state and replayable stream | Ordering, dedup, approvals, terminal state, cursor |
| 24 | `24-production-runtime` | Production runtime | Retry, circuit breaking, concurrency, recovery, SLO |
| 25 | `25-capstone` | Capstone | Requirements, architecture, evaluation, safety, ops pack |

Run one lab with, for example:

```bash
python3 -m pytest 08-memory-rag -q
python3 -m pytest 23-agentic-ui -q
```

`06-lifecycle/selection_matrix.md` and `25-capstone/README.md` are reviewed artifacts rather than Pytest targets. Submit their decision evidence or project evidence packs manually.

### C.1.1 Progressive Lab: Turn the Opening Coding Agent into a Production System

Start with the [single-file native coding-agent guide](https://github.com/het2333/Go-Agentic/blob/main/code/go-agentic/01-minimal-loop/CODING_AGENT.md). Do not add every capability at once. At each checkpoint, address one failure mode that has become visible and retain the before/after trace and test result.

| Checkpoint | Add to the same agent | Evidence required |
| --- | --- | --- |
| [Chapter 4](../chapter4/Chapter4-Building-Classic-Agent-Paradigms.md) | Explicit Observe—Decide—Act—Verify state and a bounded loop | Tool failures feed the next turn; repeated state and exhausted budget terminate |
| [Chapter 5](../chapter5/Chapter5-Building-Agents-with-Low-Code-Platforms.md) | Argument schemas, precise edits, tool authority, and trust boundaries | Invalid arguments do not execute; model text cannot create side effects outside tools |
| [Chapter 9](../chapter9/Chapter9-Context-Engineering.md) | JIT file retrieval, structured working notes, and compaction | A compacted long task retains its goal, constraints, verification state, and next step |
| [Chapter 12](../chapter12/Chapter12-Agent-Performance-Evaluation.md) | Reproducible tasks, trace metrics, safety regressions, and an independent evaluator | Report failure rate, cost, and risk slices rather than only a successful demo |
| [Chapter 24](../chapter24/Chapter24-Production-Runtime-and-Platform-Engineering.md) | Durable task state, idempotency, retries, recovery, approvals, and SLOs | Restarts and unknown outcomes cannot cause duplicate writes or false completion |

The core stays small throughout: `messages → model decision → tool call → environment execution → observation → next decision`. Add a component only when it answers a reproducible failure, not to make the architecture diagram look more elaborate.

## C.2 Recommended Order

1. **Minimal loop:** 01 → 04 → 05.
2. **Context and protocols:** 08 → 09 → 10.
3. **Optimization and acceptance:** 11 → 12.
4. **Real projects:** 13 → 14 → 15.
5. **Models and post-training:** 17 → 18 → 19.
6. **Systems:** 20 → 21 → 22.
7. **Productization:** 23 → 24 → 25.

Retain the command, environment version, input fixture, actual output, failed example, and conclusion. A green screenshot alone does not demonstrate understanding.

## C.3 Test Troubleshooting

| Symptom | First check | Evidence to collect |
| --- | --- | --- |
| `ModuleNotFoundError` | Run from `code/go-agentic`; check `pytest.ini` | `pwd`, collection path, `pythonpath` entry |
| 0 tests collected | `test_*.py` and `test_` function names | `pytest --collect-only -q` |
| Unit passes, full suite fails | Module collision, global state, order dependency | Unit/full collection and first stack trace |
| Flaky float assertion | Direct `==`, units, rounding | Raw values, tolerance, units |
| Local pass, CI fail | Python/dependency/locale/timezone/path case | Versions, locale, timezone, fixture |
| Test hangs | Missing termination, blocking IO, unbounded retry | Current stack, loop count, timeout/retry counters |

## C.4 Agent Behavior Troubleshooting

| Symptom | First check | Evidence to collect |
| --- | --- | --- |
| Infinite loop | Stop rule, max steps, repeated-state detection | Per-step state, action signature, remaining budget |
| Repeated write | Stable idempotency key; query outcome after timeout | Business key, request ID, target audit |
| Correct tool, wrong arguments | Business constraints in schema; visible validation error | Arguments, error, tool version |
| JIT search becomes noisy | Evidence-driven query updates; stop/dedup | Query sequence, document IDs, marginal evidence |
| Compaction loses goal | Preserve goal, constraints, next action | Structured before/after diff |
| Agents wait on each other | One owner and acceptance per handoff | Owner, deadline, acceptance, escalation |
| Citation does not support claim | Claim–evidence alignment | Claim ID, location, excerpt, retrieval time |

## C.5 Retrieval and Evaluation Troubleshooting

| Symptom | First check | Evidence to collect |
| --- | --- | --- |
| Semantically similar but unanswerable hits | Chunk contains answer; filters do not exclude it | Query, top-k text, score, metadata |
| Hybrid retrieval gets worse | Sparse/dense scores were directly added | Per-source ranks, normalization, fused order |
| Strange nDCG | Grades and ideal ranking | Grades, DCG, IDCG, intermediate values |
| Unstable LLM judge | Order, length, and model identity leakage | Swapped-order result, agreement, human slices |
| Aggregate rises, risky slice fails | Average hides subgroup | Risk-slice metrics, failures, confidence interval |
| Synthetic data is too easy | Generator shares tested-model bias | Real-failure coverage, audit, difficulty distribution |

## C.6 Training and Systems Troubleshooting

| Symptom | First check | Evidence to collect |
| --- | --- | --- |
| Loss stalls/NaN | Label mask, LR, gradient norm, mixed precision | Valid-token ratio, first NaN step, scaler state |
| General ability regresses | Regression set and data mixture | Before/after slices, provenance, checkpoint |
| MoE expert imbalance | Router distribution, capacity, dropped tokens | Tokens/expert, balance loss, all-to-all time |
| Low GPU utilization | Separate compute, memory, communication, CPU wait | Timeline, kernels, HBM/link traffic, queue gaps |
| Theoretical fit OOMs | Activations, buffers, fragmentation, peak | Allocated/reserved/peak, operator, batch/sequence |
| More GPUs are slower | Parallel dimension crosses slow fabric; no overlap | Topology, collective payload/time, MFU |
| Inference P99 spike | Queue, long prompts, KV pressure, tool latency | Stage trace, concurrency, sequence distribution, admission |
| RLHF throughput low | Which rollout/environment/verifier/sync queue grows | Queue depth, service rate, policy version, staleness |

## C.7 UI and Production Troubleshooting

| Symptom | First check | Evidence to collect |
| --- | --- | --- |
| Duplicate events after reconnect | Event-ID dedup and cursor meaning | Requested cursor, sequence/ID, replay range |
| UI says complete while worker runs | Single source for terminal state | Task state, terminal event, worker lease |
| Target changes after approval | Approval binds payload/version | Approval ID, target, payload hash, execution request |
| Streaming freezes page | Per-token render or unbounded buffer | Event rate, batch interval, queue length, main-thread time |
| Retry amplifies incident | Blind retry after unknown write outcome | Error class, retry policy, idempotency, target audit |
| Circuit never recovers | Half-open probe and health signal | State transitions, probe, success threshold, timeline |
| Secret appears in logs | Field allowlist and redaction boundary | Allowed fields, sample log, scan result |

## C.8 Minimum Lab Evidence Pack

- `README`: goal, hypothesis, command, environment, and limitations.
- Automated tests: normal, boundary, failure, and idempotency/termination cases.
- One failed example and root cause, not only a successful demo.
- Metrics for quality, latency, cost, and safety with data/version labels.
- System diagram covering state, data flow, trust boundaries, and side effects.
- Decision record listing rejected options, evidence, and reproduction steps.
