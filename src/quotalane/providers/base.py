from __future__ import annotations

from typing import Protocol

from quotalane.models.batch import Batch
from quotalane.models.results import BatchExecutionResult


class BatchExecutor(Protocol):
    async def execute_batch(self, batch: Batch) -> BatchExecutionResult:
        ...
