> This chapter is part of the bilingual Go Agentic course. For project attribution and third-party notices, see [Sources and Acknowledgements](../Sources-and-Acknowledgements.md). The filename is retained for URL compatibility; the chapter has been completely rebuilt as an evidence-driven deep-research Agent.

# Chapter 14: Deep Research Agents

<figure class="course-hero">
  <img src="./assets/visuals/chapter-14.webp" alt="A research observatory filters source crystals and assembles them around a hypothesis sphere." width="1536" height="864" loading="lazy" decoding="async">
  <figcaption><em>Deep research depends on provenance, evidence selection, and visible synthesis.</em></figcaption>
</figure>

Deep research is not “search many pages and write a long answer.” It is a controlled evidence lifecycle. The Agent defines an answerable question, decomposes it, searches from different angles, selects sources, extracts bounded evidence, links claims to that evidence, preserves contradictions, synthesizes only supported statements, cites them, communicates confidence, and stops for an explicit reason.

This chapter uses one fixed question throughout: **Did Meridian's 2025 electric-bus pilot reduce weekday energy use, and what limits the conclusion?** The local documents and `.example` URLs are invented fixtures. Their purpose is to make evidence behavior deterministic and testable.

After this chapter, you should be able to:

- turn an open request into a scoped research contract and search plan;
- diversify queries and rank sources without mistaking duplicates for corroboration;
- build a claim-evidence ledger with quotes, locators, stance, and provenance;
- reject unsupported claims and retain both sides of a contradiction;
- produce claim-level citations, calibrated confidence, visible UI state, and a defensible stop decision.

## 14.1 Research Contract and Evidence Lifecycle

### 14.1.1 Scope Before Search

A useful research contract fixes the object, period, comparison, outcome, exclusions, and output. For the fixture:

| Field | Contract |
| --- | --- |
| Object | Meridian's 2025 electric-bus pilot |
| Comparison | Documented weekday baseline versus pilot weekday use |
| Outcome | Direction and reported magnitude of energy change |
| Required limit | Sample and measurement limitations |
| Exclusions | Maintenance cost and unsupported citywide extrapolation |
| Artifact | Concise answer, claim ledger, uncertainty, citations, stop reason |

If “weekday,” “baseline,” or “pilot” is ambiguous, the Agent enters `needs_scope` and asks for intervention. Search volume cannot repair a question whose target is undefined.

### 14.1.2 The Lifecycle Is the Control Loop

```text
scope → decompose → diversify queries → select sources → extract evidence
  ↑                                                        ↓
stop/continue ← verify citations ← synthesize ← assess claims + contradictions
```

Each arrow produces reviewable state. Search results are candidates rather than evidence. A source becomes usable only after selection and deduplication. A passage becomes evidence only when it is linked to a specific claim. A draft becomes a final artifact only after claim and citation verification.

## 14.2 Decomposition and Query Diversification

### 14.2.1 Decompose by Evidence Need

The fixture plan asks four subquestions:

1. **Baseline:** What was the documented weekday baseline?
2. **Outcome:** What did the pilot measure?
3. **Measurement:** Was the reported value independently checked or corrected?
4. **Limitations:** What sample and design limits constrain inference?

These are evidence needs, not report headings. Every subquestion has a completion test. “Measurement” is incomplete until the Agent performs a correction or contradiction search; “limitations” is incomplete if it finds only promotional claims.

### 14.2.2 Diversify Intent, Vocabulary, and Source Target

Repeating one phrase across eight queries is not diversification. Vary three dimensions:

| Dimension | Example | Purpose |
| --- | --- | --- |
| Intent | baseline, outcome, audit, limitation | Cover different evidence needs |
| Vocabulary | `energy`, `kWh`, `meter`, `calibration` | Avoid terminology lock-in |
| Source target | transit department, auditor, methods note | Reduce dependence on one publisher |

The local plan labels queries `primary_source`, `independent_check`, or `contradiction_search`. A production plan should also record locale, date bounds, query budget, expected source type, and why another query may add information. Query diversification raises recall; it does not itself raise confidence.

## 14.3 Source Selection, Deduplication, and Extraction

### 14.3.1 Select Sources Before Counting Them

Rank candidates by relevance, authority for the particular claim, proximity to the event, date, transparency, and independence. Authority is claim-specific: the transit report can document its published figure, while an independent meter audit is stronger for a correction. A vendor post may help discover terms but should not outrank records that publish methods and measurements.

