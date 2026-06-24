from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class BatchExecutionStatus(str, Enum):
    succeeded = "succeeded"
    failed = "failed"
    partially_succeeded = "partially_succeeded"


class BatchUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    provider_request_count: int = 1


class BatchExecutionResult(BaseModel):
    batch_id: str
    status: BatchExecutionStatus
    completed_work_item_ids: list[str] = Field(default_factory=list)
    failed_work_item_ids: list[str] = Field(default_factory=list)
    missing_work_item_ids: list[str] = Field(default_factory=list)
    usage: BatchUsage = Field(default_factory=BatchUsage)
    error_code: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.status == BatchExecutionStatus.succeeded

    @property
    def has_missing_outputs(self) -> bool:
        return bool(self.missing_work_item_ids)
