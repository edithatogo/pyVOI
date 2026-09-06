"""Scientific-review evidence must be structured, bound, and fail closed."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from voiage import scientific_review_evidence as review_evidence
from voiage.scientific_review_evidence import (
    ScientificReviewEvidenceError,
    bind_scientific_review_bundle,
    canonical_json_sha256,
    load_scientific_review_schemas,
    validate_scientific_review_bundle,
    validate_scientific_review_evidence,
)

ROOT = Path(__file__).parents[1]
FIXTURE = (
    ROOT
    / "specs/frontier/governance/scientific-review/v1/fixtures/valid-review-bundle.json"
)
GIT = shutil.which("git")


def _bundle() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _rebind(bundle: dict[str, object]) -> dict[str, object]:
    return bind_scientific_review_bundle(bundle)


def test_all_scientific_review_evidence_schemas_are_valid() -> None:
    schemas = load_scientific_review_schemas()

    assert set(schemas) == {
        "adjudication",
        "artifact-manifest",
        "delta-classification",
        "disagreement",
        "disposition",
        "finding",
        "promotion-receipt",
        "review-packet",
        "reviewer-attestation",
        "role-report",
        "scientific-approval",
    }


@pytest.mark.parametrize(
    ("schema_contents", "message"),
    [
        (None, "cannot load schema"),
        ("{", "cannot load schema"),
        ("[]", "must be an object"),
    ],
)
def test_schema_loading_fails_closed_for_missing_or_malformed_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    schema_contents: str | None,
    message: str,
) -> None:
    schema_root = tmp_path / "schemas"
    schema_root.mkdir()
    if schema_contents is not None:
        (schema_root / "common.schema.json").write_text(
            schema_contents, encoding="utf-8"
        )
    monkeypatch.setattr(review_evidence, "SCHEMA_ROOT", schema_root)

    with pytest.raises(ScientificReviewEvidenceError, match=message):
        load_scientific_review_schemas()


def test_valid_review_bundle_is_candidate_bound_and_complete() -> None:
    bundle = _bundle()

    validate_scientific_review_bundle(bundle)
    for kind, payload in bundle["evidence"].items():
        if kind in {"reviewer-attestation", "role-report"}:
            for item in payload:
                validate_scientific_review_evidence(kind, item)
        elif kind not in {
            "finding",
            "disagreement",
            "disposition",
            "delta-classification",
        }:
            validate_scientific_review_evidence(kind, payload)


def test_contract_uses_typed_git_oids_and_canonical_content_digests() -> None:
    bundle = _bundle()
    packet = bundle["evidence"]["review-packet"]

    assert bundle["schema_version"] == "1.1.0"
    assert packet["candidate_commit"] == {"algorithm": "sha1", "value": "a" * 40}
    assert packet["candidate_tree"] == {"algorithm": "sha1", "value": "b" * 40}
    assert packet["packet_sha256"] == canonical_json_sha256(
        packet, excluded_json_pointers={"/packet_sha256"}
    )

    legacy = deepcopy(packet)
    legacy["candidate_commit"] = "a" * 64
    with pytest.raises(ScientificReviewEvidenceError):
        validate_scientific_review_evidence("review-packet", legacy)


def test_fabricated_declared_digest_is_rejected() -> None:
    bundle = _bundle()
    bundle["evidence"]["review-packet"]["packet_sha256"] = "f" * 64

    with pytest.raises(ScientificReviewEvidenceError, match="canonical digest"):
        validate_scientific_review_bundle(bundle)


def test_manifest_bytes_are_verified_against_the_frozen_git_tree(
    tmp_path: Path,
) -> None:
    assert GIT is not None
    repository = tmp_path / "repo"
    repository.mkdir()
    subprocess.run([GIT, "init", "-q", str(repository)], check=True)
    subprocess.run(
        [GIT, "-C", str(repository), "config", "user.email", "test@example.invalid"],
        check=True,
    )
    subprocess.run(
        [GIT, "-C", str(repository), "config", "user.name", "Contract Test"],
        check=True,
    )
    artifact = repository / "specs/example.json"
    artifact.parent.mkdir()
    artifact.write_text('{"fixture":true}\n', encoding="utf-8")
    subprocess.run([GIT, "-C", str(repository), "add", "."], check=True)
    subprocess.run(
        [GIT, "-C", str(repository), "commit", "-q", "-m", "fixture"],
        check=True,
    )
    commit = subprocess.check_output(
        [GIT, "-C", str(repository), "rev-parse", "HEAD"], text=True
    ).strip()
    tree = subprocess.check_output(
        [GIT, "-C", str(repository), "rev-parse", "HEAD^{tree}"], text=True
    ).strip()

    bundle = _bundle()
    bundle["fixture_status"] = "candidate_bound_contract_test"
    for value in bundle["evidence"].values():
        items = value if isinstance(value, list) else [value]
        for item in items:
            if "candidate_commit" in item:
                item["candidate_commit"] = {"algorithm": "sha1", "value": commit}
                item["candidate_tree"] = {"algorithm": "sha1", "value": tree}
    bundle["evidence"]["artifact-manifest"]["artifacts"][0]["sha256"] = hashlib.sha256(
        artifact.read_bytes()
    ).hexdigest()
    bundle = _rebind(bundle)
    validate_scientific_review_bundle(bundle, repository_root=repository)

    artifact.write_text('{"fixture":false}\n', encoding="utf-8")
    # The working tree is irrelevant; the frozen commit remains authoritative.
    validate_scientific_review_bundle(bundle, repository_root=repository)

    bundle["evidence"]["artifact-manifest"]["artifacts"][0]["sha256"] = "f" * 64
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="artifact bytes"):
        validate_scientific_review_bundle(bundle, repository_root=repository)


def test_report_attestation_and_decision_roles_cannot_collapse() -> None:
    bundle = _bundle()
    report = bundle["evidence"]["role-report"][0]
    report["reviewer"]["qualifications"] = ["different claim"]
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="attestation exactly"):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    bundle["evidence"]["scientific-approval"]["approver"] = deepcopy(
        bundle["evidence"]["adjudication"]["chair"]
    )
    bundle["evidence"]["scientific-approval"]["human_receipt"]["signer_identity"] = (
        "review-chair"
    )
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="separation of duties"):
        validate_scientific_review_bundle(bundle)


def test_medium_finding_requires_disposition_and_fresh_rereview() -> None:
    bundle = _bundle()
    finding = bundle["evidence"]["finding"][0]
    finding["severity"] = "medium"
    bundle["evidence"]["disposition"] = []
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="Medium finding"):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    bundle["evidence"]["finding"][0]["severity"] = "medium"
    bundle["evidence"]["disposition"][0]["rereview_report_ids"] = []
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="affected-role re-review"):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    bundle["evidence"]["finding"][0]["severity"] = "medium"
    bundle["evidence"]["disposition"][0]["rereview_report_ids"] = ["REPORT-ESTIMAND"]
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="affected-role re-review"):
        validate_scientific_review_bundle(bundle)


def test_reviewed_exclusion_must_bind_removed_capabilities() -> None:
    bundle = _bundle()
    disposition = bundle["evidence"]["disposition"][0]
    disposition["disposition"] = "reviewed_exclusion"
    disposition["excluded_capabilities"] = []
    bundle = _rebind(bundle)

    with pytest.raises(ScientificReviewEvidenceError, match="excluded capability"):
        validate_scientific_review_bundle(bundle)


def test_bounded_delta_is_field_allowlisted_and_signers_are_distinct() -> None:
    bundle = _bundle()
    delta = bundle["evidence"]["delta-classification"][0]
    delta["changed_paths"] = ["docs/synthetic-review.md"]
    delta["changed_artifact_hashes"][0]["path"] = "docs/synthetic-review.md"
    delta["changed_artifact_hashes"][0]["changed_fields"] = ["/title"]
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="administrative allowlist"):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    delta = bundle["evidence"]["delta-classification"][0]
    delta["signatures"][1]["reviewer"]["identity"] = delta["signatures"][0]["reviewer"][
        "identity"
    ]
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="distinct people"):
        validate_scientific_review_bundle(bundle)


def test_changed_path_and_hash_inventory_must_match_exactly() -> None:
    bundle = _bundle()
    bundle["evidence"]["delta-classification"][0]["changed_paths"].append(
        "conductor/tracks/other/metadata.json"
    )
    bundle = _rebind(bundle)

    with pytest.raises(ScientificReviewEvidenceError, match="changed-path inventory"):
        validate_scientific_review_bundle(bundle)


def test_human_receipts_expiry_and_supersession_fail_closed() -> None:
    bundle = _bundle()
    approval = bundle["evidence"]["scientific-approval"]
    assert approval["approver"]["actor_type"] == "human"
    assert approval["human_receipt"]["verification_method"] in {
        "signed_commit",
        "authenticated_github",
        "external_authoritative_receipt",
    }

    approval["human_receipt"]["signer_identity"] = "different-person"
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="signer"):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    approval = bundle["evidence"]["scientific-approval"]
    approval["expires_at"] = approval["decision_at"]
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="after decision_at"):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    bundle["evidence"]["scientific-approval"]["superseded_by"] = "APPROVAL-2"
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="superseded"):
        validate_scientific_review_bundle(
            bundle, at_time=datetime(2026, 8, 3, tzinfo=UTC)
        )


def test_unknown_finding_disposition_is_rejected() -> None:
    bundle = _bundle()
    extra = deepcopy(bundle["evidence"]["disposition"][0])
    extra["disposition_id"] = "D-UNKNOWN"
    extra["finding_id"] = "F-UNKNOWN"
    bundle["evidence"]["disposition"].append(extra)
    bundle = _rebind(bundle)

    with pytest.raises(ScientificReviewEvidenceError, match="unknown finding"):
        validate_scientific_review_bundle(bundle)


@pytest.mark.parametrize(
    "field", ["candidate_commit", "candidate_tree", "packet_sha256"]
)
def test_mixed_candidate_or_packet_binding_is_rejected(field: str) -> None:
    bundle = _bundle()
    bundle["evidence"]["scientific-approval"][field] = (
        {"algorithm": "sha1", "value": "f" * 40}
        if field != "packet_sha256"
        else "f" * 64
    )

    with pytest.raises(ScientificReviewEvidenceError, match="binding"):
        validate_scientific_review_bundle(bundle)


def test_boolean_only_or_conflicted_approval_is_rejected() -> None:
    approval = _bundle()["evidence"]["scientific-approval"]
    boolean_only = {
        "approved": True,
        "candidate_commit": approval["candidate_commit"],
    }

    with pytest.raises(ScientificReviewEvidenceError):
        validate_scientific_review_evidence("scientific-approval", boolean_only)

    conflicted = deepcopy(approval)
    conflicted["approver"]["conflict_status"] = "disqualifying"
    conflicted["approver"]["independent"] = False
    with pytest.raises(ScientificReviewEvidenceError, match="eligible independent"):
        validate_scientific_review_bundle(
            {
                **_bundle(),
                "evidence": {
                    **_bundle()["evidence"],
                    "scientific-approval": conflicted,
                },
            }
        )


def test_unknown_kind_and_malformed_bundle_shapes_are_rejected() -> None:
    with pytest.raises(ScientificReviewEvidenceError, match="unknown"):
        validate_scientific_review_evidence("boolean-approval", {"approved": True})
    with pytest.raises(ScientificReviewEvidenceError, match="must be an object"):
        validate_scientific_review_bundle(None)

    bundle = _bundle()
    bundle["schema_version"] = "2.0.0"
    with pytest.raises(ScientificReviewEvidenceError, match="schema_version"):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    bundle["evidence"]["disagreement"] = "not-an-array"
    with pytest.raises(ScientificReviewEvidenceError, match="must be an array"):
        validate_scientific_review_bundle(bundle)


def test_required_roles_and_unresolved_high_findings_block_acceptance() -> None:
    bundle = _bundle()
    bundle["evidence"]["role-report"] = bundle["evidence"]["role-report"][:-1]
    with pytest.raises(ScientificReviewEvidenceError, match="required reviewer roles"):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    bundle["evidence"]["finding"] = [
        {
            **bundle["evidence"]["finding"][0],
            "severity": "high",
            "finding_id": "F-HIGH-OPEN",
        }
    ]
    bundle["evidence"]["disposition"] = []
    bundle["evidence"]["role-report"][0]["finding_ids"] = ["F-HIGH-OPEN"]
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="Critical/High"):
        validate_scientific_review_bundle(bundle)


def test_independently_verified_high_finding_is_accepted() -> None:
    bundle = _bundle()
    bundle["evidence"]["finding"][0]["severity"] = "high"

    validate_scientific_review_bundle(bundle)


def test_every_report_requires_a_matching_attestation_and_scope() -> None:
    bundle = _bundle()
    bundle["evidence"]["reviewer-attestation"] = [
        item
        for item in bundle["evidence"]["reviewer-attestation"]
        if item["reviewer"]["identity"] != "reviewer-estimand"
    ]
    with pytest.raises(
        ScientificReviewEvidenceError,
        match="role report reviewer lacks a matching attestation: reviewer-estimand",
    ):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    bundle["evidence"]["adjudication"]["scope"]["family"] = "different-family"
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="scope"):
        validate_scientific_review_bundle(bundle)


def test_open_scientific_dissent_blocks_positive_approval() -> None:
    bundle = _bundle()
    bundle["evidence"]["disagreement"] = [
        {
            "evidence_kind": "disagreement",
            "schema_version": "1.1.0",
            "disagreement_id": "DISSENT-1",
            "candidate_commit": {"algorithm": "sha1", "value": "a" * 40},
            "candidate_tree": {"algorithm": "sha1", "value": "b" * 40},
            "packet_sha256": bundle["evidence"]["review-packet"]["packet_sha256"],
            "topic": "scientific validity",
            "positions": [
                {
                    "reviewer_identity": "reviewer-estimand",
                    "position": "valid",
                    "evidence_refs": ["REPORT-ESTIMAND"],
                },
                {
                    "reviewer_identity": "reviewer-estimator",
                    "position": "not valid",
                    "evidence_refs": ["REPORT-ESTIMATOR"],
                },
            ],
            "scientific_validity_dissent": True,
            "resolution_evidence_required": "Independent reconstruction",
            "status": "open",
            "recorded_at": "2026-08-02T00:00:00Z",
        }
    ]
    bundle["expected_disagreement_ids"] = ["DISSENT-1"]
    for kind in ("adjudication", "scientific-approval", "promotion-receipt"):
        bundle["evidence"][kind]["dissent_refs"] = ["DISSENT-1"]
    bundle = _rebind(bundle)
    with pytest.raises(
        ScientificReviewEvidenceError,
        match="unresolved scientific-validity dissent blocks positive approval",
    ):
        validate_scientific_review_bundle(bundle)


def test_ineligible_reviewers_and_inconsistent_decisions_are_rejected() -> None:
    bundle = _bundle()
    bundle["evidence"]["role-report"][0]["reviewer"]["independent"] = False
    with pytest.raises(ScientificReviewEvidenceError, match="role reports"):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    bundle["evidence"]["adjudication"]["chair"]["conflict_status"] = "disqualifying"
    with pytest.raises(ScientificReviewEvidenceError, match="chair"):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    bundle["evidence"]["adjudication"]["decision"] = "reviewed_exclusion"
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="decision differs"):
        validate_scientific_review_bundle(bundle)


def test_bounded_delta_requires_metadata_only_paths_and_two_signatures() -> None:
    bundle = _bundle()
    delta = bundle["evidence"]["delta-classification"][0]
    delta["changed_paths"] = ["voiage/methods/utility_information.py"]
    delta["changed_artifact_hashes"][0]["path"] = delta["changed_paths"][0]
    with pytest.raises(ScientificReviewEvidenceError, match="administrative allowlist"):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    bundle["evidence"]["delta-classification"][0]["signatures"] = [
        bundle["evidence"]["delta-classification"][0]["signatures"][0]
    ]
    with pytest.raises(ScientificReviewEvidenceError, match="two independent"):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    bundle["evidence"]["delta-classification"][0]["signatures"][0]["reviewer"][
        "independent"
    ] = False
    with pytest.raises(ScientificReviewEvidenceError, match="eligible and independent"):
        validate_scientific_review_bundle(bundle)


@pytest.mark.parametrize("changed_path", ["/absolute.md", "docs/../review.md"])
def test_bounded_delta_rejects_absolute_and_parent_traversal_paths(
    changed_path: str,
) -> None:
    bundle = _bundle()
    bundle["evidence"]["delta-classification"][0]["changed_paths"] = [changed_path]
    bundle["evidence"]["delta-classification"][0]["changed_artifact_hashes"][0][
        "path"
    ] = changed_path

    with pytest.raises(ScientificReviewEvidenceError, match="administrative allowlist"):
        validate_scientific_review_bundle(bundle)


def test_full_invalidation_delta_does_not_use_metadata_only_exception() -> None:
    bundle = _bundle()
    delta = bundle["evidence"]["delta-classification"][0]
    delta["classification"] = "full_invalidation"
    delta["changed_paths"] = ["voiage/scientific_review_evidence.py"]
    delta["changed_artifact_hashes"][0]["path"] = delta["changed_paths"][0]

    validate_scientific_review_bundle(bundle)


def test_promotion_digest_decision_and_supersession_are_fail_closed() -> None:
    bundle = _bundle()
    bundle["evidence"]["promotion-receipt"]["scientific_approval_sha256"] = "f" * 64
    bundle["evidence"]["promotion-receipt"]["human_receipt"]["payload_sha256"] = (
        canonical_json_sha256(
            bundle["evidence"]["promotion-receipt"],
            excluded_json_pointers={
                "/receipt_sha256",
                "/human_receipt/payload_sha256",
            },
        )
    )
    with pytest.raises(ScientificReviewEvidenceError, match="approval digest"):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    bundle["evidence"]["promotion-receipt"]["decision"] = "promote"
    bundle["evidence"]["scientific-approval"]["decision"] = (
        "conditional_remediation_and_rereview"
    )
    bundle["evidence"]["adjudication"]["decision"] = (
        "conditional_remediation_and_rereview"
    )
    bundle = _rebind(bundle)
    with pytest.raises(
        ScientificReviewEvidenceError, match="scientifically acceptable"
    ):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    bundle["evidence"]["promotion-receipt"]["decision"] = "promote"
    bundle["evidence"]["scientific-approval"]["superseded_by"] = "APPROVAL-2"
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="superseded"):
        validate_scientific_review_bundle(bundle)


def test_expired_or_superseded_approval_cannot_authorize_promotion() -> None:
    bundle = _bundle()
    bundle["evidence"]["scientific-approval"]["expires_at"] = "2026-08-01T00:00:00Z"
    bundle["evidence"]["promotion-receipt"]["decision"] = "promote"
    bundle["evidence"]["promotion-receipt"]["decision_at"] = "2026-08-02T00:00:00Z"
    bundle = _rebind(bundle)

    with pytest.raises(ScientificReviewEvidenceError, match="expired"):
        validate_scientific_review_bundle(bundle)


def test_current_approval_can_authorize_promotion() -> None:
    bundle = _bundle()
    bundle["evidence"]["promotion-receipt"]["decision"] = "promote"
    bundle = _rebind(bundle)

    validate_scientific_review_bundle(bundle)


@pytest.mark.parametrize("timestamp", [None, "not-a-timestamp"])
def test_timestamp_parser_fails_closed_for_non_timestamp_values(
    timestamp: object,
) -> None:
    with pytest.raises(ScientificReviewEvidenceError, match="RFC 3339"):
        review_evidence._parse_timestamp(timestamp, "approval.expires_at")


def test_canonical_pointer_and_administrative_path_helpers_fail_closed() -> None:
    payload = {"nested": {"value": 1}, "a/b": {"~key": 2}}
    with pytest.raises(ValueError, match="absolute"):
        review_evidence._remove_json_pointer(payload, "nested/value")
    review_evidence._remove_json_pointer(payload, "/missing/value")
    review_evidence._remove_json_pointer(payload, "/a~1b/~0key")
    assert payload == {"nested": {"value": 1}, "a/b": {}}
    scalar_payload = {"nested": 1}
    review_evidence._remove_json_pointer(scalar_payload, "/nested/value")
    assert scalar_payload == {"nested": 1}

    assert review_evidence._is_administrative_only(
        "conductor/governance-readback.json", ["/observed_at"]
    )
    assert not review_evidence._is_administrative_only(
        "conductor/governance-readback.json", []
    )
    assert not review_evidence._is_administrative_only(
        "conductor/tracks/example/metadata.json", ["/status"]
    )


def test_timestamp_and_human_receipt_helpers_reject_invalid_assurance() -> None:
    with pytest.raises(ScientificReviewEvidenceError, match="UTC offset"):
        review_evidence._parse_timestamp("2026-08-02T00:00:00", "decision_at")

    artifact = _bundle()["evidence"]["scientific-approval"]
    digest = review_evidence._declared_digest("scientific-approval", artifact)
    for field, value, message in (
        ("verification_method", "email", "unsupported"),
        ("payload_sha256", "f" * 64, "canonical digest"),
        ("verification_status", "pending", "not verified"),
    ):
        changed = deepcopy(artifact)
        changed["human_receipt"][field] = value
        with pytest.raises(ScientificReviewEvidenceError, match=message):
            review_evidence._verify_human_receipt(changed, digest, "approval")


def test_role_and_inventory_identifiers_must_be_unique_and_complete() -> None:
    mutations = []

    def duplicate_attestation(bundle: dict[str, object]) -> None:
        bundle["evidence"]["reviewer-attestation"].append(
            deepcopy(bundle["evidence"]["reviewer-attestation"][0])
        )

    mutations.append((duplicate_attestation, "unique identities"))

    def duplicate_report(bundle: dict[str, object]) -> None:
        bundle["evidence"]["role-report"][1]["report_id"] = bundle["evidence"][
            "role-report"
        ][0]["report_id"]

    mutations.append((duplicate_report, "report IDs"))

    def duplicate_finding(bundle: dict[str, object]) -> None:
        bundle["evidence"]["finding"].append(deepcopy(bundle["evidence"]["finding"][0]))

    mutations.append((duplicate_finding, "finding IDs"))

    def incomplete_report_findings(bundle: dict[str, object]) -> None:
        bundle["evidence"]["role-report"][0]["finding_ids"] = []

    mutations.append((incomplete_report_findings, "finding inventory is incomplete"))

    def duplicate_disposition(bundle: dict[str, object]) -> None:
        duplicate = deepcopy(bundle["evidence"]["disposition"][0])
        duplicate["disposition_id"] = "D-LOW-2"
        bundle["evidence"]["disposition"].append(duplicate)

    mutations.append((duplicate_disposition, "only one disposition"))

    for mutate, message in mutations:
        bundle = _bundle()
        mutate(bundle)
        bundle = _rebind(bundle)
        with pytest.raises(ScientificReviewEvidenceError) as caught:
            validate_scientific_review_bundle(bundle)
        assert message in str(caught.value), mutate.__name__

    bundle = _rebind(_bundle())
    bundle["expected_finding_ids"] = []
    with pytest.raises(ScientificReviewEvidenceError, match="finding inventory"):
        validate_scientific_review_bundle(bundle)


def test_finding_severity_disposition_rules_fail_closed() -> None:
    bundle = _bundle()
    bundle["evidence"]["disposition"] = []
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="Low finding"):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    bundle["evidence"]["finding"][0]["severity"] = "medium"
    bundle["evidence"]["disposition"][0]["independently_verified"] = False
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="unresolved Medium"):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    bundle["evidence"]["finding"][0]["severity"] = "critical"
    bundle["evidence"]["disposition"][0]["disposition"] = "accepted_experimental_risk"
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="Critical/High"):
        validate_scientific_review_bundle(bundle)


def test_human_decision_makers_and_receipt_digests_are_enforced() -> None:
    bundle = _bundle()
    bundle["evidence"]["role-report"][0]["report_sha256"] = "f" * 64
    with pytest.raises(ScientificReviewEvidenceError, match="canonical digest"):
        validate_scientific_review_bundle(bundle)

    for decision_kind, actor_field in (
        ("adjudication", "chair"),
        ("scientific-approval", "approver"),
    ):
        bundle = _bundle()
        bundle["evidence"][decision_kind][actor_field]["actor_type"] = "agent"
        bundle = _rebind(bundle)
        with pytest.raises(ScientificReviewEvidenceError, match="must be human"):
            validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    bundle["evidence"]["reviewer-attestation"] = [
        item
        for item in bundle["evidence"]["reviewer-attestation"]
        if item["reviewer"]["identity"] != "review-chair"
    ]
    with pytest.raises(ScientificReviewEvidenceError, match="matching attestation"):
        validate_scientific_review_bundle(bundle)


def test_disagreement_and_dissent_inventories_are_exact() -> None:
    bundle = _bundle()
    bundle["expected_disagreement_ids"] = ["D-MISSING"]
    with pytest.raises(ScientificReviewEvidenceError, match="disagreement inventory"):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    bundle["evidence"]["scientific-approval"]["dissent_refs"] = ["D-MISSING"]
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="dissent references"):
        validate_scientific_review_bundle(bundle)


def test_delta_hashes_and_attested_signers_are_exact() -> None:
    bundle = _bundle()
    delta = bundle["evidence"]["delta-classification"][0]
    delta["changed_artifact_hashes"][0]["after_sha256"] = delta[
        "changed_artifact_hashes"
    ][0]["before_sha256"]
    with pytest.raises(ScientificReviewEvidenceError, match="changed-path inventory"):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    delta = bundle["evidence"]["delta-classification"][0]
    delta["signatures"][0]["reviewer"]["qualifications"] = ["mismatched"]
    with pytest.raises(ScientificReviewEvidenceError, match="attestation exactly"):
        validate_scientific_review_bundle(bundle)


def test_promotion_requires_human_current_scope_and_unexcluded_capability() -> None:
    bundle = _bundle()
    bundle["evidence"]["promotion-receipt"]["maintainer"]["actor_type"] = "agent"
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="human maintainer"):
        validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    disposition = bundle["evidence"]["disposition"][0]
    disposition["disposition"] = "reviewed_exclusion"
    disposition["excluded_capabilities"] = ["synthetic_example_capability"]
    bundle["evidence"]["promotion-receipt"]["decision"] = "promote"
    bundle = _rebind(bundle)
    with pytest.raises(ScientificReviewEvidenceError, match="excluded capability"):
        validate_scientific_review_bundle(bundle)

    for decision_kind in ("adjudication", "promotion-receipt"):
        bundle = _bundle()
        bundle["evidence"][decision_kind]["superseded_by"] = "NEXT-DECISION"
        bundle = _rebind(bundle)
        with pytest.raises(ScientificReviewEvidenceError, match="superseded"):
            validate_scientific_review_bundle(bundle)


def test_non_synthetic_evidence_requires_repository_and_safe_git_objects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _bundle()
    bundle["fixture_status"] = "candidate_bound_contract_test"
    with pytest.raises(ScientificReviewEvidenceError, match="repository_root"):
        validate_scientific_review_bundle(bundle)

    monkeypatch.setattr(review_evidence, "GIT_EXECUTABLE", None)
    with pytest.raises(ScientificReviewEvidenceError, match="git is unavailable"):
        validate_scientific_review_bundle(bundle, repository_root=tmp_path)


def test_binder_allows_evidence_without_optional_candidate_fields() -> None:
    bundle = _bundle()
    del bundle["evidence"]["finding"][0]["candidate_tree"]

    bound = _rebind(bundle)

    assert "candidate_tree" not in bound["evidence"]["finding"][0]


def test_packet_manifest_digest_binding_is_verified_directly() -> None:
    evidence = _rebind(_bundle())["evidence"]
    evidence["review-packet"]["artifact_manifest_sha256"] = "f" * 64
    evidence["review-packet"]["packet_sha256"] = review_evidence._declared_digest(
        "review-packet", evidence["review-packet"]
    )

    with pytest.raises(ScientificReviewEvidenceError, match="artifact-manifest"):
        review_evidence._verify_declared_digests(evidence)


def test_git_command_and_frozen_object_failures_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evidence = _bundle()["evidence"]

    def fail_command(*_args: object, **_kwargs: object) -> bytes:
        raise OSError("unavailable")

    monkeypatch.setattr(review_evidence.subprocess, "check_output", fail_command)
    with pytest.raises(ScientificReviewEvidenceError, match="cannot verify frozen"):
        review_evidence._git_output(tmp_path, "rev-parse", "HEAD")

    def object_format_mismatch(
        _root: Path, *arguments: str, binary: bool = False
    ) -> str | bytes:
        del binary
        if arguments == ("rev-parse", "--show-object-format"):
            return "sha256\n"
        return b"artifact" if arguments[0] == "show" else "b" * 40

    monkeypatch.setattr(review_evidence, "_git_output", object_format_mismatch)
    with pytest.raises(ScientificReviewEvidenceError, match="object format"):
        review_evidence._verify_repository_evidence(evidence, tmp_path)

    def tree_mismatch(
        _root: Path, *arguments: str, binary: bool = False
    ) -> str | bytes:
        del binary
        if arguments == ("rev-parse", "--show-object-format"):
            return "sha1\n"
        return "c" * 40

    monkeypatch.setattr(review_evidence, "_git_output", tree_mismatch)
    with pytest.raises(ScientificReviewEvidenceError, match="candidate tree"):
        review_evidence._verify_repository_evidence(evidence, tmp_path)

    unsafe = deepcopy(evidence)
    unsafe["artifact-manifest"]["artifacts"][0]["path"] = "/absolute.json"

    def valid_git(_root: Path, *arguments: str, binary: bool = False) -> str | bytes:
        if arguments == ("rev-parse", "--show-object-format"):
            return "sha1\n"
        if arguments[0] == "rev-parse":
            return "b" * 40
        return b"artifact" if binary else "artifact"

    monkeypatch.setattr(review_evidence, "_git_output", valid_git)
    with pytest.raises(ScientificReviewEvidenceError, match="path is unsafe"):
        review_evidence._verify_repository_evidence(unsafe, tmp_path)

    duplicate = deepcopy(evidence)
    duplicate["artifact-manifest"]["artifacts"].append(
        deepcopy(duplicate["artifact-manifest"]["artifacts"][0])
    )
    for artifact in duplicate["artifact-manifest"]["artifacts"]:
        artifact["sha256"] = hashlib.sha256(b"artifact").hexdigest()
    with pytest.raises(ScientificReviewEvidenceError, match="paths must be unique"):
        review_evidence._verify_repository_evidence(duplicate, tmp_path)


def test_human_role_report_and_attestation_receipts_are_verified() -> None:
    bundle = _bundle()
    report = bundle["evidence"]["role-report"][0]
    attestation = bundle["evidence"]["reviewer-attestation"][0]
    report["reviewer"]["actor_type"] = "human"
    attestation["reviewer"]["actor_type"] = "human"
    bundle["evidence"]["delta-classification"][0]["signatures"][1]["reviewer"][
        "actor_type"
    ] = "human"
    receipt = deepcopy(bundle["evidence"]["scientific-approval"]["human_receipt"])
    receipt["signer_identity"] = report["reviewer"]["identity"]
    report["human_receipt"] = deepcopy(receipt)
    attestation["human_receipt"] = deepcopy(receipt)
    bundle = _rebind(bundle)

    validate_scientific_review_bundle(bundle)


def test_valid_medium_rereview_and_reviewed_exclusion_paths() -> None:
    bundle = _bundle()
    bundle["evidence"]["finding"][0]["severity"] = "medium"
    disposition = bundle["evidence"]["disposition"][0]
    disposition["affected_reviewer_roles"] = ["estimand_domain"]
    disposition["rereview_report_ids"] = ["REPORT-ESTIMAND"]
    disposition["decided_at"] = "2026-08-01T00:00:00Z"
    bundle = _rebind(bundle)
    validate_scientific_review_bundle(bundle)

    bundle = _bundle()
    disposition = bundle["evidence"]["disposition"][0]
    disposition["disposition"] = "reviewed_exclusion"
    disposition["excluded_capabilities"] = ["synthetic_example_capability"]
    bundle = _rebind(bundle)
    validate_scientific_review_bundle(bundle)


def test_positive_decisions_expire_at_explicit_evaluation_time() -> None:
    bundle = _bundle()
    bundle["evidence"]["adjudication"]["expires_at"] = "2026-08-03T00:00:00Z"
    bundle = _rebind(bundle)

    with pytest.raises(
        ScientificReviewEvidenceError, match="adjudication decision is expired"
    ):
        validate_scientific_review_bundle(
            bundle, at_time=datetime(2026, 8, 4, tzinfo=UTC)
        )
