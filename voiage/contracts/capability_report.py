"""Schema-bound, privacy-safe CLI capability report contract."""

from __future__ import annotations

from typing import Literal, cast

from pydantic import model_validator

from voiage.contracts.analysis import ContractModel, Identifier


class CliCapabilityReport(ContractModel):
    """Safe, deterministic capability report emitted by the CLI."""

    schema_version: Literal["1.0.0"] = "1.0.0"
    package_version: str
    backend: Identifier
    optional_modules: dict[Identifier, bool]
    methods: tuple[Identifier, ...]
    dispatch_methods: tuple[Identifier, ...]
    selected_method: Identifier | None = None
    dry_run: Literal[True] = True

    @model_validator(mode="before")
    @classmethod
    def normalize_sequences(cls, value: object) -> object:
        """Accept JSON arrays while retaining immutable internal sequences."""
        if isinstance(value, dict):
            normalized = {
                str(key): item
                for key, item in cast("dict[object, object]", value).items()
            }
            for key in ("methods", "dispatch_methods"):
                sequence = normalized.get(key)
                if isinstance(sequence, list):
                    normalized[key] = tuple(cast("list[object]", sequence))
            return normalized
        return value

    @model_validator(mode="after")
    def dispatch_matches_methods(self) -> CliCapabilityReport:
        """Reject reports that advertise an unregistered or hidden method."""
        if self.methods != self.dispatch_methods:
            raise ValueError("capability methods must match dispatch methods")
        return self
