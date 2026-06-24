from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from quotalane.models.batch import Batch, BatchStatus
from quotalane.models.job import Job, JobStatus
from quotalane.models.lane import LaneState, QuotaLane
from quotalane.models.work import WorkItem, WorkStatus, sanitize_metadata
from quotalane.storage.db import connect, initialize_database


def _dt(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _parse_dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _now() -> str:
    return datetime.now(UTC).isoformat()


class SQLiteRepository:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        initialize_database(self.db_path)

    def connection(self) -> sqlite3.Connection:
        return connect(self.db_path)

    def reset(self) -> None:
        with self.connection() as conn:
            for table in (
                "batch_attempts",
                "scheduler_events",
                "checkpoints",
                "batches",
                "work_items",
                "lanes",
                "jobs",
            ):
                conn.execute(f"DELETE FROM {table}")
            conn.commit()

    def upsert_job(self, job: Job) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                  status=excluded.status,
                  total_work_items=excluded.total_work_items,
                  completed_work_items=excluded.completed_work_items,
                  failed_work_items=excluded.failed_work_items,
                  missing_outputs=excluded.missing_outputs,
                  total_estimated_input_tokens=excluded.total_estimated_input_tokens,
                  checkpoint_path=excluded.checkpoint_path,
                  updated_at=excluded.updated_at
                """,
                (
                    job.job_id,
                    job.job_type,
                    job.status.value,
                    job.total_work_items,
                    job.completed_work_items,
                    job.failed_work_items,
                    job.missing_outputs,
                    job.total_estimated_input_tokens,
                    job.checkpoint_path,
                    _dt(job.created_at),
                    _dt(job.updated_at),
                ),
            )
            conn.commit()

    def get_job(self, job_id: str) -> Job | None:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if not row:
            return None
        return Job(
            job_id=row["job_id"],
            job_type=row["job_type"],
            status=JobStatus(row["status"]),
            total_work_items=row["total_work_items"],
            completed_work_items=row["completed_work_items"],
            failed_work_items=row["failed_work_items"],
            missing_outputs=row["missing_outputs"],
            total_estimated_input_tokens=row["total_estimated_input_tokens"],
            checkpoint_path=row["checkpoint_path"],
            created_at=_parse_dt(row["created_at"]),
            updated_at=_parse_dt(row["updated_at"]),
        )

    def list_jobs(self) -> list[Job]:
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
        return [self.get_job(row["job_id"]) for row in rows if row["job_id"]]

    def upsert_work_items(self, job_id: str, items: list[WorkItem]) -> None:
        with self.connection() as conn:
            conn.executemany(
                """
                INSERT INTO work_items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(work_item_id) DO UPDATE SET
                  estimated_input_tokens=excluded.estimated_input_tokens,
                  metadata_json=excluded.metadata_json,
                  status=excluded.status,
                  attempt_count=excluded.attempt_count,
                  updated_at=excluded.updated_at
                """,
                [
                    (
                        item.work_item_id,
                        job_id,
                        item.external_id,
                        item.input_text_hash,
                        item.estimated_input_tokens,
                        json.dumps(item.metadata, sort_keys=True),
                        item.status.value,
                        item.attempt_count,
                        _dt(item.created_at),
                        _dt(item.updated_at),
                    )
                    for item in items
                ],
            )
            conn.commit()

    def list_work_items(self, job_id: str) -> list[WorkItem]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM work_items WHERE job_id = ? ORDER BY work_item_id", (job_id,)
            ).fetchall()
        return [
            WorkItem(
                work_item_id=row["work_item_id"],
                external_id=row["external_id"],
                input_text_hash=row["input_text_hash"],
                estimated_input_tokens=row["estimated_input_tokens"],
                metadata=json.loads(row["metadata_json"]),
                status=WorkStatus(row["status"]),
                attempt_count=row["attempt_count"],
                created_at=_parse_dt(row["created_at"]),
                updated_at=_parse_dt(row["updated_at"]),
            )
            for row in rows
        ]

    def update_work_statuses(self, job_id: str, statuses: dict[str, WorkStatus], increment_attempt: bool = False) -> None:
        with self.connection() as conn:
            for work_item_id, status in statuses.items():
                if increment_attempt:
                    conn.execute(
                        """
                        UPDATE work_items
                        SET status = ?, attempt_count = attempt_count + 1, updated_at = ?
                        WHERE job_id = ? AND work_item_id = ?
                        """,
                        (status.value, _now(), job_id, work_item_id),
                    )
                else:
                    conn.execute(
                        """
                        UPDATE work_items SET status = ?, updated_at = ?
                        WHERE job_id = ? AND work_item_id = ?
                        """,
                        (status.value, _now(), job_id, work_item_id),
                    )
            conn.commit()

    def upsert_batches(self, batches: list[Batch]) -> None:
        with self.connection() as conn:
            conn.executemany(
                """
                INSERT INTO batches VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(batch_id) DO UPDATE SET
                  lane_id=excluded.lane_id,
                  work_item_ids_json=excluded.work_item_ids_json,
                  estimated_input_tokens=excluded.estimated_input_tokens,
                  status=excluded.status,
                  attempt_count=excluded.attempt_count,
                  parent_batch_id=excluded.parent_batch_id,
                  error_code=excluded.error_code,
                  started_at=excluded.started_at,
                  completed_at=excluded.completed_at
                """,
                [
                    (
                        batch.batch_id,
                        batch.job_id,
                        batch.lane_id,
                        json.dumps(batch.work_item_ids),
                        batch.estimated_input_tokens,
                        batch.status.value,
                        batch.attempt_count,
                        batch.parent_batch_id,
                        batch.error_code,
                        _dt(batch.created_at),
                        _dt(batch.started_at),
                        _dt(batch.completed_at),
                    )
                    for batch in batches
                ],
            )
            conn.commit()

    def list_batches(self, job_id: str) -> list[Batch]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM batches WHERE job_id = ? ORDER BY created_at, batch_id", (job_id,)
            ).fetchall()
        return [
            Batch(
                batch_id=row["batch_id"],
                job_id=row["job_id"],
                lane_id=row["lane_id"],
                work_item_ids=json.loads(row["work_item_ids_json"]),
                estimated_input_tokens=row["estimated_input_tokens"],
                status=BatchStatus(row["status"]),
                attempt_count=row["attempt_count"],
                parent_batch_id=row["parent_batch_id"],
                error_code=row["error_code"],
                created_at=_parse_dt(row["created_at"]),
                started_at=_parse_dt(row["started_at"]),
                completed_at=_parse_dt(row["completed_at"]),
            )
            for row in rows
        ]

    def upsert_lanes(self, lanes: list[QuotaLane]) -> None:
        with self.connection() as conn:
            conn.executemany(
                """
                INSERT INTO lanes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(lane_id) DO UPDATE SET
                  state=excluded.state,
                  cooldown_until_window=excluded.cooldown_until_window,
                  in_flight_batch_id=excluded.in_flight_batch_id,
                  requests_used_current_window=excluded.requests_used_current_window,
                  input_tokens_used_current_window=excluded.input_tokens_used_current_window,
                  current_window=excluded.current_window,
                  requests_used_today=excluded.requests_used_today,
                  input_tokens_used_today=excluded.input_tokens_used_today,
                  last_request_window=excluded.last_request_window,
                  failure_count=excluded.failure_count,
                  updated_at=excluded.updated_at
                """,
                [
                    (
                        lane.lane_id,
                        lane.provider,
                        lane.model,
                        lane.api_key_env_name,
                        lane.requests_per_minute,
                        lane.input_tokens_per_minute,
                        lane.safe_input_token_target,
                        lane.hard_input_token_cap,
                        lane.daily_request_limit,
                        lane.daily_token_limit,
                        lane.state.value,
                        lane.cooldown_until_window,
                        lane.in_flight_batch_id,
                        lane.requests_used_current_window,
                        lane.input_tokens_used_current_window,
                        lane.current_window,
                        lane.requests_used_today,
                        lane.input_tokens_used_today,
                        lane.last_request_window,
                        lane.failure_count,
                        _dt(lane.updated_at),
                    )
                    for lane in lanes
                ],
            )
            conn.commit()

    def list_lanes(self) -> list[QuotaLane]:
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM lanes ORDER BY lane_id").fetchall()
        return [
            QuotaLane(
                lane_id=row["lane_id"],
                provider=row["provider"],
                model=row["model"],
                api_key_env_name=row["api_key_env_name"],
                requests_per_minute=row["requests_per_minute"],
                input_tokens_per_minute=row["input_tokens_per_minute"],
                safe_input_token_target=row["safe_input_token_target"],
                hard_input_token_cap=row["hard_input_token_cap"],
                daily_request_limit=row["daily_request_limit"],
                daily_token_limit=row["daily_token_limit"],
                state=LaneState(row["state"]),
                cooldown_until_window=row["cooldown_until_window"],
                in_flight_batch_id=row["in_flight_batch_id"],
                requests_used_current_window=row["requests_used_current_window"],
                input_tokens_used_current_window=row["input_tokens_used_current_window"],
                current_window=row["current_window"],
                requests_used_today=row["requests_used_today"],
                input_tokens_used_today=row["input_tokens_used_today"],
                last_request_window=row["last_request_window"],
                failure_count=row["failure_count"],
                updated_at=_parse_dt(row["updated_at"]),
            )
            for row in rows
        ]

    def record_attempt(
        self,
        *,
        batch_id: str,
        lane_id: str,
        attempt_number: int,
        virtual_window: int,
        status: str,
        error_code: str | None,
        input_tokens: int,
    ) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO batch_attempts
                (batch_id, lane_id, attempt_number, virtual_window, status, error_code, input_tokens, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (batch_id, lane_id, attempt_number, virtual_window, status, error_code, input_tokens, _now()),
            )
            conn.commit()

    def record_event(
        self,
        *,
        job_id: str,
        event_type: str,
        message: str,
        lane_id: str | None = None,
        batch_id: str | None = None,
        virtual_window: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        safe_details = sanitize_metadata(details or {})
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO scheduler_events
                (job_id, event_type, message, lane_id, batch_id, virtual_window, details_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    event_type,
                    message,
                    lane_id,
                    batch_id,
                    virtual_window,
                    json.dumps(safe_details, sort_keys=True),
                    _now(),
                ),
            )
            conn.commit()

    def list_events(self, job_id: str, limit: int = 50) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM scheduler_events
                WHERE job_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (job_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def save_checkpoint(self, job_id: str, virtual_window: int, state: dict[str, Any]) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO checkpoints (job_id, virtual_window, state_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (job_id, virtual_window, json.dumps(state, sort_keys=True), _now()),
            )
            conn.commit()

    def latest_checkpoint(self, job_id: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM checkpoints
                WHERE job_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (job_id,),
            ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "job_id": row["job_id"],
            "virtual_window": row["virtual_window"],
            "state": json.loads(row["state_json"]),
            "created_at": row["created_at"],
        }
