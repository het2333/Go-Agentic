# 单文件原生 Coding Agent

`coding_agent.py` 是一个可以调用真实模型、读写真实文件、运行真实程序的单文件教学版 Coding Agent。Python 3.10+，只用标准库，无需安装 SDK、LangChain 或 LangGraph。

安全文件工具目前支持具备 `dir_fd`、文件描述符目录遍历、`O_NOFOLLOW` 和 `O_DIRECTORY` 的 POSIX 平台（常见的 Linux 与 macOS）。程序启动时会检查这些能力；不支持的平台会在访问文件前明确停止，不会退回到先检查路径再按路径名打开的不安全实现。绝对工作目录从已打开的文件系统根描述符开始，按组件逐级打开；相对工作目录先绑定当前目录描述符，再逐级打开。所有根路径组件都禁止跟随符号链接，含 `..` 的根路径会被拒绝。日志显示的工作目录路径只是说明信息，文件工具的访问权只来自已经绑定的根描述符。

## 先跑起来

在仓库根目录运行：

```bash
cd code/go-agentic/01-minimal-loop

# 填入你的服务配置。MODEL 必须支持 Chat Completions 的 function calling。
export OPENAI_API_KEY='你的 API Key'
export OPENAI_MODEL='你有权限使用的模型 ID'
export OPENAI_BASE_URL='https://api.openai.com/v1'

# 复制练习到临时目录，后续修改发生在这个副本里。
exercise_dir=$(mktemp -d)
cp demo/*.py "$exercise_dir/"

python3 coding_agent.py \
  --workspace "$exercise_dir" \
  --allow-run \
  '运行 python3 check_hello.py，分析失败原因，只修改 hello.py 修复问题，不改检查文件。最后重新运行检查并用中文解释。'
```

这些环境变量也可配置兼容服务；`OPENAI_BASE_URL` 是 API 根地址，程序会追加 `/chat/completions`，并把 `OPENAI_API_KEY` 作为 Bearer 凭证发送给该地址。远程地址必须使用 HTTPS；只有 `localhost` 或回环 IP 可使用 HTTP，供本地测试和开发。程序拒绝 3xx 重定向且不会访问重定向目标，避免把 Bearer 凭证带到另一个地址。本程序不自动读取 `.env` 文件。模型必须同时支持该接口和工具调用，并非所有模型都适用；例如官方文档注明 GPT-6 Astra 的工具调用需要 Responses API，不能直接用在这个示例中。

不带 `--allow-run` 时仍可读写文件，但不会向模型提供命令工具。启用后程序以当前用户权限执行，`--workspace` 只为命令设置起始目录，不是操作系统沙箱。因此第一次使用建议按上述命令操作临时练习目录。

子进程不会继承完整环境。程序只转发当前已设置的 `PATH`、`HOME`、`LANG`、`LC_ALL`、`LC_CTYPE`、`TMPDIR` 和 `TERM`；`OPENAI_API_KEY` 以及其他未列出的 token、凭证和配置变量不会传入命令。这个环境最小化不能限制命令读取当前用户可访问的文件或网络资源。

练习原文件有意保留 bug。预期轨迹如下，具体调用顺序由模型决定：

```text
run_command(["python3", "check_hello.py"])
  ← exit_code=1，AssertionError
read_file("hello.py")
  ← return username
write_file("hello.py", "...return username.strip()...")
  ← 已写入
run_command(["python3", "check_hello.py"])
  ← exit_code=0，PASS: 4 cases
最终回答：说明修改和验证结果
```

你也可以自己检查它的修改：

```bash
cat "$exercise_dir/hello.py"
(cd "$exercise_dir" && python3 check_hello.py)
```

## 最值得看懂的循环

先打开 `coding_agent.py` 的 `run_agent()`。把日志和异常处理暂时略去，它做的就是下面这些事；这是简化示意，完整可运行版本在文件里：

