# Tools, Environments, and RAG Fixture / 工具、环境与 RAG 示例

Purpose / 用途：演示 Tool Schema、语义校验、权限先于执行、结构化错误，以及对固定本地语料的确定性 JIT 检索。

- Dependencies / 依赖：Python 3.11+ 标准库；运行测试需要 pytest。
- Input / 输入：`ToolCall`、权限集合、查询文本、标签和固定 `Document` 语料。
- Output / 输出：带状态码和匹配 `Snippet` 的 `ToolResult`，以及可检查的调用计数。
- Safety and side effects / 安全与副作用：只读内存语料；不访问网络、磁盘、模型、密钥或外部数据库。
- Limitations / 限制：词法评分不是向量检索；本例不实现 MCP、身份认证、沙箱或生产检索质量评估。

Run from the repository root / 在仓库根目录运行：

```bash
python3 -m pytest code/go-agentic/05-tools-environments-rag/test_environment.py -q
python3 -m pytest code/go-agentic -q
```

Chapters / 对应章节：[中文第五章](../../../docs/chapter5/第五章%20基于低代码平台的智能体搭建.md) · [English Chapter 5](../../../docs/chapter5/Chapter5-Building-Agents-with-Low-Code-Platforms.md)
