# voiage/cli.py

"""
Command-Line Interface (CLI) for voiage.

This module provides CLI entry points for performing VOI analyses
or accessing voiage utilities from the command line.
It uses Typer for command-line argument parsing.
"""

# Typer argument declarations intentionally call helper constructors in defaults.
# ruff: noqa: B008, TRY301

from collections.abc import Callable, Iterable
import csv
import importlib
import io
import json
import logging
from pathlib import Path
import re
from typing import Any, Literal, cast

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
import numpy as np
import typer

from voiage.contracts.distributional_information import (
    VALUE_OF_DISTRIBUTIONAL_INFORMATION_INPUT_SCHEMA_V1,
)
from voiage.contracts.estimation import EstimationVarianceSpec
from voiage.contracts.study_design import (
    CossResultV1,
    FeasibleDesignRangeV1,
    SelectionUncertaintyV1,
    StudyDesignContextV1,
    StudyDesignPointInputV1,
    TiePolicy,
)
from voiage.contracts.value_flexibility import VALUE_OF_FLEXIBILITY_INPUT_SCHEMA_V1
from voiage.core.io import (
    import_callable,
    read_parameter_set_csv,
    read_value_array_csv,
)
from voiage.experimental.study_design import calculate_coss as calculate_coss_result
from voiage.factory import create_distributed_large_scale_analysis
from voiage.ingestion.cli import app as ingestion_app
from voiage.logging import LoggingSettings, configure_logging
from voiage.methods.adaptive import (
    adaptive_evsi,
    bayesian_adaptive_trial_simulator,
    sophisticated_adaptive_trial_simulator,
)
from voiage.methods.adaptive_learning_bandit import (
    value_of_adaptive_learning_bandit as calculate_bandit_result,
)
from voiage.methods.ai_assisted_evidence_triage import (
    value_of_ai_assisted_evidence_triage as calculate_ai_triage_result,
)
from voiage.methods.ambiguity_distribution_shift import (
    value_of_ambiguity_distribution_shift as calculate_ambiguity_shift_result,
)
from voiage.methods.basic import evpi, evppi
from voiage.methods.belief_state_information import (
    belief_state_information_value as calculate_belief_state_information_result,
)
from voiage.methods.calibration import voi_calibration
from voiage.methods.capacity_budget_constrained import (
    value_of_capacity_budget_constrained as calculate_capacity_budget_result,
)
from voiage.methods.causal_transportability import (
    value_of_causal_transportability as calculate_causal_transportability_result,
)
from voiage.methods.ceaf import calculate_ceaf as calculate_ceaf_result
from voiage.methods.computational import (
    value_of_computational_refinement as calculate_computational_result,
)
from voiage.methods.data_quality import (
    value_of_data_quality as calculate_data_quality_result,
)
from voiage.methods.deterministic_sensitivity import (
    deterministic_sensitivity_from_specification as calculate_deterministic_sensitivity_result,
)
from voiage.methods.distributional import (
    DistributionalEquityResult,
    value_of_distributional_equity,
)
from voiage.methods.distributional_information import (
    distributional_information_from_specification as calculate_distributional_information_result,
)
from voiage.methods.dominance import calculate_dominance as calculate_dominance_result
from voiage.methods.dynamic_real_options import (
    value_of_dynamic_real_options as calculate_dynamic_real_options_result,
)
from voiage.methods.dynamic_real_options import (
    value_of_flexibility as calculate_flexibility_result,
)
from voiage.methods.equity_information import (
    value_of_equity_information as calculate_equity_information_result,
)
from voiage.methods.estimation import evppi_var, evsi_var
from voiage.methods.event_localized_information import (
    event_localized_information_value as calculate_event_localized_information_result,
)
from voiage.methods.evidence_obsolescence_refresh import (
    value_of_evidence_obsolescence_refresh as calculate_obsolescence_result,
)
from voiage.methods.expert_synthesis import (
    value_of_expert_synthesis as calculate_expert_synthesis_result,
)
from voiage.methods.explainability_transparency import (
    value_of_explainability_transparency as calculate_explainability_result,
)
from voiage.methods.federated_privacy_preserving import (
    value_of_federated_privacy_preserving as calculate_federated_privacy_result,
)
from voiage.methods.forecast_signal_information import (
    forecast_signal_information_value as calculate_forecast_signal_information_result,
)
from voiage.methods.heterogeneity import (
    HeterogeneityResult,
    value_of_heterogeneity,
)
from voiage.methods.heterogeneity_value import (
    heterogeneity_value_decomposition as calculate_heterogeneity_value_result,
)
from voiage.methods.implementation import (
    ImplementationAdjustedResult,
    value_of_implementation,
)
from voiage.methods.implementation_information import (
    implementation_information_value as calculate_implementation_information_result,
)
from voiage.methods.implementation_strategy import (
    value_of_implementation_strategy_comparison as calculate_implementation_strategy_result,
)
from voiage.methods.information_source_portfolio import (
    information_source_portfolio_value as calculate_information_source_portfolio_result,
)
from voiage.methods.interoperability_standardization import (
    value_of_interoperability_standardization as calculate_interoperability_result,
)
from voiage.methods.mcda_information import (
    mcda_information_value as calculate_mcda_information_result,
)
from voiage.methods.monitoring_surveillance import (
    value_of_monitoring_surveillance as calculate_monitoring_surveillance_result,
)
from voiage.methods.network_meta_analysis import (
    calculate_nma_evpi,
    calculate_nma_evppi,
)
from voiage.methods.observational import voi_observational
from voiage.methods.outcome_conditional_sample_information import (
    outcome_conditional_sample_information_value as calculate_outcome_conditional_result,
)
from voiage.methods.perspective import (
    ValueOfPerspectiveResult,
)
from voiage.methods.perspective import (
    value_of_perspective as calculate_perspective_result,
)
from voiage.methods.portfolio import portfolio_voi
from voiage.methods.preference import (
    PreferenceHeterogeneityResult,
    PreferenceProfile,
    PreferenceProfileSet,
)
from voiage.methods.qualitative_information import (
    qualitative_information_from_specification as calculate_qualitative_information_result,
)
from voiage.methods.qualitative_information import (
    render_qualitative_information_text,
)
from voiage.methods.regulatory_market_access import (
    value_of_regulatory_market_access as calculate_market_access_result,
)
from voiage.methods.replication_reproducibility import (
    value_of_replication_reproducibility as calculate_replication_result,
)
from voiage.methods.risk_sensitive_voi import (
    risk_sensitive_constrained_voi as calculate_risk_sensitive_voi_result,
)
from voiage.methods.sample_information import enbs, evsi
from voiage.methods.sequential import sequential_voi
from voiage.methods.signed_social_information import (
    signed_social_information_value as calculate_signed_social_information_result,
)
from voiage.methods.strategic_behavior import (
    value_of_strategic_behavior as calculate_strategic_result,
)
from voiage.methods.structural import structural_evpi, structural_evppi
from voiage.methods.threshold import (
    ThresholdProfile,
    ThresholdProfileSet,
    ThresholdResult,
)
from voiage.methods.threshold import (
    value_of_threshold as calculate_threshold_result,
)
from voiage.methods.uncertainty_modelling_value import (
    value_of_uncertainty_modelling as calculate_uncertainty_modelling_value_result,
)
from voiage.methods.utility_information import (
    _bind_presentation,
    expected_utility_information_value,
    value_of_clairvoyance,
)
from voiage.methods.validation import (
    ModelValidationResult,
    ValidationProfile,
    ValidationProfileSet,
)
from voiage.methods.validation import (
    value_of_model_validation as calculate_validation_result,
)
from voiage.parallel import get_execution_adapter, is_placeholder_execution_adapter
from voiage.plot.ceac import plot_ceac as render_ceac
from voiage.plot.ceaf import plot_ceaf as render_ceaf
from voiage.plot.dominance import plot_cost_effectiveness_plane as render_dominance
from voiage.plot.perspective import plot_perspective_regret as render_perspective_regret
from voiage.plot.voi_curves import (
    plot_coss as render_coss,
)
from voiage.plot.voi_curves import (
    plot_evpi_vs_wtp as render_evpi_vs_wtp,
)
from voiage.plot.voi_curves import (
    plot_evsi_vs_sample_size as render_evsi_vs_sample_size,
)
from voiage.reporting import (
    build_cheers_reporting,
    build_estimation_variance_reporting,
)
from voiage.schema import (
    DynamicSpec,
    ParameterSet,
    PortfolioSpec,
    PortfolioStudy,
    TrialDesign,
    ValueArray,
)

app = typer.Typer(
    help="voiage: A Command-Line Interface for Value of Information Analysis."
)
app.add_typer(ingestion_app, name="ingest")


def _module_available(name: str) -> bool:
    """Return whether an optional module can be imported successfully."""
    try:
        importlib.import_module(name)
    except (ImportError, OSError, RuntimeError):
        return False
    return True


@app.command(name="capabilities")
def capabilities(
    json_output: bool = typer.Option(
        False, "--json", help="Emit machine-readable JSON."
    ),
) -> None:
    """Report installed capabilities without evaluating a model."""
    from voiage import __version__

    report = {
        "schema_version": "1.0.0",
        "package_version": __version__,
        "backend": "rust-backed-cpu",
        "optional_modules": {
            name: _module_available(name)
            for name in ("jax", "torch", "polars", "pyarrow")
        },
        "methods": ["evpi", "evppi", "evsi", "enbs", "ceaf", "dominance"],
        "dry_run": True,
    }
    if json_output:
        typer.echo(json.dumps(report, sort_keys=True))
    else:
        typer.echo(f"voiage {report['package_version']} ({report['backend']})")
        typer.echo("methods: " + ", ".join(report["methods"]))


OutputFormat = Literal["text", "json", "csv"]

