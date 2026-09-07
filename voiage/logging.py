"""Structured, application-owned logging for VOIAGE."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
import logging
import os
import pathlib  # noqa: TC003 - Pydantic resolves this annotation at runtime
import re
import secrets
import sys
from typing import TYPE_CHECKING, ClassVar, TypeVar, cast, final, override
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from voiage.assurance_policy import is_sensitive_log_key

if TYPE_CHECKING:
    from collections.abc import Generator

    from voiage.contracts.analysis import AnalysisResult, ContractModel

PayloadT = TypeVar("PayloadT", bound="ContractModel")

_OWNED_HANDLER = "_voiage_handler"
_RESERVED_FIELDS = frozenset(
    {
        "analysis_id",
        "backend_requested",
        "backend_selected",
        "exception",
        "fallback_code",
        "level",
        "logger",
        "message",
        "numerical_policy_id",
        "run_id",
        "service",
        "span_id",
        "timestamp",
        "trace_flags",
        "trace_id",
        "traceparent",
    }
)
_TRACE_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_SPAN_ID_RE = re.compile(r"^[0-9a-f]{16}$")
_TRACE_FLAGS_RE = re.compile(r"^[0-9a-f]{2}$")
_BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
_QUERY_CREDENTIAL_RE = re.compile(
    "".join(
        (
            r"(?i)([?&](?:access[_-]?key|api[_-]?key|authorization|cookie|credential|",
            r"jwt|passphrase|password|private[_-]?key|secret|session(?:[_-]?id)?|",
            r"sig(?:nature)?|token)=)([^&#\s]+)",
        )
    )
)
_ABSOLUTE_PATH_RE = re.compile(r"(?:/Users|/home|/private|[A-Za-z]:\\)[^\s,;]+")
_ASSIGNMENT_RE = re.compile(
    "".join(
        (
            r"(?i)\b(access[_-]?key|api[_-]?key|authorization|cookie|credential|jwt|",
            r"passphrase|password|private[_-]?key|secret|session(?:[_-]?id)?|",
            r"sig(?:nature)?|token)\s*([:=])\s*([^\s,;]+)",
        )
    )
)


@dataclass(frozen=True, slots=True)
class _LogContextState:
    run_id: str | None
    correlation: Mapping[str, object]
    fields: Mapping[str, object]


_CONTEXT: ContextVar[_LogContextState | None] = ContextVar(
    "voiage_log_context", default=None
)


def _current_context() -> _LogContextState:
    return _CONTEXT.get() or _LogContextState(run_id=None, correlation={}, fields={})


def _redact_text(value: str) -> str:
    value = _BEARER_RE.sub("Bearer [REDACTED]", value)
    value = _JWT_RE.sub("[REDACTED]", value)
    value = _QUERY_CREDENTIAL_RE.sub(r"\1[REDACTED]", value)
    value = _ASSIGNMENT_RE.sub(r"\1\2[REDACTED]", value)
    return _ABSOLUTE_PATH_RE.sub("[PATH_REDACTED]", value)


def _sensitive_key(key: str) -> bool:
    return is_sensitive_log_key(key)


def _redact_value(value: object) -> object:
    if isinstance(value, Mapping):
        items = cast("Mapping[object, object]", value)
        return {
            str(key): "[REDACTED]" if _sensitive_key(str(key)) else _redact_value(item)
            for key, item in items.items()
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_redact_value(item) for item in cast("Iterable[object]", value)]
    if isinstance(value, str):
        return _redact_text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _redact_text(str(value))


def _safe_context(values: Mapping[str, object]) -> dict[str, object]:
    """Recursively redact context and reject trusted-field impersonation."""
    reserved = sorted(_RESERVED_FIELDS.intersection(values))
    if reserved:
        raise ValueError(f"reserved logging context field: {reserved[0]}")
    return {
        key: "[REDACTED]" if _sensitive_key(key) else _redact_value(value)
        for key, value in values.items()
    }


class TraceContext(BaseModel):
    """W3C Trace Context identifiers shared by VOP and VOIAGE."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    trace_id: str = Field(default_factory=lambda: secrets.token_hex(16))
    span_id: str = Field(default_factory=lambda: secrets.token_hex(8))
    trace_flags: str = "00"

    @field_validator("trace_id")
    @classmethod
    def validate_trace_id(cls, value: str) -> str:
        """Require a lowercase non-zero 128-bit trace identifier."""
        if _TRACE_ID_RE.fullmatch(value) is None or value == "0" * 32:
            raise ValueError("trace_id must be 32 lowercase non-zero hex characters")
        return value

    @field_validator("span_id")
    @classmethod
    def validate_span_id(cls, value: str) -> str:
        """Require a lowercase non-zero 64-bit span identifier."""
        if _SPAN_ID_RE.fullmatch(value) is None or value == "0" * 16:
            raise ValueError("span_id must be 16 lowercase non-zero hex characters")
        return value

    @field_validator("trace_flags")
    @classmethod
    def validate_trace_flags(cls, value: str) -> str:
        """Require the two-digit W3C trace flags value."""
        if _TRACE_FLAGS_RE.fullmatch(value) is None:
            raise ValueError("trace_flags must be two lowercase hex characters")
        return value

    @property
    def traceparent(self) -> str:
        """Return the canonical W3C traceparent header value."""
        return f"00-{self.trace_id}-{self.span_id}-{self.trace_flags}"


