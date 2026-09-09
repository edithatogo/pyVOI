"""Capability descriptions and fail-closed backend selection."""

# pyright: reportExplicitAny=false

from __future__ import annotations

from collections.abc import Sequence  # noqa: TC003 - public protocol signature
from enum import StrEnum
from typing import Literal, Protocol

import numpy as np  # noqa: TC002 - public protocol signature
from numpy.typing import NDArray  # noqa: TC002 - public protocol signature
from pydantic import Field, field_serializer

from voiage.contracts.analysis import ContractModel, Identifier
from voiage.contracts.critical_invariants import capability_gaps


class Capability(StrEnum):
    """Stable backend capability identifiers."""

    DENSE_ARRAY = "dense-array"
    DETERMINISTIC = "deterministic"
    JIT = "jit"
    AUTODIFF = "autodiff"
    BATCHING = "batching"
    STREAMING = "streaming"
    FREE_THREADED = "free-threaded"
    ARROW_C_STREAM = "arrow-c-stream"


LiteralDtype = Literal["float32", "float64"]


class BackendCapabilities(ContractModel):
    """Machine-readable capabilities of one calculation backend."""

    backend_name: Identifier
    backend_version: str
    method_families: frozenset[Identifier]
    dtypes: frozenset[LiteralDtype]
    devices: frozenset[Identifier] = Field(min_length=1)
    features: frozenset[Capability] = frozenset()

    @field_serializer(
        "method_families", "dtypes", "devices", "features", when_used="json"
    )
    def serialize_sets(self, value: frozenset[object]) -> tuple[str, ...]:
        """Serialize descriptor sets in stable lexical order."""
        return tuple(sorted(str(item) for item in value))


class KernelRequirements(ContractModel):
    """Capabilities required to execute one kernel under a policy."""

    method_family: Identifier
    dtype: LiteralDtype
    device: Identifier | None = None
    required_features: frozenset[Capability] = frozenset()

    @field_serializer("required_features", when_used="json")
    def serialize_required_features(
        self, value: frozenset[Capability]
    ) -> tuple[str, ...]:
        """Serialize required feature sets in canonical order."""
        return tuple(sorted(item.value for item in value))


class CapabilityReport(ContractModel):
    """Explain whether a backend satisfies a kernel requirement."""

    backend_name: Identifier
    supported: bool
    missing: tuple[Identifier, ...] = ()


class CapabilityBackend(Protocol):
    """Minimal backend surface required by the generic dispatcher."""

    @property
    def capabilities(self) -> BackendCapabilities:
        """Return immutable capability metadata."""
        ...

    def calculate_evpi(self, net_benefits: NDArray[np.generic]) -> float:
        """Execute the EVPI pilot operation."""
        ...


class UnsupportedCapabilityError(ValueError):
    """Raised when no candidate backend satisfies a kernel contract."""


def evaluate_backend(
    backend: CapabilityBackend, requirements: KernelRequirements
) -> CapabilityReport:
    """Evaluate a backend without silently weakening requirements."""
    capabilities = backend.capabilities
    missing = capability_gaps(
        method_family=requirements.method_family,
        dtype=requirements.dtype,
        device=requirements.device,
        required_features=tuple(item.value for item in requirements.required_features),
        supported_methods=capabilities.method_families,
        supported_dtypes=capabilities.dtypes,
        supported_devices=capabilities.devices,
        supported_features=tuple(item.value for item in capabilities.features),
    )
    return CapabilityReport(
        backend_name=capabilities.backend_name,
        supported=not missing,
        missing=missing,
    )


def select_backend(
    backends: Sequence[CapabilityBackend], requirements: KernelRequirements
) -> CapabilityBackend:
    """Return the first capable backend or fail with complete evidence."""
    reports = tuple(evaluate_backend(item, requirements) for item in backends)
    for backend, report in zip(backends, reports, strict=True):
        if report.supported:
            return backend
    detail = "; ".join(
        f"{item.backend_name}: {', '.join(item.missing) or 'unavailable'}"
        for item in reports
    )
    raise UnsupportedCapabilityError(
        f"No backend satisfies kernel requirements ({detail or 'no candidates'})"
    )
