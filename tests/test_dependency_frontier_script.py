"""Unit contracts for the dependency-frontier policy implementation."""

from __future__ import annotations

from packaging.requirements import Requirement

from scripts.dependency_frontier import audit_requirement, usable_versions


def test_frontier_separates_support_floor_lock_and_upper_bound() -> None:
    row = audit_requirement(
        "core",
        Requirement("example>=1.0,<3"),
        {"example": ["2.5"]},
        {
            "releases": {
                "1.0": [{}],
                "2.5": [{}],
                "3.0": [{}],
                "4.0rc1": [{}],
            }
        },
    )

    assert row["minimum_supported"] == "1.0"
    assert row["locked"] == ["2.5"]
    assert row["latest_compatible"] == "2.5"
    assert row["latest_overall"] == "3.0"
    assert row["upper_bound_blocker"] is True
    assert row["policy_violations"] == []


def test_frontier_fails_only_real_lock_policy_violations() -> None:
    missing = audit_requirement(
        "core", Requirement("example>=1"), {}, {"releases": {"1.0": [{}]}}
    )
    incompatible = audit_requirement(
        "core",
        Requirement("example>=2"),
        {"example": ["1.0"]},
        {"releases": {"1.0": [{}], "2.0": [{}]}},
    )

    assert missing["policy_violations"] == ["missing_from_lock"]
    assert incompatible["policy_violations"] == [
        "locked_version_outside_declared_range"
    ]


def test_yanked_and_prerelease_versions_are_not_stable_frontier() -> None:
    versions = usable_versions(
        {
            "1.0": [{}],
            "2.0": [{"yanked": True}],
            "3.0b1": [{}],
        }
    )

    assert [str(version) for version in versions] == ["1.0"]


def test_rust_feature_matrix_names_default_optional_and_all_feature_lanes() -> None:
    from scripts.rust_feature_matrix import build_matrix

    report = build_matrix(__import__("pathlib").Path.cwd())
    diagnostics = next(
        row for row in report["packages"] if row["package"] == "voiage-diagnostics"
    )
    assert report["workspace_rust_version"] == "1.85"
    assert diagnostics["features"] == ["otel"]
    assert diagnostics["lanes"] == [
        "default",
        "no-default-features",
        "feature:otel",
        "all-features",
    ]


def test_rust_feature_matrix_verification_is_locked_and_covers_minimal_lane(
    monkeypatch,
):
    from pathlib import Path

    from scripts.rust_feature_matrix import build_matrix, verify_matrix

    commands = []
    monkeypatch.setattr(
        "scripts.rust_feature_matrix.subprocess.run",
        lambda command, **kwargs: commands.append((command, kwargs)),
    )
    verify_matrix(Path.cwd(), build_matrix(Path.cwd()))
    assert commands
    assert all(item[0][item[0].index("--locked")] == "--locked" for item in commands)
    assert any("--no-default-features" in item[0] for item in commands)
    assert any("--all-features" in item[0] for item in commands)
