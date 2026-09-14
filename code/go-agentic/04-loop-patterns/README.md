# Loop Patterns Fixture / Loop 模式示例

Purpose / 用途：用确定性 Policy、Environment 和 Verifier 演示同一 `plan → execute → verify → retry` 状态机中的规划、反馈、重试预算和终止。

- Dependencies / 依赖：Python 3.11+ 标准库；运行测试需要 pytest。
- Input / 输入：固定任务、Policy 生成的动作计划、验证反馈与 `retry_budget`。
- Output / 输出：`LoopResult`，包含状态、尝试次数、结果和完整 `Transition` 轨迹。
- Safety and side effects / 安全与副作用：只操作测试内存状态；不访问网络、模型、环境变量或真实文件。
- Limitations / 限制：这是状态机教学 Fixture，不是 Pi API、并发执行器、持久化 Runtime 或生产重试系统。

Run from the repository root / 在仓库根目录运行：

```bash
python3 -m pytest code/go-agentic/04-loop-patterns/test_loop.py -q
python3 -m pytest code/go-agentic -q
```

Chapters / 对应章节：[中文第四章](../../../docs/chapter4/第四章%20智能体经典范式构建.md) · [English Chapter 4](../../../docs/chapter4/Chapter4-Building-Classic-Agent-Paradigms.md)