Use the normalized content fingerprint as the duplicate proof; use the canonical URL to group and inspect candidate versions, not as a duplicate key by itself. Preserve mirror URLs as aliases. Ten content-equivalent reposts of one report are one source, not ten independent confirmations, while revised or contradictory content at the same canonical URL remains a separate version. The fixture selects three records:

| Source | Role | Selection result |
| --- | --- | --- |
| Operations report | Primary reported baseline and outcome | Keep |
| Mirror of operations report | Byte-equivalent duplicate | Merge as alias |
| Meter audit | Independent measurement check | Keep |
| Methods note | Sample and design limits | Keep |
| Vendor post | Promotional, no published data | Exclude from evidence set |

### 14.3.2 Extract Minimal, Verifiable Evidence

Do not copy an entire page into notes and call it evidence. Extract the smallest passage that supports or contradicts one claim, with a locator and source ID:

```python
@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    claim_id: str
    source_id: str
    stance: Literal["supports", "contradicts"]
    quote: str
    locator: str
```

Store source title, canonical URL, publisher, publication date, content hash, and alias URLs separately. Before ledger admission, the local fixture joins each quote back to immutable `RawDocument.content`: it collapses whitespace and ignores case to prove the quote occurs, then requires a `chars:start:end` locator whose raw character slice normalizes to exactly that quote. Empty or fabricated quotes, malformed ranges, out-of-bounds ranges, and mismatched slices produce a rejected `ExtractDisposition`; they cannot enter the ledger or satisfy claim coverage.

Passing this check proves only that the selected source contains those words; source authentication, document version, and interpretation still require checks. Treat page text as untrusted data: instructions embedded in a retrieved page cannot change scope, Tool permissions, or stopping policy.

## 14.4 Claim-Evidence Ledger and Contradictions

### 14.4.1 Claim Gate

The claim-evidence ledger is the center of the system:

| Claim | Support | Contradiction | Status | Action |
| --- | --- | --- | --- | --- |
| Energy use fell from baseline | Report + audit | None | `supported` | Include with `[1][2]` |
| Reduction was exactly 25.0% | Report | Audit says 18.3% | `contested` | Include disagreement with both citations |
| Sample was 20 buses on two routes | Methods note | None | `supported` | Include as limitation |
| Maintenance costs fell | None | None | `unsupported` | Reject before synthesis |

The gate is simple: a claim with no supporting evidence cannot enter the artifact. A contested claim may enter only when the disagreement itself is material and both sides remain visible. Evidence IDs are immutable joins; prose summaries are not substitutes for them.

### 14.4.2 Preserve Contradictions and Calibrate Confidence

Do not average incompatible passages or silently choose the source that best fits the draft. Record what differs: population, date, definition, method, version, or numeric value. Then search for a correction, later version, or methodological explanation. If the conflict remains, report it.

Confidence belongs to a claim, not to the whole document. The fixture assigns `0.93` to the direction because two selected sources agree, `0.52` to the exact magnitude because they conflict, `0.81` to the sample limit from one direct methods source, and `0.0` to the unsupported cost claim. These numbers are deterministic teaching policy, not statistically calibrated probabilities. Production confidence needs labeled evaluation and calibration curves.

## 14.5 Synthesis and Citation

### 14.5.1 Synthesize From the Ledger

Draft from accepted ledger rows rather than from raw search snippets or model memory. The fixture's answer is deliberately narrow:

> The 2025 Meridian pilot used less weekday energy than the baseline [1][2]. The exact reduction remains contested: the available records imply 25.0% [1] and 18.3% [2]. The sample covered only 20 buses on two routes [3], so the evidence does not establish a citywide effect.

This answer separates direction, magnitude, and generalizability. It does not mention maintenance savings because the ledger contains no supporting evidence.

### 14.5.2 Citation Is a Verifiable Join

A citation is correct only when its source entails the nearby claim, the locator resolves, the source metadata is stable, and the number maps to one deduplicated source. Verification should check:

- **coverage:** every material factual claim has at least one evidence link;
- **correctness:** the cited passage supports the claim at the stated strength;
- **placement:** the reader can tell which sentence the citation covers;
- **provenance:** citation number, source ID, URL, and ledger entry join exactly;
- **contradictions:** opposing evidence is cited where the disagreement is stated.