_SCALAR_PATTERN = re.compile(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?")
_CLI_LOGGER = logging.getLogger("voiage.cli")
_CLI_STATE: dict[str, bool | OutputFormat] = {
    "output_format": "text",
    "quiet": False,
    "verbose": False,
}

_CONFIG_TEMPLATES: dict[str, dict[str, object]] = {
    "evsi": {
        "command": "calculate-evsi",
        "description": "Template for EVSI analysis inputs.",
        "parameter_file": "parameters.csv",
        "trial_design_file": "trial_design.json",
        "model": "your.module:callable",
        "net_benefit_file": None,
        "method": "two_loop",
        "metamodel": "linear",
        "n_outer_loops": 100,
        "n_inner_loops": 1000,
        "population": None,
        "discount_rate": None,
        "time_horizon": None,
    },
    "evppi": {
        "command": "calculate-evppi",
        "description": "Template for EVPPI analysis inputs.",
        "net_benefit_file": "net_benefits.csv",
        "parameter_file": "parameters.csv",
        "population": None,
        "discount_rate": None,
        "time_horizon": None,
    },
    "distributed-large-scale": {
        "command": "create-distributed-large-scale",
        "description": "Template for CPU-cluster or distributed large-scale analysis inputs.",
        "chunk_size": 10000,
        "n_nodes": 1,
        "workers_per_node": None,
        "scheduler": "process",
        "scheduler_is_placeholder": False,
        "scheduler_address": None,
        "use_processes": True,
        "memory_limit_mb": None,
    },
    "nma-voi": {
        "command": "calculate-nma-voi",
        "description": "Template for NMA VOI inputs.",
        "treatment_effects": {"Placebo-Drug_A": [0.0, 0.0]},
        "n_studies": 0,
        "treatments": ["Placebo", "Drug_A"],
        "outcome_type": "continuous",
        "parameters_of_interest": None,
        "willingness_to_pay": None,
        "population": None,
        "discount_rate": None,
        "time_horizon": None,
    },
    "perspective": {
        "command": "calculate-perspective",
        "description": "Template for experimental Value of Perspective inputs.",
        "net_benefit": [
            [[10.0, 7.0], [8.0, 11.0]],
            [[10.0, 7.0], [8.0, 11.0]],
        ],
        "strategy_names": ["A", "B"],
        "perspective_names": ["payer", "societal"],
        "perspective_weights": {"payer": 0.5, "societal": 0.5},
        "reference_perspective": "payer",
    },
    "dynamic-real-options": {
        "command": "calculate-dynamic-real-options",
        "description": "Template for fixture-backed staged dynamic real-options VOI inputs.",
        "decision_stage_names": ["now", "after_phase_1", "after_phase_2"],
        "strategy_names": ["immediate_adopt", "delay_and_review", "wait_for_trial"],
        "net_benefit": [[[10.0, 11.0, 9.0], [8.0, 12.0, 13.0], [7.0, 10.0, 14.0]]],
        "stage_weights": {"now": 0.2, "after_phase_1": 0.3, "after_phase_2": 0.5},
        "discount_rate": 0.03,
        "irreversibility_penalty": 0.5,
        "lock_in_penalty": 0.25,
        "evidence_arrival_times": {"after_phase_1": 1.0, "after_phase_2": 2.0},
        "exercise_rules": {"now": "exercise_immediately"},
    },
    "causal-transportability": {
        "command": "calculate-causal-transportability",
        "description": "Template for fixture-backed causal transportability VOI inputs.",
        "analysis_id": "causal-transportability-analysis",
        "decision_problem_id": "screening-program-001",
        "source_population_ids": ["trial_population", "real_world_population"],
        "target_population_ids": ["urban_target", "rural_target"],
        "strategy_names": ["status_quo", "adapted_policy"],
        "net_benefit": [[[10.0, 12.0], [9.0, 11.0]]],
        "transport_weights": [[1.0, 0.7], [0.8, 0.9]],
        "validity_penalties": [[0.0, 1.0], [0.5, 0.4]],
        "reference_target_population": "urban_target",
    },
    "data-quality": {
        "command": "calculate-data-quality",
        "description": "Template for fixture-backed data-quality, privacy, and linkage VOI inputs.",
        "analysis_id": "data-quality-analysis",
        "decision_problem_id": "screening-program-001",
        "data_quality_profile_ids": ["clean_registry", "noisy_linked_records"],
        "strategy_names": [
            "status_quo",
            "collect_more_data",
            "privacy_preserving_linkage",
        ],
        "net_benefit": [[[10.0, 9.0], [12.0, 11.4], [11.5, 12.1]]],
        "acquisition_costs": [[0.0, 1.5, 2.5], [0.0, 1.0, 2.0]],
        "privacy_constraints": [[0.0, 0.4, 0.7], [0.1, 0.3, 0.5]],
        "measurement_error_rates": [[0.05, 0.12, 0.2], [0.08, 0.15, 0.25]],
        "linkage_weights": [[1.0, 0.8, 0.6], [0.9, 0.7, 0.5]],
        "reference_data_quality_profile": "clean_registry",
    },
    "computational": {
        "command": "calculate-computational-refinement",
        "description": "Template for fixture-backed computational VOI inputs.",
        "analysis_id": "computational-analysis",
        "decision_problem_id": "screening-program-001",
        "compute_budget_ids": ["baseline_compute", "enhanced_compute"],
        "strategy_names": ["status_quo", "refine_model", "approximate_fast"],
        "net_benefit": [[[10.0, 9.7], [11.4, 12.1], [11.0, 11.8]]],
        "compute_costs": [[0.0, 2.0, 1.0], [0.0, 3.0, 1.5]],
        "approximation_errors": [[0.3, 0.1, 0.2], [0.25, 0.08, 0.15]],
        "refinement_weights": [[0.5, 0.9, 0.6], [0.4, 1.0, 0.7]],
        "reference_compute_budget": "baseline_compute",
    },
    "expert-synthesis": {
        "command": "calculate-expert-synthesis",
        "description": "Template for fixture-backed expert elicitation and synthesis VOI inputs.",
        "analysis_id": "expert-synthesis-analysis",
        "decision_problem_id": "screening-program-001",
        "expert_profile_ids": ["structured_panel", "delphi_panel"],
        "strategy_names": ["status_quo", "expert_elicitation", "synthesis_reweighted"],
        "net_benefit": [[[10.0, 9.8], [11.5, 11.0], [11.2, 11.6]]],
        "elicitation_costs": [[0.0, 1.4, 2.0], [0.0, 1.1, 1.8]],
        "synthesis_penalties": [[0.0, 0.5, 0.2], [0.1, 0.4, 0.3]],
        "reference_expert_profile": "structured_panel",
    },
    "monitoring-surveillance": {
        "command": "calculate-monitoring-surveillance",
        "description": "Template for fixture-backed monitoring and surveillance VOI inputs.",
        "analysis_id": "monitoring-surveillance-analysis",
        "decision_problem_id": "screening-program-001",
        "strategy_names": ["status_quo", "monitor", "revise_decision"],
        "net_benefit": [[[10.0, 10.4, 10.8], [11.0, 11.5, 12.0], [10.5, 11.2, 12.4]]],
        "monitoring_costs": [[0.0, 0.5, 0.8], [0.0, 0.6, 0.9], [0.0, 0.7, 1.0]],
        "detection_delays": [[0.0, 0.2, 0.3], [0.0, 0.2, 0.2], [0.0, 0.1, 0.2]],
        "false_signal_rates": [[0.0, 0.1, 0.15], [0.0, 0.08, 0.12], [0.0, 0.06, 0.1]],
        "decision_revision_probabilities": [
            [0.0, 0.4, 0.5],
            [0.0, 0.5, 0.6],
            [0.0, 0.6, 0.8],
        ],
        "surveillance_frequency": 1.0,
        "stopping_threshold": 0.5,
    },
    "implementation-strategy": {
        "command": "calculate-implementation-strategy",
        "description": "Template for fixture-backed implementation-strategy comparison VOI inputs.",
        "analysis_id": "implementation-strategy-analysis",
        "decision_problem_id": "screening-program-001",
        "strategy_names": ["status_quo", "training_support", "digital_scale_up"],
        "net_benefit": [[[10.0, 10.5, 11.0], [11.0, 12.0, 13.0], [10.6, 12.3, 14.0]]],
        "uptake": [[0.95, 0.7, 0.55], [0.95, 0.8, 0.7], [0.95, 0.9, 0.82]],
        "adherence": [[0.95, 0.75, 0.65], [0.95, 0.8, 0.72], [0.95, 0.85, 0.78]],
        "coverage": [[0.8, 0.65, 0.5], [0.8, 0.72, 0.62], [0.8, 0.78, 0.72]],
        "implementation_delays": [[0.0, 1.0, 2.0], [0.0, 0.8, 1.4], [0.0, 0.6, 1.0]],
        "scale_up_costs": [[0.0, 0.8, 1.2], [0.0, 0.7, 1.0], [0.0, 0.6, 0.8]],
        "population_impacts": [[0.0, 0.4, 0.5], [0.0, 0.6, 0.8], [0.0, 0.8, 1.2]],
        "discount_rate": 0.03,
    },
    "equity-information": {
        "command": "calculate-equity-information",
        "description": "Template for fixture-backed equity-information VOI inputs.",
        "net_benefit": [[10.0, 8.0], [12.0, 7.0], [6.0, 11.0], [5.0, 13.0]],
        "strategy_names": ["A", "B"],
        "subgroups": ["low", "low", "high", "high"],
        "equity_weights": [0.5, 0.5],
        "resolved_equity_weights": [[0.8, 0.2], [0.2, 0.8]],
        "scenario_probabilities": [0.5, 0.5],
        "information_cost": 0.0,
        "policy_strata": ["protected", "policy-relevant"],
    },
    "ambiguity-distribution-shift": {
        "command": "calculate-ambiguity-distribution-shift",
        "description": "Template for fixture-backed ambiguity and distribution-shift VOI inputs.",
        "net_benefit": [[10.0, 8.0], [12.0, 7.0], [6.0, 11.0], [5.0, 13.0]],
        "strategy_names": ["A", "B"],
        "shift_weights": [[0.4, 0.4, 0.1, 0.1], [0.1, 0.1, 0.4, 0.4]],
        "scenario_names": ["source", "shifted"],
        "scenario_probabilities": [0.5, 0.5],
        "ambiguity_radius": 0.1,
        "information_cost": 0.0,
    },
    "adaptive-learning-bandit": {
        "command": "calculate-adaptive-learning-bandit",
        "description": "Template for fixture-backed adaptive learning and bandit VOI inputs.",
        "reward_samples": [[0.4, 0.5, 0.6, 0.7], [0.7, 0.8, 0.9, 1.0]],
        "arm_names": ["control", "adaptive"],
        "policy": "ucb",
        "horizon": 4,
        "exploration_cost": 0.01,
        "confidence": 2.0,
        "seed": 0,
    },
    "capacity-budget-constrained": {
        "command": "calculate-capacity-budget-constrained",
        "description": "Template for fixture-backed budget and capacity-constrained VOI inputs.",
        "scenario_values": [[10.0, 8.0, 4.0], [6.0, 11.0, 9.0], [12.0, 7.0, 10.0]],
        "strategy_names": ["small", "balanced", "large"],
        "strategy_costs": [2.0, 5.0, 8.0],
        "strategy_capacity": [1.0, 2.0, 4.0],
        "budget": 5.0,
        "capacity": 2.0,
        "information_cost": 0.0,
    },
    "federated-privacy-preserving": {
        "command": "calculate-federated-privacy-preserving",
        "description": "Template for fixture-backed federated and privacy-preserving VOI inputs.",
        "site_summaries": [[8.0, 7.0], [6.0, 9.0], [7.0, 8.0]],
        "site_weights": [0.2, 0.5, 0.3],
        "privacy_budgets": [1.0, 0.8, 1.2],
        "prior_strategy_values": [6.5, 7.0],
        "strategy_names": ["status_quo", "privacy_preserving"],
        "noise_scale": 0.0,
        "individual_data_access": "blocked",
        "seed": 0,
    },
    "ai-assisted-evidence-triage": {
        "command": "calculate-ai-assisted-evidence-triage",
        "description": "Template for fixture-backed AI-assisted evidence-triage VOI inputs.",
        "relevance_labels": [1, 1, 0, 1, 0, 1],
        "triage_scores": [0.95, 0.4, 0.8, 0.7, 0.2, 0.6],
        "decision_impacts": [10.0, 8.0, 4.0, 6.0, 3.0, 5.0],
        "reviewer_time_minutes": [10.0, 8.0, 6.0, 7.0, 4.0, 5.0],
        "extraction_error_rates": [0.01, 0.1, 0.05, 0.02, 0.2, 0.03],
        "triage_threshold": 0.5,
        "audit_sample_rate": 0.5,
        "human_override_rate": 0.25,
        "model_drift": 0.1,
        "automation_cost": 2.0,
        "audit_cost_per_item": 0.5,
        "reviewer_cost_per_minute": 0.1,
    },
    "explainability-transparency": {
        "command": "calculate-explainability-transparency",
        "description": "Template for fixture-backed explainability and transparency VOI inputs.",
        "predictive_utilities": [8.0, 7.0, 6.0, 5.0],
        "explanation_quality": [0.9, 0.4, 0.8, 0.2],
        "transparency_evidence": [0.8, 0.3, 0.7, 0.1],
        "trust_scores": [0.9, 0.4, 0.8, 0.2],
        "governance_impacts": [5.0, 3.0, 4.0, 2.0],
        "audit_costs": [1.0, 1.0, 1.0, 1.0],
        "adoption_threshold": 0.5,
        "transparency_weight": 0.5,
    },
    "interoperability-standardization": {
        "command": "calculate-interoperability-standardization",
        "description": "Template for fixture-backed interoperability and standardization VOI inputs.",
        "evidence_utilities": [10.0, 8.0, 6.0, 5.0],
        "schema_compatibility": [0.9, 0.4, 0.8, 0.2],
        "semantic_alignment": [0.8, 0.3, 0.7, 0.1],
        "data_usability": [0.9, 0.5, 0.8, 0.2],
        "transformation_error_rates": [0.05, 0.2, 0.1, 0.3],
        "standardization_costs": [1.0, 1.0, 1.0, 1.0],
        "reuse_probabilities": [0.8, 0.4, 0.7, 0.2],
        "harmonization_threshold": 0.5,
    },
    "regulatory-market-access": {
        "command": "calculate-regulatory-market-access",
        "description": "Template for fixture-backed regulatory and market-access VOI inputs.",
        "scenario_values": [10.0, 8.0, 6.0, 4.0],
        "approval_probabilities": [0.8, 0.5, 0.3, 0.2],
        "reimbursement_probabilities": [0.7, 0.5, 0.2, 0.1],
        "access_delays_months": [2.0, 4.0, 8.0, 12.0],
        "evidence_package_costs": [1.0, 1.0, 1.0, 1.0],
        "label_expansion_values": [3.0, 2.0, 1.0, 0.5],
        "price_threshold_values": [2.0, 1.0, 0.5, 0.25],
        "scenario_names": [
            "approved",
            "restricted_label",
            "coverage_evidence",
            "rejected",
        ],
        "approval_threshold": 0.5,
        "monthly_access_delay_cost": 0.1,
    },
    "replication-reproducibility": {
        "command": "calculate-replication-reproducibility",
        "description": "Template for fixture-backed replication and reproducibility VOI inputs.",
        "evidence_values": [10.0, 8.0, 6.0, 4.0],
        "replication_probabilities": [0.9, 0.5, 0.7, 0.2],
        "reproducibility_failure_risks": [0.1, 0.4, 0.2, 0.8],
        "audit_costs": [1.0, 1.0, 1.0, 1.0],
        "reanalysis_values": [2.0, 1.0, 1.5, 0.5],
        "credibility_adjustments": [1.2, 1.0, 1.1, 0.8],
        "evidence_downgrades": [0.1, 0.3, 0.2, 0.6],
        "replication_threshold": 0.5,
    },
    "evidence-obsolescence-refresh": {
        "command": "calculate-evidence-obsolescence-refresh",
        "description": "Template for fixture-backed evidence obsolescence and refresh VOI inputs.",
        "evidence_values": [10.0, 8.0, 12.0, 6.0, 4.0],
        "evidence_age_months": [2.0, 18.0, 24.0, 15.0, 3.0],
        "half_lives_months": [36.0, 36.0, 36.0, 36.0, 36.0],
        "obsolescence_risks": [0.1, 0.8, 0.9, 0.7, 0.2],
        "refresh_costs": [1.0, 1.0, 1.0, 1.0, 1.0],
        "living_review_values": [0.5, 3.0, 2.0, 1.0, 0.2],
        "model_refresh_values": [0.2, 2.0, 3.0, 1.0, 0.1],
        "drift_rates": [0.1, 0.7, 0.9, 0.6, 0.2],
        "refresh_threshold": 0.5,
        "refresh_cadence_months": 12.0,
    },
    "strategic-behavior": {
        "command": "calculate-strategic-behavior",
        "description": "Template for fixture-backed strategic behavior and game-theoretic VOI inputs.",
        "scenario_values": [10.0, 8.0, 6.0, 4.0],
        "equilibrium_probabilities": [0.8, 0.6, 0.3, 0.2],
        "incentive_response_values": [2.0, 1.0, 0.5, 0.2],
        "disclosure_values": [1.0, 2.0, 0.5, 0.2],
        "bargaining_values": [1.5, 1.0, 0.2, 0.1],
        "adversarial_risks": [0.1, 0.2, 0.4, 0.8],
        "response_sensitivities": [0.2, 0.5, 0.8, 0.9],
        "strategic_regrets": [0.5, 0.4, 0.2, 0.1],
        "equilibrium_threshold": 0.5,
    },
    "preference": {
        "command": "calculate-preference",
        "description": "Template for preference heterogeneity / individualized care inputs.",
        "analysis_id": "preference-screening-001",
        "decision_problem_id": "screening-program-001",
        "net_benefit": [
            [[10.0, 7.0], [8.0, 11.0]],
            [[10.0, 7.0], [8.0, 11.0]],
        ],
        "strategy_names": ["A", "B"],
        "preference_profiles": [
            {
                "id": "access_first",
                "label": "Access first",
                "weight": 0.25,
            },
            {
                "id": "outcomes_first",
                "label": "Outcomes first",
                "weight": 0.75,
            },
        ],
        "reference_preference_profile": "access_first",
    },
    "validation": {
        "command": "calculate-validation",
        "description": "Template for model-validation VOI inputs.",
        "net_benefit": [
            [[10.0, 7.0], [8.0, 11.0]],
            [[10.0, 7.0], [8.0, 11.0]],
        ],
        "strategy_names": ["A", "B"],
        "validation_profiles": [
            {
                "id": "external_validation",
                "label": "External validation",
                "weight": 0.6,
            },
            {
                "id": "discrepancy_reduction",
                "label": "Discrepancy reduction",
                "weight": 0.4,
            },
        ],
        "reference_validation_profile": "external_validation",
    },
    "threshold": {
        "command": "calculate-threshold",
        "description": "Template for threshold, tipping-point, and robust VOI inputs.",
        "net_benefit": [
            [[10.0, 7.0], [8.0, 11.0]],
            [[10.0, 7.0], [8.0, 11.0]],
        ],
        "strategy_names": ["A", "B"],
        "threshold_profiles": [
            {"id": "wtp_reversal", "label": "WTP reversal", "weight": 0.5},
            {
                "id": "policy_constraint",
                "label": "Policy constraint",
                "weight": 0.5,
            },
        ],
        "reference_threshold_profile": "wtp_reversal",
    },
}


def _configure_cli_logging(verbose: bool) -> None:
    """Configure the package logger through the shared logging contract."""
    _CLI_STATE["verbose"] = verbose
    settings = LoggingSettings.from_environment(level="DEBUG" if verbose else "ERROR")
    configure_logging(settings)


def _log_cli_debug(command: str, **details: object) -> None:
    """Emit a structured debug message when verbose logging is enabled."""
    if not cast("bool", _CLI_STATE["verbose"]):
        return

    if details:
        formatted_details = ", ".join(
            f"{key}={value!r}" for key, value in details.items()
        )
        _CLI_LOGGER.debug("%s: %s", command, formatted_details)
        return

    _CLI_LOGGER.debug("%s", command)


@app.callback(invoke_without_command=False)
def main(
    output_format: OutputFormat = typer.Option(
        "text",
        "--format",
        help="Output format for command results: text, json, or csv",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        help="Suppress confirmation messages and keep only the result output",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Emit debug diagnostics to stderr without changing stdout output",
    ),
) -> None:
    """Configure CLI-wide output formatting."""
    _CLI_STATE["output_format"] = output_format
    _CLI_STATE["quiet"] = quiet
    _configure_cli_logging(verbose)


def _read_trial_design_json(path: Path) -> TrialDesign:
    """Read a trial design JSON file."""
    return TrialDesign.from_dict(_read_json_file(path))


def _read_json_file(path: Path) -> object:
    """Read a JSON file and return the decoded object."""
    _log_cli_debug("read-json", path=str(path))
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _read_coss_specification(
    path: Path,
) -> tuple[
    StudyDesignContextV1,
    tuple[StudyDesignPointInputV1, ...],
    FeasibleDesignRangeV1 | None,
    TiePolicy,
    float,
    float,
    SelectionUncertaintyV1 | None,
]:
    """Read and validate an experimental COSS specification."""
    payload = _read_json_file(path)
    if not isinstance(payload, dict):
        raise TypeError("COSS specification must contain a JSON object.")
    context = StudyDesignContextV1.model_validate_json(
        json.dumps(payload.get("context"))
    )
    raw_designs = payload.get("designs")
    if not isinstance(raw_designs, list) or not raw_designs:
        raise TypeError("COSS specification 'designs' must be a non-empty list.")
    designs = tuple(
        StudyDesignPointInputV1.model_validate_json(json.dumps(item))
        for item in raw_designs
    )
    raw_range = payload.get("declared_feasible_range")
    feasible_range = (
        None
        if raw_range is None
        else FeasibleDesignRangeV1.model_validate_json(json.dumps(raw_range))
    )
    tie_policy = cast("TiePolicy", payload.get("tie_policy", "smallest_sample_size"))
    absolute_tolerance = float(payload.get("absolute_tolerance", 1e-12))
    relative_tolerance = float(payload.get("relative_tolerance", 1e-12))
    raw_uncertainty = payload.get("selection_uncertainty")
    selection_uncertainty = (
        None
        if raw_uncertainty is None
        else SelectionUncertaintyV1.model_validate_json(json.dumps(raw_uncertainty))
    )
    return (
        context,
        designs,
        feasible_range,
        tie_policy,
        absolute_tolerance,
        relative_tolerance,
        selection_uncertainty,
    )


def _read_coss_result(path: Path) -> CossResultV1:
    """Read a COSS contract directly or from a CLI result envelope."""
    payload = _read_json_file(path)
    if not isinstance(payload, dict):
        raise TypeError("COSS result must contain a JSON object.")
    candidate = payload.get("result", payload)
    return CossResultV1.model_validate_json(json.dumps(candidate))


def _coss_result_payload(result: CossResultV1) -> dict[str, object]:
    """Return a provenance-bearing CLI envelope for a governed COSS result."""
    context = result.context
    return {
        "command": "calculate-coss",
        "metric": "COSS",
        "method_maturity": "experimental",
        "result": result.model_dump(mode="json"),
        "reporting": build_cheers_reporting(
            analysis_type="calculate-coss",
            method_family="study_design_efficiency",
            method_maturity="experimental",
            decision_problem_id=context.decision_problem_id,
            population=context.population_scale,
            estimator=result.estimator,
            seed=context.random_seed,
            provenance=dict(result.estimator_provenance),
            reproducibility={
                "schema_version": result.schema_version,
                "value_unit": context.value_unit,
                "time_horizon": context.time_horizon,
                "discounting_id": context.discounting_id,
                "study_model_id": context.study_model_id,
                "cost_model_id": context.cost_model_id,
                "tie_policy": result.tie_policy,
                "absolute_tolerance": result.absolute_tolerance,
                "relative_tolerance": result.relative_tolerance,
            },
            diagnostics={
                "codes": list(result.diagnostics),
                "boundary_state": result.boundary_state,
                "tied_optimal_design_ids": list(result.tied_optimal_design_ids),
                "selection_uncertainty_method": result.selection_uncertainty.method,
            },
        ),
    }


def _save_figure(ax: object, output_file: Path) -> None:
    """Save a Matplotlib axes figure to disk."""
    _log_cli_debug("save-figure", output_file=str(output_file))
    figure = getattr(ax, "figure", None)
    if figure is None:
        raise TypeError("Plot function did not return a Matplotlib axes object.")
    figure.savefig(output_file, bbox_inches="tight")


def _csv_string(value: object) -> str:
    """Convert a value to a CSV-safe string."""
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, sort_keys=True)


def _format_output(text_output: str, payload: dict[str, object]) -> str:
    """Format a command response according to the active CLI output format."""
    output_format = cast("OutputFormat", _CLI_STATE["output_format"])
    if output_format == "text":
        return text_output
    if output_format == "json":
        return json.dumps(payload, indent=2, sort_keys=True)
    if output_format == "csv":
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(payload))
        writer.writeheader()
        writer.writerow({key: _csv_string(value) for key, value in payload.items()})
        return buffer.getvalue().strip()
    raise ValueError(f"Unsupported output format: {output_format}")


def _should_echo_status_messages() -> bool:
    """Return whether non-result confirmation messages should be emitted."""
    return (
        cast("bool", _CLI_STATE["quiet"]) is False
        and cast("OutputFormat", _CLI_STATE["output_format"]) == "text"
    )


def _write_output_file(output_file: Path, content: str) -> None:
    """Write command output to a file with a trailing newline."""
    _log_cli_debug("write-output", output_file=str(output_file))
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content + "\n")


def _read_plot_surface(path: Path) -> tuple[ValueArray, list[float]]:
    """Read a 3D net-benefit surface from JSON for CEAC/CEAF plotting."""
    payload = _read_json_file(path)
    if not isinstance(payload, dict):
        raise TypeError("Plot surface file must contain a JSON object.")
    payload = cast("dict[str, object]", payload)
    if "net_benefit" not in payload or "wtp_thresholds" not in payload:
        raise TypeError(
            "Plot surface file must contain 'net_benefit' and 'wtp_thresholds'."
        )

    net_benefit = np.asarray(
        cast("list[list[list[float]]]", payload["net_benefit"]),
        dtype=float,
    )
    if net_benefit.ndim != 3:
        raise TypeError("`net_benefit` must be a 3D array.")

    strategy_names = payload.get("strategy_names")
    if strategy_names is None:
        strategy_names = [f"Strategy {idx + 1}" for idx in range(net_benefit.shape[1])]
    if not isinstance(strategy_names, list):
        raise TypeError("'strategy_names' must be a list when provided.")

    wtp_thresholds = payload["wtp_thresholds"]
    if not isinstance(wtp_thresholds, list):
        raise TypeError("'wtp_thresholds' must be a list.")

    import xarray as xr

    dataset = xr.Dataset(
        {"net_benefit": (("n_samples", "n_strategies", "n_wtp"), net_benefit)},
        coords={
            "n_samples": np.arange(net_benefit.shape[0]),
            "n_strategies": np.arange(net_benefit.shape[1]),
            "n_wtp": np.arange(net_benefit.shape[2]),
            "strategy": ("n_strategies", strategy_names),
        },
    )
    return ValueArray(dataset=dataset), [
        float(cast("float", value)) for value in wtp_thresholds
    ]


def _read_perspective_surface(
    path: Path,
) -> tuple[
    dict[str, object],
    ValueArray,
    list[str] | None,
    list[str] | None,
    object,
    object,
]:
    """Read a multi-perspective net-benefit surface from JSON."""
    payload = _read_json_file(path)
    if not isinstance(payload, dict):
        raise TypeError("Perspective surface file must contain a JSON object.")
    payload = cast("dict[str, object]", payload)
    if "net_benefit" not in payload:
        raise TypeError("Perspective surface file must contain 'net_benefit'.")

    net_benefit = np.asarray(
        cast("list[list[list[float]]]", payload["net_benefit"]),
        dtype=float,
    )
    if net_benefit.ndim != 3:
        raise TypeError(
            "`net_benefit` must be a 3D array (samples x strategies x perspectives)."
        )

    strategy_names = payload.get("strategy_names")
    if strategy_names is not None and not isinstance(strategy_names, list):
        raise TypeError("'strategy_names' must be a list when provided.")
    perspective_names = payload.get("perspective_names")
    if perspective_names is not None and not isinstance(perspective_names, list):
        raise TypeError("'perspective_names' must be a list when provided.")

    value_array = ValueArray.from_numpy_perspectives(
        net_benefit,
        strategy_names=cast("list[str] | None", strategy_names),
        perspective_names=cast("list[str] | None", perspective_names),
    )
    return (
        payload,
        value_array,
        cast("list[str] | None", strategy_names),
        cast("list[str] | None", perspective_names),
        payload.get("perspective_weights"),
        payload.get("reference_perspective"),
        payload.get("analysis_id"),
        payload.get("decision_problem_id"),
    )


def _perspective_result_payload(
    result: ValueOfPerspectiveResult,
    analysis_id: str | None,
    decision_problem_id: str | None,
) -> dict[str, object]:
    """Return a JSON/CSV-safe payload for Value of Perspective results."""
    return {
        "analysis_id": analysis_id,
        "decision_problem_id": decision_problem_id,
        "analysis_type": "value_of_perspective",
        "value": result.value,
        "method_maturity": result.method_maturity,
        "perspective_ids": result.perspective_ids,
        "strategy_names": result.strategy_names,
        "expected_net_benefits": result.expected_net_benefits.tolist(),
        "optimal_strategy_by_perspective": dict(
            zip(result.perspective_ids, result.optimal_strategy_names, strict=True)
        ),
        "regret_matrix": result.regret_matrix.tolist(),
        "switching_values": dict(
            zip(
                result.perspective_ids,
                result.switching_values.tolist(),
                strict=True,
            )
        ),
        "consensus_strategy": result.consensus_strategy_name,
        "robust_strategy": result.robust_strategy_name,
        "pareto_strategies": result.pareto_strategy_names,
        "reference_perspective": result.reference_perspective_id,
        "reporting": result.reporting,
        "diagnostics": result.diagnostics,
    }


def _preference_result_payload(
    result: PreferenceHeterogeneityResult,
    command: str,
) -> dict[str, object]:
    """Return a JSON/CSV-safe payload for preference heterogeneity results."""
    payload = dict(cast("dict[str, object]", result.to_dict()))
    payload["command"] = command
    payload["metric"] = "Value of Preference"
    return payload


def _read_frontier_profile_surface(
    path: Path,
    label: str,
    profile_key: str,
) -> tuple[dict[str, object], ValueArray, list[str] | None, list[object], object]:
    """Read a 3D net-benefit surface for a frontier comparison command."""
    payload = _read_json_file(path)
    if not isinstance(payload, dict):
        raise TypeError(f"{label} input file must contain a JSON object.")
    payload = cast("dict[str, object]", payload)
    if "net_benefit" not in payload:
        raise TypeError(f"{label} input file must contain 'net_benefit'.")

    net_benefit = np.asarray(
        cast("list[list[list[float]]]", payload["net_benefit"]),
        dtype=float,
    )
    if net_benefit.ndim != 3:
        raise TypeError(
            "`net_benefit` must be a 3D array (samples x strategies x profiles)."
        )

    strategy_names = payload.get("strategy_names")
    if strategy_names is not None and not isinstance(strategy_names, list):
        raise TypeError("'strategy_names' must be a list when provided.")

    profile_entries = payload.get(profile_key)
    if profile_entries is None:
        raise TypeError(f"{label} input file must contain '{profile_key}'.")
    if not isinstance(profile_entries, list):
        raise TypeError(f"'{profile_key}' must be a list.")

    reference_profile = payload.get(f"reference_{profile_key[:-1]}")

    value_array = ValueArray.from_numpy_perspectives(
        net_benefit,
        strategy_names=cast("list[str] | None", strategy_names),
        perspective_names=[
            str(entry["id"])
            if isinstance(entry, dict) and "id" in entry
            else str(entry)
            for entry in profile_entries
        ],
    )
    return (
        payload,
        value_array,
        cast("list[str] | None", strategy_names),
        cast("list[object]", profile_entries),
        reference_profile,
    )


def _validation_result_payload(
    result: ModelValidationResult,
    command: str,
) -> dict[str, object]:
    """Return a JSON/CSV-safe payload for model-validation results."""
    return {
        "command": command,
        "metric": "Value of Model Validation",
        "value": result.value,
        "method_maturity": result.method_maturity,
        "reporting": result.reporting,
        "validation_profile_ids": result.validation_profile_ids,
        "validation_profile_labels": result.validation_profile_labels,
        "strategies": result.strategy_names,
        "optimal_strategy_by_validation_profile": dict(
            result.optimal_strategy_by_validation_profile
        ),
        "discrepancy_reduction_value": result.discrepancy_reduction_value,
        "discrepancy_matrix": result.discrepancy_matrix.tolist(),
        "consensus_strategy": result.consensus_strategy,
        "robust_strategy": result.robust_strategy,
        "pareto_strategies": result.pareto_strategies,
        "reference_validation_profile": result.reference_validation_profile,
        "diagnostics": result.diagnostics,
    }


def _threshold_result_payload(
    result: ThresholdResult,
    command: str,
) -> dict[str, object]:
    """Return a JSON/CSV-safe payload for threshold results."""
    return {
        "command": command,
        "metric": "Value of Threshold Information",
        "value": result.value,
        "method_maturity": result.method_maturity,
        "reporting": result.reporting,
        "threshold_profile_ids": result.threshold_profile_ids,
        "threshold_profile_labels": result.threshold_profile_labels,
        "strategies": result.strategy_names,
        "optimal_strategy_by_threshold_profile": dict(
            result.optimal_strategy_by_threshold_profile
        ),
        "threshold_crossing_probability_matrix": (
            result.threshold_crossing_probability_matrix.tolist()
        ),
        "decision_reversal_matrix": result.decision_reversal_matrix.tolist(),
        "robust_strategy": result.robust_strategy,
        "tipping_point_strategy": result.tipping_point_strategy,
        "pareto_strategies": result.pareto_strategies,
        "reference_threshold_profile": result.reference_threshold_profile,
        "diagnostics": result.diagnostics,
    }


