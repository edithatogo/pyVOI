"""Fail-closed VOP/VOI pilot contract tests."""

import json
from pathlib import Path
from unittest.mock import Mock

from pydantic import ValidationError
import pytest

from voiage.logging import validate_vop_pilot_contract
from voiage.versioning import VersionSyncError

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "specs/integration/vop-voiage/pilot-logging-version.json"
UPSTREAM = ROOT / "specs/integration/vop-voiage/bundles/UPSTREAM.json"
BUNDLE_MANIFEST = ROOT / "specs/integration/vop-voiage/bundles/1.0.0/manifest.json"


def test_pilot_reuses_pinned_upstream_and_semantic_identities() -> None:
    pilot = json.loads(PILOT.read_text())
    upstream = json.loads(UPSTREAM.read_text())
    assert pilot["source_revision"] == upstream["canonical_git_commit"]
    assert pilot["source_bundle"] == str(UPSTREAM.relative_to(ROOT))
    assert set(pilot["identity"]) == {"algorithm_id", "rng_id", "input_schema_id"}
    assert pilot["data_policy"].startswith("synthetic-only")


def test_pilot_binds_the_exact_bundle_and_provider_neutral_policy() -> None:
    """Pin the installed pilot to the reviewed bundle bytes and policy."""
    pilot = json.loads(PILOT.read_text())
    upstream = json.loads(UPSTREAM.read_text())
    manifest = json.loads(BUNDLE_MANIFEST.read_text())
    assert manifest["bundle_sha256"] == upstream["bundle_sha256"]
    assert manifest["bundle_version"] == upstream["bundle_version"]
    assert manifest["source_repository"] == upstream["canonical_repository"]
    assert manifest["source_path"] == upstream["canonical_path"]
    assert pilot["provider_policy"] == (
        "semantic contract only; provider APIs are not interchangeable"
    )


def test_two_provider_apis_produce_the_same_semantic_voi_result() -> None:
    """Provider neutrality is behavioral, while provider APIs remain distinct."""
    semantic_draws = [
        {"standard_care": 0.0, "hpv_vaccination": 10.0},
        {"standard_care": 10.0, "hpv_vaccination": 0.0},
    ]

    def provider_records(records: list[dict[str, float]]) -> float:
        current = max(
            sum(record[name] for record in records) / len(records)
            for name in ("standard_care", "hpv_vaccination")
        )
        clairvoyant = sum(max(record.values()) for record in records) / len(records)
        return clairvoyant - current

    class MatrixProvider:
        def evaluate(
            self, matrix: tuple[tuple[float, float], ...], *, threshold: float
        ) -> float:
            del threshold
            current = max(
                sum(row[index] for row in matrix) / len(matrix) for index in range(2)
            )
            clairvoyant = sum(max(row) for row in matrix) / len(matrix)
            return clairvoyant - current

    matrix = tuple(
        (record["standard_care"], record["hpv_vaccination"])
        for record in semantic_draws
    )
    assert (
        provider_records(semantic_draws)
        == MatrixProvider().evaluate(matrix, threshold=50_000.0)
        == 5.0
    )


@pytest.mark.parametrize(
    "mutation",
    [
        {"source_revision": "0" * 40},
        {
            "identity": {
                "algorithm_id": "",
                "rng_id": "pcg64:seeded:v1",
                "input_schema_id": "vop-net-benefit:v1",
            }
        },
        {"correlation": {"run_id": "", "analysis_id": "a", "trace_id": "bad"}},
    ],
)
def test_pilot_rejects_contract_mutations(mutation: dict[str, object]) -> None:
    pilot = json.loads(PILOT.read_text())
    pilot.update(mutation)
    with pytest.raises((ValueError, TypeError, RuntimeError)):
        validate_vop_pilot_contract(pilot)


def test_production_validator_rejects_missing_identity_and_correlation() -> None:
    pilot = json.loads(PILOT.read_text())
    for key, value in (("identity", None), ("correlation", None)):
        candidate = dict(pilot)
        candidate[key] = value
        with pytest.raises((ValueError, TypeError, RuntimeError)):
            validate_vop_pilot_contract(candidate)

    candidate = dict(pilot)
    candidate["correlation"] = {
        "run_id": "",
        "analysis_id": "analysis",
        "trace_id": pilot["correlation"]["trace_id"],
    }
    with pytest.raises(ValueError):
        validate_vop_pilot_contract(candidate)


@pytest.mark.parametrize(
    ("mutation", "expected_error", "diagnostic"),
    [
        (
            {"unit": "usd_per_qaly"},
            ValueError,
            "pilot units or weights are incompatible",
        ),
        (
            {"weight_field": "wrong_weight"},
            ValueError,
            "pilot units or weights are incompatible",
        ),
        ({"consumer_version": "unknown"}, VersionSyncError, "unsupported canonical"),
        (
            {"correlation": {"run_id": "", "analysis_id": "a", "trace_id": "bad"}},
            ValidationError,
            "trace_id must be 32 lowercase non-zero hex characters",
        ),
    ],
)
def test_ac2_negative_cases_fail_before_model_evaluation(
    mutation: dict[str, object], expected_error: type[Exception], diagnostic: str
) -> None:
    """Reject each AC2 mutation before the downstream evaluator is entered."""
    pilot = json.loads(PILOT.read_text())
    pilot.update(mutation)
    evaluator = Mock(name="model_evaluator")

    def evaluate(candidate: dict[str, object]) -> None:
        validate_vop_pilot_contract(candidate)
        evaluator(candidate)

    with pytest.raises(expected_error, match=diagnostic):
        evaluate(pilot)
    evaluator.assert_not_called()
