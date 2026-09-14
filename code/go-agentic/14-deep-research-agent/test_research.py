from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path


def _load_research_module():
    module_name = "chapter14_evidence_research"
    module_path = Path(__file__).with_name("research.py")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


research = _load_research_module()


def _fixture_agent_without(*document_ids: str):
    documents = tuple(
        document
        for document in research.build_fixture_documents()
        if document.document_id not in document_ids
    )
    return research.ResearchAgent(
        documents,
        research.build_fixture_claims(),
        required_claim_ids=("energy-direction", "exact-magnitude", "sample-limit"),
    )


def test_plan_scopes_the_question_and_diversifies_queries() -> None:
    agent = research.build_fixture_agent()

    plan = agent.plan(research.FIXTURE_QUESTION)

    assert plan.scope == (
        "Compare the 2025 Meridian pilot's weekday energy use with its "
        "documented baseline and state limits on the conclusion."
    )
    assert plan.exclusions == ("maintenance cost", "citywide extrapolation")
    assert [item.focus for item in plan.subquestions] == [
        "baseline",
        "outcome",
        "measurement",
        "limitations",
    ]
    assert {query.strategy for query in plan.queries} == {
        "primary_source",
        "independent_check",
        "contradiction_search",
    }
    assert len({query.text for query in plan.queries}) == len(plan.queries) == 8


def test_pipeline_deduplicates_sources_and_preserves_provenance() -> None:
    result = research.build_fixture_agent().run(research.FIXTURE_QUESTION)

    assert [source.source_id for source in result.sources] == [
        "operations-report",
        "meter-audit",
        "methods-note",
    ]
    report = result.sources[0]
    assert report.canonical_url == (
        "https://data.meridian.example/transit/2025-pilot-report"
    )
    assert report.alias_urls == (
        "https://mirror.meridian.example/2025-pilot-report.pdf",
    )
    assert report.content_hash


def test_deduplication_keeps_changed_content_at_the_same_canonical_url() -> None:
    original = research.build_fixture_documents()[0]
    revised = research.RawDocument(
        "operations-report-revised",
        "2025 Electric-Bus Pilot Operations Report (revised)",
        original.url,
        original.canonical_url,
        original.publisher,
        "2025-08-10",
        original.source_kind,
        "The revised reduction was 18.3%, not 25.0%.",
        (
            research.RawExtract(
                "exact-magnitude",
                "contradicts",
                "The revised reduction was 18.3%, not 25.0%.",
                "chars:0:43",
            ),
        ),
    )
    agent = research.ResearchAgent(
        (original, revised),
        research.build_fixture_claims(),
        required_claim_ids=("exact-magnitude",),
    )

    result = agent.run(
        research.FIXTURE_QUESTION,
        queries_run=2,
        query_budget=4,
        novel_sources_last_round=1,
    )

    assert [source.source_id for source in result.sources] == [
        "operations-report",
        "operations-report-revised",
    ]
    assert [item.status for item in result.source_dispositions] == [
        "selected",
        "selected",
    ]
    assert result.source_dispositions[1].reason == "distinct_content_version"
    assert result.assessment("exact-magnitude").status == "contested"


def test_supported_claims_are_linked_to_extracts_from_selected_sources() -> None:
    result = research.build_fixture_agent().run(research.FIXTURE_QUESTION)
    direction = result.assessment("energy-direction")

    assert direction.status == "supported"
    assert direction.confidence == 0.93
    assert direction.supporting_evidence_ids == (
        "operations-report:energy-direction:supports",
        "meter-audit:energy-direction:supports",
    )
    for evidence_id in direction.supporting_evidence_ids:
        evidence = result.evidence(evidence_id)
        assert evidence.claim_id == "energy-direction"
        assert evidence.quote
        assert evidence.locator


def test_valid_normalized_quote_and_character_locator_enter_the_ledger() -> None:
    document = research.RawDocument(
        "verified-document",
        "Verified Document",
        "https://data.meridian.example/verified",
        "https://data.meridian.example/verified",
        "Meridian Transit Department",
        "2025-08-12",
        "primary_report",
        "Verified   passage.\nMore.",
        (
            research.RawExtract(
                "verified-claim",
                "supports",
                "verified passage.",
                "chars:0:19",
            ),
        ),
    )
    agent = research.ResearchAgent(
        (document,),
        (research.Claim("verified-claim", "The passage was verified."),),
        required_claim_ids=("verified-claim",),
    )

    result = agent.run(research.FIXTURE_QUESTION)

    assert [item.status for item in result.extract_dispositions] == ["accepted"]
    assert result.extract_dispositions[0].reason == "quote_and_locator_verified"
    assert result.ledger == (
        research.EvidenceItem(
            "verified-document:verified-claim:supports",
            "verified-claim",
            "verified-document",
            "supports",
            "verified passage.",
            "chars:0:19",
        ),
    )
    assert result.assessment("verified-claim").status == "supported"
    assert result.final_artifact == result.diagnostic_draft