def _read_2d_method_surface(
    path: Path,
    label: str,
) -> tuple[dict[str, object], ValueArray, list[str] | None]:
    """Read a 2D net-benefit surface from JSON for frontier CLI commands."""
    payload = _read_json_file(path)
    if not isinstance(payload, dict):
        raise TypeError(f"{label} input file must contain a JSON object.")
    payload = cast("dict[str, object]", payload)
    if "net_benefit" not in payload:
        raise TypeError(f"{label} input file must contain 'net_benefit'.")

    net_benefit = np.asarray(
        cast("list[list[float]]", payload["net_benefit"]),
        dtype=float,
    )
    if net_benefit.ndim != 2:
        raise TypeError("`net_benefit` must be a 2D array (samples x strategies).")

    strategy_names = payload.get("strategy_names")
    if strategy_names is not None and not isinstance(strategy_names, list):
        raise TypeError("'strategy_names' must be a list when provided.")

    value_array = ValueArray.from_numpy(
        net_benefit,
        strategy_names=cast("list[str] | None", strategy_names),
    )
    return payload, value_array, cast("list[str] | None", strategy_names)


def _result_method_maturity(result: object) -> str:
    """Return the method maturity attached to a structured result."""
    maturity = getattr(result, "method_maturity", None)
    if maturity is not None:
        return str(maturity)

    reporting = cast("dict[str, object]", getattr(result, "reporting", {}))
    return str(reporting.get("method_maturity", "unknown"))


def _heterogeneity_result_payload(
    result: HeterogeneityResult,
    command: str,
) -> dict[str, object]:
    """Return a JSON/CSV-safe payload for Value of Heterogeneity results."""
    return {
        "command": command,
        "metric": "Value of Heterogeneity",
        "value": result.value,
        "method_maturity": _result_method_maturity(result),
        "reporting": result.reporting,
        "subgroup_labels": result.subgroup_labels,
        "subgroup_weights": result.subgroup_weights.tolist(),
        "subgroup_optimal_strategy_indices": (
            result.subgroup_optimal_strategy_indices.tolist()
        ),
        "subgroup_optimal_strategy_names": result.subgroup_optimal_strategy_names,
        "subgroup_expected_net_benefits": (
            result.subgroup_expected_net_benefits.tolist()
        ),
        "overall_optimal_strategy_index": result.overall_optimal_strategy_index,
        "overall_optimal_strategy_name": result.overall_optimal_strategy_name,
        "overall_expected_net_benefit": result.overall_expected_net_benefit,
    }


def _distributional_result_payload(
    result: DistributionalEquityResult,
    command: str,
) -> dict[str, object]:
    """Return a JSON/CSV-safe payload for distributional VOI results."""
    return {
        "command": command,
        "metric": "Value of Distributional Equity",
        "value": result.value,
        "method_maturity": _result_method_maturity(result),
        "reporting": result.reporting,
        "subgroup_labels": result.subgroup_labels,
        "subgroup_weights": result.subgroup_weights.tolist(),
        "equity_weights": result.equity_weights.tolist(),
        "subgroup_optimal_strategy_indices": (
            result.subgroup_optimal_strategy_indices.tolist()
        ),
        "subgroup_optimal_strategy_names": result.subgroup_optimal_strategy_names,
        "subgroup_expected_net_benefits": (
            result.subgroup_expected_net_benefits.tolist()
        ),
        "equity_weighted_expected_net_benefits": (
            result.equity_weighted_expected_net_benefits.tolist()
        ),
        "overall_optimal_strategy_index": result.overall_optimal_strategy_index,
        "overall_optimal_strategy_name": result.overall_optimal_strategy_name,
        "social_welfare_optimal_strategy_index": (
            result.social_welfare_optimal_strategy_index
        ),
        "social_welfare_optimal_strategy_name": result.social_welfare_optimal_strategy_name,
        "social_welfare_value": result.social_welfare_value,
        "diagnostics": result.diagnostics,
    }


def _implementation_result_payload(
    result: ImplementationAdjustedResult,
    command: str,
) -> dict[str, object]:
    """Return a JSON/CSV-safe payload for implementation-adjusted VOI results."""
    return {
        "command": command,
        "metric": "Value of Implementation",
        "value": result.value,
        "method_maturity": _result_method_maturity(result),
        "reporting": result.reporting,
        "baseline_expected_net_benefits": (
            result.baseline_expected_net_benefits.tolist()
        ),
        "baseline_optimal_strategy_index": result.baseline_optimal_strategy_index,
        "baseline_optimal_strategy_name": result.baseline_optimal_strategy_name,
        "adjusted_expected_net_benefits": result.adjusted_expected_net_benefits.tolist(),
        "adjusted_optimal_strategy_index": result.adjusted_optimal_strategy_index,
        "adjusted_optimal_strategy_name": result.adjusted_optimal_strategy_name,
        "implementation_multiplier": result.implementation_multiplier,
        "uptake": result.uptake,
        "adherence": result.adherence,
        "coverage": result.coverage,
        "implementation_delay": result.implementation_delay,
        "implementation_uncertainty": result.implementation_uncertainty,
        "discount_rate": result.discount_rate,
        "time_horizon": result.time_horizon,
        "population": result.population,
        "diagnostics": result.diagnostics,
    }


def _optional_float_field(
    payload: dict[str, object],
    key: str,
    default: float | None,
) -> float | None:
    """Read an optional numeric JSON field."""
    value = payload.get(key, default)
    if value is None:
        return default
    return _read_float(value, key)


def _ceaf_result_payload(result: Any, command: str) -> dict[str, object]:
    """Return a JSON/CSV-safe payload for CEAF results."""
    return {
        "command": command,
        "metric": "CEAF",
        "wtp_thresholds": cast("np.ndarray", result.wtp_thresholds).tolist(),
        "optimal_strategy_indices": cast(
            "np.ndarray", result.optimal_strategy_indices
        ).tolist(),
        "optimal_strategy_names": cast("list[str]", result.optimal_strategy_names),
        "acceptability_probabilities": cast(
            "np.ndarray", result.acceptability_probabilities
        ).tolist(),
        "probability_lower": cast("np.ndarray", result.probability_lower).tolist(),
        "probability_upper": cast("np.ndarray", result.probability_upper).tolist(),
        "expected_net_benefit": cast(
            "np.ndarray", result.expected_net_benefit
        ).tolist(),
        "reporting": cast("dict[str, object]", result.reporting),
    }


def _dominance_result_payload(result: Any, command: str) -> dict[str, object]:
    """Return a JSON/CSV-safe payload for dominance results."""
    return {
        "command": command,
        "metric": "Dominance",
        "strategy_names": cast("list[str]", result.strategy_names),
        "costs": cast("np.ndarray", result.costs).tolist(),
        "effects": cast("np.ndarray", result.effects).tolist(),
        "frontier_indices": cast("list[int]", result.frontier_indices),
        "strongly_dominated_indices": cast(
            "list[int]", result.strongly_dominated_indices
        ),
        "extended_dominated_indices": cast(
            "list[int]", result.extended_dominated_indices
        ),
        "status": cast("list[str]", result.status),
        "incremental_costs": cast("np.ndarray", result.incremental_costs).tolist(),
        "incremental_effects": cast("np.ndarray", result.incremental_effects).tolist(),
        "icers": cast("np.ndarray", result.icers).tolist(),
        "reporting": cast("dict[str, object]", result.reporting),
    }


def _scalar_result_payload(
    *,
    command: str,
    metric: str,
    value: float,
    method_family: str,
    estimator: str | None = None,
    reporting_details: dict[str, object] | None = None,
    **details: object,
) -> dict[str, object]:
    """Return a JSON/CSV-safe payload for scalar VOI results."""
    payload: dict[str, object] = {
        "command": command,
        "metric": metric,
        "value": value,
        "reporting": build_cheers_reporting(
            analysis_type=command,
            method_family=method_family,
            method_maturity="stable",
            estimator=estimator,
            reproducibility=reporting_details or {},
        ),
    }
    payload.update(details)
    return payload


def _distributed_large_scale_payload(
    *,
    command: str,
    scheduler: str,
    scheduler_address: str | None,
    cluster_config: object,
    chunk_size: int,
    input_files: dict[str, str | None],
) -> dict[str, object]:
    """Return a JSON-safe payload for distributed CPU/HPC setup."""
    return {
        "command": command,
        "analysis_type": "distributed_large_scale_preparation",
        "scheduler": scheduler,
        "scheduler_is_placeholder": is_placeholder_execution_adapter(scheduler),
        "scheduler_address": scheduler_address,
        "chunk_size": chunk_size,
        "cluster_config": {
            "n_nodes": getattr(cluster_config, "n_nodes", None),
            "workers_per_node": getattr(cluster_config, "workers_per_node", None),
            "use_processes": getattr(cluster_config, "use_processes", None),
            "chunk_count": getattr(cluster_config, "chunk_count", None),
            "total_workers": getattr(cluster_config, "total_workers", None),
            "scheduler": getattr(cluster_config, "scheduler", None),
            "scheduler_address": getattr(cluster_config, "scheduler_address", None),
        },
        "input_files": input_files,
    }


def _read_plot_series(path: Path) -> dict[str, list[float]]:
    """Read a simple plot-series JSON payload."""
    payload = _read_json_file(path)
    if not isinstance(payload, dict):
        raise TypeError("Plot series file must contain a JSON object.")
    payload = cast("dict[str, object]", payload)
    series: dict[str, list[float]] = {}
    for key, values in payload.items():
        if isinstance(values, list):
            series[key] = [float(cast("float", value)) for value in values]
    return series


def _read_cost_effect_csv(path: Path) -> tuple[list[float], list[float], list[str]]:
    """Read dominance plot data from a CSV file with cost/effect columns."""
    costs: list[float] = []
    effects: list[float] = []
    names: list[str] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            names.append(str(row.get("strategy", f"Strategy {len(names) + 1}")))
            costs.append(float(row["cost"]))
            effects.append(float(row["effect"]))
    if not costs:
        raise ValueError("Dominance input file must contain at least one row.")
    return costs, effects, names


def _read_scalar_input(value_or_file: str, label: str) -> float:
    """Read a scalar value directly or from a result file."""
    _log_cli_debug("read-scalar", label=label, value_or_file=value_or_file)
    try:
        return float(value_or_file)
    except ValueError:
        path = Path(value_or_file)
        if not path.exists():
            raise FileNotFoundError(f"{label} file not found at '{path}'") from None

        content = path.read_text(encoding="utf-8").strip()
        match = _SCALAR_PATTERN.search(content)
        if match is None:
            raise ValueError(
                f"{label} file does not contain a numeric value."
            ) from None
        return float(match.group(0))


def _read_float(value: object, label: str) -> float:
    """Parse a numeric JSON value."""
    if not isinstance(value, (int, float)):
        raise TypeError(f"{label} must be a number.")
    return float(value)


def _generate_config_template(template_name: str) -> dict[str, object]:
    """Return a named configuration template for the CLI."""
    try:
        return _CONFIG_TEMPLATES[template_name]
    except KeyError as exc:
        available = ", ".join(sorted(_CONFIG_TEMPLATES))
        raise ValueError(
            f"Unknown config template '{template_name}'. Available templates: {available}"
        ) from exc


@app.command(name="generate-config")
def generate_config(
    template_name: str = typer.Argument(
        ...,
        help="Name of the configuration template to generate (for example: evsi)",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the generated config"
    ),
) -> None:
    """Generate a JSON configuration template for a CLI command.

    Examples
    --------
    Generate an EVSI config template and save it to a file:

    .. code-block:: bash

        voiage generate-config evsi > evsi_config.json
    """
    try:
        _log_cli_debug(
            "generate-config",
            template_name=template_name,
            output_file=str(output_file) if output_file else None,
        )
        payload = _generate_config_template(template_name)
        output_text = json.dumps(payload, indent=2, sort_keys=True)
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="calculate-estimation-variance")
def calculate_estimation_variance(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Versioned estimation-variance specification JSON",
    ),
    data_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help=(
            "Runtime sample JSON; EVSI requires posterior_variances with aligned "
            "predictive_probabilities"
        ),
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="File to save the versioned result and reporting payload",
    ),
) -> None:
    """Calculate experimental scalar ``EVPPI_var`` or ``EVSI_var``."""
    try:
        specification = EstimationVarianceSpec.model_validate_json(
            specification_file.read_text(encoding="utf-8")
        )
        data = json.loads(data_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise TypeError("runtime sample JSON must be an object")
        if specification.method_id == "evppi_var":
            result = evppi_var(
                data["target_samples"],
                data["conditioning_groups"],
                specification=specification,
            )
        else:
            result = evsi_var(
                data["prior_target_samples"],
                data["posterior_variances"],
                data["predictive_probabilities"],
                specification=specification,
            )
        payload = {
            "result": result.model_dump(mode="json"),
            "reporting": build_estimation_variance_reporting(result),
        }
        output_text = json.dumps(payload, indent=2, sort_keys=True)
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command()
def calculate_evpi(
    net_benefit_file: Path = typer.Argument(
        ...,
        metavar="NET_BENEFIT_FILE",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to CSV containing net benefits (samples x strategies)",
    ),
    population: float | None = typer.Option(
        None, "--population", help="Population size for population-adjusted EVPI"
    ),
    discount_rate: float | None = typer.Option(
        None, "--discount-rate", help="Annual discount rate (e.g., 0.03)"
    ),
    time_horizon: float | None = typer.Option(
        None, "--time-horizon", help="Time horizon in years"
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save EVPI result"
    ),
) -> None:
    """Calculate Expected Value of Perfect Information (EVPI) from input data.

    Examples
    --------
    Calculate EVPI from a net-benefits CSV:

    .. code-block:: bash

        voiage calculate-evpi net_benefits.csv
    """
    try:
        _log_cli_debug(
            "calculate-evpi",
            input_file=str(net_benefit_file),
            population=population,
            discount_rate=discount_rate,
            time_horizon=time_horizon,
        )
        # Read net benefit data from CSV
        nba = read_value_array_csv(str(net_benefit_file), skip_header=True)

        # Calculate EVPI
        result = evpi(
            nba,
            population=population,
            discount_rate=discount_rate,
            time_horizon=time_horizon,
        )

        # Format result string
        result_str = f"EVPI: {result:.6f}"
        output_text = _format_output(
            result_str,
            _scalar_result_payload(
                command="calculate-evpi",
                metric="EVPI",
                value=result,
                method_family="evpi",
                estimator="analytic",
                reporting_details={
                    "population": population,
                    "discount_rate": discount_rate,
                    "time_horizon": time_horizon,
                },
            ),
        )

        # Print result to console
        typer.echo(output_text)

        # Save to output file if specified
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")

    except FileNotFoundError:
        typer.echo(
            f"Error: Net benefit file not found at '{net_benefit_file}'", err=True
        )
        raise typer.Exit(code=1) from None
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="create-distributed-large-scale")
def create_distributed_large_scale(
    net_benefit_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to CSV containing net benefits (samples x strategies)",
    ),
    parameter_file: Path | None = typer.Option(
        None,
        "--parameters",
        help="Optional CSV containing parameter samples",
    ),
    chunk_size: int = typer.Option(
        10000, "--chunk-size", help="Chunk size for distributed execution"
    ),
    n_nodes: int = typer.Option(1, "--n-nodes", help="Number of CPU nodes to target"),
    workers_per_node: int | None = typer.Option(
        None, "--workers-per-node", help="Workers to use on each node"
    ),
    scheduler: str = typer.Option(
        "process",
        "--scheduler",
        help="Execution scheduler adapter (process, thread, dask, ray, fpga, or asic)",
    ),
    scheduler_address: str | None = typer.Option(
        None, "--scheduler-address", help="Optional remote scheduler address"
    ),
    use_processes: bool = typer.Option(
        True, "--use-processes/--use-threads", help="Prefer process-based workers"
    ),
    memory_limit_mb: float | None = typer.Option(
        None, "--memory-limit-mb", help="Optional memory limit per worker"
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the distributed config payload"
    ),
) -> None:
    """Prepare a distributed large-scale analysis and emit the cluster plan."""
    try:
        _log_cli_debug(
            "create-distributed-large-scale",
            net_benefit_file=str(net_benefit_file),
            parameter_file=str(parameter_file) if parameter_file else None,
            chunk_size=chunk_size,
            n_nodes=n_nodes,
            workers_per_node=workers_per_node,
            scheduler=scheduler,
            scheduler_address=scheduler_address,
            use_processes=use_processes,
            memory_limit_mb=memory_limit_mb,
        )
        net_benefits = read_value_array_csv(str(net_benefit_file), skip_header=True)
        parameters = (
            read_parameter_set_csv(str(parameter_file), skip_header=True)
            if parameter_file is not None
            else None
        )
        adapter = get_execution_adapter(scheduler)
        _, cluster_config = create_distributed_large_scale_analysis(
            nb_array=net_benefits,
            parameter_samples=parameters,
            chunk_size=chunk_size,
            n_nodes=n_nodes,
            workers_per_node=workers_per_node,
            scheduler=scheduler,
            scheduler_address=scheduler_address,
            use_processes=use_processes,
            memory_limit_mb=memory_limit_mb,
        )
        output_text = _format_output(
            "Distributed large-scale analysis prepared.",
            _distributed_large_scale_payload(
                command="create-distributed-large-scale",
                scheduler=adapter.name,
                scheduler_address=scheduler_address,
                cluster_config=cluster_config,
                chunk_size=chunk_size,
                input_files={
                    "net_benefit_file": str(net_benefit_file),
                    "parameter_file": str(parameter_file) if parameter_file else None,
                },
            ),
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def calculate_evppi(
    net_benefit_file: Path = typer.Argument(
        ...,
        metavar="NET_BENEFIT_FILE",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to CSV containing net benefits (samples x strategies)",
    ),
    parameter_file: Path = typer.Argument(
        ...,
        metavar="PARAMETER_FILE",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to CSV for parameters of interest (samples x params)",
    ),
    population: float | None = typer.Option(
        None, "--population", help="Population size for population-adjusted EVPPI"
    ),
    discount_rate: float | None = typer.Option(
        None, "--discount-rate", help="Annual discount rate (e.g., 0.03)"
    ),
    time_horizon: float | None = typer.Option(
        None, "--time-horizon", help="Time horizon in years"
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save EVPPI result"
    ),
) -> None:
    """Calculate Expected Value of Partial Perfect Information (EVPPI).

    Examples
    --------
    Calculate EVPPI from net-benefit and parameter sample CSV files:

    .. code-block:: bash

        voiage calculate-evppi net_benefits.csv parameters.csv
    """
    try:
        _log_cli_debug(
            "calculate-evppi",
            net_benefit_file=str(net_benefit_file),
            parameter_file=str(parameter_file),
            population=population,
            discount_rate=discount_rate,
            time_horizon=time_horizon,
        )
        # Read net benefit data from CSV
        nba = read_value_array_csv(str(net_benefit_file), skip_header=True)

        # Read parameter data from CSV
        param_set = read_parameter_set_csv(str(parameter_file), skip_header=True)

        # Get parameter names for EVPPI calculation
        parameter_names = param_set.parameter_names

        # Calculate EVPPI
        result = evppi(
            nb_array=nba,
            parameter_samples=param_set,
            parameters_of_interest=parameter_names,
            population=population,
            discount_rate=discount_rate,
            time_horizon=time_horizon,
        )

        # Format result string
        result_str = f"EVPPI: {result:.6f}"
        output_text = _format_output(
            result_str,
            _scalar_result_payload(
                command="calculate-evppi",
                metric="EVPPI",
                value=result,
                method_family="evppi",
                estimator="regression",
                reporting_details={
                    "population": population,
                    "discount_rate": discount_rate,
                    "time_horizon": time_horizon,
                },
            ),
        )

        # Print result to console
        typer.echo(output_text)

        # Save to output file if specified
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")

    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="calculate-calibration")
