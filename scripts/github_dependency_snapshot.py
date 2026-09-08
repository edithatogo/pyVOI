"""Convert the retained CycloneDX inventory to a GitHub dependency snapshot."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any


def snapshot(document: dict[str, Any], *, sha: str, ref: str) -> dict[str, Any]:
    """Build one GitHub dependency-submission payload."""
    ref_to_purl = {
        component.get("bom-ref"): component.get("purl")
        for component in document.get("components", [])
        if isinstance(component, dict)
        and isinstance(component.get("bom-ref"), str)
        and isinstance(component.get("purl"), str)
    }
    dependency_refs = {
        dependency_ref
        for relationship in document.get("dependencies", [])
        if isinstance(relationship, dict)
        for dependency_ref in relationship.get("dependsOn", [])
        if isinstance(dependency_ref, str)
    }
    dependency_edges = {
        relationship.get("ref"): [
            ref_to_purl[dependency_ref]
            for dependency_ref in relationship.get("dependsOn", [])
            if dependency_ref in ref_to_purl
        ]
        for relationship in document.get("dependencies", [])
        if isinstance(relationship, dict) and isinstance(relationship.get("ref"), str)
    }
    resolved: dict[str, dict[str, Any]] = {}
    for component in document.get("components", []):
        if not isinstance(component, dict):
            continue
        purl = component.get("purl")
        if not isinstance(purl, str) or not purl:
            continue
        resolved[purl] = {
            "package_url": purl,
            "relationship": (
                "indirect" if component.get("bom-ref") in dependency_refs else "direct"
            ),
            "scope": "runtime",
            "dependencies": dependency_edges.get(component.get("bom-ref"), []),
        }
    return {
        "version": 0,
        "sha": sha,
        "ref": ref,
        "job": {
            "correlator": "polyglot-assurance_dependency-submission",
            "id": os.environ.get("GITHUB_RUN_ID", "local"),
        },
        "detector": {
            "name": "voiage-polyglot-cyclonedx",
            "version": "1.0.0",
            "url": "https://github.com/edithatogo/voiage",
        },
        "scanned": os.environ.get("GITHUB_RUN_STARTED_AT", "1970-01-01T00:00:00Z"),
        "manifests": {
            "polyglot.sbom.cdx.json": {
                "name": "voiage mixed-language resolved dependencies",
                "file": {"source_location": "polyglot.sbom.cdx.json"},
                "resolved": resolved,
            }
        },
    }


def main() -> int:
    """Write the dependency snapshot named by the command line."""
    if len(sys.argv) != 3:
        print("usage: github_dependency_snapshot.py SBOM OUTPUT", file=sys.stderr)
        return 2
    document = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    payload = snapshot(
        document,
        sha=os.environ.get("GITHUB_SHA", "0" * 40),
        ref=os.environ.get("GITHUB_REF", "refs/heads/local"),
    )
    Path(sys.argv[2]).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
