"""A dependency-free durable-job state machine for Chapter 24."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    id: str
    tenant_id: str
    task: str
    idempotency_key: str
    status: JobStatus = JobStatus.QUEUED
    attempts: int = 0
    max_retries: int = 0
    checkpoint: dict[str, Any] = field(default_factory=dict)


class DurableRuntime:
    _ALLOWED = {
        JobStatus.QUEUED: {JobStatus.RUNNING, JobStatus.CANCELLED},
        JobStatus.RUNNING: {
            JobStatus.WAITING_FOR_APPROVAL,
            JobStatus.SUCCEEDED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        },
        JobStatus.WAITING_FOR_APPROVAL: {JobStatus.RUNNING, JobStatus.CANCELLED},
        JobStatus.SUCCEEDED: set(),
        JobStatus.FAILED: set(),
        JobStatus.CANCELLED: set(),
    }

    def __init__(self) -> None:
        self._jobs: dict[tuple[str, str], Job] = {}
        self._idempotency: dict[tuple[str, str], str] = {}

    def submit(self, tenant_id: str, task: str, idempotency_key: str, *, max_retries: int = 0) -> Job:
        if not tenant_id or not idempotency_key:
            raise ValueError("tenant_id and idempotency_key are required")
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        index_key = (tenant_id, idempotency_key)
        existing_id = self._idempotency.get(index_key)
        if existing_id:
            return self.get(tenant_id, existing_id)
        job = Job(str(uuid4()), tenant_id, task, idempotency_key, max_retries=max_retries)
        self._jobs[(tenant_id, job.id)] = job
        self._idempotency[index_key] = job.id
        return job

    def get(self, tenant_id: str, job_id: str) -> Job:
        try:
            return self._jobs[(tenant_id, job_id)]
        except KeyError as error:
            raise KeyError(f"job {job_id!r} not found for tenant") from error

    def transition(self, tenant_id: str, job_id: str, status: JobStatus) -> Job:
        job = self.get(tenant_id, job_id)
        if status not in self._ALLOWED[job.status]:
            raise ValueError(f"invalid transition: {job.status.value} -> {status.value}")
        job.status = status
        return job

    def checkpoint(self, tenant_id: str, job_id: str, state: dict[str, Any]) -> Job:
        job = self.get(tenant_id, job_id)
        if job.status not in {JobStatus.RUNNING, JobStatus.WAITING_FOR_APPROVAL}:
            raise ValueError("checkpoints require an active job")
        job.checkpoint = dict(state)
        return job

    def retry(self, tenant_id: str, job_id: str) -> Job:
        job = self.get(tenant_id, job_id)
        if job.status is not JobStatus.FAILED:
            raise ValueError("only failed jobs can be retried")
        if job.attempts >= job.max_retries:
            raise RuntimeError("retry budget exhausted")
        job.attempts += 1
        job.status = JobStatus.QUEUED
        return job

    def cancel(self, tenant_id: str, job_id: str) -> Job:
        return self.transition(tenant_id, job_id, JobStatus.CANCELLED)
