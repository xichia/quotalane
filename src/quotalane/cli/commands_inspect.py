from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from quotalane.config.settings import DEFAULT_DB_PATH
from quotalane.storage.repositories import SQLiteRepository

console = Console()


def inspect(
    job_id: Annotated[str, typer.Argument(help="Job ID to inspect.")],
    db_path: Annotated[Path, typer.Option("--db", help="SQLite checkpoint database path.")] = DEFAULT_DB_PATH,
    limit_events: Annotated[int, typer.Option("--limit-events", help="Recent events to show.")] = 10,
) -> None:
    repo = SQLiteRepository(db_path)
    job = repo.get_job(job_id)
    if job is None:
        raise typer.BadParameter(f"No job found: {job_id}")

    console.print(f"[bold]{job.job_id}[/bold]")
    console.print(f"Status: {job.status.value}")
    console.print(f"Work items: {job.completed_work_items:,}/{job.total_work_items:,} completed")
    console.print(f"Failed: {job.failed_work_items:,}")
    console.print(f"Missing outputs: {job.missing_outputs:,}")
    console.print(f"Estimated input tokens: {job.total_estimated_input_tokens:,}")

    batch_table = Table(title="Batches")
    batch_table.add_column("Status")
    batch_table.add_column("Count")
    counts: dict[str, int] = {}
    for batch in repo.list_batches(job_id):
        counts[batch.status.value] = counts.get(batch.status.value, 0) + 1
    for status, count in sorted(counts.items()):
        batch_table.add_row(status, str(count))
    console.print(batch_table)

    event_table = Table(title="Recent scheduler events")
    event_table.add_column("Window")
    event_table.add_column("Type")
    event_table.add_column("Lane")
    event_table.add_column("Batch")
    event_table.add_column("Message")
    for event in repo.list_events(job_id, limit=limit_events):
        event_table.add_row(
            str(event.get("virtual_window") or ""),
            str(event["event_type"]),
            str(event.get("lane_id") or ""),
            str(event.get("batch_id") or ""),
            str(event["message"]),
        )
    console.print(event_table)
