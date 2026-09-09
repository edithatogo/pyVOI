#!/usr/bin/env python3
"""Validate the independent current/N-1/incompatible VOP consumer matrix."""

# pyright: reportAny=false, reportUnusedCallResult=false

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from math import isclose, isfinite
from pathlib import Path
from typing import cast

from voiage.contracts.bundle import (
    BundleVerificationError,
    validate_schema_evolution,
    verify_pinned_contract_bundle,
)

_REQUIRED_CASES: tuple[dict[str, object], ...] = (
    {
        "id": "n-minus-1-to-current",
        "from": "n_minus_1",
        "to": "current",
        "expected": "backward_compatible",
    },
    {
        "id": "current-identity",
        "from": "current",
        "to": "current",
        "expected": "identity_compatible",
    },
    {
        "id": "intentionally-incompatible-dtype",
        "from": "n_minus_1",
        "to": "current",
        "mutation": {
            "field": "incremental_cost",
            "property": "arrow_type",
            "value": "float32",
        },
        "expected": "incompatible",
    },
)
_PROVENANCE_KEYS = {
    "derivation",
    "source_arrow_schema_fingerprint",
    "source_bundle_sha256",
}
_SEMANTIC_FIXTURE = Path(
    "tests/fixtures/compatibility_witnesses/provider-semantics.json"
)


def _object(path: Path) -> dict[str, object]:
    value: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return cast("dict[str, object]", value)


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _canonical_provider(provider: dict[str, object]) -> tuple[tuple[float, ...], ...]:
    """Translate one provider shape to the narrow VOI sample interchange."""
    if provider.get("utility_unit") != "net-benefit":
        raise ValueError("provider utility_unit must be net-benefit")
    raw_rows = provider.get("rows")
    if not isinstance(raw_rows, list) or not raw_rows:
        raise ValueError("provider rows must be a non-empty list")
    rows: list[tuple[float, ...]] = []
    weights: list[float] = []
    for raw_row in raw_rows:
        if not isinstance(raw_row, dict):
            raise TypeError("provider row must be an object")
        raw_values = raw_row.get("net_benefit")
        raw_weight = raw_row.get("weight")
        if not isinstance(raw_values, list) or not isinstance(raw_weight, (int, float)):
            raise TypeError("provider row requires net_benefit and weight")
        values = tuple(float(value) for value in raw_values)
        if not values or any(not isfinite(value) for value in values):
            raise ValueError("provider net_benefit values must be finite")
        weight = float(raw_weight)
        if not isfinite(weight) or weight < 0:
            raise ValueError("provider weights must be finite and non-negative")
        rows.append(values)
        weights.append(weight)
    if len({len(row) for row in rows}) != 1 or not isclose(sum(weights), 1.0):
        raise ValueError("provider rows must share shape and weights must sum to one")
    return tuple(
        sorted((*row, weight) for row, weight in zip(rows, weights, strict=True))
    )


def evaluate_provider_semantics(
    repo: Path, fixture_path: Path = _SEMANTIC_FIXTURE
) -> dict[str, object]:
    """Check equivalent provider representations and fail-closed mutations."""
    fixture = _object(repo / fixture_path)
    if fixture.get("schema_version") != "1.0.0":
        raise ValueError("unsupported provider semantics schema")
    cases = fixture.get("cases")
    if not isinstance(cases, list) or len(cases) != 3:
        raise ValueError("provider semantics fixture must contain three cases")
    results: list[dict[str, object]] = []
    for case in cases:
        if not isinstance(case, dict):
            raise TypeError("provider semantics case must be an object")
        providers = case.get("providers")
        if not isinstance(providers, list) or not providers:
            raise ValueError("provider semantics case requires providers")
        invalid_provider = next(
            (provider for provider in providers if not isinstance(provider, dict)), None
        )
        if invalid_provider is not None:
            actual = "rejected"
            detail = "provider must be an object"
        else:
            try:
                canonical = [_canonical_provider(provider) for provider in providers]
            except (TypeError, ValueError) as error:
                actual = "rejected"
                detail = str(error)
            else:
                actual = (
                    "accepted"
                    if len({repr(item) for item in canonical}) == 1
                    else "rejected"
                )
                detail = (
                    "equivalent canonical interchange"
                    if actual == "accepted"
                    else "semantic mismatch"
                )
        results.append(
            {
                "id": case.get("id"),
                "expected": case.get("expected"),
                "actual": actual,
                "detail": detail,
            }
        )
    return {
        "schema_version": "1.0.0",
        "cases": results,
        "passed": all(item["expected"] == item["actual"] for item in results),
    }


