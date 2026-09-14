<div align="right">
  中文 | <a href="./README_EN.md">English</a>
</div>

# Go Agentic

<figure class="course-hero">
  <img src="./assets/visuals/home.webp" alt="发光的智能体核心连接五个不同的学习领域，构成技术课程地图。" width="1536" height="864" loading="lazy" decoding="async">
  <figcaption><em>课程地图串联基础原理、工具、记忆、协作与系统工程。</em></figcaption>
</figure>

> 不只教模型怎样回答，而是教一个 Agent 怎样在真实环境里持续获得信息、采取行动、验证结果，并在明确边界内完成任务。

Go Agentic 是一门面向现代 Agentic AI 工程的 25 章实践课程。课程先帮你构建能运行、能验证的 Agent，再深入模型数学、后训练、高性能推理、分布式基础设施和生产平台。Pi 贯穿 Agent 工程实践；DeepSeek Harness 和 Hermes 只用于解释不同架构边界。

- [项目仓库说明](../README.md)
- [English course home](./README_EN.md)
- [来源与致谢](./来源与致谢.md)

## 选择你的学习路径

不需要一开始学完全部内容。先选择当前目标；页面顶部的滑动开关会记住你的选择。

<div class="learning-route-grid">
  <article class="learning-route-card recommended" id="route-application">
    <span class="learning-route-badge">推荐 · 先做出可用产品</span>
    <h3>Agent 应用工程</h3>
    <p>适合希望快速交付 Agent 产品、企业自动化或 Deep Research 应用的开发者。</p>
    <p class="learning-route-sequence">第 1–16 章 → 第 23–25 章</p>
    <a class="learning-route-action" href="#/./chapter1/第一章%20初识智能体">开始应用工程路线</a>
  </article>
  <article class="learning-route-card" id="route-fullstack">
    <span class="learning-route-badge">完整 · 从 Agent 到基础设施</span>
    <h3>全栈 Agentic AI</h3>
    <p>适合希望系统掌握模型、后训练、推理优化、分布式和生产平台的读者。</p>
    <p class="learning-route-sequence">第 1–25 章按顺序学习</p>
    <a class="learning-route-action" href="#/./chapter1/第一章%20初识智能体">开始全栈路线</a>
  </article>
  <article class="learning-route-card" id="route-systems">
    <span class="learning-route-badge">进阶 · 补齐底层能力</span>
    <h3>模型与系统进阶</h3>
    <p>适合已有 Agent 基础，希望集中学习 Transformer、训练、GPU 和分布式系统的读者。</p>
    <p class="learning-route-sequence">完成第 1–12 章 → 第 17–22 章</p>
    <a class="learning-route-action" href="#/./chapter17/第十七章%20Transformer数学基础">从第 17 章开始</a>
  </article>
</div>

暂时不确定？先做[附录 A 自测题库](./appendices/附录A%20自测题库.md)，再回来选择。前 16 章只需 Python、命令行和模型 API 基础；第 17–22 章需要更多线性代数、概率、PyTorch 和 GPU 系统知识，但保留无大规模 GPU 的学习路径。

## 学习成果

- 设计带工具调用、错误恢复、验证和终止条件的 Agent Loop；
- 管理 JIT Context、Compaction、结构化状态、RAG 和长期记忆；
- 用环境、轨迹、基准、审批、审计和回放证明 Agent 有效且可控；
- 解释 Transformer、预训练、AdamW、PPO、DPO 和 GRPO 的必要数学；
- 识别 GPU 内存、NVLink/InfiniBand、FlashAttention、vLLM、FSDP 和 ZeRO 的系统瓶颈；
- 交付支持进度、工具流、证据、审批、恢复和成本 SLO 的生产 Agent 系统。

## 课程路线

### 第一阶段：Agentic AI 基础（第 1–3 章）

1. [初识 Agentic AI](./chapter1/第一章%20初识智能体.md)
2. [智能体发展与现代运行时](./chapter2/第二章%20智能体发展史.md)
3. [Agent 所需的 LLM 与系统基础](./chapter3/第三章%20大语言模型基础.md)

> **阶段交付：** 能区分 Model、Agent、Framework、Harness、Runtime 与 Environment，并判断常见 Agent 失败位于哪一层。

