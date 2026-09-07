"""Contract checks for explicitly opt-in native telemetry qualification."""

from pathlib import Path


def test_telemetry_is_feature_off_by_default_and_bounded() -> None:
    cargo = Path("rust/crates/voiage-diagnostics/Cargo.toml").read_text()
    source = Path("rust/crates/voiage-diagnostics/src/otel_export.rs").read_text()
    assert "default = []" in cargo
    assert "max_retries must be <= 3" in source
    assert "dashboard" not in source.lower()
