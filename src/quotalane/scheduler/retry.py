from __future__ import annotations

from quotalane.models.batch import Batch, BatchStatus


def should_retry_batch(batch: Batch, max_attempts: int) -> bool:
    return batch.attempt_count < max_attempts


def mark_for_retry(batch: Batch) -> Batch:
    return batch.model_copy(update={"status": BatchStatus.retry_pending, "lane_id": None})