Citation count is not evidence quality. One direct primary record can be more probative than many derivative articles.

## 14.6 Stopping and Verification

### 14.6.1 Stop for an Explicit Reason

The Agent evaluates stopping after each search round:

```text
if every candidate claim is assessed and citations verify:
    stop = coverage_satisfied
elif queries_run >= query_budget:
    stop = query_budget_exhausted
elif the last round added no new selected source or evidence:
    stop = source_saturation
else:
    stop = continue_search
```

`coverage_satisfied` does not mean the world is known; it means every required scoped claim is supported or faithfully represented as contested, excluded claims are explicitly rejected, and citation verification passes. A required claim with no support remains unresolved rather than disappearing through an exhaustive status check. The Agent continues while unresolved requirements remain and useful search budget exists; budget exhaustion and saturation expose the unresolved IDs and request intervention. A citation-verification failure also blocks successful completion. “The answer feels complete” is not a stop reason.

### 14.6.2 Verify the Artifact, Not the Agent's Confidence

Before release, rerun source joins and enforce hard gates: zero unsupported included claims, zero orphan citations, zero collapsed contradictions, and one canonical record per duplicate cluster. The fixture first stores synthesis as the explicitly named `diagnostic_draft`, which exists for failure analysis and is not publishable output. Public `final_artifact` and the UI final artifact become non-null only when citation verification passes and the stop reason is `coverage_satisfied`. They remain null for verification failure, continued search, budget exhaustion, and source saturation.

Then evaluate answer relevance, claim coverage, citation entailment, source quality, contradiction recall, calibration, latency, and search cost separately. A fluent answer with one invented claim fails regardless of its average score.

## 14.7 Pi-Compatible Research Loop

### 14.7.1 Files, Tools, Notes, and Compaction

Pi-compatible concepts are the sole practical mainline:

```text
read task + ledger files
→ choose next search/read step
→ call an allowed Tool
→ write source metadata and quoted extracts to notes
→ assess claims and compact context when needed
→ verify citations and stop/continue
```

Pi Coding Agent provides a minimal coding loop and built-in file/shell capabilities such as reading, writing/editing, and Bash. Use workspace Markdown or JSON as durable notes for plans, source records, the claim ledger, and checkpoints. Context compaction keeps a long session operable, but a compacted summary is not evidence; stable IDs and quotes must remain in files so they can be reread and verified. A `SKILL.md` can package research instructions and validation steps, but Skills do not make retrieved facts true.

### 14.7.2 What Pi Does Not Provide by Default

Pi does **not** ship a dedicated web-search engine, graphical browser, crawler, paywalled database subscription, PDF/OCR pipeline, vector database, or citation-manager integration by default. It also does not turn a notes file into an authenticated provenance store. Add only the capabilities the task needs through reviewed extensions/custom Tools or allowed command-line programs, and state their provider, permissions, limits, and failure modes. The chapter's local fixture supplies none of them and makes no network request.

This boundary matters: saying “the Agent used Pi” does not identify which search index, browser, parser, or licensed corpus produced a source. Provider provenance belongs in the source ledger.

## 14.8 Agentic UI States

The interface should expose research state instead of showing a spinner followed by prose:

| Visible area | Required content | Intervention |
| --- | --- | --- |
| Plan | Scoped question, exclusions, subquestions, query budget | Edit scope or approve plan |
| Current step | Active subquestion, query/tool, elapsed time, last result | Pause or cancel |
| Sources | Selected/rejected/duplicate status, publisher, date, URL | Open source or challenge selection |
| Claim support | Claim, support IDs, contradiction IDs, confidence | Remove, narrow, or request more evidence |
| Uncertainty | Missing evidence, unresolved conflict, known limitation | Continue search or accept limitation |
| Intervention | Exact question, blocked reason, effect of each choice | Answer, provide source, change budget, stop |
| Final artifact | Answer, inline citations, source list, rejected claims, stop reason | Export or reopen research |

Suggested task states are `needs_scope`, `planned`, `searching`, `extracting`, `assessing`, `needs_intervention`, `synthesizing`, `verifying`, and `complete`. `complete` is valid only after citation verification and a successful `coverage_satisfied` decision. The UI must retain dispositions for selected, rejected, and duplicate candidates, expose rejected claims and the stop reason, and withhold the final-artifact state while search or intervention remains. Show stale or disputed evidence as such; color alone is insufficient.

