"""Contracts for stable and preview dependency promotion policy."""

from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).parents[1]
POLICY_PATH = (
    ROOT
    / "specs"
    / "submission-readiness"
    / "dependency-promotion-policy-20260829.json"
)
AUDIT_PATH = (
    ROOT / "specs" / "submission-readiness" / "dependency-frontier-audit-20260829.json"
)


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_policy_covers_every_audited_candidate_without_changing_lane_identity() -> None:
    policy = _json(POLICY_PATH)
    audit = _json(AUDIT_PATH)
    lanes = {lane["id"]: lane for lane in policy["lanes"]}
    audited = {lane["id"]: lane for lane in audit["candidate_lanes"]}

    assert lanes.keys() == audited.keys()
    for lane_id, source in audited.items():
        assert lanes[lane_id]["source_lane"] == lane_id
        assert lanes[lane_id]["candidates"] == source["candidates"]
        assert lanes[lane_id]["required_gates"]
        assert lanes[lane_id]["isolation"]


def test_lifecycle_keeps_preview_observation_non_blocking() -> None:
    policy = _json(POLICY_PATH)
    lifecycle = {entry["stage"]: entry for entry in policy["lifecycle"]}

    assert list(lifecycle) == ["observe", "qualify", "candidate", "promote"]
    assert lifecycle["observe"]["blocking"] is False
    assert lifecycle["qualify"]["blocking"] is False
    assert lifecycle["candidate"]["blocking"] is True
    assert lifecycle["promote"]["blocking"] is True
    assert all(lane["blocking_stage"] == "candidate" for lane in policy["lanes"])


def test_universal_gate_requires_numerics_interchange_cpu_and_supply_chain() -> None:
    policy = _json(POLICY_PATH)
    gates = policy["universal_promotion_gates"]

    assert gates.keys() == {
        "correctness",
        "numerics",
        "interchange",
        "packaging",
        "security_and_licence",
        "performance",
        "documentation",
        "hosted",
    }
    assert policy["cpu_fallback_policy"]["required"] is True
    assert (
        "CPU-only clean install" in policy["cpu_fallback_policy"]["promotion_evidence"]
    )
    assert all(gates.values())


def test_receipts_and_rollback_are_fail_closed() -> None:
    policy = _json(POLICY_PATH)
    receipt = policy["promotion_receipt"]
    rollback = policy["rollback_policy"]

    assert len(receipt["required_fields"]) >= 20
    assert {"promote", "reject", "rollback"} <= set(receipt["allowed_decisions"])
    assert "numerical mismatch outside tolerance" in rollback["triggers"]
    assert "publish no release from the failed candidate" in rollback["actions"]
    assert rollback["data_compatibility"]
    assert len(policy["prohibited_shortcuts"]) == 6


def test_dependency_findings_have_explicit_policy_closure() -> None:
    closure = _json(POLICY_PATH)["finding_closure"]

    assert closure.keys() == {"DEP-001", "DEP-002", "DEP-003", "DEP-005", "DEP-006"}
    assert all(closure.values())


def test_preview_workflow_is_isolated_non_blocking_and_observational() -> None:
    workflow = (ROOT / ".github/workflows/dependency-preview.yml").read_text(
        encoding="utf-8"
    )

    assert "pull_request:" not in workflow
    assert "push:" not in workflow
    jobs_section = workflow.split("\njobs:\n", maxsplit=1)[1]
    job_blocks = re.split(r"(?m)^  (?=[a-z][a-z0-9-]+:\s*$)", jobs_section)[1:]
    assert job_blocks
    assert all("continue-on-error: true" in block for block in job_blocks)
    for candidate in (
        "scipy-1.18",
        "pandas-3",
        "xarray-2026",
        "griffe-2",
        "jax-0.11",
        "ruff-0.16",
    ):
        assert candidate in workflow
    assert "uv pip install --python .venv --upgrade --resolution highest" in workflow
    assert "metadata_check_exit_code=" in workflow
    assert "dependency-preview-metadata-check.txt" in workflow
    assert "fetch-depth: 0" in workflow
    assert "env -u RUSTC_WRAPPER cargo install" in workflow
    assert (
        "mozilla-actions/sccache-action@d651010b8da762cde178750d8eda7b5febfe147a"
        in workflow
    )
    assert "Python 3.15 prerelease" in workflow
    assert "cargo-nextest and sccache observation" in workflow
    assert "without publishing artifacts" in workflow


def test_g02_matrix_rejects_unqualified_feature_promotion() -> None:
    matrix = _json(
        ROOT
        / "conductor"
        / "tracks"
        / "agent_safe_engineering_20260907"
        / "dependency-feature-matrix.json"
    )
    assert matrix["workspace_rust_version"] == "1.85"
    assert matrix["resolution"] == "rust/Cargo.lock"
    assert matrix["qualification_policy"]["minimal_lane"] == "no-default-features"
    packages = {row["package"]: row for row in matrix["packages"]}
    diagnostics = packages["voiage-diagnostics"]
    assert diagnostics["features"] == ["otel"]
    assert "feature:otel" in diagnostics["lanes"]
    assert all(
        "feature:otel" not in row["lanes"]
        for name, row in packages.items()
        if name != "voiage-diagnostics"
    )
    assert len(matrix["baseline_input_hashes"]) >= 7
    assert matrix["acceptance_witness"]["expected_red"]
    assert matrix["toolchain"]["workspace_msrv"] == "1.85"
