#!/usr/bin/env python3
"""Emit a deterministic Rust feature/MSRV qualification matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tomllib


def package_matrix(manifest: Path) -> dict[str, object]:
    """Return feature lanes and MSRV metadata for one Cargo package."""
    data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    package = data.get("package", {})
    features = data.get("features", {})
    assert isinstance(package, dict)
    assert isinstance(features, dict)
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
        "rust_version": package.get("rust-version"),
        "features": names,
        "lanes": lanes,
    }


def build_matrix(root: Path) -> dict[str, object]:
    """Return the workspace-wide deterministic feature qualification matrix."""
    workspace = tomllib.loads((root / "rust/Cargo.toml").read_text(encoding="utf-8"))
    members = workspace["workspace"]["members"]
    assert isinstance(members, list)
    rows = [
        package_matrix(root / "rust" / str(member) / "Cargo.toml") for member in members
    ]
    return {
        "schema_version": "1.0",
        "workspace_rust_version": workspace["workspace"]["package"]["rust-version"],
        "packages": rows,
    }


def main() -> int:
    """Write the matrix report and return a successful process status."""
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, nargs="?", default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_matrix(args.root.resolve())
    destination = args.output or args.root / ".conductor/local/rust-feature-matrix.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
