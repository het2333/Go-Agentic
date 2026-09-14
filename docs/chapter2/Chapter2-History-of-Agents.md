<div align="right">
  <a href="./第二章%20智能体发展史.md">中文</a> | English
</div>

# Chapter 2: Agent History and Modern Runtimes

<figure class="course-hero">
  <img src="./assets/visuals/chapter-02.webp" alt="Three mechanical forms trace the evolution from reactive automation to adaptive agent runtime." width="1536" height="864" loading="lazy" decoding="async">
  <figcaption><em>Agent runtimes evolved by adding planning, tools, memory, and adaptation.</em></figcaption>
</figure>

Agents did not suddenly appear in the LLM era. Symbolic systems, expert systems, and reinforcement learning had already studied how a system chooses actions from an environment. The modern shift is that language models provide a general language decision interface, tool calling connects decisions to software, and harnesses and runtimes make the loop controllable, observable, and persistent.

By the end of this chapter, you should be able to:

- state the central contribution of symbolic AI, expert systems, reinforcement learning, and LLM agents;
- explain why ELIZA creates an impression of dialogue without a modern agent loop;
- explain how tool calling, context windows, harnesses, and runtimes form the modern stack;
- place Pi in a Model—Harness—Runtime—Environment stack without assigning product capabilities to the model.

## 2.1 A Selective Historical Line

### 2.1.1 Symbols, Search, and Expert Systems

Early symbolic AI represented intelligent behavior with symbolic structures and rule operations. Newell and Simon's physical symbol system view emphasized that problem solving could be described with states, operators, and search. This tradition left engineering habits that still matter: represent state explicitly, constrain the available operations, and record the decision path.

ELIZA used keywords, decomposition rules, and reassembly templates to produce dialogue. Its core can be reduced to:

```text
read input
→ find the highest-priority keyword
→ match a sentence pattern
→ apply a response template
→ use a generic response if nothing matches
```

Its value was showing how a small rule set could create a strong interactive impression. Its boundary was equally clear: no open environment, tool action, result verification, or persistent goal-directed state. Mistaking “sounds conversational” for “understands and completes tasks” is the issue Weizenbaum raised in the original paper and later discussion.

Expert systems applied symbolic rules to narrow professional domains. DENDRAL combined chemical knowledge with candidate search, while MYCIN used rules and uncertainty weights to assist infection diagnosis. They demonstrated the value of domain knowledge and explanation chains, while exposing expensive knowledge acquisition, brittle rules, and weak transfer across domains. Modern tool schemas, policy rules, and safety checks retain the idea that critical constraints should be explicit.

### 2.1.2 Reinforcement Learning: From Rules to Interaction

Reinforcement learning writes the problem as sequential interaction between an Agent and an Environment:

```text
state s_t → action a_t → reward r_(t+1), state s_(t+1)
```

A policy chooses an action from state, and the environment returns a new state and reward. Q-learning showed how action values can be learned from interaction; AlphaGo combined policy networks, value networks, and tree search to achieve a breakthrough in the bounded environment of Go.

This line contributed three ideas to modern agents:

1. the current action changes future observable state;
2. evaluation should examine a complete trajectory, not only one output;
3. exploration must be bounded by the environment, reward, and budget.

An LLM agent usually does not update model weights during each user task, but it does adapt later actions from observations in the trace. This is in-context adaptation and should not be confused with training.

### 2.1.3 LLM Agents: Language as the Decision Interface

The Transformer enabled models to handle long-range dependencies in context; large-scale language modeling then brought instruction following, few-shot adaptation, and code generation. Work such as ReAct interleaved reasoning traces and environment actions, allowing a language model to query external information and continue from the returned result.

The key change is not that a model receives operating-system authority. It is that a software system can:

- describe a goal, tools, and observations through messages;
- receive text or a structured tool request;
- execute the request in a host program;
- return the tool result to the model as a new message;
- decide whether to continue using verification, budget, and approval rules.

A modern agent is therefore the joint result of model capability and systems engineering.

## 2.2 Why the Modern Stack Formed

### 2.2.1 Tool Calling Connects Language to Action

Tool calling lets a model emit a structured intent that names a tool and supplies arguments. The executor is always the harness or application. It must validate the tool name and arguments, check authority, execute code, and return an observable result.


Providers differ in message roles, supported schema subsets, parallel calls, and error formats. A framework or provider adapter can normalize some differences, but the application must still test its own boundary.

### 2.2.2 The Context Window Becomes Working State

An LLM generates each response only from the context in the current request. System instructions, the user goal, tool definitions, message history, and tool results all consume the context window. A larger window can carry a longer trace, but irrelevant logs, stale assumptions, and conflicting instructions also enter the decision.

This produced context selection, summarizing compaction, session branching, and external memory. A context window is a finite input budget, not a reliable database; a cache is an optimization for repeated prefixes, not memory. Chapters 8–9 develop these capabilities.

### 2.2.3 Harness and Runtime Turn Calls into a System

One “model → tool → model” exchange is a single interaction. A harness adds the loop, tool registration, observation wrapping, verification, error handling, approvals, and trace logs. A runtime then owns session persistence, process lifecycle, resources, concurrency, recovery, and the user interface.

| Layer | Typical state | Typical failure |
| --- | --- | --- |
| Model / Provider | Messages, sampling parameters, model response | Timeout, rate limit, invalid structure |
| Harness | Tool table, loop state, budget, verification result | Wrong dispatch, infinite loop, false completion |
| Runtime | Session, process, persistence, concurrent resources | Crash, failed recovery, state conflict |
| Environment | Files, tests, browser, business API | Permission denial, changed data, tool error |

