from quotalane.simulator.engine import run_simulation


def test_simulator_estimated_elapsed_time(small_config, db_path):
    result = run_simulation(small_config, db_path=db_path, reset=True)
    assert result.estimated_elapsed_minutes == result.estimated_dispatch_windows
    assert result.estimated_elapsed_minutes >= 1
