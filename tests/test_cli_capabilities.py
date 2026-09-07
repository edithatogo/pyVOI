"""Tests for the side-effect-free capability report."""

import json

from typer.testing import CliRunner

from voiage import cli


def test_capabilities_json_is_dry_run_and_machine_readable() -> None:
    result = CliRunner().invoke(cli.app, ["capabilities", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "1.0.0"
    assert payload["dry_run"] is True
    assert "evpi" in payload["methods"]
    assert set(payload["optional_modules"]) == {"jax", "torch", "polars", "pyarrow"}
    assert all(isinstance(value, bool) for value in payload["optional_modules"].values())
