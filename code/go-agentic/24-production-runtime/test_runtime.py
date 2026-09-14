import pytest

from runtime import DurableRuntime, JobStatus


def test_job_moves_through_approval_to_success():
    runtime = DurableRuntime()
    job = runtime.submit("tenant-a", "send-email", "key-1", max_retries=2)
    runtime.transition("tenant-a", job.id, JobStatus.RUNNING)
    runtime.checkpoint("tenant-a", job.id, {"draft": "hello"})
    runtime.transition("tenant-a", job.id, JobStatus.WAITING_FOR_APPROVAL)
    runtime.transition("tenant-a", job.id, JobStatus.RUNNING)
    runtime.transition("tenant-a", job.id, JobStatus.SUCCEEDED)
    assert runtime.get("tenant-a", job.id).status is JobStatus.SUCCEEDED
    assert runtime.get("tenant-a", job.id).checkpoint == {"draft": "hello"}


def test_idempotency_is_scoped_to_tenant():
    runtime = DurableRuntime()
    first = runtime.submit("tenant-a", "task", "same")
    repeated = runtime.submit("tenant-a", "task", "same")
    other_tenant = runtime.submit("tenant-b", "task", "same")
    assert repeated.id == first.id
    assert other_tenant.id != first.id
    with pytest.raises(KeyError):
        runtime.get("tenant-b", first.id)


def test_retry_budget_and_checkpoint_resume():
    runtime = DurableRuntime()
    job = runtime.submit("tenant-a", "task", "key", max_retries=1)
    runtime.transition("tenant-a", job.id, JobStatus.RUNNING)
    runtime.checkpoint("tenant-a", job.id, {"cursor": 7})
    runtime.transition("tenant-a", job.id, JobStatus.FAILED)
    resumed = runtime.retry("tenant-a", job.id)
    assert resumed.status is JobStatus.QUEUED
    assert resumed.attempts == 1
    assert resumed.checkpoint == {"cursor": 7}
    runtime.transition("tenant-a", job.id, JobStatus.RUNNING)
    runtime.transition("tenant-a", job.id, JobStatus.FAILED)
    with pytest.raises(RuntimeError, match="budget"):
        runtime.retry("tenant-a", job.id)


def test_cancel_and_invalid_transition():
    runtime = DurableRuntime()
    job = runtime.submit("tenant-a", "task", "key")
    runtime.cancel("tenant-a", job.id)
    assert runtime.get("tenant-a", job.id).status is JobStatus.CANCELLED
    with pytest.raises(ValueError, match="invalid transition"):
        runtime.transition("tenant-a", job.id, JobStatus.SUCCEEDED)
