"""Version synchronization helpers for release automation.

The production Cargo workspace is authoritative. Package adapters and external
binding manifests must remain coherent with it, and release tags are accepted
only when they exactly encode that workspace version.
"""

import argparse
from collections.abc import Callable
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
import tomllib
from typing import Any

from defusedxml import ElementTree

REPO_ROOT = Path.cwd()
_DESCRIPTION_VERSION_RE = re.compile(r"^Version:\s*(?P<version>\S+)\s*$")
_DESCRIPTION_RELEASE_VERSION_RE = re.compile(
    r"^Config/voiage/Release-Version:\s*(?P<version>\S+)\s*$"
)
_CANONICAL_VERSION_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)"
    r"(?:-rc\.(?P<rc>0|[1-9]\d*))?$"
)
_R_VERSION_RE = re.compile(r"^(?:0|[1-9]\d*)(?:\.(?:0|[1-9]\d*)){1,}$")


@dataclass(frozen=True, slots=True)
class VersionTarget:
    """A manifest whose version must match the canonical repo version."""

    label: str
    path: Path
    reader: Callable[[Path], str]


@dataclass(frozen=True, slots=True)
class VersionMismatch:
    """A manifest whose version does not match the canonical repo version."""

    label: str
    path: Path
    expected: str
    found: str


@dataclass(frozen=True, slots=True)
class ReleaseIdentity:
    """Canonical release identity and its ecosystem-specific projections."""

    canonical: str
    python: str
    cargo: str
    julia: str
    is_prerelease: bool


@dataclass(frozen=True, slots=True)
class VersionEnvelope:
    """Version identities required to safely replay a serialized VOI result."""

    schema_version: str
    package_version: str
    algorithm_id: str
    rng_id: str
    input_schema_id: str


def validate_version_envelope(value: object) -> VersionEnvelope:
    """Validate a version envelope without silently accepting unknown fields."""
    if not isinstance(value, dict):
        raise VersionSyncError("version envelope must be an object")
    required = {
        "schema_version",
        "package_version",
        "algorithm_id",
        "rng_id",
        "input_schema_id",
    }
    missing = sorted(required - value.keys())
    unknown = sorted(set(value) - required)
    if missing:
        raise VersionSyncError(
            "version envelope missing required fields: " + ", ".join(missing)
        )
    if unknown and value.get("schema_version") == "1.0":
        raise VersionSyncError(
            "version envelope has unknown fields: " + ", ".join(unknown)
        )
    schema_version = value["schema_version"]
    if (
        not isinstance(schema_version, str)
        or not schema_version.startswith("1.")
        or schema_version.count(".") != 1
    ):
        raise VersionSyncError("unsupported version envelope schema")
    if any(
        not isinstance(value[field], str) or not value[field].strip()
        for field in required
    ):
        raise VersionSyncError("version envelope fields must be non-empty strings")
    release_identity(value["package_version"])
    return VersionEnvelope(**value)


def migrate_version_envelope(
    old: object, new: object
) -> dict[str, VersionEnvelope | str]:
    """Record an explicit envelope migration while preserving both identities."""
    previous = validate_version_envelope(old)
    current = validate_version_envelope(new)
    if previous == current:
        raise VersionSyncError("migration requires distinct version identities")
    return {"from": previous, "to": current, "migration": "explicit"}


class VersionSyncError(RuntimeError):
    """Raised when version synchronization fails."""


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    if not isinstance(data, dict):
        raise VersionSyncError(f"{path}: expected TOML document object")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise VersionSyncError(f"{path}: expected JSON object")
    return data


def _read_canonical_version(pyproject_path: Path) -> str:
    """Read the Cargo workspace version adjacent to ``pyproject.toml``."""
    project = _load_toml(pyproject_path).get("project")
    if not isinstance(project, dict):
        raise VersionSyncError(f"{pyproject_path}: missing [project] table")
    dynamic = project.get("dynamic", [])
    if not isinstance(dynamic, list) or "version" not in dynamic:
        raise VersionSyncError(
            f"{pyproject_path}: project.version must be dynamic and Cargo-backed"
        )
    return _read_toml_version(
        pyproject_path.parent / "rust/Cargo.toml",
        key_path=("workspace", "package", "version"),
    )


def _read_json_version(path: Path) -> str:
    version = _load_json(path).get("version")
    if not isinstance(version, str) or not version.strip():
        raise VersionSyncError(f"{path}: missing version")
    return version


