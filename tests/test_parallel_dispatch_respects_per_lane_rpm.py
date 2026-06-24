from quotalane.simulator.engine import run_simulation
from quotalane.storage.repositories import SQLiteRepository


def test_parallel_dispatch_respects_per_lane_rpm(small_config, db_path):
    run_simulation(small_config, db_path=db_path, reset=True)
    repo = SQLiteRepository(db_path)
    with repo.connection() as conn:
        rows = conn.execute(
            """
            SELECT lane_id, virtual_window, COUNT(*) AS request_count
            FROM batch_attempts
            GROUP BY lane_id, virtual_window
            """
        ).fetchall()
    assert rows
    assert all(row["request_count"] <= 1 for row in rows)
