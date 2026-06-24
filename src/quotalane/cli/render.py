from __future__ import annotations

from rich.console import Console
from rich.table import Table

from quotalane.simulator.engine import SimulationResult


def render_simulation_result(
    console: Console, result: SimulationResult, *, show_windows: bool = True
) -> None:
    console.print("[bold]QuotaLane simulation[/bold]\n")
    summary = Table(show_header=False)
    summary.add_column("Metric")
    summary.add_column("Value")
    summary.add_row("Job", result.job_id)
    summary.add_row("Work items", f"{result.work_items:,}")
    summary.add_row("Estimated input tokens", f"{result.estimated_input_tokens:,}")
    summary.add_row("Lanes", str(result.lane_count))
    summary.add_row("Batches planned", str(result.batches_planned))
    console.print(summary)

    if show_windows:
        for window in result.windows:
            console.print(f"\n[bold]Dispatch window {window.window}:[/bold]")
            for record in window.assignments:
                status = f" ({record.status})" if record.status else ""
                console.print(
                    f"  {record.lane_id} -> {record.batch_id} -> "
                    f"{record.estimated_input_tokens:,} tokens{status}"
                )

    console.print("\n[bold]Result:[/bold]")
    console.print(f"  completed batches: {result.completed_batches}")
    console.print(f"  failed batches: {result.failed_batches}")
    console.print(f"  missing outputs: {result.missing_outputs}")
    console.print(f"  parallel lanes used: {result.parallel_lanes_used}")
    console.print(f"  estimated dispatch windows: {result.estimated_dispatch_windows}")
    console.print(f"  estimated elapsed time: ~{result.estimated_elapsed_minutes} minutes")
    console.print(f"  final status: {result.final_status.value}")
