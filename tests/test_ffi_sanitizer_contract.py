"""Fail-closed contract for Linux C ABI sanitizer evidence."""

from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_sanitizer_workflow_is_separate_and_fail_closed() -> None:
    workflow = (ROOT / ".github/workflows/ffi-sanitizers.yml").read_text()

    assert "ubuntu-24.04" in workflow
    assert "permissions: {}" in workflow
    assert re.search(r"toolchain: nightly-\d{4}-\d{2}-\d{2}", workflow)
    assert "bash scripts/run_ffi_sanitizers.sh" in workflow
    assert "continue-on-error" not in workflow
    assert "C consumer ASan UBSan LSan with ASan-instrumented Rust" in workflow
    assert "Rust ABI ASan UBSan LSan" not in workflow


def test_runner_instruments_rust_and_real_c_consumer() -> None:
    runner = (ROOT / "scripts/run_ffi_sanitizers.sh").read_text()

    required_contract = (
        "set -euo pipefail",
        "-Zsanitizer=address",
        "-Zbuild-std",
        "__asan_",
        "-fsanitize=address,undefined",
        "detect_leaks=1",
        "halt_on_error=1",
        "voiage_v1_sanitizer_smoke.c",
    )
    for marker in required_contract:
        assert marker in runner


def test_consumer_pairs_every_successful_handle_and_allocation() -> None:
    consumer = (ROOT / "tests/ffi/voiage_v1_sanitizer_smoke.c").read_text()

    assert "voiage_v1_handle_create(&handle)" in consumer
    assert "voiage_v1_handle_free(handle)" in consumer
    assert "voiage_v1_error_message" in consumer
    assert "malloc" in consumer
    assert "free(message)" in consumer


def test_public_c_consumer_compiles_against_the_versioned_header() -> None:
    """A deliberately independent C consumer freezes the additive ABI surface."""
    compiler = shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")
    assert compiler is not None, "a C compiler is required for the ABI witness"
    fixture = ROOT / "tests/fixtures/compatibility_witnesses/voiage_v1_consumer.c"
    header_dir = ROOT / "rust/crates/voiage-ffi/include"
    result = subprocess.run(
        [compiler, "-std=c11", "-Werror", "-fsyntax-only", "-I", str(header_dir), str(fixture)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
