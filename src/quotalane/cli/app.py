from __future__ import annotations

import typer

from quotalane.cli.commands_inspect import inspect as inspect_command
from quotalane.cli.commands_resume import resume as resume_command
from quotalane.cli.commands_simulate import simulate as simulate_command
from quotalane.cli.commands_status import status as status_command

app = typer.Typer(
    help="QuotaLane: a multi-key, token-aware LLM workload scheduler.\n\nUse this tool to simulate, inspect, and resume long-running LLM batch jobs safely."
)

# Re-apply simulate command without the extra decorator, the typper app will just use the function docstring or help parameter in app.command
app.command("simulate", help="Simulate a workload based on a YAML job configuration.")(simulate_command)
app.command("status", help="List all jobs and their completion status.")(status_command)
app.command("inspect", help="View detailed batch and event status for a specific job.")(inspect_command)
app.command("resume", help="Resume an incomplete job from its last SQLite checkpoint.")(resume_command)


if __name__ == "__main__":
    app()
