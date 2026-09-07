"""Fail-closed repository quality and GitHub Actions harness checks."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ACTION_PATTERN = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.MULTILINE)
SHA_PATTERN = re.compile(r"@[0-9a-f]{40}$")
WORKFLOW_SUFFIXES = (".yml", ".yaml")
REQUIRED_UV_VERSION = "0.12.5"
REQUIRED_FILES = (
    "AGENTS.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "pyproject.toml",
    "tox.ini",
    ".github/CODEOWNERS",
    ".github/PULL_REQUEST_TEMPLATE/default.md",
    ".pre-commit-config.yaml",
    "renovate.json",
    "roadmap.md",
    "todo.md",
    "changelog.md",
)
REQUIRED_WORKFLOWS = (
    "ci.yml",
    "codeql.yml",
    "dependency-review.yml",
    "gitleaks.yml",
    "operational-assurance.yml",
    "rust-fuzz.yml",
    "rust-security.yml",
    "sbom.yml",
    "scorecard.yml",
    "zizmor.yml",
)
REQUIRED_CONTEXT_MARKERS = (
    "## Context Loading Order",
    "## Repository Context Map",
    "## Solo-Maintainer Merge Policy",
)
CONTRACT_GOVERNANCE_MARKERS = {
    "pyproject.toml": (
        'contracts = "uv run nox -s contracts"',
        'contracts-profile = "uv run nox -s contract_profile"',
        'contracts-mutation = "uv run nox -s contract_mutation"',
        '"voiage/contracts/capabilities.py"',
        '"voiage/contracts/digests.py"',
    ),
    "noxfile.py": (
        "def contracts(",
        "def contract_profile(",
        "def contract_mutation(",
    ),
    "pixi.toml": (
        "contracts =",
        "contracts-profile =",
        "contracts-mutation =",
        "mutation-score =",
    ),
    ".github/workflows/ci.yml": (
        "scripts/export_v2_contracts.py --check",
        "tests/test_contract_automation.py",
        "tests/test_contract_interchange.py",
        "tests/test_vop_governance_mirror.py",
        "scripts/profile_contracts.py",
        "mutmut export-cicd-stats",
        "--baseline-stats .github/mutation-baselines/voiage-broad.json",
        "mutation-score-broad.json",
        "scripts/run_critical_mutation_lane.py . --threshold 90",
    ),
}
OPERATIONAL_ASSURANCE_MARKERS = {
    ".github/workflows/operational-assurance.yml": (
        "scripts/check_consumer_matrix.py",
        "scripts/check_coverage_policy.py",
        "--cov-fail-under=90",
        "f05231ce21a81ffb4029493927e5572d114fad67",
        "include-hidden-files: true",
        "if-no-files-found: error",
    ),
    ".github/workflows/ci.yml": (
        "scripts/check_mutation_cohort.py",
        ".github/mutation-baselines/voiage-cohort.json",
        "mutation-cohort.json",
        "VOIAGE_MUTATION_BASELINE_SHA256",
        "mutmut-universe.txt",
    ),
    ".github/mutation-baselines/README.md": (
        "VOIAGE_MUTATION_BASELINE_SHA256",
        "Do not add an approval Boolean",
        "fails closed",
    ),
    ".github/coverage-policy.json": (
        '"aggregate_percent": 90.0',
        '"changed_branch_percent": 100.0',
    ),
}
EXPECTED_COVERAGE_POLICY = {
    "schema_version": "1.0.0",
    "aggregate_percent": 90.0,
    "critical_modules": {
        "voiage/assurance_policy.py": 100.0,
        "voiage/contracts/bundle.py": 90.0,
        "voiage/mutation_policy.py": 95.0,
    },
    "changed_line_percent": 95.0,
    "changed_branch_percent": 100.0,
}


@dataclass(frozen=True)
class Finding:
    """One harness finding suitable for both humans and CI."""

    path: str
    message: str


def workflow_files(root: Path) -> list[Path]:
    """Return tracked workflow files in stable order."""
    workflow_root = root / ".github" / "workflows"
    return sorted(
        path
        for path in workflow_root.iterdir()
        if path.is_file() and path.suffix in WORKFLOW_SUFFIXES
    )


def check_required_files(root: Path) -> list[Finding]:
    """Check the repository-owned governance and build surfaces."""
    return [
        Finding(relative_path, "required file is missing")
        for relative_path in REQUIRED_FILES
        if not (root / relative_path).is_file()
    ]


def check_context_contract(root: Path) -> list[Finding]:
    """Ensure agent-facing repository context remains explicit and discoverable."""
    path = root / "AGENTS.md"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    return [
        Finding("AGENTS.md", f"required context section is missing: {marker}")
        for marker in REQUIRED_CONTEXT_MARKERS
        if marker not in text
    ]


def check_workflows(root: Path) -> list[Finding]:
    """Check workflow permissions, action immutability, and unsafe triggers."""
    findings: list[Finding] = []
    workflow_root = root / ".github" / "workflows"
    for path in workflow_files(root):
        relative_path = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        if not re.search(r"^permissions:(?:\s*\{\})?\s*$", text, re.MULTILINE):
            findings.append(
                Finding(relative_path, "workflow must declare top-level permissions")
            )
        if re.search(r"permissions:\s+(?:write-all|read-all)", text):
            findings.append(Finding(relative_path, "broad permissions are forbidden"))
        if re.search(r"^\s*pull_request_target:\s*$", text, re.MULTILINE):
            findings.append(Finding(relative_path, "pull_request_target is forbidden"))
        for action in ACTION_PATTERN.findall(text):
            if action.startswith("./") or action.startswith("docker://"):
                continue
            if "@" not in action or not SHA_PATTERN.search(action):
                findings.append(
                    Finding(
                        relative_path, f"action is not pinned to a commit SHA: {action}"
                    )
                )
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if "uses: astral-sh/setup-uv@" not in line:
                continue
            action_indent = len(line) - len(line.lstrip())
            configured_version: str | None = None
            for candidate in lines[index + 1 : index + 14]:
                stripped = candidate.strip()
                indent = len(candidate) - len(candidate.lstrip())
                if stripped.startswith("- ") and indent <= action_indent:
                    break
                if stripped.startswith("version:"):
                    configured_version = stripped.split(":", 1)[1].strip().strip("\"'")
                    break
            if configured_version != REQUIRED_UV_VERSION:
                findings.append(
                    Finding(
                        relative_path,
                        "setup-uv must pin the repository frontier version "
                        f"{REQUIRED_UV_VERSION}",
                    )
                )
        if path.parent != workflow_root:
            findings.append(
                Finding(relative_path, "workflow is outside the expected directory")
            )
    findings.extend(
        Finding(f".github/workflows/{name}", "required security workflow is missing")
        for name in REQUIRED_WORKFLOWS
        if not (workflow_root / name).is_file()
    )
    return findings


def check_conflict_markers(root: Path) -> list[Finding]:
    """Reject unresolved Git merge markers in tracked text files."""
    markers = (b"<<<<<<< ", b">>>>>>> ")
    ignored_directories = {
        ".assurance",
        ".git",
        ".tmp-c14",
        ".tox",
        ".venv",
        "__pycache__",
        "_build",
        "build",
        "dist",
        "coverage_html_report",
        "target",
    }
    git = shutil.which("git")
    tracked = (
        subprocess.run(  # noqa: S603 -- executable is resolved from the host PATH.
            [git, "-C", str(root), "ls-files", "-z"],
            capture_output=True,
            check=False,
        )
        if git is not None
        else None
    )
    if tracked is not None and tracked.returncode == 0:
        candidates = [
            root / relative.decode("utf-8", errors="surrogateescape")
            for relative in tracked.stdout.split(b"\0")
            if relative
        ]
    else:
        candidates = list(root.rglob("*"))

    findings: list[Finding] = []
    for path in candidates:
        if not path.is_file() or ignored_directories.intersection(path.parts):
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        if any(
            line.startswith(marker.decode()) for line in content for marker in markers
        ):
            findings.append(
                Finding(
                    path.relative_to(root).as_posix(),
                    "unresolved merge conflict marker",
                )
            )
    return findings


def check_docs_platform(root: Path) -> list[Finding]:
    """Keep Astro/Starlight as the repository's only documentation build path."""
    findings: list[Finding] = []
    forbidden_files = ("docs/conf.py", "docs/Makefile", "docs/make.bat")
    findings.extend(
        Finding(path, "legacy Sphinx build file is forbidden")
        for path in forbidden_files
        if (root / path).exists()
    )
    active_config = (
        "pyproject.toml",
        "tox.ini",
        "noxfile.py",
        ".github/workflows/ci.yml",
    )
    for relative_path in active_config:
        path = root / relative_path
        if path.is_file() and re.search(
            r"sphinx(?:-build)?", path.read_text(encoding="utf-8"), re.IGNORECASE
        ):
            findings.append(
                Finding(
                    relative_path, "Sphinx is forbidden in active build configuration"
                )
            )
    site_manifest = root / "docs/astro-site/package.json"
    if not site_manifest.is_file():
        findings.append(
            Finding("docs/astro-site/package.json", "Astro docs manifest is missing")
        )
    return findings


