#!/usr/bin/env python3
"""Validate the frontier VOI fixture registry and family manifests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, cast

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from jsonschema.exceptions import ValidationError as JsonSchemaError
from referencing import Registry, Resource

REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTIER_ROOT = REPO_ROOT / "specs" / "frontier"
REGISTRY_ROOT = FRONTIER_ROOT / "fixtures"
REGISTRY_MANIFEST = REGISTRY_ROOT / "manifest.json"
REGISTRY_SCHEMA = REGISTRY_ROOT / "manifest.schema.json"


class ValidationError(Exception):
    """Raised when the frontier contract registry is invalid."""


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _require_non_empty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{path}: expected non-empty string")
    return value


def _resolve_contained(
    root: Path, relative: str, label: str, *, base: Path | None = None
) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute():
        raise ValidationError(f"{label}: absolute paths are forbidden")
    resolved_root = root.resolve()
    resolved = ((base or resolved_root) / candidate).resolve()
    if not resolved.is_relative_to(resolved_root):
        raise ValidationError(f"{label}: path escapes its governed root")
    return resolved


def _schema_validator(
    schema: dict[str, object], *, registry: Registry | None = None
) -> Draft202012Validator:
    try:
        Draft202012Validator.check_schema(schema)
        return Draft202012Validator(
            schema,
            registry=registry or Registry(),
            format_checker=FormatChecker(),
        )
    except SchemaError as error:
        raise ValidationError(f"invalid JSON Schema: {error.message}") from error


def _validate_json(
    validator: Draft202012Validator, payload: object, label: str
) -> None:
    try:
        validator.validate(payload)
    except JsonSchemaError as error:
        raise ValidationError(f"{label}: {error.message}") from error


def _validate_registry() -> list[dict[str, object]]:
    registry = _load_json(REGISTRY_MANIFEST)
    if not isinstance(registry, dict):
        raise ValidationError("frontier registry manifest must be an object")
    if registry.get("version") != "v1":
        raise ValidationError("frontier registry version must be 'v1'")
    if registry.get("status") != "registry":
        raise ValidationError("frontier registry status must be 'registry'")

    schema = _load_json(REGISTRY_SCHEMA)
    if (
        not isinstance(schema, dict)
        or schema.get("title") != "FrontierFixtureRegistryV1"
    ):
        raise ValidationError(
            "frontier registry schema title must be 'FrontierFixtureRegistryV1'"
        )
    _validate_json(_schema_validator(schema), registry, "frontier registry")

    families = registry.get("families")
    if not isinstance(families, list) or not families:
        raise ValidationError("frontier registry must define at least one family")

    validated: list[dict[str, object]] = []
    names: set[str] = set()
    paths: set[Path] = set()
    for index, item in enumerate(families):
        if not isinstance(item, dict):
            raise ValidationError(f"$.families[{index}]: expected object")
        name = _require_non_empty_string(item.get("name"), f"$.families[{index}].name")
        relpath = _require_non_empty_string(
            item.get("path"), f"$.families[{index}].path"
        )
        maturity = _require_non_empty_string(
            item.get("method_maturity"), f"$.families[{index}].method_maturity"
        )
        if maturity not in {"experimental", "fixture-backed"}:
            raise ValidationError(
                f"$.families[{index}].method_maturity: expected 'experimental' or 'fixture-backed'"
            )
        if name in names:
            raise ValidationError(f"$.families[{index}].name: duplicate family name")
        resolved_manifest = _resolve_contained(
            FRONTIER_ROOT, relpath, f"$.families[{index}].path"
        )
        if resolved_manifest in paths:
            raise ValidationError(f"$.families[{index}].path: duplicate manifest path")
        names.add(name)
        paths.add(resolved_manifest)
        manifest_kind = item.get("manifest_kind", "split")
        if manifest_kind not in {"split", "bundled"}:
            raise ValidationError(
                f"$.families[{index}].manifest_kind: expected 'split' or 'bundled'"
            )
        validated.append(
            {"name": name, "path": relpath, "manifest_kind": manifest_kind}
        )
    return validated


def _validate_family_manifest(manifest_path: Path) -> None:
    manifest = _load_json(manifest_path)
    if not isinstance(manifest, dict):
        raise ValidationError(f"{manifest_path}: manifest must be an object")
    if manifest.get("version") != "v1":
        raise ValidationError(f"{manifest_path}: version must be 'v1'")
    if manifest.get("status") != "fixture-backed":
        raise ValidationError(f"{manifest_path}: status must be 'fixture-backed'")

    normative = manifest.get("normative")
    if not isinstance(normative, list) or not normative:
        raise ValidationError(
            f"{manifest_path}: normative must contain at least one item"
        )

    fixture_root = manifest_path.parent
    for index, entry in enumerate(normative):
        if not isinstance(entry, dict):
            raise ValidationError(
                f"{manifest_path}: normative[{index}] must be an object"
            )
        input_artifact = _require_non_empty_string(
            entry.get("input_artifact"),
            f"{manifest_path}.normative[{index}].input_artifact",
        )
        output_artifact = _require_non_empty_string(
            entry.get("expected_output_artifact"),
            f"{manifest_path}.normative[{index}].expected_output_artifact",
        )
        input_path = _resolve_contained(
            fixture_root, input_artifact, f"{manifest_path}.normative[{index}].input"
        )
        output_path = _resolve_contained(
            fixture_root,
            output_artifact,
            f"{manifest_path}.normative[{index}].output",
        )
        if not input_path.is_file():
            raise ValidationError(
                f"{manifest_path}: missing input artifact {input_artifact}"
            )
        if not output_path.is_file():
            raise ValidationError(
                f"{manifest_path}: missing output artifact {output_artifact}"
            )


def _validate_bundled_family_manifest(manifest_path: Path) -> None:
    manifest = _load_json(manifest_path)
    if not isinstance(manifest, dict):
        raise ValidationError(f"{manifest_path}: manifest must be an object")
    schema_version = _require_non_empty_string(
        manifest.get("schema_version"), f"{manifest_path}.schema_version"
    )
    if not schema_version.endswith("-v1"):
        raise ValidationError(f"{manifest_path}: schema_version must end with '-v1'")
    if manifest.get("method_maturity") != "experimental":
        raise ValidationError(
            f"{manifest_path}: bundled manifest must remain experimental"
        )
    fixture_root = manifest_path.parent
    schemas: dict[str, dict[str, object]] = {}
    for schema_key in ("request_schema", "result_schema", "reference_schema"):
        schema_path = _require_non_empty_string(
            manifest.get(schema_key), f"{manifest_path}.{schema_key}"
        )
        resolved_schema = _resolve_contained(
            fixture_root.parent,
            schema_path,
            f"{manifest_path}.{schema_key}",
            base=fixture_root,
        )
        if not resolved_schema.is_file():
            raise ValidationError(f"{manifest_path}: missing schema {schema_path}")
        loaded_schema = _load_json(resolved_schema)
        if not isinstance(loaded_schema, dict):
            raise ValidationError(
                f"{manifest_path}: schema {schema_path} must be an object"
            )
        schemas[schema_key] = cast("dict[str, object]", loaded_schema)

    request_schema = schemas["request_schema"]
    request_id = _require_non_empty_string(
        request_schema.get("$id"), f"{manifest_path}.request_schema.$id"
    )
    schema_registry = Registry().with_resource(
        request_id, Resource.from_contents(request_schema)
    )
    request_validator = _schema_validator(request_schema, registry=schema_registry)
    result_validator = _schema_validator(
        schemas["result_schema"], registry=schema_registry
    )
    reference_validator = _schema_validator(schemas["reference_schema"])
    fixtures = manifest.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        raise ValidationError(f"{manifest_path}: fixtures must not be empty")
    fixture_ids: set[str] = set()
    fixture_paths: set[Path] = set()
    for index, entry in enumerate(fixtures):
        if not isinstance(entry, dict):
            raise ValidationError(
                f"{manifest_path}: fixtures[{index}] must be an object"
            )
        fixture_id = _require_non_empty_string(
            entry.get("id"), f"{manifest_path}.fixtures[{index}].id"
        )
        artifact = _require_non_empty_string(
            entry.get("path"), f"{manifest_path}.fixtures[{index}].path"
        )
        expected_hash = _require_non_empty_string(
            entry.get("sha256"), f"{manifest_path}.fixtures[{index}].sha256"
        )
        if fixture_id in fixture_ids:
            raise ValidationError(f"{manifest_path}: duplicate fixture id {fixture_id}")
        artifact_path = _resolve_contained(
            fixture_root, artifact, f"{manifest_path}.fixtures[{index}].path"
        )
        if artifact_path in fixture_paths:
            raise ValidationError(f"{manifest_path}: duplicate fixture path {artifact}")
        if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            raise ValidationError(
                f"{manifest_path}: fixtures[{index}].sha256 must be lowercase SHA-256"
            )
        fixture_ids.add(fixture_id)
        fixture_paths.add(artifact_path)
        if not artifact_path.is_file():
            raise ValidationError(
                f"{manifest_path}: missing bundled artifact {artifact}"
            )
        actual_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise ValidationError(
                f"{manifest_path}: SHA-256 mismatch for bundled artifact {artifact}"
            )
        payload = _load_json(artifact_path)
        if not isinstance(payload, dict) or set(payload) not in (
            {"request", "expected"},
            {"request", "result"},
        ):
            raise ValidationError(
                f"{manifest_path}: bundled artifact {artifact} must contain "
                "exactly request and expected or result"
            )
        _validate_json(
            request_validator,
            payload["request"],
            f"{manifest_path}: {artifact}.request",
        )
        if "result" in payload:
            _validate_json(
                result_validator,
                payload["result"],
                f"{manifest_path}: {artifact}.result",
            )
        else:
            _validate_json(
                reference_validator,
                payload["expected"],
                f"{manifest_path}: {artifact}.expected",
            )


def main() -> int:
    """Validate all frontier fixture registry entries."""
    family_entries = _validate_registry()
    for entry in family_entries:
        manifest_path = _resolve_contained(
            FRONTIER_ROOT, cast("str", entry["path"]), "frontier family manifest"
        )
        if not manifest_path.is_file():
            raise ValidationError(f"missing frontier family manifest: {manifest_path}")
        if entry["manifest_kind"] == "bundled":
            _validate_bundled_family_manifest(manifest_path)
        else:
            _validate_family_manifest(manifest_path)

    print(f"validated {REGISTRY_MANIFEST.relative_to(REPO_ROOT)}")
    for entry in family_entries:
        print(f"validated {entry['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