### 第二阶段：构建可运行 Agent（第 4–7 章）

4. [Agent 设计模式与 Loop](./chapter4/第四章%20智能体经典范式构建.md)
5. [工具、环境与 Agentic RAG](./chapter5/第五章%20基于低代码平台的智能体搭建.md)
6. [Agent 开发生命周期与框架选择](./chapter6/第六章%20框架开发实践.md)
7. [现代智能体运行时](./chapter7/第七章%20构建你的Agent框架.md)

> **阶段交付：** 跑通一个能观察环境、调用工具、验证结果并安全终止的 Agent。

### 第三阶段：上下文与外部能力（第 8–10 章）

8. [RAG 与记忆系统](./chapter8/第八章%20记忆与检索.md)
9. [Context Engineering 与 Loop Engineering](./chapter9/第九章%20上下文工程.md)
10. [MCP、Skills 与 A2A](./chapter10/第十章%20智能体通信协议.md)

> **阶段交付：** 建立按需上下文、可恢复记忆和外部能力接口。

### 第四阶段：优化、评测与安全（第 11–12 章）

11. [Agentic RL 与推理模型](./chapter11/第十一章%20Agentic-RL.md)
12. [环境、评测、可观测性与安全](./chapter12/第十二章%20智能体性能评估.md)

> **阶段交付：** 建立可复现任务集、轨迹、指标、审批和安全门。

### 第五阶段：期中项目（第 13–16 章）

13. [真实任务执行 Agent](./chapter13/第十三章%20智能旅行助手.md)
14. [Deep Research Agent](./chapter14/第十四章%20自动化深度研究智能体.md)
15. [多智能体系统项目](./chapter15/第十五章%20构建赛博小镇.md)
16. [期中项目验收与复盘](./chapter16/第十六章%20期中项目验收与复盘.md)

> **阶段交付：** 完成一个具有证据、审批、审计、评测和失败恢复的期中 Agent 项目。

### 第六阶段：模型原理与后训练（第 17–19 章）

17. [Transformer 数学基础](./chapter17/第十七章%20Transformer数学基础.md)
18. [预训练、优化与模型压缩](./chapter18/第十八章%20预训练优化与模型压缩.md)
19. [对齐与强化学习](./chapter19/第十九章%20对齐与强化学习.md)

> **阶段交付：** 用公式、数值实验和轨迹解释模型如何学习、对齐和改变 Agent 行为。

### 第七阶段：推理与分布式基础设施（第 20–22 章）

20. [GPU 系统与高速互联](./chapter20/第二十章%20GPU系统与高速互联.md)
21. [高性能 LLM 推理](./chapter21/第二十一章%20高性能LLM推理.md)
22. [分布式训练与 RLHF 基础设施](./chapter22/第二十二章%20分布式训练与RLHF基础设施.md)

> **阶段交付：** 能估算内存、带宽、吞吐量和分布式通信成本，并选择合理的训练或推理架构。

### 第八阶段：Agentic UI 与生产系统（第 23–24 章）

23. [Agentic UI 与人在回路](./chapter23/第二十三章%20Agentic%20UI与人在回路.md)
24. [生产 Runtime 与平台工程](./chapter24/第二十四章%20生产Runtime与平台工程.md)

> **阶段交付：** 构建可观察、可审批、可恢复且可运营的生产 Agent 平台。

### 第九阶段：毕业设计（第 25 章）

25. [毕业设计、验收与未来方向](./chapter25/第二十五章%20毕业设计.md)

> **阶段交付：** 交付可复现、可评测、可审计和可发布的最终 Agentic AI 系统。

## 建议的学习方式

每次实践都当作完整闭环：明确任务和权限，观察环境，选择行动，验证结果，记录状态，并在失败时恢复或停止。第 16 章是期中检查点；通过后再决定是先进入生产应用路线，还是完整学习模型与基础设施。

## 来源与许可

Go Agentic 的课程叙事、案例和学习路径均独立编写。课程引用的论文、标准、软件项目以及为链接兼容而保留的材料，均按具体用途标注来源；出处与适用许可见[来源与致谢](./来源与致谢.md)。这些资料提供事实依据或技术背景，不定义本课程的表达与结构。
