# Context and Loop Engineering Fixture / 上下文与循环工程示例

Purpose / 用途：用显式 Token/Cost Unit 演示证据选择、预算、Compaction、恢复状态、验证门和循环终止。

- Dependencies / 依赖：Python 3.11+ 标准库；运行测试需要 pytest。
- Input / 输入：固定 `Evidence`、`ContextBudget`、任务状态、来源快照和 `LoopLimits`。
- Output / 输出：`ContextSelection`、`CompactionRecord`、`ResumeResult` 与有界循环状态。
- Safety and side effects / 安全与副作用：只计算固定内存数据；不读取真实会话、网络、文件、模型或 Provider Tokenizer。
- Limitations / 限制：人工 Token Cost 只保证 Fixture 可复现，不代表任何 Provider 的真实计费或上下文窗口。

Run from the repository root / 在仓库根目录运行：

```bash
python3 -m pytest code/go-agentic/09-context-loop/test_context.py -q
python3 -m pytest code/go-agentic -q
```

Chapters / 对应章节：[中文第九章](../../../docs/chapter9/第九章%20上下文工程.md) · [English Chapter 9](../../../docs/chapter9/Chapter9-Context-Engineering.md)
