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
    assert all(
        isinstance(value, bool) for value in payload["optional_modules"].values()
    )


def test_capabilities_reports_structured_unsupported_method_error() -> None:
    result = CliRunner().invoke(
        cli.app, ["capabilities", "--json", "--method", "not-a-method"]
    )
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "unsupported_method"
    assert payload["error"]["action"] == "choose one of available_methods"
    assert payload["dry_run"] is True


def test_capabilities_selects_supported_method_without_evaluation() -> None:
    result = CliRunner().invoke(cli.app, ["capabilities", "--json", "--method", "EVPI"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["selected_method"] == "evpi"
    assert payload["dry_run"] is True


def test_capabilities_text_reports_selected_method() -> None:
    result = CliRunner().invoke(cli.app, ["capabilities", "--method", "EVPI"])
    assert result.exit_code == 0
    assert "selected method: evpi (available)" in result.stdout
