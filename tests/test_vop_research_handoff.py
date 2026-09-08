"""Fail-closed tests for the two-environment research-use replay."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
import zipfile

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "vop_handoff", ROOT / "scripts/run_vop_research_handoff.py"
)
assert SPEC
assert SPEC.loader
handoff = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(handoff)


def _packet(
    tmp_path: Path, csv_text: str = "standard_care,hpv_vaccination\n0,10\n10,0\n"
) -> tuple[Path, str]:
    draws = tmp_path / "hpv_vaccination_net_benefit.csv"
    draws.write_text(csv_text, encoding="utf-8")
    receipt = tmp_path / "export.json"
    receipt.write_text(
        json.dumps(
            {
                "schema_version": handoff.EXPORT_SCHEMA,
                "source_revision": handoff.VOP_REVISION,
                "source_parameter_sha256": handoff.PARAMETER_SHA256,
                "draws": 2,
                "seed": 20260727,
                "willingness_to_pay_nzd_per_qaly": 50000.0,
                "net_benefit_csv_sha256": hashlib.sha256(
                    draws.read_bytes()
                ).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    return receipt, hashlib.sha256(receipt.read_bytes()).hexdigest()


def test_load_handoff_binds_receipt_and_csv(tmp_path: Path) -> None:
    receipt, digest = _packet(tmp_path)
    matrix, record = handoff.load_handoff(receipt, digest)
    np.testing.assert_array_equal(matrix, [[0, 10], [10, 0]])
    assert record["draws"] == 2


def test_ac5_writes_redacted_synthetic_replay_packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run the real export/evaluate workflow and retain bounded metadata."""
    import voiage

    parameter_path = tmp_path / "src/vop_poc_nz/parameters.yaml"
    parameter_path.parent.mkdir(parents=True)
    parameter_path.write_text("pinned test fixture", encoding="utf-8")
    monkeypatch.setattr(
        handoff, "PARAMETER_SHA256", hashlib.sha256(parameter_path.read_bytes()).hexdigest()
    )
    monkeypatch.setattr(handoff.shutil, "which", lambda name: "/usr/bin/git")
    monkeypatch.setattr(
        handoff.subprocess,
        "check_output",
        lambda *args, **kwargs: handoff.VOP_REVISION
        if args[0][-1] == "HEAD"
        else "",
    )
    core = types.ModuleType("vop_poc_nz.cea_model_core")
    analysis = types.ModuleType("vop_poc_nz.pipeline.analysis")
    monkeypatch.setattr(core, "run_cea", lambda: None, raising=False)
    monkeypatch.setattr(
        analysis,
        "load_parameters",
        lambda path: {"hpv_vaccination": {}},
        raising=False,
    )
    monkeypatch.setitem(sys.modules, core.__name__, core)
    monkeypatch.setitem(sys.modules, analysis.__name__, analysis)
    monkeypatch.setattr(
        handoff, "generate_draws", lambda *args, **kwargs: np.array([[0, 10], [10, 0]])
    )
    export_dir = tmp_path / "export"
    handoff.export(tmp_path, export_dir, draws=2, seed=7)
    receipt = export_dir / "export.json"
    receipt_sha256 = hashlib.sha256(receipt.read_bytes()).hexdigest()
    monkeypatch.setattr(
        handoff,
        "verify_installed_wheel",
        lambda wheel: {"module_path": str(Path(sys.prefix) / "lib/voiage/__init__.py")},
    )
    monkeypatch.setattr(voiage, "__version__", "2.2.0")
    monkeypatch.setattr(
        voiage, "__file__", str(Path(sys.prefix) / "lib/voiage/__init__.py")
    )
    evaluation = tmp_path / "evaluation.json"
    handoff.evaluate(receipt, receipt_sha256, evaluation, wheel=tmp_path / "public.whl")
    evaluated = json.loads(evaluation.read_text())
    csv_path = export_dir / handoff.CSV_NAME
    packet = {
        "schema_version": "1.0.0",
        "data_policy": "synthetic-only; local validation packet",
        "voiage_version": evaluated["voiage_version"],
        "source_revision": handoff.VOP_REVISION,
        "export_receipt_sha256": receipt_sha256,
        "net_benefit_csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "expected_voi": evaluated["evpi_nzd_per_cohort"],
        "limitations": ["two synthetic draws", "no hosted publication or release"],
    }
    output = tmp_path / "redacted-validation-packet.json"
    output.write_text(json.dumps(packet, sort_keys=True), encoding="utf-8")
    retained = json.loads(output.read_text(encoding="utf-8"))
    assert retained["data_policy"].startswith("synthetic-only")
    assert retained["expected_voi"] == 5.0
    assert (
        retained["net_benefit_csv_sha256"]
        == hashlib.sha256(csv_path.read_bytes()).hexdigest()
    )
    assert "standard_care" not in output.read_text(encoding="utf-8")


