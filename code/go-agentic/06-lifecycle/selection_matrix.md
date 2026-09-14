# Agent Harness and Framework Selection Matrix / Agent Harness 与框架选择矩阵

> **As of / 截至：2026-09-13.** This matrix is a dated shortlist of current examples, not an endorsement or a substitute for a task-set evaluation. Candidate versions are the package releases checked on that date; verify features and licenses against each project's current official documentation before adoption.
>
> **候选版本核对日期：2026-09-13。** 本矩阵是带时间属性的当前示例短名单，不构成推荐，也不能替代任务集评估。候选版本是当日核对的软件包版本；采用前应根据各项目最新官方文档核实功能与许可证。

## 1. Start from required capabilities / 从所需能力出发

Score each capability as **required**, **useful**, or **irrelevant** before looking at project names. A candidate fails the gate if it cannot satisfy any required capability through a tested, supportable path.

在查看项目名称前，先把每项能力标为**必需**、**有用**或**无关**。如果候选方案无法通过经过测试且可维护的路径满足任一必需能力，它就不能通过选择门槛。

| Capability / 能力 | Evidence to request / 应要求的证据 | Common trade-off / 常见代价 |
| --- | --- | --- |
| Explicit loop control / 显式循环控制 | Inspectable states, transitions, budgets, and termination / 可检查的状态、转移、预算与终止 | More control code / 更多控制代码 |
| Typed tool boundary / 类型化工具边界 | Schema validation, permission checks, structured errors / Schema 校验、权限检查、结构化错误 | Narrower tool surface / 更窄的工具面 |
| Durable state / 持久状态 | Checkpoint, resume, migration, and concurrency tests / 检查点、恢复、迁移与并发测试 | Storage and consistency work / 存储与一致性工作 |
| Human approval / 人工审批 | Pause, inspect, approve or reject, and resume / 暂停、检查、批准或拒绝、恢复 | Added latency and UI work / 额外延迟与界面工作 |
| Multi-agent coordination / 多 Agent 协调 | Ownership, message routing, termination, and conflict policy / 所有权、消息路由、终止与冲突策略 | Larger state and evaluation space / 更大的状态与评估空间 |
| Observability and evaluation / 可观测性与评估 | Exportable traces, stable IDs, task-level scoring / 可导出轨迹、稳定 ID、任务级评分 | Telemetry cost and retention duties / 遥测成本与保留责任 |
| Service deployment / 服务部署 | Isolation, rate limits, queues, rollback, and SLO evidence / 隔离、限流、队列、回滚与 SLO 证据 | Operational complexity / 运维复杂度 |
| Provider portability / 提供商可移植性 | Contract tests across required model APIs / 所需模型 API 间的契约测试 | Lowest-common-denominator pressure / 最小公分母压力 |

## 2. Current examples by architectural fit / 按架构适配度列出的当前示例

The “strong fit” column names the shape each project exposes most directly. Every row still requires a local proof with your tools, model, data, and deployment boundary.

“主要适配”列描述各项目最直接暴露的架构形态。每一行仍需使用你的工具、模型、数据和部署边界完成本地验证。

| Current example / 当前示例 | Candidate version / 候选版本 | Strong fit / 主要适配 | Inspect first / 优先检查 | Prefer when / 适合条件 | Watch closely / 重点风险 |
| --- | --- | --- | --- | --- | --- |
| [Pi](https://github.com/earendil-works/pi) | `@earendil-works/pi-coding-agent@0.85.1` | Minimal terminal coding harness; sessions and extensions / 最小终端编码 Harness；会话与扩展 | Tool authority, extension boundary, session behavior / 工具权限、扩展边界、会话行为 | You want a transparent coding loop and small core / 需要透明的编码循环与小型核心 | Product service features may need separate components / 产品服务能力可能需要独立组件 |
| [LangGraph](https://github.com/langchain-ai/langgraph) | `langgraph 1.2.11` | Explicit graph and state-machine orchestration / 显式图与状态机编排 | State schema, checkpointing, interrupts, deployment path / 状态 Schema、检查点、中断、部署路径 | Branches, resumability, and auditability dominate / 分支、恢复与审计优先 | Graph and state design add code and migration work / 图与状态设计增加代码与迁移工作 |
| [AutoGen](https://github.com/microsoft/autogen) | `autogen-agentchat 0.7.5` | Event-driven and conversational multi-agent applications / 事件驱动与对话式多 Agent 应用 | Team termination, tool execution owner, message history / 团队终止、工具执行者、消息历史 | Role-based collaboration is part of the task / 基于角色的协作属于任务本身 | Conversation growth and emergent paths expand evaluation / 对话增长与涌现路径扩大评估空间 |
| [AgentScope](https://github.com/agentscope-ai/agentscope) | `agentscope 2.0.8` | Multi-agent application components and distributed execution / 多 Agent 应用组件与分布式执行 | Message ordering, runtime topology, tracing, failure recovery / 消息顺序、运行时拓扑、追踪、故障恢复 | Distribution and service integration are early requirements / 分布式与服务集成是早期需求 | Operational surface can exceed prototype needs / 运维面可能超过原型需求 |
| [CAMEL](https://github.com/camel-ai/camel) | `camel-ai 0.2.90` | Role-playing, agent societies, and research workflows / 角色扮演、Agent 社会与研究工作流 | Role protocol, workforce routing, termination, evaluation / 角色协议、Workforce 路由、终止、评估 | Open-ended collaboration is the experiment / 开放式协作本身是实验对象 | More agents do not guarantee better task outcomes / 更多 Agent 不保证更好的任务结果 |
| [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) | `openai-agents 0.22.2` | Provider-integrated tools, handoffs, guardrails, sessions, and tracing / 提供商集成的工具、移交、护栏、会话与追踪 | Provider coupling, trace data, handoff semantics, approval flow / 提供商耦合、轨迹数据、移交语义、审批流 | Built-in provider integration reduces delivery work / 内置提供商集成能减少交付工作 | Portability and data-governance requirements need explicit tests / 可移植性与数据治理需要显式测试 |

## 3. Decision record / 决策记录

Record the decision beside the prototype. A useful record is short enough to review and precise enough to falsify.

把决策记录放在原型旁边。有效记录应足够简短以便审阅，也足够精确以便证伪。

```text
Task set / 任务集:
Required capabilities / 必需能力:
Candidates and versions / 候选方案与版本:
Prototype evidence / 原型证据:
Evaluation result / 评估结果:
Security and operations result / 安全与运维结果:
Chosen option and rejected alternatives / 选择项与排除项:
Revisit trigger / 重新评估触发条件:
```

Revisit the decision when the task distribution, authority boundary, deployment target, model provider, or maintenance capacity changes. A framework migration is an interface migration: preserve task fixtures, tool contracts, trace fields, and acceptance thresholds so the new candidate can be compared on the same evidence.

当任务分布、权限边界、部署目标、模型提供商或维护能力发生变化时，应重新评估。框架迁移属于接口迁移：保留任务 Fixture、工具契约、轨迹字段和验收阈值，才能用同一证据比较新候选方案。

## Official project sources / 项目官方资料

- [Pi repository](https://github.com/earendil-works/pi)
- [LangGraph repository](https://github.com/langchain-ai/langgraph)
- [AutoGen repository](https://github.com/microsoft/autogen)
- [AgentScope repository](https://github.com/agentscope-ai/agentscope)
- [CAMEL repository](https://github.com/camel-ai/camel)
- [OpenAI Agents SDK repository](https://github.com/openai/openai-agents-python)
