# Evidence-Driven Deep Research Agent / 证据驱动的深度研究 Agent

This deterministic Python-standard-library fixture turns one fixed research
question into a scoped plan, diversified queries, selected and deduplicated
sources, source-verified extracts, a claim-evidence ledger, contradiction-aware
assessments, a diagnostic draft, a gated final artifact, and an explicit stop
decision. It makes no network or model call and needs no API key.

这个仅使用 Python 标准库的确定性示例，把一个固定研究问题转换为范围明确的计划、多样化查询、筛选并去重的来源、经原文验证的引文、主张—证据账本、保留矛盾的评估、诊断草稿、门控后的最终产物和明确停止决定。它不调用网络或模型，也不需要 API Key。

## Run / 运行

From the repository root / 在仓库根目录运行：

```bash
python3 -m pytest code/go-agentic/14-deep-research-agent/test_research.py -q
python3 -m pytest code/go-agentic -q
```

## Evidence flow / 证据流

```text
scope → subquestions → diversified queries → source selection + deduplication
      → quote + chars:start:end verification → accepted extract ledger
      → support/contradiction audit → diagnostic draft + citation verification
      → final artifact only after verified coverage → stop reason
```

`build_fixture_agent()` returns the real in-memory pipeline used by the tests.
The operations report and its content-equivalent mirror collapse into one
source, while changed content at the same canonical URL remains a distinct
version. A meter audit
supports the direction of the energy change while contradicting the reported
25.0% magnitude. Extract dispositions audit accepted and rejected quote/locator
pairs. The verified final artifact keeps both values and their citations. A
maintenance-cost claim has no evidence, so it is rejected before synthesis.

`build_fixture_agent()` 返回测试实际使用的内存管线。运营报告及其镜像合并为一个来源；仪表审计支持能耗下降方向，却反驳报告中的 25.0% 幅度。引文处置记录会审计通过或被拒绝的引文/定位组合。经过验证的最终产物保留两个数值及各自引用。维护成本主张没有证据，因此在综合前被拒绝。

`decide_stop()` returns `coverage_satisfied`, `query_budget_exhausted`,
`source_saturation`, `continue_search`, or `citation_verification_failed` from
explicit counters, required unresolved claims, and citation verification.
`ResearchResult.diagnostic_draft` retains candidate synthesis for debugging.
It is not final output. `ResearchResult.final_artifact` and
`ResearchUI.final_artifact` remain `None` until both citation verification and
the `coverage_satisfied` stopping gate succeed. The result and UI also expose
every source and extract disposition, rejected claim, stop decision,
verification result, and intervention state.

`decide_stop()` 根据显式计数、必需但未解决的主张以及引用验证结果，返回 `coverage_satisfied`、`query_budget_exhausted`、`source_saturation`、`continue_search` 或 `citation_verification_failed`。`ResearchResult.diagnostic_draft` 只保留供诊断的候选综合，并非最终输出；只有引用验证与 `coverage_satisfied` 停止门同时成功时，`ResearchResult.final_artifact` 和 `ResearchUI.final_artifact` 才非空。结果和 UI 还暴露来源与引文处置、被拒绝主张、停止决策、验证结果和人工介入状态。

This fixture demonstrates course contracts rather than a Pi SDK, browser,
search provider, crawler, PDF parser, vector database, citation-style engine,
or production research system. The `.example` URLs and documents are invented
fixtures. Production use needs licensed retrieval, content parsing, source
authentication, durable provenance, adversarial-input controls, privacy and
copyright policy, rate limits, monitoring, and human review.

本示例演示课程契约，并非 Pi SDK、浏览器、搜索提供商、爬虫、PDF 解析器、向量数据库、引用格式引擎或生产研究系统。所有 `.example` URL 与文档均为虚构 Fixture。生产使用还需要合规检索、内容解析、来源认证、持久化溯源、对抗输入控制、隐私与版权政策、限流、监控和人工复核。
