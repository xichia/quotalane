from quotalane.simulator.engine import run_simulation
from quotalane.storage.repositories import SQLiteRepository


def test_failed_lane_does_not_block_healthy_lanes(small_config, db_path):
    config = small_config.model_copy(
        update={"simulation": small_config.simulation.model_copy(update={"fail_batch_ids": ["batch_001"]})}
    )
    result = run_simulation(config, db_path=db_path, reset=True)
    assert result.completed_batches > 0
    repo = SQLiteRepository(db_path)
    lanes = repo.list_lanes()
    assert any(lane.failure_count > 0 for lane in lanes)
    assert any(lane.failure_count == 0 for lane in lanes)