def evaluate_matrix(repo: Path, matrix_path: Path) -> dict[str, object]:
    """Return fail-closed, content-addressed consumer-matrix evidence."""
    matrix = _object(matrix_path)
    if (
        set(matrix)
        != {
            "schema_version",
            "matrix_id",
            "producer_runtime_dependency",
            "bundle",
            "descriptors",
            "cases",
        }
        or matrix.get("schema_version") != "1.0.0"
    ):
        raise ValueError("unsupported consumer matrix schema")
    if matrix.get("producer_runtime_dependency") is not False:
        raise ValueError("consumer matrix must not depend on VOP runtime code")
    bundle = cast("dict[str, object]", matrix["bundle"])
    descriptors = cast("dict[str, object]", matrix["descriptors"])
    pin_path = repo / cast("str", bundle["pin_path"])
    descriptor_path = repo / cast("str", descriptors["path"])
    if _digest(pin_path) != bundle.get("pin_sha256"):
        raise ValueError("consumer pin digest mismatch")
    if _digest(descriptor_path) != descriptors.get("sha256"):
        raise ValueError("migration descriptor digest mismatch")
    verified = verify_pinned_contract_bundle(
        repo / cast("str", bundle["path"]), pin_path
    )
    transition = _object(descriptor_path)
    provenance = transition.get("provenance")
    if not isinstance(provenance, dict):
        raise TypeError("migration provenance must be an object")
    typed_provenance = cast("dict[str, object]", provenance)
    if set(typed_provenance) != _PROVENANCE_KEYS:
        raise ValueError("migration provenance must contain the exact required keys")
    if typed_provenance.get("source_bundle_sha256") != verified.bundle_sha256:
        raise ValueError("migration source bundle provenance mismatch")
    n_minus_1_key = descriptors.get("n_minus_1")
    current_key = descriptors.get("current")
    if not isinstance(n_minus_1_key, str) or not isinstance(current_key, str):
        raise TypeError("descriptor roles must be strings")
    roles = {
        "n_minus_1": cast("dict[str, object]", transition[n_minus_1_key]),
        "current": cast("dict[str, object]", transition[current_key]),
    }
    source_fingerprint = typed_provenance.get("source_arrow_schema_fingerprint")
    if (
        source_fingerprint != verified.arrow_schema_fingerprint
        or source_fingerprint != roles["n_minus_1"].get("schema_fingerprint")
    ):
        raise ValueError("migration source Arrow fingerprint provenance mismatch")
    derivation = typed_provenance.get("derivation")
    if not isinstance(derivation, str) or not derivation.strip():
        raise ValueError("migration provenance derivation must not be empty")
    raw_cases = matrix["cases"]
    if not isinstance(raw_cases, list) or raw_cases != list(_REQUIRED_CASES):
        raise ValueError("consumer matrix must contain the exact required cases")
    results: list[dict[str, object]] = []
    for raw_case in cast("list[object]", raw_cases):
        case = cast("dict[str, object]", raw_case)
        previous = deepcopy(roles[cast("str", case["from"])])
        current = deepcopy(roles[cast("str", case["to"])])
        mutation = case.get("mutation")
        if mutation is not None:
            change = cast("dict[str, object]", mutation)
            fields = cast("list[dict[str, object]]", current["fields"])
            field = next(item for item in fields if item["name"] == change["field"])
            field[cast("str", change["property"])] = change["value"]
        expected = case["expected"]
        try:
            outcome = validate_schema_evolution(previous, current)
        except BundleVerificationError:
            actual = "incompatible"
        else:
            actual = (
                "identity_compatible"
                if outcome.forward_compatible
                else "backward_compatible"
            )
        results.append({"id": case["id"], "expected": expected, "actual": actual})
    passed = all(item["expected"] == item["actual"] for item in results)
    return {
        "schema_version": "1.0.0",
        "matrix_id": matrix["matrix_id"],
        "bundle_sha256": verified.bundle_sha256,
        "pin_sha256": _digest(pin_path),
        "descriptor_sha256": _digest(descriptor_path),
        "cases": results,
        "passed": passed,
    }


def main() -> int:
    """Run the matrix and optionally retain its JSON evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--matrix",
        type=Path,
        default=Path("specs/integration/vop-voiage/bundles/consumer-matrix.json"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    evidence = evaluate_matrix(args.repo.resolve(), args.matrix.resolve())
    rendered = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    print(rendered, end="")
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    return 0 if evidence["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
