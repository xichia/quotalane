from quotalane.simulator.engine import run_simulation


def test_each_lane_gets_one_batch_per_window(small_config, db_path):
    result = run_simulation(small_config, db_path=db_path, reset=True)
    for window in result.windows:
        lane_ids = [record.lane_id for record in window.assignments]
        assert len(lane_ids) == len(set(lane_ids))


def test_first_dispatch_window_uses_each_ready_lane_once(small_config, db_path):
    result = run_simulation(small_config, db_path=db_path, reset=True, max_windows=1)

    assert len(result.windows) == 1
    assert len(result.windows[0].assignments) == len(small_config.lanes)
