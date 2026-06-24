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


def test_cli_simulate_missing_config():
    runner = CliRunner()
    result = runner.invoke(app, ["simulate", "does_not_exist.yaml"])
    assert result.exit_code != 0
    assert "Config file not found" in result.output


def test_cli_simulate_invalid_config(tmp_path):
    invalid_config = tmp_path / "invalid.yaml"
    invalid_config.write_text("not: a: valid: yaml: - [")
    runner = CliRunner()
    result = runner.invoke(app, ["simulate", str(invalid_config)])
    assert result.exit_code != 0
    assert "Invalid YAML" in result.output

    invalid_values = tmp_path / "invalid_values.yaml"
    invalid_values.write_text("job_id: test\njob_type: test\nprovider: test\nmodel: test\nlanes: []")
    result = runner.invoke(app, ["simulate", str(invalid_values)])
    assert result.exit_code != 0
    assert "Invalid config values" in result.output
