"""Contract checks for optional native structured diagnostics."""

from pathlib import Path


def test_native_telemetry_is_application_owned_and_optional() -> None:
    cargo = Path("rust/crates/voiage-diagnostics/Cargo.toml").read_text()
    source = Path("rust/crates/voiage-diagnostics/src/telemetry.rs").read_text()
    assert 'tracing = { version = "0.1", default-features = false }' in cargo
    assert "global_default" not in source
    assert "voiage.diagnostic" in source


def test_python_bridge_exports_host_owned_diagnostic_event() -> None:
    source = Path("rust/crates/voiage-python/src/lib.rs").read_text()
    assert "fn emit_diagnostic(" in source
    assert "Correlation::new(run_id, analysis_id)" in source
    assert "wrap_pyfunction!(emit_diagnostic, module)" in source
