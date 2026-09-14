# Evaluation and Safety Fixture / 评测与安全示例

Purpose / 用途：对固定 Agent 运行的最终状态、禁止动作、步骤、成本和证据做独立评分，并展示硬门如何覆盖平均分。

- Dependencies / 依赖：Python 3.11+ 标准库；运行测试需要 pytest。
- Input / 输入：`EvaluationCase` 与包含 `TrajectoryStep` 的 `AgentRun`。
- Output / 输出：`EvaluationRecord`，包含分量得分、总分、通过状态和失败原因。
- Safety and side effects / 安全与副作用：纯函数评估固定记录；不执行轨迹中的动作，不访问网络、模型、密钥或外部系统。
- Limitations / 限制：不是 BFCL、GAIA、MCP 一致性或生产安全认证；没有统计置信区间、并发隔离和防篡改存储。

Run from the repository root / 在仓库根目录运行：

```bash
python3 -m pytest code/go-agentic/12-evaluation-safety/test_evaluator.py -q
python3 -m pytest code/go-agentic -q
```

Chapters / 对应章节：[中文第十二章](../../../docs/chapter12/第十二章%20智能体性能评估.md) · [English Chapter 12](../../../docs/chapter12/Chapter12-Agent-Performance-Evaluation.md)
