"""Tests for fail-closed Conductor packet validation."""

import copy
import json
from pathlib import Path

import pytest

from scripts.validate_execution_packets import validate_packet

ROOT = Path(__file__).parents[1]
PACKET_PATH = (
    ROOT / "conductor/tracks/execution_packet_guard_20260907/implementation-packet.json"
)


@pytest.fixture
def packet() -> dict:
    return json.loads(PACKET_PATH.read_text(encoding="utf-8"))


def test_real_packet_preserves_track_identity(packet: dict) -> None:
    assert validate_packet(packet, ROOT) == []
    assert packet["track_id"] == "execution_packet_guard_20260907"
    assert packet["delivery_repository"] == "edithatogo/voiage"


@pytest.mark.parametrize(
    "field", ["schema_version", "track_id", "phases", "input_sha256"]
)
def test_missing_required_field_is_rejected(packet: dict, field: str) -> None:
    packet.pop(field)
    assert any(
        "missing required fields" in error for error in validate_packet(packet, ROOT)
    )


def test_unknown_packet_fields_are_rejected(packet: dict) -> None:
    packet["unexpected"] = "must fail closed"
    errors = validate_packet(packet, ROOT)
    assert any("unknown packet fields: unexpected" in error for error in errors)


def test_unknown_and_duplicate_task_ids_are_rejected(packet: dict) -> None:
    packet["phases"][0]["task_ids"] = ["T1.1", "T1.1", "T99.9"]
    errors = validate_packet(packet, ROOT)
    assert any("duplicate task ID" in error for error in errors)
    assert any("unknown task ID" in error for error in errors)


def test_dependency_cycle_is_rejected(packet: dict) -> None:
    packet["phases"][0]["dependencies"] = {"T1.1": ["T1.2"], "T1.2": ["T1.1"]}
    errors = validate_packet(packet, ROOT)
    assert "dependency cycle detected" in errors


@pytest.mark.parametrize("path", ["/var/voiage-outside", "../outside"])
def test_escaping_changed_path_is_rejected_without_mutation(
    packet: dict, path: str
) -> None:
    before = copy.deepcopy(packet)
    assert validate_packet(packet, ROOT, changed_paths=[path])
    assert packet == before


def test_out_of_scope_staged_unstaged_or_untracked_path_is_rejected(
    packet: dict,
) -> None:
    errors = validate_packet(packet, ROOT, changed_paths=["roadmap.md", "new-file.py"])
    assert any("out-of-scope changed path" in error for error in errors)


def test_stale_hash_and_unsupported_result_state_are_rejected(packet: dict) -> None:
    packet["input_sha256"]["scripts/repo_harness.py"] = "0" * 64
    packet["result_states"] = ["unknown"]
    errors = validate_packet(packet, ROOT)
    assert any("stale baseline hash" in error for error in errors)
    assert "unsupported result state: unknown" in errors


def test_pending_prerequisite_cannot_authorize_ready_packet(packet: dict) -> None:
    packet["prerequisite_tracks"] = [
        {"track_id": "upstream", "result_status": "pending"}
    ]
    assert validate_packet(packet, ROOT, require_ready=True)


def test_no_commands_are_executed_by_validation(
    packet: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess

    monkeypatch.setattr(
        subprocess, "run", lambda *args, **kwargs: pytest.fail("command executed")
    )
    assert validate_packet(packet, ROOT) == []
