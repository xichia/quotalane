from pathlib import Path

from typer.testing import CliRunner

from quotalane.cli.app import app


def test_cli_simulate(tmp_path):
    config_path = Path(__file__).resolve().parents[1] / "examples" / "paragraph_summary_large_job.yaml"
    db_path = tmp_path / "cli.sqlite"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["simulate", str(config_path), "--db", str(db_path), "--reset", "--max-windows", "1", "--no-windows"],
    )
    assert result.exit_code == 0
    assert "QuotaLane simulation" in result.output
