# Preface

## Begin with an execution that only looks successful

Imagine a procurement assistant reporting, “The supplier change is complete.” That sentence could come from three very different systems: a model guessed the outcome, a program submitted a request without checking the response, or an agent read the current order, obtained approval, made the change, and queried the target system again. Their prose may be equally fluent, but their engineering credibility is not.

Go Agentic studies the third system. The course treats an agent as a bounded decision loop operating in an environment: it observes state, chooses an action, invokes a tool, checks the outcome, updates its record, and stops when the task succeeds, fails, becomes too risky, or exhausts its budget. The model supplies language and decision capacity; the runtime owns state, permissions, recovery, and audit; the verifier uses evidence to decide whether work is complete. This division of responsibility runs through all 25 chapters.

## One course line from a working loop to production

The sequence follows prerequisite relationships. Chapters 1–3 establish the boundaries among model, agent, harness, runtime, and environment. Chapters 4–7 implement a loop that runs and terminates. Chapters 8–10 add retrieval, memory, context, and external protocols. Chapters 11–12 introduce optimization, evaluation, observability, and safety gates.

Chapters 13–16 put those capabilities into task execution, deep research, and multi-agent projects, then use a midterm review to expose missing evidence and recovery paths. Chapters 17–19 explain model behavior through tokens, attention, training state, and preference objectives. Chapters 20–22 calculate capacity, communication, and cost across GPUs, inference services, and distributed training. Chapters 23–24 connect runtime state to user interfaces and production platforms. Chapter 25 closes the course with a baseline, ablations, a security review, and a reproducibility pack.

The mathematics and systems chapters are part of the application argument. Attention cost changes context policy. KV-cache capacity limits concurrency. Training-data boundaries affect tool-schema compliance. Queues and idempotency determine whether a correct decision produces a safe external result. The capstone collects these local decisions into evidence for an evaluable, auditable, and recoverable system.

## Choose one of three routes

- **Agent application engineering:** Complete Chapters 1–16, then Chapters 23–25. This route suits readers shipping enterprise automation, research, or tool-using agents before they need model training or large-scale infrastructure.
- **Full-stack Agentic AI:** Study Chapters 1–25 in order. Choose this route when you need to explain model behavior, training methods, inference capacity, and production-platform tradeoffs together.
- **Models and systems:** Finish Chapters 1–12, then focus on Chapters 17–22. This route is for readers who already understand agent loops and want depth in Transformers, post-training, GPUs, and distributed systems.

Every route keeps the same safety floor: model output is not an execution result, schema validity is not business validity, aggregate metrics cannot conceal high-risk failures, and consequential side effects require permission, a preview, approval, an idempotency key, and a traceable outcome.

## How to work through the course

Basic Python, command-line use, and model-API concepts are enough for the first 16 chapters. Chapters 17–22 use linear algebra, probability, PyTorch, and computer-systems concepts. Their equations answer measurable engineering questions and do not assume access to a large GPU cluster.

For each chapter, keep a run record containing the task contract, command and environment version, input fixture, actual output, one failed case, the reason for the repair, and the final acceptance result. The maintained offline labs live in `code/go-agentic/` and favor deterministic data, so their core semantics can be checked without paid APIs or large-model downloads. After reading a table or equation, change a parameter, induce a failure, and explain why the system recovers or stops.

Mastery means you can answer four questions: Where is authoritative state? What evidence supports the next action? Which failures are safe to retry? Who or what rule can stop execution? Carry those questions through the course and you will build an engineering method that transfers to new models, tools, and domains.