def calculate_calibration(
    parameter_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to CSV containing PSA parameters (samples x parameters)",
    ),
    calibration_study_design_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON calibration study design",
    ),
    calibration_process_spec_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON calibration process specification",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="Dotted path to a callable accepting ParameterSet and returning ValueArray",
    ),
    population: float | None = typer.Option(
        None, "--population", help="Population size for population-adjusted VOI"
    ),
    discount_rate: float | None = typer.Option(
        None, "--discount-rate", help="Annual discount rate (e.g., 0.03)"
    ),
    time_horizon: float | None = typer.Option(
        None, "--time-horizon", help="Time horizon in years"
    ),
    n_outer_loops: int = typer.Option(
        20, "--n-outer-loops", help="Outer Monte Carlo loops"
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save calibration VOI result"
    ),
) -> None:
    """Calculate calibration VOI from PSA, study design, and process specs.

    Examples
    --------
    Calculate calibration VOI from a parameter CSV and JSON study files:

    .. code-block:: bash

        voiage calculate-calibration parameters.csv calibration_study.json calibration_process.json
    """
    try:
        _log_cli_debug(
            "calculate-calibration",
            parameter_file=str(parameter_file),
            calibration_study_design_file=str(calibration_study_design_file),
            calibration_process_spec_file=str(calibration_process_spec_file),
            model=model,
            population=population,
            discount_rate=discount_rate,
            time_horizon=time_horizon,
            n_outer_loops=n_outer_loops,
        )
        psa_prior = read_parameter_set_csv(str(parameter_file), skip_header=True)
        calibration_study_design_obj = _read_json_file(calibration_study_design_file)
        if not isinstance(calibration_study_design_obj, dict):
            raise TypeError("Calibration study design file must contain a JSON object.")
        calibration_study_design = cast(
            "dict[str, object]", calibration_study_design_obj
        )
        calibration_process_spec_obj = _read_json_file(calibration_process_spec_file)
        if not isinstance(calibration_process_spec_obj, dict):
            raise TypeError(
                "Calibration process specification file must contain a JSON object."
            )
        calibration_process_spec = cast(
            "dict[str, object]", calibration_process_spec_obj
        )

        cal_study_modeler = import_callable(model) if model is not None else None
        result = voi_calibration(
            cal_study_modeler=cal_study_modeler,
            psa_prior=psa_prior,
            calibration_study_design=calibration_study_design,
            calibration_process_spec=calibration_process_spec,
            population=population,
            discount_rate=discount_rate,
            time_horizon=time_horizon,
            n_outer_loops=n_outer_loops,
        )
        result_str = f"Calibration VOI: {result:.6f}"
        output_text = _format_output(
            result_str,
            _scalar_result_payload(
                command="calculate-calibration",
                metric="Calibration VOI",
                value=result,
                method_family="calibration",
                estimator=model or "sophisticated",
                reporting_details={
                    "population": population,
                    "discount_rate": discount_rate,
                    "time_horizon": time_horizon,
                    "n_outer_loops": n_outer_loops,
                    "calibration_study_design": calibration_study_design_file.name,
                    "calibration_process_spec": calibration_process_spec_file.name,
                },
            ),
        )
        typer.echo(output_text)

        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except json.JSONDecodeError as e:
        typer.echo(f"Error: Invalid JSON in calibration input file - {e}", err=True)
        raise typer.Exit(code=1) from e
    except (TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def calculate_evsi(
    parameter_file: Path = typer.Argument(
        ...,
        metavar="PARAMETER_FILE",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to CSV containing PSA parameters (samples x parameters)",
    ),
    trial_design_file: Path = typer.Argument(
        ...,
        metavar="TRIAL_DESIGN_FILE",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON trial design with an 'arms' array",
    ),
    net_benefit_file: Path | None = typer.Option(
        None,
        "--net-benefit-file",
        "-n",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="CSV net benefits used by the default static model",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="Dotted path to a callable accepting ParameterSet and returning ValueArray",
    ),
    method: str = typer.Option(
        "two_loop",
        "--method",
        help="EVSI method: two_loop, regression, efficient, or moment_based",
    ),
    metamodel: str = typer.Option(
        "linear",
        "--metamodel",
        help="Metamodel for efficient EVSI: linear or random_forest",
    ),
    n_outer_loops: int = typer.Option(
        100,
        "--n-outer-loops",
        help="Outer simulations for two_loop/regression EVSI",
    ),
    n_inner_loops: int = typer.Option(
        1000,
        "--n-inner-loops",
        help="Inner simulations for two_loop EVSI",
    ),
    population: float | None = typer.Option(
        None, "--population", help="Population size for population-adjusted EVSI"
    ),
    discount_rate: float | None = typer.Option(
        None, "--discount-rate", help="Annual discount rate (e.g., 0.03)"
    ),
    time_horizon: float | None = typer.Option(
        None, "--time-horizon", help="Time horizon in years"
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save EVSI result"
    ),
) -> None:
    """Calculate Expected Value of Sample Information (EVSI).

    Examples
    --------
    Calculate EVSI from a PSA parameter CSV and a trial design JSON file:

    .. code-block:: bash

        voiage calculate-evsi parameters.csv trial_design.json
    """
    try:
        _log_cli_debug(
            "calculate-evsi",
            parameter_file=str(parameter_file),
            trial_design_file=str(trial_design_file),
            net_benefit_file=str(net_benefit_file) if net_benefit_file else None,
            model=model,
            method=method,
            metamodel=metamodel,
            n_outer_loops=n_outer_loops,
            n_inner_loops=n_inner_loops,
            population=population,
            discount_rate=discount_rate,
            time_horizon=time_horizon,
        )
        param_set = read_parameter_set_csv(str(parameter_file), skip_header=True)
        trial_design = _read_trial_design_json(trial_design_file)

        if model is not None:
            model_func = import_callable(model)
        elif net_benefit_file is not None:
            nba = read_value_array_csv(str(net_benefit_file), skip_header=True)

            def model_func(_: ParameterSet) -> ValueArray:
                return nba

        else:
            typer.echo(
                "Error: provide either --model or --net-benefit-file for EVSI.",
                err=True,
            )
            raise typer.Exit(code=1)

        result = evsi(
            model_func=model_func,
            psa_prior=param_set,
            trial_design=trial_design,
            population=population,
            discount_rate=discount_rate,
            time_horizon=time_horizon,
            method=method,
            n_outer_loops=n_outer_loops,
            n_inner_loops=n_inner_loops,
            metamodel=metamodel,
        )
        result_str = f"EVSI: {result:.6f}"
        output_text = _format_output(
            result_str,
            _scalar_result_payload(
                command="calculate-evsi",
                metric="EVSI",
                value=result,
                method_family="evsi",
                estimator=method,
                reporting_details={
                    "population": population,
                    "discount_rate": discount_rate,
                    "time_horizon": time_horizon,
                    "metamodel": metamodel,
                    "n_outer_loops": n_outer_loops,
                    "n_inner_loops": n_inner_loops,
                },
            ),
        )

        typer.echo(output_text)

        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")

    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except json.JSONDecodeError as e:
        typer.echo(f"Error: Invalid JSON in trial design file - {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def calculate_enbs(
    evsi_input: str = typer.Option(
        ...,
        "--evsi",
        help="EVSI value or path to a file containing a numeric EVSI result",
    ),
    research_cost: float = typer.Option(
        ...,
        "--research-cost",
        help="Total cost of the proposed research",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save ENBS result"
    ),
) -> None:
    """Calculate Expected Net Benefit of Sampling (ENBS).

    Examples
    --------
    Calculate ENBS from an EVSI value and research cost:

    .. code-block:: bash

        voiage calculate-enbs --evsi 12.5 --research-cost 10.0
    """
    try:
        _log_cli_debug(
            "calculate-enbs",
            evsi_input=evsi_input,
            research_cost=research_cost,
        )
        evsi_result = _read_scalar_input(evsi_input, "EVSI")
        result = enbs(evsi_result=evsi_result, research_cost=research_cost)
        result_str = f"ENBS: {result:.6f}"
        output_text = _format_output(
            result_str,
            _scalar_result_payload(
                command="calculate-enbs",
                metric="ENBS",
                value=result,
                method_family="enbs",
                estimator="difference",
                evsi_input=evsi_input,
                research_cost=research_cost,
                reporting_details={
                    "evsi_input": evsi_input,
                    "research_cost": research_cost,
                },
            ),
        )
        typer.echo(output_text)

        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="calculate-coss")
