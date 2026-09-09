"""Executable inventory for the pre-submission structure/API/ABI audit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import voiage

ROOT = Path(__file__).parents[1]
AUDIT_PATH = (
    ROOT / "specs" / "submission-readiness" / "structure-api-abi-audit-20260829.json"
)
DELTA_PATH = ROOT / "specs/submission-readiness/structure-inventory-delta-20260901.json"


def _read(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_current_membership(actual: set[str], *, root: Path = ROOT) -> None:
    """Keep the dated count separate from the later observed full membership."""
    audit_path = root / AUDIT_PATH.relative_to(ROOT)
    delta = json.loads((root / DELTA_PATH.relative_to(ROOT)).read_text())
    historical = delta["historical_audit"]
    assert historical["path"] == AUDIT_PATH.relative_to(ROOT).as_posix()
    assert hashlib.sha256(audit_path.read_bytes()).hexdigest() == historical["sha256"]
    audit = json.loads(audit_path.read_text())
    baseline = delta["verified_baseline"]
    assert baseline["commit"] == "1c66be00142a0434dc694073c55a2e2988de4b40"
    modules = baseline["python_modules"]
    assert modules == sorted(set(modules))
    assert (
        hashlib.sha256(json.dumps(modules, separators=(",", ":")).encode()).hexdigest()
        == baseline["python_modules_sha256"]
    )
    assert (
        len(modules)
        == historical["python_runtime_modules"]
        == audit["inventory"]["python_runtime_modules"]
        == 176
    )
    additions = delta["additions"]
    assert additions == [
        "voiage/contracts/capability_report.py",
        "voiage/sampling_harm_agent_assurance.py",
    ]
    assert delta["removals"] == []
    assert set(modules).isdisjoint(additions)
    assert actual == set(modules) | set(additions)
    assert len(actual) == delta["current_python_runtime_modules"] == 178


def test_structure_inventory_matches_current_sources() -> None:
    audit = _read(AUDIT_PATH)
    stable_api = _read(ROOT / "specs/v2/stable-api.json")
    assert isinstance(audit, dict)
    assert isinstance(stable_api, dict)
    inventory = audit["inventory"]

    _validate_current_membership(
        {path.relative_to(ROOT).as_posix() for path in (ROOT / "voiage").rglob("*.py")}
    )
    assert inventory["rust_workspace_crates"] == len(
        list((ROOT / "rust/crates").glob("*/Cargo.toml"))
    )
    stable_symbols = stable_api["symbols"]["stable"]
    assert inventory["stable_python_symbols"] == len(stable_symbols)
    assert all(hasattr(voiage, symbol) for symbol in stable_symbols)
    assert inventory["c_abi_symbols"] == len(
        [
            line
            for line in (ROOT / "specs/abi/v1/symbols.txt")
            .read_text(encoding="utf-8")
            .splitlines()
            if line and not line.startswith("#")
        ]
    )
    assert inventory["tracked_stale_r_source_archives"] == int(
        (ROOT / "r-package/voiageR/voiageR_0.1.0.tar.gz").is_file()
    )


def test_structure_findings_record_resolutions_and_external_gate() -> None:
    audit = _read(AUDIT_PATH)
    assert isinstance(audit, dict)
    findings = audit["findings"]
    by_id = {finding["id"]: finding for finding in findings}

    assert set(by_id) == {f"STRUCT-{number:03d}" for number in range(1, 8)}
    assert by_id["STRUCT-001"]["severity"] == "critical"
    assert by_id["STRUCT-003"]["state"] == "external_gate"
    assert {
        by_id[f"STRUCT-{number:03d}"]["state"] for number in (1, 2, 4, 5, 6, 7)
    } == {"resolved"}
    assert all(finding["evidence"] for finding in findings)
    assert all(finding["required_disposition"] for finding in findings)
    assert all(finding["resolution"] for finding in findings)


@pytest.mark.parametrize(
    "mutation", ["remove", "unregistered_addition", "same_count_replacement"]
)
def test_structure_delta_rejects_unrecorded_membership_changes(mutation: str) -> None:
    actual = {
        path.relative_to(ROOT).as_posix() for path in (ROOT / "voiage").rglob("*.py")
    }
    if mutation in {"remove", "same_count_replacement"}:
        actual.remove("voiage/scientific_review_evidence.py")
    if mutation in {"unregistered_addition", "same_count_replacement"}:
        actual.add("voiage/unregistered_verifier.py")
    with pytest.raises(AssertionError):
        _validate_current_membership(actual)


def test_structure_delta_rejects_changed_historical_bytes(tmp_path: Path) -> None:
    for source in (AUDIT_PATH, DELTA_PATH):
        target = tmp_path / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    historical = tmp_path / AUDIT_PATH.relative_to(ROOT)
    historical.write_bytes(historical.read_bytes() + b"\n")
    actual = {
        path.relative_to(ROOT).as_posix() for path in (ROOT / "voiage").rglob("*.py")
    }
    with pytest.raises(AssertionError):
        _validate_current_membership(actual, root=tmp_path)
