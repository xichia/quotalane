from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from quotalane.cli.render import render_simulation_result
from quotalane.config.job_config import load_job_config
from quotalane.config.settings import DEFAULT_DB_PATH
from quotalane.simulator.engine import run_simulation

console = Console()


import yaml
from pydantic import ValidationError


def simulate(
    config_path: Annotated[Path, typer.Argument(help="Path to a QuotaLane YAML job config.")],
    db_path: Annotated[Path, typer.Option("--db", help="SQLite checkpoint database path.")] = DEFAULT_DB_PATH,
    reset: Annotated[bool, typer.Option("--reset", help="Clear existing database state before running.")] = False,
    max_windows: Annotated[int | None, typer.Option("--max-windows", help="Stop after N windows for resume demos.")] = None,
    no_windows: Annotated[bool, typer.Option("--no-windows", help="Hide dispatch-window details.")] = False,
) -> None:
    if not config_path.exists():
        raise typer.BadParameter(f"Config file not found: {config_path}")

    try:
        config = load_job_config(config_path)
    except yaml.YAMLError as e:
        raise typer.BadParameter(f"Invalid YAML in config file {config_path}: {e}")
    except (ValueError, ValidationError) as e:
        raise typer.BadParameter(f"Invalid config values in {config_path}:\n{e}")

    result = run_simulation(config, db_path=db_path, reset=reset, max_windows=max_windows)
    render_simulation_result(console, result, show_windows=not no_windows)
