from quotalane.models.batch import BatchStatus
from quotalane.simulator.engine import run_simulation
from quotalane.storage.repositories import SQLiteRepository


def test_failed_batch_requeues_to_available_lane(small_config, db_path):
    config = small_config.model_copy(
        update={
            "simulation": small_config.simulation.model_copy(
                update={"fail_batch_ids": ["batch_001"]}
            )
        }
    )
    run_simulation(config, db_path=db_path, reset=True)
    repo = SQLiteRepository(db_path)
    events = repo.list_events(config.job_id, limit=100)
    assert any(event["event_type"] == "batch_requeued" for event in events)

    batches = {batch.batch_id: batch for batch in repo.list_batches(config.job_id)}
    assert batches["batch_001"].status == BatchStatus.completed
    assert batches["batch_001"].attempt_count == 2

    with repo.connection() as conn:
        attempts = conn.execute(
            """
            SELECT status
            FROM batch_attempts
            WHERE batch_id = ?
            ORDER BY id
            """,
            ("batch_001",),
        ).fetchall()
    assert [attempt["status"] for attempt in attempts] == ["failed", "succeeded"]
