"""Executable and contract assurance for issue #572 forecast-signal value."""

# pyright: reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownLambdaType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnusedCallResult=false

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
import pytest
from typer.testing import CliRunner

import voiage
from voiage.cli import app
from voiage.contracts.forecast_signal_information import (
    FORECAST_SIGNAL_INFORMATION_INPUT_SCHEMA_V1,
    FORECAST_SIGNAL_INFORMATION_RESULT_SCHEMA_V1,
    validate_forecast_signal_information_result_semantics,
    validate_forecast_signal_information_semantics,
)
from voiage.exceptions import InputError
import voiage.methods.forecast_signal_information as forecast_signal_module
from voiage.methods.forecast_signal_information import (
    ForecastSignalInformationResult,
    forecast_signal_information_value,
)

ROOT = Path(__file__).parents[1]
CONTRACT = ROOT / "specs/frontier/forecast-signal-information/v1"


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _input() -> dict[str, Any]:
    return _json(CONTRACT / "fixtures/normative/input.json")


def _evaluate(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return forecast_signal_information_value(
        payload if payload is not None else _input()
    ).to_contract_dict()


def test_portable_schemas_match_installed_contract_and_normative_fixture() -> None:
    input_schema = _json(
        CONTRACT / "schemas/forecast-signal-information-input.schema.json"
    )
    result_schema = _json(
        CONTRACT / "schemas/forecast-signal-information-result.schema.json"
    )
    expected = _json(CONTRACT / "fixtures/normative/expected.json")
    assert input_schema == FORECAST_SIGNAL_INFORMATION_INPUT_SCHEMA_V1
    assert result_schema == FORECAST_SIGNAL_INFORMATION_RESULT_SCHEMA_V1
    Draft202012Validator(input_schema).validate(_input())
    Draft202012Validator(result_schema).validate(expected)
    assert _evaluate() == expected


def test_analytical_newsvendor_signal_values_decisions_cost_and_regret() -> None:
    result = _evaluate()
    assert result["baseline"] == {
        "expected_action_values": {"order-50": 200.0, "order-100": 240.0},
        "choice_tie": ["order-100"],
        "value": 240.0,
    }
    partitions = {item["signal_id"]: item for item in result["signal_partitions"]}
    assert partitions["signal-low"]["probability"] == pytest.approx(0.44)
    assert partitions["signal-low"]["deployed_choice_tie"] == ["order-50"]
    assert partitions["signal-high"]["probability"] == pytest.approx(0.56)
    assert partitions["signal-high"]["deployed_choice_tie"] == ["order-100"]
    assert result["value"] == pytest.approx(
        {
            "counterfactual_timely_oracle": 40.0,
            "gross_deployed": 40.0,
            "calibration_loss": 0.0,
            "cost": 10.0,
            "net_deployed": 30.0,
            "maximum_price": 40.0,
        }
    )
    assert result["regret"] == pytest.approx(
        {"baseline_expected": 80.0, "deployed_expected": 40.0, "avoided": 40.0}
    )
    assert result["diagnostics"]["weighted_calibration_l1"] == pytest.approx(0.0)
    assert result["assurance"]["accuracy_is_value"] is False


def test_no_skill_signal_has_zero_value() -> None:
    payload = _input()
    for signal in payload["signals"]:
        signal["likelihood_by_outcome"] = {"demand-low": 0.5, "demand-high": 0.5}
        signal["reported_outcome_probabilities"] = {
            "demand-low": 0.4,
            "demand-high": 0.6,
        }
    result = _evaluate(payload)
    assert result["value"]["counterfactual_timely_oracle"] == pytest.approx(0.0)
    assert result["value"]["gross_deployed"] == pytest.approx(0.0)
    assert result["regret"]["avoided"] == pytest.approx(0.0)


def test_perfect_signal_reaches_perfect_information_value() -> None:
    payload = _input()
    payload["signals"][0]["likelihood_by_outcome"] = {
        "demand-low": 1.0,
        "demand-high": 0.0,
    }
    payload["signals"][0]["reported_outcome_probabilities"] = {
        "demand-low": 1.0,
        "demand-high": 0.0,
    }
    payload["signals"][1]["likelihood_by_outcome"] = {
        "demand-low": 0.0,
        "demand-high": 1.0,
    }
    payload["signals"][1]["reported_outcome_probabilities"] = {
        "demand-low": 0.0,
        "demand-high": 1.0,
    }
    result = _evaluate(payload)
    assert result["value"]["gross_deployed"] == pytest.approx(80.0)
    assert result["regret"]["deployed_expected"] == pytest.approx(0.0)


def test_miscalibrated_forecast_can_harm_decisions_without_negative_price() -> None:
    payload = _input()
    for signal in payload["signals"]:
        reported = signal["reported_outcome_probabilities"]
        signal["reported_outcome_probabilities"] = {
            "demand-low": reported["demand-high"],
            "demand-high": reported["demand-low"],
        }
    result = _evaluate(payload)
    assert result["value"]["counterfactual_timely_oracle"] == pytest.approx(40.0)
    assert result["value"]["gross_deployed"] == pytest.approx(-80.0)
    assert result["value"]["calibration_loss"] == pytest.approx(120.0)
    assert result["value"]["maximum_price"] == 0.0
    assert result["diagnostics"]["excess_brier"] > 0.0


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("information_available", 3.0, "information_available_after_decision"),
        ("maximum_freshness", 1.0, "forecast_exceeds_maximum_freshness"),
    ],
)
def test_late_or_stale_signal_has_zero_operational_value(
    field: str, value: float, reason: str
) -> None:
    payload = _input()
    payload["timing"][field] = value
    result = _evaluate(payload)
    assert result["timing"]["operationally_usable"] is False
    assert result["timing"]["reason"] == reason
    assert result["value"]["counterfactual_timely_oracle"] == pytest.approx(40.0)
    assert result["value"]["gross_deployed"] == pytest.approx(0.0)
    assert result["value"]["net_deployed"] == pytest.approx(-10.0)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda payload: payload["outcomes"][0].update(probability=0.3),
            "outcome probabilities must sum to 1",
        ),
        (
            lambda payload: payload["actions"][0]["outcome_values"].pop("demand-high"),
            "constraint minProperties|exactly match outcomes",
        ),
        (
            lambda payload: payload["signals"][0][
                "reported_outcome_probabilities"
            ].update({"demand-low": 0.5}),
            "reported outcome probabilities must sum to 1",
        ),
        (
            lambda payload: payload["signals"][0]["likelihood_by_outcome"].update(
                {"demand-low": 0.7}
            ),
            "signal likelihoods for outcome demand-low must sum to 1",
        ),
        (
            lambda payload: payload["feasible_action_ids"].append("unknown"),
            "subset of actions",
        ),
        (
            lambda payload: payload["signal_cost"].update(unit="USD"),
            "cost unit must match",
        ),
        (
            lambda payload: payload["timing"].update(maximum_freshness=float("nan")),
            "timing values must be finite",
        ),
        (
            lambda payload: payload["signal_cost"].update(amount=float("inf")),
            "signal cost amount must be finite",
        ),
        (
            lambda payload: payload["tolerances"].update(absolute_tie=float("nan")),
            "tolerances must be finite",
        ),
        (
            lambda payload: payload["signals"][1].update(
                signal_id=payload["signals"][0]["signal_id"]
            ),
            "signal IDs must be unique",
        ),
        (
            lambda payload: payload["signals"][0][
                "reported_outcome_probabilities"
            ].update({"demand-low": float("nan")}),
            "reported outcome probabilities must be finite",
        ),
        (
            lambda payload: payload["actions"][0]["outcome_values"].update(
                unexpected=0.0
            ),
            "outcome-value map must exactly match outcomes",
        ),
        (
            lambda payload: payload["actions"][0]["outcome_values"].update(
                {"demand-low": float("inf")}
            ),
            "action outcome values must be finite",
        ),
        (
            lambda payload: payload["signals"][0]["likelihood_by_outcome"].update(
                unexpected=0.0
            ),
            "signal probability maps must exactly match outcomes",
        ),
        (
            lambda payload: (
                payload["signals"][0].update(
                    likelihood_by_outcome={"demand-low": 0.0, "demand-high": 0.0}
                ),
                payload["signals"][1].update(
                    likelihood_by_outcome={"demand-low": 1.0, "demand-high": 1.0}
                ),
            ),
            "every declared signal must have positive marginal probability",
        ),
    ],
)
def test_semantic_pathologies_fail_closed(mutation, message: str) -> None:
    payload = _input()
    mutation(payload)
    with pytest.raises((TypeError, ValueError), match=message):
        validate_forecast_signal_information_semantics(payload)