def check_contract_governance(root: Path) -> list[Finding]:
    """Ensure the v2 contract gate is mirrored across supported runners."""
    findings: list[Finding] = []
    for relative_path, markers in CONTRACT_GOVERNANCE_MARKERS.items():
        path = root / relative_path
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        missing = [marker for marker in markers if marker not in text]
        if missing:
            findings.append(
                Finding(
                    relative_path,
                    "contract governance markers are missing: " + ", ".join(missing),
                )
            )
    return findings


def check_operational_assurance(root: Path) -> list[Finding]:
    """Ensure compatibility, coverage, and cohort gates remain wired."""
    findings: list[Finding] = []
    for relative_path, markers in OPERATIONAL_ASSURANCE_MARKERS.items():
        path = root / relative_path
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        missing = [marker for marker in markers if marker not in text]
        if missing:
            findings.append(
                Finding(
                    relative_path,
                    "operational assurance markers are missing: " + ", ".join(missing),
                )
            )
    policy_path = root / ".github" / "coverage-policy.json"
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        policy = None
    if policy != EXPECTED_COVERAGE_POLICY:
        findings.append(
            Finding(
                ".github/coverage-policy.json",
                "coverage policy must exactly match the promoted thresholds",
            )
        )
    baseline_path = root / ".github" / "mutation-baselines" / "voiage-cohort.json"
    try:
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        provenance = baseline["promotion_provenance"]
        cohort = baseline["cohort"]
        universe = baseline["universe"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        provenance = cohort = universe = None
    externally_anchored = (
        isinstance(provenance, dict)
        and "human_approved" not in provenance
        and provenance.get("review_state") == "requires_external_anchor"
        and isinstance(cohort, dict)
        and {"tool_version", "lock_sha256", "configuration_sha256", "sources"}
        <= set(cohort)
        and isinstance(universe, dict)
        and isinstance(universe.get("ids"), list)
        and isinstance(universe.get("sha256"), str)
    )
    if not externally_anchored:
        findings.append(
            Finding(
                ".github/mutation-baselines/voiage-cohort.json",
                "mutation baseline must require an external review anchor",
            )
        )
    return findings


def check_execution_packets(root: Path) -> list[Finding]:
    """Validate checked-in implementation packets without running their commands."""
    try:
        from scripts.validate_execution_packets import validate_packet
    except ModuleNotFoundError:
        # ``python scripts/repo_harness.py`` puts scripts/ on sys.path.
        from validate_execution_packets import validate_packet

    findings: list[Finding] = []
    for packet_path in sorted(
        (root / "conductor" / "tracks").glob("*/implementation-packet.json")
    ):
        try:
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            errors = validate_packet(packet, root)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            errors = [str(exc)]
        findings.extend(
            Finding(packet_path.relative_to(root).as_posix(), error) for error in errors
        )
    return findings


def collect_findings(root: Path) -> list[Finding]:
    """Run all deterministic harness checks."""
    return (
        check_required_files(root)
        + check_context_contract(root)
        + check_workflows(root)
        + check_docs_platform(root)
        + check_contract_governance(root)
        + check_operational_assurance(root)
        + check_execution_packets(root)
        + check_conflict_markers(root)
    )


def main(argv: list[str] | None = None) -> int:
    """Run the harness and emit a machine-readable summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json", type=Path, help="write the summary to a JSON file")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    findings = collect_findings(root)
    summary = {
        "root": str(root),
        "workflow_count": len(workflow_files(root)),
        "finding_count": len(findings),
        "status": "fail" if findings else "pass",
        "findings": [asdict(finding) for finding in findings],
    }
    rendered = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
