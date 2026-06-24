from quotalane.models.work import WorkItem
from quotalane.scheduler.batch_packer import pack_work_items


def test_batch_packing_under_safe_target_for_small_remainder():
    items = [
        WorkItem(
            work_item_id=f"w{i}",
            external_id=f"e{i}",
            input_text_hash=f"h{i}",
            estimated_input_tokens=10_000,
        )
        for i in range(5)
    ]
    batches = pack_work_items(
        job_id="job",
        work_items=items,
        safe_input_token_target=225_000,
        hard_input_token_cap=240_000,
        max_items_per_batch=500,
    )
    assert len(batches) == 1
    assert batches[0].estimated_input_tokens == 50_000
