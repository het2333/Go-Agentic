# 附录 C 实验与排错索引

全部实验以 Python 标准库与本地确定性数据为主，可在 CPU、无模型、无 API、无网络环境运行。统一入口：

```bash
cd code/go-agentic
python3 -m pytest -q
```

## C.1 实验总索引

| 编号 | 目录 | 核心能力 | 重点验收 |
| --- | --- | --- | --- |
| 01 | `01-minimal-loop` | 最小 Observe–Decide–Act Loop | 状态更新、终止、步数上限 |
| 04 | `04-loop-patterns` | ReAct/计划执行等循环模式 | 工具结果驱动下一步，失败不死循环 |
| 05 | `05-tools-environments-rag` | 工具与环境边界 | Schema、权限、可信/不可信数据分离 |
| 06 | `06-lifecycle` | 技术选型矩阵 | 用约束和证据比较方案，不按热度选型 |
| 08 | `08-memory-rag` | 记忆、Multi-query、HyDE、RRF | 写入策略、融合、归一化、检索回归 |
| 09 | `09-context-loop` | JIT Context 与压缩 | Token 预算、结构化笔记、信息保真 |
| 10 | `10-mcp-skills-a2a` | 工具服务器与协议边界 | 能力发现、参数校验、错误语义 |
| 11 | `11-agentic-rl` | Best-of-N、ToT、MCTS | 搜索预算、确定性评价、停止条件 |
| 12 | `12-evaluation-safety` | 评测器与检索指标 | MRR/nDCG/F1、一致性、安全回归 |
| 13 | `13-enterprise-execution-agent` | 企业执行 Agent | 审批、幂等、审计、补偿动作 |
| 14 | `14-deep-research-agent` | Deep Research | 查询分解、证据对齐、引用完整性 |
| 15 | `15-multi-agent-system` | 多 Agent 工作流 | 交接契约、验收、失败升级 |
| 17 | `17-transformer-math` | Attention、Tokenization、Decoding | Mask、数值、Top-k/Top-p/约束解码 |
| 18 | `18-training-compression` | 训练与压缩账本 | SFT Mask/Packing、LoRA、MoE、资源估算 |
| 19 | `19-alignment` | RL 与偏好目标 | Return/GAE、PPO/DPO/KTO/RLVR 边界 |
| 20 | `20-gpu-topology` | Roofline、MFU、互联与成本 | 单位、瓶颈、Ring 流量、设备预算 |
| 21 | `21-inference-capacity` | KV Cache 容量 | K/V 双份、GQA 维度、最大 Batch |
| 22 | `22-distributed-training` | ZeRO/FSDP 与并行规划 | 状态分片、世界大小、同步与设备小时 |
| 23 | `23-agentic-ui` | UI State 与可重放事件流 | 顺序、去重、审批、终局、重连 Cursor |
| 24 | `24-production-runtime` | 生产运行时 | 重试、熔断、并发、恢复与 SLO |
| 25 | `25-capstone` | 毕业设计 | 需求、架构、评测、安全、运维证据包 |

运行单项实验：

```bash
python3 -m pytest 08-memory-rag -q
python3 -m pytest 23-agentic-ui -q
```

`06-lifecycle/selection_matrix.md` 和 `25-capstone/README.md` 是人工评审产物，不由 Pytest 判定；应按文件内模板提交选型证据或项目证据包。

### C.1.1 贯穿实验：把开场 Coding Agent 一步步做成生产系统