class AnalysisLogContext(BaseModel):
    """Trusted shared correlation fields for one analysis execution."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    run_id: str = Field(min_length=1)
    trace: TraceContext = Field(default_factory=TraceContext)
    analysis_id: str = Field(min_length=1)
    backend_requested: str = Field(min_length=1)
    backend_selected: str = Field(min_length=1)
    fallback_code: str = Field(min_length=1)
    numerical_policy_id: str = Field(pattern=r"^[0-9a-f]{64}$")

    def correlation_fields(self) -> dict[str, str]:
        """Project immutable identifiers to the shared structured-log shape."""
        return {
            "analysis_id": self.analysis_id,
            "backend_requested": self.backend_requested,
            "backend_selected": self.backend_selected,
            "fallback_code": self.fallback_code,
            "numerical_policy_id": self.numerical_policy_id,
            "trace_id": self.trace.trace_id,
            "span_id": self.trace.span_id,
            "trace_flags": self.trace.trace_flags,
            "traceparent": self.trace.traceparent,
        }


def numerical_policy_digest(policy: BaseModel | Mapping[str, object]) -> str:
    """Return a deterministic identifier without logging policy values."""
    value: object = (
        policy.model_dump(mode="json") if isinstance(policy, BaseModel) else policy
    )
    encoded = json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode()
    return sha256(encoded).hexdigest()


class LoggingSettings(BaseModel):
    """Pydantic-v2 validated logging settings."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid", frozen=True, defer_build=True
    )
    level: str = "ERROR"
    json_output: bool = False
    console: bool = True
    log_file: pathlib.Path | None = None
    service: str = "voiage"
    run_id: str = Field(default_factory=lambda: uuid4().hex)

    @field_validator("level")
    @classmethod
    def validate_level(cls, value: str) -> str:
        """Normalize and validate a standard-library logging level."""
        normalized = value.upper()
        if normalized not in logging.getLevelNamesMapping():
            raise ValueError(f"unknown logging level: {value}")
        return normalized

    @classmethod
    def from_environment(cls, **overrides: object) -> LoggingSettings:
        """Load the stable ``VOIAGE_LOG_*`` environment contract."""
        values: dict[str, object] = {
            "level": os.getenv("VOIAGE_LOG_LEVEL", "ERROR"),
            "json_output": os.getenv("VOIAGE_LOG_FORMAT", "human").lower() == "json",
            "run_id": os.getenv("VOIAGE_RUN_ID") or uuid4().hex,
        }
        values.update(overrides)
        return cls.model_validate(values)


class BoundedLogQueue:
    """Bounded, non-blocking queue with deterministic severity-aware loss."""

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self._items: deque[tuple[int, str]] = deque(maxlen=capacity)
        self._capacity = capacity
        self.dropped = 0

    def put(self, level: int, message: str) -> bool:
        """Add an event without blocking, dropping lower-severity entries first."""
        if len(self._items) < self._capacity:
            self._items.append((level, message))
            return True
        if level >= logging.ERROR:
            for index, (queued_level, _) in enumerate(self._items):
                if queued_level < logging.ERROR:
                    del self._items[index]
                    self._items.append((level, message))
                    self.dropped += 1
                    return True
        self.dropped += 1
        return False

    def get(self) -> tuple[int, str] | None:
        """Remove and return the oldest queued event."""
        return self._items.popleft() if self._items else None


