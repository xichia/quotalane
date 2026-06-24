from pathlib import Path

from typer.testing import CliRunner

from quotalane.cli.app import app


def test_cli_resume_unknown_job(tmp_path):
    db_path = tmp_path / "empty.sqlite"
    config_path = Path(__file__).resolve().parents[1] / "examples" / "paragraph_summary_large_job.yaml"
    runner = CliRunner()
    result = runner.invoke(app, ["resume", "unknown_job_id", "--config", str(config_path), "--db", str(db_path)])
    assert result.exit_code != 0
    assert "not found in database" in result.output


def test_cli_inspect_unknown_job(tmp_path):
    db_path = tmp_path / "empty.sqlite"
    runner = CliRunner()
    result = runner.invoke(app, ["inspect", "unknown_job_id", "--db", str(db_path)])
    assert result.exit_code != 0
    assert "No job found" in result.output