def test_public_runtime_wraps_invalid_input_and_copy_is_independent() -> None:
    payload = _input()
    payload["timing"]["decision_time"] = 9.0
    with pytest.raises(InputError, match="timing"):
        forecast_signal_information_value(payload)
    result = forecast_signal_information_value(_input())
    first = result.to_contract_dict()
    first["value"]["gross_deployed"] = -999.0
    assert result.to_contract_dict()["value"]["gross_deployed"] == pytest.approx(40.0)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("net_deployed", 999.0, "net deployed value"),
        ("maximum_price", 0.0, "maximum price"),
    ],
)
def test_result_value_identities_fail_closed(
    field: str, value: float, message: str
) -> None:
    result = _evaluate()
    result["value"][field] = value
    with pytest.raises(ValueError, match=message):
        validate_forecast_signal_information_result_semantics(result)


def test_result_rejects_unknown_baseline_choice_and_regret_mismatch() -> None:
    result = _evaluate()
    result["baseline"]["choice_tie"] = ["unknown"]
    with pytest.raises(ValueError, match="baseline choices"):
        validate_forecast_signal_information_result_semantics(result)

    result = _evaluate()
    result["regret"]["avoided"] = -999.0
    with pytest.raises(ValueError, match="regret avoided"):
        validate_forecast_signal_information_result_semantics(result)


