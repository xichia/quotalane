from quotalane.simulator.engine import run_simulation
from quotalane.storage.repositories import SQLiteRepository


def test_checkpoint_save_load(small_config, db_path):
    run_simulation(small_config, db_path=db_path, reset=True, max_windows=1)
    repo = SQLiteRepository(db_path)
    checkpoint = repo.latest_checkpoint(small_config.job_id)
    assert checkpoint is not None
    assert checkpoint["job_id"] == small_config.job_id
