"""Comprehensive tests for the CLI implementation."""

import csv
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest
from typer.main import get_command
from typer.testing import CliRunner

from voiage import cli

runner = CliRunner()


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _compact(text: str) -> str:
    for char in "│╭╮╰╯─":
        text = text.replace(char, " ")
    return " ".join(text.split())


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)


def test_evpi_cli() -> None:
    """Test the EVPI CLI command with various options."""
    # Create temporary files for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create sample net benefits data
        net_benefits_file = tmpdir_path / "net_benefits.csv"
        net_benefits_data = [
            ["Strategy A", "Strategy B"],
            [1000, 1200],
            [950, 1250],
            [1050, 1150],
            [900, 1300],
            [1100, 1100],
        ]

        with open(net_benefits_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(net_benefits_data)

        # Test basic EVPI calculation
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "voiage.cli",
                "calculate-evpi",
                str(net_benefits_file),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "EVPI:" in result.stdout
        evpi_value = float(result.stdout.split(":")[1].strip())
        assert evpi_value >= 0

        # Test EVPI with population scaling
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "voiage.cli",
                "calculate-evpi",
                str(net_benefits_file),
                "--population",
                "100000",
                "--time-horizon",
                "10",
                "--discount-rate",
                "0.03",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "EVPI:" in result.stdout
        scaled_evpi_value = float(result.stdout.split(":")[1].strip())
        assert scaled_evpi_value >= 0
        # Scaled EVPI should be larger than unscaled
        assert scaled_evpi_value >= evpi_value

        # Test EVPI with output file
        output_file = tmpdir_path / "evpi_result.txt"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "voiage.cli",
                "calculate-evpi",
                str(net_benefits_file),
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "EVPI:" in result.stdout
        assert "Result saved to" in result.stdout
        assert output_file.exists()

        # Check output file content
        with open(output_file) as f:
            content = f.read().strip()
            assert "EVPI:" in content


def test_cli_output_format_option(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise the CLI-wide output format option."""
    net_benefits_file = tmp_path / "net_benefits.csv"
    with open(net_benefits_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(
            [
                ["Strategy A", "Strategy B"],
                [1000, 1200],
                [950, 1250],
            ]
        )

    json_result = runner.invoke(
        cli.app,
        ["--format", "json", "calculate-evpi", str(net_benefits_file)],
    )

    assert json_result.exit_code == 0
    payload = json.loads(json_result.stdout)
    assert payload["command"] == "calculate-evpi"
    assert payload["metric"] == "EVPI"
    assert isinstance(payload["value"], float)
    assert payload["reporting"]["reporting_standard"] == "CHEERS-VOI"
    assert payload["reporting"]["analysis_type"] == "calculate-evpi"

    json_output_file = tmp_path / "evpi.json"
    json_file_result = runner.invoke(
        cli.app,
        [
            "--format",
            "json",
            "calculate-evpi",
            str(net_benefits_file),
            "--output",
            str(json_output_file),
        ],
    )

    assert json_file_result.exit_code == 0
    assert json.loads(json_output_file.read_text(encoding="utf-8"))["command"] == (
        "calculate-evpi"
    )

    csv_result = runner.invoke(
        cli.app,
        ["--format", "csv", "calculate-evpi", str(net_benefits_file)],
    )

    assert csv_result.exit_code == 0
    rows = list(csv.DictReader(csv_result.stdout.splitlines()))
    assert len(rows) == 1
    assert rows[0]["command"] == "calculate-evpi"
    assert rows[0]["metric"] == "EVPI"
    assert rows[0]["value"]

    portfolio_file = tmp_path / "portfolio.json"
    _write_json(
        portfolio_file,
        {
            "budget_constraint": 120,
            "optimization_method": "dynamic_programming",
            "studies": [
                {
                    "name": "Study Alpha",
                    "cost": 50,
                    "value": 100,
                    "design": {"arms": [{"name": "Arm A", "sample_size": 10}]},
                },
                {
                    "name": "Study Beta",
                    "cost": 60,
                    "value": 90,
                    "design": {"arms": [{"name": "Arm B", "sample_size": 12}]},
                },
            ],
        },
    )

    portfolio_csv = runner.invoke(
        cli.app,
        ["--format", "csv", "calculate-portfolio-voi", str(portfolio_file)],
    )

    assert portfolio_csv.exit_code == 0
    portfolio_rows = list(csv.DictReader(portfolio_csv.stdout.splitlines()))
    assert portfolio_rows[0]["command"] == "calculate-portfolio-voi"
    assert portfolio_rows[0]["selected_studies"]

    surface_file = tmp_path / "surface.json"
    _write_json(
        surface_file,
        {
            "strategy_names": ["Strategy A", "Strategy B"],
            "wtp_thresholds": [0, 50000],
            "net_benefit": [
                [[10, 15], [12, 14]],
                [[11, 16], [13, 15]],
            ],
        },
    )

    plot_result = runner.invoke(
        cli.app, ["--format", "json", "plot-ceac", str(surface_file)]
    )

    assert plot_result.exit_code == 0
    plot_payload = json.loads(plot_result.stdout)
    assert plot_payload["command"] == "plot-ceac"
    assert plot_payload["saved"] is False

    plot_csv = runner.invoke(
        cli.app, ["--format", "csv", "plot-ceac", str(surface_file)]
    )
    assert plot_csv.exit_code == 0
    plot_csv_rows = list(csv.DictReader(plot_csv.stdout.splitlines()))
    assert plot_csv_rows[0]["command"] == "plot-ceac"
    assert plot_csv_rows[0]["output_file"] == ""

    preference_surface = tmp_path / "preference.json"
    _write_json(
        preference_surface,
        {
            "net_benefit": [
                [[10.0, 7.0], [8.0, 11.0]],
                [[10.0, 7.0], [8.0, 11.0]],
            ],
            "strategy_names": ["Strategy A", "Strategy B"],
            "preference_profiles": [
                {
                    "id": "access_first",
                    "label": "Access first",
                    "weight": 0.5,
                },
                {
                    "id": "outcomes_first",
                    "label": "Outcomes first",
                    "weight": 0.5,
                },
            ],
            "reference_preference_profile": "access_first",
        },
    )

    preference_json = runner.invoke(
        cli.app,
        ["--format", "json", "calculate-preference", str(preference_surface)],
    )
    assert preference_json.exit_code == 0
    preference_payload = json.loads(preference_json.stdout)
    assert preference_payload["command"] == "calculate-preference"
    assert preference_payload["analysis_type"] == "value_of_preference_information"
    assert preference_payload["method_maturity"] == "fixture-backed"
    assert preference_payload["individualized_care_value"] >= 0
    assert preference_payload["reporting"]["reporting_standard"] == "CHEERS-VOI"

    preference_csv = runner.invoke(
        cli.app,
        ["--format", "csv", "calculate-preference", str(preference_surface)],
    )
    assert preference_csv.exit_code == 0
    preference_rows = list(csv.DictReader(preference_csv.stdout.splitlines()))
    assert len(preference_rows) == 1
    assert preference_rows[0]["command"] == "calculate-preference"
    assert preference_rows[0]["metric"] == "Value of Preference"
    assert preference_rows[0]["method_maturity"] == "fixture-backed"
    assert preference_rows[0]["value"]

    parameter_file = tmp_path / "parameters.csv"
    parameter_file.write_text("x\n1\n2\n", encoding="utf-8")
    trial_design_file = tmp_path / "trial_design.json"
    _write_json(trial_design_file, {"arms": [{"name": "Arm A", "sample_size": 5}]})

    monkeypatch.setattr(cli, "import_callable", lambda _: lambda _: object())
    monkeypatch.setattr(cli, "evsi", lambda **kwargs: 5.5)

    evsi_output = tmp_path / "evsi_result.json"
    evsi_result = runner.invoke(
        cli.app,
        [
            "--format",
            "json",
            "calculate-evsi",
            str(parameter_file),
            str(trial_design_file),
            "--model",
            "dummy.module:callable",
            "--output",
            str(evsi_output),
        ],
    )

    assert evsi_result.exit_code == 0
    evsi_payload = json.loads(evsi_output.read_text(encoding="utf-8"))
    assert evsi_payload["command"] == "calculate-evsi"
    assert evsi_payload["value"] == 5.5
    assert evsi_payload["reporting"]["reporting_standard"] == "CHEERS-VOI"

    nma_file = tmp_path / "nma.json"
    _write_json(
        nma_file,
        {
            "study_data": [{"study_id": 1}],
            "treatment_effects": {"A-B": [0.1, 0.2, 0.3]},
        },
    )

    monkeypatch.setattr(
        cli.np.random, "rand", lambda n_samples: np.linspace(0.0, 1.0, n_samples)
    )
    monkeypatch.setattr(cli, "calculate_nma_evpi", lambda *args, **kwargs: 2.5)
    monkeypatch.setattr(cli, "calculate_nma_evppi", lambda *args, **kwargs: 1.25)

    nma_output = tmp_path / "nma_result.json"
    nma_result = runner.invoke(
        cli.app,
        [
            "--format",
            "json",
            "calculate-nma-voi",
            str(nma_file),
            "--parameters-of-interest",
            "hazard_ratio,cost_offset",
            "--willingness-to-pay",
            "25000",
            "--output",
            str(nma_output),
        ],
    )

    assert nma_result.exit_code == 0
    nma_payload = json.loads(nma_output.read_text(encoding="utf-8"))
    assert nma_payload["command"] == "calculate-nma-voi"
    assert nma_payload["metric"] == "NMA-EVPPI"


def test_cli_quiet_option(tmp_path: Path) -> None:
    """Exercise the CLI-wide quiet option."""
    net_benefits_file = tmp_path / "net_benefits.csv"
    with open(net_benefits_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(
            [
                ["Strategy A", "Strategy B"],
                [1000, 1200],
                [950, 1250],
            ]
        )

    output_file = tmp_path / "evpi.txt"
    result = runner.invoke(
        cli.app,
        [
            "--quiet",
            "calculate-evpi",
            str(net_benefits_file),
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert result.stdout.strip().startswith("EVPI:")
    assert "Result saved to" not in result.stdout
    assert output_file.read_text(encoding="utf-8").strip().startswith("EVPI:")


def test_cli_verbose_option(tmp_path: Path) -> None:
    """Exercise the CLI-wide verbose option."""
    net_benefits_file = tmp_path / "net_benefits.csv"
    with open(net_benefits_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(
            [
                ["Strategy A", "Strategy B"],
                [1000, 1200],
                [950, 1250],
            ]
        )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "voiage.cli",
            "--verbose",
            "--format",
            "json",
            "calculate-evpi",
            str(net_benefits_file),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["command"] == "calculate-evpi"
    assert "DEBUG:voiage.cli:calculate-evpi" in result.stderr


def test_generate_config_command(tmp_path: Path) -> None:
    """Exercise the CLI config generation command."""
    output_file = tmp_path / "evsi_config.json"
    result = runner.invoke(
        cli.app,
        ["generate-config", "evsi", "--output", str(output_file)],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["command"] == "calculate-evsi"
    assert payload["method"] == "two_loop"
    assert output_file.exists()
    assert json.loads(output_file.read_text(encoding="utf-8"))["command"] == (
        "calculate-evsi"
    )


def test_generate_config_command_rejects_unknown_template() -> None:
    """Exercise invalid config template handling."""
    result = runner.invoke(cli.app, ["generate-config", "bogus"])

    assert result.exit_code == 1
    assert "Unknown config template" in result.stderr


def test_evppi_cli() -> None:
    """Test the EVPPI CLI command with various options."""
    # Create temporary files for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create sample net benefits data
        net_benefits_file = tmpdir_path / "net_benefits.csv"
        net_benefits_data = [
            ["Strategy A", "Strategy B"],
            [1000, 1200],
            [950, 1250],
            [1050, 1150],
            [900, 1300],
            [1100, 1100],
        ]

        with open(net_benefits_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(net_benefits_data)

        # Create sample parameters data
        parameters_file = tmpdir_path / "parameters.csv"
        parameters_data = [
            ["param1", "param2"],
            [0.5, 0.3],
            [0.6, 0.4],
            [0.4, 0.2],
            [0.7, 0.5],
            [0.5, 0.3],
        ]

        with open(parameters_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(parameters_data)

        # Test basic EVPPI calculation
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "voiage.cli",
                "calculate-evppi",
                str(net_benefits_file),
                str(parameters_file),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "EVPPI:" in result.stdout
        evppi_value = float(result.stdout.split(":")[1].strip())
        assert evppi_value >= 0

        # Test EVPPI with population scaling
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "voiage.cli",
                "calculate-evppi",
                str(net_benefits_file),
                str(parameters_file),
                "--population",
                "100000",
                "--time-horizon",
                "10",
                "--discount-rate",
                "0.03",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "EVPPI:" in result.stdout
        scaled_evppi_value = float(result.stdout.split(":")[1].strip())
        assert scaled_evppi_value >= 0

        # Test EVPPI with output file
        output_file = tmpdir_path / "evppi_result.txt"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "voiage.cli",
                "calculate-evppi",
                str(net_benefits_file),
                str(parameters_file),
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "EVPPI:" in result.stdout
        assert "Result saved to" in result.stdout
        assert output_file.exists()

        # Check output file content
        with open(output_file) as f:
            content = f.read().strip()
            assert "EVPPI:" in content


def test_cli_help() -> None:
    """Test CLI help commands."""
    runner = CliRunner()

    # Test main help
    result = runner.invoke(cli.app, ["--help"])

    assert result.exit_code == 0
    assert "voiage" in result.stdout
    assert "calculate-evpi" in result.stdout
    assert "calculate-evppi" in result.stdout
    assert "calculate-evsi" in result.stdout
    assert "calculate-enbs" in result.stdout
    assert "calculate-ceaf" in result.stdout
    assert "calculate-dominance" in result.stdout
    assert "calculate-adaptive-evsi" in result.stdout
    assert "calculate-portfolio-voi" in result.stdout
    assert "calculate-sequential-voi" in result.stdout
    assert "calculate-perspective" in result.stdout
    assert "calculate-preference" in result.stdout
    assert "calculate-validation" in result.stdout
    assert "calculate-threshold" in result.stdout
    assert "plot-perspective-regret" in result.stdout
    assert "generate-config" in result.stdout
    assert "Options" in result.stdout
    assert "Commands" in result.stdout

    # Test calculate-evpi help
    result = runner.invoke(cli.app, ["calculate-evpi", "--help"])

    assert result.exit_code == 0
    assert "calculate-evpi" in result.stdout
    assert "NET_BENEFIT_FILE" in result.stdout

    # Test calculate-evppi help
    result = runner.invoke(cli.app, ["calculate-evppi", "--help"])

    assert result.exit_code == 0
    stdout = _strip_ansi(result.stdout)
    assert "calculate-evppi" in stdout
    assert "NET_BENEFIT_FILE" in stdout
    assert "PARAMETER_FILE" in stdout

    result = runner.invoke(cli.app, ["calculate-evsi", "--help"])

    assert result.exit_code == 0
    stdout = _strip_ansi(result.stdout)
    assert "calculate-evsi" in stdout
    assert "PARAMETER_FILE" in stdout
    assert "TRIAL_DESIGN_FILE" in stdout

    result = runner.invoke(cli.app, ["calculate-enbs", "--help"])

    assert result.exit_code == 0
    stdout = _strip_ansi(result.stdout)
    assert "calculate-enbs" in stdout
    assert "Calculate ENBS from an EVSI value and research cost" in stdout
    assert "--research-cost" in stdout

    result = runner.invoke(cli.app, ["calculate-adaptive-evsi", "--help"])

    assert result.exit_code == 0
    stdout = _strip_ansi(result.stdout)
    assert "calculate-adaptive-evsi" in stdout
    assert "--adaptive-rules" in stdout

    result = runner.invoke(cli.app, ["calculate-portfolio-voi", "--help"])

    assert result.exit_code == 0
    stdout = _strip_ansi(result.stdout)
    assert "calculate-portfolio-voi" in stdout

    result = runner.invoke(cli.app, ["calculate-sequential-voi", "--help"])

    assert result.exit_code == 0
    stdout = _strip_ansi(result.stdout)
    assert "calculate-sequential-voi" in stdout
    assert "--optimization-method" in stdout

    result = runner.invoke(cli.app, ["generate-config", "--help"])

    assert result.exit_code == 0
    stdout = _strip_ansi(result.stdout)
    assert "generate-config" in stdout
    assert "evsi_config.json" in stdout

    help_checks = [
        ["calculate-evpi", "voiage calculate-evpi net_benefits.csv"],
        [
            "calculate-evppi",
            "voiage calculate-evppi net_benefits.csv parameters.csv",
        ],
        [
            "calculate-evsi",
            "voiage calculate-evsi parameters.csv trial_design.json",
        ],
        [
            "calculate-enbs",
            "voiage calculate-enbs --evsi 12.5 --research-cost 10.0",
        ],
        ["calculate-ceaf", "voiage calculate-ceaf surface.json"],
        ["calculate-dominance", "voiage calculate-dominance dominance.csv"],
        [
            "calculate-adaptive-evsi",
            "voiage calculate-adaptive-evsi parameters.csv trial_design.json --adaptive-rules adaptive_rules.json",
        ],
        ["calculate-portfolio-voi", "voiage calculate-portfolio-voi portfolio.json"],
        [
            "calculate-sequential-voi",
            "voiage calculate-sequential-voi parameters.csv dynamic_spec.json",
        ],
        [
            "calculate-perspective",
            "voiage calculate-perspective perspective_surface.json",
        ],
        [
            "calculate-preference",
            "voiage calculate-preference preference_surface.json",
        ],
        [
            "calculate-validation",
            "voiage calculate-validation validation_surface.json",
        ],
        [
            "calculate-threshold",
            "voiage calculate-threshold threshold_surface.json",
        ],
        [
            "calculate-structural-evpi",
            "voiage calculate-structural-evpi structural_config.json",
        ],
        [
            "calculate-structural-evppi",
            "voiage calculate-structural-evppi structural_config.json --structures-of-interest 0 2",
        ],
        ["calculate-nma-voi", "voiage calculate-nma-voi nma_config.json"],
        ["plot-ceac", "voiage plot-ceac surface.json"],
        ["plot-ceaf", "voiage plot-ceaf surface.json"],
        ["plot-voi-curves", "voiage plot-voi-curves curves.json"],
        ["plot-dominance", "voiage plot-dominance dominance.csv"],
        [
            "plot-perspective-regret",
            "voiage plot-perspective-regret perspective_surface.json --output regret.png",
        ],
        ["generate-config", "voiage generate-config evsi > evsi_config.json"],
    ]

    for command_name, example_text in help_checks:
        result = runner.invoke(cli.app, [command_name, "--help"])
        assert result.exit_code == 0
        stdout = _strip_ansi(result.stdout)
        assert "Examples" in stdout
        assert _compact(example_text) in _compact(stdout)


def test_cli_command_registry_matches_expected_surface() -> None:
    """Ensure the Typer command registry exposes the expected public surface."""
    command = get_command(cli.app)

    assert set(command.commands) == {
        "calculate-adaptive-evsi",
        "calculate-calibration",
        "calculate-causal-transportability",
        "calculate-data-quality",
        "calculate-deterministic-sensitivity",
        "calculate-computational-refinement",
        "calculate-coss",
        "calculate-expert-synthesis",
        "calculate-monitoring-surveillance",
        "calculate-implementation-strategy",
        "calculate-distributional-equity",
        "calculate-equity-information",
        "calculate-ambiguity-distribution-shift",
        "calculate-adaptive-learning-bandit",
        "calculate-capacity-budget-constrained",
        "calculate-federated-privacy-preserving",
        "calculate-event-localized-information",
        "calculate-outcome-conditional-sample-information",
        "calculate-forecast-signal-information",
        "calculate-belief-state-information",
        "calculate-ai-assisted-evidence-triage",
        "calculate-explainability-transparency",
        "calculate-interoperability-standardization",
        "calculate-regulatory-market-access",
        "calculate-replication-reproducibility",
        "calculate-evidence-obsolescence-refresh",
        "calculate-strategic-behavior",
        "calculate-dynamic-real-options",
        "calculate-ceaf",
        "calculate-dominance",
        "calculate-enbs",
        "calculate-expected-utility-information",
        "calculate-evpi",
        "calculate-evppi",
        "calculate-evsi",
        "calculate-estimation-variance",
        "calculate-heterogeneity",
        "calculate-heterogeneity-value",
        "calculate-implementation",
        "calculate-implementation-information",
        "calculate-information-source-portfolio",
        "calculate-uncertainty-modelling-value",
        "calculate-signed-social-information",
        "calculate-mcda-information",
        "calculate-observational",
        "calculate-nma-voi",
        "calculate-perspective",
        "calculate-preference",
        "calculate-risk-sensitive-voi",
        "calculate-portfolio-voi",
        "calculate-sequential-voi",
        "calculate-structural-evpi",
        "calculate-structural-evppi",
        "calculate-threshold",
        "calculate-validation",
        "calculate-value-of-flexibility",
        "calculate-value-of-distributional-information",
        "capabilities",
        "assess-qualitative-information",
        "create-distributed-large-scale",
        "generate-config",
        "ingest",
        "plot-ceac",
        "plot-ceaf",
        "plot-coss",
        "plot-dominance",
        "plot-perspective-regret",
        "plot-voi-curves",
    }


def test_cli_preference_surface_help_and_registry() -> None:
    """Track the intended preference surface for the comprehensive CLI."""
    command = get_command(cli.app)
    assert "calculate-preference" in command.commands

    result = runner.invoke(cli.app, ["calculate-preference", "--help"])

    assert result.exit_code == 0
    stdout = _strip_ansi(result.stdout)
    assert "Examples" in stdout
    assert "calculate-preference" in stdout
    assert _compact("voiage calculate-preference preference_surface.json") in _compact(
        stdout
    )


def test_cli_error_handling() -> None:
    """Test CLI error handling."""
    # Test missing file
    result = subprocess.run(
        [sys.executable, "-m", "voiage.cli", "calculate-evpi", "nonexistent_file.csv"],
        capture_output=True,
        text=True,
    )

    # This should fail because the file doesn't exist
    assert result.returncode != 0
    assert "Error" in result.stderr or "error" in result.stderr.lower()


def test_structural_evpi_cli_with_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise the structural EVPI command success path and file output."""
    net_benefits_file = tmp_path / "net_benefits.csv"
    net_benefits_file.write_text("placeholder\n", encoding="utf-8")
    config_file = tmp_path / "structural_evpi.json"
    output_file = tmp_path / "structural_evpi_result.txt"
    _write_json(
        config_file,
        {
            "structures": [
                {
                    "name": "A",
                    "probability": 0.25,
                    "net_benefits_file": "net_benefits.csv",
                },
                {
                    "name": "B",
                    "probability": 0.75,
                    "net_benefits_file": "net_benefits.csv",
                },
            ]
        },
    )

    read_calls: list[tuple[str, bool]] = []
    probabilities_seen: list[float] = []

    def fake_read_value_array_csv(
        path: str, skip_header: bool = False
    ) -> SimpleNamespace:
        read_calls.append((path, skip_header))
        return SimpleNamespace(numpy_values=np.array([[1.0, 2.0], [3.0, 4.0]]))

    def fake_structural_evpi(
        evaluators: list,
        probabilities: list[float],
        psa_samples: list,
        **kwargs: object,
    ) -> float:
        probabilities_seen.extend(probabilities)
        assert len(evaluators) == 2
        assert len(psa_samples) == 2
        assert kwargs["population"] == 1000
        assert kwargs["time_horizon"] == 5
        assert kwargs["discount_rate"] == 0.05
        return 12.345678

    monkeypatch.setattr(cli, "read_value_array_csv", fake_read_value_array_csv)
    monkeypatch.setattr(cli, "structural_evpi", fake_structural_evpi)

    result = runner.invoke(
        cli.app,
        [
            "calculate-structural-evpi",
            str(config_file),
            "--population",
            "1000",
            "--time-horizon",
            "5",
            "--discount-rate",
            "0.05",
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Structural EVPI: 12.345678" in result.stdout
    assert f"Result saved to {output_file}" in result.stdout
    assert (
        output_file.read_text(encoding="utf-8").strip() == "Structural EVPI: 12.345678"
    )
    assert read_calls == [
        (str(net_benefits_file), True),
        (str(net_benefits_file), True),
    ]
    assert probabilities_seen == [0.25, 0.75]


def test_evsi_cli_with_static_net_benefit_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise EVSI CLI with the default static net-benefit model."""
    parameter_file = tmp_path / "parameters.csv"
    parameter_file.write_text(
        "mean_new_treatment,mean_standard_care,sd_outcome\n10,8,1\n11,9,1\n9,7,1\n",
        encoding="utf-8",
    )
    net_benefit_file = tmp_path / "net_benefits.csv"
    net_benefit_file.write_text(
        "standard,new\n100,110\n102,111\n101,109\n",
        encoding="utf-8",
    )
    trial_design_file = tmp_path / "trial_design.json"
    _write_json(
        trial_design_file,
        {
            "arms": [
                {"name": "New Treatment", "sample_size": 10},
                {"name": "Standard Care", "sample_size": 10},
            ]
        },
    )

    method_seen: list[str] = []

    def fake_evsi(**kwargs: object) -> float:
        method_seen.append(str(kwargs["method"]))
        assert kwargs["metamodel"] == "linear"
        assert kwargs["n_outer_loops"] == 5
        return 4.25

    monkeypatch.setattr(cli, "evsi", fake_evsi)

    result = runner.invoke(
        cli.app,
        [
            "calculate-evsi",
            str(parameter_file),
            str(trial_design_file),
            "--net-benefit-file",
            str(net_benefit_file),
            "--method",
            "efficient",
            "--n-outer-loops",
            "5",
        ],
    )

    assert result.exit_code == 0
    assert "EVSI: 4.250000" in result.stdout
    assert method_seen == ["efficient"]


def test_enbs_cli_with_value_and_file_input(tmp_path: Path) -> None:
    """Exercise the ENBS CLI with direct and file-backed EVSI inputs."""
    evsi_file = tmp_path / "evsi_result.txt"
    evsi_file.write_text("EVSI: 17.5\n", encoding="utf-8")
    output_file = tmp_path / "enbs_result.txt"

    value_result = runner.invoke(
        cli.app,
        [
            "calculate-enbs",
            "--evsi",
            "25.5",
            "--research-cost",
            "3.25",
            "--output",
            str(output_file),
        ],
    )

    assert value_result.exit_code == 0
    assert "ENBS: 22.250000" in value_result.stdout
    assert f"Result saved to {output_file}" in value_result.stdout
    assert output_file.read_text(encoding="utf-8").strip() == "ENBS: 22.250000"

    file_result = runner.invoke(
        cli.app,
        [
            "calculate-enbs",
            "--evsi",
            str(evsi_file),
            "--research-cost",
            "2.5",
        ],
    )

    assert file_result.exit_code == 0
    assert "ENBS: 15.000000" in file_result.stdout


def test_enbs_cli_validation_errors(tmp_path: Path) -> None:
    """Exercise ENBS CLI validation and file parsing failures."""
    missing_file = tmp_path / "missing_evsi.txt"
    result = runner.invoke(
        cli.app,
        [
            "calculate-enbs",
            "--evsi",
            str(missing_file),
            "--research-cost",
            "1.0",
        ],
    )
    assert result.exit_code == 1
    assert "Error: EVSI file not found" in result.stderr

    invalid_file = tmp_path / "invalid_evsi.txt"
    invalid_file.write_text("no numeric result here", encoding="utf-8")
    result = runner.invoke(
        cli.app,
        [
            "calculate-enbs",
            "--evsi",
            str(invalid_file),
            "--research-cost",
            "1.0",
        ],
    )
    assert result.exit_code == 1
    assert "does not contain a numeric value" in result.stderr

    negative_cost = runner.invoke(
        cli.app,
        ["calculate-enbs", "--evsi", "10.0", "--research-cost", "-1.0"],
    )
    assert negative_cost.exit_code == 1
    assert "Research cost cannot be negative" in negative_cost.stderr


def test_adaptive_evsi_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise the adaptive EVSI CLI path."""
    parameter_file = tmp_path / "parameters.csv"
    parameter_file.write_text(
        "treatment_effect,control_rate\n0.1,0.2\n0.2,0.3\n", encoding="utf-8"
    )
    trial_design_file = tmp_path / "trial_design.json"
    _write_json(
        trial_design_file,
        {
            "arms": [
                {"name": "Control", "sample_size": 10},
                {"name": "Treatment", "sample_size": 10},
            ]
        },
    )
    adaptive_rules_file = tmp_path / "adaptive_rules.json"
    _write_json(
        adaptive_rules_file,
        {
            "interim_analysis_points": [0.5],
            "early_stopping_rules": {"efficacy": 0.9, "futility": 0.05},
        },
    )

    seen: dict[str, object] = {}

    def fake_adaptive_evsi(**kwargs: object) -> float:
        seen.update(kwargs)
        simulator = cast("Any", kwargs["adaptive_trial_simulator"])
        assert simulator.__name__ == "sophisticated_adaptive_trial_simulator"
        return 7.5

    monkeypatch.setattr(cli, "adaptive_evsi", fake_adaptive_evsi)

    result = runner.invoke(
        cli.app,
        [
            "calculate-adaptive-evsi",
            str(parameter_file),
            str(trial_design_file),
            "--adaptive-rules",
            str(adaptive_rules_file),
            "--simulator",
            "sophisticated",
            "--n-outer-loops",
            "3",
            "--n-inner-loops",
            "4",
        ],
    )

    assert result.exit_code == 0
    assert "Adaptive EVSI: 7.500000" in result.stdout
    assert seen["n_outer_loops"] == 3
    assert seen["n_inner_loops"] == 4

    output_file = tmp_path / "adaptive_evsi.txt"
    output_result = runner.invoke(
        cli.app,
        [
            "calculate-adaptive-evsi",
            str(parameter_file),
            str(trial_design_file),
            "--adaptive-rules",
            str(adaptive_rules_file),
            "--simulator",
            "sophisticated",
            "--output",
            str(output_file),
        ],
    )

    assert output_result.exit_code == 0
    assert output_file.read_text(encoding="utf-8").strip() == "Adaptive EVSI: 7.500000"

    invalid_result = runner.invoke(
        cli.app,
        [
            "calculate-adaptive-evsi",
            str(parameter_file),
            str(trial_design_file),
            "--adaptive-rules",
            str(adaptive_rules_file),
            "--simulator",
            "unknown",
        ],
    )
    assert invalid_result.exit_code == 1
    assert "simulator must be one of" in invalid_result.stderr


def test_portfolio_voi_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise the portfolio VOI CLI path."""
    portfolio_file = tmp_path / "portfolio.json"
    _write_json(
        portfolio_file,
        {
            "budget_constraint": 120,
            "optimization_method": "dynamic_programming",
            "dependency_discount": 0.5,
            "dependency_groups": {"Study Alpha": "group-1"},
            "studies": [
                {
                    "name": "Study Alpha",
                    "cost": 50,
                    "value": 100,
                    "design": {"arms": [{"name": "Arm A", "sample_size": 10}]},
                },
                {
                    "name": "Study Beta",
                    "cost": 60,
                    "value": 90,
                    "design": {"arms": [{"name": "Arm B", "sample_size": 12}]},
                },
            ],
        },
    )

    seen: dict[str, object] = {}

    def fake_portfolio_voi(**kwargs: object) -> dict[str, object]:
        seen.update(kwargs)
        return {
            "selected_studies": [
                SimpleNamespace(name="Study Alpha"),
                SimpleNamespace(name="Study Beta"),
            ],
            "total_value": 190.0,
            "total_cost": 110.0,
        }

    monkeypatch.setattr(cli, "portfolio_voi", fake_portfolio_voi)

    result = runner.invoke(cli.app, ["calculate-portfolio-voi", str(portfolio_file)])

    assert result.exit_code == 0
    assert "Selected studies: Study Alpha, Study Beta" in result.stdout
    assert "Total value: 190.000000" in result.stdout
    assert "Total cost: 110.000000" in result.stdout
    assert isinstance(seen["portfolio_specification"], object)

    output_file = tmp_path / "portfolio_voi.txt"
    output_result = runner.invoke(
        cli.app,
        [
            "calculate-portfolio-voi",
            str(portfolio_file),
            "--output",
            str(output_file),
        ],
    )

    assert output_result.exit_code == 0
    assert "Result saved to" in output_result.stdout
    assert "Selected studies: Study Alpha, Study Beta" in output_file.read_text(
        encoding="utf-8"
    )


def test_sequential_voi_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise the sequential VOI CLI path."""
    parameter_file = tmp_path / "parameters.csv"
    parameter_file.write_text(
        "net_benefit_A,net_benefit_B\n10,12\n11,13\n",
        encoding="utf-8",
    )
    dynamic_spec_file = tmp_path / "dynamic_spec.json"
    _write_json(dynamic_spec_file, {"time_steps": [0.0, 1.0, 2.0]})

    seen: dict[str, object] = {}

    def fake_sequential_voi(**kwargs: object) -> float:
        seen.update(kwargs)
        dynamic_specification = cast("Any", kwargs["dynamic_specification"])
        assert dynamic_specification.time_steps == [0.0, 1.0, 2.0]
        return 3.25

    monkeypatch.setattr(cli, "sequential_voi", fake_sequential_voi)

    result = runner.invoke(
        cli.app,
        [
            "calculate-sequential-voi",
            str(parameter_file),
            str(dynamic_spec_file),
            "--wtp",
            "25000",
            "--optimization-method",
            "backward_induction",
        ],
    )

    assert result.exit_code == 0
    assert "Sequential VOI: 3.250000" in result.stdout
    assert seen["wtp"] == 25000.0

    output_file = tmp_path / "sequential_voi.txt"
    output_result = runner.invoke(
        cli.app,
        [
            "calculate-sequential-voi",
            str(parameter_file),
            str(dynamic_spec_file),
            "--output",
            str(output_file),
        ],
    )

    assert output_result.exit_code == 0
    assert output_file.read_text(encoding="utf-8").strip() == "Sequential VOI: 3.250000"


def test_plot_cli_commands(tmp_path: Path) -> None:
    """Exercise the plotting CLI commands."""
    surface_file = tmp_path / "surface.json"
    _write_json(
        surface_file,
        {
            "strategy_names": ["Strategy A", "Strategy B"],
            "wtp_thresholds": [0, 50000, 100000],
            "net_benefit": [
                [[10, 15, 20], [12, 14, 18]],
                [[11, 16, 21], [13, 15, 19]],
                [[9, 13, 17], [14, 18, 22]],
            ],
        },
    )

    ceac_output = tmp_path / "ceac.png"
    ceac_result = runner.invoke(
        cli.app,
        ["plot-ceac", str(surface_file), "--output", str(ceac_output)],
    )
    assert ceac_result.exit_code == 0
    assert ceac_output.exists()

    ceac_no_output = runner.invoke(cli.app, ["plot-ceac", str(surface_file)])
    assert ceac_no_output.exit_code == 0

    ceaf_output = tmp_path / "ceaf.png"
    ceaf_result = runner.invoke(
        cli.app,
        ["plot-ceaf", str(surface_file), "--output", str(ceaf_output)],
    )
    assert ceaf_result.exit_code == 0
    assert ceaf_output.exists()

    ceaf_no_output = runner.invoke(cli.app, ["plot-ceaf", str(surface_file)])
    assert ceaf_no_output.exit_code == 0

    curves_file = tmp_path / "curves.json"
    _write_json(
        curves_file,
        {
            "wtp_thresholds": [0, 1, 2],
            "evpi_values": [1.0, 1.5, 2.0],
        },
    )
    curves_output = tmp_path / "curves.png"
    curves_result = runner.invoke(
        cli.app,
        ["plot-voi-curves", str(curves_file), "--output", str(curves_output)],
    )
    assert curves_result.exit_code == 0
    assert curves_output.exists()

    curves_no_output = runner.invoke(cli.app, ["plot-voi-curves", str(curves_file)])
    assert curves_no_output.exit_code == 0

    dominance_file = tmp_path / "dominance.csv"
    dominance_file.write_text(
        "strategy,cost,effect\nA,100,1.0\nB,150,1.2\nC,130,1.1\n",
        encoding="utf-8",
    )
    dominance_output = tmp_path / "dominance.png"
    dominance_result = runner.invoke(
        cli.app,
        ["plot-dominance", str(dominance_file), "--output", str(dominance_output)],
    )
    assert dominance_result.exit_code == 0
    assert dominance_output.exists()

    dominance_no_output = runner.invoke(
        cli.app, ["plot-dominance", str(dominance_file)]
    )
    assert dominance_no_output.exit_code == 0


def test_plot_cli_validation_helpers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise plot helper validation and error branches."""
    with pytest.raises(TypeError, match="Plot function did not return"):
        cli._save_figure(object(), tmp_path / "broken.png")

    assert cli._csv_string(None) == ""
    assert cli._csv_string(["alpha", "beta"]) == '["alpha", "beta"]'
    assert cli._csv_string({"x": 1}) == '{"x": 1}'

    with pytest.raises(TypeError, match="must be a number"):
        cli._read_float("not-a-number", "value")

    monkeypatch.setitem(cli._CLI_STATE, "output_format", "bogus")
    with pytest.raises(ValueError, match="Unsupported output format"):
        cli._format_output("ignored", {"command": "test"})

    evpi_input = tmp_path / "evpi_input.csv"
    evpi_input.write_text("Strategy A,Strategy B\n1,2\n", encoding="utf-8")
    monkeypatch.setattr(
        cli,
        "read_value_array_csv",
        lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError("missing")),
    )
    evpi_error = runner.invoke(cli.app, ["calculate-evpi", str(evpi_input)])
    assert evpi_error.exit_code == 1
    assert "Net benefit file not found" in evpi_error.stderr

    bad_surface_payload = tmp_path / "bad_surface_payload.json"
    bad_surface_payload.write_text("[]", encoding="utf-8")
    with pytest.raises(TypeError, match="JSON object"):
        cli._read_plot_surface(bad_surface_payload)

    missing_surface_fields = tmp_path / "missing_surface_fields.json"
    _write_json(
        missing_surface_fields,
        {
            "net_benefit": [[[1.0, 2.0]]],
        },
    )
    with pytest.raises(TypeError, match="net_benefit.*wtp_thresholds"):
        cli._read_plot_surface(missing_surface_fields)

    bad_surface_ndim = tmp_path / "bad_surface_ndim.json"
    _write_json(
        bad_surface_ndim,
        {
            "net_benefit": [[1.0, 2.0]],
            "wtp_thresholds": [0.0],
        },
    )
    with pytest.raises(TypeError, match="3D array"):
        cli._read_plot_surface(bad_surface_ndim)

    bad_surface = tmp_path / "bad_surface.json"
    _write_json(
        bad_surface,
        {
            "net_benefit": [[[1.0, 2.0]]],
            "wtp_thresholds": [0.0],
            "strategy_names": "not-a-list",
        },
    )
    with pytest.raises(TypeError, match="strategy_names"):
        cli._read_plot_surface(bad_surface)

    bad_surface_2 = tmp_path / "bad_surface_2.json"
    _write_json(
        bad_surface_2,
        {
            "net_benefit": [[[1.0, 2.0]]],
            "wtp_thresholds": "not-a-list",
        },
    )
    with pytest.raises(TypeError, match="wtp_thresholds"):
        cli._read_plot_surface(bad_surface_2)

    bad_series = tmp_path / "bad_series.json"
    bad_series.write_text("[]", encoding="utf-8")
    with pytest.raises(TypeError, match="Plot series file must contain"):
        cli._read_plot_series(bad_series)

    mixed_series = tmp_path / "mixed_series.json"
    _write_json(
        mixed_series,
        {
            "wtp_thresholds": [0.0, 1.0],
            "notes": "ignored",
        },
    )
    assert cli._read_plot_series(mixed_series) == {"wtp_thresholds": [0.0, 1.0]}

    empty_dominance = tmp_path / "empty_dominance.csv"
    empty_dominance.write_text("strategy,cost,effect\n", encoding="utf-8")
    with pytest.raises(ValueError, match="at least one row"):
        cli._read_cost_effect_csv(empty_dominance)

    evsi_series = tmp_path / "evsi_series.json"
    _write_json(
        evsi_series,
        {
            "sample_sizes": [1, 2, 3],
            "evsi_values": [1.0, 1.5, 2.0],
            "enbs_values": [0.5, 1.0, 1.5],
            "research_costs": [0.2, 0.3, 0.4],
        },
    )
    evsi_output = tmp_path / "evsi_curve.png"
    evsi_result = runner.invoke(
        cli.app,
        ["plot-voi-curves", str(evsi_series), "--output", str(evsi_output)],
    )
    assert evsi_result.exit_code == 0
    assert evsi_output.exists()

    structural_config = tmp_path / "structural_missing.json"
    _write_json(
        structural_config,
        {
            "structures": [
                {
                    "name": "A",
                    "probability": 1.0,
                    "net_benefits_file": "missing.csv",
                }
            ]
        },
    )
    (tmp_path / "missing.csv").write_text("placeholder\n", encoding="utf-8")
    missing_flag_result = runner.invoke(
        cli.app, ["calculate-structural-evppi", str(structural_config)]
    )
    assert missing_flag_result.exit_code == 1
    assert "parameters-of-interest" in missing_flag_result.stderr


def test_evsi_cli_requires_model_or_net_benefits(tmp_path: Path) -> None:
    """EVSI CLI should report a clear missing model input error."""
    parameter_file = tmp_path / "parameters.csv"
    parameter_file.write_text("x\n1\n2\n", encoding="utf-8")
    trial_design_file = tmp_path / "trial_design.json"
    _write_json(trial_design_file, {"arms": [{"name": "Arm A", "sample_size": 5}]})

    result = runner.invoke(
        cli.app,
        ["calculate-evsi", str(parameter_file), str(trial_design_file)],
    )

    assert result.exit_code == 1
    assert "provide either --model or --net-benefit-file" in result.stderr


def test_structural_evpi_cli_validation_errors(tmp_path: Path) -> None:
    """Exercise structural EVPI config validation and JSON parsing errors."""
    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{not json", encoding="utf-8")
    result = runner.invoke(cli.app, ["calculate-structural-evpi", str(invalid_json)])
    assert result.exit_code == 1
    assert "Error: Invalid JSON in config file" in result.stderr

    missing_structures = tmp_path / "missing_structures.json"
    _write_json(missing_structures, {"foo": "bar"})
    result = runner.invoke(
        cli.app, ["calculate-structural-evpi", str(missing_structures)]
    )
    assert result.exit_code == 1
    assert "Error: Config file must contain 'structures' key" in result.stderr

    invalid_probabilities = tmp_path / "invalid_probabilities.json"
    _write_json(
        invalid_probabilities,
        {
            "structures": [
                {"probability": 0.2, "net_benefits_file": "a.csv"},
                {"probability": 0.3, "net_benefits_file": "b.csv"},
            ]
        },
    )
    result = runner.invoke(
        cli.app, ["calculate-structural-evpi", str(invalid_probabilities)]
    )
    assert result.exit_code == 1
    assert "Error: Structure probabilities must sum to 1 (got 0.5)" in result.stderr


def test_structural_evppi_cli_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise the structural EVPPI command success path."""
    net_benefits_file = tmp_path / "net_benefits.csv"
    net_benefits_file.write_text("placeholder\n", encoding="utf-8")
    config_file = tmp_path / "structural_evppi.json"
    _write_json(
        config_file,
        {
            "structures": [
                {
                    "name": "A",
                    "probability": 0.4,
                    "net_benefits_file": "net_benefits.csv",
                },
                {
                    "name": "B",
                    "probability": 0.6,
                    "net_benefits_file": "net_benefits.csv",
                },
            ]
        },
    )

    def fake_read_value_array_csv(
        path: str, skip_header: bool = False
    ) -> SimpleNamespace:
        assert path == str(net_benefits_file)
        assert skip_header is True
        return SimpleNamespace(numpy_values=np.array([[5.0, 6.0], [7.0, 8.0]]))

    def fake_structural_evppi(
        evaluators: list,
        probabilities: list[float],
        psa_samples: list,
        structures_of_interest: list[int],
        **kwargs: object,
    ) -> float:
        assert len(evaluators) == 2
        assert len(psa_samples) == 2
        assert probabilities == [0.4, 0.6]
        assert structures_of_interest == [0, 1]
        assert kwargs["population"] == 2500
        return 9.876543

    monkeypatch.setattr(cli, "read_value_array_csv", fake_read_value_array_csv)
    monkeypatch.setattr(cli, "structural_evppi", fake_structural_evppi)

    result = runner.invoke(
        cli.app,
        [
            "calculate-structural-evppi",
            str(config_file),
            "--structures-of-interest",
            "0",
            "--structures-of-interest",
            "1",
            "--population",
            "2500",
        ],
    )

    assert result.exit_code == 0
    assert "Structural EVPPI: 9.876543" in result.stdout


def test_structural_evppi_cli_parameters_of_interest_alias(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise the structural EVPPI command using the new alias flag."""
    net_benefits_file = tmp_path / "net_benefits.csv"
    net_benefits_file.write_text("placeholder\n", encoding="utf-8")
    config_file = tmp_path / "structural_evppi_alias.json"
    output_file = tmp_path / "structural_evppi_alias_result.txt"
    _write_json(
        config_file,
        {
            "structures": [
                {
                    "name": "A",
                    "probability": 0.5,
                    "net_benefits_file": "net_benefits.csv",
                },
                {
                    "name": "B",
                    "probability": 0.5,
                    "net_benefits_file": "net_benefits.csv",
                },
            ]
        },
    )

    def fake_read_value_array_csv(
        path: str, skip_header: bool = False
    ) -> SimpleNamespace:
        assert path == str(net_benefits_file)
        assert skip_header is True
        return SimpleNamespace(numpy_values=np.array([[1.0, 2.0], [3.0, 4.0]]))

    def fake_structural_evppi(
        evaluators: list,
        probabilities: list[float],
        psa_samples: list,
        structures_of_interest: list[int],
        **kwargs: object,
    ) -> float:
        assert structures_of_interest == [0]
        assert kwargs["population"] == 1000
        return 2.468

    monkeypatch.setattr(cli, "read_value_array_csv", fake_read_value_array_csv)
    monkeypatch.setattr(cli, "structural_evppi", fake_structural_evppi)

    result = runner.invoke(
        cli.app,
        [
            "calculate-structural-evppi",
            str(config_file),
            "--parameters-of-interest",
            "0",
            "--population",
            "1000",
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Structural EVPPI: 2.468000" in result.stdout
    assert (
        output_file.read_text(encoding="utf-8").strip() == "Structural EVPPI: 2.468000"
    )


def test_nma_voi_cli_branches(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise the EVPI and EVPPI branches of the NMA command."""
    config_file = tmp_path / "nma.json"
    _write_json(
        config_file,
        {
            "study_data": [{"study_id": 1}],
            "treatment_effects": {"A-B": [0.1, 0.2, 0.3]},
        },
    )

    seen_random_sizes: list[int] = []

    def fake_rand(n_samples: int) -> np.ndarray:
        seen_random_sizes.append(n_samples)
        return np.linspace(0.0, 1.0, n_samples)

    def fake_calculate_nma_evpi(config: dict, **kwargs: object) -> float:
        assert config["study_data"] == [{"study_id": 1}]
        assert kwargs["willingness_to_pay"] == 50000.0
        assert kwargs["population"] == 200
        return 2.5

    def fake_calculate_nma_evppi(
        config: dict,
        parameters_of_interest: list[str],
        parameter_samples: dict,
        **kwargs: object,
    ) -> float:
        assert config["study_data"] == [{"study_id": 1}]
        assert parameters_of_interest == ["hazard_ratio", "cost_offset"]
        assert sorted(parameter_samples) == ["cost_offset", "hazard_ratio"]
        assert all(len(values) == 3 for values in parameter_samples.values())
        assert kwargs["willingness_to_pay"] == 25000.0
        return 1.25

    monkeypatch.setattr(cli.np.random, "rand", fake_rand)
    monkeypatch.setattr(cli, "calculate_nma_evpi", fake_calculate_nma_evpi)
    monkeypatch.setattr(cli, "calculate_nma_evppi", fake_calculate_nma_evppi)

    evpi_result = runner.invoke(
        cli.app,
        [
            "calculate-nma-voi",
            str(config_file),
            "--willingness-to-pay",
            "50000",
            "--population",
            "200",
        ],
    )
    assert evpi_result.exit_code == 0
    assert "NMA-EVPI: 2.500000" in evpi_result.stdout

    evppi_result = runner.invoke(
        cli.app,
        [
            "calculate-nma-voi",
            str(config_file),
            "--willingness-to-pay",
            "25000",
            "--parameters-of-interest",
            "hazard_ratio,cost_offset",
        ],
    )
    assert evppi_result.exit_code == 0
    assert "NMA-EVPPI: 1.250000" in evppi_result.stdout
    assert seen_random_sizes == [3, 3]


def test_nma_voi_cli_validation_errors(tmp_path: Path) -> None:
    runner = CliRunner()

    missing_config = tmp_path / "missing.json"
    missing_result = runner.invoke(cli.app, ["calculate-nma-voi", str(missing_config)])
    missing_error = _compact(_strip_ansi(missing_result.stdout + missing_result.stderr))
    assert missing_result.exit_code == 2
    assert "Invalid value for 'CONFIG_FILE'" in missing_error
    assert "does not exist." in missing_error

    invalid_config = tmp_path / "invalid.json"
    invalid_config.write_text("{not json", encoding="utf-8")
    invalid_result = runner.invoke(cli.app, ["calculate-nma-voi", str(invalid_config)])
    invalid_error = _compact(_strip_ansi(invalid_result.stdout + invalid_result.stderr))
    assert invalid_result.exit_code == 1
    assert "Error: Invalid JSON in config file" in invalid_error


def test_nma_voi_cli_internal_exception(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = CliRunner()
    config_file = tmp_path / "nma.json"
    _write_json(
        config_file,
        {
            "study_data": [{"study_id": 1}],
            "treatment_effects": {"A-B": [0.1, 0.2, 0.3]},
        },
    )

    def boom(*args: object, **kwargs: object) -> float:
        raise RuntimeError("boom")

    monkeypatch.setattr(cli, "calculate_nma_evpi", boom)

    result = runner.invoke(cli.app, ["calculate-nma-voi", str(config_file)])
    assert result.exit_code == 1
    assert "An error occurred: boom" in result.stderr


if __name__ == "__main__":
    test_evpi_cli()
    test_evppi_cli()
    test_cli_help()
    test_cli_error_handling()
    print("All CLI comprehensive tests passed!")
