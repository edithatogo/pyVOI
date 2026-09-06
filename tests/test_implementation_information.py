"""Contract and numerical tests for joint implementation-information value."""

# pyright: reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnusedCallResult=false

from copy import deepcopy
import json
import math
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
import pytest
from typer.testing import CliRunner

import voiage
from voiage import methods
from voiage.cli import app
from voiage.exceptions import InputError
import voiage.methods.implementation_information as implementation_information_module
from voiage.methods.implementation_information import implementation_information_value

ROOT = Path(__file__).parents[1]
CONTRACT = ROOT / "specs/frontier/implementation-information/v1"
INPUT = CONTRACT / "fixtures/normative/input.json"
EXPECTED = CONTRACT / "fixtures/normative/expected.json"


def _input() -> dict[str, Any]:
    return json.loads(INPUT.read_text())


def _result(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return implementation_information_value(payload or _input()).to_contract_dict()


def _apply_pathology(case_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    case = json.loads(case_path.read_text())
    payload = json.loads((case_path.parent / case["base_input"]).read_text())
    target: Any = payload
    for component in case["path"][:-1]:
        target = target[component]
    leaf = case["path"][-1]
    if case["operation"] == "set":
        target[leaf] = case["value"]
    elif case["operation"] == "set_nonfinite":
        target[leaf] = math.inf
    elif case["operation"] == "delete":
        del target[leaf]
    else:  # pragma: no cover - the fixture contract guards this branch
        raise AssertionError(f"unknown pathology operation: {case['operation']}")
    return payload, case


def test_portable_schemas_and_normative_fixture() -> None:
    input_schema = json.loads(
        (CONTRACT / "schemas/implementation-information-input.schema.json").read_text()
    )
    result_schema = json.loads(
        (CONTRACT / "schemas/implementation-information-result.schema.json").read_text()
    )
    Draft202012Validator(input_schema).validate(_input())
    result = _result()
    Draft202012Validator(result_schema).validate(result)
    assert result == json.loads(EXPECTED.read_text())


@pytest.mark.parametrize(
    "case_path",
    sorted((CONTRACT / "fixtures/cases").glob("*.json")),
    ids=lambda path: path.stem,
)
def test_pathological_fixtures_fail_closed(case_path: Path) -> None:
    payload, case = _apply_pathology(case_path)
    with pytest.raises(InputError, match=case["expected_error"]):
        implementation_information_value(payload)


def test_four_cell_decomposition_and_interaction_identity() -> None:
    result = _result()
    matrix = result["matrix"]
    assert isinstance(matrix, dict)
    assert matrix["current_information_current_implementation"][
        "aggregate_value"
    ] == pytest.approx(12000)
    assert matrix["perfect_information_current_implementation"][
        "aggregate_value"
    ] == pytest.approx(12400)
    assert matrix["current_information_perfect_implementation"][
        "aggregate_value"
    ] == pytest.approx(12000)
    assert matrix["perfect_information_perfect_implementation"][
        "aggregate_value"
    ] == pytest.approx(14000)

    gross = result["gross_components"]
    assert isinstance(gross, dict)
    assert gross["realizable_evpi"] == pytest.approx(400)
    assert gross["evpim"] == pytest.approx(0)
    assert gross["evp"] == pytest.approx(2000)
    assert gross["interaction"] == pytest.approx(1600)
    assert gross["evp"] == pytest.approx(
        gross["realizable_evpi"] + gross["evpim"] + gross["interaction"]
    )
    assert result["identity_residuals"] == {
        "evp_equals_realizable_evpi_plus_evpim_plus_interaction": pytest.approx(0),
        "perfect_implementation_evpi_equals_evp_minus_evpim": pytest.approx(0),
    }


def test_specific_implementation_and_signal_dependent_ia_evsi() -> None:
    result = _result()
    gross = result["gross_components"]
    net = result["net_components"]
    assert isinstance(gross, dict)
    assert isinstance(net, dict)
    assert gross["evsim"] == pytest.approx(400)
    assert net["evsim"] == pytest.approx(350)
    assert gross["ia_evsi"] == pytest.approx(1000)
    assert net["ia_evsi"] == pytest.approx(925)
    assurance = result["assurance"]
    assert isinstance(assurance, dict)
    assert assurance["implementation_information_independence_assumed"] is False
    assert assurance["state_dependent_current_implementation_observed"] is True
    assert assurance["signal_dependent_post_sample_implementation_supported"] is True
    audit = result["implementation_audit"]
    changes = result["uptake_changes"]
    assert audit["current"]["low"]["new"] == {"standard": 0.8, "new": 0.2}
    assert audit["specific"]["high"]["new"] == {"standard": 0.2, "new": 0.8}
    assert changes["specific_minus_current"]["high"]["new"]["new"] == pytest.approx(0.2)
    assert changes["post_sample_minus_current_by_signal"]["favourable"]["high"]["new"][
        "new"
    ] == pytest.approx(0.2)
    matrix = result["matrix"]
    assert matrix["perfect_information_current_implementation"]["state_action_values"][
        "high"
    ]["new"] == pytest.approx(14.8)


def test_zero_uptake_edge_case_is_enumerated_without_independence() -> None:
    payload = _input()
    current = payload["current_implementation"]
    assert isinstance(current, dict)
    for state in current.values():
        assert isinstance(state, dict)
        state["new"] = {"standard": 1, "new": 0}
    payload.pop("sampling_model")
    result = _result(payload)
    matrix = result["matrix"]
    assert isinstance(matrix, dict)
    assert matrix["current_information_current_implementation"][
        "aggregate_value"
    ] == pytest.approx(10000)
    assert result["gross_components"]["evpim"] == pytest.approx(2000)


def test_complete_ties_and_false_switch_regression() -> None:
    tied = _input()
    for state in tied["states"]:
        state["net_benefit"] = {"standard": 10, "new": 10}
    tied_result = _result(tied)
    assert tied_result["matrix"]["current_information_current_implementation"][
        "policy_ties"
    ]["all"] == ["new", "standard"]

    no_switch = _input()
    for state in no_switch["states"]:
        state["net_benefit"] = {"standard": 10, "new": 20}
    no_switch_result = _result(no_switch)
    assert (
        no_switch_result["decision_switches"]["current_to_perfect_information"] is False
    )


def test_state_and_action_permutations_preserve_estimands() -> None:
    forward = _result()
    permuted = _input()
    permuted["states"].reverse()
    permuted["actions"].reverse()
    reverse = _result(permuted)
    assert reverse["gross_components"] == forward["gross_components"]
    assert reverse["net_components"] == forward["net_components"]


def test_strict_schemas_reject_open_scientific_envelopes() -> None:
    input_schema = json.loads(
        (CONTRACT / "schemas/implementation-information-input.schema.json").read_text()
    )
    result_schema = json.loads(
        (CONTRACT / "schemas/implementation-information-result.schema.json").read_text()
    )
    invalid_input = _input()
    invalid_input["states"] = [{}]
    assert list(Draft202012Validator(input_schema).iter_errors(invalid_input))
    invalid_result = _result()
    invalid_result["matrix"] = {}
    assert list(Draft202012Validator(result_schema).iter_errors(invalid_result))


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("value_unit", "", "value_unit"),
        ("chronology", "not-a-sequence", "chronology"),
        ("population", 1e308, "product must be finite"),
    ],
)
def test_nonportable_units_chronology_and_scaling_fail_closed(
    field: str, value: object, match: str
) -> None:
    payload = _input()
    payload[field] = value
    if field == "population":
        payload["discounted_time_factor"] = 1e308
    with pytest.raises(InputError, match=match):
        implementation_information_value(payload)


