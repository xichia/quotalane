from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class BatchStatus(str, Enum):
    pending = "pending"
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    partially_completed = "partially_completed"
    retry_pending = "retry_pending"


class Batch(BaseModel):
    batch_id: str
    job_id: str
    lane_id: str | None = None
    work_item_ids: list[str]
    estimated_input_tokens: int = Field(ge=0)
    status: BatchStatus = BatchStatus.pending
    attempt_count: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_code: str | None = None
    parent_batch_id: str | None = None

    @property
    def size(self) -> int:
        return len(self.work_item_ids)

    def assign(self, lane_id: str) -> Batch:
        return self.model_copy(
            update={
                "lane_id": lane_id,
                "status": BatchStatus.processing,
                "started_at": utc_now(),
                "attempt_count": self.attempt_count + 1,
            }
        )

    def complete(self) -> Batch:
        return self.model_copy(
            update={"status": BatchStatus.completed, "completed_at": utc_now(), "error_code": None}
        )

    def fail(self, error_code: str) -> Batch:
        return self.model_copy(
            update={"status": BatchStatus.failed, "completed_at": utc_now(), "error_code": error_code}
        )
