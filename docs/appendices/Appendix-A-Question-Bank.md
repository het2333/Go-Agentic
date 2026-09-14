# Appendix A: Question Bank

Use these questions to test whether you can turn concepts into system decisions. Answer before reading the key. Open design questions admit multiple implementations, but a complete answer must define state, evidence, failure boundaries, and acceptance checks.

## A.1 Foundations and Models

1. Why is a chatbot that calls one tool not necessarily an Agent? Name four states in a minimal loop.
2. What uncertainty suits ReAct, Plan-and-Execute, and Reflection? When does reflection only add cost?
3. Why can incorrect chat templates or special tokens break tool use when weights are unchanged?
4. Compare greedy, top-p, and constrained decoding by their primary goal.
5. Why divide attention logits by $\sqrt{d_k}$, and what does a causal mask enforce?
6. What separate problems do SFT completion masks, packing, and padding solve?

## A.2 Tools, Context, and Memory

7. Define schemas, idempotency keys, and error classes for “read order, then send approved email.”
8. Why is prompt injection a data/control-boundary problem rather than merely prompt wording?
9. How do one-shot RAG and Agentic Search differ in control flow, and when should search stop?
10. Where do multi-query, HyDE, RRF, and cross-encoder reranking fit in retrieval?
11. Distinguish working, episodic, semantic memory, and external sources of truth. Which authorizes a side effect?
12. Which five information classes must survive long-task compaction?

## A.3 Optimization, Learning, Evaluation, and Safety

13. How do self-consistency, Best-of-N, Tree of Thoughts, and MCTS trade inference cost for quality?
14. Why does a high offline benchmark score not prove deployment readiness? Name four end-to-end metric classes.
15. How do MRR and nDCG differ? When is token F1 preferable to exact match?
16. How would you detect order, verbosity, and self-preference bias in LLM-as-Judge?
17. What feedback signals do PPO, DPO, KTO, and RLVR require?
18. How do ORM and PRM supervision differ, and how can a flawed process reward be gamed?
19. Explain how least privilege, approval gates, sandboxing, audit, and compensating actions form defense in depth.

## A.4 Systems, UI, and Production

20. Use Roofline to separate memory- from compute-bound work. Why does low MFU not prove insufficient compute?
21. Why do prefill and decode behave differently? What experiences do TTFT and inter-token latency measure?
22. Which dimensions determine KV-cache size, and why do GQA/MQA reduce it?
23. What do DP, TP, PP, and SP partition, and which dimensions most need fast intra-node links?
24. Which resident states do ZeRO-3/FSDP reduce, and why can a theoretical fit still OOM?
25. Which fields belong in a reconnectable UI event envelope? Which events must survive backpressure?
26. Why should Generative UI emit allowlisted component schemas rather than arbitrary HTML/JavaScript?
27. How would you define SLO, circuit-breaker, degradation, retry, and rollback boundaries?

## A.5 Integrated Design Questions

28. Design a procurement execution Agent: state machine, sources, approvals, idempotency, recovery, and five metrics.
29. Design a Deep Research Agent: query decomposition, source quality, evidence alignment, contradiction handling, and stopping.
30. Before splitting one Agent into many, state three required benefit signals and three new risks.
31. Create a 128K online-serving capacity plan covering weights, KV cache, concurrency, admission control, P95, and cost.
32. Define policy version, trajectory lineage, maximum staleness, checkpoint publication, and gates for asynchronous RLHF.

## A.6 Practice Routes

| Route | Chapter sequence | Route outcome |
| --- | --- | --- |
| Agent Application Engineering | 1–16 → 23–25 | Ship an evaluated Agent product with UI, approvals, recovery, and production controls |
| Full-stack Agentic AI | 1–25 in order | Connect Agent engineering with model, training, inference, distributed-systems, and production evidence |
| Models and Systems | Complete 1–12 → 17–22 | Add Transformer, post-training, GPU, inference, and distributed-systems depth to established Agent foundations |