def _read_toml_version(path: Path, *, key_path: tuple[str, ...] = ()) -> str:
    data: Any = _load_toml(path)
    if key_path:
        for key in key_path:
            if not isinstance(data, dict) or key not in data:
                raise VersionSyncError(f"{path}: missing {'.'.join(key_path)}")
            data = data[key]
    else:
        data = data.get("version")
    if not isinstance(data, str) or not data.strip():
        raise VersionSyncError(f"{path}: missing version")
    return data


def _read_cargo_version(path: Path) -> str:
    return _read_toml_version(path, key_path=("package", "version"))


def _read_workspace_inherited_cargo_version(path: Path) -> str:
    data = _load_toml(path)
    package = data.get("package")
    if not isinstance(package, dict):
        raise VersionSyncError(f"{path}: missing package table")
    version = package.get("version")
    if isinstance(version, dict) and version.get("workspace") is True:
        return _read_toml_version(
            path.parents[2] / "Cargo.toml",
            key_path=("workspace", "package", "version"),
        )
    if isinstance(version, str) and version.strip():
        raise VersionSyncError(f"{path}: package version must inherit from workspace")
    raise VersionSyncError(f"{path}: package version must inherit from workspace")


def _read_csproj_version(path: Path) -> str:
    tree = ElementTree.parse(path)
    root = tree.getroot()
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag != "Version":
            continue
        version = (element.text or "").strip()
        if version:
            return version
    raise VersionSyncError(f"{path}: missing <Version>")


