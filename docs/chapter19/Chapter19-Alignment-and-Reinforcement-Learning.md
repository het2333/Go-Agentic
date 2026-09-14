# Chapter 19: Alignment and Reinforcement Learning

<figure class="course-hero">
  <img src="../assets/visuals/chapter-19.webp" alt="Candidate paths pass through human preference balances and converge on a safer aligned trajectory." width="1536" height="864" loading="lazy" decoding="async">
  <figcaption><em>Preference optimization shapes behavior by comparing outcomes and reinforcing better trajectories.</em></figcaption>
</figure>

Chapter 11 asked when training is warranted and when to fix the loop, tool, or environment first. This chapter studies the objective functions: how demonstrations, preferences, and verifiable rewards change parameters.

## 19.1 Mathematical Bridge to RL

An MDP $(\mathcal S,\mathcal A,P,R,\gamma)$ describes states, actions, transitions, rewards, and discounting. For agents, authoritative state usually lives in the environment while context is only a partial observation. Let $T$ index the terminal state: states are $s_0,\ldots,s_T$, actions and rewards are indexed $0,\ldots,T-1$, and $r_t$ arrives on the transition from $s_t$ to $s_{t+1}$. For $t<T$, the finite return is:

$$G_t=\sum_{k=0}^{T-t-1}\gamma^k r_{t+k}$$

Policy gradients estimate:

$$\nabla_\theta J(\theta)=\mathbb E_{\tau\sim\pi_\theta}\left[\sum_t\nabla_\theta\log\pi_\theta(a_t|s_t)A_t\right]$$

An actor emits actions while a critic estimates $V(s)$. Set $V(s_T)=0$ at termination. The TD residual $\delta_t=r_t+\gamma V(s_{t+1})-V(s_t)$ measures one-step surprise, and GAE combines the residuals for the remaining transitions:

$$A_t^{GAE}=\sum_{l=0}^{T-t-1}(\gamma\lambda)^l\delta_{t+l}$$

Small $\lambda$ trusts the critic more; large $\lambda$ approaches long returns. Q-learning is not a direct fit for huge language action spaces, but clarifies replay, bootstrapping, and off-policy bias. Reward shaping must not replace hard safety gates with compensable penalties.

## 19.2 SFT: Learning Demonstrations

For input $x$ and demonstration $y$:

$$\mathcal{L}_{\mathrm{SFT}}=-\sum_t\log\pi_\theta(y_t\mid x,y_{<t})$$

Agent demonstrations should include observations, tool calls, tool results, validation, and termination—not only final prose. Otherwise a model may learn to state success without learning the successful process.

## 19.3 Reward Models

For preference tuple $(x,y_w,y_l)$:

$$P(y_w\succ y_l\mid x)=\sigma(r_\phi(x,y_w)-r_\phi(x,y_l))$$

$$\mathcal{L}_{\mathrm{RM}}=-\log\sigma(r_w-r_l)$$

If annotators see only final text, reward can favor fluent claims over real execution. Agent preference data should expose trajectories, tool evidence, and side effects.

## 19.4 PPO

Define the policy ratio:

$$r_t(\theta)=\frac{\pi_\theta(a_t\mid s_t)}{\pi_{\theta_{old}}(a_t\mid s_t)}$$

PPO uses:

$$\mathcal{L}_{\mathrm{clip}}=\mathbb{E}_t\left[\min\left(r_tA_t,\operatorname{clip}(r_t,1-\epsilon,1+\epsilon)A_t\right)\right]$$

Clipping limits large updates; a critic estimates value for advantages. RLHF commonly adds a KL penalty against a reference policy to limit reward-driven drift.

## 19.5 DPO

Direct Preference Optimization writes preference learning as:

$$\mathcal{L}_{\mathrm{DPO}}=-\log\sigma\left(\beta\left[\log\frac{\pi_\theta(y_w\mid x)}{\pi_{ref}(y_w\mid x)}-\log\frac{\pi_\theta(y_l\mid x)}{\pi_{ref}(y_l\mid x)}\right]\right)$$

DPO avoids training a critic in the optimization loop, but still depends on preference quality, a reference policy, and $\beta$. Tool failures absent from preference data do not disappear automatically.

## 19.6 GRPO

Sample a group of outputs for one prompt and normalize rewards within the group:

$$A_i=\frac{r_i-\operatorname{mean}(r)}{\operatorname{std}(r)+\epsilon}$$

A PPO-like clipped ratio and KL constraint then update the policy. Group-relative normalization reduces dependence on a separate critic, but needs diverse candidates and discriminative rewards.

## 19.7 Credit Assignment

Terminal reward does not identify the first wrong step. Separate model tool selection, schema expressiveness, environment faults, verifier errors, and runtime timeouts. Treating all five as model reward trains the policy to compensate for system defects.

## 19.8 Preference Variants and Selection

| Method | Feedback | Geometry | Useful when | Main failure |
| --- | --- | --- | --- | --- |
| Offline DPO | Frozen preference pairs | Log-ratio against reference | Strong offline pairs exist | Frozen data distribution |
| Online DPO | Preferences on current samples | Moving preference boundary | New behavior can be scored | Sampling cost and reward drift |
| KTO | Possibly unpaired good/bad labels | Utility around a KL baseline | Pairing is incomplete | Class imbalance and baseline error |
| IPO | Preference pairs | Squared distance to target margin | Preference overfitting matters | Wrong target margin |
| ORPO | SFT examples plus preferences | NLL plus odds ratio | Single-stage tuning | Competing loss scales |
| Best-of-N | Candidate scores | Selection without updates | Validate reward before training | Inference cost grows with $N$ |

Choose from available feedback first, safe online sampling second, and the training stack last. If a grader cannot reliably select good traces with Best-of-N, using it for RL is riskier.

## 19.9 Reward Types and Composition

- **Outcome reward models (ORMs)** score terminal results; their signal is often sparse and may still depend on learned or human judgment.
- **Process reward models (PRMs)** score intermediate states; dense but vulnerable to plausible-looking work.
- **RLVR** reserves mechanical checkability for compilers, tests, rules, or executable verifiers.
- **Listwise rewards** compare several candidates at once, expressing ranking at higher labeling cost.

Unauthorized side effects, unsupported claims, and budget violations should be non-compensable gates. Optimize quality, cost, and steps only among trajectories that pass them.

## 19.10 Numerical Lab

```bash
cd code/go-agentic
python3 -m pytest 19-alignment -q
```

`objectives.py` implements DPO and GRPO. `rl_math.py` adds discounted returns, GAE, Bradley-Terry probabilities, and DPO/IPO/KTO geometry comparisons. These scalar experiments catch sign, scale, terminal, and normalization mistakes before a training framework hides them.

## 19.11 Mastery Standard

Calculate returns, TD residuals, and GAE; distinguish ORM, PRM, and RLVR; and compare SFT, PPO, DPO, GRPO, KTO, IPO, and ORPO by data, objective, critic, online sampling, compute, and failure modes.