@final
class _ContextFilter(logging.Filter):
    def __init__(self, settings: LoggingSettings) -> None:
        super().__init__()
        self.settings: LoggingSettings = settings

    @override
    def filter(self, record: logging.LogRecord) -> bool:
        state = _current_context()
        record.service = self.settings.service
        record.run_id = state.run_id or self.settings.run_id
        record.correlation = dict(state.correlation)
        record.context = dict(state.fields)
        return True


@final
class RedactingFormatter(logging.Formatter):
    """Apply credential redaction to human-readable log messages."""

    @override
    def format(self, record: logging.LogRecord) -> str:
        """Format and scrub one human-readable record."""
        return _redact_text(super().format(record))


@final
class JsonFormatter(logging.Formatter):
    """Emit newline-delimited JSON for CI and observability systems."""

    @override
    def format(self, record: logging.LogRecord) -> str:
        """Serialize one log record without relying on global state."""
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "service": getattr(record, "service", "voiage"),
            "run_id": getattr(record, "run_id", None),
            "message": _redact_text(record.getMessage()),
        }
        payload.update(getattr(record, "correlation", {}))
        payload.update(getattr(record, "context", {}))
        if record.exc_info:
            payload["exception"] = _redact_text(self.formatException(record.exc_info))
        return json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)


@contextmanager
def log_context(**values: object) -> Generator[None]:
    """Bind context for the current thread, task, or async execution path."""
    current = _current_context()
    state = _LogContextState(
        run_id=current.run_id,
        correlation=current.correlation,
        fields={**current.fields, **_safe_context(values)},
    )
    token = _CONTEXT.set(state)
    try:
        yield
    finally:
        _CONTEXT.reset(token)


@contextmanager
def analysis_log_context(context: AnalysisLogContext) -> Generator[None]:
    """Bind trusted run, trace, backend, fallback and policy correlation."""
    current = _current_context()
    state = _LogContextState(
        run_id=context.run_id,
        correlation=context.correlation_fields(),
        fields=current.fields,
    )
    token = _CONTEXT.set(state)
    try:
        yield
    finally:
        _CONTEXT.reset(token)


def analysis_log_context_from_result[PayloadT: "ContractModel"](
    result: AnalysisResult[PayloadT], *, trace: TraceContext | None = None
) -> AnalysisLogContext:
    """Adapt a VOIAGE analysis envelope to the shared logging contract."""
    requested = (
        result.run_context.requested_backend or result.run_context.selected_backend
    )
    fallback_used = (
        requested != result.run_context.selected_backend
        or "backend-fallback" in result.diagnostics.degraded_paths
    )
    fallback = "none"
    if fallback_used:
        fallback = next(
            (
                warning.code
                for warning in result.diagnostics.warnings
                if warning.code == "backend_fallback"
            ),
            "backend_fallback",
        )
    return AnalysisLogContext(
        run_id=result.run_context.run_id,
        trace=trace or TraceContext(),
        analysis_id=result.analysis_id,
        backend_requested=requested,
        backend_selected=result.run_context.selected_backend,
        fallback_code=fallback,
        numerical_policy_id=numerical_policy_digest(result.numerical_policy),
    )


def configure_logging(settings: LoggingSettings | None = None) -> logging.Logger:
    """Configure VOIAGE-owned handlers without disturbing host applications."""
    settings = settings or LoggingSettings.from_environment()
    logger = logging.getLogger("voiage")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    for handler in tuple(logger.handlers):
        if getattr(handler, _OWNED_HANDLER, False):
            logger.removeHandler(handler)
            handler.close()

    context_filter = _ContextFilter(settings)
    human = RedactingFormatter("%(levelname)s:%(name)s:%(message)s [run_id=%(run_id)s]")
    formatter: logging.Formatter = JsonFormatter() if settings.json_output else human
    if settings.console:
        console = logging.StreamHandler(sys.stderr)
        console.setLevel(settings.level)
        console.setFormatter(formatter)
        console.addFilter(context_filter)
        setattr(console, _OWNED_HANDLER, True)
        logger.addHandler(console)
    if settings.log_file is not None:
        settings.log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            settings.log_file, mode="a", encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JsonFormatter())
        file_handler.addFilter(context_filter)
        setattr(file_handler, _OWNED_HANDLER, True)
        logger.addHandler(file_handler)
    logger.info("logging_configured")
    return logger
