from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

from scripts.check_consumer_matrix import evaluate_matrix, evaluate_provider_semantics

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "specs/integration/vop-voiage/bundles/consumer-matrix.json"


def test_current_n_minus_one_and_incompatible_matrix_is_independent() -> None:
    evidence = evaluate_matrix(ROOT, MATRIX)
    assert evidence["passed"] is True
    assert [case["actual"] for case in evidence["cases"]] == [
        "backward_compatible",
        "identity_compatible",
        "incompatible",
    ]
    assert "vop" not in {name.split(".")[0] for name in sys.modules}


def test_provider_semantics_accepts_equivalent_shapes_and_rejects_mutations() -> None:
    evidence = evaluate_provider_semantics(ROOT)
    assert evidence["passed"] is True
    assert [case["actual"] for case in evidence["cases"]] == [
        "accepted",
        "rejected",
        "rejected",
    ]


@pytest.mark.parametrize("field", ["pin_sha256", "descriptor_sha256"])
def test_matrix_content_addresses_every_external_input(
    tmp_path: Path, field: str
) -> None:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    section, key = (
        ("bundle", "pin_sha256") if field == "pin_sha256" else ("descriptors", "sha256")
    )
    matrix[section][key] = "0" * 64
    target = tmp_path / "matrix.json"
    target.write_text(json.dumps(matrix), encoding="utf-8")
    with pytest.raises(ValueError, match="digest mismatch"):
        evaluate_matrix(ROOT, target)


@pytest.mark.parametrize("mutation", [[], [{"id": "substitute"}]])
def test_matrix_rejects_missing_or_substituted_cases(
    tmp_path: Path, mutation: list[object]
) -> None:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    matrix["cases"] = mutation
    target = tmp_path / "matrix.json"
    target.write_text(json.dumps(matrix), encoding="utf-8")
    with pytest.raises(ValueError, match="exact required cases"):
        evaluate_matrix(ROOT, target)


def test_matrix_rejects_migration_provenance_not_bound_to_bundle(
    tmp_path: Path,
) -> None:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    source = ROOT / matrix["descriptors"]["path"]
    descriptor = json.loads(source.read_text(encoding="utf-8"))
    descriptor["provenance"]["source_bundle_sha256"] = "0" * 64
    target_descriptor = tmp_path / "migration.json"
    target_descriptor.write_text(json.dumps(descriptor), encoding="utf-8")
    matrix["descriptors"]["path"] = str(target_descriptor)
    matrix["descriptors"]["sha256"] = sha256(target_descriptor.read_bytes()).hexdigest()
    target_matrix = tmp_path / "matrix.json"
    target_matrix.write_text(json.dumps(matrix), encoding="utf-8")
    with pytest.raises(ValueError, match="source bundle provenance mismatch"):
        evaluate_matrix(ROOT, target_matrix)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            {"source_arrow_schema_fingerprint": "0" * 64},
            "source Arrow fingerprint provenance mismatch",
        ),
        ({"derivation": None}, "derivation must not be empty"),
        ({"unexpected": "field"}, "exact required keys"),
    ],
)
def test_matrix_rejects_incomplete_or_false_schema_provenance(
    tmp_path: Path, mutation: dict[str, object], message: str
) -> None:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    source = ROOT / matrix["descriptors"]["path"]
    descriptor = json.loads(source.read_text(encoding="utf-8"))
    descriptor["provenance"].update(mutation)
    target_descriptor = tmp_path / "migration.json"
    target_descriptor.write_text(json.dumps(descriptor), encoding="utf-8")
    matrix["descriptors"]["path"] = str(target_descriptor)
    matrix["descriptors"]["sha256"] = sha256(target_descriptor.read_bytes()).hexdigest()
    target_matrix = tmp_path / "matrix.json"
    target_matrix.write_text(json.dumps(matrix), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        evaluate_matrix(ROOT, target_matrix)
