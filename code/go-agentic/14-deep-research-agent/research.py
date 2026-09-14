"""Deterministic evidence-driven deep-research teaching fixture."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, TypeAlias


FIXTURE_QUESTION = (
    "Did Meridian's 2025 electric-bus pilot reduce weekday energy use, "
    "and what limits the conclusion?"
)

Strategy: TypeAlias = Literal[
    "primary_source",
    "independent_check",
    "contradiction_search",
]
Stance: TypeAlias = Literal["supports", "contradicts"]
ClaimStatus: TypeAlias = Literal["supported", "contested", "unsupported"]
StopReason: TypeAlias = Literal[
    "coverage_satisfied",
    "query_budget_exhausted",
    "source_saturation",
    "continue_search",
    "citation_verification_failed",
]
SourceStatus: TypeAlias = Literal["selected", "duplicate", "rejected"]
ExtractStatus: TypeAlias = Literal["accepted", "rejected"]
VerificationStatus: TypeAlias = Literal["passed", "failed"]


@dataclass(frozen=True)
class Subquestion:
    subquestion_id: str
    focus: str
    question: str


@dataclass(frozen=True)
class SearchQuery:
    query_id: str
    subquestion_id: str
    strategy: Strategy
    text: str


@dataclass(frozen=True)
class ResearchPlan:
    question: str
    scope: str
    exclusions: tuple[str, ...]
    subquestions: tuple[Subquestion, ...]
    queries: tuple[SearchQuery, ...]


@dataclass(frozen=True)
class RawExtract:
    claim_id: str
    stance: Stance
    quote: str
    locator: str


@dataclass(frozen=True)
class RawDocument:
    document_id: str
    title: str
    url: str
    canonical_url: str
    publisher: str
    published_at: str
    source_kind: str
    content: str
    extracts: tuple[RawExtract, ...]


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    title: str
    canonical_url: str
    publisher: str
    published_at: str
    source_kind: str
    content_hash: str
    alias_urls: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceDisposition:
    document_id: str
    url: str
    canonical_url: str
    status: SourceStatus
    reason: str
    retained_source_id: str | None


@dataclass(frozen=True)
class ExtractDisposition:
    document_id: str
    source_id: str
    claim_id: str
    stance: Stance
    status: ExtractStatus
    reason: str
    evidence_id: str | None


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    claim_id: str
    source_id: str
    stance: Stance
    quote: str
    locator: str


@dataclass(frozen=True)
class ClaimAssessment:
    claim_id: str
    claim_text: str
    status: ClaimStatus
    confidence: float
    supporting_evidence_ids: tuple[str, ...]
    contradicting_evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class Citation:
    number: int
    source_id: str
    title: str
    url: str


@dataclass(frozen=True)
class RenderedClaim:
    claim_id: str
    status: ClaimStatus
    text: str
    evidence_ids: tuple[str, ...]
    citation_numbers: tuple[int, ...]


@dataclass(frozen=True)
class ResearchArtifact:
    title: str
    body: str
    included_claim_ids: tuple[str, ...]
    citations: tuple[Citation, ...]
    rendered_claims: tuple[RenderedClaim, ...]


@dataclass(frozen=True)
class CitationVerification:
    status: VerificationStatus
    issues: tuple[str, ...]


@dataclass(frozen=True)
class StopDecision:
    should_stop: bool
    reason: StopReason
    unresolved_claim_ids: tuple[str, ...]


@dataclass(frozen=True)
class ResearchUI:
    plan: ResearchPlan
    current_step: str
    sources: tuple[SourceRecord, ...]
    source_dispositions: tuple[SourceDisposition, ...]
    extract_dispositions: tuple[ExtractDisposition, ...]
    claim_support: tuple[ClaimAssessment, ...]
    rejected_claims: tuple[ClaimAssessment, ...]
    uncertainty: tuple[str, ...]
    intervention: str
    stop: StopDecision
    verification: CitationVerification
    final_artifact: ResearchArtifact | None


@dataclass(frozen=True)
class ResearchResult:
    plan: ResearchPlan
    sources: tuple[SourceRecord, ...]
    source_dispositions: tuple[SourceDisposition, ...]
    extract_dispositions: tuple[ExtractDisposition, ...]
    ledger: tuple[EvidenceItem, ...]
    assessments: tuple[ClaimAssessment, ...]
    rejected_claim_ids: tuple[str, ...]
    uncertainties: tuple[str, ...]
    diagnostic_draft: ResearchArtifact
    final_artifact: ResearchArtifact | None
    verification: CitationVerification
    stop: StopDecision
    ui: ResearchUI

    def assessment(self, claim_id: str) -> ClaimAssessment:
        try:
            return next(item for item in self.assessments if item.claim_id == claim_id)
        except StopIteration as error:
            raise KeyError(f"unknown claim: {claim_id}") from error

    def evidence(self, evidence_id: str) -> EvidenceItem:
        try:
            return next(item for item in self.ledger if item.evidence_id == evidence_id)
        except StopIteration as error:
            raise KeyError(f"unknown evidence: {evidence_id}") from error


def _content_hash(content: str) -> str:
    normalized = _normalize_text(content)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _normalize_text(value: str) -> str:
    return " ".join(value.split()).casefold()


def _plan(question: str) -> ResearchPlan:
    if question != FIXTURE_QUESTION:
        raise ValueError("this deterministic fixture supports FIXTURE_QUESTION only")
    subquestions = (
        Subquestion("sq-baseline", "baseline", "What was the documented baseline?"),
        Subquestion("sq-outcome", "outcome", "What did the pilot measure?"),
        Subquestion(
            "sq-measurement",
            "measurement",
            "Was the reported measurement independently checked?",
        ),
        Subquestion(
            "sq-limitations",
            "limitations",
            "What limits inference beyond the pilot?",
        ),
    )
    queries = (
        SearchQuery(
            "q1",
            "sq-baseline",
            "primary_source",
            "site:data.meridian.example transit 2025 pilot baseline energy",
        ),
        SearchQuery(
            "q2",
            "sq-baseline",
            "independent_check",
            '"Meridian electric-bus pilot" baseline weekday kWh',
        ),
        SearchQuery(
            "q3",
            "sq-outcome",
            "primary_source",
            "site:data.meridian.example 2025 pilot weekday energy result",
        ),
        SearchQuery(
            "q4",
            "sq-outcome",
            "independent_check",
            '"Meridian" bus pilot measured energy 2025',
        ),
        SearchQuery(
            "q5",
            "sq-measurement",
            "contradiction_search",
            '"Meridian pilot" audit corrected meter reading',
        ),
        SearchQuery(
            "q6",
            "sq-measurement",
            "independent_check",
            '"2025-pilot-report" correction OR audit',
        ),
        SearchQuery(
            "q7",
            "sq-limitations",
            "primary_source",
            "site:data.meridian.example pilot methods sample routes buses",
        ),
        SearchQuery(
            "q8",
            "sq-limitations",
            "contradiction_search",
            '"Meridian electric-bus pilot" limitation extrapolation',
        ),
    )
    return ResearchPlan(
        question=question,
        scope=(
            "Compare the 2025 Meridian pilot's weekday energy use with its "
            "documented baseline and state limits on the conclusion."
        ),
        exclusions=("maintenance cost", "citywide extrapolation"),
        subquestions=subquestions,
        queries=queries,
    )


def _select_and_deduplicate(
    documents: tuple[RawDocument, ...],
) -> tuple[
    tuple[tuple[SourceRecord, RawDocument], ...],
    tuple[SourceDisposition, ...],
]:
    accepted_kinds = {"primary_report", "independent_audit", "methods"}
    selected: list[tuple[SourceRecord, RawDocument]] = []
    hash_to_index: dict[str, int] = {}
    seen_canonical_urls: set[str] = set()
    dispositions: list[SourceDisposition] = []
    for document in documents:
        if document.source_kind not in accepted_kinds:
            dispositions.append(
                SourceDisposition(
                    document.document_id,
                    document.url,
                    document.canonical_url,
                    "rejected",
                    "source_kind_not_accepted",
                    None,
                )
            )
            continue
        fingerprint = _content_hash(document.content)
        duplicate_index = hash_to_index.get(fingerprint)
        if duplicate_index is not None:
            source, original = selected[duplicate_index]
            aliases = source.alias_urls
            if document.url != source.canonical_url and document.url not in aliases:
                aliases = aliases + (document.url,)
            selected[duplicate_index] = (
                SourceRecord(
                    source_id=source.source_id,
                    title=source.title,
                    canonical_url=source.canonical_url,
                    publisher=source.publisher,
                    published_at=source.published_at,
                    source_kind=source.source_kind,
                    content_hash=source.content_hash,
                    alias_urls=aliases,
                ),
                original,
            )
            dispositions.append(
                SourceDisposition(
                    document.document_id,
                    document.url,
                    document.canonical_url,
                    "duplicate",
                    "normalized_content_match",
                    source.source_id,
                )
            )
            continue
        reason = (
            "distinct_content_version"
            if document.canonical_url in seen_canonical_urls
            else "accepted_source_kind"
        )
        source = SourceRecord(
            source_id=document.document_id,
            title=document.title,
            canonical_url=document.canonical_url,
            publisher=document.publisher,
            published_at=document.published_at,
            source_kind=document.source_kind,
            content_hash=fingerprint,
        )
        hash_to_index[fingerprint] = len(selected)
        seen_canonical_urls.add(document.canonical_url)
        selected.append((source, document))
        dispositions.append(
            SourceDisposition(
                document.document_id,
                document.url,
                document.canonical_url,
                "selected",
                reason,
                source.source_id,
            )
        )
    return tuple(selected), tuple(dispositions)


def _extract_evidence(
    selected: tuple[tuple[SourceRecord, RawDocument], ...],
) -> tuple[tuple[EvidenceItem, ...], tuple[ExtractDisposition, ...]]:
    items: list[EvidenceItem] = []
    dispositions: list[ExtractDisposition] = []
    for source, document in selected:
        for extract in document.extracts:
            evidence_id = f"{source.source_id}:{extract.claim_id}:{extract.stance}"
            reason = _extract_rejection_reason(document.content, extract)
            if reason is not None:
                dispositions.append(
                    ExtractDisposition(
                        document.document_id,
                        source.source_id,
                        extract.claim_id,
                        extract.stance,
                        "rejected",
                        reason,
                        None,
                    )
                )
                continue
            item = EvidenceItem(
                evidence_id=evidence_id,
                claim_id=extract.claim_id,
                source_id=source.source_id,
                stance=extract.stance,
                quote=extract.quote,
                locator=extract.locator,
            )
            items.append(item)
            dispositions.append(
                ExtractDisposition(
                    document.document_id,
                    source.source_id,
                    extract.claim_id,
                    extract.stance,
                    "accepted",
                    "quote_and_locator_verified",
                    evidence_id,
                )
            )
    return tuple(items), tuple(dispositions)


def _extract_rejection_reason(content: str, extract: RawExtract) -> str | None:
    if not isinstance(extract.quote, str) or not _normalize_text(extract.quote):
        return "quote_is_empty_or_invalid"
    normalized_quote = _normalize_text(extract.quote)
    if not isinstance(content, str) or normalized_quote not in _normalize_text(content):
        return "quote_not_found_in_source"
    if not isinstance(extract.locator, str):
        return "locator_contract_invalid"
    match = re.fullmatch(r"chars:(0|[1-9]\d*):(0|[1-9]\d*)", extract.locator)
    if match is None:
        return "locator_contract_invalid"
    start, end = (int(value) for value in match.groups())
    if start >= end or end > len(content):
        return "locator_out_of_bounds"
    if _normalize_text(content[start:end]) != normalized_quote:
        return "locator_does_not_match_quote"
    return None


def _assess(
    claims: tuple[Claim, ...], ledger: tuple[EvidenceItem, ...]
) -> tuple[ClaimAssessment, ...]:
    assessments: list[ClaimAssessment] = []
    for claim in claims:
        supports = tuple(
            item.evidence_id
            for item in ledger
            if item.claim_id == claim.claim_id and item.stance == "supports"
        )
        contradicts = tuple(
            item.evidence_id
            for item in ledger
            if item.claim_id == claim.claim_id and item.stance == "contradicts"
        )
        if supports and contradicts:
            status: ClaimStatus = "contested"
            confidence = 0.52
        elif supports:
            status = "supported"
            confidence = 0.93 if len(supports) > 1 else 0.81
        else:
            status = "unsupported"
            confidence = 0.0
        assessments.append(
            ClaimAssessment(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                status=status,
                confidence=confidence,
                supporting_evidence_ids=supports,
                contradicting_evidence_ids=contradicts,
            )
        )
    return tuple(assessments)


def _synthesize(
    sources: tuple[SourceRecord, ...],
    ledger: tuple[EvidenceItem, ...],
    assessments: tuple[ClaimAssessment, ...],
) -> ResearchArtifact:
    source_by_id = {source.source_id: source for source in sources}
    evidence_by_id = {item.evidence_id: item for item in ledger}
    citation_number_by_source: dict[str, int] = {}
    rendered_claims: list[RenderedClaim] = []

    for assessment in assessments:
        if assessment.status == "unsupported":
            continue
        retained_ids = (
            assessment.supporting_evidence_ids
            + assessment.contradicting_evidence_ids
        )
        retained_evidence = tuple(
            evidence_by_id[evidence_id]
            for evidence_id in retained_ids
            if evidence_id in evidence_by_id
            and evidence_by_id[evidence_id].source_id in source_by_id
        )
        if not retained_evidence:
            continue
        if assessment.status == "contested" and not any(
            item.stance == "contradicts" for item in retained_evidence
        ):
            continue

        citation_numbers: list[int] = []
        for evidence in retained_evidence:
            if evidence.source_id not in citation_number_by_source:
                citation_number_by_source[evidence.source_id] = (
                    len(citation_number_by_source) + 1
                )
            number = citation_number_by_source[evidence.source_id]
            if number not in citation_numbers:
                citation_numbers.append(number)

        if assessment.status == "supported":
            citation_marks = "".join(f"[{number}]" for number in citation_numbers)
            text = f"{assessment.claim_text.rstrip('.')} {citation_marks}."
        else:
            conflict_parts = [
                f'"{evidence.quote}" '
                f"[{citation_number_by_source[evidence.source_id]}]"
                for evidence in retained_evidence
            ]
            text = (
                f'{assessment.claim_text.rstrip(".")} remains contested: '
                + "; ".join(conflict_parts)
                + "."
            )
        rendered_claims.append(
            RenderedClaim(
                claim_id=assessment.claim_id,
                status=assessment.status,
                text=text,
                evidence_ids=tuple(item.evidence_id for item in retained_evidence),
                citation_numbers=tuple(citation_numbers),
            )
        )

    citations_by_number = sorted(
        citation_number_by_source.items(), key=lambda item: item[1]
    )
    citations = tuple(
        Citation(
            number,
            source_id,
            source_by_id[source_id].title,
            source_by_id[source_id].canonical_url,
        )
        for source_id, number in citations_by_number
    )
    rendered = tuple(rendered_claims)
    return ResearchArtifact(
        title="Meridian electric-bus pilot: evidence report",
        body=" ".join(item.text for item in rendered),
        included_claim_ids=tuple(item.claim_id for item in rendered),
        citations=citations,
        rendered_claims=rendered,
    )


def verify_artifact(
    artifact: ResearchArtifact,
    sources: tuple[SourceRecord, ...],
    ledger: tuple[EvidenceItem, ...],
    assessments: tuple[ClaimAssessment, ...],
) -> CitationVerification:
    issues: list[str] = []
    source_by_id = {source.source_id: source for source in sources}
    evidence_by_id = {item.evidence_id: item for item in ledger}
    assessment_by_id = {item.claim_id: item for item in assessments}
    citation_by_number = {item.number: item for item in artifact.citations}

    expected_numbers = tuple(range(1, len(artifact.citations) + 1))
    if tuple(item.number for item in artifact.citations) != expected_numbers:
        issues.append("citation_numbers_not_contiguous")
    if len({item.source_id for item in artifact.citations}) != len(
        artifact.citations
    ):
        issues.append("duplicate_citation_source")
    for citation in artifact.citations:
        source = source_by_id.get(citation.source_id)
        if source is None or (
            citation.title,
            citation.url,
        ) != (source.title, source.canonical_url):
            issues.append(f"citation_source_join_failed:{citation.number}")

    if artifact.body != " ".join(item.text for item in artifact.rendered_claims):
        issues.append("body_not_derived_from_rendered_claims")
    if artifact.included_claim_ids != tuple(
        item.claim_id for item in artifact.rendered_claims
    ):
        issues.append("included_claim_ids_do_not_match_body")

    for rendered in artifact.rendered_claims:
        assessment = assessment_by_id.get(rendered.claim_id)
        if assessment is None or assessment.status == "unsupported":
            issues.append(f"unaccepted_claim_rendered:{rendered.claim_id}")
            continue
        retained_ids = set(
            assessment.supporting_evidence_ids
            + assessment.contradicting_evidence_ids
        )
        if not rendered.evidence_ids or not set(rendered.evidence_ids) <= retained_ids:
            issues.append(f"unretained_evidence_rendered:{rendered.claim_id}")
        expected_claim_numbers: list[int] = []
        expected_inline_numbers: list[int] = []
        stances: set[Stance] = set()
        for evidence_id in rendered.evidence_ids:
            evidence = evidence_by_id.get(evidence_id)
            if evidence is None:
                issues.append(f"orphan_evidence:{evidence_id}")
                continue
            stances.add(evidence.stance)
            numbers = [
                number
                for number, citation in citation_by_number.items()
                if citation.source_id == evidence.source_id
            ]
            if not numbers:
                issues.append(f"uncited_evidence:{evidence_id}")
            else:
                expected_inline_numbers.append(numbers[0])
                if numbers[0] not in expected_claim_numbers:
                    expected_claim_numbers.append(numbers[0])
        inline_numbers = tuple(
            int(value) for value in re.findall(r"\[(\d+)\]", rendered.text)
        )
        if tuple(expected_claim_numbers) != rendered.citation_numbers:
            issues.append(f"claim_citation_join_failed:{rendered.claim_id}")
        expected_rendered_numbers = (
            tuple(expected_inline_numbers)
            if rendered.status == "contested"
            else tuple(expected_claim_numbers)
        )
        if inline_numbers != expected_rendered_numbers:
            issues.append(f"inline_citations_do_not_match:{rendered.claim_id}")
        if rendered.status == "contested" and stances != {"supports", "contradicts"}:
            issues.append(f"conflict_not_preserved:{rendered.claim_id}")

    return CitationVerification("failed" if issues else "passed", tuple(issues))


def decide_stop(
    *,
    unresolved_claim_ids: tuple[str, ...],
    queries_run: int,
    query_budget: int,
    novel_sources_last_round: int,
    citations_verified: bool,
) -> StopDecision:
    if queries_run < 0 or query_budget < 1 or novel_sources_last_round < 0:
        raise ValueError("stop-policy counts must be non-negative and budget positive")
    if not unresolved_claim_ids and not citations_verified:
        return StopDecision(True, "citation_verification_failed", ())
    if not unresolved_claim_ids:
        return StopDecision(True, "coverage_satisfied", ())
    if queries_run >= query_budget:
        return StopDecision(True, "query_budget_exhausted", unresolved_claim_ids)
    if novel_sources_last_round == 0:
        return StopDecision(True, "source_saturation", unresolved_claim_ids)
    return StopDecision(False, "continue_search", unresolved_claim_ids)


class ResearchAgent:
    def __init__(
        self,
        documents: tuple[RawDocument, ...],
        claims: tuple[Claim, ...],
        *,
        required_claim_ids: tuple[str, ...] | None = None,
        artifact_verifier: Callable[
            [
                ResearchArtifact,
                tuple[SourceRecord, ...],
                tuple[EvidenceItem, ...],
                tuple[ClaimAssessment, ...],
            ],
            CitationVerification,
        ] = verify_artifact,
    ) -> None:
        self._documents = documents
        self._claims = claims
        self._required_claim_ids = (
            required_claim_ids
            if required_claim_ids is not None
            else tuple(claim.claim_id for claim in claims)
        )
        self._artifact_verifier = artifact_verifier

    def plan(self, question: str) -> ResearchPlan:
        return _plan(question)

    def run(
        self,
        question: str,
        *,
        queries_run: int | None = None,
        query_budget: int | None = None,
        novel_sources_last_round: int = 1,
    ) -> ResearchResult:
        plan = self.plan(question)
        selected, source_dispositions = _select_and_deduplicate(self._documents)
        sources = tuple(source for source, _ in selected)
        ledger, extract_dispositions = _extract_evidence(selected)
        assessments = _assess(self._claims, ledger)
        rejected_assessments = tuple(
            item for item in assessments if item.status == "unsupported"
        )
        rejected = tuple(item.claim_id for item in rejected_assessments)
        evidence_by_id = {item.evidence_id: item for item in ledger}
        uncertainties = tuple(
            f"{item.claim_text} Conflict: "
            + " | ".join(
                evidence_by_id[evidence_id].quote
                for evidence_id in (
                    item.supporting_evidence_ids
                    + item.contradicting_evidence_ids
                )
            )
            for item in assessments
            if item.status == "contested"
        )
        diagnostic_draft = _synthesize(sources, ledger, assessments)
        verification = self._artifact_verifier(
            diagnostic_draft, sources, ledger, assessments
        )
        assessment_by_id = {item.claim_id: item for item in assessments}
        unresolved = tuple(
            claim_id
            for claim_id in self._required_claim_ids
            if claim_id not in assessment_by_id
            or assessment_by_id[claim_id].status == "unsupported"
        )
        effective_queries_run = (
            len(plan.queries) if queries_run is None else queries_run
        )
        effective_query_budget = (
            len(plan.queries) if query_budget is None else query_budget
        )
        stop = decide_stop(
            unresolved_claim_ids=unresolved,
            queries_run=effective_queries_run,
            query_budget=effective_query_budget,
            novel_sources_last_round=novel_sources_last_round,
            citations_verified=verification.status == "passed",
        )
        final_artifact = (
            diagnostic_draft if stop.reason == "coverage_satisfied" else None
        )
        if stop.reason == "coverage_satisfied":
            current_step = "complete"
            intervention = "not_required"
        elif stop.reason == "continue_search":
            current_step = "searching"
            intervention = "not_required"
        else:
            current_step = "needs_intervention"
            intervention = (
                "citation_verification_failed: review citation joins"
                if stop.reason == "citation_verification_failed"
                else f"{stop.reason}: review unresolved requirements"
            )
        ui = ResearchUI(
            plan=plan,
            current_step=current_step,
            sources=sources,
            source_dispositions=source_dispositions,
            extract_dispositions=extract_dispositions,
            claim_support=assessments,
            rejected_claims=rejected_assessments,
            uncertainty=uncertainties,
            intervention=intervention,
            stop=stop,
            verification=verification,
            final_artifact=final_artifact,
        )
        return ResearchResult(
            plan=plan,
            sources=sources,
            source_dispositions=source_dispositions,
            extract_dispositions=extract_dispositions,
            ledger=ledger,
            assessments=assessments,
            rejected_claim_ids=rejected,
            uncertainties=uncertainties,
            diagnostic_draft=diagnostic_draft,
            final_artifact=final_artifact,
            verification=verification,
            stop=stop,
            ui=ui,
        )


def _located_extract(
    content: str,
    claim_id: str,
    stance: Stance,
    quote: str,
) -> RawExtract:
    start = content.index(quote)
    return RawExtract(
        claim_id,
        stance,
        quote,
        f"chars:{start}:{start + len(quote)}",
    )


def build_fixture_documents() -> tuple[RawDocument, ...]:
    report_content = (
        "The documented weekday baseline was 1,200 kWh. During the 2025 pilot, "
        "20 buses averaged 900 kWh per weekday. The reported reduction was 25.0%."
    )
    report_direction_quote = (
        "The documented weekday baseline was 1,200 kWh. During the 2025 pilot, "
        "20 buses averaged 900 kWh per weekday."
    )
    report_magnitude_quote = "The reported reduction was 25.0%."
    report_extracts = (
        _located_extract(
            report_content,
            "energy-direction",
            "supports",
            report_direction_quote,
        ),
        _located_extract(
            report_content,
            "exact-magnitude",
            "supports",
            report_magnitude_quote,
        ),
    )
    return (
        RawDocument(
            "operations-report",
            "2025 Electric-Bus Pilot Operations Report",
            "https://data.meridian.example/transit/2025-pilot-report",
            "https://data.meridian.example/transit/2025-pilot-report",
            "Meridian Transit Department",
            "2025-07-15",
            "primary_report",
            report_content,
            report_extracts,
        ),
        RawDocument(
            "operations-report-mirror",
            "2025 Electric-Bus Pilot Operations Report (mirror)",
            "https://mirror.meridian.example/2025-pilot-report.pdf",
            "https://data.meridian.example/transit/2025-pilot-report",
            "Meridian Open Records Mirror",
            "2025-07-15",
            "primary_report",
            report_content,
            report_extracts,
        ),
        RawDocument(
            "meter-audit",
            "Electric-Bus Pilot Meter Audit",
            "https://audit.meridian.example/reports/bus-pilot-meter-review",
            "https://audit.meridian.example/reports/bus-pilot-meter-review",
            "Meridian Office of the Auditor",
            "2025-08-04",
            "independent_audit",
            "The 1,200 kWh baseline is confirmed. Corrected pilot use of 980 kWh "
            "remained below 1,200 kWh. Calibration implies an 18.3% reduction "
            "rather than 25.0%.",
            (
                _located_extract(
                    "The 1,200 kWh baseline is confirmed. Corrected pilot use of "
                    "980 kWh remained below 1,200 kWh. Calibration implies an "
                    "18.3% reduction rather than 25.0%.",
                    "energy-direction",
                    "supports",
                    "Corrected pilot use of 980 kWh remained below 1,200 kWh.",
                ),
                _located_extract(
                    "The 1,200 kWh baseline is confirmed. Corrected pilot use of "
                    "980 kWh remained below 1,200 kWh. Calibration implies an "
                    "18.3% reduction rather than 25.0%.",
                    "exact-magnitude",
                    "contradicts",
                    "Calibration implies an 18.3% reduction rather than 25.0%.",
                ),
            ),
        ),
        RawDocument(
            "methods-note",
            "2025 Electric-Bus Pilot Methods Note",
            "https://data.meridian.example/transit/2025-pilot-methods",
            "https://data.meridian.example/transit/2025-pilot-methods",
            "Meridian Transit Department",
            "2025-07-15",
            "methods",
            "The pilot covered 20 buses on two routes and was not designed to "
            "estimate a citywide causal effect.",
            (
                _located_extract(
                    "The pilot covered 20 buses on two routes and was not designed "
                    "to estimate a citywide causal effect.",
                    "sample-limit",
                    "supports",
                    "The pilot covered 20 buses on two routes and was not "
                    "designed to estimate a citywide causal effect.",
                ),
            ),
        ),
        RawDocument(
            "vendor-post",
            "Meridian buses transform urban transport",
            "https://vendor.example/blog/meridian-buses",
            "https://vendor.example/blog/meridian-buses",
            "Bus Vendor",
            "2025-07-16",
            "promotional",
            "The vendor calls the pilot transformative without publishing data.",
            (),
        ),
    )


def build_fixture_claims() -> tuple[Claim, ...]:
    return (
        Claim(
            "energy-direction",
            "The 2025 Meridian pilot used less weekday energy than the baseline.",
        ),
        Claim("exact-magnitude", "Weekday energy use fell by exactly 25.0%."),
        Claim(
            "sample-limit",
            "The sample covered only 20 buses on two routes, so the evidence "
            "does not establish a citywide effect.",
        ),
        Claim("maintenance-cost", "Maintenance costs fell during the pilot."),
    )


def build_fixture_agent() -> ResearchAgent:
    return ResearchAgent(
        build_fixture_documents(),
        build_fixture_claims(),
        required_claim_ids=("energy-direction", "exact-magnitude", "sample-limit"),
    )
