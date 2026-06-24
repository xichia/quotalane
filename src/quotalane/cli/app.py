from __future__ import annotations

import typer

from quotalane.cli.commands_inspect import inspect as inspect_command
from quotalane.cli.commands_resume import resume as resume_command
from quotalane.cli.commands_simulate import simulate as simulate_command
from quotalane.cli.commands_status import status as status_command

app = typer.Typer(help="QuotaLane: multi-key, token-aware LLM workload scheduler.")

app.command("simulate")(simulate_command)
app.command("status")(status_command)
app.command("inspect")(inspect_command)
app.command("resume")(resume_command)


if __name__ == "__main__":
    app()