def test_retained_replay_preserves_history_and_binds_both_environments() -> None:
    historical = json.loads(
        (ROOT / "paper/joss-developer-research-use.json").read_text()
    )
    assert historical["published_package"]["version"] == "2.0.0"
    replay = historical["computational_refresh"]
    assert replay["version"] == "2.2.0"
    for field in ("script", "export_receipt", "evaluation_receipt"):
        assert (
            hashlib.sha256((ROOT / replay[field]).read_bytes()).hexdigest()
            == replay[field + "_sha256"]
        )
    exported = json.loads((ROOT / replay["export_receipt"]).read_text())
    evaluated = json.loads((ROOT / replay["evaluation_receipt"]).read_text())
    assert evaluated["export_receipt_sha256"] == replay["export_receipt_sha256"]
    assert evaluated["net_benefit_csv_sha256"] == exported["net_benefit_csv_sha256"]
    assert (
        evaluated["net_benefit_csv_sha256"]
        == historical["analysis"]["net_benefit_csv_sha256"]
    )
    assert (
        evaluated["evpi_nzd_per_cohort"]
        == evaluated["numpy_reference_evpi_nzd_per_cohort"]
        == 0.0
    )
    assert "voiage" not in exported["environment"]["distributions"]
    assert "vop_poc_nz" not in evaluated["environment"]["distributions"]
    assert exported["environment"]["distributions"]["pandas"] == "3.0.3"
    assert evaluated["environment"]["distributions"]["pandas"] == "2.3.3"
    matrix, _ = handoff.load_handoff(
        ROOT / replay["export_receipt"], replay["export_receipt_sha256"]
    )
    assert matrix.shape == (500, 2)
    assert (
        evaluated["public_wheel_verification"]["wheel_sha256"]
        in handoff.PUBLIC_WHEEL_SHA256
    )


@pytest.mark.parametrize("target", ["receipt", "csv"])
def test_load_handoff_rejects_modified_bytes(tmp_path: Path, target: str) -> None:
    receipt, digest = _packet(tmp_path)
    path = (
        receipt if target == "receipt" else tmp_path / "hpv_vaccination_net_benefit.csv"
    )
    path.write_text(path.read_text() + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256"):
        handoff.load_handoff(receipt, digest)


@pytest.mark.parametrize(
    "csv_text",
    [
        "hpv_vaccination,standard_care\n0,10\n10,0\n",
        "standard_care,hpv_vaccination\n0,10\n",
        "standard_care,hpv_vaccination\n0,10,1\n10,0,1\n",
        "standard_care,hpv_vaccination\n0,nan\n10,0\n",
        "standard_care,hpv_vaccination\n0,inf\n10,0\n",
        "standard_care,hpv_vaccination\n0,ten\n10,0\n",
    ],
)
def test_load_handoff_rejects_invalid_matrix(tmp_path: Path, csv_text: str) -> None:
    receipt, digest = _packet(tmp_path, csv_text)
    with pytest.raises(ValueError):
        handoff.load_handoff(receipt, digest)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("schema_version", "unknown"),
        ("source_revision", "0" * 40),
        ("source_parameter_sha256", "0" * 64),
        ("draws", 1),
        ("draws", True),
        ("seed", True),
        ("willingness_to_pay_nzd_per_qaly", 0),
    ],
)
def test_load_handoff_rejects_wrong_contract(
    tmp_path: Path, key: str, value: object
) -> None:
    receipt, _ = _packet(tmp_path)
    record = json.loads(receipt.read_text())
    record[key] = value
    receipt.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError):
        handoff.load_handoff(receipt, hashlib.sha256(receipt.read_bytes()).hexdigest())


