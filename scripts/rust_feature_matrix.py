#!/usr/bin/env python3
"""Emit a deterministic Rust feature/MSRV qualification matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tomllib


def package_matrix(manifest: Path, workspace_rust_version: str) -> dict[str, object]:
    """Return feature lanes and MSRV metadata for one Cargo package."""
    try:
        data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Package manifest not found: {manifest}") from error
    package = data.get("package", {})
    features = data.get("features", {})
    if not isinstance(package, dict) or not isinstance(features, dict):
        raise TypeError(f"Invalid package manifest structure: {manifest}")
    names = sorted(str(name) for name in features if name != "default")
    lanes = [
        "default",
        "no-default-features",
        *[f"feature:{name}" for name in names],
        "all-features",
    ]
    return {
        "package": package.get("name"),
        "manifest": str(manifest),
        "rust_version": workspace_rust_version
        if package.get("rust-version") == {"workspace": True}
        else package.get("rust-version"),
        "features": names,
        "lanes": lanes,
    }


def build_matrix(root: Path) -> dict[str, object]:
    """Return the workspace-wide deterministic feature qualification matrix."""
    manifest = root / "rust/Cargo.toml"
    try:
        workspace = tomllib.loads(manifest.read_text(encoding="utf-8"))
        workspace_table = workspace["workspace"]
        members = workspace_table["members"]
        workspace_package = workspace_table["package"]
        workspace_rust_version = workspace_package["rust-version"]
    except (FileNotFoundError, KeyError, TypeError) as error:
        raise ValueError(f"Invalid workspace manifest structure: {manifest}") from error
    if not isinstance(members, list) or not isinstance(workspace_rust_version, str):
        raise TypeError("Workspace members must be a list and rust-version a string")
    rows = [
        package_matrix(
            root / "rust" / str(member) / "Cargo.toml", workspace_rust_version
        )
        for member in members
    ]
    return {
        "schema_version": "1.0",
        "workspace_rust_version": workspace_rust_version,
        "packages": rows,
    }


def verify_matrix(root: Path, report: dict[str, object]) -> list[list[str]]:
    """Run every declared feature lane with Cargo's locked resolver."""
    commands: list[list[str]] = []
    for row in report["packages"]:
        package = row["package"]
        for lane in row["lanes"]:
            command = [
                "cargo",
                "check",
                "--manifest-path",
                "rust/Cargo.toml",
                "-p",
                str(package),
                "--locked",
            ]
            if lane == "no-default-features":
                command.append("--no-default-features")
            elif lane == "all-features":
                command.append("--all-features")
            elif lane.startswith("feature:"):
                command.extend(["--features", lane.removeprefix("feature:")])
            subprocess.run(command, cwd=root, check=True)  # noqa: S603 -- command is constructed from Cargo metadata
            commands.append(command)
    return commands


def main() -> int:
    """Write the matrix report and return a successful process status."""
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, nargs="?", default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="run locked cargo checks for every feature lane",
    )
    args = parser.parse_args()
    report = build_matrix(args.root.resolve())
    if args.verify:
        verify_matrix(args.root.resolve(), report)
    destination = args.output or args.root / ".conductor/local/rust-feature-matrix.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
