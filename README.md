<div align="right">
  中文 | <a href="./README_EN.md">English</a>
</div>

# Go Agentic

> 不只教模型怎样回答，而是教 Agent 如何在真实环境中获取信息、采取行动、验证结果，并在明确边界内完成任务。

Go Agentic 是一门 25 章的全栈 Agentic AI 工程课程。课程从可运行 Agent 出发，逐步进入 Context、Memory、Protocol、Evaluation、模型数学、后训练、GPU/推理基础设施、Agentic UI 和生产 Runtime。

- [打开课程](./docs/README.md)
- [前言](./docs/前言.md)
- [来源与致谢](./docs/来源与致谢.md)

## 学习路线

| 阶段 | 章节 | 主题 |
| --- | --- | --- |
| 一 | 1–3 | Agentic AI 基础与 LLM 够用知识 |
| 二 | 4–7 | Agent Loop、Tool、Environment 与 Runtime |
| 三 | 8–10 | RAG、Memory、Context、MCP、Skills 与 A2A |
| 四 | 11–12 | Agentic RL 决策、评测、可观测性与安全 |
| 五 | 13–16 | 真实项目与期中验收 |
| 六 | 17–19 | Transformer、预训练、AdamW、压缩、PPO/DPO/GRPO |
| 七 | 20–22 | GPU、NVLink/InfiniBand、FlashAttention/vLLM、FSDP/ZeRO |
| 八 | 23–24 | Agentic UI、人在回路与生产 Runtime |
| 九 | 25 | 毕业设计、验收与发布 |

**Agent 应用工程路线：** 第 1–16 章 → 第 23–25 章。

**全栈 Agentic AI 路线：** 第 1–25 章按顺序学习。

**模型与系统进阶路线：** 完成第 1–12 章后，集中学习第 17–22 章。

前 16 章只需 Python、命令行和模型 API 基础；第 17–22 章会使用线性代数、概率、PyTorch 和系统知识，但保留无大规模 GPU 的离线实验。

## 实践与验证

当前维护的离线实验位于 `code/go-agentic/`。所有实验优先使用固定 Fixture，可在不调用付费 API 和不下载大模型的情况下完成核心验证。

```bash
cd code/go-agentic
python3 -m pytest -q
```

## 来源与许可

文档与原创视觉资产采用 [CC BY 4.0](./LICENSES/CC-BY-4.0.txt)；`code/go-agentic/`、`tools/independent_release/`、`docs/tests/` 与 `docs/index.html` 中的软件采用 [Apache License 2.0](./LICENSES/Apache-2.0.txt)。完整路径边界与法律文本副本见根目录 [LICENSE](./LICENSE)。

论文、标准、软件项目与设计参考资料按实际用途披露，不表示认可、赞助或隶属关系。详见[来源与致谢](./docs/来源与致谢.md)。