def test_replay_is_deterministic_and_does_not_mutate_parameters() -> None:
    params = {
        "costs": {"health_system": {"new_treatment": [2.0], "standard_care": [1.0]}},
        "qalys": {"new_treatment": [2.0], "standard_care": [1.0]},
    }
    before = json.dumps(params, sort_keys=True)

    def run_cea(draw: dict, *, perspective: str) -> dict[str, float]:
        assert perspective == "health_system"
        return {
            "qalys_standard_care": draw["qalys"]["standard_care"][0],
            "qalys_new_treatment": draw["qalys"]["new_treatment"][0],
            "cost_standard_care": draw["costs"][perspective]["standard_care"][0],
            "cost_new_treatment": draw["costs"][perspective]["new_treatment"][0],
        }

    first = handoff.generate_draws(params, run_cea, draws=3, seed=7)
    np.testing.assert_array_equal(
        first, handoff.generate_draws(params, run_cea, draws=3, seed=7)
    )
    assert json.dumps(params, sort_keys=True) == before
    with pytest.raises(ValueError, match="draws"):
        handoff.generate_draws(params, run_cea, draws=1, seed=7)


def test_receipt_output_never_overwrites_existing_evidence(tmp_path: Path) -> None:
    output = tmp_path / "receipt.json"
    handoff.write_receipt(output, {"one": 1})
    with pytest.raises(FileExistsError):
        handoff.write_receipt(output, {"two": 2})
    assert json.loads(output.read_text()) == {"one": 1}


@pytest.mark.parametrize("invalid", [None, "version", "checkout", "calculation"])
def test_evaluate_installed_boundary_and_reference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, invalid: str | None
) -> None:
    import voiage
    import voiage.methods.basic

    receipt, digest = _packet(tmp_path)
    monkeypatch.setattr(
        handoff,
        "verify_installed_wheel",
        lambda wheel: {"module_path": str(Path(sys.prefix) / "lib/voiage/__init__.py")},
    )
    monkeypatch.setattr(
        voiage, "__version__", "2.0.0" if invalid == "version" else "2.2.0"
    )
    monkeypatch.setattr(
        voiage,
        "__file__",
        str(tmp_path / "__init__.py")
        if invalid == "checkout"
        else str(Path(sys.prefix) / "lib/voiage/__init__.py"),
    )
    if invalid == "calculation":
        monkeypatch.setattr(voiage.methods.basic, "evpi", lambda matrix: 999.0)
    output = tmp_path / "evaluation.json"
    if invalid:
        with pytest.raises(ValueError):
            handoff.evaluate(receipt, digest, output, wheel=tmp_path / "public.whl")
        assert not output.exists()
    else:
        handoff.evaluate(receipt, digest, output, wheel=tmp_path / "public.whl")
        result = json.loads(output.read_text())
        assert result["evpi_nzd_per_cohort"] == 5.0
        assert result["numpy_reference_evpi_nzd_per_cohort"] == 5.0
        assert result["export_receipt_sha256"] == digest