def test_runtime_wraps_internal_refinement_assurance_failure(monkeypatch) -> None:
    policy_values = iter([1e9, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    monkeypatch.setattr(
        forecast_signal_module,
        "_policy_value",
        lambda *_args, **_kwargs: next(policy_values),
    )
    with pytest.raises(InputError, match="signal refinement assurance failed"):
        forecast_signal_information_value(_input())


def test_permutations_and_infeasible_actions_preserve_declared_decision() -> None:
    expected = _evaluate()
    payload = deepcopy(_input())
    payload["outcomes"].reverse()
    payload["actions"].reverse()
    payload["signals"].reverse()
    payload["actions"].append(
        {
            "action_id": "infeasible-windfall",
            "label": "Infeasible windfall",
            "outcome_values": {"demand-low": 1e9, "demand-high": 1e9},
            "constraint_basis": "excluded by declared capacity constraint",
        }
    )
    actual = _evaluate(payload)
    assert actual["baseline"] == expected["baseline"]
    assert actual["value"] == pytest.approx(expected["value"])


def test_cli_json_text_and_public_exports(tmp_path: Path) -> None:
    request = CONTRACT / "fixtures/normative/input.json"
    output = tmp_path / "result.json"
    result = CliRunner().invoke(
        app,
        [
            "--format",
            "json",
            "calculate-forecast-signal-information",
            str(request),
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["value"]["gross_deployed"] == pytest.approx(40.0)
    assert json.loads(output.read_text(encoding="utf-8")) == payload
    text_output = tmp_path / "result.txt"
    text_saved = CliRunner().invoke(
        app,
        [
            "calculate-forecast-signal-information",
            str(request),
            "--output",
            str(text_output),
        ],
    )
    assert text_saved.exit_code == 0
    assert f"Result saved to {text_output}" in text_saved.stdout
    text = CliRunner().invoke(
        app, ["calculate-forecast-signal-information", str(request)]
    )
    assert text.exit_code == 0
    assert "maximum price 40.000000 NZD per inventory decision" in text.stdout
    assert voiage.ForecastSignalInformationResult is ForecastSignalInformationResult
    assert voiage.forecast_signal_information_value is forecast_signal_information_value


def test_cli_rejects_non_object_request(tmp_path: Path) -> None:
    request = tmp_path / "request.json"
    request.write_text("[]", encoding="utf-8")
    result = CliRunner().invoke(
        app, ["calculate-forecast-signal-information", str(request)]
    )
    assert result.exit_code == 1
    assert "must be a JSON object" in result.output


def test_capability_boundary_is_experimental_python_only() -> None:
    capability = _json(CONTRACT / "capabilities.json")
    assert capability["maturity"] == "experimental"
    assert capability["stable_claim_allowed"] is False
    assert capability["surfaces"] == {
        "python": {"status": "executable"},
        "rust": {"status": "unsupported"},
        "r": {"status": "unsupported"},
        "julia": {"status": "unsupported"},
        "mojo": {"status": "external"},
    }


def test_contract_evidence_is_sha256_pinned_and_keeps_external_gates_open() -> None:
    evidence = _json(CONTRACT / "fixtures/evidence.json")
    assert evidence["execution_status"] == "experimental_python"
    assert evidence["stable_claim_allowed"] is False
    assert "independent scientific review" in evidence["unresolved_gates"]
    for artifact in evidence["artifacts"]:
        path = ROOT / artifact["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]


def test_c18_m23_and_native_delivery_subissues_are_governed() -> None:
    track_id = "supported_frontier_method_completion_20260723"
    track = ROOT / "conductor/archive" / track_id
    requirements = (ROOT / "conductor/requirements.md").read_text(encoding="utf-8")
    plan = (track / "plan.md").read_text(encoding="utf-8")
    metadata = _json(track / "metadata.json")
    cross_references = _json(ROOT / "conductor/github-cross-references.json")
    cross_reference = next(
        item for item in cross_references["tracks"] if item["track_id"] == track_id
    )
    expected_issues = {
        f"https://github.com/edithatogo/voiage/issues/{number}"
        for number in (572, 759, 760, 762)
    }

    assert "M23 / planned v1.3.0" in requirements
    assert "C18 governed forecast-signal decision value" in requirements
    assert {
        "M21",
        "M22",
        "M23",
    } <= set(metadata["planned_version_extensions"]["1.3.0"])
    assert "M23" in metadata["requirement_ids"]
    assert expected_issues <= set(metadata["github_subissues"])
    assert expected_issues <= set(cross_reference["subissues"])
    assert "F572-1 / #760" in plan
    assert "F572-2 / #759" in plan
    assert "F572-3 / #762" in plan
    assert "canonical C18" in plan
    assert "remain pending" in plan
    pr_url = "https://github.com/edithatogo/voiage/pull/770"
    assert pr_url in metadata["github_cross_reference"]["pull_requests"]
    assert any(item["url"] == pr_url for item in cross_reference["pull_requests"])
