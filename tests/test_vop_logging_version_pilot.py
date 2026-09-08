"""Fail-closed VOP/VOI pilot contract tests."""

import json
from pathlib import Path

import pytest

from voiage.logging import validate_vop_pilot_contract

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
        {"consumer_version": "unknown"},
        {"unit": "usd_per_qaly"},
        {"weight_field": "wrong_weight"},
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