@pytest.mark.parametrize("invalid", [None, "git", "revision", "dirty", "parameters"])
def test_export_checks_source_before_importing_vop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, invalid: str | None
) -> None:
    parameter_path = tmp_path / "src/vop_poc_nz/parameters.yaml"
    parameter_path.parent.mkdir(parents=True)
    parameter_path.write_text("pinned test fixture", encoding="utf-8")
    monkeypatch.setattr(
        handoff,
        "PARAMETER_SHA256",
        hashlib.sha256(parameter_path.read_bytes()).hexdigest(),
    )
    monkeypatch.setattr(
        handoff.shutil,
        "which",
        lambda name: None if invalid == "git" else "/usr/bin/git",
    )
    responses = iter(
        [
            "0" * 40 if invalid == "revision" else handoff.VOP_REVISION,
            "M file" if invalid == "dirty" else "",
        ]
    )
    monkeypatch.setattr(
        handoff.subprocess, "check_output", lambda *args, **kwargs: next(responses)
    )
    if invalid == "parameters":
        parameter_path.write_text("modified", encoding="utf-8")
    core = types.ModuleType("vop_poc_nz.cea_model_core")
    analysis = types.ModuleType("vop_poc_nz.pipeline.analysis")
    monkeypatch.setattr(core, "run_cea", lambda: None, raising=False)
    monkeypatch.setattr(
        analysis, "load_parameters", lambda path: {"hpv_vaccination": {}}, raising=False
    )
    monkeypatch.setitem(sys.modules, core.__name__, core)
    monkeypatch.setitem(sys.modules, analysis.__name__, analysis)
    monkeypatch.setattr(
        handoff, "generate_draws", lambda *args, **kwargs: np.array([[0, 10], [10, 0]])
    )
    monkeypatch.setattr(sys, "path", list(sys.path))
    output = tmp_path / "export"
    if invalid:
        with pytest.raises((ValueError, RuntimeError)):
            handoff.export(tmp_path, output, draws=2, seed=7)
        assert not output.exists()
    else:
        handoff.export(tmp_path, output, draws=2, seed=7)
        receipt = output / "export.json"
        matrix, _ = handoff.load_handoff(
            receipt, hashlib.sha256(receipt.read_bytes()).hexdigest()
        )
        np.testing.assert_array_equal(matrix, [[0, 10], [10, 0]])


@pytest.mark.parametrize("mode", ["export", "evaluate"])
def test_cli_dispatches_only_one_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        handoff, "export", lambda *args, **kwargs: calls.append("export")
    )
    monkeypatch.setattr(
        handoff, "evaluate", lambda *args, **kwargs: calls.append("evaluate")
    )
    args = (
        ["--vop-root", str(tmp_path / "vop")]
        if mode == "export"
        else [
            "--export-receipt",
            str(tmp_path / "export.json"),
            "--export-sha256",
            "0" * 64,
            "--wheel",
            str(tmp_path / "public.whl"),
        ]
    )
    monkeypatch.setattr(
        sys, "argv", ["handoff", mode, *args, "--output", str(tmp_path / "new-output")]
    )
    handoff.main()
    assert calls == [mode]


@pytest.mark.parametrize(
    "mutation", [None, "wheel", "modified", "missing", "extra", "version", "prefix"]
)
def test_public_wheel_verification_rejects_unreviewed_installed_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str | None
) -> None:
    root = tmp_path / "env/site-packages"
    package = root / "voiage"
    package.mkdir(parents=True)
    module = package / "__init__.py"
    module.write_bytes(b"public fixture code")
    wheel = tmp_path / "public.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("voiage/__init__.py", module.read_bytes())
        archive.writestr("voiage-2.2.0.dist-info/RECORD", b"installer-managed")
    monkeypatch.setattr(
        handoff, "PUBLIC_WHEEL_SHA256", {handoff.sha256(wheel.read_bytes())}
    )
    monkeypatch.setattr(
        sys, "prefix", str(tmp_path / "other" if mutation == "prefix" else tmp_path)
    )
    distribution = types.SimpleNamespace(
        version="2.0.0" if mutation == "version" else "2.2.0",
        locate_file=lambda name: root / name,
    )
    monkeypatch.setattr(
        handoff.importlib.metadata, "distribution", lambda name: distribution
    )
    if mutation == "wheel":
        wheel.write_bytes(wheel.read_bytes() + b"altered")
    elif mutation == "modified":
        module.write_bytes(b"unreviewed local build")
    elif mutation == "missing":
        module.unlink()
    elif mutation == "extra":
        (package / "extra.py").write_bytes(b"unreviewed")
    if mutation:
        with pytest.raises(ValueError):
            handoff.verify_installed_wheel(wheel)
    else:
        result = handoff.verify_installed_wheel(wheel)
        assert result["installed_files_verified"] == 1
        assert result["wheel_sha256"] == handoff.sha256(wheel.read_bytes())


def test_wheel_identity_failure_cannot_issue_an_evaluation_receipt(
    tmp_path: Path,
) -> None:
    receipt, digest = _packet(tmp_path)
    wheel = tmp_path / "unreviewed.whl"
    wheel.write_bytes(b"not a public wheel")
    output = tmp_path / "evaluation.json"
    with pytest.raises(ValueError, match="reviewed public"):
        handoff.evaluate(receipt, digest, output, wheel=wheel)
    assert not output.exists()
