# RAG and Memory Fixture / RAG 与记忆示例

Purpose / 用途：演示带来源的记忆写入、检索、整合、遗忘、隐私策略和带版本的外部状态，而不把检索结果自动当作长期记忆。

- Dependencies / 依赖：Python 3.11+ 标准库；运行测试需要 pytest。
- Input / 输入：`MemoryCandidate`、查询、当前时间、保留策略和版本化 `StateRecord`。
- Output / 输出：写入决定、排序后的 `MemoryHit`、来源快照、整合结果和状态冲突。
- Safety and side effects / 安全与副作用：只修改进程内存中的 Store；不访问网络、真实用户数据、磁盘或模型。
- Limitations / 限制：没有向量数据库、持久化、加密、租户隔离、并发控制或统计检索评估。

Run from the repository root / 在仓库根目录运行：

```bash
python3 -m pytest code/go-agentic/08-memory-rag/test_memory.py -q
python3 -m pytest code/go-agentic -q
```

Chapters / 对应章节：[中文第八章](../../../docs/chapter8/第八章%20记忆与检索.md) · [English Chapter 8](../../../docs/chapter8/Chapter8-Memory-and-Retrieval.md)