def test_fabricated_quote_is_rejected_and_cannot_satisfy_claim_coverage() -> None:
    document = research.RawDocument(
        "fabricated-document",
        "Fabricated Extract Test",
        "https://data.meridian.example/fabricated",
        "https://data.meridian.example/fabricated",
        "Meridian Transit Department",
        "2025-08-12",
        "primary_report",
        "The baseline was 1,200 kWh.",
        (
            research.RawExtract(
                "energy-direction",
                "supports",
                "The pilot average was 900 kWh.",
                "chars:0:27",
            ),
        ),
    )
    agent = research.ResearchAgent(
        (document,),
        (research.Claim("energy-direction", "The pilot used less energy."),),
        required_claim_ids=("energy-direction",),
    )

    result = agent.run(research.FIXTURE_QUESTION)

    assert result.ledger == ()
    assert result.assessment("energy-direction").status == "unsupported"
    assert result.extract_dispositions[0].status == "rejected"
    assert result.extract_dispositions[0].reason == "quote_not_found_in_source"
    assert result.stop.unresolved_claim_ids == ("energy-direction",)
    assert result.final_artifact is None


def test_invalid_locator_is_rejected_even_when_quote_exists() -> None:
    document = research.RawDocument(
        "bad-locator-document",
        "Invalid Locator Test",
        "https://data.meridian.example/bad-locator",
        "https://data.meridian.example/bad-locator",
        "Meridian Transit Department",
        "2025-08-12",
        "primary_report",
        "The pilot average was 900 kWh.",
        (
            research.RawExtract(
                "energy-direction",
                "supports",
                "The pilot average was 900 kWh.",
                "Results, paragraph 2",
            ),
        ),
    )
    agent = research.ResearchAgent(
        (document,),
        (research.Claim("energy-direction", "The pilot used less energy."),),
        required_claim_ids=("energy-direction",),
    )

    result = agent.run(research.FIXTURE_QUESTION)

    assert result.ledger == ()
    assert result.extract_dispositions[0].status == "rejected"
    assert result.extract_dispositions[0].reason == "locator_contract_invalid"
    assert result.assessment("energy-direction").status == "unsupported"
    assert result.final_artifact is None


def test_unsupported_claim_is_rejected_and_never_enters_the_artifact() -> None:
    result = research.build_fixture_agent().run(research.FIXTURE_QUESTION)
    costs = result.assessment("maintenance-cost")

    assert costs.status == "unsupported"
    assert costs.confidence == 0.0
    assert costs.supporting_evidence_ids == ()
    assert result.rejected_claim_ids == ("maintenance-cost",)
    assert "maintenance costs fell" not in result.diagnostic_draft.body.lower()


def test_contradiction_is_retained_with_both_sides_and_lower_confidence() -> None:
    result = research.build_fixture_agent().run(research.FIXTURE_QUESTION)
    magnitude = result.assessment("exact-magnitude")

    assert magnitude.status == "contested"
    assert magnitude.confidence == 0.52
    assert magnitude.supporting_evidence_ids == (
        "operations-report:exact-magnitude:supports",
    )
    assert magnitude.contradicting_evidence_ids == (
        "meter-audit:exact-magnitude:contradicts",
    )
    assert len(result.uncertainties) == 1
    assert "The reported reduction was 25.0%." in result.uncertainties[0]
    assert (
        "Calibration implies an 18.3% reduction rather than 25.0%."
        in result.uncertainties[0]
    )


def test_synthesis_emits_stable_citations_for_every_included_claim() -> None:
    result = research.build_fixture_agent().run(research.FIXTURE_QUESTION)

    assert result.diagnostic_draft.included_claim_ids == (
        "energy-direction",
        "exact-magnitude",
        "sample-limit",
    )
    assert [citation.number for citation in result.diagnostic_draft.citations] == [1, 2, 3]
    assert [citation.source_id for citation in result.diagnostic_draft.citations] == [
        "operations-report",
        "meter-audit",
        "methods-note",
    ]
    assert "less weekday energy than the baseline [1][2]" in result.diagnostic_draft.body
    assert '"The reported reduction was 25.0%." [1]' in result.diagnostic_draft.body
    assert (
        '"Calibration implies an 18.3% reduction rather than 25.0%." [2]'
        in result.diagnostic_draft.body
    )
    assert "does not establish a citywide effect [3]" in result.diagnostic_draft.body
    assert result.final_artifact == result.diagnostic_draft