def test_unknown_cost_and_nonfinite_value_fail_closed() -> None:
    unknown_cost = _input()
    unknown_cost["costs"]["mystery"] = 100
    with pytest.raises(InputError, match="unknown cost"):
        implementation_information_value(unknown_cost)

    nonfinite = _input()
    nonfinite["states"][0]["net_benefit"]["new"] = float("inf")
    with pytest.raises(InputError, match="finite"):
        implementation_information_value(nonfinite)


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        (lambda value: value["states"][0].update(probability=0.7), "sum to one"),
        (lambda value: value.update(population=0), "population"),
        (
            lambda value: value["current_implementation"]["low"]["new"].update(new=0.3),
            "sum to one",
        ),
        (lambda value: value["states"][0]["net_benefit"].pop("new"), "all actions"),
        (
            lambda value: value["sampling_model"]["signals"][0][
                "likelihood_by_state"
            ].pop("high"),
            "every state",
        ),
    ],
)
def test_invalid_contracts_fail_closed(mutation: object, match: str) -> None:
    payload = deepcopy(_input())
    mutation(payload)  # type: ignore[operator]
    with pytest.raises(InputError, match=match):
        implementation_information_value(payload)


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        (lambda value: value.update(unexpected=True), "keys must match"),
        (lambda value: value.update(schema_version="v2"), "schema_version"),
        (lambda value: value.update(analysis_type="evpi"), "analysis_type"),
        (lambda value: value.update(analysis_id=""), "analysis_id"),
        (lambda value: value.update(actions=["standard"]), "at least two"),
        (
            lambda value: value.update(actions=["standard", "standard"]),
            "unique identifiers",
        ),
        (lambda value: value.update(actions=["standard", ""]), "non-empty strings"),
        (lambda value: value.update(states=[]), "states must be a non-empty"),
        (lambda value: value["states"][0].pop("net_benefit"), "each state"),
        (lambda value: value["states"][0].update(state_id=""), "state_id"),
        (
            lambda value: value["states"][1].update(
                state_id=value["states"][0]["state_id"]
            ),
            "state identifiers must be unique",
        ),
        (
            lambda value: value["states"][0].update(probability=-0.1),
            "finite and non-negative",
        ),
        (
            lambda value: value.update(discounted_time_factor=0),
            "discounted_time_factor",
        ),
        (lambda value: value.update(tie_tolerance=-1), "tie_tolerance"),
        (
            lambda value: value["current_implementation"].pop("high"),
            "exactly the declared states",
        ),
        (
            lambda value: value["current_implementation"]["low"].pop("new"),
            "exactly the intended actions",
        ),
        (
            lambda value: value["current_implementation"]["low"]["new"].pop("new"),
            "exactly the declared actions",
        ),
        (
            lambda value: value["current_implementation"]["low"]["new"].update(
                standard=-0.1, new=1.1
            ),
            "finite and non-negative",
        ),
        (lambda value: value.update(sampling_model=[]), "must be an object"),
        (
            lambda value: value["sampling_model"].update(unexpected=True),
            "sampling_model keys",
        ),
        (
            lambda value: value["sampling_model"].update(signals=[]),
            "signals must be non-empty",
        ),
        (
            lambda value: value["sampling_model"]["signals"][0].pop(
                "likelihood_by_state"
            ),
            "each signal must contain",
        ),
        (
            lambda value: value["sampling_model"]["signals"][0].update(signal_id=""),
            "signal_id",
        ),
        (
            lambda value: value["sampling_model"]["signals"][1].update(
                signal_id=value["sampling_model"]["signals"][0]["signal_id"]
            ),
            "signal identifiers must be unique",
        ),
        (
            lambda value: value["sampling_model"]["post_sample_implementation"].pop(
                "unfavourable"
            ),
            "must contain every signal",
        ),
        (lambda value: value.update(costs=[]), "costs must be an object"),
        (
            lambda value: value["costs"].update(perfect_information=-1),
            "costs must be finite and non-negative",
        ),
    ],
)
def test_runtime_contract_rejects_every_invalid_envelope(
    mutation: object, match: str
) -> None:
    payload = deepcopy(_input())
    mutation(payload)  # type: ignore[operator]
    with pytest.raises(InputError, match=match):
        implementation_information_value(payload)


