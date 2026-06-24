from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from quotalane.cli.render import render_simulation_result
from quotalane.config.job_config import load_job_config
from quotalane.config.settings import DEFAULT_DB_PATH
from quotalane.simulator.engine import run_simulation
from quotalane.storage.repositories import SQLiteRepository

console = Console()


def resume(
    job_id: Annotated[str, typer.Argument(help="Job ID to resume.")],
    config_path: Annotated[Path, typer.Option("--config", help="Path to the original YAML job config.")] = Path(
        "examples/paragraph_summary_large_job.yaml"
    ),
    db_path: Annotated[Path, typer.Option("--db", help="SQLite checkpoint database path.")] = DEFAULT_DB_PATH,
    no_windows: Annotated[bool, typer.Option("--no-windows", help="Hide dispatch-window details.")] = False,
) -> None:
    if not config_path.exists():
        raise typer.BadParameter(f"Config file not found: {config_path}")

    repo = SQLiteRepository(db_path)
    if repo.get_job(job_id) is None:
        raise typer.BadParameter(f"Job {job_id!r} not found in database. Cannot resume.")

    config = load_job_config(config_path)
    if config.job_id != job_id:
        raise typer.BadParameter(f"Config job_id is {config.job_id!r}, not {job_id!r}")

    result = run_simulation(config, db_path=db_path, resume=True)
    render_simulation_result(console, result, show_windows=not no_windows)
