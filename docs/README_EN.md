<div align="right">
  <a href="./README.md">中文</a> | English
</div>

# Go Agentic

<figure class="course-hero">
  <img src="./assets/visuals/home.webp" alt="A luminous agent core links five distinct learning territories across a technical course map." width="1536" height="864" loading="lazy" decoding="async">
  <figcaption><em>The course map connects foundations, tools, memory, coordination, and systems engineering.</em></figcaption>
</figure>

> This course is not only about how a model answers. It is about how an agent gathers information, acts in a real environment, verifies outcomes, and completes work within clear boundaries.

Go Agentic is a 25-chapter, hands-on course in full-stack Agentic AI engineering. It first teaches you to build agents that run and verify their work, then moves into model mathematics, post-training, high-performance inference, distributed infrastructure, and production platforms. Pi connects the agent-engineering practice; DeepSeek Harness and Hermes appear only when a different architectural boundary is useful.

- [Repository overview](../README_EN.md)
- [中文课程首页](./README.md)
- [Sources and Acknowledgements](./Sources-and-Acknowledgements.md)

## Choose your learning path

You do not need to learn everything at once. Choose your current goal; the sliding switch at the top remembers it.

<div class="learning-route-grid">
  <article class="learning-route-card recommended" id="route-application">
    <span class="learning-route-badge">RECOMMENDED · SHIP A USEFUL PRODUCT</span>
    <h3>Agent Application Engineering</h3>
    <p>For developers building Agent products, enterprise automation, or Deep Research applications.</p>
    <p class="learning-route-sequence">Chapters 1–16 → Chapters 23–25</p>
    <a class="learning-route-action" href="#/en/chapter1/Chapter1-Introduction-to-Agents.md">Start the application route</a>
  </article>
  <article class="learning-route-card" id="route-fullstack">
    <span class="learning-route-badge">COMPLETE · AGENT TO INFRASTRUCTURE</span>
    <h3>Full-stack Agentic AI</h3>
    <p>For readers mastering models, post-training, inference, distributed systems, and production platforms.</p>
    <p class="learning-route-sequence">Complete Chapters 1–25 in order</p>
    <a class="learning-route-action" href="#/en/chapter1/Chapter1-Introduction-to-Agents.md">Start the full-stack route</a>
  </article>
  <article class="learning-route-card" id="route-systems">
    <span class="learning-route-badge">ADVANCED · BUILD SYSTEMS DEPTH</span>
    <h3>Models and Systems</h3>
    <p>For readers with Agent foundations who want focused Transformer, training, GPU, and distributed-systems depth.</p>
    <p class="learning-route-sequence">Finish Chapters 1–12 → Chapters 17–22</p>
    <a class="learning-route-action" href="#/en/chapter17/Chapter17-Transformer-Mathematics.md">Start with Chapter 17</a>
  </article>
</div>

Not sure yet? Use [Appendix A: Question Bank](./appendices/Appendix-A-Question-Bank.md), then return to choose. Basic Python, command-line, and model-API experience is enough for Chapters 1–16. Chapters 17–22 require more linear algebra, probability, PyTorch, and GPU systems knowledge, but retain a path without a large GPU cluster.

## Learning outcomes

- Design agent loops with tools, recovery, verification, and termination conditions.
- Manage JIT context, compaction, structured state, RAG, and long-term memory.
- Prove agent quality and control with environments, traces, benchmarks, approvals, audits, and replay.
- Explain the mathematics needed for Transformers, pretraining, AdamW, PPO, DPO, and GRPO.
- Diagnose GPU memory, NVLink/InfiniBand, FlashAttention, vLLM, FSDP, and ZeRO bottlenecks.
- Deliver a production agent system with progress, tool streams, evidence, approvals, recovery, and cost/latency SLOs.

## Course path

### Stage I: Agentic AI Foundations (Chapters 1–3)

1. [Introducing Agentic AI](./chapter1/Chapter1-Introduction-to-Agents.md)
2. [Agent History and Modern Runtimes](./chapter2/Chapter2-History-of-Agents.md)
3. [LLM and Systems Foundations for Agents](./chapter3/Chapter3-Fundamentals-of-Large-Language-Models.md)

> **Stage deliverable:** Distinguish model, agent, framework, harness, runtime, and environment boundaries and locate common failures.

### Stage II: Build a Working Agent (Chapters 4–7)

