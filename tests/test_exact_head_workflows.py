"""Regression tests for exact-source checkout provenance in C15 gates."""

from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"
SOURCE_HEAD_EXPRESSION = "${{ github.event.pull_request.head.sha || github.sha }}"


def _assert_exact_head_steps(steps: list[dict[str, object]]) -> None:
    checkout = steps[0]
    assert str(checkout["uses"]).startswith("actions/checkout@")
    options = checkout["with"]
    assert isinstance(options, dict)
    assert options == {
        "ref": SOURCE_HEAD_EXPRESSION,
        "fetch-depth": 0,
        "persist-credentials": False,
    }

    assertion = steps[1]
    assert assertion["name"] == "Assert and record exact source head"
    assert assertion["env"] == {"EXPECTED_SOURCE_HEAD": SOURCE_HEAD_EXPRESSION}
    command = str(assertion["run"])
    assert 'tested_head="$(git rev-parse HEAD)"' in command
    assert 'test "${tested_head}" = "${EXPECTED_SOURCE_HEAD}"' in command
    assert "GITHUB_STEP_SUMMARY" in command


def test_every_polyglot_job_binds_and_records_exact_source_head() -> None:
    workflow = yaml.safe_load(
        (WORKFLOWS / "bindings-ci.yml").read_text(encoding="utf-8")
    )
    for job_name in ("rust", "julia", "r"):
        _assert_exact_head_steps(workflow["jobs"][job_name]["steps"])


def test_mutation_job_binds_and_records_exact_source_head() -> None:
    workflow = yaml.safe_load((WORKFLOWS / "ci.yml").read_text(encoding="utf-8"))
    _assert_exact_head_steps(workflow["jobs"]["test-mutation"]["steps"])


def test_coverage_job_binds_and_records_exact_source_head() -> None:
    workflow = yaml.safe_load((WORKFLOWS / "ci.yml").read_text(encoding="utf-8"))
    _assert_exact_head_steps(workflow["jobs"]["coverage-report"]["steps"])
