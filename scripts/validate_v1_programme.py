#!/usr/bin/env python3
"""Validate the machine-readable mature v1.0 programme baseline."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

EXPECTED_EXECUTION_ORDER = [
    "architecture-and-contracts",
    "rust-runtime-takeover",
    "legacy-core-retirement",
    "binding-and-extension-consolidation",
    "astro-documentation-consolidation",
    "quality-security-and-reproducibility",
    "registry-publication-and-installability",
    "release-candidate-and-v1-release",
    "post-v1-hardware-evidence",
]
MAX_SNAPSHOT_AGE_DAYS = 30


class ValidationError(ValueError):
    """Raised when the programme baseline and repository disagree."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValidationError(f"cannot read valid baseline JSON: {path}") from error
    if not isinstance(value, dict):
        raise ValidationError("programme baseline must be a JSON object")
    return value


def _required_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise ValidationError(f"required programme file is missing: {path}") from error


def _string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValidationError(f"{field} must be a list of strings")
    return value


def validate(repo_root: Path, *, now: datetime | None = None) -> None:
    """Validate programme state rooted at ``repo_root``.

    Args:
        repo_root: Repository checkout containing Conductor and roadmap files.
        now: Optional UTC clock value for deterministic tests.

    Raises
    ------
        ValidationError: If the baseline is malformed, stale, or inconsistent.
    """
    conductor = repo_root / "conductor"
    baseline = _load_json(conductor / "v1-programme-baseline.json")
    registry = _required_text(conductor / "tracks.md")
    roadmap = _required_text(repo_root / "roadmap.md")
    todo = _required_text(repo_root / "todo.md")

    conductor_state = baseline.get("conductor")
    if not isinstance(conductor_state, dict):
        raise ValidationError("conductor must be an object")
    expected_active = set(
        _string_list(conductor_state.get("active_track_ids"), "active_track_ids")
    )
    tracks_root = conductor / "tracks"
    actual_active = (
        {path.name for path in tracks_root.iterdir() if path.is_dir()}
        if tracks_root.is_dir()
        else set()
    )
    if actual_active != expected_active:
        raise ValidationError("active track directories do not match the baseline")

    registered_active = set(re.findall(r"\./tracks/([^/]+)/", registry))
    if registered_active != expected_active:
        raise ValidationError("active registry links do not match the baseline")

    archive_root = conductor / "archive"
    archive_count = (
        sum(path.is_dir() for path in archive_root.iterdir())
        if archive_root.is_dir()
        else 0
    )
    if archive_count != conductor_state.get("archived_track_count"):
        raise ValidationError("archived track count does not match the baseline")

    for track_id in expected_active:
        if track_id not in roadmap or track_id not in todo:
            raise ValidationError(
                f"active programme {track_id} is missing from roadmap or backlog"
            )

    execution_order = _string_list(baseline.get("execution_order"), "execution_order")
    if execution_order != EXPECTED_EXECUTION_ORDER:
        raise ValidationError(
            "execution order does not match the v1 programme contract"
        )

    github = baseline.get("github")
    if not isinstance(github, dict):
        raise ValidationError("github must be an object")
    for field in ("open_pull_requests", "open_issues", "remote_branches"):
        value = github.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValidationError(f"github.{field} must be a non-negative integer")
    if not isinstance(github.get("latest_release"), str):
        raise ValidationError("github.latest_release must be a string")
    blocked_pull_requests = github.get("blocked_pull_requests")
    if not isinstance(blocked_pull_requests, list):
        raise ValidationError("github.blocked_pull_requests must be a list")
    for pull_request in blocked_pull_requests:
        if not isinstance(pull_request, dict):
            raise ValidationError("blocked pull request entries must be objects")
        number = pull_request.get("number")
        if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
            raise ValidationError(
                "blocked pull request numbers must be positive integers"
            )
        if not all(
            isinstance(pull_request.get(field), str) for field in ("scope", "evidence")
        ):
            raise ValidationError("blocked pull requests require scope and evidence")
    snapshot_value = github.get("snapshot_at")
    if not isinstance(snapshot_value, str):
        raise ValidationError("github.snapshot_at must be an ISO-8601 string")
    try:
        snapshot = datetime.fromisoformat(snapshot_value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValidationError("github.snapshot_at is not valid ISO-8601") from error
    if now is not None:
        clock = now if now.tzinfo is not None else now.replace(tzinfo=UTC)
    else:
        env_now = os.environ.get("PROGRAMME_VALIDATOR_NOW")
        if env_now:
            try:
                clock = datetime.fromisoformat(env_now.replace("Z", "+00:00"))
            except ValueError:
                clock = datetime.now(UTC)
        else:
            clock = datetime.now(UTC)
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=UTC)
    if snapshot.tzinfo is None:
        raise ValidationError("github.snapshot_at must be timezone-aware")
    age_days = (clock - snapshot.astimezone(UTC)).total_seconds() / 86400
    if age_days < 0 or age_days > MAX_SNAPSHOT_AGE_DAYS:
        raise ValidationError("GitHub programme snapshot is stale or in the future")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root to validate (default: current directory)",
    )
    return parser.parse_args()


def main() -> int:
    """Run validation and return a process exit status."""
    args = _parse_args()
    try:
        validate(args.repo_root.resolve())
    except ValidationError as error:
        print(f"v1 programme integrity: error: {error}", file=sys.stderr)
        return 1
    print("v1 programme integrity: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
