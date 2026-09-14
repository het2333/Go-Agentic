# 附录 B 公式与系统速查

本附录是计算与设计检查表，不替代正文。先统一单位：容量优先标明 Byte/GiB，带宽区分 bit/s 与 Byte/s，延迟说明 P50/P95/P99，成本说明计费范围。

## B.1 Transformer 与解码

| 项目 | 公式/规则 | 检查点 |
| --- | --- | --- |
| Scaled Attention | $\operatorname{softmax}(QK^T/\sqrt{d_k})V$ | Mask、Head Shape、数值稳定性 |
| 多头拼接 | $\operatorname{Concat}(head_1,\ldots,head_h)W^O$ | $d_{model}=h\times d_{head}$（常见但非唯一） |
| 交叉熵 | $-\sum_t \log p(y_t\mid y_{<t},x)$ | Padding/Prompt Token 是否被 Mask |
| Temperature | $p_i\propto\exp(z_i/T)$ | $T\to0$ 趋近 Greedy；高温增随机性 |
| Top-k | 仅保留概率最高的 $k$ 个 Token | 固定候选数，不保证概率质量 |
| Top-p | 保留累计概率达到 $p$ 的最小集合 | 候选数随分布变化 |
| Min-p | 保留 $p_i\geq p_{min}\max_j p_j$ | 相对最高概率阈值 |
| Constrained | 只允许自动机/Grammar 的合法下一 Token | 保证格式，不保证事实与业务合法 |

## B.2 训练、参数高效微调与 MoE

| 项目 | 速查 |
| --- | --- |
| AdamW | $m_t=\beta_1m_{t-1}+(1-\beta_1)g_t$；$v_t=\beta_2v_{t-1}+(1-\beta_2)g_t^2$；权重衰减与梯度更新解耦 |
| LoRA | $W'=W+BA$，秩 $r\ll\min(d_{in},d_{out})$；训练参数约为 $r(d_{in}+d_{out})$ |
| QLoRA | 冻结量化基座，反向传播到 LoRA Adapter；量化节省不等于训练零开销 |
| Packing | 多样本放入同一序列，必须隔离 Attention/Label 边界 |
| MoE | Router 选择 Top-k Expert；检查 Capacity、Dropped Token、负载均衡损失与跨卡 All-to-All |
| 遗忘/Alignment Tax | 同时保留领域任务、通用能力、安全和工具协议回归集 |

模型状态粗略显存账本：

$$M\approx M_{param}+M_{grad}+M_{optimizer}+M_{activation}+M_{temp}$$

混合精度 Adam 常同时存在低精度参数、梯度、FP32 Master Weight 和两个 Moment；不要只用“参数量 × 2 Byte”。

## B.3 强化学习与偏好优化

有限时域约定：$T$ 是终止状态 $s_T$ 的下标，Action 与 Reward 使用 $0,\ldots,T-1$，$r_t$ 属于 $s_t\rightarrow s_{t+1}$ 这次转移，并令 $V(s_T)=0$。对 $t<T$：

| 项目 | 公式/含义 |
| --- | --- |
| Return | $G_t=\sum_{k=0}^{T-t-1}\gamma^k r_{t+k}$ |
| Advantage | $A_t=Q(s_t,a_t)-V(s_t)$ |
| Policy Gradient | $\nabla J(\theta)=\mathbb{E}[\nabla\log\pi_\theta(a_t\mid s_t)A_t]$ |
| TD Error | $\delta_t=r_t+\gamma V(s_{t+1})-V(s_t)$ |
| GAE | $A_t^{GAE}=\sum_{l=0}^{T-t-1}(\gamma\lambda)^l\delta_{t+l}$ |
| PPO Ratio | $r_t(\theta)=\pi_\theta(a_t\mid s_t)/\pi_{old}(a_t\mid s_t)$，配合 Clip/KL 限制更新 |
| DPO | 提高偏好回答相对拒绝回答的策略—参考对数概率差 |
| RLVR | Reward 由编译、单测、数学答案或规则检查器提供；重点防止 Reward Hacking |

ORM 对完整结果评分，PRM 对中间步骤评分；可验证不代表奖励定义无漏洞。记录 Policy/Reward/Verifier/Data Version。

## B.4 检索与评测

