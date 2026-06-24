from __future__ import annotations

from collections.abc import Sequence

from quotalane.models.batch import Batch, BatchStatus
from quotalane.models.work import WorkItem


class BatchPackingError(ValueError):
    pass


def _batch_id(index: int) -> str:
    return f"batch_{index:03d}"


def pack_work_items(
    *,
    job_id: str,
    work_items: Sequence[WorkItem],
    safe_input_token_target: int,
    hard_input_token_cap: int,
    max_items_per_batch: int,
    preserve_input_order: bool = True,
    allow_safe_target_overflow: bool = True,
    start_index: int = 1,
    batch_id_prefix: str = "batch",
) -> list[Batch]:
    """Pack work items into deterministic near-target token batches.

    The default algorithm preserves input order and greedily appends work items until adding the
    next item would exceed the safe target. A slight safe-target overflow is allowed only when the
    current batch is materially under-filled and the new item remains below the hard cap.
    """
    if safe_input_token_target > hard_input_token_cap:
        raise BatchPackingError("safe_input_token_target must be <= hard_input_token_cap")
    if max_items_per_batch <= 0:
        raise BatchPackingError("max_items_per_batch must be positive")

    ordered_items = (
        list(work_items)
        if preserve_input_order
        else sorted(work_items, key=lambda w: w.work_item_id)
    )
    batches: list[Batch] = []
    current_ids: list[str] = []
    current_tokens = 0
    batch_number = start_index

    def emit() -> None:
        nonlocal current_ids, current_tokens, batch_number
        if not current_ids:
            return
        batch_id = f"{batch_id_prefix}_{batch_number:03d}"
        batches.append(
            Batch(
                batch_id=batch_id,
                job_id=job_id,
                work_item_ids=current_ids,
                estimated_input_tokens=current_tokens,
                status=BatchStatus.queued,
            )
        )
        current_ids = []
        current_tokens = 0
        batch_number += 1

    for item in ordered_items:
        tokens = item.estimated_input_tokens
        if tokens > hard_input_token_cap:
            raise BatchPackingError(
                f"work item {item.work_item_id} has {tokens} tokens, "
                f"above hard cap {hard_input_token_cap}"
            )

        would_exceed_hard = current_tokens + tokens > hard_input_token_cap
        would_exceed_safe = current_tokens + tokens > safe_input_token_target
        would_exceed_items = len(current_ids) + 1 > max_items_per_batch

        if current_ids and (would_exceed_hard or would_exceed_items):
            emit()

        if current_ids and would_exceed_safe and not would_exceed_hard:
            underfilled = current_tokens < int(safe_input_token_target * 0.90)
            if not (allow_safe_target_overflow and underfilled):
                emit()

        current_ids.append(item.work_item_id)
        current_tokens += tokens

        if current_tokens >= safe_input_token_target or len(current_ids) >= max_items_per_batch:
            # Keep a near-target batch rather than trying to squeeze in more after reaching target.
            emit()

    emit()
    return batches