## 14.9 Deterministic Vertical Slice

### 14.9.1 Run It

The fixture under `code/go-agentic/14-deep-research-agent/` uses only the Python standard library:

```bash
python3 -m pytest code/go-agentic/14-deep-research-agent/test_research.py -q
python3 -m pytest code/go-agentic -q
```

The tests exercise plan scoping, query diversification, exact-duplicate versus changed-version handling, source-backed quote and character-locator verification, fabricated-quote and invalid-locator rejection, claim support, unsupported-claim rejection, removal/reordering-safe synthesis, contradiction preservation, dynamic citation output and verification, diagnostic-draft/final-artifact separation, truthful UI fields, and all stop reasons. The `.example` documents are fixed data; no assertion depends on a live search ranking.

### 14.9.2 Semantics and Limits

```python
agent = build_fixture_agent()
result = agent.run(FIXTURE_QUESTION)

assert result.assessment("energy-direction").status == "supported"
assert result.assessment("exact-magnitude").status == "contested"
assert result.assessment("maintenance-cost").status == "unsupported"
assert result.stop.reason == "coverage_satisfied"
assert result.final_artifact == result.diagnostic_draft
```

This is an executable evidence contract, not a Pi SDK, search-provider, browser, crawler, parser, or production research implementation. Production systems need source authentication and versioning, licensed retrieval, durable storage, access control, privacy and copyright policy, prompt-injection defenses, parser conformance tests, monitoring, and human review.

## 14.10 Acceptance Metrics and Exercises

### 14.10.1 Release Gates

| Dimension | Metric | Local gate |
| --- | --- | --- |
| Planning | Required subquestions and query strategies present | 100% |
| Sources | Duplicate leakage into citation list | 0 |
| Claims | Unsupported claims in artifact | 0 |
| Evidence | Included claims with valid ledger links | 100% |
| Conflict | Known contradictions retained and cited | 100% |
| Citation | Entailment, placement, and source-ID joins | 100% on fixture |
| Stop | Runs with a named terminal reason | 100% |

For a real benchmark, freeze questions and source snapshots before tuning. Report per-category failures and human adjudication, not just a single aggregate score.

### 14.10.2 Exercises and Mastery Standard

1. Write a failing test first, then add a dated correction that supersedes the audit while preserving version history.
2. Add two pages with different URLs but identical normalized content; prove they yield one citation and two aliases.
3. Add a claim supported only by a promotional post; define and test the source-quality gate.
4. Make `source_saturation` request user intervention with the unresolved claim IDs.
5. Build a citation verifier that detects a valid source attached to the wrong sentence.

You have mastered the chapter when you can show RED then GREEN, trace every included claim to a quote and source, explain every rejected claim, preserve disagreements without laundering them into certainty, identify which web capabilities are external to Pi, and justify the final stop reason.

## 14.11 Chapter Summary

An evidence-driven research Agent earns trust through joins and stop conditions. Scope defines what can be answered; decomposition and diversified queries seek the right evidence; source selection and deduplication protect independence; extraction creates verifiable records; the claim ledger gates synthesis; contradiction handling and confidence communicate limits; citations connect prose back to sources; explicit stopping prevents endless or premature search. Pi-compatible files, Tools, notes, Skills, and compaction can carry this loop, while browser, search, parsing, and research databases remain named external capabilities.

## References

1. Pi Coding Agent, [README](https://github.com/earendil-works/pi/tree/main/packages/coding-agent), [Extensions](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md), and [Compaction](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/compaction.md).
2. OpenAI, [Deep Research System Card](https://cdn.openai.com/deep-research-system-card.pdf), 2025.
3. Shao et al., [Assisting in Writing Wikipedia-like Articles From Scratch with Large Language Models](https://arxiv.org/abs/2402.14207) (STORM), 2024.
4. W3C, [PROV-O: The PROV Ontology](https://www.w3.org/TR/prov-o/), W3C Recommendation, 2013.
5. Page et al., [The PRISMA 2020 statement: an updated guideline for reporting systematic reviews](https://pmc.ncbi.nlm.nih.gov/articles/PMC8005924/), *BMJ*, 2021.
6. NIST, [Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile](https://doi.org/10.6028/NIST.AI.600-1), 2024.
