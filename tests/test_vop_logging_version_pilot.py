"""Fail-closed VOP/VOI pilot contract tests."""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "specs/integration/vop-voiage/pilot-logging-version.json"
UPSTREAM = ROOT / "specs/integration/vop-voiage/bundles/UPSTREAM.json"


def test_pilot_reuses_pinned_upstream_and_semantic_identities() -> None:
    pilot = json.loads(PILOT.read_text())
    upstream = json.loads(UPSTREAM.read_text())
    assert pilot["source_revision"] == upstream["canonical_git_commit"]
    assert pilot["source_bundle"] == str(UPSTREAM.relative_to(ROOT))
    assert set(pilot["identity"]) == {"algorithm_id", "rng_id", "input_schema_id"}
    assert pilot["data_policy"].startswith("synthetic-only")


def _validate(pilot: dict[str, object]) -> None:
    upstream = json.loads(UPSTREAM.read_text())
    if pilot["source_revision"] != upstream["canonical_git_commit"]:
        raise ValueError("source revision mismatch")
    identity = pilot["identity"]
    if not isinstance(identity, dict) or not all(
        identity.get(key) for key in ("algorithm_id", "rng_id", "input_schema_id")
    ):
        raise ValueError("identity is incomplete")
    correlation = pilot["correlation"]
    if (
        not isinstance(correlation, dict)
        or not correlation.get("run_id")
        or len(str(correlation.get("trace_id", ""))) != 32
    ):
        raise ValueError("correlation is malformed")
    if pilot["consumer_version"] != "2.2.0":
        raise ValueError("unknown consumer version")


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
    ],
)
def test_pilot_rejects_contract_mutations(mutation: dict[str, object]) -> None:
    pilot = json.loads(PILOT.read_text())
    pilot.update(mutation)
    with pytest.raises(ValueError):
        _validate(pilot)