def test_optional_specific_and_sampling_contracts_can_be_omitted() -> None:
    payload = _input()
    payload.pop("specific_implementation")
    payload.pop("sampling_model")
    result = _result(payload)
    assert "evsim" not in result["gross_components"]
    assert "ia_evsi" not in result["gross_components"]
    assert "specific" not in result["implementation_audit"]
    assert "post_sample_by_signal" not in result["implementation_audit"]
    assert result["decision_switches"]["current_to_specific_implementation"] is None
    assert result["decision_switches"]["sample_information"] is None


def test_finite_guards_reject_weighted_sample_aggregate_and_net_overflow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        implementation_information_module,
        "_realised_value",
        lambda *_args: float("inf"),
    )
    with pytest.raises(InputError, match="state/action values must be finite"):
        implementation_information_value(_input())

    monkeypatch.undo()
    original = implementation_information_module._realised_value
    calls = 0

    def overflow_only_after_scenario_cells(*args: object) -> float:
        nonlocal calls
        calls += 1
        if calls > 24:
            return float("inf")
        return original(*args)  # type: ignore[arg-type]

    monkeypatch.setattr(
        implementation_information_module,
        "_realised_value",
        overflow_only_after_scenario_cells,
    )
    with pytest.raises(
        InputError, match="sample-weighted action values must be finite"
    ):
        implementation_information_value(_input())

    monkeypatch.undo()
    aggregate = _input()
    aggregate["population"] = 1e308
    with pytest.raises(InputError, match="aggregate value must be finite"):
        implementation_information_value(aggregate)

    net = _input()
    net["costs"]["perfect_information"] = 1e308
    net["costs"]["perfect_implementation"] = 1e308
    with pytest.raises(InputError, match="net components must be finite"):
        implementation_information_value(net)


def test_public_api_and_cli(tmp_path: Path) -> None:
    assert voiage.implementation_information_value is implementation_information_value
    assert methods.implementation_information_value is implementation_information_value
    assert (
        methods.ImplementationInformationResult.__name__
        == "ImplementationInformationResult"
    )
    output = tmp_path / "result.json"
    invocation = CliRunner().invoke(
        app,
        [
            "--format",
            "json",
            "calculate-implementation-information",
            str(INPUT),
            "--output",
            str(output),
        ],
    )
    assert invocation.exit_code == 0, invocation.output
    cli_payload = json.loads(invocation.output)
    assert cli_payload["analysis_type"] == "implementation_information_decomposition"
    assert json.loads(output.read_text()) == json.loads(EXPECTED.read_text())


def test_cli_rejects_non_object_specification(tmp_path: Path) -> None:
    specification = tmp_path / "non-object.json"
    specification.write_text("[]")

    invocation = CliRunner().invoke(
        app,
        ["calculate-implementation-information", str(specification)],
    )

    assert invocation.exit_code == 1
    assert (
        "Error: Implementation-information specification must be an object."
        in invocation.output
    )


def test_cli_reports_saved_human_output(tmp_path: Path) -> None:
    output = tmp_path / "result.txt"

    invocation = CliRunner().invoke(
        app,
        [
            "calculate-implementation-information",
            str(INPUT),
            "--output",
            str(output),
        ],
    )

    assert invocation.exit_code == 0, invocation.output
    assert f"Result saved to {output}" in invocation.output
    assert output.read_text().startswith("Implementation-information value:")
