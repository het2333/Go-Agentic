"""Deterministic supplier delivery execution-agent teaching fixture."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Iterable, Literal, Mapping, TypeAlias


EvidenceSource: TypeAlias = Literal["email", "erp", "contract", "logistics"]
TaskStatus: TypeAlias = Literal[
    "collecting_evidence",
    "needs_evidence",
    "evidence_blocked",
    "no_action",
    "awaiting_approval",
    "rejected",
    "recovery_required",
    "completed",
]
RecoveryPhase: TypeAlias = Literal[
    "prepare",
    "approval_audit",
    "send_audit",
    "completion_audit",
]

REQUIRED_SOURCES: tuple[EvidenceSource, ...] = (
    "email",
    "erp",
    "contract",
    "logistics",
)
DEMO_NOW = datetime.fromisoformat("2026-09-13T09:00:00+08:00")
FRESHNESS_MINUTES: Mapping[EvidenceSource, int] = {
    "email": 48 * 60,
    "erp": 15,
    "contract": 24 * 60,
    "logistics": 15,
}


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    source: EvidenceSource
    record_id: str
    observed_at: str
    content_hash: str
    facts: Mapping[str, object]


@dataclass(frozen=True)
class AnomalyDecision:
    code: str
    severity: str
    rationale: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class ActionPreview:
    action: str
    target: str
    subject: str
    body: str
    idempotency_key: str
    action_hash: str


@dataclass(frozen=True)
class ApprovalDecision:
    approval_id: str
    actor: str
    approved: bool
    action_hash: str
    decided_at: str = "2026-09-13T08:59:00+08:00"
    expires_at: str = "2026-09-13T09:05:00+08:00"


@dataclass(frozen=True)
class SentMessage:
    message_id: str
    recipient: str
    subject: str
    body: str
    idempotency_key: str


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    sequence: int
    kind: str
    task_id: str
    occurred_at: str
    details: Mapping[str, object]


@dataclass(frozen=True)
class TaskState:
    task_id: str
    order_id: str
    status: TaskStatus
    evidence: tuple[EvidenceRecord, ...] = ()
    missing_evidence: tuple[EvidenceSource, ...] = ()
    evidence_issues: tuple[str, ...] = ()
    anomaly: AnomalyDecision | None = None
    preview: ActionPreview | None = None
    approval: ApprovalDecision | None = None
    message_id: str | None = None
    last_error: str | None = None
    recovery_phase: RecoveryPhase | None = None


def _hash_payload(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def make_evidence_record(
    source: EvidenceSource,
    record_id: str,
    observed_at: str,
    facts: Mapping[str, object],
) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=f"{source}:{record_id}",
        source=source,
        record_id=record_id,
        observed_at=observed_at,
        content_hash=_hash_payload(facts),
        facts=dict(facts),
    )


class InMemoryEmailAdapter:
    source: EvidenceSource = "email"

    def __init__(self, records: Mapping[str, EvidenceRecord]) -> None:
        self._records = dict(records)

    def recent_for_order(self, order_id: str) -> EvidenceRecord | None:
        return self._records.get(order_id)

    def put(self, order_id: str, record: EvidenceRecord) -> None:
        self._records[order_id] = record


class InMemoryERPAdapter:
    source: EvidenceSource = "erp"

    def __init__(self, records: Mapping[str, EvidenceRecord]) -> None:
        self._records = dict(records)

    def purchase_order(self, order_id: str) -> EvidenceRecord | None:
        return self._records.get(order_id)

    def put(self, order_id: str, record: EvidenceRecord) -> None:
        self._records[order_id] = record


class InMemoryContractAdapter:
    source: EvidenceSource = "contract"

    def __init__(self, records: Mapping[str, EvidenceRecord]) -> None:
        self._records = dict(records)

    def terms_for_order(self, order_id: str) -> EvidenceRecord | None:
        return self._records.get(order_id)

    def put(self, order_id: str, record: EvidenceRecord) -> None:
        self._records[order_id] = record


class InMemoryLogisticsAdapter:
    source: EvidenceSource = "logistics"

    def __init__(self, records: Mapping[str, EvidenceRecord]) -> None:
        self._records = dict(records)

    def shipment_for_order(self, order_id: str) -> EvidenceRecord | None:
        return self._records.get(order_id)

    def put(self, order_id: str, record: EvidenceRecord) -> None:
        self._records[order_id] = record


class EvidenceLedger:
    def __init__(self) -> None:
        self._records: dict[EvidenceSource, EvidenceRecord] = {}

    def add(self, record: EvidenceRecord) -> None:
        existing = self._records.get(record.source)
        if existing is not None and existing != record:
            raise ValueError(f"conflicting evidence for source: {record.source}")
        self._records[record.source] = record

    def get(self, source: EvidenceSource) -> EvidenceRecord:
        try:
            return self._records[source]
        except KeyError as error:
            raise KeyError(f"missing evidence source: {source}") from error

    @property
    def records(self) -> tuple[EvidenceRecord, ...]:
        return tuple(
            self._records[source]
            for source in REQUIRED_SOURCES
            if source in self._records
        )

    @property
    def missing_sources(self) -> tuple[EvidenceSource, ...]:
        return tuple(source for source in REQUIRED_SOURCES if source not in self._records)


class SourceEvidenceValidator:
    """Validate authoritative source payloads before policy/model consumption."""

    @staticmethod
    def _required_string(
        source: EvidenceSource,
        facts: Mapping[str, object],
        field: str,
    ) -> tuple[str, ...]:
        if field not in facts:
            return (f"{source} evidence field {field} is required",)
        value = facts[field]
        if not isinstance(value, str) or not value.strip():
            return (
                f"{source} evidence field {field} must be a non-empty string",
            )
        return ()

    @staticmethod
    def _required_boolean(
        source: EvidenceSource,
        facts: Mapping[str, object],
        field: str,
    ) -> tuple[str, ...]:
        if field not in facts:
            return (f"{source} evidence field {field} is required",)
        if type(facts[field]) is not bool:
            return (f"{source} evidence field {field} must be a boolean",)
        return ()

    @staticmethod
    def _required_timestamp(
        source: EvidenceSource,
        facts: Mapping[str, object],
        field: str,
    ) -> tuple[str, ...]:
        if field not in facts:
            return (f"{source} evidence field {field} is required",)
        value = facts[field]
        if not isinstance(value, str):
            return (
                f"{source} evidence field {field} must be an ISO 8601 "
                "timestamp with timezone",
            )
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return (
                f"{source} evidence field {field} must be an ISO 8601 "
                "timestamp with timezone",
            )
        if parsed.tzinfo is None:
            return (
                f"{source} evidence field {field} must be an ISO 8601 "
                "timestamp with timezone",
            )
        return ()

    def validate(self, record: EvidenceRecord) -> tuple[str, ...]:
        validators = {
            "email": self._validate_email,
            "erp": self._validate_erp,
            "contract": self._validate_contract,
            "logistics": self._validate_logistics,
        }
        return validators[record.source](record.facts)

    def _validate_email(self, facts: Mapping[str, object]) -> tuple[str, ...]:
        issues: list[str] = []
        for field in ("order_id", "supplier_contact", "supplier_id"):
            issues.extend(self._required_string("email", facts, field))
        issues.extend(self._required_boolean("email", facts, "shipment_claimed"))
        return tuple(issues)

    def _validate_erp(self, facts: Mapping[str, object]) -> tuple[str, ...]:
        issues: list[str] = []
        for field in ("contract_id", "order_id", "supplier", "supplier_id"):
            issues.extend(self._required_string("erp", facts, field))
        issues.extend(self._required_timestamp("erp", facts, "delivery_due"))
        return tuple(issues)

    def _validate_contract(self, facts: Mapping[str, object]) -> tuple[str, ...]:
        issues: list[str] = []
        for field in ("contract_id", "order_id", "supplier_id"):
            issues.extend(self._required_string("contract", facts, field))
        issues.extend(self._required_boolean("contract", facts, "tracking_required"))
        field = "tracking_required_within_hours"
        if field not in facts:
            issues.append(f"contract evidence field {field} is required")
        else:
            value = facts[field]
            if type(value) is not int or value <= 0:
                issues.append(
                    "contract evidence field tracking_required_within_hours "
                    "must be a positive integer"
                )
        return tuple(issues)

    def _validate_logistics(self, facts: Mapping[str, object]) -> tuple[str, ...]:
        issues: list[str] = []
        for field in ("order_id", "status", "supplier_id"):
            issues.extend(self._required_string("logistics", facts, field))
        issues.extend(self._required_timestamp("logistics", facts, "shipped_at"))
        if "tracking_number" not in facts:
            issues.append("logistics evidence field tracking_number is required")
        else:
            tracking_number = facts["tracking_number"]
            if tracking_number is not None and (
                not isinstance(tracking_number, str) or not tracking_number.strip()
            ):
                issues.append(
                    "logistics evidence field tracking_number must be null or a "
                    "non-empty string"
                )
        return tuple(issues)


class DeliveryAnomalyPolicy:
    def decide(
        self,
        ledger: EvidenceLedger,
        *,
        now: datetime,
    ) -> AnomalyDecision | None:
        email = ledger.get("email")
        contract = ledger.get("contract")
        logistics = ledger.get("logistics")
        shipped_at = datetime.fromisoformat(str(logistics.facts["shipped_at"]))
        tracking_deadline = shipped_at + timedelta(
            hours=int(contract.facts["tracking_required_within_hours"])
        )
        if (
            email.facts["shipment_claimed"] is True
            and contract.facts["tracking_required"] is True
            and not logistics.facts.get("tracking_number")
            and now > tracking_deadline
        ):
            return AnomalyDecision(
                code="missing_tracking_number",
                severity="high",
                rationale=(
                    "The supplier reports shipment, but the tracking number remains "
                    "absent after the contractual 24-hour deadline."
                ),
                evidence_ids=tuple(record.evidence_id for record in ledger.records),
            )
        return None


class InMemoryMailGateway:
    def __init__(self) -> None:
        self._messages: dict[str, SentMessage] = {}
        self._request_fingerprints: dict[str, str] = {}

    def send_once(self, preview: ActionPreview) -> SentMessage:
        request_fingerprint = _hash_payload(
            {
                "body": preview.body,
                "recipient": preview.target,
                "subject": preview.subject,
            }
        )
        existing = self._messages.get(preview.idempotency_key)
        if existing is not None:
            if self._request_fingerprints[preview.idempotency_key] != request_fingerprint:
                raise ValueError(
                    "idempotency key reused with a different request payload"
                )
            return existing
        message = SentMessage(
            message_id=(
                "msg-"
                + hashlib.sha256(preview.idempotency_key.encode("utf-8")).hexdigest()[:12]
            ),
            recipient=preview.target,
            subject=preview.subject,
            body=preview.body,
            idempotency_key=preview.idempotency_key,
        )
        self._messages[preview.idempotency_key] = message
        self._request_fingerprints[preview.idempotency_key] = request_fingerprint
        return message

    @property
    def sent_messages(self) -> tuple[SentMessage, ...]:
        return tuple(self._messages.values())


class InMemoryAuditLog:
    def __init__(self, fail_once: Iterable[str] = ()) -> None:
        self._events: dict[str, AuditEvent] = {}
        self._fail_once = set(fail_once)

    def append_once(
        self,
        *,
        event_id: str,
        kind: str,
        task_id: str,
        details: Mapping[str, object],
    ) -> AuditEvent:
        normalized_details = dict(details)
        existing = self._events.get(event_id)
        if existing is not None:
            if (
                existing.kind != kind
                or existing.task_id != task_id
                or existing.details != normalized_details
            ):
                raise ValueError(
                    "audit event ID reused with conflicting payload: " + event_id
                )
            return existing
        if kind in self._fail_once:
            self._fail_once.remove(kind)
            raise RuntimeError(f"audit append failed for {kind}")
        event = AuditEvent(
            event_id=event_id,
            sequence=len(self._events) + 1,
            kind=kind,
            task_id=task_id,
            occurred_at=DEMO_NOW.isoformat(),
            details=normalized_details,
        )
        self._events[event_id] = event
        return event

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events.values())


class EnterpriseExecutionAgent:
    def __init__(
        self,
        *,
        email: InMemoryEmailAdapter,
        erp: InMemoryERPAdapter,
        contract: InMemoryContractAdapter,
        logistics: InMemoryLogisticsAdapter,
        policy: DeliveryAnomalyPolicy,
        mail_gateway: InMemoryMailGateway,
        audit_log: InMemoryAuditLog,
    ) -> None:
        self._email = email
        self._erp = erp
        self._contract = contract
        self._logistics = logistics
        self._policy = policy
        self._mail_gateway = mail_gateway
        self._audit_log = audit_log
        self._source_validator = SourceEvidenceValidator()
        self._state: TaskState | None = None

    @property
    def state(self) -> TaskState | None:
        return self._state

    def _audit(
        self,
        suffix: str,
        kind: str,
        details: Mapping[str, object],
    ) -> AuditEvent:
        if self._state is None:
            raise RuntimeError("task has not started")
        return self._audit_log.append_once(
            event_id=f"{self._state.task_id}:{suffix}",
            kind=kind,
            task_id=self._state.task_id,
            details=details,
        )

    def _audit_or_block(
        self,
        suffix: str,
        kind: str,
        details: Mapping[str, object],
    ) -> bool:
        try:
            self._audit(suffix, kind, details)
        except (RuntimeError, ValueError) as error:
            if self._state is None:
                raise
            self._state = replace(
                self._state,
                status="recovery_required",
                last_error=str(error),
                recovery_phase="prepare",
            )
            return False
        return True

    def _validate_evidence(
        self,
        order_id: str,
        ledger: EvidenceLedger,
    ) -> tuple[str, ...]:
        issues: list[str] = []
        for record in ledger.records:
            try:
                expected_hash = _hash_payload(record.facts)
            except (TypeError, ValueError):
                issues.append(
                    f"{record.source} evidence facts are not JSON-compatible"
                )
                continue
            if record.content_hash != expected_hash:
                issues.append(f"{record.source} evidence content hash mismatch")
                continue
            try:
                observed_at = datetime.fromisoformat(record.observed_at)
            except (TypeError, ValueError):
                issues.append(f"{record.source} evidence has invalid observed_at")
                continue
            if observed_at.tzinfo is None:
                issues.append(f"{record.source} evidence observed_at lacks timezone")
                continue
            age = DEMO_NOW - observed_at
            if age < timedelta(0):
                issues.append(f"{record.source} evidence is observed in the future")
                continue
            freshness_limit = FRESHNESS_MINUTES[record.source]
            freshness_window = timedelta(minutes=freshness_limit)
            if age > freshness_window:
                issues.append(
                    f"{record.source} evidence is stale "
                    f"(age {age.total_seconds():g}s; "
                    f"limit {freshness_window.total_seconds():g}s)"
                )
            issues.extend(self._source_validator.validate(record))

        for record in ledger.records:
            record_order_id = record.facts.get("order_id")
            if (
                isinstance(record_order_id, str)
                and record_order_id.strip()
                and record_order_id != order_id
            ):
                issues.append(
                    f"{record.source} evidence belongs to "
                    f"{record_order_id}, not {order_id}"
                )

        email = ledger.get("email")
        erp = ledger.get("erp")
        contract = ledger.get("contract")
        logistics = ledger.get("logistics")
        erp_contract_id = erp.facts.get("contract_id")
        contract_contract_id = contract.facts.get("contract_id")
        if (
            isinstance(erp_contract_id, str)
            and erp_contract_id.strip()
            and isinstance(contract_contract_id, str)
            and contract_contract_id.strip()
            and erp_contract_id != contract_contract_id
        ):
            issues.append("ERP and contract records disagree on contract_id")
        supplier_ids = {
            record.source: record.facts.get("supplier_id")
            for record in (email, erp, contract, logistics)
        }
        if all(
            isinstance(value, str) and value.strip()
            for value in supplier_ids.values()
        ) and len(set(supplier_ids.values())) != 1:
            issues.append("evidence sources disagree on supplier_id")
        if (
            email.facts.get("shipment_claimed") is True
            and logistics.facts.get("status") not in {"shipped", "in_transit", "delivered"}
        ):
            issues.append(
                "email claims shipment but logistics status is "
                f"{logistics.facts.get('status')}"
            )
        return tuple(issues)

    @staticmethod
    def _evidence_revision(ledger: EvidenceLedger) -> str:
        return _hash_payload(
            {
                "records": tuple(
                    (record.evidence_id, record.observed_at, record.content_hash)
                    for record in ledger.records
                )
            }
        )[:12]

    def prepare(self, order_id: str) -> TaskState:
        if not order_id.strip():
            raise ValueError("order_id is required")
        if self._state is not None and self._state.status == "completed":
            if self._state.order_id == order_id:
                return self._state
            raise RuntimeError("completed task is terminal")
        if (
            self._state is not None
            and self._state.status == "recovery_required"
            and self._state.recovery_phase != "prepare"
        ):
            return self._state
        task_id = f"delivery-anomaly:{order_id}"
        self._state = TaskState(
            task_id=task_id,
            order_id=order_id,
            status="collecting_evidence",
        )
        ledger = EvidenceLedger()
        reads = (
            self._email.recent_for_order,
            self._erp.purchase_order,
            self._contract.terms_for_order,
            self._logistics.shipment_for_order,
        )
        for read in reads:
            record = read(order_id)
            if record is not None:
                ledger.add(record)

        missing = ledger.missing_sources
        self._state = replace(
            self._state,
            evidence=ledger.records,
            missing_evidence=missing,
        )
        revision = self._evidence_revision(ledger)
        if not self._audit_or_block(
            f"evidence:{revision}",
            "evidence_collected",
            {
                "evidence_ids": tuple(record.evidence_id for record in ledger.records),
                "evidence_hashes": tuple(
                    record.content_hash for record in ledger.records
                ),
                "order_id": order_id,
            },
        ):
            return self._state
        if missing:
            self._state = replace(self._state, status="needs_evidence")
            if not self._audit_or_block(
                f"evidence-incomplete:{revision}",
                "evidence_incomplete",
                {"missing_sources": missing, "order_id": order_id},
            ):
                return self._state
            return self._state

        evidence_issues = self._validate_evidence(order_id, ledger)
        if evidence_issues:
            self._state = replace(
                self._state,
                status="evidence_blocked",
                evidence_issues=evidence_issues,
                last_error="; ".join(evidence_issues),
            )
            if not self._audit_or_block(
                f"evidence-blocked:{revision}",
                "evidence_blocked",
                {"issues": evidence_issues, "order_id": order_id},
            ):
                return self._state
            return self._state

        anomaly = self._policy.decide(ledger, now=DEMO_NOW)
        if anomaly is None:
            self._state = replace(self._state, status="no_action")
            if not self._audit_or_block(
                f"decision:{revision}", "no_anomaly", {"order_id": order_id}
            ):
                return self._state
            return self._state

        preview = self._build_preview(order_id, ledger, anomaly)
        self._state = replace(
            self._state,
            status="awaiting_approval",
            anomaly=anomaly,
            preview=preview,
        )
        if not self._audit_or_block(
            f"decision:{revision}",
            "anomaly_decided",
            {
                "anomaly_code": anomaly.code,
                "evidence_ids": anomaly.evidence_ids,
                "order_id": order_id,
            },
        ):
            return self._state
        if not self._audit_or_block(
            f"preview:{preview.action_hash}",
            "draft_prepared",
            {
                "action_hash": preview.action_hash,
                "idempotency_key": preview.idempotency_key,
                "order_id": order_id,
                "target": preview.target,
            },
        ):
            return self._state
        return self._state

    def supply_evidence(self, record: EvidenceRecord) -> TaskState:
        if self._state is None:
            raise RuntimeError("task has not started")
        if self._state.status == "completed":
            return self._state
        if record.source not in REQUIRED_SOURCES:
            raise ValueError(f"unknown evidence source: {record.source}")
        if record.facts.get("order_id") != self._state.order_id:
            raise ValueError("supplied evidence belongs to a different order")
        adapters = {
            "email": self._email,
            "erp": self._erp,
            "contract": self._contract,
            "logistics": self._logistics,
        }
        adapters[record.source].put(self._state.order_id, record)
        return self.prepare(self._state.order_id)

    def _build_preview(
        self,
        order_id: str,
        ledger: EvidenceLedger,
        anomaly: AnomalyDecision,
    ) -> ActionPreview:
        email = ledger.get("email")
        erp = ledger.get("erp")
        contract = ledger.get("contract")
        logistics = ledger.get("logistics")
        target = str(email.facts["supplier_contact"])
        subject = f"Action required: tracking number for {order_id}"
        body = (
            "Hello Northstar team,\n\n"
            f"Your latest update says {order_id} shipped "
            f"[{email.evidence_id}], and the PO remains due on "
            f"{erp.facts['delivery_due']} [{erp.evidence_id}]. The contract requires "
            "tracking within 24 hours "
            f"[{contract.evidence_id}], but the shipment record still has no tracking "
            f"number [{logistics.evidence_id}].\n\n"
            "Please reply with the carrier, tracking number, and confirmed delivery ETA. "
            "This draft does not change the PO or contract.\n"
        )
        idempotency_key = f"delivery-anomaly:{order_id}:{anomaly.code}"
        action_payload = {
            "action": "send_supplier_follow_up",
            "body": body,
            "idempotency_key": idempotency_key,
            "subject": subject,
            "target": target,
        }
        return ActionPreview(
            action="send_supplier_follow_up",
            target=target,
            subject=subject,
            body=body,
            idempotency_key=idempotency_key,
            action_hash=_hash_payload(action_payload),
        )

    def execute(self, approval: ApprovalDecision | None = None) -> TaskState:
        if self._state is None:
            raise RuntimeError("prepare must run before execute")
        if self._state.status == "completed":
            return self._state
        if self._state.status == "recovery_required":
            return self.resume()
        if self._state.status == "needs_evidence":
            self._state = replace(
                self._state,
                last_error=(
                    "required evidence is missing: "
                    + ", ".join(self._state.missing_evidence)
                ),
            )
            return self._state
        if self._state.status in {"evidence_blocked", "no_action", "rejected"}:
            return self._state
        preview = self._state.preview
        if preview is None:
            raise RuntimeError("no action preview is available")
        if approval is None:
            self._state = replace(
                self._state,
                status="awaiting_approval",
                last_error="human approval is required",
            )
            return self._state
        if approval.action_hash != preview.action_hash:
            self._state = replace(
                self._state,
                status="awaiting_approval",
                last_error="approval does not match the preview",
            )
            return self._state
        approval_error = self._approval_error(approval)
        if approval_error is not None:
            self._state = replace(
                self._state,
                status="awaiting_approval",
                last_error=approval_error,
            )
            return self._state
        if not approval.approved:
            self._state = replace(self._state, status="rejected", last_error=None)
            self._audit(
                f"approval-rejected:{approval.approval_id}",
                "approval_rejected",
                {
                    "action_hash": approval.action_hash,
                    "actor": approval.actor,
                    "approval_id": approval.approval_id,
                },
            )
            return self._state

        self._state = replace(self._state, approval=approval, last_error=None)
        return self._execute_authorized(recovering=False)

    def _approval_error(self, approval: ApprovalDecision) -> str | None:
        try:
            decided_at = datetime.fromisoformat(approval.decided_at)
            expires_at = datetime.fromisoformat(approval.expires_at)
        except ValueError:
            return "approval timestamps are invalid"
        if decided_at.tzinfo is None or expires_at.tzinfo is None:
            return "approval timestamps must include a timezone"
        if expires_at <= decided_at:
            return "approval expiry must be after its decision time"
        if decided_at > DEMO_NOW:
            return "approval decision time is in the future"
        if expires_at <= DEMO_NOW:
            return "approval has expired"
        return None

    def _execute_authorized(self, *, recovering: bool) -> TaskState:
        if self._state is None or self._state.preview is None:
            raise RuntimeError("no action preview is available")
        approval = self._state.approval
        if approval is None:
            raise RuntimeError("authorized execution has no persisted approval")
        preview = self._state.preview
        approval_details = {
            "action_hash": approval.action_hash,
            "actor": approval.actor,
            "approval_id": approval.approval_id,
            "decided_at": approval.decided_at,
            "expires_at": approval.expires_at,
        }
        try:
            approval_event = self._audit(
                f"approval-recorded:{approval.approval_id}",
                "approval_recorded",
                approval_details,
            )
            if (
                approval_event.kind != "approval_recorded"
                or approval_event.task_id != self._state.task_id
                or approval_event.details != approval_details
            ):
                raise RuntimeError("authorized approval audit was not persisted")
        except (RuntimeError, ValueError) as error:
            self._state = replace(
                self._state,
                status="recovery_required",
                last_error=str(error),
                recovery_phase="approval_audit",
            )
            return self._state

        message = self._mail_gateway.send_once(preview)
        try:
            self._audit_log.append_once(
                event_id=f"{self._state.task_id}:message-sent",
                kind="message_sent",
                task_id=self._state.task_id,
                details={
                    "approval_id": approval.approval_id,
                    "idempotency_key": preview.idempotency_key,
                    "message_id": message.message_id,
                    "order_id": self._state.order_id,
                },
            )
        except (RuntimeError, ValueError) as error:
            self._state = replace(
                self._state,
                status="recovery_required",
                message_id=message.message_id,
                last_error=str(error),
                recovery_phase="send_audit",
            )
            return self._state

        if recovering:
            try:
                self._audit(
                    "recovered",
                    "recovered",
                    {
                        "approval_id": approval.approval_id,
                        "idempotency_key": preview.idempotency_key,
                        "message_id": message.message_id,
                    },
                )
            except (RuntimeError, ValueError) as error:
                self._state = replace(
                    self._state,
                    status="recovery_required",
                    message_id=message.message_id,
                    last_error=str(error),
                    recovery_phase="completion_audit",
                )
                return self._state

        self._state = replace(
            self._state,
            status="completed",
            message_id=message.message_id,
            last_error=None,
            recovery_phase=None,
        )
        return self._state

    def resume(self) -> TaskState:
        if self._state is None:
            raise RuntimeError("task has not started")
        if self._state.status == "completed":
            return self._state
        if self._state.status != "recovery_required":
            return self._state
        if self._state.recovery_phase == "prepare":
            return self.prepare(self._state.order_id)
        if self._state.recovery_phase in {
            "approval_audit",
            "send_audit",
            "completion_audit",
        }:
            return self._execute_authorized(recovering=True)
        return self._state


@dataclass(frozen=True)
class DemoSystem:
    agent: EnterpriseExecutionAgent
    mail_gateway: InMemoryMailGateway
    audit_log: InMemoryAuditLog


def build_demo_system(
    *,
    missing_sources: Iterable[str] = (),
    fail_audit_once: Iterable[str] = (),
    evidence_overrides: Mapping[str, EvidenceRecord] | None = None,
) -> DemoSystem:
    missing = set(missing_sources)
    unknown = missing - set(REQUIRED_SOURCES)
    if unknown:
        raise ValueError(f"unknown evidence sources: {', '.join(sorted(unknown))}")

    records: dict[EvidenceSource, EvidenceRecord] = {
        "email": make_evidence_record(
            "email",
            "MSG-483",
            "2026-09-12T08:30:00+08:00",
            {
                "order_id": "PO-7",
                "shipment_claimed": True,
                "supplier_contact": "orders@northstar.example",
                "supplier_id": "SUP-21",
            },
        ),
        "erp": make_evidence_record(
            "erp",
            "PO-7:v3",
            "2026-09-13T08:55:00+08:00",
            {
                "contract_id": "CTR-9",
                "delivery_due": "2026-09-13T18:00:00+08:00",
                "order_id": "PO-7",
                "supplier": "Northstar Components",
                "supplier_id": "SUP-21",
            },
        ),
        "contract": make_evidence_record(
            "contract",
            "CTR-9:v2",
            "2026-09-13T08:56:00+08:00",
            {
                "contract_id": "CTR-9",
                "order_id": "PO-7",
                "supplier_id": "SUP-21",
                "tracking_required": True,
                "tracking_required_within_hours": 24,
            },
        ),
        "logistics": make_evidence_record(
            "logistics",
            "SHIP-77:v1",
            "2026-09-13T08:58:00+08:00",
            {
                "order_id": "PO-7",
                "shipped_at": "2026-09-12T08:00:00+08:00",
                "status": "in_transit",
                "supplier_id": "SUP-21",
                "tracking_number": None,
            },
        ),
    }
    for source in missing:
        del records[source]  # type: ignore[index]
    for source_name, record in (evidence_overrides or {}).items():
        if source_name not in REQUIRED_SOURCES:
            raise ValueError(f"unknown evidence source override: {source_name}")
        if record.source != source_name:
            raise ValueError("evidence override key does not match record source")
        records[record.source] = record

    email = InMemoryEmailAdapter({"PO-7": records["email"]} if "email" in records else {})
    erp = InMemoryERPAdapter({"PO-7": records["erp"]} if "erp" in records else {})
    contract = InMemoryContractAdapter(
        {"PO-7": records["contract"]} if "contract" in records else {}
    )
    logistics = InMemoryLogisticsAdapter(
        {"PO-7": records["logistics"]} if "logistics" in records else {}
    )
    mail_gateway = InMemoryMailGateway()
    audit_log = InMemoryAuditLog(fail_once=fail_audit_once)
    agent = EnterpriseExecutionAgent(
        email=email,
        erp=erp,
        contract=contract,
        logistics=logistics,
        policy=DeliveryAnomalyPolicy(),
        mail_gateway=mail_gateway,
        audit_log=audit_log,
    )
    return DemoSystem(agent=agent, mail_gateway=mail_gateway, audit_log=audit_log)
