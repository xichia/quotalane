from quotalane.models.job import JobStatus
from quotalane.simulator.engine import run_simulation
from quotalane.storage.repositories import SQLiteRepository


def test_checkpoint_resume_multi_lane_job(small_config, db_path):
    first = run_simulation(small_config, db_path=db_path, reset=True, max_windows=1)
    assert first.final_status in {JobStatus.partially_completed, JobStatus.completed}
    first_batch_ids = [record.batch_id for window in first.windows for record in window.assignments]

    resumed = run_simulation(small_config, db_path=db_path, resume=True)

    assert resumed.final_status == JobStatus.completed

    repo = SQLiteRepository(db_path)
    with repo.connection() as conn:
        attempt_counts = {
            row["batch_id"]: row["attempt_count"]
            for row in conn.execute(
                """
                SELECT batch_id, COUNT(*) AS attempt_count
                FROM batch_attempts
                WHERE batch_id IN ({})
                GROUP BY batch_id
                """.format(",".join("?" for _ in first_batch_ids)),
                first_batch_ids,
            ).fetchall()
        }
    assert attempt_counts == {batch_id: 1 for batch_id in first_batch_ids}
