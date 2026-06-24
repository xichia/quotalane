from quotalane.simulator.engine import run_simulation


def test_multi_lane_parallel_dispatch(small_config, db_path):
    result = run_simulation(small_config, db_path=db_path, reset=True)
    assert result.parallel_lanes_used == 2
    assert result.completed_batches > 0
    assert result.final_status.value == "completed"
