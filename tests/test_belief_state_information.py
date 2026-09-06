"""Contract and numerical assurance for issue #597 belief-state VOI."""

# pyright: reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportMissingModuleSource=false, reportUnknownLambdaType=false
# pyright: reportUnusedCallResult=false
# pyright: reportMissingImports=false, reportPrivateUsage=false

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
import pytest
from referencing import Registry, Resource
from typer.testing import CliRunner

from voiage import (
    belief_state_information_value as exported_belief_state_value,
)
from voiage import (
    cli,
    methods,
)
from voiage.cli import app
from voiage.exceptions import InputError
import voiage.methods.belief_state_information as belief_module
from voiage.methods.belief_state_information import (
    belief_state_information_value,
    validate_belief_state_information_result,
)

ROOT = Path(__file__).parents[1]
CONTRACT = ROOT / "specs/frontier/belief-state-information/v1"
INPUT = CONTRACT / "fixtures/normative/input.json"
EXPECTED = CONTRACT / "fixtures/normative/expected.json"


def _input() -> dict[str, Any]:
    return json.loads(INPUT.read_text(encoding="utf-8"))


def _result(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return belief_state_information_value(payload or _input()).to_contract_dict()


def _apply_pathology(case_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    case = json.loads(case_path.read_text())
    payload = json.loads((case_path.parent / case["base_input"]).read_text())
    target: Any = payload
    for component in case["path"][:-1]:
        target = target[component]
    if case["operation"] == "set_horizon_one":
        target[case["path"][-1]] = case["value"]
        payload["constraints"]["allowed_control_action_ids_by_stage"].pop("1")
    else:
        target[case["path"][-1]] = case["value"]
    return payload, case


def _result_schema_validator(
    input_schema: dict[str, object], result_schema: dict[str, object]
) -> Draft202012Validator:
    registry = Registry().with_resource(
        str(input_schema["$id"]), Resource.from_contents(input_schema)
    )
    return Draft202012Validator(result_schema, registry=registry)


def test_portable_schemas_and_normative_fixture() -> None:
    input_schema = json.loads(
        (CONTRACT / "schemas/belief-state-information-input.schema.json").read_text()
    )
    result_schema = json.loads(
        (CONTRACT / "schemas/belief-state-information-result.schema.json").read_text()
    )
    Draft202012Validator(input_schema).validate(_input())
    result = _result()
    _result_schema_validator(input_schema, result_schema).validate(result)
    assert result == json.loads(EXPECTED.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "case_path",
    sorted((CONTRACT / "fixtures/cases").glob("*.json")),
    ids=lambda path: path.stem,
)
def test_pathological_fixtures_are_executable(case_path: Path) -> None:
    payload, case = _apply_pathology(case_path)
    if "expected_error" in case:
        with pytest.raises(InputError, match=case["expected_error"]):
            belief_state_information_value(payload)
        return
    result = _result(payload)
    for key, expected in case["expected_values"].items():
        assert result["values"][key] == pytest.approx(expected)


def test_contract_evidence_hashes_are_exact() -> None:
    evidence = json.loads((CONTRACT / "fixtures/evidence.json").read_text())
    for artifact in evidence["artifacts"]:
        payload = (ROOT / artifact["path"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == artifact["sha256"]


def test_nonmyopic_intervention_value_and_matched_comparator() -> None:
    result = _result()
    values = result["values"]
    assert values["closed_loop_gross"] == pytest.approx(7.0)
    assert values["expected_sensing_cost"] == pytest.approx(0.5)
    assert values["closed_loop_net"] == pytest.approx(6.5)
    assert values["no_information"] == pytest.approx(0.0)
    assert values["gross_information_value"] == pytest.approx(7.0)
    assert values["net_information_value"] == pytest.approx(6.5)
    assert values["myopic_information_value"] == pytest.approx(0.0)
    assert values["nonmyopic_information_value"] == pytest.approx(6.5)
    assert values["nonmyopic_minus_myopic"] == pytest.approx(6.5)
    assert values["fully_observed_value"] == pytest.approx(20.0)
    assert values["partial_observability_regret"] == pytest.approx(13.0)

    root = result["policy_tree"]
    assert root["control_choice_tie"] == ["probe"]
    assert root["selected_control"] == "probe"
    assert root["sensor_choice_tie"] == ["diagnostic"]
    assert root["selected_sensor"] == "diagnostic"
    assert [branch["observation_id"] for branch in root["branches"]] == [
        "negative",
        "positive",
    ]
    assert root["chronology"] == [
        "control",
        "transition",
        "observe",
        "update",
    ]


def test_conditional_sensing_null_sensor_and_martingale_assurance() -> None:
    result = _result()
    conditional = result["conditional_sensing_values"]
    probe = next(item for item in conditional if item["control_action_id"] == "probe")
    diagnostic = next(
        item for item in probe["sensors"] if item["sensor_id"] == "diagnostic"
    )
    null = next(item for item in probe["sensors"] if item["sensor_id"] == "none")
    assert diagnostic["gross_value"] == pytest.approx(8.0)
    assert diagnostic["net_value"] == pytest.approx(7.5)
    assert diagnostic["net_increment_vs_null"] == pytest.approx(7.5)
    assert null["gross_value"] == pytest.approx(0.0)
    assert null["net_value"] == pytest.approx(0.0)

    assurance = result["assurance"]
    assert assurance["posterior_martingale_verified"] is True
    assert assurance["null_sensor_reduction_verified"] is True
    assert assurance["no_information_reduction_verified"] is True
    assert assurance["exact_enumeration"] is True
    assert assurance["approximation_used"] is False
    assert assurance["complete_ties_reported"] is True
    assert assurance["action_dependent_learning"] is True
    assert assurance["usable_downstream_learning_response"] is True
    assert assurance["dual_control_diagnostic"] is True
    assert assurance["unique_additive_dual_control_value_claimed"] is False
    assert result["language_dispositions"] == {
        "python": "executable-experimental",
        "rust": "unsupported",
        "r": "unsupported",
        "julia": "unsupported",
        "mojo": "external-boundary",
    }


def test_complete_ties_and_deterministic_permutation() -> None:
    tied = _input()
    tied["horizon"] = 1
    tied["constraints"]["allowed_control_action_ids_by_stage"].pop("1")
    result = _result(tied)
    assert result["policy_tree"]["control_choice_tie"] == [
        "choose_bad",
        "choose_good",
        "wait",
    ]
    assert result["policy_tree"]["selected_control"] == "choose_bad"

    permuted = _input()
    permuted["latent_states"].reverse()
    permuted["control_actions"].reverse()
    permuted["sensors"].reverse()
    assert _result(permuted)["values"] == _result()["values"]


def test_horizon_curve_stopping_and_exact_bounds() -> None:
    result = _result()
    assert result["value_by_horizon"] == [
        {
            "horizon": 1,
            "closed_loop_net": pytest.approx(0.0),
            "no_information": pytest.approx(0.0),
            "net_information_value": pytest.approx(0.0),
        },
        {
            "horizon": 2,
            "closed_loop_net": pytest.approx(6.5),
            "no_information": pytest.approx(0.0),
            "net_information_value": pytest.approx(6.5),
        },
    ]
    assert result["stopping"] == {
        "kind": "fixed_horizon",
        "reason": "horizon_reached",
        "stage": 2,
    }
    assert result["approximation_bounds"] == {
        "lower": pytest.approx(6.5),
        "upper": pytest.approx(6.5),
        "gap": pytest.approx(0.0),
    }


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        (
            lambda value: value["latent_states"][0].update(initial_probability=0.7),
            "sum to one",
        ),
        (lambda value: value.update(horizon=0), "horizon"),
        (
            lambda value: value["transition_model"]["probe"]["good"].pop("bad"),
            "all latent states",
        ),
        (lambda value: value["sensors"][0].update(cost=-1), "nonnegative"),
        (
            lambda value: value["sensors"][1].update(null_sensor=True),
            "exactly one null",
        ),
        (
            lambda value: value["sensors"][0]["likelihood_by_control"]["probe"][
                "good"
            ].update(positive=0.8),
            "sum to one",
        ),
    ],
)
def test_invalid_models_fail_closed(mutation: object, match: str) -> None:
    payload = _input()
    mutation(payload)  # type: ignore[operator]
    with pytest.raises(InputError, match=match):
        belief_state_information_value(payload)


def test_unknown_fields_nonfinite_values_and_chronology_fail_closed() -> None:
    unknown = _input()
    unknown["surprise"] = True
    with pytest.raises(InputError, match="unknown fields"):
        belief_state_information_value(unknown)

    nonfinite = _input()
    nonfinite["rewards"]["probe"]["good"] = float("inf")
    with pytest.raises(InputError, match="finite"):
        belief_state_information_value(nonfinite)

    chronology = _input()
    chronology["chronology"] = ["observe", "control", "transition", "update"]
    with pytest.raises(InputError, match="chronology"):
        belief_state_information_value(chronology)


def test_schema_rejects_open_envelopes() -> None:
    input_schema = json.loads(
        (CONTRACT / "schemas/belief-state-information-input.schema.json").read_text()
    )
    result_schema = json.loads(
        (CONTRACT / "schemas/belief-state-information-result.schema.json").read_text()
    )
    invalid_input = _input()
    invalid_input["surprise"] = True
    assert list(Draft202012Validator(input_schema).iter_errors(invalid_input))
    invalid_result = _result()
    invalid_result["values"] = {}
    assert list(
        _result_schema_validator(input_schema, result_schema).iter_errors(
            invalid_result
        )
    )
    invalid_model_assurance = _result()
    invalid_model_assurance["model_assurance"]["input_contract"]["surprise"] = True
    assert list(
        _result_schema_validator(input_schema, result_schema).iter_errors(
            invalid_model_assurance
        )
    )


def test_public_api_cli_and_maturity_boundary(tmp_path: Path) -> None:
    assert exported_belief_state_value is belief_state_information_value
    assert methods.belief_state_information_value is belief_state_information_value

    run = CliRunner().invoke(
        app,
        ["--format", "json", "calculate-belief-state-information", str(INPUT)],
    )
    assert run.exit_code == 0, run.output
    payload = json.loads(run.stdout)
    assert payload["analysis_type"] == "belief_state_information_result"
    assert payload["method_maturity"] == "experimental"

    output = tmp_path / "result.json"
    saved = CliRunner().invoke(
        app,
        [
            "--format",
            "json",
            "calculate-belief-state-information",
            str(INPUT),
            "--output",
            str(output),
        ],
    )
    assert saved.exit_code == 0, saved.output
    assert json.loads(output.read_text()) == json.loads(saved.stdout)

    bad = tmp_path / "bad.json"
    bad.write_text("[]", encoding="utf-8")
    failed = CliRunner().invoke(app, ["calculate-belief-state-information", str(bad)])
    assert failed.exit_code == 1
    assert "must be an object" in failed.output


def test_cli_announces_saved_output_when_status_messages_are_enabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The optional terminal status branch remains covered and deterministic."""
    output = tmp_path / "result.json"
    monkeypatch.setattr(cli, "_should_echo_status_messages", lambda: True)

    saved = CliRunner().invoke(
        app,
        [
            "--format",
            "json",
            "calculate-belief-state-information",
            str(INPUT),
            "--output",
            str(output),
        ],
    )

    assert saved.exit_code == 0, saved.output
    assert json.loads(output.read_text(encoding="utf-8"))["analysis_type"] == (
        "belief_state_information_result"
    )
    assert f"Result saved to {output}" in saved.stdout


def test_result_copy_is_independent() -> None:
    result = belief_state_information_value(_input())
    first = result.to_contract_dict()
    first["values"]["closed_loop_net"] = -999
    assert result.to_contract_dict()["values"]["closed_loop_net"] == pytest.approx(6.5)


def test_no_information_and_null_sensor_reductions() -> None:
    payload = _input()
    payload["constraints"]["allowed_sensor_ids_by_control"] = {
        action["action_id"]: ["none"] for action in payload["control_actions"]
    }
    result = _result(payload)
    assert result["values"]["closed_loop_net"] == pytest.approx(
        result["values"]["no_information"]
    )
    assert result["values"]["net_information_value"] == pytest.approx(0.0)


def test_minimization_direction_uses_declared_objective_consistently() -> None:
    payload = deepcopy(_input())
    payload["objective_direction"] = "minimize"
    for action in payload["rewards"].values():
        for state_id, value in action.items():
            action[state_id] = -value
    result = _result(payload)
    assert result["values"]["net_information_value"] == pytest.approx(6.5)
    assert result["values"]["closed_loop_net"] == pytest.approx(-6.5)


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        (lambda value: value.pop("analysis_id"), "missing fields"),
        (lambda value: value.update(schema_version="2"), "schema_version"),
        (lambda value: value.update(analysis_type="other"), "analysis_type"),
        (lambda value: value.update(method_maturity="stable"), "method_maturity"),
        (lambda value: value.update(analysis_id=""), "analysis_id"),
        (
            lambda value: value.update(objective_direction="sideways"),
            "objective_direction",
        ),
        (lambda value: value.update(policy_class="open_loop"), "policy_class"),
        (lambda value: value.update(stopping={}), "fixed_horizon"),
        (lambda value: value.update(horizon=True), "integer"),
        (lambda value: value.update(horizon=13), "between 1 and 12"),
        (lambda value: value.update(discount_factor="unknown"), "must be numeric"),
        (lambda value: value.update(discount_factor=0), "discount_factor"),
        (lambda value: value.update(tolerances={}), "tolerances must declare"),
        (lambda value: value["tolerances"].update(absolute_tie=-1), "nonnegative"),
        (lambda value: value.update(latent_states=[]), "non-empty array"),
        (
            lambda value: value["latent_states"][0].update(state_id=""),
            "non-empty string",
        ),
        (
            lambda value: value["latent_states"].append(
                deepcopy(value["latent_states"][0])
            ),
            "unique",
        ),
        (
            lambda value: (
                value["latent_states"][0].update(initial_probability=-0.1),
                value["latent_states"][1].update(initial_probability=1.1),
            ),
            "between zero and one",
        ),
        (lambda value: value["transition_model"].pop("wait"), "all control actions"),
        (lambda value: value["transition_model"].update(wait=[]), "must be an object"),
        (
            lambda value: value["transition_model"]["wait"].pop("good"),
            "all latent states",
        ),
        (
            lambda value: value["transition_model"]["wait"]["bad"].update(
                bad=1.1, good=-0.1
            ),
            "between zero and one",
        ),
        (lambda value: value["rewards"].pop("wait"), "all control actions"),
        (lambda value: value["rewards"]["wait"].pop("good"), "all latent states"),
        (lambda value: value["sensors"][0].update(extra=True), "sensor fields"),
        (lambda value: value["sensors"][0].update(cost=1), "null sensor cost"),
        (
            lambda value: value["sensors"][1]["likelihood_by_control"].pop("wait"),
            "all control actions",
        ),
        (
            lambda value: value["sensors"][1]["likelihood_by_control"]["wait"].pop(
                "good"
            ),
            "all latent states",
        ),
        (
            lambda value: value["sensors"][0]["likelihood_by_control"]["wait"][
                "good"
            ].update(negative=0.6, positive=0.4),
            "state independent",
        ),
        (lambda value: value["constraints"].update(extra=True), "constraints fields"),
        (
            lambda value: value["constraints"][
                "allowed_control_action_ids_by_stage"
            ].pop("1"),
            "cover every stage",
        ),
        (
            lambda value: value["constraints"][
                "allowed_control_action_ids_by_stage"
            ].update({"0": []}),
            "non-empty known unique",
        ),
        (
            lambda value: value["constraints"]["allowed_sensor_ids_by_control"].pop(
                "wait"
            ),
            "cover all control actions",
        ),
        (
            lambda value: value["constraints"]["allowed_sensor_ids_by_control"].update(
                wait=["diagnostic"]
            ),
            "include null",
        ),
    ],
)
def test_all_strict_contract_boundaries_fail_closed(
    mutation: object, match: str
) -> None:
    payload = _input()
    mutation(payload)  # type: ignore[operator]
    with pytest.raises(InputError, match=match):
        belief_state_information_value(payload)


def test_zero_probability_observation_and_action_independence_are_exact() -> None:
    payload = _input()
    for sensor in payload["sensors"]:
        for by_state in sensor["likelihood_by_control"].values():
            for probabilities in by_state.values():
                probabilities.update(negative=1.0, positive=0.0)
    result = _result(payload)
    assert result["assurance"]["action_dependent_learning"] is False
    assert result["policy_tree"]["branches"][0]["observation_id"] == "negative"


def test_state_independent_action_dependent_observations_do_not_claim_learning() -> (
    None
):
    payload = _input()
    for sensor in payload["sensors"]:
        for action_id, by_state in sensor["likelihood_by_control"].items():
            probabilities = (
                {"negative": 0.8, "positive": 0.2}
                if action_id == "probe"
                else {"negative": 0.4, "positive": 0.6}
            )
            for state_id in by_state:
                by_state[state_id] = dict(probabilities)
    result = _result(payload)
    assert result["values"]["net_information_value"] == pytest.approx(0.0)
    assert result["assurance"]["usable_downstream_learning_response"] is False
    assert result["assurance"]["action_dependent_learning"] is False
    assert result["assurance"]["dual_control_diagnostic"] is False


def test_state_informative_but_action_independent_learning_is_not_dual_control() -> (
    None
):
    payload = _input()
    informative = payload["sensors"][1]["likelihood_by_control"]["probe"]
    for action_id in payload["sensors"][1]["likelihood_by_control"]:
        payload["sensors"][1]["likelihood_by_control"][action_id] = deepcopy(
            informative
        )
    assurance = _result(payload)["assurance"]
    assert assurance["usable_downstream_learning_response"] is True
    assert assurance["action_dependent_learning"] is False
    assert assurance["dual_control_diagnostic"] is False


def test_transition_dependence_alone_does_not_claim_dual_control() -> None:
    payload = _input()
    for sensor in payload["sensors"]:
        for by_state in sensor["likelihood_by_control"].values():
            for state_id in by_state:
                by_state[state_id] = {"negative": 0.5, "positive": 0.5}
    payload["transition_model"]["probe"] = {
        "bad": {"bad": 0.0, "good": 1.0},
        "good": {"bad": 1.0, "good": 0.0},
    }
    assurance = _result(payload)["assurance"]
    assert assurance["action_dependent_transition"] is True
    assert assurance["action_dependent_learning"] is False
    assert assurance["dual_control_diagnostic"] is False


def test_exact_enumeration_budget_fails_closed_before_expansion() -> None:
    payload = _input()
    payload["horizon"] = 5
    payload["constraints"]["allowed_control_action_ids_by_stage"] = {
        str(stage): ["choose_bad", "choose_good", "probe", "wait"] for stage in range(5)
    }
    with pytest.raises(InputError, match="expansion estimate.*exceeds"):
        belief_state_information_value(payload)


def test_fully_observed_state_branching_is_included_in_preflight() -> None:
    payload = _input()
    state_ids = [f"state-{index}" for index in range(20)]
    payload["horizon"] = 4
    payload["latent_states"] = [
        {
            "state_id": state_id,
            "initial_probability": 1.0 if index == 0 else 0.0,
        }
        for index, state_id in enumerate(state_ids)
    ]
    payload["control_actions"] = [{"action_id": "wait"}]
    payload["observations"] = [{"observation_id": "none"}]
    deterministic = {
        state_id: 1.0 if index == 0 else 0.0 for index, state_id in enumerate(state_ids)
    }
    payload["transition_model"] = {
        "wait": {state_id: dict(deterministic) for state_id in state_ids}
    }
    payload["rewards"] = {"wait": dict.fromkeys(state_ids, 0.0)}
    payload["sensors"] = [
        {
            "sensor_id": "none",
            "null_sensor": True,
            "cost": 0.0,
            "likelihood_by_control": {
                "wait": {state_id: {"none": 1.0} for state_id in state_ids}
            },
        }
    ]
    payload["constraints"] = {
        "allowed_control_action_ids_by_stage": {
            str(stage): ["wait"] for stage in range(4)
        },
        "allowed_sensor_ids_by_control": {"wait": ["none"]},
    }

    with pytest.raises(InputError, match="expansion estimate 168453 exceeds"):
        belief_state_information_value(payload)


def test_small_branching_problem_can_use_the_declared_maximum_horizon() -> None:
    payload = _input()
    payload["horizon"] = 12
    payload["constraints"]["allowed_control_action_ids_by_stage"] = {
        str(stage): ["wait"] for stage in range(12)
    }
    payload["constraints"]["allowed_sensor_ids_by_control"] = {
        action["action_id"]: ["none"] for action in payload["control_actions"]
    }
    result = _result(payload)
    assert result["horizon"] == 12
    assert (
        result["assurance"]["estimated_bellman_expansions"]
        <= result["assurance"]["exact_enumeration_budget"]
    )
    assert result["assurance"]["estimated_bellman_expansions"] == 24_649


@pytest.mark.parametrize(
    "target",
    ["latent_states", "control_actions", "observations"],
)
def test_nested_identifier_records_are_strict_at_runtime(target: str) -> None:
    payload = _input()
    payload[target][0]["extra"] = True
    with pytest.raises(InputError, match="entry fields must be strict"):
        belief_state_information_value(payload)


def test_sensor_boolean_is_strict_at_runtime() -> None:
    payload = _input()
    payload["sensors"][1]["null_sensor"] = 0
    with pytest.raises(InputError, match="must be boolean"):
        belief_state_information_value(payload)


def test_probability_tolerance_is_bounded_and_used_consistently() -> None:
    too_loose = _input()
    too_loose["tolerances"]["probability"] = 1e-3
    with pytest.raises(InputError, match="must not exceed"):
        belief_state_information_value(too_loose)

    tolerated = _input()
    tolerated["tolerances"]["probability"] = 1e-6
    tolerated["latent_states"][0]["initial_probability"] = 0.5000004
    result = _result(tolerated)
    assert result["assurance"]["posterior_martingale_max_residual"] <= 1e-6


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["assurance"].update(extra=True),
        lambda value: value["policy_tree"]["branches"][0].update(extra=True),
        lambda value: value["conditional_sensing_values"][0]["sensors"][0].update(
            extra=True
        ),
        lambda value: value["values"].update(net_information_value=99.0),
        lambda value: value["value_by_horizon"][-1].update(net_information_value=99.0),
        lambda value: value["assurance"].update(dual_control_diagnostic=False),
        lambda value: value["assurance"].update(posterior_martingale_max_residual=0.5),
        lambda value: value["conditional_sensing_values"][2]["sensors"][0].update(
            net_increment_vs_null=99.0
        ),
        lambda value: value.update(schema_version="2.0.0"),
        lambda value: value.update(analysis_id=""),
        lambda value: value.update(objective_direction="sideways"),
        lambda value: value.update(horizon=True),
        lambda value: value.update(discount_factor=0.0),
        lambda value: value["policy_tree"].update(belief={}),
        lambda value: value["policy_tree"].update(belief={"bad": 2.0}),
        lambda value: value["policy_tree"].update(stage=True),
        lambda value: value["policy_tree"].update(chronology=[]),
        lambda value: value["policy_tree"]["predictive_belief"].update(extra=0.0),
        lambda value: value["policy_tree"]["control_choice_tie"].append("probe"),
        lambda value: value["policy_tree"].update(selected_control="unknown"),
        lambda value: value["policy_tree"].update(selected_sensor="unknown"),
        lambda value: value["policy_tree"]["branches"][0].update(observation_id=""),
        lambda value: value["policy_tree"]["branches"][1].update(
            observation_id=value["policy_tree"]["branches"][0]["observation_id"]
        ),
        lambda value: value["policy_tree"]["branches"][0].update(probability=0.0),
        lambda value: value["policy_tree"]["branches"][0]["posterior_belief"].update(
            extra=0.0
        ),
        lambda value: value["policy_tree"]["branches"][0]["continuation"].update(
            stage=9
        ),
        lambda value: value["policy_tree"]["branches"][0].update(probability=0.4),
        lambda value: value["values"].update(expected_sensing_cost=-1.0),
        lambda value: value["values"].update(
            myopic_information_value=-1.0, nonmyopic_minus_myopic=7.5
        ),
        lambda value: value["value_by_horizon"].pop(),
        lambda value: value["value_by_horizon"][0].update(horizon=2),
        lambda value: value["value_by_horizon"][-1].update(
            closed_loop_net=1.0, net_information_value=1.0
        ),
        lambda value: value["conditional_sensing_values"][1].update(
            control_action_id=value["conditional_sensing_values"][0][
                "control_action_id"
            ]
        ),
        lambda value: value["conditional_sensing_values"][0]["sensors"][1].update(
            sensor_id=value["conditional_sensing_values"][0]["sensors"][0]["sensor_id"]
        ),
        lambda value: value["conditional_sensing_values"][0]["sensors"][0].update(
            net_value=99.0
        ),
        lambda value: value["stopping"].update(stage=99),
        lambda value: value["approximation_bounds"].update(gap=1.0),
        lambda value: value["assurance"].update(exact_enumeration=1),
        lambda value: value["assurance"].update(solver="approximate"),
        lambda value: value["assurance"].update(estimated_bellman_expansions=999999),
        lambda value: value["language_dispositions"].update(rust="stable"),
        lambda value: value.update(limitations=[""]),
    ],
)
def test_result_semantic_validator_rejects_mutations(mutation: object) -> None:
    result = _result()
    mutation(result)  # type: ignore[operator]
    with pytest.raises((TypeError, ValueError)):
        validate_belief_state_information_result(result)


@pytest.mark.parametrize(
    "field",
    [
        "posterior_martingale_verified",
        "null_sensor_reduction_verified",
        "no_information_reduction_verified",
        "complete_ties_reported",
    ],
)
def test_result_validator_requires_successful_exact_assurance(field: str) -> None:
    result = _result()
    result["assurance"][field] = False
    with pytest.raises(ValueError, match="exact assurance"):
        validate_belief_state_information_result(result)


def test_result_validator_requires_the_governed_expansion_budget() -> None:
    result = _result()
    result["assurance"]["exact_enumeration_budget"] = 50_001
    with pytest.raises(ValueError, match="declared budget"):
        validate_belief_state_information_result(result)


def test_result_validator_reconstructs_all_model_derived_assurance() -> None:
    mutations = [
        lambda result: result["assurance"].update(estimated_bellman_expansions=1),
        lambda result: result["value_by_horizon"][-1].update(
            closed_loop_net=result["value_by_horizon"][-1]["closed_loop_net"] + 100.0,
            no_information=result["value_by_horizon"][-1]["no_information"] + 100.0,
        ),
        lambda result: result["policy_tree"].update(
            control_choice_tie=["fabricated"], selected_control="fabricated"
        ),
        lambda result: result["assurance"].update(
            action_dependent_transition=not result["assurance"][
                "action_dependent_transition"
            ]
        ),
        lambda result: result["assurance"].update(
            usable_downstream_learning_response=not result["assurance"][
                "usable_downstream_learning_response"
            ]
        ),
    ]
    for mutation in mutations:
        result = _result()
        mutation(result)
        with pytest.raises(ValueError, match="reproduce the committed input model"):
            validate_belief_state_information_result(result)


def test_result_validator_requires_an_exact_input_model_commitment() -> None:
    result = _result()
    result["model_assurance"]["input_contract"]["rewards"]["probe"]["bad"] = 99.0
    with pytest.raises(ValueError, match="input model commitment"):
        validate_belief_state_information_result(result)


def test_result_model_reconstruction_accepts_only_its_committed_source() -> None:
    result = _result()
    validate_belief_state_information_result(result)

    source_model = belief_module._validate_and_build(_input())
    source_model.payload["analysis_id"] = "different-source"
    with pytest.raises(ValueError, match="source model does not match"):
        belief_module._validate_belief_state_information_result(
            result, source_model=source_model
        )


def test_result_validator_requires_a_complete_fixed_horizon_policy_tree() -> None:
    one_stage = _input()
    one_stage["horizon"] = 1
    one_stage["constraints"]["allowed_control_action_ids_by_stage"] = {
        "0": ["choose_bad", "choose_good", "probe", "wait"]
    }
    one_stage_result = _result(one_stage)
    one_stage_result["policy_tree"]["stage"] = 1
    with pytest.raises(ValueError, match="stage must match"):
        validate_belief_state_information_result(one_stage_result)

    continued_past_horizon = _result(one_stage)
    continued_past_horizon["policy_tree"]["branches"][0]["continuation"] = deepcopy(
        continued_past_horizon["policy_tree"]
    )
    with pytest.raises(ValueError, match="stop at the fixed horizon"):
        validate_belief_state_information_result(continued_past_horizon)

    truncated = _result()
    truncated["policy_tree"]["branches"][0]["continuation"] = None
    with pytest.raises(ValueError, match="fixed horizon"):
        validate_belief_state_information_result(truncated)


def test_action_dependent_transition_is_reported() -> None:
    payload = _input()
    payload["transition_model"]["probe"] = {
        "bad": {"bad": 0.0, "good": 1.0},
        "good": {"bad": 1.0, "good": 0.0},
    }
    assert _result(payload)["assurance"]["action_dependent_transition"] is True


def test_defensive_observation_and_value_invariants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = belief_module._validate_and_build(_input())
    model.likelihood["none"]["wait"]["bad"] = {"negative": 0.4, "positive": 0.4}
    model.likelihood["none"]["wait"]["good"] = {"negative": 0.4, "positive": 0.4}
    with pytest.raises(ArithmeticError, match="branches must sum"):
        belief_module._observe(model, model.initial_belief, "wait", "none")

    valid_model = belief_module._validate_and_build(_input())
    monkeypatch.setattr(
        belief_module,
        "_adaptive",
        lambda *_args: belief_module._Evaluation(-1.0, -1.0, 0.0, {}),
    )
    with pytest.raises(ArithmeticError, match="information value is negative"):
        belief_module._evaluate(valid_model)
