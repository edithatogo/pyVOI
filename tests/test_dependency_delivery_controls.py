"""Keep dependency automation and coverage delivery within reviewed boundaries."""

from fnmatch import fnmatchcase
import json
from pathlib import Path
import re

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_codecov_upload_uses_real_authoritative_report_and_oidc() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    job = workflow["jobs"]["coverage-report"]
    assert job["permissions"] == {"contents": "read", "id-token": "write"}
    steps = job["steps"]
    generation = next(
        i
        for i, step in enumerate(steps)
        if "tox -e coverage_report" in step.get("run", "")
    )
    upload_index = next(
        i
        for i, step in enumerate(steps)
        if step.get("uses", "").startswith("codecov/codecov-action@")
    )
    upload = steps[upload_index]
    assert generation < upload_index
    assert not upload.get("continue-on-error", False)
    assert "if" not in upload
    assert re.fullmatch(r"codecov/codecov-action@[0-9a-f]{40}", upload["uses"])
    assert upload["with"]["files"] == "./coverage.xml"
    assert upload["with"]["use_oidc"] is True
    assert upload["with"]["fail_ci_if_error"] is True
    assert upload["with"]["disable_search"] is True
    assert "token" not in upload["with"]


def test_renovate_inherits_owner_policy_without_changing_library_support() -> None:
    config = json.loads((ROOT / "renovate.json").read_text())
    assert config["extends"][0] == "github>edithatogo/renovate-config"
    assert config["rangeStrategy"] == "auto"
    rules = config["packageRules"]
    assert all(rule.get("automergeType") != "branch" for rule in rules)
    assert all("matchPackagePatterns" not in rule for rule in rules)
    library = next(
        rule
        for rule in rules
        if "Preserve published library" in rule.get("description", "")
    )
    assert {"cargo", "pep621", "pip_requirements", "pip_setup"} <= set(
        library["matchManagers"]
    )
    assert library["rangeStrategy"] == "auto"
    assert library["automerge"] is False
    final = rules[-1]
    assert set(config["enabledManagers"]) <= set(final["matchManagers"])
    assert final["automerge"] is False
    assert final["automergeType"] == "pr"
    engines = next(rule for rule in rules if rule.get("matchDepTypes") == ["engines"])
    assert engines["enabled"] is False
    interpreter = next(
        rule for rule in rules if "python-version" in rule.get("matchDatasources", [])
    )
    assert {"python-version", "node-version", "rust-version"} <= set(
        interpreter["matchDatasources"]
    )
    assert interpreter["matchUpdateTypes"] == ["pin"]
    assert interpreter["enabled"] is False


@pytest.mark.parametrize(
    "package", ["typer", "typing_extensions", "types-requests", "types-setuptools"]
)
def test_linting_group_does_not_capture_runtime_or_stub_packages(package: str) -> None:
    config = json.loads((ROOT / "renovate.json").read_text())
    lint = next(
        rule for rule in config["packageRules"] if rule.get("groupSlug") == "linting"
    )
    assert lint["matchPackageNames"] == ["ruff", "ty"]
    assert package not in lint["matchPackageNames"]


def test_renovate_keeps_archival_environments_outside_live_dependency_updates() -> None:
    config = json.loads((ROOT / "renovate.json").read_text())
    archive_rule = next(
        rule
        for rule in config["packageRules"]
        if rule.get("matchFileNames")
        == [
            "paper/reproduction-environment/**",
            "specs/submission-readiness/dependency-frontier-environment-20260829/**",
        ]
    )
    assert archive_rule["enabled"] is False
    patterns = archive_rule["matchFileNames"]
    for archived in (
        "paper/reproduction-environment/pyproject.toml",
        "paper/reproduction-environment/uv.lock",
        "specs/submission-readiness/dependency-frontier-environment-20260829/pyproject.toml",
    ):
        assert any(fnmatchcase(archived, pattern) for pattern in patterns)
    for live in (
        "pyproject.toml",
        "uv.lock",
        "requirements-joss.txt",
        "docs/astro-site/package.json",
    ):
        assert not any(fnmatchcase(live, pattern) for pattern in patterns)


def test_governed_python_upgrades_require_separate_qualification() -> None:
    config = json.loads((ROOT / "renovate.json").read_text())
    rule = next(
        rule
        for rule in config["packageRules"]
        if rule.get("matchPackageNames") == ["scipy", "jax", "mutmut"]
    )
    assert rule["matchManagers"] == ["pep621"]
    assert rule["groupName"] is None
    assert rule["groupSlug"] is None
    assert rule["dependencyDashboardApproval"] is True
    assert rule["automerge"] is False


def test_release_automation_policy_has_distinct_fail_closed_states() -> None:
    policy = json.loads(
        (
            ROOT
            / "conductor/tracks/agent_safe_engineering_20260907/automation-policy.json"
        ).read_text(encoding="utf-8")
    )
    assert policy["schema_version"] == "1.0"
    states = set(policy["states"])
    assert {"pending", "verified", "staged", "published", "partial", "failed"} <= states
    transitions = {tuple(edge) for edge in policy["allowed_transitions"]}
    assert ("staged", "published") in transitions
    assert ("staged", "partial") in transitions
    assert ("partial", "failed") in transitions
    assert ("pending", "published") not in transitions
    assert ("partial", "published") not in transitions
    assert len(policy["required_evidence"]) == len(set(policy["required_evidence"]))
    assert {
        "artifact_digest_mismatch",
        "signer_unverified",
        "exception_expired",
        "platform_receipt_missing",
        "publication_partial",
        "replay_artifact_mismatch",
    } <= set(policy["failure_reasons"])

    guards = policy["failure_guards"]
    assert ["staged", "published"] in guards["artifact_digest_mismatch"][
        "blocked_transitions"
    ]
    assert ["staged", "published"] in guards["signer_unverified"]["blocked_transitions"]


def test_release_automation_policy_binds_immutable_artifacts_and_no_publish_authority() -> (
    None
):
    policy = json.loads(
        (
            ROOT
            / "conductor/tracks/agent_safe_engineering_20260907/automation-policy.json"
        ).read_text(encoding="utf-8")
    )
    invariants = set(policy["invariants"])
    assert (
        "a release version is bound to one immutable source commit and artifact digest"
        in invariants
    )
    assert (
        "replay cannot publish different artifact bytes under an existing version"
        in invariants
    )
    assert any("never authorizes" in invariant for invariant in invariants)


def test_release_automation_policy_rejects_staged_publish_for_digest_and_signer_failures() -> (
    None
):
    policy = json.loads(
        (
            ROOT
            / "conductor/tracks/agent_safe_engineering_20260907/automation-policy.json"
        ).read_text(encoding="utf-8")
    )
    publish_edge = ["staged", "published"]
    for reason in ("artifact_digest_mismatch", "signer_unverified"):
        assert publish_edge in policy["failure_guards"][reason]["blocked_transitions"]