def calculate_coss_command(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to a governed experimental COSS JSON specification",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the COSS result"
    ),
) -> None:
    """Evaluate an experimental Curve of Optimal Sample Size (COSS).

    The JSON specification records the common value/cost context, every
    evaluated design, feasibility, tie policy, and optional uncertainty.
    Signed ENBS values are preserved, including when all designs are negative.
    """
    try:
        _log_cli_debug(
            "calculate-coss",
            specification_file=str(specification_file),
            output_file=str(output_file) if output_file else None,
        )
        (
            context,
            designs,
            feasible_range,
            tie_policy,
            absolute_tolerance,
            relative_tolerance,
            selection_uncertainty,
        ) = _read_coss_specification(specification_file)
        result = calculate_coss_result(
            context=context,
            designs=designs,
            declared_feasible_range=feasible_range,
            tie_policy=tie_policy,
            absolute_tolerance=absolute_tolerance,
            relative_tolerance=relative_tolerance,
            selection_uncertainty=selection_uncertainty,
        )
        if result.optimal_design_id is None:
            text_result = "COSS optimum: unavailable (no feasible design)"
        else:
            text_result = (
                f"COSS optimum: {result.optimal_design_id} "
                f"(sample size {result.optimal_sample_size})\n"
                f"Maximum ENBS: {result.maximum_enbs:.6f}\n"
                f"Boundary: {result.boundary_state}"
            )
        output_text = _format_output(text_result, _coss_result_payload(result))
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except FileNotFoundError as error:
        typer.echo(f"Error: File not found - {error}", err=True)
        raise typer.Exit(code=1) from error
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error
    except Exception as error:
        typer.echo(f"An error occurred: {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command(name="calculate-observational")
def calculate_observational(
    parameter_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to CSV containing PSA parameters (samples x parameters)",
    ),
    observational_study_design_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON observational study design",
    ),
    bias_models_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON bias-model specification",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="Dotted path to a callable accepting ParameterSet and returning ValueArray",
    ),
    population: float | None = typer.Option(
        None, "--population", help="Population size for population-adjusted VOI"
    ),
    discount_rate: float | None = typer.Option(
        None, "--discount-rate", help="Annual discount rate (e.g., 0.03)"
    ),
    time_horizon: float | None = typer.Option(
        None, "--time-horizon", help="Time horizon in years"
    ),
    n_outer_loops: int = typer.Option(
        20, "--n-outer-loops", help="Outer Monte Carlo loops"
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save observational VOI result"
    ),
) -> None:
    """Calculate observational VOI from PSA, study design, and bias models.

    Examples
    --------
    Calculate observational VOI from a parameter CSV and JSON study files:

    .. code-block:: bash

        voiage calculate-observational parameters.csv observational_study.json bias_models.json
    """
    try:
        _log_cli_debug(
            "calculate-observational",
            parameter_file=str(parameter_file),
            observational_study_design_file=str(observational_study_design_file),
            bias_models_file=str(bias_models_file),
            model=model,
            population=population,
            discount_rate=discount_rate,
            time_horizon=time_horizon,
            n_outer_loops=n_outer_loops,
        )
        psa_prior = read_parameter_set_csv(str(parameter_file), skip_header=True)
        observational_study_design_obj = _read_json_file(
            observational_study_design_file
        )
        if not isinstance(observational_study_design_obj, dict):
            raise TypeError(
                "Observational study design file must contain a JSON object."
            )
        observational_study_design = cast(
            "dict[str, object]", observational_study_design_obj
        )
        bias_models_obj = _read_json_file(bias_models_file)
        if not isinstance(bias_models_obj, dict):
            raise TypeError("Bias models file must contain a JSON object.")
        bias_models = cast("dict[str, object]", bias_models_obj)

        obs_study_modeler = import_callable(model) if model is not None else None
        result = voi_observational(
            obs_study_modeler=obs_study_modeler,
            psa_prior=psa_prior,
            observational_study_design=observational_study_design,
            bias_models=bias_models,
            population=population,
            discount_rate=discount_rate,
            time_horizon=time_horizon,
            n_outer_loops=n_outer_loops,
        )
        result_str = f"Observational VOI: {result:.6f}"
        output_text = _format_output(
            result_str,
            _scalar_result_payload(
                command="calculate-observational",
                metric="Observational VOI",
                value=result,
                method_family="observational",
                estimator=model or "basic",
                reporting_details={
                    "population": population,
                    "discount_rate": discount_rate,
                    "time_horizon": time_horizon,
                    "n_outer_loops": n_outer_loops,
                    "observational_study_design": observational_study_design_file.name,
                    "bias_models": bias_models_file.name,
                },
            ),
        )
        typer.echo(output_text)

        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except json.JSONDecodeError as e:
        typer.echo(f"Error: Invalid JSON in observational input file - {e}", err=True)
        raise typer.Exit(code=1) from e
    except (TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def calculate_adaptive_evsi(
    parameter_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to CSV containing PSA parameters (samples x parameters)",
    ),
    trial_design_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON trial design with arm definitions",
    ),
    adaptive_rules_file: Path = typer.Option(
        ...,
        "--adaptive-rules",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON adaptive rules specification",
    ),
    simulator: str = typer.Option(
        "bayesian",
        "--simulator",
        help="Adaptive simulator to use: bayesian or sophisticated",
    ),
    population: float | None = typer.Option(
        None, "--population", help="Population size for population-adjusted EVSI"
    ),
    discount_rate: float | None = typer.Option(
        None, "--discount-rate", help="Annual discount rate (e.g., 0.03)"
    ),
    time_horizon: float | None = typer.Option(
        None, "--time-horizon", help="Time horizon in years"
    ),
    n_outer_loops: int = typer.Option(
        10, "--n-outer-loops", help="Outer Monte Carlo loops"
    ),
    n_inner_loops: int = typer.Option(
        50, "--n-inner-loops", help="Inner Monte Carlo loops"
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save adaptive EVSI result"
    ),
) -> None:
    """Calculate Expected Value of Sample Information for adaptive trial designs.

    Examples
    --------
    Calculate adaptive EVSI from parameters, a trial design, and rules:

    .. code-block:: bash

        voiage calculate-adaptive-evsi parameters.csv trial_design.json --adaptive-rules adaptive_rules.json
    """
    try:
        _log_cli_debug(
            "calculate-adaptive-evsi",
            parameter_file=str(parameter_file),
            trial_design_file=str(trial_design_file),
            adaptive_rules_file=str(adaptive_rules_file),
            simulator=simulator,
            population=population,
            discount_rate=discount_rate,
            time_horizon=time_horizon,
            n_outer_loops=n_outer_loops,
            n_inner_loops=n_inner_loops,
        )
        param_set = read_parameter_set_csv(str(parameter_file), skip_header=True)
        trial_design = _read_trial_design_json(trial_design_file)
        adaptive_rules_obj = _read_json_file(adaptive_rules_file)
        if not isinstance(adaptive_rules_obj, dict):
            raise TypeError("Adaptive rules file must contain a JSON object.")
        adaptive_rules = cast("dict[str, object]", adaptive_rules_obj)

        if simulator == "bayesian":
            adaptive_simulator = bayesian_adaptive_trial_simulator
        elif simulator == "sophisticated":
            adaptive_simulator = sophisticated_adaptive_trial_simulator
        else:
            raise ValueError("simulator must be one of: bayesian, sophisticated.")

        result = adaptive_evsi(
            adaptive_trial_simulator=adaptive_simulator,
            psa_prior=param_set,
            base_trial_design=trial_design,
            adaptive_rules=adaptive_rules,
            population=population,
            discount_rate=discount_rate,
            time_horizon=time_horizon,
            n_outer_loops=n_outer_loops,
            n_inner_loops=n_inner_loops,
        )
        result_str = f"Adaptive EVSI: {result:.6f}"
        output_text = _format_output(
            result_str,
            {
                "command": "calculate-adaptive-evsi",
                "metric": "Adaptive EVSI",
                "value": result,
                "simulator": simulator,
            },
        )
        typer.echo(output_text)

        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except json.JSONDecodeError as e:
        typer.echo(f"Error: Invalid JSON in input file - {e}", err=True)
        raise typer.Exit(code=1) from e
    except (TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def calculate_portfolio_voi(
    portfolio_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON portfolio specification",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save portfolio VOI result"
    ),
) -> None:
    """Optimize a research portfolio using the portfolio VOI methods.

    Examples
    --------
    Optimize a portfolio from a JSON specification:

    .. code-block:: bash

        voiage calculate-portfolio-voi portfolio.json
    """
    try:
        _log_cli_debug(
            "calculate-portfolio-voi",
            portfolio_file=str(portfolio_file),
        )
        config_obj = _read_json_file(portfolio_file)
        if not isinstance(config_obj, dict):
            raise TypeError("Portfolio file must contain a JSON object.")
        config = cast("dict[str, object]", config_obj)

        studies_data = config.get("studies")
        if not isinstance(studies_data, list) or not studies_data:
            raise TypeError("Portfolio file must contain a non-empty 'studies' list.")
        studies_data = cast("list[object]", studies_data)

        studies: list[PortfolioStudy] = []
        study_values: dict[str, float] = {}
        for study_data in studies_data:
            if not isinstance(study_data, dict):
                raise TypeError("Each portfolio study must be a JSON object.")
            study_data = cast("dict[str, object]", study_data)
            if "name" not in study_data or "cost" not in study_data:
                raise TypeError("Each study must include 'name' and 'cost'.")
            if "design" not in study_data or "value" not in study_data:
                raise TypeError("Each study must include 'design' and 'value'.")

            name = str(study_data["name"])
            cost = _read_float(study_data["cost"], f"Study '{name}' cost")
            value = _read_float(study_data["value"], f"Study '{name}' value")
            design_obj = study_data["design"]
            if not isinstance(design_obj, dict):
                raise TypeError(f"Study '{name}' design must be a JSON object.")

            studies.append(
                PortfolioStudy(
                    name=name,
                    design=TrialDesign.from_dict(design_obj),
                    cost=cost,
                )
            )
            study_values[name] = value

        budget_constraint = None
        if "budget_constraint" in config and config["budget_constraint"] is not None:
            budget_constraint = _read_float(
                config["budget_constraint"], "budget_constraint"
            )

        portfolio_spec = PortfolioSpec(
            studies=studies,
            budget_constraint=budget_constraint,
        )

        optimization_method = str(config.get("optimization_method", "greedy"))
        dependency_groups = config.get("dependency_groups")
        dependency_discount = _read_float(
            config.get("dependency_discount", 0.0), "dependency_discount"
        )

        result = portfolio_voi(
            portfolio_specification=portfolio_spec,
            study_value_calculator=lambda study: study_values[study.name],
            optimization_method=optimization_method,
            dependency_groups=dependency_groups
            if isinstance(dependency_groups, dict)
            else None,
            dependency_discount=dependency_discount,
        )

        selected_studies = cast("list[PortfolioStudy]", result["selected_studies"])
        selected_names = ", ".join(study.name for study in selected_studies)
        if not selected_names:
            selected_names = "None"

        total_value = float(cast("float", result["total_value"]))
        total_cost = float(cast("float", result["total_cost"]))
        text_output = "\n".join(
            [
                f"Selected studies: {selected_names}",
                f"Total value: {total_value:.6f}",
                f"Total cost: {total_cost:.6f}",
            ]
        )
        output_text = _format_output(
            text_output,
            {
                "command": "calculate-portfolio-voi",
                "selected_studies": [study.name for study in selected_studies],
                "total_value": total_value,
                "total_cost": total_cost,
                "optimization_method": optimization_method,
            },
        )
        typer.echo(output_text)

        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except json.JSONDecodeError as e:
        typer.echo(f"Error: Invalid JSON in portfolio file - {e}", err=True)
        raise typer.Exit(code=1) from e
    except (TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


def _sequential_passthrough_step_model(
    psa: ParameterSet, action: object, specification: DynamicSpec
) -> dict[str, object]:
    """Default CLI step model that preserves the current PSA state.

    The sequential CLI does not accept a user-supplied transition model yet.
    Returning the current PSA as the next state keeps the wrapper callable and
    lets the sequential engine progress deterministically without pretending to
    model a more complex transition.
    """
    _ = action, specification
    return {"next_psa": psa}


@app.command()
def calculate_sequential_voi(
    parameter_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to CSV containing PSA parameters (samples x parameters)",
    ),
    dynamic_spec_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON dynamic specification with time_steps",
    ),
    wtp: float = typer.Option(0.0, "--wtp", help="Willingness-to-pay threshold"),
    population: float | None = typer.Option(
        None, "--population", help="Population size for scaling"
    ),
    discount_rate: float | None = typer.Option(
        None, "--discount-rate", help="Annual discount rate (e.g., 0.03)"
    ),
    time_horizon: float | None = typer.Option(
        None, "--time-horizon", help="Time horizon in years"
    ),
    optimization_method: str = typer.Option(
        "backward_induction",
        "--optimization-method",
        help="Sequential optimization method",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save sequential VOI result"
    ),
) -> None:
    """Calculate sequential VOI using a dynamic specification.

    Examples
    --------
    Calculate sequential VOI from a parameter CSV and dynamic spec JSON:

    .. code-block:: bash

        voiage calculate-sequential-voi parameters.csv dynamic_spec.json
    """
    try:
        _log_cli_debug(
            "calculate-sequential-voi",
            parameter_file=str(parameter_file),
            dynamic_spec_file=str(dynamic_spec_file),
            wtp=wtp,
            population=population,
            discount_rate=discount_rate,
            time_horizon=time_horizon,
            optimization_method=optimization_method,
        )
        initial_psa = read_parameter_set_csv(str(parameter_file), skip_header=True)
        dynamic_spec_obj = _read_json_file(dynamic_spec_file)
        if not isinstance(dynamic_spec_obj, dict):
            raise TypeError("Dynamic spec file must contain a JSON object.")
        dynamic_spec_obj = cast("dict[str, object]", dynamic_spec_obj)
        if "time_steps" not in dynamic_spec_obj:
            raise TypeError("Dynamic spec file must contain 'time_steps'.")

        time_steps = cast("list[float]", dynamic_spec_obj["time_steps"])
        dynamic_spec = DynamicSpec(time_steps=time_steps)
        result = sequential_voi(
            step_model=_sequential_passthrough_step_model,
            initial_psa=initial_psa,
            dynamic_specification=dynamic_spec,
            wtp=wtp,
            population=population,
            discount_rate=discount_rate,
            time_horizon=time_horizon,
            optimization_method=optimization_method,
        )

        if optimization_method == "generator" and not isinstance(result, (int, float)):
            if not isinstance(result, Iterable):
                raise TypeError(
                    "Sequential VOI generator did not return an iterable result."
                )
            try:
                total = 0.0
                for step in result:
                    if not isinstance(step, dict) or "discounted_evpi" not in step:
                        raise TypeError(
                            "Sequential VOI generator did not return numeric step summaries."
                        )
                    total += float(step["discounted_evpi"])
                result = total
            except (KeyError, TypeError, ValueError) as exc:
                raise TypeError(
                    "Sequential VOI generator did not return numeric step summaries."
                ) from exc

        if not isinstance(result, (int, float)):
            raise TypeError("Sequential VOI did not return a numeric result.")

        result_str = f"Sequential VOI: {float(result):.6f}"
        output_text = _format_output(
            result_str,
            {
                "command": "calculate-sequential-voi",
                "metric": "Sequential VOI",
                "value": float(result),
                "wtp": wtp,
                "optimization_method": optimization_method,
            },
        )
        typer.echo(output_text)

        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except json.JSONDecodeError as e:
        typer.echo(f"Error: Invalid JSON in dynamic spec file - {e}", err=True)
        raise typer.Exit(code=1) from e
    except (TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def calculate_structural_evpi(
    config_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON config file defining model structures",
    ),
    population: float | None = typer.Option(
        None,
        "--population",
        help="Population size for population-adjusted structural EVPI",
    ),
    discount_rate: float | None = typer.Option(
        None, "--discount-rate", help="Annual discount rate (e.g., 0.03)"
    ),
    time_horizon: float | None = typer.Option(
        None, "--time-horizon", help="Time horizon in years"
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save structural EVPI result"
    ),
) -> None:
    r"""Calculate Structural Expected Value of Perfect Information (SEVPI).

    Structural EVPI quantifies the expected gain from knowing with certainty
    which model structure is the most appropriate one. The config file should
    be a JSON file with the following format:

    \b
    {
      "structures": [
        {
          "name": "model_a",
          "probability": 0.6,
          "net_benefits_file": "net_benefits_a.csv"
        },
        {
          "name": "model_b",
          "probability": 0.4,
          "net_benefits_file": "net_benefits_b.csv"
        }
      ]
    }

    Examples
    --------
    Calculate structural EVPI from a JSON config:

    .. code-block:: bash

        voiage calculate-structural-evpi structural_config.json
    """
    try:
        _log_cli_debug(
            "calculate-structural-evpi",
            config_file=str(config_file),
            population=population,
            discount_rate=discount_rate,
            time_horizon=time_horizon,
        )
        # Read config file
        config = json.loads(config_file.read_text(encoding="utf-8"))

        if "structures" not in config:
            typer.echo("Error: Config file must contain 'structures' key", err=True)
            raise typer.Exit(code=1)

        structures = config["structures"]

        # Validate probabilities sum to 1
        total_prob = sum(s["probability"] for s in structures)
        if not np.isclose(total_prob, 1.0):
            typer.echo(
                f"Error: Structure probabilities must sum to 1 (got {total_prob})",
                err=True,
            )
            raise typer.Exit(code=1)

        # Create model structure evaluators
        evaluators = []
        psa_samples = []

        for struct in structures:
            nb_file = struct["net_benefits_file"]
            nb_path = Path(nb_file)
            if not nb_path.is_absolute():
                nb_path = config_file.parent / nb_path

            # Read net benefits
            nba = read_value_array_csv(str(nb_path), skip_header=True)

            # Create evaluator function
            def make_evaluator(nb_array: object) -> Callable[[object], object]:
                def evaluator(psa_sample: object) -> object:
                    return nb_array

                return evaluator

            evaluators.append(make_evaluator(nba))

            # Create PSA sample (use net benefit values as proxy)
            psa = ParameterSet.from_numpy_or_dict(
                {
                    f"param_{i}": nba.numpy_values[:, i]
                    if i < nba.numpy_values.shape[1]
                    else nba.numpy_values[:, 0]
                    for i in range(max(1, nba.numpy_values.shape[1]))
                }
            )
            psa_samples.append(psa)

        # Extract probabilities
        probabilities = [s["probability"] for s in structures]

        # Calculate structural EVPI
        result = structural_evpi(
            evaluators,
            probabilities,
            psa_samples,
            population=population,
            discount_rate=discount_rate,
            time_horizon=time_horizon,
        )

        # Format result string
        result_str = f"Structural EVPI: {result:.6f}"
        output_text = _format_output(
            result_str,
            {
                "command": "calculate-structural-evpi",
                "metric": "Structural EVPI",
                "value": result,
            },
        )

        # Print result to console
        typer.echo(output_text)

        # Save to output file if specified
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")

    except FileNotFoundError:
        typer.echo(f"Error: Config file not found at '{config_file}'", err=True)
        raise typer.Exit(code=1) from None
    except json.JSONDecodeError as e:
        typer.echo(f"Error: Invalid JSON in config file - {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def calculate_structural_evppi(
    config_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON config file defining model structures",
    ),
    structures_of_interest: list[int] | None = typer.Option(
        None,
        "--structures-of-interest",
        "-s",
        help="Indices of structures to learn about (0-indexed, can specify multiple)",
    ),
    parameters_of_interest: list[int] | None = typer.Option(
        None,
        "--parameters-of-interest",
        "-p",
        help="Alias for --structures-of-interest for structural EVPPI",
    ),
    population: float | None = typer.Option(
        None,
        "--population",
        help="Population size for population-adjusted structural EVPPI",
    ),
    discount_rate: float | None = typer.Option(
        None, "--discount-rate", help="Annual discount rate (e.g., 0.03)"
    ),
    time_horizon: float | None = typer.Option(
        None, "--time-horizon", help="Time horizon in years"
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save structural EVPPI result"
    ),
) -> None:
    """Calculate Structural Expected Value of Partial Perfect Information (SEVPPI).

    Structural EVPPI quantifies the expected gain from resolving uncertainty
    about a specific subset of model structures.

    The config file format is the same as for structural EVPI.

    Examples
    --------
    Calculate structural EVPPI for selected structures:

    .. code-block:: bash

        voiage calculate-structural-evppi structural_config.json --structures-of-interest 0 2
    """
    try:
        _log_cli_debug(
            "calculate-structural-evppi",
            config_file=str(config_file),
            structures_of_interest=structures_of_interest,
            parameters_of_interest=parameters_of_interest,
            population=population,
            discount_rate=discount_rate,
            time_horizon=time_horizon,
        )
        selected_structures = structures_of_interest or parameters_of_interest
        if not selected_structures:
            typer.echo(
                "Error: --structures-of-interest or --parameters-of-interest is required",
                err=True,
            )
            raise typer.Exit(code=1)

        # Read config file
        config = json.loads(config_file.read_text(encoding="utf-8"))

        if "structures" not in config:
            typer.echo("Error: Config file must contain 'structures' key", err=True)
            raise typer.Exit(code=1)

        structures = config["structures"]

        # Validate probabilities sum to 1
        total_prob = sum(s["probability"] for s in structures)
        if not np.isclose(total_prob, 1.0):
            typer.echo(
                f"Error: Structure probabilities must sum to 1 (got {total_prob})",
                err=True,
            )
            raise typer.Exit(code=1)

        # Create model structure evaluators
        evaluators = []
        psa_samples = []

        for struct in structures:
            nb_file = struct["net_benefits_file"]
            nb_path = Path(nb_file)
            if not nb_path.is_absolute():
                nb_path = config_file.parent / nb_path

            # Read net benefits
            nba = read_value_array_csv(str(nb_path), skip_header=True)

            # Create evaluator function
            def make_evaluator(nb_array: object) -> Callable[[object], object]:
                def evaluator(psa_sample: object) -> object:
                    return nb_array

                return evaluator

            evaluators.append(make_evaluator(nba))

            # Create PSA sample
            psa = ParameterSet.from_numpy_or_dict(
                {
                    f"param_{i}": nba.numpy_values[:, i]
                    if i < nba.numpy_values.shape[1]
                    else nba.numpy_values[:, 0]
                    for i in range(max(1, nba.numpy_values.shape[1]))
                }
            )
            psa_samples.append(psa)

        # Extract probabilities
        probabilities = [s["probability"] for s in structures]

        # Calculate structural EVPPI
        result = structural_evppi(
            evaluators,
            probabilities,
            psa_samples,
            structures_of_interest=list(selected_structures),
            population=population,
            discount_rate=discount_rate,
            time_horizon=time_horizon,
        )

        # Format result string
        result_str = f"Structural EVPPI: {result:.6f}"
        output_text = _format_output(
            result_str,
            {
                "command": "calculate-structural-evppi",
                "metric": "Structural EVPPI",
                "value": result,
                "structures_of_interest": list(selected_structures),
            },
        )

        # Print result to console
        typer.echo(output_text)

        # Save to output file if specified
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")

    except FileNotFoundError:
        typer.echo(f"Error: Config file not found at '{config_file}'", err=True)
        raise typer.Exit(code=1) from None
    except json.JSONDecodeError as e:
        typer.echo(f"Error: Invalid JSON in config file - {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def calculate_nma_voi(
    config_file: Path = typer.Argument(
        ...,
        metavar="CONFIG_FILE",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON config file defining NMA data",
    ),
    parameters_of_interest: str | None = typer.Option(
        None,
        "--parameters-of-interest",
        "-p",
        help="Comma-separated list of parameters for EVPPI (e.g., 'effect_A,effect_B')",
    ),
    willingness_to_pay: float | None = typer.Option(
        None, "--willingness-to-pay", "-w", help="Willingness-to-pay threshold per unit"
    ),
    population: float | None = typer.Option(
        None, "--population", help="Population size for population-adjusted VOI"
    ),
    discount_rate: float | None = typer.Option(
        None, "--discount-rate", help="Annual discount rate (e.g., 0.03)"
    ),
    time_horizon: float | None = typer.Option(
        None, "--time-horizon", help="Time horizon in years"
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save NMA VOI result"
    ),
) -> None:
    r"""Calculate VOI for Network Meta-Analysis (NMA-EVPI or NMA-EVPPI).

    The config file should be a JSON file with the following format:

    \b
    {
      "treatment_effects": {
        "Placebo-Drug_A": [0.5, 0.6, 0.4, ...],
        "Placebo-Drug_B": [0.7, 0.8, 0.6, ...],
        "Drug_A-Drug_B": [0.2, 0.1, 0.3, ...]
      },
      "n_studies": 10,
      "treatments": ["Placebo", "Drug_A", "Drug_B"],
      "outcome_type": "continuous"
    }

    If --parameters-of-interest is provided, calculates EVPPI; otherwise EVPI.

    Examples
    --------
    Calculate NMA EVPI from a JSON config:

    .. code-block:: bash

        voiage calculate-nma-voi nma_config.json
    """
    try:
        _log_cli_debug(
            "calculate-nma-voi",
            config_file=str(config_file),
            parameters_of_interest=parameters_of_interest,
            willingness_to_pay=willingness_to_pay,
            population=population,
            discount_rate=discount_rate,
            time_horizon=time_horizon,
        )
        # Read config file
        config = json.loads(config_file.read_text(encoding="utf-8"))

        # Convert list values to numpy arrays
        treatment_effects = {}
        for key, values in config.get("treatment_effects", {}).items():
            pair = tuple(key.split("-")) if isinstance(key, str) and "-" in key else key
            treatment_effects[pair] = np.asarray(values, dtype=float)

        config["treatment_effects"] = treatment_effects

        # Calculate NMA VOI
        if parameters_of_interest:
            # EVPPI calculation
            params_list = [p.strip() for p in parameters_of_interest.split(",")]

            # Generate parameter samples from treatment effects
            n_samples = next(iter(treatment_effects.values())).shape[0]
            parameter_samples = {
                param: np.random.rand(n_samples) for param in params_list
            }

            result = calculate_nma_evppi(
                config,
                parameters_of_interest=params_list,
                parameter_samples=parameter_samples,
                willingness_to_pay=willingness_to_pay,
                population=population,
                discount_rate=discount_rate,
                time_horizon=time_horizon,
            )
            result_str = f"NMA-EVPPI: {result:.6f}"
        else:
            # EVPI calculation
            result = calculate_nma_evpi(
                config,
                willingness_to_pay=willingness_to_pay,
                population=population,
                discount_rate=discount_rate,
                time_horizon=time_horizon,
            )
            result_str = f"NMA-EVPI: {result:.6f}"
        output_text = _format_output(
            result_str,
            {
                "command": "calculate-nma-voi",
                "metric": "NMA-EVPPI" if parameters_of_interest else "NMA-EVPI",
                "value": result,
                "parameters_of_interest": params_list if parameters_of_interest else [],
            },
        )

        # Print result to console
        typer.echo(output_text)

        # Save to output file if specified
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")

    except FileNotFoundError:
        typer.echo(f"Error: Config file not found at '{config_file}'", err=True)
        raise typer.Exit(code=1) from None
    except json.JSONDecodeError as e:
        typer.echo(f"Error: Invalid JSON in config file - {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def calculate_perspective(
    surface_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON surface data for Value of Perspective",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save Value of Perspective result"
    ),
) -> None:
    """Calculate experimental Value of Perspective from a JSON surface file.

    Examples
    --------
    Calculate perspective regret and consensus strategy:

    .. code-block:: bash

        voiage calculate-perspective perspective_surface.json
    """
    try:
        _log_cli_debug(
            "calculate-perspective",
            surface_file=str(surface_file),
            output_file=str(output_file) if output_file else None,
        )
        (
            _payload,
            value_array,
            strategy_names,
            perspective_names,
            perspective_weights,
            reference_perspective,
            analysis_id,
            decision_problem_id,
        ) = _read_perspective_surface(surface_file)
        if not isinstance(analysis_id, str) or not analysis_id.strip():
            raise TypeError("Perspective surface file must contain 'analysis_id'.")
        if not isinstance(decision_problem_id, str) or not decision_problem_id.strip():
            raise TypeError(
                "Perspective surface file must contain 'decision_problem_id'."
            )
        result = calculate_perspective_result(
            value_array,
            strategy_names=strategy_names,
            perspective_names=perspective_names,
            perspective_weights=cast(
                "list[float] | dict[str, float] | None",
                perspective_weights,
            ),
            reference_perspective=cast("str | int | None", reference_perspective),
        )
        result_str = (
            f"Value of Perspective: {result.value:.6f}\n"
            f"Consensus strategy: {result.consensus_strategy_name}\n"
            f"Robust strategy: {result.robust_strategy_name}"
        )
        output_text = _format_output(
            result_str,
            _perspective_result_payload(
                result,
                analysis_id,
                decision_problem_id,
            ),
        )

        typer.echo(output_text)

        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")

    except FileNotFoundError:
        typer.echo(f"Error: Surface file not found at '{surface_file}'", err=True)
        raise typer.Exit(code=1) from None
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="calculate-dynamic-real-options")
def calculate_dynamic_real_options(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON staged dynamic real-options specification",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the dynamic real-options result"
    ),
) -> None:
    """Calculate fixture-backed dynamic real-options VOI from JSON."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError("Dynamic real-options specification must be a JSON object.")
        result = calculate_dynamic_real_options_result(
            np.asarray(payload["net_benefit"], dtype=float),
            cast("list[str]", payload["decision_stage_names"]),
            cast("list[str]", payload["strategy_names"]),
            cast("dict[str, float] | None", payload.get("stage_weights")),
            float(payload.get("discount_rate", 0.0)),
            float(payload.get("irreversibility_penalty", 0.0)),
            float(payload.get("lock_in_penalty", 0.0)),
            cast("dict[str, float] | None", payload.get("evidence_arrival_times")),
            cast("dict[str, str] | None", payload.get("exercise_rules")),
        )
        result_payload = {
            "analysis_type": "value_of_dynamic_real_options",
            "decision_stage_names": result.decision_stage_names,
            "strategy_names": result.strategy_names,
            "expected_net_benefits": result.expected_net_benefits.tolist(),
            "optimal_strategy_names": result.optimal_strategy_names,
            "waiting_value": result.waiting_value,
            "option_value": result.option_value,
            "policy_path_regret": result.policy_path_regret.tolist(),
            "timing_sensitivity": result.timing_sensitivity.tolist(),
            "robust_strategy_name": result.robust_strategy_name,
            "pareto_strategy_names": result.pareto_strategy_names,
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        output_text = _format_output(
            f"Dynamic real-options VOI: {result.option_value:.6f}\n"
            f"Robust strategy: {result.robust_strategy_name}",
            result_payload,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="calculate-deterministic-sensitivity")
def calculate_deterministic_sensitivity(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to a deterministic-sensitivity-input-v1 JSON specification",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="File to save the deterministic sensitivity result",
    ),
) -> None:
    """Calculate experimental deterministic one/two-way and scenario analysis."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError("DSA specification must be a JSON object.")
        result = calculate_deterministic_sensitivity_result(payload)
        result_payload = result.to_contract_dict()
        output_text = _format_output(
            "Deterministic sensitivity evaluated "
            f"{result.evaluated_record_count} records ({result.output_unit})",
            result_payload,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command(name="calculate-value-of-flexibility")
def calculate_value_of_flexibility(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to a value-of-flexibility v1 JSON specification",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the Value of Flexibility result"
    ),
) -> None:
    """Calculate experimental timing-scenario Value of Flexibility."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError("Value of Flexibility specification must be a JSON object.")
        Draft202012Validator(VALUE_OF_FLEXIBILITY_INPUT_SCHEMA_V1).validate(payload)
        result = calculate_flexibility_result(
            np.asarray(payload["net_benefit"], dtype=float),
            cast("list[str]", payload["decision_stage_names"]),
            cast("list[str]", payload["strategy_names"]),
            cast("dict[str, float]", payload["stage_weights"]),
            cast("dict[str, str]", payload["provenance"]),
            float(payload.get("discount_rate", 0.0)),
            float(payload.get("irreversibility_penalty", 0.0)),
            float(payload.get("lock_in_penalty", 0.0)),
            cast("dict[str, float] | None", payload.get("evidence_arrival_times")),
            flexible_policy_sets=cast(
                "dict[str, list[str]] | None", payload.get("flexible_policy_sets")
            ),
            constrained_strategy_names=cast(
                "list[str] | None", payload.get("constrained_strategy_names")
            ),
            value_unit=str(payload["value_unit"]),
            stage_semantics=str(payload["stage_semantics"]),
            information_value_included=bool(payload["information_value_included"]),
        )
        result_payload = {
            "analysis_type": result.analysis_type,
            "method_maturity": result.method_maturity,
            "value_unit": result.value_unit,
            "stage_semantics": result.stage_semantics,
            "decision_stage_names": result.decision_stage_names,
            "strategy_names": result.strategy_names,
            "provenance": result.provenance,
            "flexible_value": result.flexible_value,
            "constrained_value": result.constrained_value,
            "value_of_flexibility": result.value_of_flexibility,
            "flexible_policy_path": result.flexible_policy_path,
            "constrained_policy_path": result.constrained_policy_path,
            "commitment_baseline": result.commitment_baseline,
            "waiting_value": result.waiting_value,
            "option_value": result.option_value,
            "information_value_component": result.information_value_component,
            "decomposition_status": result.decomposition_status,
            "exercise_decisions": result.exercise_decisions,
            "ordered_scenario_policy_changes": result.ordered_scenario_policy_changes,
            "policy_path_regret": result.policy_path_regret.tolist(),
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        output_text = _format_output(
            f"Value of Flexibility: {result.value_of_flexibility:.6f} "
            f"{result.value_unit}",
            result_payload,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except (
        json.JSONDecodeError,
        JsonSchemaValidationError,
        ArithmeticError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command(name="calculate-value-of-distributional-information")
def calculate_value_of_distributional_information(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to a distribution-family-information v1 JSON specification",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="File to save the distribution-family information result",
    ),
) -> None:
    """Calculate experimental perfect model-family-index information value."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError(
                "Distribution-family information specification must be a JSON object."
            )
        Draft202012Validator(
            VALUE_OF_DISTRIBUTIONAL_INFORMATION_INPUT_SCHEMA_V1
        ).validate(payload)
        result = calculate_distributional_information_result(payload)
        output_text = _format_output(
            f"Distribution-family information value: {result.gross_vdi:.6f} "
            f"{result.value_unit}; signed net VDI: {result.net_vdi:.6f} "
            f"{result.value_unit}",
            result.to_contract_dict(),
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except (
        json.JSONDecodeError,
        JsonSchemaValidationError,
        ArithmeticError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command(name="calculate-mcda-information")
def calculate_mcda_information(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to a finite additive MCDA information v1 JSON specification",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="File to save the MCDA information result",
    ),
) -> None:
    """Evaluate experimental exact finite additive-MCDA information value."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError("MCDA information specification must be a JSON object.")
        result = calculate_mcda_information_result(cast("dict[str, object]", payload))
        contract = result.to_contract_dict()
        decomposition = cast("dict[str, object]", contract["decomposition"])
        output_text = _format_output(
            "MCDA information value: "
            f"joint {float(decomposition['joint_gross_voi']):.6f}; "
            f"criterion {float(decomposition['criterion_gross_voi']):.6f}; "
            f"preference {float(decomposition['preference_gross_voi']):.6f}; "
            f"interaction {float(decomposition['interaction']):.6f} "
            f"{contract['aggregate_unit']}",
            contract,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except (
        json.JSONDecodeError,
        ArithmeticError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command(name="calculate-event-localized-information")
def calculate_event_localized_information(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to an event-localized information v1 JSON specification",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="File to save the event-localized information result",
    ),
) -> None:
    """Evaluate experimental exact finite event-localized information value."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError(
                "Event-localized information specification must be a JSON object."
            )
        result = calculate_event_localized_information_result(
            cast("dict[str, object]", payload)
        )
        contract = result.to_contract_dict()
        event = cast("dict[str, object]", contract["event"])
        density = cast("dict[str, object]", contract["density"])
        output_text = _format_output(
            "Event-localized information value: "
            f"event {float(event['perfect_gross_voi']):.6f}; "
            f"density {float(density['information_value']):.6f} "
            f"{contract['value_unit']}",
            contract,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except (
        json.JSONDecodeError,
        ArithmeticError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command(name="calculate-outcome-conditional-sample-information")
def calculate_outcome_conditional_sample_information(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to an outcome-conditional sample-information v1 JSON specification",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="File to save the outcome-conditional sample-information result",
    ),
) -> None:
    """Evaluate exact finite experimental outcome-conditional sample value."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError(
                "Outcome-conditional sample-information specification must be "
                "a JSON object."
            )
        result = calculate_outcome_conditional_result(
            cast("dict[str, object]", payload)
        )
        contract = result.to_contract_dict()
        aggregate = cast("dict[str, object]", contract["aggregate"])
        output_text = _format_output(
            "Outcome-conditional sample-information value: "
            f"EVSI {float(aggregate['evsi']):.6f}; "
            f"sigma-VSI {float(aggregate['sigma_vsi']):.6f}; "
            f"net {float(aggregate['net_evsi']):.6f} "
            f"{contract['value_unit']}",
            contract,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except (
        json.JSONDecodeError,
        ArithmeticError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command(name="calculate-implementation-information")
def calculate_implementation_information(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to an implementation-information v1 JSON specification",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="File to save the implementation-information result",
    ),
) -> None:
    """Evaluate the experimental finite information/implementation matrix."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError(
                "Implementation-information specification must be an object."
            )
        result = calculate_implementation_information_result(
            cast("dict[str, object]", payload)
        )
        contract = result.to_contract_dict()
        gross = cast("dict[str, object]", contract["gross_components"])
        output_text = _format_output(
            "Implementation-information value: "
            f"EVP {float(gross['evp']):.6f}; "
            f"realizable EVPI {float(gross['realizable_evpi']):.6f}; "
            f"EVPIM {float(gross['evpim']):.6f} {contract['value_unit']}",
            contract,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except (
        json.JSONDecodeError,
        ArithmeticError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command(name="calculate-belief-state-information")
def calculate_belief_state_information(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to a belief-state information v1 JSON specification",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="File to save the belief-state information result",
    ),
) -> None:
    """Evaluate experimental finite belief-state sequential information."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError("Belief-state information specification must be an object.")
        contract = calculate_belief_state_information_result(
            cast("dict[str, object]", payload)
        ).to_contract_dict()
        values = cast("dict[str, object]", contract["values"])
        output_text = _format_output(
            "Belief-state information value: "
            f"net {float(values['net_information_value']):.6f}; "
            f"gross {float(values['gross_information_value']):.6f} "
            f"{contract['value_unit']}",
            contract,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except (
        json.JSONDecodeError,
        ArithmeticError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command(name="calculate-forecast-signal-information")
def calculate_forecast_signal_information(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to a finite forecast-signal information v1 JSON specification",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="File to save the forecast-signal information result",
    ),
) -> None:
    """Evaluate experimental finite forecast-signal decision value."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError(
                "forecast-signal information specification must be a JSON object."
            )
        result = calculate_forecast_signal_information_result(
            cast("dict[str, object]", payload)
        )
        contract = result.to_contract_dict()
        value = cast("dict[str, object]", contract["value"])
        output_text = _format_output(
            "Forecast-signal information value: "
            f"gross {float(value['gross_deployed']):.6f}; "
            f"net {float(value['net_deployed']):.6f}; "
            f"maximum price {float(value['maximum_price']):.6f} "
            f"{contract['value_unit']}",
            contract,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except (
        json.JSONDecodeError,
        ArithmeticError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command(name="calculate-risk-sensitive-voi")
def calculate_risk_sensitive_voi(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to a risk-sensitive constrained VOI v1 JSON specification",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the risk-sensitive VOI result"
    ),
) -> None:
    """Evaluate experimental exact finite risk-sensitive constrained VOI."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError("Risk-sensitive VOI specification must be a JSON object.")
        contract = calculate_risk_sensitive_voi_result(
            cast("dict[str, object]", payload)
        ).to_contract_dict()
        value = cast("dict[str, object]", contract["value"])
        output_text = _format_output(
            "Risk-sensitive constrained VOI: "
            f"gross {float(value['gross']):.6f}; net {float(value['net']):.6f} "
            f"{value['unit']}",
            contract,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except (
        json.JSONDecodeError,
        ArithmeticError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command(name="calculate-information-source-portfolio")
def calculate_information_source_portfolio(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to an information-source portfolio v1 JSON specification",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="File to save the information-source portfolio result",
    ),
) -> None:
    """Optimize an experimental exact finite information-source sequence."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError(
                "Information-source portfolio specification must be a JSON object."
            )
        result = calculate_information_source_portfolio_result(
            cast("dict[str, object]", payload)
        )
        contract = result.to_contract_dict()
        optimum = cast("dict[str, object]", contract["optimum"])
        sequence = cast("list[str]", optimum["source_sequence"])
        context = cast("dict[str, object]", contract["value_context"])
        output_text = _format_output(
            "Information-source portfolio: "
            f"{', '.join(sequence) if sequence else 'no procurement'}; "
            f"gross {float(cast('float', optimum['gross_value'])):.6f}; "
            f"net {float(cast('float', optimum['net_value'])):.6f} "
            f"{context['value_unit']}",
            contract,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except (
        json.JSONDecodeError,
        ArithmeticError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command(name="calculate-heterogeneity-value")
def calculate_heterogeneity_value(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to a heterogeneity-value decomposition v1 specification",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="File to save the heterogeneity-value result",
    ),
) -> None:
    """Evaluate experimental exact finite static/dynamic heterogeneity value."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError("Heterogeneity-value specification must be a JSON object.")
        result = calculate_heterogeneity_value_result(
            cast("dict[str, object]", payload)
        )
        contract = result.to_contract_dict()
        decomposition = cast("dict[str, object]", contract["four_value_decomposition"])
        objective = cast("dict[str, object]", contract["objective"])
        output_text = _format_output(
            "Heterogeneity value: "
            f"Static {float(decomposition['static_value']):.6f}; "
            f"dynamic {float(decomposition['dynamic_value']):.6f} "
            f"{objective['value_unit']}",
            contract,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except (
        json.JSONDecodeError,
        ArithmeticError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command(name="calculate-uncertainty-modelling-value")
def calculate_uncertainty_modelling_value(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to an uncertainty-modelling value v1 JSON specification",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="File to save the EVIU/VSS result",
    ),
) -> None:
    """Evaluate experimental exact finite EVIU, VSS and EVPI diagnostics."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError(
                "Uncertainty-modelling value specification must be a JSON object."
            )
        result = calculate_uncertainty_modelling_value_result(
            cast("dict[str, object]", payload)
        )
        contract = result.to_contract_dict()
        decomposition = cast("dict[str, object]", contract["decomposition"])
        objective = cast("dict[str, object]", contract["objective"])
        output_text = _format_output(
            "Uncertainty-modelling value: "
            f"EVIU/VSS {decomposition['vss']}; "
            f"EVPI {float(cast('float', decomposition['evpi'])):.6f} "
            f"{objective['value_unit']}",
            contract,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except (
        json.JSONDecodeError,
        ArithmeticError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command(name="calculate-signed-social-information")
def calculate_signed_social_information(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to a signed-social information v1 JSON specification",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="File to save the signed-social information result",
    ),
) -> None:
    """Evaluate experimental exact finite signed/social information value."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError(
                "Signed-social information specification must be a JSON object."
            )
        contract = calculate_signed_social_information_result(
            cast("dict[str, object]", payload)
        ).to_contract_dict()
        optimum = cast("dict[str, object]", contract["optimum"])
        output_text = _format_output(
            "Signed-social information value: "
            f"design {optimum['selected_design_id']}; "
            f"social {float(optimum['social_value']):.6f} "
            f"{contract['value_unit']}",
            contract,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except (
        json.JSONDecodeError,
        ArithmeticError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command(name="assess-qualitative-information")
def assess_qualitative_information(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to a qualitative-information assessment v1 JSON specification",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="File to save the qualitative assessment result",
    ),
) -> None:
    """Evaluate an experimental non-cardinal qualitative information workflow."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError(
                "Qualitative information specification must be a JSON object."
            )
        payload = cast("dict[str, object]", payload)
        result = calculate_qualitative_information_result(payload)
        output_text = _format_output(
            render_qualitative_information_text(result).rstrip(),
            result.to_contract_dict(),
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command(name="calculate-causal-transportability")
def calculate_causal_transportability(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON causal transportability specification",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the causal transportability result"
    ),
) -> None:
    """Calculate fixture-backed causal transportability VOI from JSON."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError(
                "Causal transportability specification must be a JSON object."
            )
        result = calculate_causal_transportability_result(
            np.asarray(payload["net_benefit"], dtype=float),
            cast("list[str]", payload["source_population_ids"]),
            cast("list[str]", payload["target_population_ids"]),
            cast("list[str]", payload["strategy_names"]),
            np.asarray(payload["transport_weights"], dtype=float),
            np.asarray(payload["validity_penalties"], dtype=float),
            analysis_id=str(
                payload.get("analysis_id", "causal-transportability-analysis")
            ),
            decision_problem_id=str(payload.get("decision_problem_id", "unspecified")),
            reference_target_population=cast(
                "str | None", payload.get("reference_target_population")
            ),
        )
        result_payload = {
            "analysis_type": "value_of_causal_transportability",
            "method_maturity": result.method_maturity,
            "value": result.value,
            "causal_identification_value": result.causal_identification_value,
            "transportability_value": result.transportability_value,
            "external_validity_value": result.external_validity_value,
            "source_population_ids": result.source_population_ids,
            "target_population_ids": result.target_population_ids,
            "strategy_names": result.strategy_names,
            "expected_net_benefits": result.expected_net_benefits.tolist(),
            "optimal_strategy_by_target_population": result.optimal_strategy_by_target_population,
            "transport_weight_matrix": result.transport_weight_matrix.tolist(),
            "validity_penalty_matrix": result.validity_penalty_matrix.tolist(),
            "robust_strategy": result.robust_strategy,
            "pareto_strategies": result.pareto_strategies,
            "reference_target_population": result.reference_target_population,
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        output_text = _format_output(
            f"Causal transportability VOI: {result.value:.6f}\n"
            f"Robust strategy: {result.robust_strategy}",
            result_payload,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except (KeyError, json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="calculate-data-quality")
def calculate_data_quality(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON data-quality specification",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the data-quality result"
    ),
) -> None:
    """Calculate fixture-backed data-quality and privacy VOI from JSON."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError("Data-quality specification must be a JSON object.")
        result = calculate_data_quality_result(
            np.asarray(payload["net_benefit"], dtype=float),
            cast("list[str]", payload["data_quality_profile_ids"]),
            cast("list[str]", payload["strategy_names"]),
            np.asarray(payload["acquisition_costs"], dtype=float),
            np.asarray(payload["privacy_constraints"], dtype=float),
            np.asarray(payload["measurement_error_rates"], dtype=float),
            np.asarray(payload["linkage_weights"], dtype=float),
            analysis_id=str(payload.get("analysis_id", "data-quality-analysis")),
            decision_problem_id=str(payload.get("decision_problem_id", "unspecified")),
            reference_data_quality_profile=cast(
                "str | None", payload.get("reference_data_quality_profile")
            ),
        )
        result_payload = {
            "analysis_type": "value_of_data_quality_privacy_linkage",
            "method_maturity": result.method_maturity,
            "value": result.value,
            "acquisition_cost_value": result.acquisition_cost_value,
            "privacy_value": result.privacy_value,
            "measurement_error_value": result.measurement_error_value,
            "linkage_value": result.linkage_value,
            "data_quality_profile_ids": result.data_quality_profile_ids,
            "strategy_names": result.strategy_names,
            "expected_net_benefits": result.expected_net_benefits.tolist(),
            "optimal_strategy_by_data_quality_profile": result.optimal_strategy_by_data_quality_profile,
            "acquisition_cost_matrix": result.acquisition_cost_matrix.tolist(),
            "privacy_constraint_matrix": result.privacy_constraint_matrix.tolist(),
            "measurement_error_matrix": result.measurement_error_matrix.tolist(),
            "linkage_weight_matrix": result.linkage_weight_matrix.tolist(),
            "consensus_strategy": result.consensus_strategy,
            "robust_strategy": result.robust_strategy,
            "pareto_strategies": result.pareto_strategies,
            "reference_data_quality_profile": result.reference_data_quality_profile,
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        output_text = _format_output(
            f"Data-quality VOI: {result.value:.6f}\n"
            f"Robust strategy: {result.robust_strategy}",
            result_payload,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except (KeyError, json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="calculate-computational-refinement")
def calculate_computational_refinement(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON computational refinement specification",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the computational result"
    ),
) -> None:
    """Calculate fixture-backed computational refinement VOI from JSON."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError("Computational specification must be a JSON object.")
        result = calculate_computational_result(
            np.asarray(payload["net_benefit"], dtype=float),
            cast("list[str]", payload["compute_budget_ids"]),
            cast("list[str]", payload["strategy_names"]),
            np.asarray(payload["compute_costs"], dtype=float),
            np.asarray(payload["approximation_errors"], dtype=float),
            np.asarray(payload["refinement_weights"], dtype=float),
            analysis_id=str(payload.get("analysis_id", "computational-analysis")),
            decision_problem_id=str(payload.get("decision_problem_id", "unspecified")),
            reference_compute_budget=cast(
                "str | None", payload.get("reference_compute_budget")
            ),
        )
        result_payload = {
            "analysis_type": "value_of_computational_refinement",
            "method_maturity": result.method_maturity,
            "value": result.value,
            "compute_value": result.compute_value,
            "approximation_error_value": result.approximation_error_value,
            "refinement_value": result.refinement_value,
            "compute_budget_ids": result.compute_budget_ids,
            "strategy_names": result.strategy_names,
            "expected_net_benefits": result.expected_net_benefits.tolist(),
            "optimal_strategy_by_compute_budget": result.optimal_strategy_by_compute_budget,
            "compute_cost_matrix": result.compute_cost_matrix.tolist(),
            "approximation_error_matrix": result.approximation_error_matrix.tolist(),
            "refinement_weight_matrix": result.refinement_weight_matrix.tolist(),
            "consensus_strategy": result.consensus_strategy,
            "robust_strategy": result.robust_strategy,
            "pareto_strategies": result.pareto_strategies,
            "reference_compute_budget": result.reference_compute_budget,
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        output_text = _format_output(
            f"Computational refinement VOI: {result.value:.6f}\n"
            f"Robust strategy: {result.robust_strategy}",
            result_payload,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except (KeyError, json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="calculate-expert-synthesis")
def calculate_expert_synthesis(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON expert synthesis specification",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the expert synthesis result"
    ),
) -> None:
    """Calculate fixture-backed expert synthesis VOI from JSON."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError("Expert synthesis specification must be a JSON object.")
        result = calculate_expert_synthesis_result(
            np.asarray(payload["net_benefit"], dtype=float),
            cast("list[str]", payload["expert_profile_ids"]),
            cast("list[str]", payload["strategy_names"]),
            np.asarray(payload["elicitation_costs"], dtype=float),
            np.asarray(payload["synthesis_penalties"], dtype=float),
            analysis_id=str(payload.get("analysis_id", "expert-synthesis-analysis")),
            decision_problem_id=str(payload.get("decision_problem_id", "unspecified")),
            reference_expert_profile=cast(
                "str | None", payload.get("reference_expert_profile")
            ),
        )
        result_payload = {
            "analysis_type": "value_of_expert_synthesis",
            "method_maturity": result.method_maturity,
            "value": result.value,
            "elicitation_value": result.elicitation_value,
            "synthesis_design_value": result.synthesis_design_value,
            "expert_profile_ids": result.expert_profile_ids,
            "strategy_names": result.strategy_names,
            "expected_net_benefits": result.expected_net_benefits.tolist(),
            "optimal_strategy_by_expert_profile": result.optimal_strategy_by_expert_profile,
            "elicitation_cost_matrix": result.elicitation_cost_matrix.tolist(),
            "synthesis_penalty_matrix": result.synthesis_penalty_matrix.tolist(),
            "consensus_strategy": result.consensus_strategy,
            "robust_strategy": result.robust_strategy,
            "pareto_strategies": result.pareto_strategies,
            "reference_expert_profile": result.reference_expert_profile,
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        output_text = _format_output(
            f"Expert synthesis VOI: {result.value:.6f}\n"
            f"Robust strategy: {result.robust_strategy}",
            result_payload,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except (KeyError, json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="calculate-monitoring-surveillance")
def calculate_monitoring_surveillance(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON monitoring and surveillance specification",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the monitoring result"
    ),
) -> None:
    """Calculate fixture-backed monitoring and surveillance VOI from JSON."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError("Monitoring specification must be a JSON object.")
        result = calculate_monitoring_surveillance_result(
            np.asarray(payload["net_benefit"], dtype=float),
            cast("list[str]", payload["strategy_names"]),
            np.asarray(payload["monitoring_costs"], dtype=float),
            np.asarray(payload["detection_delays"], dtype=float),
            np.asarray(payload["false_signal_rates"], dtype=float),
            np.asarray(payload["decision_revision_probabilities"], dtype=float),
            surveillance_frequency=float(payload.get("surveillance_frequency", 1.0)),
            stopping_threshold=float(payload.get("stopping_threshold", 0.5)),
            analysis_id=str(
                payload.get("analysis_id", "monitoring-surveillance-analysis")
            ),
            decision_problem_id=str(payload.get("decision_problem_id", "unspecified")),
        )
        result_payload = {
            "analysis_type": "value_of_monitoring_surveillance",
            "method_maturity": result.method_maturity,
            "value": result.value,
            "monitoring_value": result.monitoring_value,
            "signal_detection_value": result.signal_detection_value,
            "decision_revision_value": result.decision_revision_value,
            "stopping_value": result.stopping_value,
            "strategy_names": result.strategy_names,
            "expected_net_benefits": result.expected_net_benefits.tolist(),
            "optimal_strategy_by_period": result.optimal_strategy_by_period,
            "monitoring_cost_matrix": result.monitoring_cost_matrix.tolist(),
            "detection_delay_matrix": result.detection_delay_matrix.tolist(),
            "false_signal_rate_matrix": result.false_signal_rate_matrix.tolist(),
            "decision_revision_matrix": result.decision_revision_matrix.tolist(),
            "surveillance_frequency": result.surveillance_frequency,
            "stopping_period": result.stopping_period,
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        output_text = _format_output(
            f"Monitoring and surveillance VOI: {result.value:.6f}\n"
            f"Stopping period: {result.stopping_period}",
            result_payload,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except (KeyError, json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="calculate-implementation-strategy")
def calculate_implementation_strategy(
    specification_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON implementation-strategy comparison specification",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the implementation comparison result"
    ),
) -> None:
    """Calculate fixture-backed implementation-strategy comparison VOI."""
    try:
        payload = _read_json_file(specification_file)
        if not isinstance(payload, dict):
            raise TypeError(
                "Implementation strategy specification must be a JSON object."
            )
        result = calculate_implementation_strategy_result(
            np.asarray(payload["net_benefit"], dtype=float),
            cast("list[str]", payload["strategy_names"]),
            np.asarray(payload["uptake"], dtype=float),
            np.asarray(payload["adherence"], dtype=float),
            np.asarray(payload["coverage"], dtype=float),
            np.asarray(payload["implementation_delays"], dtype=float),
            np.asarray(payload["scale_up_costs"], dtype=float),
            np.asarray(payload["population_impacts"], dtype=float),
            discount_rate=float(payload.get("discount_rate", 0.0)),
            analysis_id=str(
                payload.get("analysis_id", "implementation-strategy-analysis")
            ),
            decision_problem_id=str(payload.get("decision_problem_id", "unspecified")),
        )
        result_payload = {
            "analysis_type": "value_of_implementation_strategy_comparison",
            "method_maturity": result.method_maturity,
            "value": result.value,
            "implementation_value": result.implementation_value,
            "strategy_names": result.strategy_names,
            "expected_net_benefits": result.expected_net_benefits.tolist(),
            "optimal_strategy_by_period": result.optimal_strategy_by_period,
            "uptake_matrix": result.uptake_matrix.tolist(),
            "adherence_matrix": result.adherence_matrix.tolist(),
            "coverage_matrix": result.coverage_matrix.tolist(),
            "implementation_delay_matrix": result.implementation_delay_matrix.tolist(),
            "scale_up_cost_matrix": result.scale_up_cost_matrix.tolist(),
            "population_impact_matrix": result.population_impact_matrix.tolist(),
            "implementation_multiplier_matrix": result.implementation_multiplier_matrix.tolist(),
            "adoption_uncertainty_matrix": result.adoption_uncertainty_matrix.tolist(),
            "population_impact_by_strategy": result.population_impact_by_strategy,
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        output_text = _format_output(
            f"Implementation strategy comparison VOI: {result.value:.6f}\n"
            f"Best period-one strategy: {result.optimal_strategy_by_period['0']}",
            result_payload,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except (KeyError, json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="calculate-preference")
def calculate_preference(
    surface_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON surface data for preference heterogeneity VOI",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save preference result"
    ),
) -> None:
    """Calculate preference heterogeneity and individualized-care VOI.

    Examples
    --------
    Calculate preference regret and consensus strategy:

    .. code-block:: bash

        voiage calculate-preference preference_surface.json
    """
    try:
        _log_cli_debug(
            "calculate-preference",
            surface_file=str(surface_file),
            output_file=str(output_file) if output_file else None,
        )
        (
            payload,
            value_array,
            strategy_names,
            profile_entries,
            reference_preference_profile,
        ) = _read_frontier_profile_surface(
            surface_file,
            "Preference surface",
            "preference_profiles",
        )
        profiles = PreferenceProfileSet(
            [
                PreferenceProfile(**entry)
                if isinstance(entry, dict)
                else PreferenceProfile(id=str(entry))
                for entry in profile_entries
            ]
        )
        from voiage.methods.preference import (
            value_of_preference as calculate_preference_result,
        )

        result = calculate_preference_result(
            value_array,
            preference_profiles=profiles,
            strategy_names=strategy_names,
            reference_preference_profile=cast(
                "str | int | None", reference_preference_profile
            ),
            analysis_id=cast("str | None", payload.get("analysis_id")),
            decision_problem_id=cast("str | None", payload.get("decision_problem_id")),
        )
        result_str = (
            f"Value of Preference: {result.value:.6f}\n"
            f"Consensus strategy: {result.consensus_strategy_name}\n"
            f"Robust strategy: {result.robust_strategy_name}"
        )
        output_text = _format_output(
            result_str,
            _preference_result_payload(result, "calculate-preference"),
        )

        typer.echo(output_text)

        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")

    except FileNotFoundError:
        typer.echo(f"Error: Surface file not found at '{surface_file}'", err=True)
        raise typer.Exit(code=1) from None
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="calculate-validation")
def calculate_validation(
    surface_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON surface data for model-validation VOI",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save model-validation result"
    ),
) -> None:
    """Calculate value of model validation from a JSON surface file.

    Examples
    --------
    Calculate validation regret and consensus strategy:

    .. code-block:: bash

        voiage calculate-validation validation_surface.json
    """
    try:
        _log_cli_debug(
            "calculate-validation",
            surface_file=str(surface_file),
            output_file=str(output_file) if output_file else None,
        )
        (
            _payload,
            value_array,
            strategy_names,
            profile_entries,
            reference_validation_profile,
        ) = _read_frontier_profile_surface(
            surface_file,
            "Validation surface",
            "validation_profiles",
        )
        profiles = ValidationProfileSet(
            [
                ValidationProfile(**entry)
                if isinstance(entry, dict)
                else ValidationProfile(id=str(entry))
                for entry in profile_entries
            ]
        )
        result = calculate_validation_result(
            value_array,
            validation_profiles=profiles,
            strategy_names=strategy_names,
            reference_validation_profile=cast(
                "str | int | None", reference_validation_profile
            ),
        )
        result_str = (
            f"Model validation VOI: {result.value:.6f}\n"
            f"Consensus strategy: {result.consensus_strategy}\n"
            f"Robust strategy: {result.robust_strategy}"
        )
        output_text = _format_output(
            result_str,
            _validation_result_payload(result, "calculate-validation"),
        )

        typer.echo(output_text)

        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")

    except FileNotFoundError:
        typer.echo(f"Error: Surface file not found at '{surface_file}'", err=True)
        raise typer.Exit(code=1) from None
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="calculate-expected-utility-information")
def calculate_expected_utility_information(
    request_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to the versioned expected-utility information request JSON",
    ),
    presentation_label: Literal["canonical", "voc"] = typer.Option(
        "canonical",
        "--presentation",
        help="Render the canonical result directly or as a VoC presentation",
    ),
    selected_measure: Literal["eui", "cei", "bpi", "spi", "ppi", "evpi"] = typer.Option(
        "eui",
        "--measure",
        help="Measure selected for presentation; evpi requires affine clairvoyance",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the result"
    ),
) -> None:
    """Compute one canonical expected-utility information result.

    ``voc`` is a presentation of the same clairvoyant result, not a second
    numerical command or kernel.
    """
    try:
        _log_cli_debug(
            "calculate-expected-utility-information",
            request_file=str(request_file),
            presentation_label=presentation_label,
            selected_measure=selected_measure,
        )
        request = _read_json_file(request_file)
        if not isinstance(request, dict):
            raise TypeError("Expected-utility request file must contain a JSON object.")
        typed_request = dict(cast("dict[str, object]", request))
        typed_request["presentation_label"] = presentation_label
        if presentation_label == "voc":
            result = value_of_clairvoyance(
                typed_request,
                selected_measure=selected_measure,
            )
        else:
            if selected_measure == "evpi":
                raise ValueError("The evpi display alias requires --presentation voc.")
            result = expected_utility_information_value(typed_request)
            result = _bind_presentation(result, selected_measure=selected_measure)

        measure_result = cast(
            "dict[str, object]",
            result[
                "affine_reduction" if selected_measure == "evpi" else selected_measure
            ],
        )
        measure_status = cast("str", measure_result["status"])
        selected_value = measure_result["value"]
        if measure_status == "failed":
            diagnostics_ref = measure_result.get("diagnostics_ref")
            root = cast("dict[str, object]", result.get(diagnostics_ref, {}))
            termination = root.get("termination_reason", "unspecified failure")
            raise ValueError(
                f"{selected_measure} failed: {termination} "
                f"(diagnostics: {diagnostics_ref or 'none'})"
            )
        text = (
            f"Expected-utility information ({selected_measure}): "
            f"{selected_value if selected_value is not None else 'unavailable'}"
        )
        output_text = _format_output(
            text,
            {
                "command": "calculate-expected-utility-information",
                "selected_measure": selected_measure,
                "selected_status": measure_status,
                "selected_value": selected_value,
                "result": result,
            },
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except FileNotFoundError:
        typer.echo(f"Error: Request file not found at '{request_file}'", err=True)
        raise typer.Exit(code=1) from None
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="calculate-threshold")
def calculate_threshold(
    surface_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON surface data for threshold VOI",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save threshold result"
    ),
) -> None:
    """Calculate threshold, tipping-point, and robust VOI from a JSON surface file.

    Examples
    --------
    Calculate threshold-crossing summaries and robust strategy:

    .. code-block:: bash

        voiage calculate-threshold threshold_surface.json
    """
    try:
        _log_cli_debug(
            "calculate-threshold",
            surface_file=str(surface_file),
            output_file=str(output_file) if output_file else None,
        )
        (
            _payload,
            value_array,
            strategy_names,
            profile_entries,
            reference_threshold_profile,
        ) = _read_frontier_profile_surface(
            surface_file,
            "Threshold surface",
            "threshold_profiles",
        )
        profiles = ThresholdProfileSet(
            [
                ThresholdProfile(**entry)
                if isinstance(entry, dict)
                else ThresholdProfile(id=str(entry))
                for entry in profile_entries
            ]
        )
        result = calculate_threshold_result(
            value_array,
            threshold_profiles=profiles,
            strategy_names=strategy_names,
            reference_threshold_profile=cast(
                "str | int | None", reference_threshold_profile
            ),
        )
        result_str = (
            f"Threshold VOI: {result.value:.6f}\n"
            f"Tipping-point strategy: {result.tipping_point_strategy}\n"
            f"Robust strategy: {result.robust_strategy}"
        )
        output_text = _format_output(
            result_str,
            _threshold_result_payload(result, "calculate-threshold"),
        )

        typer.echo(output_text)

        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")

    except FileNotFoundError:
        typer.echo(f"Error: Surface file not found at '{surface_file}'", err=True)
        raise typer.Exit(code=1) from None
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def calculate_heterogeneity(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON input with net_benefit and subgroups",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save Value of Heterogeneity result"
    ),
) -> None:
    """Calculate Value of Heterogeneity from a JSON input file."""
    try:
        _log_cli_debug(
            "calculate-heterogeneity",
            input_file=str(input_file),
            output_file=str(output_file) if output_file else None,
        )
        payload, value_array, strategy_names = _read_2d_method_surface(
            input_file,
            "Heterogeneity",
        )
        subgroups = payload.get("subgroups")
        if subgroups is None:
            raise TypeError("Heterogeneity input file must contain 'subgroups'.")
        if not isinstance(subgroups, list):
            raise TypeError("'subgroups' must be a list.")

        n_bins = payload.get("n_bins")
        if n_bins is not None and not isinstance(n_bins, int):
            raise TypeError("'n_bins' must be an integer when provided.")

        result = value_of_heterogeneity(
            value_array,
            subgroups,
            strategy_names=strategy_names,
            n_bins=n_bins,
        )
        result_str = (
            f"Value of Heterogeneity: {result.value:.6f}\n"
            f"Overall optimal strategy: {result.overall_optimal_strategy_name}\n"
            f"Subgroups: {len(result.subgroup_labels)}"
        )
        output_text = _format_output(
            result_str,
            _heterogeneity_result_payload(result, "calculate-heterogeneity"),
        )

        typer.echo(output_text)

        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")

    except FileNotFoundError:
        typer.echo(f"Error: Input file not found at '{input_file}'", err=True)
        raise typer.Exit(code=1) from None
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def calculate_distributional_equity(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON input with net_benefit, subgroups, and equity weights",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="File to save Value of Distributional Equity result",
    ),
) -> None:
    """Calculate Value of Distributional Equity from a JSON input file."""
    try:
        _log_cli_debug(
            "calculate-distributional-equity",
            input_file=str(input_file),
            output_file=str(output_file) if output_file else None,
        )
        payload, value_array, strategy_names = _read_2d_method_surface(
            input_file,
            "Distributional equity",
        )
        subgroups = payload.get("subgroups")
        if subgroups is None:
            raise TypeError(
                "Distributional equity input file must contain 'subgroups'."
            )
        if not isinstance(subgroups, list):
            raise TypeError("'subgroups' must be a list.")

        n_bins = payload.get("n_bins")
        if n_bins is not None and not isinstance(n_bins, int):
            raise TypeError("'n_bins' must be an integer when provided.")

        equity_weights = payload.get("equity_weights")
        if equity_weights is not None and not isinstance(equity_weights, (list, dict)):
            raise TypeError("'equity_weights' must be a list or mapping when provided.")

        result = value_of_distributional_equity(
            value_array,
            subgroups,
            strategy_names=strategy_names,
            equity_weights=cast(
                "np.ndarray | list[float] | dict[str, float] | None",
                equity_weights,
            ),
            n_bins=n_bins,
        )
        result_str = (
            f"Value of Distributional Equity: {result.value:.6f}\n"
            f"Social welfare strategy: {result.social_welfare_optimal_strategy_name}\n"
            f"Subgroups: {len(result.subgroup_labels)}"
        )
        output_text = _format_output(
            result_str,
            _distributional_result_payload(result, "calculate-distributional-equity"),
        )

        typer.echo(output_text)

        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")

    except FileNotFoundError:
        typer.echo(f"Error: Input file not found at '{input_file}'", err=True)
        raise typer.Exit(code=1) from None
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="calculate-equity-information")
def calculate_equity_information(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON equity-information VOI specification",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the equity-information result"
    ),
) -> None:
    """Calculate fixture-backed Value of Equity Information."""
    try:
        payload, value_array, strategy_names = _read_2d_method_surface(
            input_file, "Equity information"
        )
        subgroups = payload.get("subgroups")
        if not isinstance(subgroups, list):
            raise TypeError("Equity information input must contain a 'subgroups' list.")
        resolved = payload.get("resolved_equity_weights")
        if not isinstance(resolved, list):
            raise TypeError(
                "Equity information input must contain 'resolved_equity_weights'."
            )
        weights = payload.get("equity_weights")
        if not isinstance(weights, list):
            raise TypeError("Equity information input must contain 'equity_weights'.")
        result = calculate_equity_information_result(
            value_array,
            subgroups,
            equity_weights=np.asarray(weights, dtype=float),
            resolved_equity_weights=np.asarray(resolved, dtype=float),
            scenario_probabilities=(
                np.asarray(payload["scenario_probabilities"], dtype=float)
                if payload.get("scenario_probabilities") is not None
                else None
            ),
            information_cost=float(payload.get("information_cost", 0.0)),
            strategy_names=strategy_names,
            policy_strata=cast("list[str] | None", payload.get("policy_strata")),
        )
        result_payload = {
            "analysis_type": "value_of_equity_information",
            "method_maturity": result.method_maturity,
            "value": result.value,
            "baseline_optimal_strategy_name": result.baseline_optimal_strategy_name,
            "baseline_social_welfare": result.baseline_social_welfare,
            "resolved_optimal_strategy_names": result.resolved_optimal_strategy_names,
            "resolved_social_welfare": result.resolved_social_welfare.tolist(),
            "equity_weights": result.equity_weights.tolist(),
            "subgroup_labels": result.subgroup_labels,
            "subgroup_expected_net_benefits": result.subgroup_expected_net_benefits.tolist(),
            "scenario_probabilities": result.scenario_probabilities.tolist(),
            "policy_strata": result.policy_strata,
            "information_cost": result.information_cost,
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        output_text = _format_output(
            f"Value of Equity Information: {result.value:.6f}\n"
            f"Baseline strategy: {result.baseline_optimal_strategy_name}",
            result_payload,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except FileNotFoundError:
        typer.echo(f"Error: Input file not found at '{input_file}'", err=True)
        raise typer.Exit(code=1) from None
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="calculate-ambiguity-distribution-shift")
def calculate_ambiguity_distribution_shift(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON ambiguity and distribution-shift VOI specification",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the distribution-shift result"
    ),
) -> None:
    """Calculate fixture-backed VOI under ambiguity and distribution shift."""
    try:
        payload, value_array, strategy_names = _read_2d_method_surface(
            input_file, "Ambiguity and distribution shift"
        )
        shift_weights = payload.get("shift_weights")
        if not isinstance(shift_weights, list):
            raise TypeError("Input must contain a 'shift_weights' list.")
        result = calculate_ambiguity_shift_result(
            value_array,
            shift_weights=np.asarray(shift_weights, dtype=float),
            strategy_names=strategy_names,
            scenario_names=cast("list[str] | None", payload.get("scenario_names")),
            scenario_probabilities=(
                np.asarray(payload["scenario_probabilities"], dtype=float)
                if payload.get("scenario_probabilities") is not None
                else None
            ),
            ambiguity_radius=float(payload.get("ambiguity_radius", 0.0)),
            information_cost=float(payload.get("information_cost", 0.0)),
        )
        result_payload = {
            "analysis_type": "value_of_ambiguity_distribution_shift",
            "method_maturity": result.method_maturity,
            "value": result.value,
            "strategy_names": result.strategy_names,
            "scenario_names": result.scenario_names,
            "scenario_probabilities": result.scenario_probabilities.tolist(),
            "scenario_expected_net_benefits": result.scenario_expected_net_benefits.tolist(),
            "robust_net_benefits": result.robust_net_benefits.tolist(),
            "robust_strategy_name": result.robust_strategy_name,
            "robust_value": result.robust_value,
            "informed_optimal_strategy_names": result.informed_optimal_strategy_names,
            "informed_expected_value": result.informed_expected_value,
            "scenario_regret": result.scenario_regret.tolist(),
            "shift_sensitivity": result.shift_sensitivity.tolist(),
            "ambiguity_radius": result.ambiguity_radius,
            "information_cost": result.information_cost,
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        output_text = _format_output(
            f"Ambiguity and distribution-shift VOI: {result.value:.6f}\n"
            f"Robust strategy: {result.robust_strategy_name}",
            result_payload,
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except FileNotFoundError:
        typer.echo(f"Error: Input file not found at '{input_file}'", err=True)
        raise typer.Exit(code=1) from None
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="calculate-adaptive-learning-bandit")
def calculate_adaptive_learning_bandit(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON adaptive-learning bandit VOI specification",
    ),
) -> None:
    """Calculate fixture-backed value of adaptive learning and bandit allocation."""
    try:
        payload = json.loads(input_file.read_text(encoding="utf-8"))
        reward_samples = payload.get("reward_samples")
        if not isinstance(reward_samples, list):
            raise TypeError("Input must contain a 'reward_samples' list.")
        result = calculate_bandit_result(
            reward_samples,
            policy=str(payload.get("policy", "ucb")),
            horizon=payload.get("horizon"),
            exploration_cost=float(payload.get("exploration_cost", 0.0)),
            epsilon=float(payload.get("epsilon", 0.1)),
            confidence=float(payload.get("confidence", 2.0)),
            stop_regret=payload.get("stop_regret"),
            arm_names=cast("list[str] | None", payload.get("arm_names")),
            seed=int(payload.get("seed", 0)),
        )
        result_payload = {
            "analysis_type": "value_of_adaptive_learning_bandit",
            "method_maturity": result.method_maturity,
            "value": result.value,
            "policy": result.policy,
            "arm_names": result.arm_names,
            "selected_arms": result.selected_arms.tolist(),
            "cumulative_rewards": result.cumulative_rewards.tolist(),
            "total_reward": result.total_reward,
            "baseline_reward": result.baseline_reward,
            "regret": result.regret,
            "opportunity_cost": result.opportunity_cost,
            "exploration_cost": result.exploration_cost,
            "decision_switch_frequency": result.decision_switch_frequency,
            "sampling_burden": result.sampling_burden,
            "stopping_step": result.stopping_step,
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        typer.echo(
            _format_output(
                f"Adaptive learning bandit VOI: {result.value:.6f}\n"
                f"Policy: {result.policy}; stopping step: {result.stopping_step}",
                result_payload,
            )
        )
    except FileNotFoundError:
        typer.echo(f"Error: Input file not found at '{input_file}'", err=True)
        raise typer.Exit(code=1) from None
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="calculate-capacity-budget-constrained")
def calculate_capacity_budget_constrained(
    input_file: Path = typer.Argument(..., exists=True),
) -> None:
    """Calculate fixture-backed constrained-budget and capacity VOI."""
    try:
        payload = json.loads(input_file.read_text(encoding="utf-8"))
        result = calculate_capacity_budget_result(
            payload["scenario_values"],
            strategy_costs=payload["strategy_costs"],
            strategy_capacity=payload["strategy_capacity"],
            budget=float(payload["budget"]),
            capacity=float(payload["capacity"]),
            strategy_names=cast("list[str] | None", payload.get("strategy_names")),
            information_cost=float(payload.get("information_cost", 0.0)),
        )
        result_payload = {
            "analysis_type": "value_of_capacity_budget_constrained",
            "method_maturity": result.method_maturity,
            "value": result.value,
            "selected_strategy": result.selected_strategy,
            "strategy_names": result.strategy_names,
            "expected_values": result.expected_values.tolist(),
            "scenario_optimal_strategies": result.scenario_optimal_strategies,
            "budget": result.budget,
            "capacity": result.capacity,
            "budget_impact": result.budget_impact,
            "capacity_shortfall": result.capacity_shortfall,
            "constrained_regret": result.constrained_regret,
            "opportunity_cost": result.opportunity_cost,
            "shadow_price_budget": result.shadow_price_budget,
            "shadow_price_capacity": result.shadow_price_capacity,
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        typer.echo(
            _format_output(
                f"Capacity and budget-constrained VOI: {result.value:.6f}",
                result_payload,
            )
        )
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
        KeyError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="calculate-federated-privacy-preserving")
def calculate_federated_privacy_preserving(
    input_file: Path = typer.Argument(..., exists=True),
) -> None:
    """Calculate fixture-backed federated privacy-preserving VOI."""
    try:
        payload = json.loads(input_file.read_text(encoding="utf-8"))
        result = calculate_federated_privacy_result(
            payload["site_summaries"],
            site_weights=payload.get("site_weights"),
            privacy_budgets=payload["privacy_budgets"],
            prior_strategy_values=payload["prior_strategy_values"],
            strategy_names=cast("list[str] | None", payload.get("strategy_names")),
            synthetic_site_summaries=payload.get("synthetic_site_summaries"),
            noise_scale=float(payload.get("noise_scale", 0.0)),
            information_cost=float(payload.get("information_cost", 0.0)),
            individual_data_access=str(
                payload.get("individual_data_access", "blocked")
            ),
            seed=int(payload.get("seed", 0)),
        )
        result_payload = {
            "analysis_type": "value_of_federated_privacy_preserving",
            "method_maturity": result.method_maturity,
            "value": result.value,
            "selected_strategy": result.selected_strategy,
            "strategy_names": result.strategy_names,
            "aggregated_net_benefits": result.aggregated_net_benefits.tolist(),
            "site_contribution_values": result.site_contribution_values.tolist(),
            "privacy_budgets": result.privacy_budgets.tolist(),
            "privacy_loss": result.privacy_loss,
            "aggregation_error": result.aggregation_error,
            "disclosure_risk": result.disclosure_risk,
            "expected_value_privacy_preserving": result.expected_value_privacy_preserving,
            "baseline_value": result.baseline_value,
            "information_cost": result.information_cost,
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        typer.echo(
            _format_output(
                f"Federated privacy-preserving VOI: {result.value:.6f}\n"
                f"Selected strategy: {result.selected_strategy}",
                result_payload,
            )
        )
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
        KeyError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        typer.echo(f"An error occurred: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command(name="calculate-ai-assisted-evidence-triage")
def calculate_ai_assisted_evidence_triage(
    input_file: Path = typer.Argument(..., exists=True),
) -> None:
    """Calculate fixture-backed AI-assisted evidence-triage VOI."""
    try:
        payload = json.loads(input_file.read_text(encoding="utf-8"))
        result = calculate_ai_triage_result(
            payload["relevance_labels"],
            payload["triage_scores"],
            payload["decision_impacts"],
            payload["reviewer_time_minutes"],
            payload["extraction_error_rates"],
            triage_threshold=float(payload.get("triage_threshold", 0.5)),
            audit_sample_rate=float(payload.get("audit_sample_rate", 0.0)),
            human_override_rate=float(payload.get("human_override_rate", 0.0)),
            model_drift=float(payload.get("model_drift", 0.0)),
            automation_cost=float(payload.get("automation_cost", 0.0)),
            audit_cost_per_item=float(payload.get("audit_cost_per_item", 0.0)),
            reviewer_cost_per_minute=float(
                payload.get("reviewer_cost_per_minute", 1.0)
            ),
        )
        result_payload = {
            "analysis_type": "value_of_ai_assisted_evidence_triage",
            "method_maturity": result.method_maturity,
            "value": result.value,
            "selected_item_indices": result.selected_item_indices.tolist(),
            "triage_threshold": result.triage_threshold,
            "sensitivity": result.sensitivity,
            "specificity": result.specificity,
            "effective_sensitivity": result.effective_sensitivity,
            "effective_specificity": result.effective_specificity,
            "false_exclusion_risk": result.false_exclusion_risk,
            "false_inclusion_burden": result.false_inclusion_burden,
            "effective_false_exclusion_impact": result.effective_false_exclusion_impact,
            "effective_false_inclusion_impact": result.effective_false_inclusion_impact,
            "reviewer_time_saved": result.reviewer_time_saved,
            "audit_value": result.audit_value,
            "audit_items": result.audit_items,
            "extraction_error_burden": result.extraction_error_burden,
            "model_drift": result.model_drift,
            "expected_value_ai_triage": result.expected_value_ai_triage,
            "baseline_value": result.baseline_value,
            "automation_cost": result.automation_cost,
            "audit_cost": result.audit_cost,
            "human_override_rate": result.human_override_rate,
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        typer.echo(
            _format_output(
                f"AI-assisted evidence-triage VOI: {result.value:.6f}",
                result_payload,
            )
        )
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
        KeyError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command(name="calculate-explainability-transparency")
def calculate_explainability_transparency(
    input_file: Path = typer.Argument(..., exists=True),
) -> None:
    """Calculate fixture-backed explainability and transparency VOI."""
    try:
        payload = json.loads(input_file.read_text(encoding="utf-8"))
        result = calculate_explainability_result(
            payload["predictive_utilities"],
            payload["explanation_quality"],
            payload["transparency_evidence"],
            payload["trust_scores"],
            payload["governance_impacts"],
            payload["audit_costs"],
            adoption_threshold=float(payload.get("adoption_threshold", 0.5)),
            transparency_weight=float(payload.get("transparency_weight", 0.5)),
        )
        result_payload = {
            "analysis_type": "value_of_explainability_transparency",
            "method_maturity": result.method_maturity,
            "value": result.value,
            "adopted_model_indices": result.adopted_model_indices.tolist(),
            "adoption_probability": result.adoption_probability,
            "transparency_value": result.transparency_value,
            "governance_value": result.governance_value,
            "predictive_value": result.predictive_value,
            "trust_value": result.trust_value,
            "robustness": result.robustness,
            "audit_cost": result.audit_cost,
            "adoption_threshold": result.adoption_threshold,
            "transparency_weight": result.transparency_weight,
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        typer.echo(
            _format_output(
                f"Explainability and transparency VOI: {result.value:.6f}",
                result_payload,
            )
        )
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
        KeyError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        typer.echo(f"An error occurred: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command(name="calculate-interoperability-standardization")
def calculate_interoperability_standardization(
    input_file: Path = typer.Argument(..., exists=True),
) -> None:
    """Calculate fixture-backed interoperability and standardization VOI."""
    try:
        payload = json.loads(input_file.read_text(encoding="utf-8"))
        result = calculate_interoperability_result(
            payload["evidence_utilities"],
            payload["schema_compatibility"],
            payload["semantic_alignment"],
            payload["data_usability"],
            payload["transformation_error_rates"],
            payload["standardization_costs"],
            payload["reuse_probabilities"],
            harmonization_threshold=float(payload.get("harmonization_threshold", 0.5)),
        )
        result_payload = {
            "analysis_type": "value_of_interoperability_standardization",
            "method_maturity": result.method_maturity,
            "value": result.value,
            "reusable_evidence_indices": result.reusable_evidence_indices.tolist(),
            "reuse_probability": result.reuse_probability,
            "harmonization_score": result.harmonization_score,
            "standardization_value": result.standardization_value,
            "data_usability_value": result.data_usability_value,
            "reduced_transformation_error": result.reduced_transformation_error,
            "evidence_reuse_value": result.evidence_reuse_value,
            "standardization_cost": result.standardization_cost,
            "baseline_value": result.baseline_value,
            "expected_value_harmonized": result.expected_value_harmonized,
            "harmonization_threshold": result.harmonization_threshold,
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        typer.echo(
            _format_output(
                f"Interoperability and standardization VOI: {result.value:.6f}",
                result_payload,
            )
        )
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
        KeyError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        typer.echo(f"An error occurred: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command(name="calculate-regulatory-market-access")
def calculate_regulatory_market_access(
    input_file: Path = typer.Argument(..., exists=True),
) -> None:
    """Calculate fixture-backed regulatory and market-access VOI."""
    try:
        payload = json.loads(input_file.read_text(encoding="utf-8"))
        result = calculate_market_access_result(
            payload["scenario_values"],
            payload["approval_probabilities"],
            payload["reimbursement_probabilities"],
            payload["access_delays_months"],
            payload["evidence_package_costs"],
            payload["label_expansion_values"],
            payload["price_threshold_values"],
            scenario_names=cast("list[str] | None", payload.get("scenario_names")),
            approval_threshold=float(payload.get("approval_threshold", 0.5)),
            monthly_access_delay_cost=float(
                payload.get("monthly_access_delay_cost", 0.0)
            ),
        )
        result_payload = {
            "analysis_type": "value_of_regulatory_market_access",
            "method_maturity": result.method_maturity,
            "value": result.value,
            "selected_scenario_indices": result.selected_scenario_indices.tolist(),
            "scenario_names": result.scenario_names,
            "approval_probability": result.approval_probability,
            "reimbursement_probability": result.reimbursement_probability,
            "joint_access_probability": result.joint_access_probability,
            "regulatory_uncertainty": result.regulatory_uncertainty,
            "payer_uncertainty": result.payer_uncertainty,
            "access_delay_months": result.access_delay_months,
            "access_delay_cost": result.access_delay_cost,
            "evidence_package_cost": result.evidence_package_cost,
            "label_expansion_value": result.label_expansion_value,
            "price_threshold_value": result.price_threshold_value,
            "expected_access_value": result.expected_access_value,
            "baseline_value": result.baseline_value,
            "expected_value_market_access_information": result.expected_value_market_access_information,
            "approval_threshold": result.approval_threshold,
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        typer.echo(
            _format_output(
                f"Regulatory and market-access VOI: {result.value:.6f}",
                result_payload,
            )
        )
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
        KeyError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        typer.echo(f"An error occurred: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command(name="calculate-evidence-obsolescence-refresh")
def calculate_evidence_obsolescence_refresh(
    input_file: Path = typer.Argument(..., exists=True),
) -> None:
    """Calculate fixture-backed evidence obsolescence and refresh VOI."""
    try:
        payload = json.loads(input_file.read_text(encoding="utf-8"))
        result = calculate_obsolescence_result(
            payload["evidence_values"],
            payload["evidence_age_months"],
            payload["half_lives_months"],
            payload["obsolescence_risks"],
            payload["refresh_costs"],
            payload["living_review_values"],
            payload["model_refresh_values"],
            payload["drift_rates"],
            refresh_threshold=float(payload.get("refresh_threshold", 0.5)),
            refresh_cadence_months=float(payload.get("refresh_cadence_months", 12.0)),
        )
        result_payload = {
            "analysis_type": "value_of_evidence_obsolescence_refresh",
            "method_maturity": result.method_maturity,
            "value": result.value,
            "selected_refresh_indices": result.selected_refresh_indices.tolist(),
            "evidence_age_months": result.evidence_age_months,
            "obsolescence_risk": result.obsolescence_risk,
            "refresh_burden": result.refresh_burden,
            "update_cadence_months": result.update_cadence_months,
            "living_review_value": result.living_review_value,
            "model_refresh_value": result.model_refresh_value,
            "obsolete_decision_risk": result.obsolete_decision_risk,
            "refresh_value": result.refresh_value,
            "update_cost": result.update_cost,
            "baseline_value": result.baseline_value,
            "expected_value_refresh": result.expected_value_refresh,
            "refresh_threshold": result.refresh_threshold,
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        typer.echo(
            _format_output(
                f"Evidence obsolescence and refresh VOI: {result.value:.6f}",
                result_payload,
            )
        )
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
        KeyError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        typer.echo(f"An error occurred: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command(name="calculate-strategic-behavior")
def calculate_strategic_behavior(
    input_file: Path = typer.Argument(..., exists=True),
) -> None:
    """Calculate fixture-backed strategic behavior VOI."""
    try:
        payload = json.loads(input_file.read_text(encoding="utf-8"))
        result = calculate_strategic_result(
            payload["scenario_values"],
            payload["equilibrium_probabilities"],
            payload["incentive_response_values"],
            payload["disclosure_values"],
            payload["bargaining_values"],
            payload["adversarial_risks"],
            payload["response_sensitivities"],
            payload["strategic_regrets"],
            equilibrium_threshold=float(payload.get("equilibrium_threshold", 0.5)),
        )
        result_payload = {
            "analysis_type": "value_of_strategic_behavior",
            "method_maturity": result.method_maturity,
            "value": result.value,
            "selected_scenario_indices": result.selected_scenario_indices.tolist(),
            "equilibrium_probability": result.equilibrium_probability,
            "response_sensitivity": result.response_sensitivity,
            "equilibrium_fragility": result.equilibrium_fragility,
            "strategic_regret": result.strategic_regret,
            "disclosure_value": result.disclosure_value,
            "incentive_value": result.incentive_value,
            "bargaining_value": result.bargaining_value,
            "adversarial_response": result.adversarial_response,
            "expected_value_strategic_information": result.expected_value_strategic_information,
            "baseline_value": result.baseline_value,
            "equilibrium_threshold": result.equilibrium_threshold,
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        typer.echo(
            _format_output(
                f"Strategic behavior VOI: {result.value:.6f}", result_payload
            )
        )
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
        KeyError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        typer.echo(f"An error occurred: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command(name="calculate-replication-reproducibility")
def calculate_replication_reproducibility(
    input_file: Path = typer.Argument(..., exists=True),
) -> None:
    """Calculate fixture-backed replication and reproducibility VOI."""
    try:
        payload = json.loads(input_file.read_text(encoding="utf-8"))
        result = calculate_replication_result(
            payload["evidence_values"],
            payload["replication_probabilities"],
            payload["reproducibility_failure_risks"],
            payload["audit_costs"],
            payload["reanalysis_values"],
            payload["credibility_adjustments"],
            payload["evidence_downgrades"],
            replication_threshold=float(payload.get("replication_threshold", 0.5)),
        )
        result_payload = {
            "analysis_type": "value_of_replication_reproducibility",
            "method_maturity": result.method_maturity,
            "value": result.value,
            "selected_replication_indices": result.selected_replication_indices.tolist(),
            "replication_probability": result.replication_probability,
            "reproducibility_risk": result.reproducibility_risk,
            "audit_burden": result.audit_burden,
            "credibility_impact": result.credibility_impact,
            "evidence_downgrade": result.evidence_downgrade,
            "replication_value": result.replication_value,
            "reanalysis_value": result.reanalysis_value,
            "audit_cost": result.audit_cost,
            "baseline_value": result.baseline_value,
            "expected_value_replication": result.expected_value_replication,
            "replication_threshold": result.replication_threshold,
            "diagnostics": result.diagnostics,
            "reporting": result.reporting,
        }
        typer.echo(
            _format_output(
                f"Replication and reproducibility VOI: {result.value:.6f}",
                result_payload,
            )
        )
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
        KeyError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        typer.echo(f"An error occurred: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command()
def calculate_implementation(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON input with net_benefit and implementation settings",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save Value of Implementation result"
    ),
) -> None:
    """Calculate Value of Implementation from a JSON input file."""
    try:
        _log_cli_debug(
            "calculate-implementation",
            input_file=str(input_file),
            output_file=str(output_file) if output_file else None,
        )
        payload, value_array, strategy_names = _read_2d_method_surface(
            input_file,
            "Implementation",
        )

        result = value_of_implementation(
            value_array,
            uptake=cast(
                "float",
                _optional_float_field(payload, "uptake", 1.0),
            ),
            adherence=cast(
                "float",
                _optional_float_field(payload, "adherence", 1.0),
            ),
            coverage=cast(
                "float",
                _optional_float_field(payload, "coverage", 1.0),
            ),
            implementation_delay=cast(
                "float",
                _optional_float_field(payload, "implementation_delay", 0.0),
            ),
            implementation_uncertainty=cast(
                "float",
                _optional_float_field(payload, "implementation_uncertainty", 0.0),
            ),
            discount_rate=cast(
                "float",
                _optional_float_field(payload, "discount_rate", 0.0),
            ),
            time_horizon=_optional_float_field(payload, "time_horizon", None),
            population=_optional_float_field(payload, "population", None),
            strategy_names=strategy_names,
        )
        result_str = (
            f"Value of Implementation: {result.value:.6f}\n"
            f"Adjusted optimal strategy: {result.adjusted_optimal_strategy_name}\n"
            f"Multiplier: {result.implementation_multiplier:.6f}"
        )
        output_text = _format_output(
            result_str,
            _implementation_result_payload(result, "calculate-implementation"),
        )

        typer.echo(output_text)

        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")

    except FileNotFoundError:
        typer.echo(f"Error: Input file not found at '{input_file}'", err=True)
        raise typer.Exit(code=1) from None
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command(name="plot-coss")
def plot_coss_command(
    result_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to a CossResultV1 JSON contract or calculate-coss JSON output",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the COSS plot"
    ),
) -> None:
    """Plot an experimental COSS result using accessible visual encodings."""
    try:
        _log_cli_debug(
            "plot-coss",
            result_file=str(result_file),
            output_file=str(output_file) if output_file else None,
        )
        result = _read_coss_result(result_file)
        ax = render_coss(result)
        if output_file:
            _save_figure(ax, output_file)
        output_text = _format_output(
            "Plot generated" if output_file is None else f"Plot saved to {output_file}",
            {
                "command": "plot-coss",
                "input_file": str(result_file),
                "output_file": str(output_file) if output_file else None,
                "saved": output_file is not None,
                "schema_version": result.schema_version,
                "optimal_design_id": result.optimal_design_id,
                "method_maturity": "experimental",
            },
        )
        typer.echo(output_text)
    except FileNotFoundError as error:
        typer.echo(f"Error: File not found - {error}", err=True)
        raise typer.Exit(code=1) from error
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error
    except Exception as error:
        typer.echo(f"An error occurred: {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command()
def plot_perspective_regret(
    surface_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON surface data for a Value of Perspective regret plot",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the perspective regret plot"
    ),
) -> None:
    """Plot the experimental Value of Perspective regret matrix.

    Examples
    --------
    Plot a perspective regret matrix:

    .. code-block:: bash

        voiage plot-perspective-regret perspective_surface.json --output regret.png
    """
    try:
        _log_cli_debug(
            "plot-perspective-regret",
            surface_file=str(surface_file),
            output_file=str(output_file) if output_file else None,
        )
        (
            _payload,
            value_array,
            strategy_names,
            perspective_names,
            perspective_weights,
            reference_perspective,
            _analysis_id,
            _decision_problem_id,
        ) = _read_perspective_surface(surface_file)
        result = calculate_perspective_result(
            value_array,
            strategy_names=strategy_names,
            perspective_names=perspective_names,
            perspective_weights=cast(
                "list[float] | dict[str, float] | None",
                perspective_weights,
            ),
            reference_perspective=cast("str | int | None", reference_perspective),
        )
        ax = render_perspective_regret(result)
        if _should_echo_status_messages():
            if output_file:
                _save_figure(ax, output_file)
                typer.echo(f"Plot saved to {output_file}")
        else:
            if output_file:
                _save_figure(ax, output_file)
            typer.echo(
                _format_output(
                    "Plot generated",
                    {
                        "command": "plot-perspective-regret",
                        "input_file": str(surface_file),
                        "output_file": str(output_file) if output_file else None,
                        "saved": output_file is not None,
                    },
                )
            )
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def plot_ceac(
    surface_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON surface data with net_benefit and wtp_thresholds",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the CEAC plot"
    ),
) -> None:
    """Plot a Cost-Effectiveness Acceptability Curve.

    Examples
    --------
    Plot a CEAC from a JSON surface file:

    .. code-block:: bash

        voiage plot-ceac surface.json
    """
    try:
        _log_cli_debug(
            "plot-ceac",
            surface_file=str(surface_file),
            output_file=str(output_file) if output_file else None,
        )
        value_array, wtp_thresholds = _read_plot_surface(surface_file)
        ax = render_ceac(value_array, wtp_thresholds=wtp_thresholds)
        if _should_echo_status_messages():
            if output_file:
                _save_figure(ax, output_file)
                typer.echo(f"Plot saved to {output_file}")
        else:
            if output_file:
                _save_figure(ax, output_file)
            typer.echo(
                _format_output(
                    "Plot generated",
                    {
                        "command": "plot-ceac",
                        "input_file": str(surface_file),
                        "output_file": str(output_file) if output_file else None,
                        "saved": output_file is not None,
                    },
                )
            )
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def plot_ceaf(
    surface_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON surface data with net_benefit and wtp_thresholds",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the CEAF plot"
    ),
) -> None:
    """Plot a Cost-Effectiveness Acceptability Frontier.

    Examples
    --------
    Plot a CEAF from a JSON surface file:

    .. code-block:: bash

        voiage plot-ceaf surface.json
    """
    try:
        _log_cli_debug(
            "plot-ceaf",
            surface_file=str(surface_file),
            output_file=str(output_file) if output_file else None,
        )
        value_array, wtp_thresholds = _read_plot_surface(surface_file)
        result = calculate_ceaf_result(value_array, wtp_thresholds)
        ax = render_ceaf(value_array, wtp_thresholds=wtp_thresholds, result=result)
        if _should_echo_status_messages():
            if output_file:
                _save_figure(ax, output_file)
                typer.echo(f"Plot saved to {output_file}")
        else:
            if output_file:
                _save_figure(ax, output_file)
            typer.echo(
                _format_output(
                    "Plot generated",
                    {
                        "command": "plot-ceaf",
                        "input_file": str(surface_file),
                        "output_file": str(output_file) if output_file else None,
                        "saved": output_file is not None,
                    },
                )
            )
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def plot_voi_curves(
    series_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON plot series data",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the VOI curves plot"
    ),
) -> None:
    """Plot EVPI/EVSI VOI curves from JSON series data.

    Examples
    --------
    Plot VOI curves from a JSON series file:

    .. code-block:: bash

        voiage plot-voi-curves curves.json
    """
    try:
        _log_cli_debug(
            "plot-voi-curves",
            series_file=str(series_file),
            output_file=str(output_file) if output_file else None,
        )
        payload = _read_plot_series(series_file)
        if "evpi_values" in payload and "wtp_thresholds" in payload:
            ax = render_evpi_vs_wtp(
                evpi_values=payload["evpi_values"],
                wtp_thresholds=payload["wtp_thresholds"],
            )
        elif "evsi_values" in payload and "sample_sizes" in payload:
            ax = render_evsi_vs_sample_size(
                evsi_values=payload["evsi_values"],
                sample_sizes=payload["sample_sizes"],
                enbs_values=payload.get("enbs_values"),
                research_costs=payload.get("research_costs"),
            )
        else:
            raise TypeError("Plot series file must contain either EVPI or EVSI data.")

        if _should_echo_status_messages():
            if output_file:
                _save_figure(ax, output_file)
                typer.echo(f"Plot saved to {output_file}")
        else:
            if output_file:
                _save_figure(ax, output_file)
            typer.echo(
                _format_output(
                    "Plot generated",
                    {
                        "command": "plot-voi-curves",
                        "input_file": str(series_file),
                        "output_file": str(output_file) if output_file else None,
                        "saved": output_file is not None,
                    },
                )
            )
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def plot_dominance(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to CSV file with strategy,cost,effect columns",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the dominance plot"
    ),
) -> None:
    """Plot the cost-effectiveness plane and frontier.

    Examples
    --------
    Plot dominance from a CSV file:

    .. code-block:: bash

        voiage plot-dominance dominance.csv
    """
    try:
        _log_cli_debug(
            "plot-dominance",
            input_file=str(input_file),
            output_file=str(output_file) if output_file else None,
        )
        costs, effects, names = _read_cost_effect_csv(input_file)
        result = calculate_dominance_result(costs, effects, strategy_names=names)
        ax = render_dominance(
            costs=costs, effects=effects, strategy_names=names, result=result
        )
        if _should_echo_status_messages():
            if output_file:
                _save_figure(ax, output_file)
                typer.echo(f"Plot saved to {output_file}")
        else:
            if output_file:
                _save_figure(ax, output_file)
            typer.echo(
                _format_output(
                    "Plot generated",
                    {
                        "command": "plot-dominance",
                        "input_file": str(input_file),
                        "output_file": str(output_file) if output_file else None,
                        "saved": output_file is not None,
                    },
                )
            )
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def calculate_ceaf(
    surface_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to JSON surface data with net_benefit and wtp_thresholds",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the CEAF result"
    ),
) -> None:
    """Calculate a Cost-Effectiveness Acceptability Frontier.

    Examples
    --------
    Calculate a CEAF from a JSON surface file:

    .. code-block:: bash

        voiage calculate-ceaf surface.json
    """
    try:
        _log_cli_debug(
            "calculate-ceaf",
            surface_file=str(surface_file),
            output_file=str(output_file) if output_file else None,
        )
        value_array, wtp_thresholds = _read_plot_surface(surface_file)
        result = calculate_ceaf_result(value_array, wtp_thresholds)
        strategy_name = (
            result.optimal_strategy_names[0] if result.optimal_strategy_names else "n/a"
        )
        result_str = (
            f"CEAF computed across {len(result.wtp_thresholds)} thresholds\n"
            f"Leading strategy: {strategy_name}"
        )
        output_text = _format_output(
            result_str,
            _ceaf_result_payload(result, "calculate-ceaf"),
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def calculate_dominance(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to CSV file with strategy,cost,effect columns",
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="File to save the dominance result"
    ),
) -> None:
    """Calculate dominance classes and the cost-effectiveness frontier.

    Examples
    --------
    Calculate dominance from a CSV file:

    .. code-block:: bash

        voiage calculate-dominance dominance.csv
    """
    try:
        _log_cli_debug(
            "calculate-dominance",
            input_file=str(input_file),
            output_file=str(output_file) if output_file else None,
        )
        costs, effects, names = _read_cost_effect_csv(input_file)
        result = calculate_dominance_result(costs, effects, strategy_names=names)
        result_str = (
            f"Dominance frontier strategies: {len(result.frontier_indices)}\n"
            f"Strongly dominated strategies: {len(result.strongly_dominated_indices)}"
        )
        output_text = _format_output(
            result_str,
            _dominance_result_payload(result, "calculate-dominance"),
        )
        typer.echo(output_text)
        if output_file:
            _write_output_file(output_file, output_text)
            if _should_echo_status_messages():
                typer.echo(f"Result saved to {output_file}")
    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1) from e


# Example of how to run if using Typer directly (not through setup.py entry points)
if __name__ == "__main__":  # pragma: no cover
    app()
