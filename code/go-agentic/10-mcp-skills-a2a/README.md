# Protocol Boundary Fixture / 协议边界示例

Purpose / 用途：通过本地 `lookup_order` Tool 演示发现、Schema、权限、只读结果和结构化错误边界。

- Dependencies / 依赖：Python 3.11+ 标准库；运行测试需要 pytest。
- Input / 输入：Tool 名称、参数 Mapping、授权 Scope 和固定订单记录。
- Output / 输出：Tool 定义或 `ToolResult`，明确区分成功、未知 Tool、参数错误、拒绝与未找到。
- Safety and side effects / 安全与副作用：只读内存订单；拒绝发生在执行前；不连接网络、MCP Transport、ERP 或身份系统。
- Limitations / 限制：不是 MCP/A2A 一致性实现，不含 JSON-RPC、握手、Resource、Prompt、OAuth、持久化或并发。

Run from the repository root / 在仓库根目录运行：

```bash
python3 -m pytest code/go-agentic/10-mcp-skills-a2a/test_tool_server.py -q
python3 -m pytest code/go-agentic -q
```

Chapters / 对应章节：[中文第十章](../../../docs/chapter10/第十章%20智能体通信协议.md) · [English Chapter 10](../../../docs/chapter10/Chapter10-Agent-Communication-Protocols.md)
