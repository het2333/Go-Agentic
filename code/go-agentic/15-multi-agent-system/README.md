# Bounded Multi-Agent Workflow / 有界多智能体工作流

This standard-library fixture turns the Chapter 13 execution contract and the
Chapter 14 evidence contract into one bounded orchestration. It makes no model,
network, Pi SDK, Hermes, MCP, email, ERP, or other external call. The default
path is deterministic, offline, and needs no API key.

本标准库 Fixture 把第 13 章的执行契约与第 14 章的证据契约组合成一条有界编排流程。它不调用模型、网络、Pi SDK、Hermes、MCP、邮件、ERP 或其他外部服务；默认路径确定、离线且无需 API Key。

## Run / 运行

From the repository root:

```bash
python3 code/go-agentic/15-multi-agent-system/workflow.py
python3 -m pytest code/go-agentic/15-multi-agent-system/test_workflow.py -q
```

Expected comparison:

```text
routine: baseline_quality=100 multi_quality=100 baseline_cost=4 multi_cost=6 worth_extra_cost=False
conflicting_evidence: baseline_quality=55 multi_quality=100 baseline_cost=4 multi_cost=9 worth_extra_cost=True
```

## Contract / 契约

The planner emits a plan; the researcher emits evidence findings; the reviewer
accepts or rejects a specific artifact digest; and the executor creates an
action preview. Every cross-role transition is a typed `Message` containing
artifact IDs. Artifacts are frozen, hashed, versioned values: correction creates
v2 with a parent link and never rewrites v1.

Planner 产出计划，Researcher 产出证据结论，Reviewer 针对特定 Artifact Digest 接受或拒绝，Executor 只生成动作预览。每次跨角色转移都是包含 Artifact ID 的显式 `Message`。Artifact 为冻结、哈希、版本化值；修订会生成带父链接的 v2，绝不覆盖 v1。

One review retry is allowed by default. A second rejection, cost exhaustion, or
deterministic role failure stops downstream work and leaves an audit event. The
gateway can run only after a fresh, timezone-aware human approval matches the
preview digest. An accepted approval is recorded before a later execution-budget
or gateway failure. Gateway collisions become terminal `gateway_failed` results
with a recovery hint, and the idempotency key still yields one effect on replay.

默认只允许一次 Review 重试。第二次拒绝、成本预算耗尽或确定性角色失败都会停止下游执行并留下审计事件。只有带时区且未过期的人工批准与预览 Digest 完全匹配时，Gateway 才能运行；已接受的批准会先于后续执行预算或 Gateway 失败写入审计。Gateway 冲突进入带恢复提示的终态 `gateway_failed`，相同幂等键重放仍只产生一次效果。

## Reading the metrics / 阅读指标

Both designs use the same draft, preview, approval, gateway execution, and audit
envelope. The baseline spends two units on single-agent reasoning plus one on
preview and one on execution. `routine` scores 100 in both designs, while role
coordination costs two extra units, so multi-agent work is not justified. In
`conflicting_evidence`, the baseline silently resolves a contradiction and
scores 55 with one safety violation. Review forces disclosure and a bounded
revision; quality reaches 100 with no safety violation at five extra units. The
fixture marks coordination worthwhile only when it completes, gains at least 20
quality points, and reduces safety violations.

两种设计使用相同的草稿、预览、批准、Gateway 执行与审计安全外壳。基线把 2 个单位用于单智能体推理，预览与执行各 1 个单位。`routine` 中两种设计均为 100 分，而角色编排多花 2 个成本单位，因此不值得使用多智能体。`conflicting_evidence` 中，单智能体静默消解冲突，得 55 分并产生 1 次安全违规；Reviewer 迫使系统披露冲突并做一次有界修订，多智能体以多 5 个成本单位换得 100 分和 0 次违规。只有流程完成、质量至少提高 20 分且安全违规减少时，Fixture 才判定编排值得。

## Production boundary / 生产边界

The fixture teaches contracts, not semantic model quality or distributed-system
guarantees. Production use needs durable artifact and audit stores, authenticated
role identities, authorization policy, concurrency control, secret handling,
provider receipts, observability, retention, incident response, and evaluation
on representative private cases.

本示例教授契约，不证明模型语义质量或分布式系统保证。生产环境还需要持久化 Artifact 与审计存储、可信角色身份、授权策略、并发控制、密钥处理、Provider 回执、可观测性、保留策略、事件响应，以及基于代表性私有案例的评估。
