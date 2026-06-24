from quotalane.simulator.engine import run_simulation


def test_simulator_parallel_windows(small_config, db_path):
    result = run_simulation(small_config, db_path=db_path, reset=True)
    assert result.windows
    assert any(len(window.assignments) == 2 for window in result.windows)
