import pytest

from quotalane.models.work import WorkItem
from quotalane.scheduler.batch_packer import BatchPackingError, pack_work_items


def test_batch_packing_never_exceeds_hard_cap(small_config):
    items = [
        WorkItem(
            work_item_id=f"w{i}",
            external_id=f"e{i}",
            input_text_hash=f"h{i}",
            estimated_input_tokens=80_000,
        )
        for i in range(10)
    ]
    batches = pack_work_items(
        job_id="job",
        work_items=items,
        safe_input_token_target=225_000,
        hard_input_token_cap=240_000,
        max_items_per_batch=500,
    )
    assert all(batch.estimated_input_tokens <= 240_000 for batch in batches)


def test_batch_packing_can_fill_exactly_to_hard_cap_when_allowed():
    items = [
        WorkItem(
            work_item_id=f"w{i}",
            external_id=f"e{i}",
            input_text_hash=f"h{i}",
            estimated_input_tokens=80_000,
        )
        for i in range(3)
    ]
    batches = pack_work_items(
        job_id="job",
        work_items=items,
        safe_input_token_target=225_000,
        hard_input_token_cap=240_000,
        max_items_per_batch=500,
        allow_safe_target_overflow=True,
    )
    assert [batch.estimated_input_tokens for batch in batches] == [240_000]


def test_batch_packing_respects_safe_target_when_overflow_disabled():
    items = [
        WorkItem(
            work_item_id=f"w{i}",
            external_id=f"e{i}",
            input_text_hash=f"h{i}",
            estimated_input_tokens=80_000,
        )
        for i in range(3)
    ]
    batches = pack_work_items(
        job_id="job",
        work_items=items,
        safe_input_token_target=225_000,
        hard_input_token_cap=240_000,
        max_items_per_batch=500,
        allow_safe_target_overflow=False,
    )
    assert [batch.estimated_input_tokens for batch in batches] == [160_000, 80_000]


def test_batch_packing_rejects_single_item_above_hard_cap():
    item = WorkItem(
        work_item_id="w1", external_id="e1", input_text_hash="h1", estimated_input_tokens=250_001
    )
    with pytest.raises(BatchPackingError):
        pack_work_items(
            job_id="job",
            work_items=[item],
            safe_input_token_target=225_000,
            hard_input_token_cap=240_000,
            max_items_per_batch=500,
        )
