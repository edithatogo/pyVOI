"""Generate FPGA/ASIC pre-silicon evidence manifests."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable

ROOT = Path(__file__).resolve().parents[1]
HARDWARE_ROOT = ROOT / "hardware" / "pre_silicon"
FIXTURE_PATH = HARDWARE_ROOT / "fixtures" / "evpi_fixed_point_fixture.json"
RTL_PATH = HARDWARE_ROOT / "rtl" / "evpi_fixed_point_kernel.v"
TB_PATH = HARDWARE_ROOT / "tb" / "evpi_fixed_point_kernel_tb.v"


@dataclass(frozen=True)
class EvidenceCommand:
    """A command that can contribute to a pre-silicon evidence packet."""

    name: str
    required_tools: tuple[str, ...]
    argv: tuple[str, ...]
    output_artifacts: tuple[str, ...]
    log_path: str
    required_artifacts: tuple[str, ...] = ()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _command_path(path: Path) -> str:
    if not path.is_absolute():
        return path.as_posix()
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _tool_version(tool: str) -> dict[str, Any]:
    executable = shutil.which(tool)
    version_command = [tool, "--version"]
    if executable is None:
        return {
            "name": tool,
            "available": False,
            "version": None,
            "version_command": version_command,
        }
    try:
        result = subprocess.run(  # noqa: S603 - version command is a fixed argv list.
            version_command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "name": tool,
            "available": True,
            "version": None,
            "version_command": version_command,
            "version_error": str(exc),
        }
    output = (result.stdout or result.stderr).strip().splitlines()
    return {
        "name": tool,
        "available": True,
        "version": output[0] if output else None,
        "version_command": version_command,
    }


def _output_arg(output_root: Path, artifact: str) -> str:
    return _command_path(output_root / artifact)


def _verilator_commands(target: str, output_root: Path) -> tuple[EvidenceCommand, ...]:
    rtl = str(RTL_PATH.relative_to(ROOT))
    tb = str(TB_PATH.relative_to(ROOT))
    binary_artifact = f"artifacts/{target}/verilator_obj/Vevpi_fixed_point_kernel_tb"
    return (
        EvidenceCommand(
            name="verilator_lint",
            required_tools=("verilator",),
            argv=("verilator", "--lint-only", rtl, tb),
            output_artifacts=(f"reports/{target}/verilator_lint.log",),
            log_path=f"reports/{target}/verilator_lint.log",
        ),
        EvidenceCommand(
            name="verilator_testbench_simulation_build",
            required_tools=("verilator",),
            argv=(
                "verilator",
                "--binary",
                "--timing",
                "--top-module",
                "evpi_fixed_point_kernel_tb",
                "--Mdir",
                _output_arg(output_root, f"artifacts/{target}/verilator_obj"),
                rtl,
                tb,
            ),
            output_artifacts=(
                binary_artifact,
                f"reports/{target}/verilator_testbench_build.log",
            ),
            log_path=f"reports/{target}/verilator_testbench_build.log",
        ),
        EvidenceCommand(
            name="verilator_testbench_simulation_run",
            required_tools=(),
            argv=(_output_arg(output_root, binary_artifact),),
            output_artifacts=(f"reports/{target}/verilator_testbench_run.log",),
            log_path=f"reports/{target}/verilator_testbench_run.log",
            required_artifacts=(binary_artifact,),
        ),
    )


def _command_catalog(target: str, output_root: Path) -> tuple[EvidenceCommand, ...]:
    rtl = str(RTL_PATH.relative_to(ROOT))
    if target == "fpga":
        return (
            *_verilator_commands(target, output_root),
            EvidenceCommand(
                name="yosys_synth_ice40_json",
                required_tools=("yosys",),
                argv=(
                    "yosys",
                    "-p",
                    "read_verilog "
                    f"{rtl}; synth_ice40 -top evpi_fixed_point_kernel "
                    "-json "
                    f"{_output_arg(output_root, 'artifacts/fpga/evpi_fixed_point_ice40.json')}; "
                    "stat",
                ),
                output_artifacts=(
                    "artifacts/fpga/evpi_fixed_point_ice40.json",
                    "reports/fpga/yosys_synth_ice40.log",
                ),
                log_path="reports/fpga/yosys_synth_ice40.log",
            ),
            EvidenceCommand(
                name="nextpnr_ice40_place_route",
                required_tools=("nextpnr-ice40",),
                argv=(
                    "nextpnr-ice40",
                    "--up5k",
                    "--package",
                    "sg48",
                    "--json",
                    _output_arg(
                        output_root, "artifacts/fpga/evpi_fixed_point_ice40.json"
                    ),
                    "--asc",
                    _output_arg(
                        output_root, "artifacts/fpga/evpi_fixed_point_ice40.asc"
                    ),
                ),
                output_artifacts=(
                    "artifacts/fpga/evpi_fixed_point_ice40.asc",
                    "reports/fpga/nextpnr_ice40.log",
                ),
                log_path="reports/fpga/nextpnr_ice40.log",
            ),
        )
    if target == "asic":
        return (
            *_verilator_commands(target, output_root),
            EvidenceCommand(
                name="yosys_synth_asic_netlist",
                required_tools=("yosys",),
                argv=(
                    "yosys",
                    "-p",
                    "read_verilog "
                    f"{rtl}; synth -top evpi_fixed_point_kernel; "
                    "write_verilog "
                    f"{_output_arg(output_root, 'artifacts/asic/evpi_fixed_point_netlist.v')}; "
                    "stat",
                ),
                output_artifacts=(
                    "artifacts/asic/evpi_fixed_point_netlist.v",
                    "reports/asic/yosys_synth_asic.log",
                ),
                log_path="reports/asic/yosys_synth_asic.log",
            ),
            EvidenceCommand(
                name="openroad_openlane_sky130_rtl_to_gds",
                required_tools=("openroad",),
                argv=("openroad", "-version"),
                output_artifacts=(
                    "artifacts/asic/evpi_fixed_point.gds",
                    "artifacts/asic/evpi_fixed_point.def",
                    "reports/asic/openlane_floorplan.log",
                    "reports/asic/openlane_place.log",
                    "reports/asic/openlane_route.log",
                    "reports/asic/openroad_timing.rpt",
                    "reports/asic/openroad_area.rpt",
                    "reports/asic/openroad_openlane_sky130.log",
                ),
                log_path="reports/asic/openroad_openlane_sky130.log",
            ),
        )
    raise ValueError(f"Unknown pre-silicon target: {target}")


def _target_metadata(target: str) -> dict[str, Any]:
    if target == "fpga":
        return {
            "track": "fpga-implementation_20260511",
            "free_runner_order": [
                "GitHub Actions with YosysHQ/setup-oss-cad-suite",
                "GitHub Codespaces",
                "Google Cloud Shell",
            ],
            "physical_gate": "Physical FPGA board runtime remains future external evidence.",
        }
    if target == "asic":
        return {
            "track": "asic-implementation_20260511",
            "free_runner_order": [
                "GitHub Actions Docker flow with OpenROAD/OpenLane/SKY130",
                "GitHub Codespaces",
                "Google Cloud Shell",
            ],
            "physical_gate": (
                "Tiny Tapeout or SkyWater MPW fabricated-silicon evidence remains "
                "future external evidence; use Chrome only for explicit signup or "
                "portal handoff."
            ),
        }
    raise ValueError(f"Unknown pre-silicon target: {target}")


def _load_fixture_summary() -> dict[str, Any]:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return {
        "path": str(FIXTURE_PATH.relative_to(ROOT)),
        "sha256": _sha256(FIXTURE_PATH),
        "kernel": fixture["kernel"],
        "scale": fixture["scale"],
        "case_count": len(fixture["cases"]),
    }


def _source_hashes() -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)): _sha256(path)
        for path in (RTL_PATH, TB_PATH, FIXTURE_PATH)
    }


def _run_command(command: EvidenceCommand, output_root: Path) -> dict[str, Any]:
    missing = [tool for tool in command.required_tools if shutil.which(tool) is None]
    missing_inputs = [
        artifact
        for artifact in command.required_artifacts
        if not (output_root / artifact).exists()
    ]
    log_path = output_root / command.log_path
    log_path.parent.mkdir(parents=True, exist_ok=True)
    for artifact in command.output_artifacts:
        (output_root / artifact).parent.mkdir(parents=True, exist_ok=True)
    if missing:
        log_path.write_text(
            f"Skipped because required tool(s) are missing: {', '.join(missing)}\n",
            encoding="utf-8",
        )
        return {
            "name": command.name,
            "status": "tool_missing",
            "required_tools": list(command.required_tools),
            "missing_tools": missing,
            "argv": list(command.argv),
            "returncode": None,
            "log_path": command.log_path,
            "output_artifacts": list(command.output_artifacts),
            "missing_artifacts": [],
        }
    if missing_inputs:
        log_path.write_text(
            "Skipped because required input artifact(s) are missing: "
            f"{', '.join(missing_inputs)}\n",
            encoding="utf-8",
        )
        return {
            "name": command.name,
            "status": "input_missing",
            "required_tools": list(command.required_tools),
            "missing_tools": [],
            "argv": list(command.argv),
            "returncode": None,
            "log_path": command.log_path,
            "output_artifacts": list(command.output_artifacts),
            "missing_artifacts": missing_inputs,
        }

    try:
        result = subprocess.run(  # noqa: S603 - command argv comes from the fixed catalog.
            list(command.argv),
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
        log_path.write_text(result.stdout + result.stderr, encoding="utf-8")
    except (OSError, subprocess.TimeoutExpired) as exc:
        log_path.write_text(str(exc), encoding="utf-8")
        return {
            "name": command.name,
            "status": "failed",
            "required_tools": list(command.required_tools),
            "missing_tools": [],
            "argv": list(command.argv),
            "returncode": None,
            "log_path": command.log_path,
            "output_artifacts": list(command.output_artifacts),
            "missing_artifacts": [],
        }
    missing_outputs = [
        artifact
        for artifact in command.output_artifacts
        if not (output_root / artifact).exists()
    ]
    if result.returncode != 0:
        status = "failed"
    elif missing_outputs:
        status = "artifact_missing"
    else:
        status = "passed"
    return {
        "name": command.name,
        "status": status,
        "required_tools": list(command.required_tools),
        "missing_tools": [],
        "argv": list(command.argv),
        "returncode": result.returncode,
        "log_path": command.log_path,
        "output_artifacts": list(command.output_artifacts),
        "missing_artifacts": missing_outputs,
    }


def _probe_command(command: EvidenceCommand, output_root: Path) -> dict[str, Any]:
    return {
        "name": command.name,
        "status": "not_run_probe",
        "required_tools": list(command.required_tools),
        "missing_tools": [
            tool for tool in command.required_tools if shutil.which(tool) is None
        ],
        "missing_artifacts": [
            artifact
            for artifact in command.required_artifacts
            if not (output_root / artifact).exists()
        ],
        "argv": list(command.argv),
        "returncode": None,
        "log_path": command.log_path,
        "output_artifacts": list(command.output_artifacts),
    }


def build_manifest(target: str, output_root: Path, probe_only: bool) -> dict[str, Any]:
    """Build one pre-silicon evidence manifest."""
    commands = _command_catalog(target, output_root)
    tool_names = sorted(
        {tool for command in commands for tool in command.required_tools}
    )
    metadata = _target_metadata(target)
    command_results = [
        _probe_command(command, output_root)
        if probe_only
        else _run_command(command, output_root)
        for command in commands
    ]
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "track": metadata["track"],
        "target": target,
        "evidence_kind": "ci_pre_silicon",
        "claim_boundary": (
            "Pre-silicon simulation/synthesis evidence only; no physical runtime "
            "or production accelerator speedup claim."
        ),
        "free_runner_order": metadata["free_runner_order"],
        "physical_gate": metadata["physical_gate"],
        "input_fixture": _load_fixture_summary(),
        "source_files": _source_hashes(),
        "tools": [_tool_version(tool) for tool in tool_names],
        "commands": command_results,
    }


def write_manifest(
    target: str,
    output_root: Path,
    probe_only: bool,
    *,
    nested: bool,
) -> Path:
    """Write a target manifest and return its path."""
    target_root = output_root / target if nested else output_root
    target_root.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(target, target_root, probe_only=probe_only)
    manifest_path = target_root / "pre_silicon_evidence_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def _targets(selection: str) -> Iterable[str]:
    if selection == "all":
        return ("fpga", "asic")
    return (selection,)


def main(argv: list[str] | None = None) -> int:
    """Run the pre-silicon evidence manifest CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=("fpga", "asic", "all"))
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "hardware" / "pre_silicon" / "evidence",
        help="Directory where target evidence manifests and logs are written.",
    )
    parser.add_argument(
        "--probe-only",
        action="store_true",
        help="Do not execute EDA commands; only record command and tool availability.",
    )
    parser.add_argument(
        "--require-tools",
        action="store_true",
        help="Return non-zero when any command is skipped or fails.",
    )
    args = parser.parse_args(argv)

    targets = tuple(_targets(args.target))
    manifest_paths = [
        write_manifest(
            target,
            args.output_root,
            probe_only=args.probe_only,
            nested=len(targets) > 1,
        )
        for target in targets
    ]
    for path in manifest_paths:
        print(path)

    if args.require_tools:
        failed_statuses = {
            "artifact_missing",
            "failed",
            "input_missing",
            "not_run_probe",
            "tool_missing",
        }
        for path in manifest_paths:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            if any(
                command["status"] in failed_statuses for command in manifest["commands"]
            ):
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