def test_synthesis_drops_claims_when_their_supporting_sources_are_removed() -> None:
    result = _fixture_agent_without(
        "operations-report", "operations-report-mirror", "meter-audit"
    ).run(
        research.FIXTURE_QUESTION,
        queries_run=4,
        query_budget=8,
        novel_sources_last_round=1,
    )

    assert result.diagnostic_draft.included_claim_ids == ("sample-limit",)
    assert "Weekday energy use fell" not in result.diagnostic_draft.body
    assert "25.0%" not in result.diagnostic_draft.body
    assert [citation.source_id for citation in result.diagnostic_draft.citations] == [
        "methods-note"
    ]
    assert result.diagnostic_draft.rendered_claims[0].citation_numbers == (1,)
    assert "[1]" in result.diagnostic_draft.body
    assert result.final_artifact is None


def test_synthesis_renumbers_reordered_sources_and_preserves_both_conflict_sides() -> None:
    documents = research.build_fixture_documents()
    reordered = (documents[2], documents[3], documents[0], documents[1], documents[4])
    result = research.ResearchAgent(
        reordered,
        research.build_fixture_claims(),
        required_claim_ids=("energy-direction", "exact-magnitude", "sample-limit"),
    ).run(research.FIXTURE_QUESTION)

    assert [citation.source_id for citation in result.diagnostic_draft.citations] == [
        "meter-audit",
        "operations-report",
        "methods-note",
    ]
    contested = next(
        claim
        for claim in result.diagnostic_draft.rendered_claims
        if claim.claim_id == "exact-magnitude"
    )
    assert contested.status == "contested"
    assert contested.evidence_ids == (
        "operations-report:exact-magnitude:supports",
        "meter-audit:exact-magnitude:contradicts",
    )
    assert contested.citation_numbers == (2, 1)
    assert "25.0%" in contested.text and "18.3%" in contested.text
    assert "[2]" in contested.text and "[1]" in contested.text
    assert result.verification.status == "passed"


def test_contested_evidence_from_one_source_can_reuse_its_citation() -> None:
    document = research.RawDocument(
        "single-source",
        "Pilot Report with Internal Conflict",
        "https://data.meridian.example/transit/conflicted-report",
        "https://data.meridian.example/transit/conflicted-report",
        "Meridian Transit Department",
        "2025-08-12",
        "primary_report",
        (
            "The original calculation reported a 25.0% reduction. "
            "The calibration note revised the reduction to 18.3%."
        ),
        (
            research.RawExtract(
                "exact-magnitude",
                "supports",
                "The original calculation reported a 25.0% reduction.",
                "chars:0:52",
            ),
            research.RawExtract(
                "exact-magnitude",
                "contradicts",
                "The calibration note revised the reduction to 18.3%.",
                "chars:53:105",
            ),
        ),
    )
    agent = research.ResearchAgent(
        (document,),
        (research.Claim("exact-magnitude", "Energy use fell by exactly 25.0%."),),
        required_claim_ids=("exact-magnitude",),
    )

    result = agent.run(research.FIXTURE_QUESTION)
    rendered = result.diagnostic_draft.rendered_claims[0]

    assert rendered.citation_numbers == (1,)
    assert rendered.text.count("[1]") == 2
    assert result.verification == research.CitationVerification("passed", ())
    assert result.stop.reason == "coverage_satisfied"
    assert result.final_artifact == result.diagnostic_draft
    assert result.ui.final_artifact == result.final_artifact


def test_citation_verification_rejects_a_wrong_source_number_on_a_claim() -> None:
    result = research.build_fixture_agent().run(research.FIXTURE_QUESTION)
    direction = result.diagnostic_draft.rendered_claims[0]
    corrupted_direction = replace(
        direction,
        text=direction.text.replace("[2]", "[3]"),
        citation_numbers=(1, 3),
    )
    rendered_claims = (
        corrupted_direction,
    ) + result.diagnostic_draft.rendered_claims[1:]
    corrupted = replace(
        result.diagnostic_draft,
        body=" ".join(item.text for item in rendered_claims),
        rendered_claims=rendered_claims,
    )

    verification = research.verify_artifact(
        corrupted,
        result.sources,
        result.ledger,
        result.assessments,
    )

    assert verification.status == "failed"
    assert "claim_citation_join_failed:energy-direction" in verification.issues


def test_run_withholds_artifact_when_integrated_citation_verification_fails() -> None:
    def fail_verification(artifact, sources, ledger, assessments):
        return research.CitationVerification("failed", ("forced_test_failure",))

    agent = research.ResearchAgent(
        research.build_fixture_documents(),
        research.build_fixture_claims(),
        required_claim_ids=("energy-direction", "exact-magnitude", "sample-limit"),
        artifact_verifier=fail_verification,
    )

    result = agent.run(research.FIXTURE_QUESTION)

    assert result.verification == research.CitationVerification(
        "failed", ("forced_test_failure",)
    )
    assert (result.stop.should_stop, result.stop.reason) == (
        True,
        "citation_verification_failed",
    )
    assert result.ui.current_step == "needs_intervention"
    assert result.ui.intervention == (
        "citation_verification_failed: review citation joins"
    )
    assert result.final_artifact is None
    assert result.ui.final_artifact is None
    assert result.diagnostic_draft.included_claim_ids == (
        "energy-direction",
        "exact-magnitude",
        "sample-limit",
    )
    assert not hasattr(result, "artifact")


