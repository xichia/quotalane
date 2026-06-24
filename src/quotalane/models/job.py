from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    partially_completed = "partially_completed"


class Job(BaseModel):
    job_id: str
    job_type: str
    status: JobStatus = JobStatus.pending
    total_work_items: int = 0
    completed_work_items: int = 0
    failed_work_items: int = 0
    missing_outputs: int = 0
    total_estimated_input_tokens: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    checkpoint_path: str | None = None
