from __future__ import annotations

import asyncio
import random

from quotalane.config.job_config import SimulationConfig
from quotalane.models.batch import Batch
from quotalane.models.results import BatchExecutionResult, BatchExecutionStatus, BatchUsage


class FakeBatchExecutor:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.fail_batch_ids = set(config.fail_batch_ids)
        self._rng = random.Random(config.random_seed)
        self._failed_once: set[str] = set()

    async def execute_batch(self, batch: Batch) -> BatchExecutionResult:
        # Keep tests and demos fast. The simulator reports virtual minutes rather than real waits.
        await asyncio.sleep(min(self.config.provider_latency_seconds, 0.02))

        if batch.batch_id in self.fail_batch_ids and batch.batch_id not in self._failed_once:
            self._failed_once.add(batch.batch_id)
            return BatchExecutionResult(
                batch_id=batch.batch_id,
                status=BatchExecutionStatus.failed,
                failed_work_item_ids=list(batch.work_item_ids),
                usage=BatchUsage(input_tokens=batch.estimated_input_tokens),
                error_code="SIMULATED_BATCH_FAILURE",
            )

        missing: list[str] = []
        completed: list[str] = []
        for item_id in batch.work_item_ids:
            if self.config.missing_output_ratio > 0 and self._rng.random() < self.config.missing_output_ratio:
                missing.append(item_id)
            else:
                completed.append(item_id)

        status = BatchExecutionStatus.succeeded
        if missing:
            status = BatchExecutionStatus.partially_succeeded

        return BatchExecutionResult(
            batch_id=batch.batch_id,
            status=status,
            completed_work_item_ids=completed,
            missing_work_item_ids=missing,
            usage=BatchUsage(input_tokens=batch.estimated_input_tokens),
        )
