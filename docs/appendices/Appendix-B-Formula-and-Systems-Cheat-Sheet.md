# Appendix B: Formula and Systems Cheat Sheet

This is a calculation and design checklist, not a substitute for the chapters. Normalize units first: label Byte/GiB, distinguish bit/s from Byte/s, state P50/P95/P99, and define what a cost estimate includes.

## B.1 Transformer and Decoding

| Item | Formula/rule | Check |
| --- | --- | --- |
| Scaled attention | $\operatorname{softmax}(QK^T/\sqrt{d_k})V$ | Mask, head shapes, numerical stability |
| Multi-head output | $\operatorname{Concat}(head_1,\ldots,head_h)W^O$ | Commonly $d_{model}=h\times d_{head}$ |
| Cross-entropy | $-\sum_t\log p(y_t\mid y_{<t},x)$ | Mask padding and prompt tokens as intended |
| Temperature | $p_i\propto\exp(z_i/T)$ | $T\to0$ approaches greedy |
| Top-k | Keep the $k$ highest-probability tokens | Fixed candidate count |
| Top-p | Smallest set whose cumulative probability reaches $p$ | Adaptive candidate count |
| Min-p | Keep $p_i\ge p_{min}\max_jp_j$ | Relative threshold |
| Constrained | Permit only grammar/automaton-valid next tokens | Syntax, not factual or business validity |

## B.2 Training, PEFT, and MoE

| Item | Quick reference |
| --- | --- |
| AdamW | $m_t=\beta_1m_{t-1}+(1-\beta_1)g_t$; $v_t=\beta_2v_{t-1}+(1-\beta_2)g_t^2$; decouple weight decay |
| LoRA | $W'=W+BA$, rank $r\ll\min(d_{in},d_{out})$; train about $r(d_{in}+d_{out})$ parameters |
| QLoRA | Freeze a quantized base and train adapters; quantization does not remove all training overhead |
| Packing | Put examples in one sequence while isolating attention and label boundaries |
| MoE | Route top-k experts; inspect capacity, dropped tokens, balance loss, and all-to-all |
| Forgetting/alignment tax | Retain domain, general, safety, and tool-protocol regressions |

Memory ledger:

$$M\approx M_{param}+M_{grad}+M_{optimizer}+M_{activation}+M_{temp}$$

Mixed-precision Adam often holds low-precision parameters, gradients, FP32 master weights, and two moments. “Parameters × 2 bytes” is not a training estimate.

## B.3 Reinforcement and Preference Learning

Finite-horizon convention: $T$ indexes terminal state $s_T$; actions and rewards use indices $0,\ldots,T-1$; $r_t$ belongs to transition $s_t\rightarrow s_{t+1}$; and $V(s_T)=0$. For $t<T$:

| Item | Formula/meaning |
| --- | --- |
| Return | $G_t=\sum_{k=0}^{T-t-1}\gamma^k r_{t+k}$ |
| Advantage | $A_t=Q(s_t,a_t)-V(s_t)$ |
| Policy gradient | $\nabla J=\mathbb{E}[\nabla\log\pi_\theta(a_t\mid s_t)A_t]$ |
| TD error | $\delta_t=r_t+\gamma V(s_{t+1})-V(s_t)$ |
| GAE | $A_t^{GAE}=\sum_{l=0}^{T-t-1}(\gamma\lambda)^l\delta_{t+l}$ |
| PPO ratio | $r_t=\pi_\theta(a_t\mid s_t)/\pi_{old}(a_t\mid s_t)$ with clipping/KL control |
| DPO | Increase the policy-vs-reference log-probability margin of preferred over rejected responses |
| RLVR | Programmatic rewards from tests, compilers, math answers, or rules; defend against reward hacking |

ORM scores outcomes; PRM scores intermediate steps. Verifiable rewards can still have specification gaps. Version policy, reward, verifier, and data.

## B.4 Retrieval and Evaluation

| Metric/method | Formula/meaning |
| --- | --- |
| Reciprocal rank | $RR=1/rank_{first\ relevant}$; MRR is the mean |
| DCG@$k$ | $\sum_{i=1}^{k}(2^{rel_i}-1)/\log_2(i+1)$ |
| nDCG@$k$ | $DCG@k/IDCG@k$ for graded relevance |
| Precision/recall | $P=TP/(TP+FP)$; $R=TP/(TP+FN)$ |
| Token F1 | $2PR/(P+R)$ over token multisets |
| RRF | $score(d)=\sum_j1/(c+rank_j(d))$ to fuse incompatible score scales |
| Exact match | Exact equality after documented normalization |
| Judge agreement | Agreement with human gold or a second evaluator, including slice errors |

Evaluation layers: model capability → retrieval/tool unit → Agent trajectory → task outcome → safety/production. Freeze dataset, seed, model, and tool versions, and retain failures as regressions.

## B.5 Inference Capacity and Performance

$$P_{attainable}=\min(P_{peak},I\times BW),\qquad I=\frac{FLOPs}{Bytes}$$

$$MFU=\frac{Model\ FLOPs}{N_{device}\times Time\times Peak\ FLOP/s/device}$$

Decoder-only KV cache:

$$M_{KV}=2LBSH_{kv}D_hb$$

| Quantity | Meaning |
| --- | --- |
| TTFT | Queue, tokenize, schedule, and prefill time until first token |
| ITL | Delay between output tokens |
| Request throughput | Completed requests per second |
| Token throughput | Input/output tokens per second—state the convention |
| Goodput | Throughput satisfying quality and SLO constraints |

Lifecycle: Gateway → Queue → Tokenize → Prefix Cache → Schedule → Prefill → Decode → Stream → Cleanup. Agent calls insert tool call/result and possible re-prefill phases.

## B.6 Interconnect and Distribution

| Item | Formula/rule |
| --- | --- |
| One-way transfer lower bound | $T\ge Bytes/Bandwidth$; divide Gbit/s by 8 first |
| Ring all-reduce | Ideal per-device traffic $2(N-1)S/N$ |
| Parallel world size | $N=DP\times TP\times PP\times SP$ |
| Sequence shard | Per-rank length $\lceil S/SP\rceil$, with padding if needed |
| Device-hours | $H=N_{device}\times T_{hour}$ |
| First cost estimate | $C=H\times Price_{device/hour}$ |

ZeRO-1 shards optimizer state, Stage 2 gradients too, and Stage 3 parameters too. FSDP gathers/releases fully sharded state around modules. Add activations, buckets, workspaces, fragmentation, and checkpoint peaks.

## B.7 Agent Protocols and Safety

### Tool contracts

- Versioned input/output schemas with types, enums, lengths, and business constraints.
- Separate reads from writes; writes carry idempotency key, target, preview, approval evidence, and outcome state.
- Distinguish validation, permission, conflict, transient, timeout, and unknown-outcome errors.
- Retry only classifiable transient failures; query effect state before retrying writes.

### Event envelope

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

Reconnect from the last acknowledged cursor, deduplicate by event ID, and treat completed/failed/cancelled as terminal. Never drop approvals, permission changes, errors, artifact versions, or terminal events under backpressure.

### Pre-deployment safety checklist

1. Mark external content as untrusted data that cannot raise instruction priority.
2. Deny by default; grant the smallest tool/resource/field/time scope.
3. Before high-risk effects, show target, full preview, evidence, reversibility, and decision scope.
4. Keep secrets out of prompts, logs, errors, and artifacts.
5. Record request, decision evidence, tool version, argument summary, approval, and outcome.
6. Red-team injection, privilege escalation, exfiltration, replay, races, and unknown outcomes.
7. Prepare compensation and human escalation for irreversible actions.