从[单文件原生 Coding Agent 运行指南](https://github.com/het2333/Go-Agentic/blob/main/code/go-agentic/01-minimal-loop/CODING_AGENT.md)开始。不要一次添加所有能力；每到一个关键章节，只解决当时已经出现的一个失败模式，并保存修改前后的轨迹与测试结果。

| 学习节点 | 给同一个 Agent 增加什么 | 必须证明什么 |
| --- | --- | --- |
| [第 4 章](../chapter4/第四章%20智能体经典范式构建.md) | 显式的 Observe—Decide—Act—Verify 状态与有界循环 | 工具失败能进入下一轮，重复状态和预算耗尽会停止 |
| [第 5 章](../chapter5/第五章%20基于低代码平台的智能体搭建.md) | 参数 Schema、精确编辑、工具权限与可信边界 | 错误参数不会执行，模型文本不能越过工具边界产生副作用 |
| [第 9 章](../chapter9/第九章%20上下文工程.md) | JIT 文件检索、结构化工作笔记与 Compaction | 长任务压缩后仍保留目标、约束、验证状态和下一步 |
| [第 12 章](../chapter12/第十二章%20智能体性能评估.md) | 可复现任务集、轨迹指标、安全回归与独立验收器 | 不只展示成功 Demo，还能报告失败率、成本与风险切片 |
| [第 24 章](../chapter24/第二十四章%20生产Runtime与平台工程.md) | 持久任务状态、幂等、重试、恢复、审批与 SLO | 进程重启和未知结果不会导致重复写入或虚假完成 |

这条路线始终保留最小核心：`messages → 模型决策 → Tool Call → 环境执行 → Observation → 再决策`。新增组件必须对应一个可复现的失败，而不是为了让架构图看起来更复杂。

## C.2 建议实验顺序

1. **最小闭环：** 01 → 04 → 05；
2. **上下文与协议：** 08 → 09 → 10；
3. **优化与验收：** 11 → 12；
4. **真实项目：** 13 → 14 → 15；
5. **模型与后训练：** 17 → 18 → 19；
6. **系统基础设施：** 20 → 21 → 22；
7. **产品化：** 23 → 24 → 25。

每次实验保留：命令、环境版本、输入 Fixture、实际输出、失败样本和结论。只截“绿色通过”不能证明理解。

## C.3 测试故障排查

| 症状 | 第一检查 | 需要看到的证据 |
| --- | --- | --- |
| `ModuleNotFoundError` | 是否从 `code/go-agentic` 运行；`pytest.ini` 是否包含目录 | `pwd`、测试收集路径、`pythonpath` 条目 |
| 0 tests collected | 文件是否命名 `test_*.py`，测试函数是否以 `test_` 开头 | `pytest --collect-only -q` 输出 |
| 单测通过、全量失败 | 模块名冲突、共享全局状态、顺序依赖 | 单项与全量收集清单、首次失败 Stack Trace |
| 浮点断言偶发失败 | 是否直接 `==`；单位与舍入是否一致 | 原始值、允许误差、输入单位 |
| 本机通过、CI 失败 | Python/依赖/Locale/时区/路径大小写差异 | 环境版本、`locale`、时区、失败 Fixture |
| 测试卡住 | 无终止条件、阻塞 IO、重试无上限 | 当前 Stack、循环步数、超时与重试计数 |

## C.4 Agent 行为故障排查

| 症状 | 第一检查 | 需要看到的证据 |
| --- | --- | --- |
| Agent 无限循环 | 终止条件、最大步数、重复状态检测 | 每轮状态摘要、动作签名、预算剩余 |
| 重复执行写操作 | 幂等键是否稳定；超时后是否先查结果 | 业务键、请求 ID、目标系统审计记录 |
| 工具选对但参数错 | Schema 是否表达业务约束；错误是否回传模型 | 原始参数、校验错误、工具版本 |
| JIT 搜索越搜越乱 | 查询是否由证据更新；是否有停止/去重 | 查询序列、命中文档 ID、边际新增证据 |
| 压缩后忘记目标 | Compaction 是否保留目标、约束和下一步 | 压缩前后结构化字段 Diff |
| 多 Agent 互相等待 | 责任与交接验收是否有唯一所有者 | 工作项 Owner、Deadline、Acceptance、Escalation |
| 最终答案有引用但不支撑 | Claim–Evidence 是否逐条对齐 | Claim ID、Source Location、原文片段、获取时间 |

## C.5 检索与评测故障排查

| 症状 | 第一检查 | 需要看到的证据 |
| --- | --- | --- |
| 向量检索“语义像但答不上” | Chunk 是否含答案；过滤条件是否误杀 | Query、Top-k 文本、分数、Metadata |
| 混合检索反而下降 | 稀疏/稠密分数是否直接相加 | 各路 Rank、归一化方式、RRF 后顺序 |
| nDCG 异常 | Relevance Grade 与理想排序是否正确 | 每项 Grade、DCG、IDCG、中间值 |
| LLM Judge 不稳定 | 候选顺序、长度和模型来源是否泄露 | 交换顺序结果、一致率、人工金标切片 |
| 总分提高但高风险失败 | 是否被平均值掩盖 | 风险分组指标、失败样本、置信区间 |
| 合成数据过于简单 | 生成器与被测模型是否共享偏差 | 真实失败覆盖率、人工抽查、难度分布 |

## C.6 训练与系统故障排查

| 症状 | 第一检查 | 需要看到的证据 |
| --- | --- | --- |
| Loss 不降/NaN | Label Mask、学习率、梯度范数、混合精度 | 有效 Token 比例、首个 NaN Step、Scaler 状态 |
| 微调后通用能力下降 | 回归集与数据配比 | 训练前后分项指标、样本来源、Checkpoint |
| MoE Expert 倾斜 | Router 分布、Capacity、Dropped Token | 每 Expert Token 数、负载损失、All-to-All 时间 |
| GPU 利用率低 | 先分计算、访存、通信、CPU 等待 | Timeline、Kernel、HBM/Link 吞吐、Queue Gap |
| 理论显存够但 OOM | 激活、临时 Buffer、碎片与峰值 | Allocated/Reserved/Peak、失败算子、Batch/Seq |
| 扩卡后变慢 | 并行维度是否跨慢链路；通信是否重叠 | 物理拓扑、Collective Payload/耗时、MFU |
| 推理 P99 激增 | Queue、长 Prompt、KV 压力、工具延迟 | 分阶段 Trace、并发、Seq 分布、Admission 决策 |
| RLHF 吞吐低 | Rollout、环境、Verifier、同步哪个排队 | 各队列深度、服务吞吐、Policy Version、Staleness |

## C.7 UI 与生产故障排查

| 症状 | 第一检查 | 需要看到的证据 |
| --- | --- | --- |
| 重连后事件重复 | Event ID 去重与 Cursor 语义 | 重连请求 Cursor、Sequence/Event ID、服务端重放范围 |
| UI 显示完成但后端仍运行 | 终局事件来源是否唯一 | Task State、Terminal Event、Worker Lease |
| 审批后目标被替换 | 审批是否绑定动作摘要/版本 | Approval ID、Target、Payload Hash、执行请求 |
| Streaming 导致页面卡顿 | 是否逐 Token 渲染、缓冲是否无界 | 事件速率、批量周期、队列长度、主线程耗时 |
| Retry 放大事故 | 是否对未知结果的写操作盲目重试 | Error Class、Retry Policy、幂等记录、目标审计 |
| 熔断器不恢复 | Half-open 探测与健康指标 | 状态转换、探测请求、成功阈值、时间线 |
| Secret 出现在日志 | 结构化日志字段与脱敏边界 | 字段 Allowlist、样例日志、扫描结果 |

## C.8 提交实验的最小证据包

- `README`：目标、假设、运行命令、环境与限制；
- 自动化测试：正常路径、边界、失败与幂等/终止；
- 一份失败样本及根因，不只展示成功 Demo；
- 指标表：质量、延迟、成本、安全，注明数据与版本；
- 系统图：状态、数据流、信任边界和副作用；
- 决策记录：放弃了什么方案、依据是什么、如何复现。
