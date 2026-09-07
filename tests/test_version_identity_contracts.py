"""Version-envelope compatibility and migration contract tests."""

from dataclasses import asdict

import pytest

from voiage.versioning import (
    VersionEnvelope,
    VersionSyncError,
    migrate_version_envelope,
    validate_version_envelope,
)


def envelope(**overrides: str) -> dict[str, str]:
    value = {
        "schema_version": "1.0",
        "package_version": "2.2.0",
        "algorithm_id": "evpi:analytic:v1",
        "rng_id": "pcg64:seeded:v1",
        "input_schema_id": "decision-problem:v1",
    }
    value.update(overrides)
    return value


def test_valid_envelope_round_trips() -> None:
    value = validate_version_envelope(envelope())
    assert isinstance(value, VersionEnvelope)
    assert asdict(value)["algorithm_id"] == "evpi:analytic:v1"


@pytest.mark.parametrize(
    "field",
    ["schema_version", "package_version", "algorithm_id", "rng_id", "input_schema_id"],
)
def test_missing_required_identity_fails(field: str) -> None:
    value = envelope()
    del value[field]
    with pytest.raises(VersionSyncError, match="missing required"):
        validate_version_envelope(value)


def test_unknown_fields_and_unsupported_major_fail() -> None:
    with pytest.raises(VersionSyncError, match="unknown fields"):
        validate_version_envelope(envelope(provider="foreign"))
    with pytest.raises(VersionSyncError, match="unsupported"):
        validate_version_envelope(envelope(schema_version="2.0"))


def test_old_reader_new_writer_compatible_with_same_major() -> None:
    old = envelope(algorithm_id="evpi:analytic:v1")
    new = envelope(algorithm_id="evpi:analytic:v2")
    assert validate_version_envelope(old).schema_version == "1.0"
    assert validate_version_envelope(new).schema_version == "1.0"


def test_migration_records_both_identities_and_rejects_same_identity() -> None:
    migrated = migrate_version_envelope(
        envelope(), envelope(algorithm_id="evpi:analytic:v2")
    )
    assert migrated["migration"] == "explicit"
    assert migrated["from"].algorithm_id != migrated["to"].algorithm_id
    with pytest.raises(VersionSyncError, match="distinct"):
        migrate_version_envelope(envelope(), envelope())


@pytest.mark.parametrize("value", [None, [], "envelope"])
def test_non_object_envelope_fails_closed(value: object) -> None:
    with pytest.raises(VersionSyncError, match="must be an object"):
        validate_version_envelope(value)


def test_non_string_identity_fields_fail_closed() -> None:
    with pytest.raises(VersionSyncError, match="non-empty strings"):
        validate_version_envelope(envelope(rng_id=123))


def test_same_major_additive_schema_is_read_compatibly() -> None:
    value = envelope(schema_version="1.1", provider="native")
    assert validate_version_envelope(value).schema_version == "1.1"