```python
messages = [system_message, user_message]
for step in range(max_rounds):
    message = model(messages, tools)
    messages.append(message)
    if not message.get("tool_calls"):
        return message["content"]
    for call in message["tool_calls"]:
        observation = workspace.execute(call)
        messages.append({
            "role": "tool",
            "tool_call_id": call["id"],
            "content": observation,
        })
```

1. **`messages` 是这一趟任务的记忆。** 每一轮都会重新把累积的对话发给模型，包括之前的工具结果。
2. **`tools` 告诉模型有什么能力。** JSON Schema 描述工具名称和参数，Python 函数负责真正执行。Schema 本身不会读写文件。
3. **模型输出一个决定。** 它可以返回普通文本，也可以返回带有名称和 JSON 参数的 `tool_calls`。不需要从自然语言里猜它想调用什么。
4. **你的程序执行这个决定。** `Workspace.execute()` 校验参数，通过固定映射找到函数，然后实际操作文件或启动子进程。
5. **Observation 让下一轮有了新证据。** `tool_call_id` 关联“这次请求”和“这次结果”。必须先保存 assistant 消息，再追加所有对应的 tool 消息。
6. **不再调用工具，就结束。** 普通文本表示模型选择结束；它本身不能证明任务成功，仍要看实际修改及测试输出。

这里最关键的区别是：下一步并没有预先写死成“读 → 改 → 测”。代码只提供循环和工具，模型根据当前 `messages` 决定接下来做什么。

## 四个工具

| 工具 | 参数 | 实际效果 |
| --- | --- | --- |
| `list_files` | `path` | 列出一个目录的直接子项 |
| `read_file` | `path` | 读取 UTF-8 文件 |
| `write_file` | `path`, `content` | 创建或覆盖完整文件 |
| `run_command` | `argv` | 启动程序，返回退出码和合并后的标准输出、错误输出 |

`argv` 是数组，如 `["python3", "check_hello.py"]`。程序不启用 shell，`&&`、重定向和通配符不会自动展开。文件工具从启动时绑定的工作目录描述符逐级打开路径，每一级和最终目标都禁止跟随符号链接；写入时创建父目录也使用同一套描述符相对操作，避免检查与打开之间的路径替换。它仍不是操作系统沙箱，命令执行也不具有这层文件边界。

## 已加上的最小保护与局限

- 默认最多 **12 次模型调用**，每轮最多 8 个工具调用；用 `--max-rounds` 调整轮数。用尽轮数会明确停止，之前的修改保留。
- 单条命令默认 **30 秒超时**；API 请求超时设置为 60 秒。模型 API 出错会停止，工具错误则回传成 `TOOL_ERROR`，让模型有机会纠正。
- 工具输出超过 **12,000 字符**会截断。这个版本适合小文件；对大文件要增加分段读取和精确替换工具，避免基于不完整内容覆盖原文件。
- 对话仅存在内存中，无跨次运行记忆，也没有上下文压缩、自动回滚或独立任务验收器。轮数上限不等于精确的 token 或费用预算。
- 终端日志会显示工具名称、参数和 observation，其中可能包含任务文本或文件内容。不要把敏感数据放进练习目录或任务提示。

## 离线验证

测试需要 pytest，Agent 本身不需要。下面在本目录执行，无需 API Key：

```bash
python3 -m pytest test_coding_agent.py test_agent.py -q
```

`test_coding_agent.py` 用本地回环 HTTP 服务模拟模型输出，实际执行 HTTP 请求、文件读写和 Python 子进程，检查请求头、重定向拒绝、HTTP/传输错误、响应格式、多轮消息关联、工具错误恢复、根路径与运行期符号链接竞争、并发关闭、环境变量最小化、输出截断、超时和停止行为。它验证程序的机制，不代表真实模型一定能解决所有任务。

原有 `agent.py` 使用固定规则和内存中的文件，适合理解最初的概念；`coding_agent.py` 将这些位置换成真实 API 和真实环境。读完 `run_agent()`，再依次阅读 `TOOLS`、`Workspace.execute()` 和 `ChatModel.__call__()`。

工具调用协议参考：[OpenAI 官方 Function calling 文档](https://developers.openai.com/api/docs/guides/function-calling)。
