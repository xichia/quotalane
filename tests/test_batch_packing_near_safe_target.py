from quotalane.scheduler.planner import plan_initial_batches
from quotalane.simulator.scenarios import generate_fake_paragraph_work_items


def test_batch_packing_near_safe_target(small_config):
    items = generate_fake_paragraph_work_items(small_config.simulation)
    batches = plan_initial_batches(small_config, items)
    assert len(batches) >= 2
    full_batches = batches[:-1]
    assert all(batch.estimated_input_tokens >= 200_000 for batch in full_batches)
    assert all(batch.estimated_input_tokens <= 240_000 for batch in batches)
