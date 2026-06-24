from __future__ import annotations

from quotalane.models.batch import Batch, BatchStatus


def create_missing_output_retry_batch(
    *,
    parent_batch: Batch,
    missing_work_item_ids: list[str],
    estimated_tokens_by_id: dict[str, int],
    retry_batch_id: str,
) -> Batch:
    estimated_tokens = sum(estimated_tokens_by_id[item_id] for item_id in missing_work_item_ids)
    return Batch(
        batch_id=retry_batch_id,
        job_id=parent_batch.job_id,
        work_item_ids=missing_work_item_ids,
        estimated_input_tokens=estimated_tokens,
        status=BatchStatus.queued,
        attempt_count=parent_batch.attempt_count,
        parent_batch_id=parent_batch.batch_id,
    )
