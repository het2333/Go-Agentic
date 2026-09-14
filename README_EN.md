<div align="right">
  <a href="./README.md">中文</a> | English
</div>

# Go Agentic

> Learn how agents gather information, act in real environments, verify outcomes, and complete work within explicit boundaries.

Go Agentic is a 25-chapter course in full-stack Agentic AI engineering. It begins with working agents and progresses through context, memory, protocols, evaluation, model mathematics, post-training, GPU and inference infrastructure, Agentic UI, and production runtimes.

- [Open the course](./docs/README_EN.md)
- [Preface](./docs/Preface.md)
- [Sources and Acknowledgements](./docs/Sources-and-Acknowledgements.md)

## Learning routes

| Stage | Chapters | Focus |
| --- | --- | --- |
| I | 1–3 | Agentic AI and sufficient LLM foundations |
| II | 4–7 | Agent loops, tools, environments, and runtimes |
| III | 8–10 | RAG, memory, context, MCP, Skills, and A2A |
| IV | 11–12 | Agentic RL decisions, evaluation, observability, and safety |
| V | 13–16 | Real projects and midterm review |
| VI | 17–19 | Transformers, pretraining, AdamW, compression, PPO/DPO/GRPO |
| VII | 20–22 | GPUs, interconnects, FlashAttention/vLLM, FSDP/ZeRO |
| VIII | 23–24 | Agentic UI, human oversight, and production runtimes |
| IX | 25 | Graduation project, review, and release |

**Agent application engineering:** Chapters 1–16 → Chapters 23–25.

**Full-stack Agentic AI:** Chapters 1–25 in order.

**Models and systems:** Finish Chapters 1–12, then focus on Chapters 17–22.

The maintained offline labs live in `code/go-agentic/` and run without paid APIs or large-model downloads:

```bash
cd code/go-agentic
python3 -m pytest -q
```

## Sources and licenses

Documentation and original visual assets are licensed under [CC BY 4.0](./LICENSES/CC-BY-4.0.txt). Software in `code/go-agentic/`, `tools/independent_release/`, `docs/tests/`, and `docs/index.html` is licensed under the [Apache License 2.0](./LICENSES/Apache-2.0.txt). The root [LICENSE](./LICENSE) maps the complete path boundary and links every full-text copy.

Papers, standards, software projects, and design references are disclosed according to their actual use. Listing them does not imply endorsement, sponsorship, or affiliation. See [Sources and Acknowledgements](./docs/Sources-and-Acknowledgements.md).
