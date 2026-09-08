"""Regression contracts for the accepted core, API, and ABI repair findings."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from scripts.check_abi_compatibility import compare

ROOT = Path(__file__).parents[1]
DISPOSITIONS = ROOT / "specs" / "abi" / "industry-decision-binding-dispositions.json"
ABI_RELEASE = ROOT / "specs" / "abi" / "releases" / "v2.1.0"
INSTALLED_RECEIPT = (
    ROOT
    / "specs"
    / "submission-readiness"
    / "installed-binding-validation-20260829.json"
)


def test_decision_problem_manifest_matches_shipped_language_surfaces() -> None:
    manifest = json.loads(DISPOSITIONS.read_text(encoding="utf-8"))
    dispositions = manifest["contracts"]["decision_problem"]["dispositions"]

    assert dispositions["python"] == {
        "status": "implemented",
        "symbol": "voiage.schema.DecisionProblem",
        "interchange": "json_and_arrow",
    }
    assert dispositions["rust"] == {
        "status": "internal",
        "symbol": "voiage_domain::DecisionProblem",
        "interchange": "native_only",
        "reason": "Internal domain type; not a public C ABI or language-binding surface.",
    }
    for language in ("r", "julia"):
        assert dispositions[language]["status"] == "unsupported"
        assert dispositions[language]["symbol"] == ""
        assert dispositions[language]["interchange"] == ""
        assert "DecisionProblem" in dispositions[language]["reason"]


def test_manifest_validator_resolves_implemented_python_symbols() -> None:
    command = [
        sys.executable,
        "-c",
        (
            "from voiage.binding_dispositions import "
            "validate_binding_dispositions_manifest; "
            "assert validate_binding_dispositions_manifest(resolve_symbols=True)"
        ),
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_v210_abi_release_baseline_is_immutable_and_machine_checked() -> None:
    required = {
        "symbols.txt",
        "layouts.txt",
        "voiage_v1.h",
        "metadata.json",
    }
    assert {path.name for path in ABI_RELEASE.iterdir() if path.is_file()} == required

    metadata = json.loads((ABI_RELEASE / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["release"] == "v2.1.0"
    assert metadata["abi_major"] == 1
    assert metadata["source_commit"]
    assert metadata["artifacts_sha256"].keys() == required - {"metadata.json"}

    result = subprocess.run(
        [
            sys.executable,
            "scripts/check_abi_compatibility.py",
            "--baseline",
            str(ABI_RELEASE),
            "--candidate-header",
            "rust/crates/voiage-ffi/include/voiage_v1.h",
            "--candidate-symbols",
            "specs/abi/v1/symbols.txt",
            "--candidate-layouts",
            "specs/abi/v1/layouts.txt",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_abi_checker_rejects_removed_symbols_signature_and_layout_changes(
    tmp_path: Path,
) -> None:
    header = tmp_path / "voiage_v1.h"
    symbols = tmp_path / "symbols.txt"
    layouts = tmp_path / "layouts.txt"
    shutil.copyfile(ROOT / "rust/crates/voiage-ffi/include/voiage_v1.h", header)
    shutil.copyfile(ROOT / "specs/abi/v1/symbols.txt", symbols)
    shutil.copyfile(ROOT / "specs/abi/v1/layouts.txt", layouts)

    symbols.write_text(
        symbols.read_text(encoding="utf-8").replace("voiage_v1_evpi\n", ""),
        encoding="utf-8",
    )
    removed = compare(ABI_RELEASE, header, symbols, layouts)
    assert removed["compatible"] is False
    assert "removed released symbols: voiage_v1_evpi" in removed["errors"]

    shutil.copyfile(ROOT / "specs/abi/v1/symbols.txt", symbols)
    header.write_text(
        header.read_text(encoding="utf-8").replace("uint64_t rows", "int64_t rows"),
        encoding="utf-8",
    )
    changed_signature = compare(ABI_RELEASE, header, symbols, layouts)
    assert changed_signature["compatible"] is False
    assert "changed released declaration: voiage_v1_evpi" in changed_signature["errors"]

    shutil.copyfile(ROOT / "rust/crates/voiage-ffi/include/voiage_v1.h", header)
    layouts.write_text(
        layouts.read_text(encoding="utf-8").replace(
            "VoiageHandleV1 8 8", "VoiageHandleV1 16 8"
        ),
        encoding="utf-8",
    )
    changed_layout = compare(ABI_RELEASE, header, symbols, layouts)
    assert changed_layout["compatible"] is False
    assert "changed released layout: VoiageHandleV1" in changed_layout["errors"]


def test_binding_capability_contract_requires_behavior_not_workflow_text() -> None:
    contract = json.loads(
        (
            ROOT
            / "specs"
            / "submission-readiness"
            / "installed-binding-capability-contract-v1.json"
        ).read_text(encoding="utf-8")
    )

    assert contract["schema_version"] == "1.0.0"
    assert contract["source_of_truth"] == (
        "specs/submission-readiness/target-architecture-freeze-20260829.json"
    )
    assert contract["required_surfaces"] == ["python", "rust", "c_abi", "r", "julia"]
    assert set(contract["required_checks"]) == {
        "enumerate exported symbols from installed artifact",
        "invoke every declared stable capability",
        "compare shared numerical fixtures",
        "reject unsupported capability through a declared error",
        "verify source version and artifact digest",
    }
    assert contract["prohibited_evidence"] == [
        "manifest substring checks",
        "workflow command substring checks",
        "repository-relative import or library lookup",
    ]


def test_installed_binding_receipt_is_artifact_and_fixture_bound() -> None:
    receipt = json.loads(INSTALLED_RECEIPT.read_text(encoding="utf-8"))

    assert receipt["release_version"] == "2.1.0"
    assert receipt["evidence_revision"]
    reference = receipt["shared_reference"]
    reference_path = ROOT / reference["path"]
    assert (
        hashlib.sha256(reference_path.read_bytes()).hexdigest() == reference["sha256"]
    )
    assert reference["case_count"] == 8

    surfaces = receipt["surfaces"]
    assert set(surfaces) == {"python", "c_abi", "r", "julia"}
    assert all(surface["status"] == "passed_local" for surface in surfaces.values())
    assert all(len(surface["sha256"]) == 64 for surface in surfaces.values())
    assert surfaces["c_abi"]["declared_symbol_count"] == 10
    assert surfaces["r"]["coverage_percent"] >= 75
    assert {gate["state"] for gate in receipt["external_gates"]} == {
        "external_gate",
        "pending",
    }
    assert "does not submit" in receipt["submission_boundary"]


def test_current_binding_capability_registry_matches_architecture_freeze() -> None:
    architecture = json.loads(
        (
            ROOT / "specs/submission-readiness/target-architecture-freeze-20260829.json"
        ).read_text(encoding="utf-8")
    )
    registry = json.loads(
        (ROOT / "specs/bindings/current-capability-matrix.json").read_text(
            encoding="utf-8"
        )
    )

    assert registry["status"] == "current"
    assert registry["source_of_truth"].endswith("#capability_matrix")
    assert registry["capabilities"] == architecture["capability_matrix"]
    assert registry["released_packaging_matrix"] == "specs/v1/binding-matrix.json"


def test_public_binding_docs_distinguish_internal_and_unavailable_surfaces() -> None:
    reference = (
        ROOT / "docs/astro-site/src/content/docs/reference/bindings.mdx"
    ).read_text(encoding="utf-8")
    api = (
        ROOT / "docs/astro-site/src/content/docs/api-reference/binding-dispositions.mdx"
    ).read_text(encoding="utf-8")

    assert "Current method-level capability matrix" in reference
    assert "| `DecisionProblem` | stable | internal type | unavailable" in reference
    assert "Julia 1.12" in reference
    assert "`internal` means" in api
    assert "not exposed by the C ABI, R, or Julia" in api


def test_abi_checker_accepts_additive_symbol_with_matching_declaration(
    tmp_path: Path,
) -> None:
    header = tmp_path / "voiage_v1.h"
    symbols = tmp_path / "symbols.txt"
    layouts = tmp_path / "layouts.txt"
    shutil.copyfile(ROOT / "rust/crates/voiage-ffi/include/voiage_v1.h", header)
    shutil.copyfile(ROOT / "specs/abi/v1/symbols.txt", symbols)
    shutil.copyfile(ROOT / "specs/abi/v1/layouts.txt", layouts)
    extra_symbol = "voiage_v1_capability_probe"
    header_text = header.read_text(encoding="utf-8")
    header.write_text(
        header_text.replace(
            '#ifdef __cplusplus\n} /* extern "C" */',
            f'# VOIAGE additive fixture\nVOIAGE_V1_API int {extra_symbol}(void);\n\n#ifdef __cplusplus\n}} /* extern "C" */',
        ),
        encoding="utf-8",
    )
    symbols.write_text(
        symbols.read_text(encoding="utf-8") + f"{extra_symbol}\n",
        encoding="utf-8",
    )
    result = compare(ABI_RELEASE, header, symbols, layouts)
    assert result["compatible"] is True
    assert extra_symbol in result["additive_symbols"]
