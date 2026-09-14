> 本章属于 Go Agentic 双语课程。项目归属与第三方说明见[来源与致谢](../来源与致谢.md)。

# 第七章 现代智能体运行时：以 Pi 为主线

<figure class="course-hero">
  <img src="../assets/visuals/chapter-07.webp" alt="分层控制中枢围绕执行核心协调调度、工具、状态与遥测。" width="1536" height="864" loading="lazy" decoding="async">
  <figcaption><em>自研运行时需要一个治理所有执行边界的控制平面。</em></figcaption>
</figure>

前六章建立了 Task、Environment、Tool、循环、验证与生命周期的基本词汇。本章把这些概念放进一个真实的代码 Harness：[Pi](https://pi.dev/)。Pi 是本章唯一的可执行学习主线，因为它很小的默认表面能够让控制循环清楚可见。DeepSeek Harness 与 Hermes 只在章末作为架构对照出现。

学完本章，你应该能够安全地运行一次 Pi 会话，解释登录修复中的每一次 Tool 转换，分支并恢复会话，区分 Compaction 与删除历史，并在 Skills、Extensions 和 Packages 之间做出选择。

## 7.1 Pi 用很小的 Harness 承担很大的责任

Pi 将自己描述为一个极简终端代码 Harness。它默认暴露给 Agent 的表面很容易画出来：

```text
任务 + 项目指令 + 会话历史
              ↓
           模型决策
              ↓
    read / write / edit / bash
              ↓
       Observation 返回模型
              ↓
      继续、压缩或终止
```

模型提出 Tool 调用；Pi 负责装配会话、执行 Tool、流式输出、中断与持久化。操作系统和项目仍然是 Environment。测试结果或文件读取是 Observation。“缺陷已经修好”这样的模型语句只是主张，直到 Environment 检查验证它为止。

Pi 支持交互、打印或 JSON 输出、RPC 和嵌入式 SDK 四种模式。本章使用交互模式，因为它会直接展示轨迹。

### 7.1.1 四个默认 Tool

| Tool | 能力 | 主要风险 | 好的证据 |
| --- | --- | --- | --- |
| `read` | 读取文件或图片 | 读取无关或敏感数据 | 精确路径与有界内容 |
| `write` | 创建或替换文件 | 覆盖有效工作 | Diff 与下游检查 |
| `edit` | 替换精确文本区域 | 修改错误的匹配项 | 小 Diff 与聚焦测试 |
| `bash` | 执行命令 | 任意副作用 | 退出码与有界输出 |

四个 Tool 足以构成完整的代码循环：`bash` 能检查仓库并运行验证，`read`、`write` 和 `edit` 则让文件修改显式可见。更多 Tool 也许能改善易用性，但也会扩大 Schema、权限和故障表面。

### 7.1.2 UI 背后的不变量

Pi 可以流式显示推理、折叠 Tool 输出或接收中途纠偏消息，但工程不变量始终是：

```python
while not terminated:
    decision = model(context, tools)
    if decision.is_tool_call:
        observation = environment.execute(decision)
        context.append(observation)
    else:
        terminate_with(decision)
```

真实实现还必须校验参数、控制权限、处理 Tool 失败、预留输出 token，并阻止未经验证的循环无限运行。

## 7.2 用明确的信任边界安装与认证

Pi 官方 README 当前推荐：

```bash
npm install -g --ignore-scripts @earendil-works/pi-coding-agent@0.85.1
pi
```

> **版本契约（2026-09-13 核验）：** `npm view @earendil-works/pi-coding-agent name version dist-tags repository --json` 返回包名 `@earendil-works/pi-coding-agent`、版本与 `latest` 均为 `0.85.1`，仓库为 `earendil-works/pi`。本课程的可复制命令固定该精确版本；实际采用前仍应重新核验官方文档和 npm Registry。

`--ignore-scripts` 会禁用依赖生命周期脚本；Pi 说明正常 npm 安装不需要这些脚本。官方安装脚本是另一种选择：

```bash
curl -fsSL https://pi.dev/install.sh | sh
```

将网络内容直接送入 Shell 会立即执行代码。在受控环境中，应先下载并检查脚本，固定获批版本，并记录已安装版本。包名和安装细节可能变化，使用前应查看当前的[官方安装说明](https://github.com/earendil-works/pi/tree/main/packages/coding-agent#quick-start)。

Pi 可以通过 `/login` 使用受支持的订阅，也可以配置 Provider API Key。认证是 Pi 实机路径的外部前提；7.6 节的确定性课程 Fixture 不需要网络或 API Key。

### 7.2.1 从安全工作区开始

第一次运行时：

1. 使用不含生产密钥、可丢弃的小型 Git 仓库。
2. 检查 `git status`，并建立可恢复的基线提交。
3. 只授予任务需要的凭证和目录。
4. 阅读项目指令，并在高影响操作前审查命令。
5. 把第三方 Extensions 和 Packages 当作可执行代码。

Pi 在加载不受信任项目中的本地设置、资源、Extensions 与包管理扩展前，会要求做出项目 Trust 决定。上下文文件仍可能影响模型，因此 Trust 只是多项控制中的一项，并不会使仓库内容自动变得安全。

## 7.3 一条完整的登录修复轨迹

继续使用课程中的重复缺陷：

```python
def normalize_username(username: str) -> str:
    return username  # 应删除首尾空白
```

Task Contract 是：

```text
定位并修复登录用户名标准化失败。
只修改被证据指向的代码。
仅在聚焦测试通过后结束。
```

### 7.3.1 先观察，再编辑

可靠的 Pi 轨迹从 Environment 证据开始：

```text
1. bash  → 运行聚焦的登录测试
2. read  → 查看失败测试与 src/auth/login.py
3. edit  → 将 `return username` 替换为 `return username.strip()`
4. bash  → 重新运行聚焦测试
5. stop  → 报告 Diff 与通过的测试
```

对应的状态流是：

```text
TASK
  ↓
OBSERVE 失败 ──→ INSPECT 源码 ──→ EDIT 最小原因
                                          ↓
                                   VALIDATE 聚焦测试
                                      │           │
                                    失败          通过
                                      │           │
                                      └─ 重试     └─ 完成
```

第一次测试避免猜测式修改。源码读取为改动提供依据。最后的测试是独立证据。如果测试仍失败，新输出会成为下一条 Observation；Agent 必须适应它，而不是重复同一编辑。

### 7.3.2 向 Pi 提供结果、约束与验证器

一条实用的真实提示是：

```text
修复此仓库中失败的用户名标准化登录测试。
先运行最窄的相关测试，并检查被指向的代码。
保持修改最小，保留无关工作，重新运行聚焦测试，
最后给出改动路径和准确的验证结果。
```

这条提示没有规定每个命令。它定义了结果、权限边界和完成证据，同时允许循环根据 Observation 调整行动。

## 7.4 Session 把轨迹变成可恢复状态

Pi Session 自动保存为 JSONL，并形成一棵树：每个条目都有标识符和父链接。因此，会话不是一段扁平聊天记录。

| 操作 | 含义 | 使用时机 |
| --- | --- | --- |
| `/resume` 或 `pi -r` | 打开过去的 Session | 继续中断的工作 |
| `pi -c` | 继续最近的 Session | 快速回到当前任务 |
| `/tree` | 在同一 Session 树中移动到过去节点 | 查看或继续另一分支 |
| `/fork` | 从过去的用户消息创建新 Session | 改写任务但不改变源 Session |
| `/clone` | 把当前活动分支复制到新 Session | 在实验前保存完整当前路径 |

当两个假设需要不同编辑时，Branching 很有用。每个分支都必须携带自己的验证证据；一个分支上的通过结果不能验证另一个分支。

### 7.4.1 Compaction 是有损交接

长 Session 最终会接近模型上下文窗口。Pi 可以自动执行 Compaction，也可以通过 `/compact` 手动触发：旧消息被总结，最近消息保留。完整会话历史仍在 JSONL 文件中，并可通过树重新访问，但后续轮次中模型收到的是压缩表示。

Compaction 必须保存继续任务所需的状态：

```text
目标
已完成工作
决策与约束
未解决的失败
相关路径与证据 ID
下一步行动
```

它应移除重复搜索、已被推翻的假设和庞大 Tool 输出。由于总结有损，关键决定之后应检查压缩状态，并将持久项目事实留在版本化文件或外部系统中。第九章会继续构造这份契约。

## 7.5 Skills、Extensions 与 Packages 改变不同层

Pi 保持核心精简，并提供三个不同的定制边界。

| 机制 | 改变什么 | 典型用途 |
| --- | --- | --- |
| Skill | 按需加载的指令与任务资源 | 评审检查表或部署流程 |
| Extension | 用 TypeScript 实现的运行时行为 | Tool、命令、权限门、UI 组件或压缩策略 |
| Pi Package | Extensions、Skills、提示与主题的分发包 | 通过 npm 或 Git 共享版本化团队流程 |

Agent 需要可重复方法时使用 Skill；执行语义需要变化时使用 Extension；这些资产需要安装、版本管理与复用时使用 Package。Package 可能包含可执行 Extension，因此安装也是供应链决策。

渐进式披露能保持 Context 精简：Pi 最初只暴露 Skill 的名称与描述，仅在 Skill 适用时加载完整指令。这与第九章对文件和证据采用的上下文原则相同。

## 7.6 可执行学习路径

先在仓库根目录运行确定性登录 Fixture：

```bash
python3 -m pytest code/go-agentic/01-minimal-loop/test_agent.py -q
```

它使用假 Policy 和内存工作区，不需要 Provider、API Key、安装包、网络请求或真实文件修改。阅读 `agent.py`，把其中的 `run_tests → read_file → replace_text → run_tests` 轨迹映射到 Pi 的 `bash → read → edit → bash` 路径。

然后，在已经配置 Provider 并准备好可丢弃仓库的前提下，用 Pi 重复这个任务。比较：

- Tool 顺序；
- 第一条失败 Observation；
- 精确编辑；
- 最终验证证据；
- 恢复任务所需的 Session 状态。

确定性 Fixture 教授契约；真实运行展示模型如何在契约内应对不确定性。

## 7.7 架构对照：DeepSeek Harness

根据 2026 年 9 月 13 日核验的官方仓库，[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) 将自身描述为构建在 Cordis 上的“一切皆插件”架构。Model Adapter、Tool、Context Contributor、批准策略、持久化、Sandbox，甚至 Agent Loop 行为都可以在插件边界相遇。当主要设计问题是运行时服务的组合与替换时，这种架构很有参考价值。

Pi 为本课程提供更小的可执行表面；DeepSeek Harness 则展示 Harness 自身变成插件图之后的形态。其官方 README 将项目标记为 Developer Preview，明确预告会有破坏兼容性的变更，并链接单独的安全说明。应把它视为有日期的架构对照，并在采用前重新核验官方文档。

## 7.8 架构对照：Hermes Agent

根据 2026 年 9 月 13 日核验的官方资料，[Hermes Agent](https://github.com/NousResearch/hermes-agent) 把终端 Agent 与持久记忆、Session Search、Skills、定时任务、消息网关、MCP 集成和隔离子智能体组合在一起。当任务需要跨 Session、跨平台和定时唤醒继续运行时，它提供了有用的对照。

Pi 的 Session 树和扩展机制仍是本章学习主线。Hermes 展示长期 Agent 周围还需要哪些运行时服务。第八章会简短回到它的记忆设计；部署前应在 [Hermes 官方文档](https://hermes-agent.nousresearch.com/docs/)中重新核验功能和命令。

## 7.9 本章小结

- Pi 通过四个默认 Tool 让 Observation—Action—Verification 循环清楚可见。
- 安全安装与 Project Trust 能降低供应链和工作区风险，但仍需最小权限与审查。
- 登录修复只有在聚焦的 Environment 检查通过后才算完成。
- Session 保留轨迹，Branching 保留替代方案，Compaction 生成有损的继续状态。
- Skills 教方法，Extensions 改运行时行为，Packages 分发两者。
- DeepSeek Harness 与 Hermes 展示了更广的组合与长期运行问题，但不取代 Pi 工作流。

## 习题

1. 为登录轨迹中的每一项标注 Task、Action、Observation、Validation 或 Termination。
2. 解释为什么成功的 `edit` 结果不能证明登录缺陷已经修好。
3. 为两个互相竞争的登录假设设计 Session 分支，并说明选择胜者需要什么证据。
4. 编写一份 Compaction Record，使任务能在编辑后的第一次测试仍失败时继续。
5. 将以下定制归类为 Skill、Extension 或 Package：评审检查表、自定义数据库 Tool、共享团队套件。
6. 选择一个架构边界比较 Pi 与 DeepSeek Harness 或 Hermes，避免使用功能数量表。

## 掌握标准

当你能够安全启动 Pi 任务，叙述 `read/write/edit/bash` 循环，恢复或分支 Session，审计一次 Compaction 交接，并且只在获得 Environment 证据后结束任务时，就掌握了本章。你还应该能解释 Skill、Extension 与 Package 分别解决什么问题。

## 一手资料

1. [Pi 官方网站与文档](https://pi.dev/docs/latest)
2. [Pi Coding Agent 官方 README](https://github.com/earendil-works/pi/tree/main/packages/coding-agent)
3. [Pi Session 格式](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/session-format.md)
4. [Pi Compaction 原理](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/compaction.md)
5. [Pi Extensions 文档](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md)
6. [DeepSeek Harness 官方仓库](https://github.com/deepseek-ai/deepseek-harness)
7. [DeepSeek Harness 架构](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md)
8. [DeepSeek Harness 安全说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/SAFETY.md)
9. [Hermes Agent 官方仓库](https://github.com/NousResearch/hermes-agent)
10. [Hermes Agent 官方文档](https://hermes-agent.nousresearch.com/docs/)