| 指标/方法 | 公式/解释 |
| --- | --- |
| Reciprocal Rank | $RR=1/rank_{first\ relevant}$；MRR 是其平均 |
| DCG@$k$ | $\sum_{i=1}^{k}(2^{rel_i}-1)/\log_2(i+1)$ |
| nDCG@$k$ | $DCG@k/IDCG@k$，适合分级相关性 |
| Precision/Recall | $P=TP/(TP+FP)$；$R=TP/(TP+FN)$ |
| Token F1 | $2PR/(P+R)$，按 Token 多重集合重合计算 |
| RRF | $score(d)=\sum_j1/(c+rank_j(d))$，融合不同量纲排序 |
| Exact Match | 规范化后完全一致；严格但可复现 |
| Judge Agreement | 与人工金标或第二评审的一致率，并报告分组误差 |

评测分层：模型能力 → 检索/工具单元 → Agent 轨迹 → 任务结果 → 安全/生产。每次回归固定数据版本、随机种子、模型与工具版本，并把失败样本保留下来。

## B.5 推理容量与性能

Roofline：

$$P_{attainable}=\min(P_{peak}, I\times BW),\qquad I=\frac{FLOPs}{Bytes}$$

$$MFU=\frac{Model\ FLOPs}{N_{device}\times Time\times Peak\ FLOP/s/device}$$

Decoder-only KV Cache：

$$M_{KV}=2LBSH_{kv}D_hb$$

| 量 | 含义 |
| --- | --- |
| TTFT | 排队、Tokenize、调度与 Prefill 后首 Token 时间 |
| ITL | 相邻输出 Token 延迟 |
| Request Throughput | 每秒完成请求数 |
| Token Throughput | 每秒输入/输出 Token 数，必须说明口径 |
| Goodput | 满足质量与 SLO 的有效吞吐 |

完整链路：Gateway → Queue → Tokenize → Prefix Cache → Schedule → Prefill → Decode → Stream → Cleanup。Agent 还会插入 Tool Call/Result 与再次 Prefill。

## B.6 互联与分布式

| 项目 | 公式/规则 |
| --- | --- |
| 单向传输下界 | $T\ge Bytes/Bandwidth$；若带宽是 Gbit/s，先除以 8 |
| Ring All-Reduce | 每卡理想流量 $2(N-1)S/N$ |
| 并行世界大小 | $N=DP\times TP\times PP\times SP$ |
| Sequence Shard | 每卡长度 $\lceil S/SP\rceil$，必要时 Padding |
| Device Hours | $H=N_{device}\times T_{hour}$ |
| 粗略成本 | $C=H\times Price_{device/hour}$ |

ZeRO-1 分优化器，Stage 2 再分梯度，Stage 3 再分参数。FSDP 按模块收集/释放全分片状态。两者都要另算激活、Bucket、Workspace、碎片与 Checkpoint 峰值。

## B.7 Agent 协议与安全

### 工具契约

- 输入/输出使用版本化 Schema，字段有类型、枚举、长度和业务约束；
- 读写分离，写操作包含 Idempotency Key、Target、预览、审批证据和结果状态；
- 错误至少区分 Validation、Permission、Conflict、Transient、Timeout、Unknown Outcome；
- 重试只覆盖可判定的瞬时失败，写操作先查询是否已生效。

### 事件 Envelope

```json
{
  "task_id": "t-42",
  "sequence": 17,
  "event_id": "e-17",
  "type": "approval_requested",
  "schema_version": 1,
  "timestamp": "2026-09-13T10:00:00Z",
  "payload": {}
}
```

重连使用最后确认 Cursor；按 Event ID 去重；Completed/Failed/Cancelled 为终局。审批、权限变化、错误、产物版本和终局事件不可因背压丢弃。

### 上线前安全清单

1. 外部内容始终标记为不可信数据，不能提升指令优先级；
2. 默认拒绝，按任务授予最小工具、资源、字段和时限；
3. 高风险副作用在执行前显示目标、完整预览、依据、可逆性与范围；
4. Secret 不进入 Prompt、日志、错误页和产物；
5. 记录请求、决策依据、工具版本、参数摘要、审批和结果；
6. 红队覆盖 Prompt Injection、越权、数据外泄、重放、并发冲突和结果未知；
7. 为不可撤销动作准备补偿流程和人工升级入口。
