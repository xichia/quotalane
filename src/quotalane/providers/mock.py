from __future__ import annotations

from quotalane.models.batch import Batch
from quotalane.models.results import BatchExecutionResult, BatchExecutionStatus, BatchUsage


class MockBatchExecutor:
    async def execute_batch(self, batch: Batch) -> BatchExecutionResult:
        return BatchExecutionResult(
            batch_id=batch.batch_id,
            status=BatchExecutionStatus.succeeded,
            completed_work_item_ids=list(batch.work_item_ids),
            usage=BatchUsage(input_tokens=batch.estimated_input_tokens),
        )
