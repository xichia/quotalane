from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from quotalane.config.settings import DEFAULT_DB_PATH
from quotalane.storage.repositories import SQLiteRepository

console = Console()


def status(
    db_path: Annotated[
        Path, typer.Option("--db", help="SQLite checkpoint database path.")
    ] = DEFAULT_DB_PATH,
) -> None:
    repo = SQLiteRepository(db_path)
    jobs = [job for job in repo.list_jobs() if job is not None]
    table = Table(title="QuotaLane jobs")
    table.add_column("Job")
    table.add_column("Status")
    table.add_column("Completed")
    table.add_column("Failed")
    table.add_column("Missing")
    table.add_column("Tokens")
    for job in jobs:
        table.add_row(
            job.job_id,
            job.status.value,
            f"{job.completed_work_items:,}/{job.total_work_items:,}",
            str(job.failed_work_items),
            str(job.missing_outputs),
            f"{job.total_estimated_input_tokens:,}",
        )
    console.print(table)
