"""Black-box provider-SDK consumer evidence using a real installed wheel."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONSUMER_PACKAGE = ROOT / "tests/fixtures/provider_sdk_wheel_consumer"


def test_consumer_cache_is_isolated_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("VOIAGE_TEST_UV_CACHE_DIR", raising=False)
    monkeypatch.setenv("UV_CACHE_DIR", "/unavailable-host-cache")
    environment = _consumer_environment(tmp_path)
    assert environment["UV_CACHE_DIR"] == str(tmp_path / "uv-cache")
    assert environment["UV_LINK_MODE"] == "copy"


def test_consumer_cache_reuse_requires_explicit_writable_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = tmp_path / "shared-downloads"
    cache.mkdir()
    monkeypatch.setenv("VOIAGE_TEST_UV_CACHE_DIR", str(cache))
    environment = _consumer_environment(tmp_path)
    assert environment["UV_CACHE_DIR"] == str(cache)
    assert environment["UV_LINK_MODE"] == "copy"


@pytest.mark.parametrize("invalid_kind", ["missing", "file", "unwritable"])
def test_consumer_cache_rejects_invalid_explicit_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, invalid_kind: str
) -> None:
    cache = tmp_path / "invalid-cache"
    if invalid_kind == "file":
        cache.touch()
    elif invalid_kind == "unwritable":
        cache.mkdir()
        monkeypatch.setattr(os, "access", lambda *_args: False)
    monkeypatch.setenv("VOIAGE_TEST_UV_CACHE_DIR", str(cache))
    with pytest.raises(ValueError, match="writable directory"):
        _consumer_environment(tmp_path)


def test_consumer_subprocess_is_bounded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_run(
        command: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        assert kwargs["timeout"] == 1200
        assert kwargs["capture_output"] is True
        return subprocess.CompletedProcess(command, 0, "boundary passed", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert _run(["probe"], cwd=tmp_path, env={}) == "boundary passed"


def _consumer_environment(tmp_path: Path) -> dict[str, str]:
    """Keep isolation by default; reuse only an explicitly selected cache."""
    environment = os.environ.copy()
    selected_cache = environment.pop("VOIAGE_TEST_UV_CACHE_DIR", None)
    cache_dir = tmp_path / "uv-cache"
    if selected_cache:
        cache_dir = Path(selected_cache).expanduser().resolve()
        if not cache_dir.is_dir() or not os.access(cache_dir, os.W_OK):
            raise ValueError("VOIAGE_TEST_UV_CACHE_DIR must be a writable directory")
    environment["UV_CACHE_DIR"] = str(cache_dir)
    environment["UV_LINK_MODE"] = "copy"
    return environment


def _run(command: list[str], *, cwd: Path, env: dict[str, str]) -> str:
    """Run one build/install boundary with its diagnostic retained by pytest."""
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        # Cold isolated installs may resolve the scientific dependency graph on
        # constrained runners; retain a finite bound.
        timeout=1200,
    )
    assert result.returncode == 0, (
        f"command failed: {' '.join(command)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    return result.stdout


@pytest.mark.integration
def test_external_provider_wheel_discovers_only_after_explicit_opt_in(
    tmp_path: Path,
) -> None:
    """A separately installed package uses only frozen public SDK surfaces."""
    uv = shutil.which("uv")
    assert uv is not None, "the wheel-consumer contract requires uv"
    # A host-specific UV_CACHE_DIR must not silently alter clean-runner behavior.
    # Explicit cache reuse changes downloads only, never the fresh environment.
    environment = _consumer_environment(tmp_path)

    voiage_dist = tmp_path / "voiage-dist"
    consumer_dist = tmp_path / "consumer-dist"
    _run(
        [uv, "build", "--wheel", "--out-dir", str(voiage_dist)],
        cwd=ROOT,
        env=environment,
    )
    _run(
        [uv, "build", "--wheel", "--out-dir", str(consumer_dist)],
        cwd=CONSUMER_PACKAGE,
        env=environment,
    )

    environment_dir = tmp_path / "consumer-venv"
    _run(
        [uv, "venv", "--python", sys.executable, str(environment_dir)],
        cwd=tmp_path,
        env=environment,
    )
    interpreter = environment_dir / "bin/python"
    _run(
        [
            uv,
            "pip",
            "install",
            "--python",
            str(interpreter),
            str(next(voiage_dist.glob("*.whl"))),
            str(next(consumer_dist.glob("*.whl"))),
        ],
        cwd=tmp_path,
        env=environment,
    )

    (tmp_path / "data.csv").write_text("value\n1\n", encoding="utf-8")
    descriptor = tmp_path / "example.json"
    descriptor.write_text(
        json.dumps({"voiage_wheel_example": "1", "resource": "data.csv"}),
        encoding="utf-8",
    )
    probe = "\n".join(
        (
            "import json, sys",
            "from pathlib import Path",
            "import voiage.ingestion",
            "assert 'voiage_sdk_wheel_consumer' not in sys.modules",
            "from voiage.ingestion import (ProviderRegistry, SourceAccessPolicy, discover_entry_point_providers)",
            "providers = discover_entry_point_providers(allowlist={'example-wheel'})",
            "assert len(providers) == 1",
            "bundle = ProviderRegistry(providers).ingest(Path('example.json'), policy=SourceAccessPolicy(Path('.')))",
            "print(json.dumps({'provider_id': bundle.manifest.provenance.provider_id, 'rows': bundle.table('data').to_pylist()}))",
        )
    )
    output = _run(
        [str(interpreter), "-I", "-c", probe],
        cwd=tmp_path,
        env=environment,
    )

    assert json.loads(output) == {
        "provider_id": "example-wheel-provider",
        "rows": [{"value": 1}],
    }
