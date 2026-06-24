from __future__ import annotations

from quotalane.config.job_config import JobConfig
from quotalane.models.batch import Batch
from quotalane.models.work import WorkItem
from quotalane.scheduler.batch_packer import pack_work_items


def plan_initial_batches(config: JobConfig, work_items: list[WorkItem]) -> list[Batch]:
    return pack_work_items(
        job_id=config.job_id,
        work_items=work_items,
        safe_input_token_target=config.batching.safe_input_token_target,
        hard_input_token_cap=config.batching.hard_input_token_cap,
        max_items_per_batch=config.batching.max_items_per_batch,
        preserve_input_order=config.batching.preserve_input_order,
        allow_safe_target_overflow=config.batching.allow_safe_target_overflow,
    )
