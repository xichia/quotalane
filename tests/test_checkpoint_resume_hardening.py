from quotalane.models.batch import BatchStatus
from quotalane.models.job import JobStatus
from quotalane.simulator.engine import run_simulation
from quotalane.storage.repositories import SQLiteRepository


def test_resume_does_not_duplicate_completed_work(small_config, db_path):
    first = run_simulation(small_config, db_path=db_path, reset=True, max_windows=1)

    # Assert something completed
    repo = SQLiteRepository(db_path)
    completed_items_before = len(
        [
            item
            for item in repo.list_work_items(small_config.job_id)
            if item.status.value == "completed"
        ]
    )
    assert completed_items_before > 0

    first_batch_ids = [record.batch_id for window in first.windows for record in window.assignments]

    resumed = run_simulation(small_config, db_path=db_path, resume=True)
    assert resumed.final_status == JobStatus.completed

    completed_items_after = len(
        [
            item
            for item in repo.list_work_items(small_config.job_id)
            if item.status.value == "completed"
        ]
    )
    # The total completed items should match the job total
    assert completed_items_after == len(repo.list_work_items(small_config.job_id))

    # Ensure attempt counts are exactly 1 for batches completed in the first run
    with repo.connection() as conn:
        attempt_counts = {
            row["batch_id"]: row["attempt_count"]
            for row in conn.execute(
                """
                SELECT batch_id, COUNT(*) AS attempt_count
                FROM batch_attempts
                WHERE batch_id IN ({}) AND status = 'completed'
                GROUP BY batch_id
                """.format(",".join("?" for _ in first_batch_ids)),
                first_batch_ids,
            ).fetchall()
        }

    for batch_id in first_batch_ids:
        # Check if the batch was completed in the first run
        if attempt_counts.get(batch_id):
            assert attempt_counts[batch_id] == 1, f"Batch {batch_id} should not be retried"


def test_resume_reconstructs_queued_and_retry_state(small_config, db_path):
    # Change config to guarantee a failure on the first batch
    small_config.simulation.fail_batch_ids = ["batch_0000_0000"]
    small_config.retry.max_attempts = 3

    run_simulation(small_config, db_path=db_path, reset=True, max_windows=1)
    repo = SQLiteRepository(db_path)

    # Check if there are queued/retry batches
    batches = repo.list_batches(small_config.job_id)
    queued_batches = [
        b for b in batches if b.status in {BatchStatus.queued, BatchStatus.retry_pending}
    ]
    assert len(queued_batches) > 0, "Should have queued retry batches"

    # The fake_executor only fails a batch once if its id is in fail_batch_ids.
    # So we don't need to remove the fail_batch_ids for it to succeed on retry.
    resumed = run_simulation(small_config, db_path=db_path, resume=True)

    assert resumed.final_status == JobStatus.completed

    # Verify retry metadata wasn't lost (i.e. attempt count is > 1 for those batches)
    batches_after = {b.batch_id: b for b in repo.list_batches(small_config.job_id)}
    for b in queued_batches:
        if b.attempt_count > 0:
            b_after = batches_after.get(b.batch_id)
            if b_after:
                assert b_after.attempt_count > 1


def test_missing_outputs_retry_survives_resume(small_config, db_path):
    small_config.simulation.missing_output_ratio = 1.0
    small_config.retry.requeue_missing_outputs = True
    small_config.retry.max_attempts = 3

    run_simulation(small_config, db_path=db_path, reset=True, max_windows=1)

    repo = SQLiteRepository(db_path)
    batches = repo.list_batches(small_config.job_id)
    retry_batches = [b for b in batches if b.batch_id.startswith("retry_")]
    assert len(retry_batches) > 0, "Missing outputs should generate retry batches"

    small_config.simulation.missing_output_ratio = 0.0
    resumed = run_simulation(small_config, db_path=db_path, resume=True)

    assert resumed.final_status == JobStatus.completed


def test_resume_events_recorded(small_config, db_path):
    # Run a partial simulation to trigger checkpoint save
    run_simulation(small_config, db_path=db_path, reset=True, max_windows=1)

    repo = SQLiteRepository(db_path)
    events = repo.list_events(small_config.job_id)
    event_types = [e["event_type"] for e in events]
    assert "checkpoint_saved" in event_types

    # Resume the simulation
    run_simulation(small_config, db_path=db_path, resume=True)

    events_after = repo.list_events(small_config.job_id)
    event_types_after = [e["event_type"] for e in events_after]
    assert "job_resumed" in event_types_after

    # Sanity check no sensitive data in any event
    for event in events_after:
        details = event.get("details_json", "")
        assert "SECRET" not in details
