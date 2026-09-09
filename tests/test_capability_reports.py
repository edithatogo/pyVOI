from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
import pytest
from typer.testing import CliRunner

from voiage.cli import app
from voiage.contracts.capability_report import CliCapabilityReport

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT
    / "conductor/tracks/agent_safe_engineering_20260907/capability-report-contract.json"
)


def test_capability_report_is_schema_bound_and_dispatch_complete() -> None:
    result = CliRunner().invoke(app, ["capabilities", "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    CliCapabilityReport.model_validate(payload)
    schema = json.loads(CONTRACT.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(payload)
    assert schema["properties"]["dry_run"]["const"] is True
    assert set(payload) - set(schema["required"]) == {"selected_method"}


def test_published_schema_rejects_dispatch_registry_drift() -> None:
    schema = json.loads(CONTRACT.read_text(encoding="utf-8"))
    report = json.loads(CliRunner().invoke(app, ["capabilities", "--json"]).stdout)
    report["dispatch_methods"] = ["evpi"]
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(report)


def test_capability_report_rejects_dispatch_drift() -> None:
    with pytest.raises(ValueError, match="match dispatch"):
        CliCapabilityReport(
            package_version="0",
            backend="rust-backed-cpu",
            optional_modules={},
            methods=("evpi",),
            dispatch_methods=(),
        )


def test_capability_report_rejects_non_object_input() -> None:
    """The JSON contract must fail closed for non-object payloads."""
    with pytest.raises(ValueError):
        CliCapabilityReport.model_validate(None)


def test_capabilities_method_query_is_dry_run() -> None:
    result = CliRunner().invoke(app, ["capabilities", "--json", "--method", "evpi"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["dry_run"] is True
    assert set(payload) == {
        "schema_version",
        "package_version",
        "backend",
        "optional_modules",
        "methods",
        "dispatch_methods",
        "dry_run",
        "selected_method",
    }