def test_ui_snapshot_exposes_dispositions_rejections_stop_and_verification() -> None:
    result = research.build_fixture_agent().run(research.FIXTURE_QUESTION)

    assert result.ui.plan == result.plan
    assert result.ui.current_step == "complete"
    assert result.ui.sources == result.sources
    assert [item.status for item in result.ui.source_dispositions] == [
        "selected",
        "duplicate",
        "selected",
        "selected",
        "rejected",
    ]
    assert result.ui.claim_support == result.assessments
    assert [claim.claim_id for claim in result.ui.rejected_claims] == [
        "maintenance-cost"
    ]
    assert result.ui.uncertainty == result.uncertainties
    assert result.ui.intervention == "not_required"
    assert result.ui.stop == result.stop
    assert result.ui.verification.status == "passed"
    assert result.final_artifact == result.diagnostic_draft
    assert result.ui.final_artifact == result.final_artifact


def test_ui_does_not_mark_an_unresolved_search_complete() -> None:
    result = _fixture_agent_without(
        "operations-report", "operations-report-mirror", "meter-audit"
    ).run(
        research.FIXTURE_QUESTION,
        queries_run=4,
        query_budget=8,
        novel_sources_last_round=1,
    )

    assert result.stop.reason == "continue_search"
    assert result.ui.current_step == "searching"
    assert result.ui.intervention == "not_required"
    assert result.final_artifact is None
    assert result.ui.final_artifact is None


def test_stop_policy_returns_explicit_reasons() -> None:
    covered = research.decide_stop(
        unresolved_claim_ids=(),
        queries_run=8,
        query_budget=8,
        novel_sources_last_round=1,
        citations_verified=True,
    )
    budget = research.decide_stop(
        unresolved_claim_ids=("open-claim",),
        queries_run=8,
        query_budget=8,
        novel_sources_last_round=1,
        citations_verified=True,
    )
    saturated = research.decide_stop(
        unresolved_claim_ids=("open-claim",),
        queries_run=6,
        query_budget=8,
        novel_sources_last_round=0,
        citations_verified=True,
    )
    continuing = research.decide_stop(
        unresolved_claim_ids=("open-claim",),
        queries_run=6,
        query_budget=8,
        novel_sources_last_round=1,
        citations_verified=True,
    )
    verification_failed = research.decide_stop(
        unresolved_claim_ids=(),
        queries_run=8,
        query_budget=8,
        novel_sources_last_round=1,
        citations_verified=False,
    )

    assert (covered.should_stop, covered.reason) == (True, "coverage_satisfied")
    assert (budget.should_stop, budget.reason) == (True, "query_budget_exhausted")
    assert (saturated.should_stop, saturated.reason) == (True, "source_saturation")
    assert (continuing.should_stop, continuing.reason) == (False, "continue_search")
    assert (verification_failed.should_stop, verification_failed.reason) == (
        True,
        "citation_verification_failed",
    )
    assert research.build_fixture_agent().run(
        research.FIXTURE_QUESTION
    ).stop == covered


def test_integrated_pipeline_reaches_unresolved_budget_and_saturation_paths() -> None:
    agent = _fixture_agent_without(
        "operations-report", "operations-report-mirror", "meter-audit"
    )

    continuing = agent.run(
        research.FIXTURE_QUESTION,
        queries_run=4,
        query_budget=8,
        novel_sources_last_round=1,
    )
    exhausted = agent.run(
        research.FIXTURE_QUESTION,
        queries_run=8,
        query_budget=8,
        novel_sources_last_round=1,
    )
    saturated = agent.run(
        research.FIXTURE_QUESTION,
        queries_run=4,
        query_budget=8,
        novel_sources_last_round=0,
    )

    assert continuing.stop.reason == "continue_search"
    assert exhausted.stop.reason == "query_budget_exhausted"
    assert saturated.stop.reason == "source_saturation"
    assert exhausted.stop.unresolved_claim_ids == (
        "energy-direction",
        "exact-magnitude",
    )
    assert exhausted.ui.current_step == "needs_intervention"
    assert saturated.ui.current_step == "needs_intervention"
    assert exhausted.final_artifact is None
    assert saturated.final_artifact is None
    assert exhausted.ui.final_artifact is None
    assert saturated.ui.final_artifact is None
