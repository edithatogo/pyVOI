"""Governance contract for the mature, hardened v1.0 programme baseline."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

BASELINE_PATH = Path("conductor/v1-programme-baseline.json")
TRACK_ID = "mature-hardened-v1-release-programme_20260719"
ACTIVE_TRACK_IDS = [
    "controlled_live_dataset_interoperability_20260801",
    "datasets_worked_examples_20260723",
    "estimation_focused_variance_voi_20260727",
    "external_voi_library_feature_parity_20260723",
    "information_source_portfolio_voi_20260801",
    "ml_llm_agent_voi_20260723",
    "polyglot_abi_binding_parity_20260723",
    "quality_release_automation_20260723",
    "research_contribution_ai_transparency_20260723",
    "remote_dataset_ingestion_security_20260801",
    "rust_polyglot_voi_completion_20260723",
    "sampling_acquisition_harm_voi_20260802",
    "stable_voi_rust_core_completion_20260723",
    "supported_frontier_method_completion_20260723",
    "uncertainty_modelling_value_20260801",
    "value_of_perspective_completion_20260723",
    "voi_method_census_contract_reconciliation_20260723",
]
VALIDATOR = Path("scripts/validate_v1_programme.py")


def _baseline() -> dict[str, object]:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def test_v1_programme_baseline_records_authoritative_repository_state() -> None:
    """The programme starts from a reproducible remote and GitHub snapshot."""
    baseline = _baseline()
    repository = baseline["repository"]
    github = baseline["github"]

    assert repository == {
        "authoritative_branch": "origin/main",
        "authoritative_commit": "35bc08ee119eb6213ac59949b3b00da1c20ca3a2",
        "implementation_branch": "codex/mature-hardened-v1-programme",
        "generated_artifacts_excluded": ["docs/astro-site/.astro/"],
    }
    assert github["snapshot_at"] == "2026-07-22T08:00:00Z"
    assert github["open_pull_requests"] == 0
    assert github["open_issues"] == 0
    assert github["remote_branches"] == 1
    assert github["latest_release"] == "v1.0.0"


def test_v1_programme_baseline_classifies_tracks_and_execution_lanes() -> None:
    """Archived groundwork, v1 work, and external gates stay distinct."""
    baseline = _baseline()
    conductor = baseline["conductor"]

    assert conductor["active_track_ids"] == ACTIVE_TRACK_IDS
    assert conductor["archived_track_count"] == 132
    assert conductor["classifications"] == {
        "v1_required": [
            "repository-owned mature-v1 programme completed; external publication gates transferred to research_software_registry_readiness_20260721"
        ],
        "historical_groundwork": "conductor/archive/",
        "post_v1_or_optional": [
            "controlled_live_dataset_interoperability_20260801",
            "datasets_worked_examples_20260723",
            "estimation_focused_variance_voi_20260727",
            "external_voi_library_feature_parity_20260723",
            "information_source_portfolio_voi_20260801",
            "ml_llm_agent_voi_20260723",
            "polyglot_abi_binding_parity_20260723",
            "quality_release_automation_20260723",
            "research_contribution_ai_transparency_20260723",
            "research_software_registry_readiness_20260721",
            "risk_adjusted_information_pricing_20260731",
            "remote_dataset_ingestion_security_20260801",
            "rust_polyglot_voi_completion_20260723",
            "sampling_acquisition_harm_voi_20260802",
            "stable_voi_rust_core_completion_20260723",
            "standardized-dataset-ingestion_20260723",
            "study_design_efficiency_20260727",
            "supported_frontier_method_completion_20260723",
            "uncertainty_modelling_value_20260801",
            "value_of_perspective_completion_20260723",
            "voi_method_census_contract_reconciliation_20260723",
            "accelerator production-speedup evidence",
            "frontier-method stable promotion beyond the frozen v1 surface",
            "FPGA and ASIC production execution",
        ],
        "externally_blocked": [
            "conda-forge indexing and review",
            "CRAN or approved R registry review",
            "Julia General registry review",
            "external hardware, cloud quota, and curation gates",
        ],
        "superseded_or_duplicate": [],
    }
    assert baseline["execution_order"] == [
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


def test_roadmap_and_backlog_distinguish_archived_v1_from_current_queue() -> None:
    """Preserve the v1 baseline without presenting it as current execution."""
    roadmap = Path("roadmap.md").read_text(encoding="utf-8")
    todo = Path("todo.md").read_text(encoding="utf-8")
    registry = Path("conductor/tracks.md").read_text(encoding="utf-8")

    assert "Current Status (As of August 2026)" in roadmap
    assert "Mature Hardened v1.0 Programme: ✅ **ARCHIVED**" in roadmap
    assert "conductor/v1-programme-baseline.json" in roadmap
    assert "The June 25 follow-through queue is complete and archived" in roadmap
    assert "Production Workspace Established, Stable Kernels Rust-Backed" in roadmap
    assert (
        "Follow-Through Expansion (created June 25, 2026): 🔄 **ACTIVE**" not in roadmap
    )

    current_track_id = "v2_2_release_and_venue_submissions_20260830"
    current_metadata = {
        path.parent.name: json.loads(path.read_text(encoding="utf-8"))
        for path in Path("conductor/tracks").glob("*/metadata.json")
    }
    from scripts.normalize_conductor_registry import collect_track_records

    registered_current = {
        record.track_dir.name: record
        for record in collect_track_records(Path.cwd())
        if record.track_dir.parent == Path.cwd() / "conductor/tracks"
    }
    assert set(current_metadata) == set(registered_current)
    assert current_track_id in current_metadata
    assert current_metadata[current_track_id]["status"] == "in_progress"
    current_todo = todo.split("## To Do\n", maxsplit=1)[1].split("\n## ", maxsplit=1)[0]
    for track_id, metadata in current_metadata.items():
        assert metadata["status"] in {"new", "in_progress", "completed"}
        assert metadata["status"] == registered_current[track_id].expected_status
        current_link = f"./tracks/{track_id}/index.md"
        assert f"]({current_link})" in registry
        assert f"conductor/tracks/{track_id}/" in roadmap
        assert f"conductor/tracks/{track_id}/" in current_todo
    assert "Mature and harden the v1.0 release" not in current_todo
    assert "*   [x] Mature and harden the v1.0 release" in todo
    assert "research_software_registry_readiness_20260721" in todo
    for track_id in ACTIVE_TRACK_IDS:
        assert track_id in roadmap
        assert track_id in todo
    assert "## [x] Track: Research Software Registry Readiness" in registry


def test_cross_reference_reconciliation_archive_records_merged_handoff() -> None:
    """The archived track must not retain its pre-merge status projection."""
    archive = Path(
        "conductor/archive/conductor-github-cross-reference-reconciliation_20260724"
    )
    index = (archive / "index.md").read_text(encoding="utf-8")
    metadata = json.loads((archive / "metadata.json").read_text(encoding="utf-8"))

    assert metadata["status"] == "completed"
    assert "Status: completed and archived" in index
    assert "pull/465" in index
    assert "No pull request proven" not in index


def test_cross_reference_reconciliation_narratives_record_completion() -> None:
    """Roadmap and backlog must agree with the archived track lifecycle."""
    track_id = "conductor-github-cross-reference-reconciliation_20260724"
    roadmap = Path("roadmap.md").read_text(encoding="utf-8")
    todo = Path("todo.md").read_text(encoding="utf-8")
    in_progress, done = todo.split("## Done", maxsplit=1)

    assert "Conductor-to-GitHub traceability is complete and archived" in roadmap
    assert "repository validation and PR handoff remain in progress" not in roadmap
    assert track_id not in in_progress
    assert track_id in done


def _run_validator(root: Path) -> subprocess.CompletedProcess[str]:
    import os

    env = os.environ.copy()
    baseline_path = root / "conductor" / "v1-programme-baseline.json"
    if not baseline_path.exists():
        baseline_path = BASELINE_PATH
    try:
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        env["PROGRAMME_VALIDATOR_NOW"] = str(baseline["github"]["snapshot_at"])
    except (KeyError, TypeError, ValueError, OSError):
        env["PROGRAMME_VALIDATOR_NOW"] = "2026-07-20T08:45:00Z"
    return subprocess.run(
        [sys.executable, str(VALIDATOR.resolve()), "--repo-root", str(root)],
        capture_output=True,
        check=False,
        text=True,
        env=env,
    )


def test_v1_programme_validator_accepts_repository_baseline() -> None:
    """The checked-in programme state must pass the reusable validator."""
    result = _run_validator(Path.cwd())

    assert result.returncode == 0, result.stderr
    assert "v1 programme integrity: ok" in result.stdout


def test_v1_programme_validator_allows_separately_governed_post_v1_tracks(
    tmp_path: Path,
) -> None:
    """The frozen v1 snapshot must not prohibit later active programmes."""
    conductor = tmp_path / "conductor"
    later_track = conductor / "tracks" / "post_v1_programme"
    for track_id in ACTIVE_TRACK_IDS:
        (conductor / "tracks" / track_id).mkdir(parents=True)
    later_track.mkdir()
    baseline = _baseline()
    baseline["conductor"]["archived_track_count"] = 0
    (conductor / "v1-programme-baseline.json").write_text(
        json.dumps(baseline), encoding="utf-8"
    )
    registry_links = [
        f"*Link: [./tracks/{track_id}/](./tracks/{track_id}/)*"
        for track_id in ACTIVE_TRACK_IDS
    ]
    registry_links.append(
        "*Link: [./tracks/post_v1_programme/](./tracks/post_v1_programme/)*"
    )
    (conductor / "tracks.md").write_text(
        "\n".join(registry_links),
        encoding="utf-8",
    )
    baseline_track_list = "\n".join(ACTIVE_TRACK_IDS)
    (tmp_path / "roadmap.md").write_text(baseline_track_list, encoding="utf-8")
    (tmp_path / "todo.md").write_text(baseline_track_list, encoding="utf-8")

    result = _run_validator(tmp_path)

    assert result.returncode == 0, result.stderr


def test_v1_programme_validator_allows_later_archived_tracks(tmp_path: Path) -> None:
    """A frozen historical count is a lower bound, not a future archive cap."""
    conductor = tmp_path / "conductor"
    for track_id in ACTIVE_TRACK_IDS:
        (conductor / "tracks" / track_id).mkdir(parents=True)
    (conductor / "archive" / "historical").mkdir(parents=True)
    (conductor / "archive" / "post_v1_completion").mkdir()
    baseline = _baseline()
    baseline["conductor"]["archived_track_count"] = 1
    (conductor / "v1-programme-baseline.json").write_text(
        json.dumps(baseline), encoding="utf-8"
    )
    registry_links = [
        f"*Link: [./tracks/{track_id}/](./tracks/{track_id}/)*"
        for track_id in ACTIVE_TRACK_IDS
    ]
    (conductor / "tracks.md").write_text("\n".join(registry_links), encoding="utf-8")
    baseline_track_list = "\n".join(ACTIVE_TRACK_IDS)
    (tmp_path / "roadmap.md").write_text(baseline_track_list, encoding="utf-8")
    (tmp_path / "todo.md").write_text(baseline_track_list, encoding="utf-8")

    result = _run_validator(tmp_path)

    assert result.returncode == 0, result.stderr


def test_v1_programme_validator_rejects_archive_loss(tmp_path: Path) -> None:
    """The repository may grow beyond the snapshot but must retain its history."""
    conductor = tmp_path / "conductor"
    for track_id in ACTIVE_TRACK_IDS:
        (conductor / "tracks" / track_id).mkdir(parents=True)
    baseline = _baseline()
    baseline["conductor"]["archived_track_count"] = 1
    (conductor / "v1-programme-baseline.json").write_text(
        json.dumps(baseline), encoding="utf-8"
    )
    registry_links = [
        f"*Link: [./tracks/{track_id}/](./tracks/{track_id}/)*"
        for track_id in ACTIVE_TRACK_IDS
    ]
    (conductor / "tracks.md").write_text("\n".join(registry_links), encoding="utf-8")
    baseline_track_list = "\n".join(ACTIVE_TRACK_IDS)
    (tmp_path / "roadmap.md").write_text(baseline_track_list, encoding="utf-8")
    (tmp_path / "todo.md").write_text(baseline_track_list, encoding="utf-8")

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "archived track count is below the frozen baseline" in result.stderr


def test_v1_programme_validator_rejects_registry_drift(tmp_path: Path) -> None:
    """A registered active track must resolve to an active directory."""
    conductor = tmp_path / "conductor"
    conductor.mkdir()
    baseline = _baseline()
    (conductor / "v1-programme-baseline.json").write_text(
        json.dumps(baseline), encoding="utf-8"
    )
    (conductor / "tracks.md").write_text(
        "## [~] Track: Mature Hardened v1.0 Architecture And Release Programme\n"
        f"*Link: [./tracks/{TRACK_ID}/](./tracks/{TRACK_ID}/)*\n",
        encoding="utf-8",
    )
    (tmp_path / "roadmap.md").write_text(TRACK_ID, encoding="utf-8")
    (tmp_path / "todo.md").write_text(TRACK_ID, encoding="utf-8")

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "active track directories do not contain the baseline" in result.stderr


def test_v1_programme_validator_rejects_execution_order_drift(
    tmp_path: Path,
) -> None:
    """The release lane must precede optional post-v1 hardware evidence."""
    conductor = tmp_path / "conductor"
    active = conductor / "tracks" / TRACK_ID
    active.mkdir(parents=True)
    baseline = _baseline()
    baseline["conductor"]["active_track_ids"] = [TRACK_ID]
    baseline["conductor"]["archived_track_count"] = 0
    baseline["execution_order"] = list(reversed(baseline["execution_order"]))
    (conductor / "v1-programme-baseline.json").write_text(
        json.dumps(baseline), encoding="utf-8"
    )
    (conductor / "tracks.md").write_text(
        "## [~] Track: Mature Hardened v1.0 Architecture And Release Programme\n"
        f"*Link: [./tracks/{TRACK_ID}/](./tracks/{TRACK_ID}/)*\n",
        encoding="utf-8",
    )
    (tmp_path / "roadmap.md").write_text(TRACK_ID, encoding="utf-8")
    (tmp_path / "todo.md").write_text(TRACK_ID, encoding="utf-8")

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "execution order does not match the v1 programme contract" in result.stderr


def test_v1_programme_validator_rejects_invalid_github_counts(
    tmp_path: Path,
) -> None:
    """Malformed GitHub evidence must not pass as a valid status snapshot."""
    conductor = tmp_path / "conductor"
    active = conductor / "tracks" / TRACK_ID
    active.mkdir(parents=True)
    baseline = _baseline()
    baseline["conductor"]["active_track_ids"] = [TRACK_ID]
    baseline["conductor"]["archived_track_count"] = 0
    baseline["github"]["open_issues"] = -1
    (conductor / "v1-programme-baseline.json").write_text(
        json.dumps(baseline), encoding="utf-8"
    )
    (conductor / "tracks.md").write_text(
        "## [~] Track: Mature Hardened v1.0 Architecture And Release Programme\n"
        f"*Link: [./tracks/{TRACK_ID}/index.md]"
        f"(./tracks/{TRACK_ID}/index.md)*\n",
        encoding="utf-8",
    )
    (tmp_path / "roadmap.md").write_text(TRACK_ID, encoding="utf-8")
    (tmp_path / "todo.md").write_text(TRACK_ID, encoding="utf-8")

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "github.open_issues must be a non-negative integer" in result.stderr
