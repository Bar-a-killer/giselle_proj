import threading
import uuid
from dataclasses import dataclass
from typing import Literal

JobStatus = Literal["pending", "running", "done", "error"]

ACTIVE_STATUSES = ("pending", "running")


@dataclass
class Job:
    id: str
    status: JobStatus = "pending"
    counts: dict | None = None
    error: str | None = None


_jobs: dict[str, Job] = {}
_lock = threading.Lock()


def try_create_job(max_active: int) -> Job | None:
    """Atomically create a job iff fewer than max_active are pending/running.

    Using this instead of a separate count_active() + create_job() avoids a race where two
    concurrent requests each see room for one more job and both get created.
    """
    with _lock:
        active = sum(1 for job in _jobs.values() if job.status in ACTIVE_STATUSES)
        if active >= max_active:
            return None
        job = Job(id=str(uuid.uuid4()))
        _jobs[job.id] = job
        return job


def get_job(job_id: str) -> Job | None:
    with _lock:
        return _jobs.get(job_id)


def set_running(job_id: str) -> None:
    with _lock:
        _jobs[job_id].status = "running"


def set_done(job_id: str, counts: dict) -> None:
    with _lock:
        job = _jobs[job_id]
        job.status = "done"
        job.counts = counts


def set_error(job_id: str, error: str) -> None:
    with _lock:
        job = _jobs[job_id]
        job.status = "error"
        job.error = error
