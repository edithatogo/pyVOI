#!/usr/bin/env python3
"""Bind mutation score, debt, and density to an immutable source/config cohort."""

# pyright: reportAny=false, reportUnknownVariableType=false, reportUnusedCallResult=false

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import tomllib
from typing import cast

from voiage.mutation_policy import mutation_score_from_mapping, validate_threshold

_STATUSES = {
    "killed",
    "survived",
    "no tests",
    "suspicious",
    "timeout",
    "segfault",
    "skipped",
    "check was interrupted by user",
    "not checked",
    "caught by type check",
}


def _object(path: Path) -> dict[str, object]:
    value: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return cast("dict[str, object]", value)


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def cohort_identity(repo: Path, config_path: Path) -> dict[str, object]:
    """Return canonical Mutmut configuration and source identities."""
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    mutmut = cast(
        "dict[str, object]", cast("dict[str, object]", config["tool"])["mutmut"]
    )
    targets = cast("list[str]", mutmut["only_mutate"])
    sources: list[dict[str, object]] = []
    logical_lines = 0
    for relative in sorted(targets):
        path = repo / relative
        data = path.read_bytes()
        logical_lines += sum(
            1
            for line in data.decode("utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
        sources.append({"path": relative, "sha256": sha256(data).hexdigest()})
    configuration_sha256 = sha256(_canonical(mutmut)).hexdigest()
    lock_path = repo / "uv.lock"
    lock_data = lock_path.read_bytes()
    lock = tomllib.loads(lock_data.decode("utf-8"))
    packages = cast("list[dict[str, object]]", lock["package"])
    mutmut_packages = [
        package for package in packages if package.get("name") == "mutmut"
    ]
    if len(mutmut_packages) != 1:
        raise ValueError("uv.lock must contain exactly one Mutmut package record")
    mutmut_package = mutmut_packages[0]
    locked_version = mutmut_package.get("version")
    if not isinstance(locked_version, str):
        raise ValueError("Mutmut lock record must contain a version")
    # Bind the cohort to the mutation tool's complete lock record, not the
    # entire application lockfile. Unrelated runtime dependency updates must
    # not require re-reviewing an unchanged mutation baseline.
    mutation_lock_identity = _canonical(mutmut_package)
    cohort = {
        "tool": "mutmut",
        "tool_version": locked_version,
        "lock_sha256": sha256(mutation_lock_identity).hexdigest(),
        "configuration_sha256": configuration_sha256,
        "sources": sources,
    }
    return {
        **cohort,
        "source_logical_lines": logical_lines,
        "cohort_sha256": sha256(_canonical(cohort)).hexdigest(),
    }


def validate_runtime_version(identity: dict[str, object], runtime_version: str) -> None:
    """Fail closed when the executing Mutmut differs from the locked cohort tool."""
    expected = identity.get("tool_version")
    if not isinstance(expected, str) or runtime_version != expected:
        raise ValueError("installed Mutmut version does not match the locked cohort")


def mutation_universe(text: str) -> dict[str, object]:
    """Parse and digest the complete stable ID set from ``mutmut results --all``."""
    identities: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        mutant_id, separator, status = line.rpartition(": ")
        if not separator or not mutant_id or status not in _STATUSES:
            raise ValueError(f"invalid mutation-universe row: {line}")
        if mutant_id in identities:
            raise ValueError(f"duplicate mutation identity: {mutant_id}")
        identities[mutant_id] = status
    ids = sorted(identities)
    return {
        "ids": ids,
        "sha256": sha256(_canonical(ids)).hexdigest(),
        "statuses": {mutant_id: identities[mutant_id] for mutant_id in ids},
    }


def evaluate_cohort(
    stats: dict[str, object],
    baseline: dict[str, object],
    identity: dict[str, object],
    universe: dict[str, object],
    threshold: float,
    *,
    baseline_sha256: str,
    reviewed_baseline_sha256: str,
) -> dict[str, object]:
    """Evaluate score and two debt ratchets only for an identical cohort."""
    if baseline.get("schema_version") != "1.0.0":
        raise ValueError("unsupported mutation cohort baseline schema")
    provenance = cast("dict[str, object]", baseline.get("promotion_provenance"))
    provenance_valid = (
        provenance.get("review_state") == "requires_external_anchor"
        and isinstance(provenance.get("run_id"), int)
        and not isinstance(provenance.get("run_id"), bool)
        and isinstance(provenance.get("commit"), str)
        and all(
            character in "0123456789abcdef"
            for character in cast("str", provenance.get("commit"))
        )
        and len(cast("str", provenance.get("commit"))) == 40
        and isinstance(provenance.get("evidence_url"), str)
        and cast("str", provenance.get("evidence_url")).startswith(
            "https://github.com/"
        )
    )
    external_review_anchor_valid = (
        len(reviewed_baseline_sha256) == 64
        and all(
            character in "0123456789abcdef" for character in reviewed_baseline_sha256
        )
        and reviewed_baseline_sha256 == baseline_sha256
    )
    expected_identity = cast("dict[str, object]", baseline["cohort"])
    identity_matches = identity == expected_identity
    score = mutation_score_from_mapping(stats)
    current_ids = cast("list[str]", universe["ids"])
    if len(current_ids) != score.total:
        raise ValueError(
            "mutation universe cardinality does not match statistics total"
        )
    statuses = cast("dict[str, str]", universe["statuses"])
    not_checked = sum(status == "not checked" for status in statuses.values())
    if not_checked:
        raise ValueError("mutation universe contains mutants that were not checked")
    caught_by_type_check = sum(
        status == "caught by type check" for status in statuses.values()
    )
    expected_status_counts = {
        "killed": score.killed,
        "survived": score.survived,
        "no tests": score.no_tests,
        "suspicious": score.suspicious,
        "timeout": score.timeout,
        "segfault": score.segfault,
        "skipped": score.skipped,
        "check was interrupted by user": score.interrupted,
    }
    if any(
        sum(status == expected for status in statuses.values()) != count
        for expected, count in expected_status_counts.items()
    ):
        raise ValueError("mutation universe statuses do not match statistics")
    reconciled_total = sum(expected_status_counts.values()) + caught_by_type_check
    if reconciled_total != score.total:
        raise ValueError(
            "mutation universe statuses do not reconcile to statistics total"
        )
    baseline_universe = cast("dict[str, object]", baseline["universe"])
    baseline_ids = cast("list[str]", baseline_universe["ids"])
    if (
        baseline_universe.get("sha256")
        != sha256(_canonical(sorted(baseline_ids))).hexdigest()
    ):
        raise ValueError("baseline mutation universe digest mismatch")
    added_ids = sorted(set(current_ids) - set(baseline_ids))
    removed_ids = sorted(set(baseline_ids) - set(current_ids))
    universe_matches = not added_ids and not removed_ids
    baseline_score = mutation_score_from_mapping(
        cast("dict[str, object]", baseline["stats"])
    )
    score_report = score.report(validate_threshold(threshold), baseline=baseline_score)
    debt = score.eligible - score.killed
    debt_density = debt / score.eligible if score.eligible else 1.0
    logical_lines = int(cast("int", identity["source_logical_lines"]))
    mutants_per_kloc = score.eligible * 1000.0 / logical_lines if logical_lines else 0.0
    policy = cast("dict[str, object]", baseline["policy"])
    maximum_debt = int(cast("int", policy["maximum_absolute_debt"]))
    maximum_density = float(cast("int | float", policy["maximum_debt_density"]))
    minimum_score = float(cast("int | float", policy["minimum_score_percent"]))
    passed = (
        identity_matches
        and provenance_valid
        and external_review_anchor_valid
        and universe_matches
        and threshold >= minimum_score
        and bool(score_report["passed"])
        and debt <= maximum_debt
        and debt_density <= maximum_density
    )
    return {
        "schema_version": "1.0.0",
        "cohort": identity,
        "expected_cohort_sha256": expected_identity.get("cohort_sha256"),
        "identity_matches": identity_matches,
        "promotion_provenance": provenance,
        "promotion_provenance_valid": provenance_valid,
        "baseline_sha256": baseline_sha256,
        "reviewed_baseline_sha256": reviewed_baseline_sha256,
        "external_review_anchor_valid": external_review_anchor_valid,
        "universe": {
            **universe,
            "baseline_sha256": baseline_universe.get("sha256"),
            "added_ids": added_ids,
            "removed_ids": removed_ids,
            "matches": universe_matches,
        },
        "score": score_report,
        "status_reconciliation": {
            "caught_by_type_check": caught_by_type_check,
            "caught_by_type_check_policy": "counts_as_unresolved_debt",
            "not_checked": 0,
            "reconciled_total": reconciled_total,
        },
        "promoted_minimum_score_percent": minimum_score,
        "debt": {
            "absolute": debt,
            "maximum_absolute": maximum_debt,
            "density": round(debt_density, 6),
            "maximum_density": maximum_density,
            "mutants_per_kloc": round(mutants_per_kloc, 3),
        },
        "passed": passed,
    }


def main() -> int:
    """Evaluate current Mutmut output against its promoted cohort baseline."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stats", type=Path, default=Path("mutants/mutmut-cicd-stats.json")
    )
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--universe", type=Path, required=True)
    parser.add_argument("--reviewed-baseline-sha256", required=True)
    parser.add_argument("--config", type=Path, default=Path("pyproject.toml"))
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--threshold", type=float, default=75.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    baseline_bytes = args.baseline.read_bytes()
    identity = cohort_identity(repo, repo / args.config)
    try:
        from importlib.metadata import version

        runtime_version = version("mutmut")
    except ImportError as exc:
        raise RuntimeError("Mutmut runtime is required for cohort enforcement") from exc
    validate_runtime_version(identity, runtime_version)
    report = evaluate_cohort(
        _object(args.stats),
        _object(args.baseline),
        identity,
        mutation_universe(args.universe.read_text(encoding="utf-8")),
        args.threshold,
        baseline_sha256=sha256(baseline_bytes).hexdigest(),
        reviewed_baseline_sha256=args.reviewed_baseline_sha256,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
