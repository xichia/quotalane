from __future__ import annotations

from typing import Any

from quotalane.storage.repositories import SQLiteRepository


def save_scheduler_checkpoint(
    repository: SQLiteRepository, *, job_id: str, virtual_window: int, state: dict[str, Any]
) -> None:
    repository.save_checkpoint(job_id, virtual_window, state)


def load_latest_scheduler_checkpoint(repository: SQLiteRepository, job_id: str) -> dict[str, Any] | None:
    return repository.latest_checkpoint(job_id)
