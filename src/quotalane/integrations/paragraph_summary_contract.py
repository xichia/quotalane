from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from quotalane.models.results import BatchExecutionResult


class ScheduledBatch(BaseModel):
    batch_id: str
    job_id: str
    lane_id: str
    work_item_ids: list[str]
    estimated_input_tokens: int
    provider: str
    model: str
    metadata: dict[str, str] = Field(default_factory=dict)


class ParagraphSummaryBatchExecutor(Protocol):
    async def execute_batch(self, batch: ScheduledBatch) -> BatchExecutionResult:
        """Resolve texts service-side, call provider, write artifacts, and return item results."""
        ...