def _read_description_version(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _DESCRIPTION_VERSION_RE.match(line.strip())
        if match:
            version = match.group("version").strip()
            if version:
                return version
    raise VersionSyncError(f"{path}: missing Version field")


def _read_description_release_version(path: Path) -> str | None:
    """Read the optional canonical release identity from an R DESCRIPTION."""
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _DESCRIPTION_RELEASE_VERSION_RE.match(line.strip())
        if match:
            return match.group("version").strip()
    return None


def release_identity(version: str) -> ReleaseIdentity:
    """Validate a canonical version and project it into package ecosystems.

    Stable versions are identical in Cargo, Julia, and Python. Release
    candidates retain their SemVer spelling in Cargo and Julia while Python
    uses its normalized PEP 440 spelling. Other prerelease labels are rejected
    so release automation cannot silently invent ecosystem-specific mappings.
    """
    match = _CANONICAL_VERSION_RE.fullmatch(version)
    if match is None:
        raise VersionSyncError(
            f"unsupported canonical version {version!r}; expected MAJOR.MINOR.PATCH"
            " or MAJOR.MINOR.PATCH-rc.N"
        )
    rc = match.group("rc")
    python_version = version if rc is None else version.split("-rc.", 1)[0] + f"rc{rc}"
    return ReleaseIdentity(
        canonical=version,
        python=python_version,
        cargo=version,
        julia=version,
        is_prerelease=rc is not None,
    )


def _read_r_release_identity(path: Path) -> str:
    """Read the canonical identity represented by an R DESCRIPTION."""
    return _read_description_release_version(path) or _read_description_version(path)


def _r_version_mismatch(
    path: Path,
    identity: ReleaseIdentity,
) -> VersionMismatch | None:
    """Validate the native R version that represents a canonical identity."""
    r_version = _read_description_version(path)
    if not identity.is_prerelease:
        if r_version == identity.canonical:
            return None
        return VersionMismatch("R", path, identity.canonical, r_version)

    if _R_VERSION_RE.fullmatch(r_version) is None:
        return VersionMismatch(
            "R package version",
            path,
            "a numeric R development version",
            r_version,
        )

    canonical_match = _CANONICAL_VERSION_RE.fullmatch(identity.canonical)
    if canonical_match is None:  # pragma: no cover - release_identity validated it
        raise ValueError("release identity returned a non-canonical version")
    rc_number = int(canonical_match.group("rc") or "0")
    r_parts = tuple(int(part) for part in r_version.split("."))
    target_parts = tuple(
        int(canonical_match.group(part)) for part in ("major", "minor", "patch")
    )
    expected_suffix = 9000 + rc_number
    if r_parts[:3] >= target_parts or r_parts[-1] != expected_suffix:
        return VersionMismatch(
            "R package version",
            path,
            f"a numeric version below {'.'.join(map(str, target_parts))} "
            f"ending in .{expected_suffix}",
            r_version,
        )
    return None


VERSION_TARGETS: tuple[VersionTarget, ...] = (
    VersionTarget(
        "Python Rust adapter",
        Path("rust/crates/voiage-python/Cargo.toml"),
        _read_workspace_inherited_cargo_version,
    ),
    VersionTarget("Julia", Path("bindings/julia/Project.toml"), _read_toml_version),
    VersionTarget(
        "R release identity",
        Path("r-package/voiageR/DESCRIPTION"),
        _read_r_release_identity,
    ),
)


def validate_release_tag(tag: str, repo_root: Path = REPO_ROOT) -> str:
    """Fail closed unless ``tag`` exactly matches the Cargo workspace version."""
    canonical = _read_canonical_version(repo_root / "pyproject.toml")
    release_identity(canonical)
    expected = f"v{canonical}"
    if tag != expected:
        raise VersionSyncError(
            f"release tag {tag!r} must match {expected!r} from rust/Cargo.toml"
        )
    return canonical


def collect_version_mismatches(
    repo_root: Path = REPO_ROOT,
) -> tuple[str, list[VersionMismatch]]:
    """Collect manifest version mismatches against the canonical repo version."""
    canonical = _read_canonical_version(repo_root / "pyproject.toml")
    identity = release_identity(canonical)
    mismatches: list[VersionMismatch] = []
    for target in VERSION_TARGETS:
        manifest_path = repo_root / target.path
        if not manifest_path.is_file():
            raise VersionSyncError(f"missing manifest: {manifest_path}")
        found = target.reader(manifest_path)
        if found != canonical:
            mismatches.append(
                VersionMismatch(
                    label=target.label,
                    path=manifest_path,
                    expected=canonical,
                    found=found,
                )
            )
    r_path = repo_root / "r-package/voiageR/DESCRIPTION"
    r_mismatch = _r_version_mismatch(r_path, identity)
    if r_mismatch is not None and not any(
        mismatch.path == r_path for mismatch in mismatches
    ):
        mismatches.append(r_mismatch)
    return canonical, mismatches


def format_version_mismatches(
    mismatches: list[VersionMismatch],
    *,
    repo_root: Path = REPO_ROOT,
) -> str:
    """Format version mismatches as a human-readable diagnostic."""
    lines = ["version synchronization failed:"]
    for mismatch in mismatches:
        relpath = mismatch.path.relative_to(repo_root).as_posix()
        lines.append(
            f"- {mismatch.label}: {relpath} expected {mismatch.expected!r} but found {mismatch.found!r}"
        )
    return "\n".join(lines)


def validate_version_sync(
    repo_root: Path = REPO_ROOT,
) -> tuple[str, list[VersionMismatch]]:
    """Validate that binding manifests match the canonical repo version."""
    canonical, mismatches = collect_version_mismatches(repo_root)
    if mismatches:
        raise VersionSyncError(
            format_version_mismatches(mismatches, repo_root=repo_root)
        )
    return canonical, mismatches


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for the version synchronization validator."""
    parser = argparse.ArgumentParser(
        description="Validate that package manifests match the canonical repo version."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root to validate (defaults to the current checkout).",
    )
    parser.add_argument(
        "--release-tag",
        help="Require an exact v<workspace-version> release tag.",
    )
    parser.add_argument(
        "--print-python-version",
        action="store_true",
        help="Print only the normalized Python package version.",
    )
    args = parser.parse_args(argv)

    try:
        canonical, _ = validate_version_sync(args.repo_root)
        if args.release_tag is not None:
            validate_release_tag(args.release_tag, args.repo_root)
    except VersionSyncError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.print_python_version:
        print(release_identity(canonical).python)
    else:
        print(
            f"validated version synchronization against "
            f"{args.repo_root / 'pyproject.toml'} @ {canonical}"
        )
    return 0


__all__ = [
    "REPO_ROOT",
    "ReleaseIdentity",
    "VersionMismatch",
    "VersionSyncError",
    "VersionTarget",
    "collect_version_mismatches",
    "format_version_mismatches",
    "main",
    "release_identity",
    "validate_release_tag",
    "validate_version_sync",
]


if __name__ == "__main__":  # pragma: no cover - exercised by workflow commands.
    raise SystemExit(main())
