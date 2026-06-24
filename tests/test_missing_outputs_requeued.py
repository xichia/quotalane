from quotalane.simulator.engine import run_simulation
from quotalane.storage.repositories import SQLiteRepository


def test_missing_outputs_requeued(small_config, db_path):
    config = small_config.model_copy(
        update={"simulation": small_config.simulation.model_copy(update={"missing_output_ratio": 0.02})}
    )
    run_simulation(config, db_path=db_path, reset=True)
    repo = SQLiteRepository(db_path)
    events = repo.list_events(config.job_id, limit=100)
    assert any(event["event_type"] == "missing_outputs_requeued" for event in events)
    assert any(batch.batch_id.startswith("retry_") for batch in repo.list_batches(config.job_id))