## A.7 Answer Key

1. An Agent observes, decides, acts, updates state, and checks continuation/termination; one call has no persistent loop.
2. ReAct supports local exploration, Plan-and-Execute decomposable long work, and Reflection verifiable correction. Reflection without new evidence or a checker tends to paraphrase.
3. Templates define roles and tool protocol; special tokens define boundaries and termination. Misalignment breaks the learned control format.
4. Greedy favors determinism, top-p samples within cumulative probability mass, and constrained decoding guarantees syntax/schema—not semantic correctness.
5. Scaling controls variance and softmax saturation. Causal masking prevents future-token access and preserves autoregressive factorization.
6. Completion masks select supervised targets, packing improves token utilization while isolating examples, and padding aligns shapes without contributing loss.
7. Bound order ID, recipient, body, and approval token; reads expose retryable errors, while writes use business idempotency and distinguish denied, conflict, timeout, and unknown outcome.
8. Untrusted text must not gain instruction authority or tool permission. Source labeling, isolation, allowlists, validation, and approvals enforce the boundary.
9. One-shot RAG fixes top-k before reasoning; Agentic Search revises query/source from evidence. Stop on sufficient evidence, low marginal value, budget, or irreducible conflict.
10. Multi-query/HyDE generate candidate queries or representations, RRF fuses rankings, and cross-encoders rerank candidates.
11. Working memory stores current state, episodic memory experiences, semantic memory abstractions, and external systems re-verifiable facts. None bypass current authorization.
12. Goal/constraints, sourced facts, completed actions/side effects, open questions/risks, and next action/acceptance criteria.
13. The first two sample whole answers, ToT preserves explicit branches, and MCTS allocates budget through select-expand-evaluate-backup. Extra search only helps with a discriminating evaluator.
14. Include task success, trajectory/tool correctness, safety violations, latency, cost, recovery, and user edits.
15. MRR emphasizes the first relevant result; nDCG supports graded multiple results. Token F1 handles equivalent tokenization and partial overlap.
16. Randomize order, control length, blind model identity, compare with human gold, and measure agreement; cross-check judges with rules or ensembles.
17. PPO uses online returns/advantages, DPO preference pairs, KTO single desirable/undesirable labels, and RLVR programmatically verifiable outcomes.
18. ORM scores whole outputs; PRM scores intermediate steps. Weak PRMs reward verbosity, fake steps, or plausible-looking traces.
19. Permissions bound capability, sandboxes impact, approvals intent, audit evidence, and compensation handles irreversible external effects.
20. Compare arithmetic intensity with the ridge point. Memory, communication, CPU stalls, fragmentation, synchronization, or imbalance can also lower MFU.
21. Prefill is parallel and often compute-heavy; decode repeatedly reads weights/cache and is often bandwidth-heavy. TTFT measures initial wait and ITL stream fluency.
22. Layers, batch, sequence, KV heads, head dimension, and precision determine size. GQA/MQA shares fewer KV heads among query heads.
23. DP splits batch, TP layer tensors, PP layers, and SP sequence/activations. Frequent intra-layer TP/SP communication most needs fast links.
24. They shard parameters, gradients, and optimizer state. Activations, transient gathers, buckets, workspaces, and fragmentation remain.
25. Include task ID, sequence, event ID, type, schema version, and timestamp. Never drop approvals, permissions, artifact versions, errors, or terminal state.
26. Schemas validate components, fields, and permissions while the app owns rendering and effects; arbitrary code expands injection, XSS, and privilege risk.
27. SLO covers success, tails, recovery, and cost. Retry only classifiable transient faults, break persistent failures, expose degradation, and compensate or version-rollback risky writes.
28–32. Check every named dimension. Missing state boundaries, source/version lineage, failure paths, or quantitative metrics makes the design incomplete.