4. [Agent Design Patterns and Loops](./chapter4/Chapter4-Building-Classic-Agent-Paradigms.md)
5. [Tools, Environments, and Agentic RAG](./chapter5/Chapter5-Building-Agents-with-Low-Code-Platforms.md)
6. [Agent Development Lifecycle and Framework Selection](./chapter6/Chapter6-Framework-Development-Practice.md)
7. [Modern Agent Runtimes](./chapter7/Chapter7-Building-Your-Agent-Framework.md)

> **Stage deliverable:** Run an agent that observes an environment, invokes tools, verifies results, and terminates safely.

### Stage III: Context and External Capabilities (Chapters 8–10)

8. [RAG and Memory Systems](./chapter8/Chapter8-Memory-and-Retrieval.md)
9. [Context Engineering and Loop Engineering](./chapter9/Chapter9-Context-Engineering.md)
10. [MCP, Skills, and A2A](./chapter10/Chapter10-Agent-Communication-Protocols.md)

> **Stage deliverable:** Build just-in-time context, recoverable memory, and external capability interfaces.

### Stage IV: Optimization, Evaluation, and Safety (Chapters 11–12)

11. [Agentic RL and Reasoning Models](./chapter11/Chapter11-Agentic-RL.md)
12. [Environments, Evaluation, Observability, and Safety](./chapter12/Chapter12-Agent-Performance-Evaluation.md)

> **Stage deliverable:** Establish reproducible task sets, traces, metrics, approval rules, and safety gates.

### Stage V: Midterm Project (Chapters 13–16)

13. [Real-World Task Execution Agents](./chapter13/Chapter13-Intelligent-Travel-Assistant.md)
14. [Deep Research Agents](./chapter14/Chapter14-Automated-Deep-Research-Agent.md)
15. [Multi-Agent Systems Project](./chapter15/Chapter15-Building-Cyber-Town.md)
16. [Midterm Review and Retrospective](./chapter16/Chapter16-Midterm-Review.md)

> **Stage deliverable:** Complete a midterm agent project with evidence, approval, audit, evaluation, and failure recovery.

### Stage VI: Model Foundations and Post-Training (Chapters 17–19)

17. [Transformer Mathematics](./chapter17/Chapter17-Transformer-Mathematics.md)
18. [Pretraining, Optimization, and Compression](./chapter18/Chapter18-Pretraining-Optimization-and-Compression.md)
19. [Alignment and Reinforcement Learning](./chapter19/Chapter19-Alignment-and-Reinforcement-Learning.md)

> **Stage deliverable:** Use equations, numerical experiments, and trajectories to explain how models learn, align, and change agent behavior.

### Stage VII: Inference and Distributed Infrastructure (Chapters 20–22)

20. [GPU Systems and Interconnects](./chapter20/Chapter20-GPU-Systems-and-Interconnects.md)
21. [High-Performance LLM Inference](./chapter21/Chapter21-High-Performance-LLM-Inference.md)
22. [Distributed Training and RLHF Infrastructure](./chapter22/Chapter22-Distributed-Training-and-RLHF-Infrastructure.md)

> **Stage deliverable:** Estimate memory, bandwidth, throughput, and communication cost and select a defensible training or inference architecture.

### Stage VIII: Agentic UI and Production Systems (Chapters 23–24)

23. [Agentic UI and Human in the Loop](./chapter23/Chapter23-Agentic-UI-and-Human-in-the-Loop.md)
24. [Production Runtime and Platform Engineering](./chapter24/Chapter24-Production-Runtime-and-Platform-Engineering.md)

> **Stage deliverable:** Build an observable, approvable, recoverable, and operable production agent platform.

### Stage IX: Graduation Project (Chapter 25)

25. [Graduation Project, Review, and Future Directions](./chapter25/Chapter25-Graduation-Project.md)

> **Stage deliverable:** Deliver a reproducible, evaluable, auditable, and releasable Agentic AI system.

## How to study

Treat each practice as a complete loop: define the task and permissions, observe the environment, choose an action, verify the result, record state, and recover or stop on failure. Chapter 16 is the midterm checkpoint. After passing it, choose whether to continue directly into production application engineering or complete the model and infrastructure route first.

## Sources and licenses

Go Agentic's course narrative, examples, and learning routes are independently authored. Papers, standards, software projects, and material retained for link compatibility are attributed according to their specific use; [Sources and Acknowledgements](./Sources-and-Acknowledgements.md) records provenance and applicable licenses. These references supply evidence or technical context rather than the course's expression or structure.