This layering locates responsibility. A model choosing the wrong tool and a tool failing during execution are different problems; a harness missing a step budget and a model occasionally repeating an action are different problems.

## 2.3 Contemporary Example: Pi's Boundary

### 2.3.1 Why It Is the Course Mainline

Pi's official documentation describes its coding agent as a “minimal terminal coding harness.” Its default tools are `read`, `write`, `edit`, and `bash`, with Sessions, Branching, Compaction, Skills, Extensions, and Packages for extension. The official repository also separates the multi-provider model API, Agent Core, and interactive Coding Agent CLI into distinct packages.

Those are project facts. “Pi is suitable for learning from the minimal loop outward” is Go Agentic's teaching choice. The course will not present third-party extensions as Pi core capabilities, and it will not turn Pi, DeepSeek Harness, and Hermes into three parallel tutorials.

### 2.3.2 How the Login Failure Moves Through the Stack

In the modern stack, the Chapter 1 trace still assigns each responsibility to a separate layer.


The model or fake policy proposes the next step; the harness executes and controls it; the repository and test process form the environment; and a passing test is verification evidence. This division of responsibility remains stable in later chapters.

## 2.4 Read the History Through One Operating Trace

The historical strands become concrete when they are assigned to different moments in one loop:

| Loop stage | Inherited capability | Engineering limit to retain |
| --- | --- | --- |
| Observe | Symbolic systems make task state and available operators explicit | A representation omits anything its designer did not encode |
| Decide | Search, learned value estimates, and language models offer different ways to select a next move | A plausible choice still needs bounded authority |
| Act | Templates, domain procedures, and typed Tool Calls turn a choice into an operation | Execution belongs to the hosting system and Environment |
| Verify | Rewards evaluate trajectories; modern task systems can also check tests, queries, approvals, or postconditions | Training reward and runtime proof answer different questions |

Consider an Agent triaging a failed overnight inventory import. It first observes an error code and the affected batch ID. A symbolic rule classifies the code as a schema family; a learned ranker orders likely causes; the language model decides which bounded diagnostic Tool to call. The Harness executes a read-only schema comparison and returns the mismatch as a new Observation. After a repair is authorized and applied, an independent row-count and checksum query verifies the import. No historical technique owns the entire trace; each contributes at a boundary where it can be inspected.

This view also prevents a common category error. Updating an LLM's weights during training, selecting an Action from the current Context, and verifying an external postcondition are three separate mechanisms even when all three use feedback.

## 2.5 Chapter Summary

- The historical through-line is “represent state—choose an action—read environment feedback”; LLMs changed the decision interface and useful scope.
- ELIZA is a rule-based dialogue program without open tools, verification, or a goal loop.
- Expert systems contributed explicit knowledge; reinforcement learning contributed sequential interaction and trajectory evaluation.
- Tool Calling, Context Windows, Harnesses, and Runtimes jointly form the modern agent stack.
- Pi is the course's sole practical mainline, and factual project claims come from its official repository.

## Exercises

1. Compare ELIZA, a Q-learning agent, and the Chapter 1 login fixture using four fields: state, action, feedback, and termination.
2. Choose one expert-system rule and place it in a prompt, a tool validator, and a fixed workflow. Compare how testable the three placements are.
3. For a failure where “the model returns a nonexistent tool name,” state what the Model, Provider Adapter, Harness, and Environment layers should each record.
4. Using the diagram in 2.3, mark which login-task state belongs in context, which belongs in the Runtime, and which exists only in the Environment.

## Mastery Standard

You meet this chapter's standard when you can explain the inheritance from symbolic rules through environment interaction to language decisions in one coherent historical line; decompose a modern agent product into Model, Harness, Runtime, and Environment; and assign a failure to the responsible layer.

## Historical Evidence Map

The following groups connect historical sources to the engineering capabilities inherited by the modern loop:

| Loop question | Historical evidence | Use in this chapter |
| --- | --- | --- |
| What state can be observed and represented? | Newell and Simon (1976), [ACM record](https://dl.acm.org/doi/10.1145/360018.360022); Weizenbaum (1966), [ACM record](https://dl.acm.org/doi/10.1145/365153.365168); Lindsay et al. (1980), [DTIC record](https://apps.dtic.mil/sti/citations/ADA095109); Shortliffe and Buchanan (1975), [journal record](https://doi.org/10.1016/0025-5564%2875%2990047-4) | Symbolic representations, rule-bound dialogue, and explicit expert knowledge |
| How can feedback change the next decision? | Sutton and Barto (2018), [second-edition book site](http://incompleteideas.net/book/the-book-2nd.html); Watkins and Dayan (1992), [journal record](https://doi.org/10.1007/BF00992698); Silver et al. (2016), [Nature record](https://www.nature.com/articles/nature16961) | Sequential action selection, reward feedback, and search guided by learned estimates |
| Why can language now select actions? | Vaswani et al. (2017), [arXiv record 1706.03762](https://arxiv.org/abs/1706.03762); Yao et al. (2022), [arXiv record 2210.03629](https://arxiv.org/abs/2210.03629) | A general language interface and the alternation of reasoning with environment action |
| What turns a model response into an auditable act? | OpenAI, [function-calling guide](https://platform.openai.com/docs/guides/function-calling); Anthropic, [tool-use overview](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview); Pi maintainers, [repository](https://github.com/earendil-works/pi) and [coding-agent documentation](https://github.com/earendil-works/pi/tree/main/packages/coding-agent) | Typed tool requests, harness execution, observations, sessions, and verification evidence |
