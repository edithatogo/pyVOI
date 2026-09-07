"""Validate Conductor implementation packets without executing packet commands."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

TASK_ID = re.compile(r"^(?:T\d+\.\d+|CLOSE\.\d+)$")
RESULT_STATES = {"pending", "passed", "failed", "blocked"}
REQUIRED = {
    "schema_version",
    "track_id",
    "source_baseline",
    "preparation_state",
    "execution_state",
    "delivery_repository",
    "read_before_start",
    "input_sha256",
    "reserved_implementation_files",
    "phases",
}


def _error(message: str) -> ValueError:
    return ValueError(message)


def _safe_relative(root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise _error(f"{label} must be a non-empty relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise _error(f"{label} escapes repository root: {value}")
    candidate = root / path
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise _error(f"{label} escapes repository root: {value}") from exc
    if candidate.is_symlink():
        try:
            candidate.resolve().relative_to(root.resolve())
        except ValueError as exc:
            raise _error(f"{label} follows an escaping symlink: {value}") from exc
    return path


def _plan_task_ids(track_dir: Path) -> set[str]:
    plan = track_dir / "plan.md"
    if not plan.is_file():
        return set()
    return set(re.findall(r"\b(?:T\d+\.\d+|CLOSE\.\d+)\b", plan.read_text()))


def validate_packet(
    packet: dict[str, Any],
    root: Path,
    *,
    require_ready: bool = False,
    changed_paths: list[str] | None = None,
) -> list[str]:
    """Return deterministic validation errors for one packet."""
    errors: list[str] = []
    missing = sorted(REQUIRED - packet.keys())
    if missing:
        errors.append("missing required fields: " + ", ".join(missing))
        return errors
    if packet.get("schema_version") != "1.0":
        errors.append("unsupported schema_version")
    track_id = packet.get("track_id")
    if not isinstance(track_id, str) or not re.fullmatch(r"[a-z0-9_]+", track_id):
        errors.append("track_id is invalid")
    if packet.get("source_baseline") and not re.fullmatch(
        r"[0-9a-f]{40}", str(packet["source_baseline"])
    ):
        errors.append("source_baseline must be a 40-character commit SHA")
    for field in ("read_before_start", "reserved_implementation_files"):
        values = packet.get(field)
        if not isinstance(values, list):
            errors.append(f"{field} must be a list")
            continue
        for value in values:
            try:
                _safe_relative(root, value, field)
            except ValueError as exc:
                errors.append(str(exc))
    hashes = packet.get("input_sha256")
    if not isinstance(hashes, dict):
        errors.append("input_sha256 must be an object")
    else:
        for name, expected in hashes.items():
            try:
                relative = _safe_relative(root, name, "input_sha256 path")
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if not isinstance(expected, str) or not re.fullmatch(
                r"[0-9a-f]{64}", expected
            ):
                errors.append(f"invalid SHA-256 for {name}")
                continue
            path = root / relative
            if not path.is_file():
                errors.append(f"input file is missing: {name}")
                continue
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != expected:
                errors.append(f"stale baseline hash: {name}")
    phases = packet.get("phases")
    ids: list[str] = []
    dependencies: dict[str, list[str]] = {}
    if not isinstance(phases, list):
        errors.append("phases must be a list")
    else:
        known = _plan_task_ids(root / "conductor" / "tracks" / str(track_id))
        for phase in phases:
            if not isinstance(phase, dict):
                errors.append("each phase must be an object")
                continue
            task_ids = phase.get("task_ids")
            if not isinstance(task_ids, list):
                errors.append("phase task_ids must be a list")
                continue
            for task_id in task_ids:
                if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
                    errors.append(f"unknown task ID: {task_id}")
                    continue
                if task_id in ids:
                    errors.append(f"duplicate task ID: {task_id}")
                ids.append(task_id)
                if known and task_id not in known:
                    errors.append(f"unknown task ID: {task_id}")
            dependencies.update(
                {str(k): list(v) for k, v in phase.get("dependencies", {}).items()}
                if isinstance(phase.get("dependencies", {}), dict)
                else {}
            )
        all_ids = set(ids)
        for deps in dependencies.values():
            for dep in deps:
                if dep not in all_ids:
                    errors.extend([f"dependency references unknown task ID: {dep}"])
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                errors.append("dependency cycle detected")
                return
            if node in visited:
                return
            visiting.add(node)
            for dep in dependencies.get(node, []):
                visit(dep)
            visiting.remove(node)
            visited.add(node)

        for task_id in ids:
            visit(task_id)
    if require_ready:
        if packet.get("execution_state") != "ready_for_preflight":
            errors.append("packet is not ready_for_preflight")
        prerequisites = packet.get("prerequisite_tracks", [])
        if not isinstance(prerequisites, list):
            errors.append("prerequisite_tracks must be a list")
        for prerequisite in prerequisites if isinstance(prerequisites, list) else []:
            if (
                not isinstance(prerequisite, dict)
                or prerequisite.get("result_status") != "passed"
                or not prerequisite.get("evidence")
            ):
                errors.extend(["pending or failed prerequisite lacks passing evidence"])
    for value in (
        packet.get("result_states", [])
        if isinstance(packet.get("result_states", []), list)
        else []
    ):
        if value not in RESULT_STATES:
            errors.extend([f"unsupported result state: {value}"])
    if changed_paths:
        allowed = set(packet.get("reserved_implementation_files", []))
        for changed in changed_paths:
            try:
                relative = _safe_relative(root, changed, "changed path").as_posix()
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if relative not in allowed:
                errors.append(f"out-of-scope changed path: {relative}")
    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    """Validate one packet and return a process status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--changed-file", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        packet = json.loads(args.packet.read_text(encoding="utf-8"))
        errors = validate_packet(
            packet,
            args.repo_root.resolve(),
            require_ready=args.require_ready,
            changed_paths=args.changed_file,
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        errors = [str(exc)]
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
