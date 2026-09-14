# Enterprise Task Execution Agent / 企业任务执行 Agent

This deterministic Python-standard-library fixture follows one supplier-delivery
anomaly from evidence collection to a human-approved email effect. It makes no
network, model, email, or ERP call and needs no key.

这个仅使用 Python 标准库的确定性示例，以供应商交付异常为主线，从证据收集推进到经人工批准的邮件副作用。它不调用网络、模型、真实邮件或 ERP，也不需要 API Key。

## Run / 运行

From the repository root / 在仓库根目录运行：

```bash
python3 -m pytest code/go-agentic/13-enterprise-execution-agent/test_agent.py -q
python3 -m pytest code/go-agentic -q
```

## Flow / 流程

```text
recent email + PO + contract + logistics
                    ↓
              evidence ledger
                    ↓
       missing-tracking decision + draft
                    ↓
        preview/action hash → human approval
                    ↓
       send_once(idempotency key) → audit
```

`build_demo_system()` returns the real in-memory components used by the tests.
The fixed `PO-7` fixture detects a missing tracking number. Evidence freshness,
content hashes, order/supplier/contract relationships, and logistics status are
validated before drafting. Freshness uses exact elapsed time: equality at the
limit passes and any positive overage fails. `missing_sources={"logistics"}` plus
`supply_evidence(record)` demonstrates same-task refresh. `fail_audit_once`
demonstrates pre-send and post-send audit recovery.

`build_demo_system()` 返回测试实际使用的内存组件。固定的 `PO-7` 数据会检出追踪号缺失。起草前会验证证据新鲜度、内容哈希、订单/供应商/合同关系和物流状态；新鲜度按精确时间差判断，恰好等于上限可通过，任何正超时均失败。`missing_sources={"logistics"}` 与 `supply_evidence(record)` 演示同任务补证；`fail_audit_once` 演示发送前和发送后的审计恢复。

Approval carries `decided_at` and `expires_at`, binds the exact preview hash,
and is persisted before sending. Rejection and approval have distinct audit IDs;
conflicting same-ID audit payloads fail, and a truthful `approval_recorded` event
must exist before sending. `completed` is terminal. Idempotency keys bind
recipient, subject, and body fingerprints, so replay returns one receipt while
same-key changed payloads are rejected.

批准记录包含 `decided_at` 和 `expires_at`，绑定完整预览哈希，并在发送前持久化。拒绝与批准使用不同审计 ID；同 ID 不同载荷会失败，且发送前必须存在真实的 `approval_recorded` 事件。`completed` 是终态。幂等键绑定收件人、主题和正文指纹，因此正常重放只返回一个回执，同键不同载荷会被拒绝。

The adapter methods model typed Tool/MCP boundaries, and the agent's
observe-decide-act-verify progression is compatible with the Pi-oriented loop
used by this course. This fixture is not a Pi SDK, MCP protocol, SMTP, or ERP
conformance implementation. Production systems need durable task state,
transactional idempotency storage, authorization, secrets, concurrency
control, provider receipts, monitoring, and retention policy.

适配器方法用于表示类型化的 Tool/MCP 边界，Agent 的“观察—决策—行动—验证”过程与本课程的 Pi 主线 Loop 兼容。本示例不是 Pi SDK、MCP 协议、SMTP 或 ERP 一致性实现。生产系统还需要持久化任务状态、事务型幂等存储、授权、密钥管理、并发控制、提供方回执、监控和保留策略。
