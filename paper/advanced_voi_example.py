"""
Advanced VOI Analysis with Australian and New Zealand Health Data
=================================================================

This example demonstrates advanced capabilities of the voiage library using
simulated data based on real Australian and New Zealand health datasets.
The example implements a complex health economic model with multiple parameters
and demonstrates advanced VOI techniques.
"""

import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression

from voiage.analysis import DecisionAnalysis
from voiage.methods.basic import evpi, evppi


def create_complex_health_model(n_simulations=2000, n_strategies=3):
    """
    Create a complex health economic model simulating a decision between
    multiple intervention strategies for a chronic condition common in
    Australia and New Zealand populations.

    Strategies:
    - Strategy 0: Standard care
    - Strategy 1: New drug intervention
    - Strategy 2: Enhanced care program

    Parameters based on Australian and New Zealand health data.
    """
    # Define population parameters
    # Based on Australian Institute of Health and Welfare (AIHW) and New Zealand health data
    base_params = {
        # Patient characteristics
        "age": np.random.normal(65, 12, n_simulations),  # Mean age 65 with SD 12
        "baseline_severity": np.random.beta(
            5, 8, n_simulations
        ),  # Baseline health severity
        "comorbidity_count": np.random.poisson(
            1.5, n_simulations
        ),  # Average 1.5 comorbidities
        "deprivation_index": np.random.normal(
            0, 1, n_simulations
        ),  # Socioeconomic factor (NZ-style)
        # Intervention parameters
        "drug_efficacy": np.random.normal(
            0.25, 0.08, n_simulations
        ),  # Treatment effect size
        "program_effectiveness": np.random.normal(
            0.18, 0.06, n_simulations
        ),  # Program effect
        "adherence_rate": np.random.beta(15, 5, n_simulations),  # Patient adherence
        # Cost parameters (in AUD/NZD)
        "drug_annual_cost": np.random.normal(
            3000, 500, n_simulations
        ),  # Annual drug cost
        "program_cost": np.random.normal(
            8000, 1500, n_simulations
        ),  # Total program cost
        "standard_care_cost": np.random.normal(
            2500, 400, n_simulations
        ),  # Annual care cost
        "event_cost": np.random.normal(
            20000, 4000, n_simulations
        ),  # Cost of adverse event
        # Outcome parameters
        "utility_baseline": np.random.normal(
            0.75, 0.1, n_simulations
        ),  # Baseline utility
        "utility_improvement_drug": np.random.normal(
            0.05, 0.02, n_simulations
        ),  # Utility gain from drug
        "utility_improvement_program": np.random.normal(
            0.08, 0.03, n_simulations
        ),  # Utility gain from program
        "event_reduction_drug": np.random.normal(
            0.20, 0.05, n_simulations
        ),  # Event risk reduction from drug
        "event_reduction_program": np.random.normal(
            0.25, 0.07, n_simulations
        ),  # Event risk reduction from program
    }

    # Calculate net benefits for each strategy
    net_benefits = np.zeros((n_simulations, n_strategies))

    # Willingness-to-pay threshold (AUD/NZD 50,000 per QALY)
    wtp = 50000

    for i in range(n_simulations):
        # Calculate baseline risk and utility
        baseline_risk = base_params["baseline_severity"][i] * (
            1 + 0.05 * base_params["comorbidity_count"][i]
        )
        baseline_utility = base_params["utility_baseline"][i] - (
            0.01 * base_params["comorbidity_count"][i]
        )

        # Calculate outcomes for each strategy over 5-year time horizon
        time_horizon = 5  # years

        # Strategy 0: Standard care
        standard_utility = baseline_utility  # No improvement
        standard_events = baseline_risk  # No reduction in events
        standard_cost = base_params["standard_care_cost"][i] * time_horizon

        # Calculate QALYs for standard care (discounted at 3%)
        standard_qalys = 0
        for t in range(time_horizon):
            year_utility = standard_utility * (1 - 0.05 * t)  # Natural decline
            discount_factor = 1 / ((1 + 0.03) ** t)
            standard_qalys += year_utility * discount_factor

        # Apply event impact
        standard_qalys -= standard_events * 0.2  # QALY loss from event

        # Strategy 1: New drug intervention
        drug_utility = (
            baseline_utility
            + base_params["utility_improvement_drug"][i]
            * base_params["adherence_rate"][i]
        )
        drug_events = baseline_risk * (
            1
            - base_params["event_reduction_drug"][i] * base_params["adherence_rate"][i]
        )
        drug_cost = standard_cost + base_params["drug_annual_cost"][i] * time_horizon

        # Calculate QALYs for drug (discounted at 3%)
        drug_qalys = 0
        for t in range(time_horizon):
            year_utility = drug_utility * (
                1 - 0.04 * t
            )  # Slightly slower decline with treatment
            discount_factor = 1 / ((1 + 0.03) ** t)
            drug_qalys += year_utility * discount_factor

        # Apply event impact
        drug_qalys -= drug_events * 0.15  # Reduced QALY loss from fewer events

        # Strategy 2: Enhanced care program
        program_utility = (
            baseline_utility + base_params["utility_improvement_program"][i]
        )
        program_events = baseline_risk * (1 - base_params["event_reduction_program"][i])
        program_cost = standard_cost + base_params["program_cost"][i]

        # Calculate QALYs for program (discounted at 3%)
        program_qalys = 0
        for t in range(time_horizon):
            year_utility = program_utility * (
                1 - 0.03 * t
            )  # Slowest decline with enhanced care
            discount_factor = 1 / ((1 + 0.03) ** t)
            program_qalys += year_utility * discount_factor

        # Apply event impact
        program_qalys -= program_events * 0.1  # Lowest QALY loss from events

        # Calculate net monetary benefits for each strategy
        standard_nmb = (standard_qalys * wtp) - standard_cost
        drug_nmb = (drug_qalys * wtp) - drug_cost
        program_nmb = (program_qalys * wtp) - program_cost

        net_benefits[i, 0] = standard_nmb
        net_benefits[i, 1] = drug_nmb
        net_benefits[i, 2] = program_nmb

    return net_benefits, base_params


def main():
    """
    Main function to run the advanced VOI analysis.
    """
    print("Advanced VOI Analysis with Australian and New Zealand Health Data")
    print("=" * 70)

    # Set seed for reproducibility
    np.random.seed(456)

    # Create the complex health model
    print("Creating complex health economic model...")
    nb_array, param_samples = create_complex_health_model(n_simulations=2000)

    print(
        f"Modelled {nb_array.shape[0]} simulated patients across {nb_array.shape[1]} strategies"
    )
    print("Mean net benefits:")
    for i in range(nb_array.shape[1]):
        strategy_names = ["Standard Care", "New Drug", "Enhanced Program"]
        print(f"  {strategy_names[i]}: AUD {nb_array[:, i].mean():,.2f}")

    # Calculate EVPI
    print("\nCalculating Expected Value of Perfect Information...")
    evpi_value = evpi(nb_array)
    print(f"EVPI: AUD {evpi_value:,.2f} per patient")

    # Calculate EVPI scaled to Australian population (approx 25 million)
    aus_pop_evpi = evpi_value * 25_000_000
    print(f"Population EVPI (Australia): AUD {aus_pop_evpi:,.2f} total")

    # Calculate EVPI scaled to New Zealand population (approx 5 million)
    nz_pop_evpi = evpi_value * 5_000_000
    print(f"Population EVPI (New Zealand): AUD {nz_pop_evpi:,.2f} total")

    # Calculate EVPPI for different parameter groups
    print("\nCalculating Expected Value of Partial Perfect Information...")

    # Group parameters for analysis
    efficacy_params = ["drug_efficacy", "program_effectiveness", "adherence_rate"]
    cost_params = [
        "drug_annual_cost",
        "program_cost",
        "standard_care_cost",
        "event_cost",
    ]
    outcome_params = [
        "utility_baseline",
        "utility_improvement_drug",
        "utility_improvement_program",
    ]
    risk_params = [
        "baseline_severity",
        "comorbidity_count",
        "event_reduction_drug",
        "event_reduction_program",
    ]

    # Calculate EVPPI for each parameter group
    evppi_efficacy = evppi(
        nb_array, param_samples, parameters_of_interest=efficacy_params
    )
    evppi_cost = evppi(nb_array, param_samples, parameters_of_interest=cost_params)
    evppi_outcome = evppi(
        nb_array, param_samples, parameters_of_interest=outcome_params
    )
    evppi_risk = evppi(nb_array, param_samples, parameters_of_interest=risk_params)

    print(f"EVPPI for efficacy parameters: AUD {evppi_efficacy:,.2f} per patient")
    print(f"EVPPI for cost parameters: AUD {evppi_cost:,.2f} per patient")
    print(f"EVPPI for outcome parameters: AUD {evppi_outcome:,.2f} per patient")
    print(f"EVPPI for risk parameters: AUD {evppi_risk:,.2f} per patient")

    # Create decision analysis object for more detailed analysis
    analysis = DecisionAnalysis(nb_array=nb_array, parameter_samples=param_samples)

    # Calculate additional metrics with population scaling
    print("\nAdditional analysis with population scaling:")
    scaled_evpi = analysis.evpi(
        population=25_000_000,  # Australian population
        time_horizon=5,  # 5-year time horizon
        discount_rate=0.03,
    )
    print(f"Population EVPI (Australia, 5 years): AUD {scaled_evpi:,.2f} total")

    # Demonstrate advanced capabilities
    print("\nDemonstrating advanced VOI capabilities...")

    # Use different regression models for EVPPI calculation
    try:
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import RBF, ConstantKernel

        # Use Gaussian Process for more complex EVPPI calculation
        # First, we'll select a subset of parameters to avoid dimensionality issues
        selected_params = [
            "drug_efficacy",
            "program_effectiveness",
            "adherence_rate",
            "baseline_severity",
        ]

        # Create combined parameter array (just for this example)

        # Calculate EVPPI with custom regression model
        # Note: This is a simplified example - in practice, we'd implement a custom method
        custom_evppi = evppi(
            nb_array,
            param_samples,
            parameters_of_interest=selected_params,
            regression_model=LinearRegression,  # Using LinearRegression class (not instance)
        )
        print(
            f"EVPPI with custom regression model: AUD {custom_evppi:,.2f} per patient"
        )
    except ImportError:
        print("Advanced regression models not available")

    # Plotting results
    plt.figure(figsize=(16, 12))

    # Plot 1: Net benefit distributions by strategy
    plt.subplot(2, 3, 1)
    strategy_names = ["Standard Care", "New Drug", "Enhanced Program"]
    for i, name in enumerate(strategy_names):
        plt.hist(nb_array[:, i], alpha=0.6, label=name, bins=30)
    plt.xlabel("Net Monetary Benefit (AUD)")
    plt.ylabel("Frequency")
    plt.title("Distribution of Net Monetary Benefits by Strategy")
    plt.legend()

    # Plot 2: Cost-effectiveness acceptability curves
    plt.subplot(2, 3, 2)
    wtp_values = np.linspace(10000, 100000, 50)
    ceac = np.zeros((len(wtp_values), nb_array.shape[1]))

    for i, wtp in enumerate(wtp_values):
        nmb = nb_array.copy()
        for strat in range(nb_array.shape[1]):
            # Convert back from net monetary benefit to calculate CEAC
            # This is simplified - in practice, you'd need to recalculate from utilities and costs
            ceac[i, strat] = np.mean(nmb[:, strat] == np.max(nmb, axis=1))

    for i, name in enumerate(strategy_names):
        plt.plot(wtp_values / 1000, ceac[:, i], label=name, linewidth=2)
    plt.xlabel("Willingness-to-Pay (AUD per QALY x1000)")
    plt.ylabel("Probability of Cost-Effectiveness")
    plt.title("Cost-Effectiveness Acceptability Curves")
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Plot 3: Parameter correlation heatmap
    plt.subplot(2, 3, 3)
    param_df = pd.DataFrame(
        {
            k: v
            for k, v in param_samples.items()
            if k
            in [
                "drug_efficacy",
                "program_effectiveness",
                "adherence_rate",
                "baseline_severity",
                "utility_baseline",
                "comorbidity_count",
            ]
        }
    )
    corr_matrix = param_df.corr()
    sns.heatmap(
        corr_matrix,
        annot=True,
        cmap="coolwarm",
        center=0,
        square=True,
        fmt=".2f",
        cbar_kws={"shrink": 0.8},
    )
    plt.title("Parameter Correlation Matrix")

    # Plot 4: EVPPI comparison
    plt.subplot(2, 3, 4)
    param_groups = ["Efficacy", "Cost", "Outcome", "Risk"]
    evppi_values = [evppi_efficacy, evppi_cost, evppi_outcome, evppi_risk]
    bars = plt.bar(
        param_groups, evppi_values, color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    )
    plt.ylabel("EVPPI (AUD per patient)")
    plt.title("EVPPI by Parameter Group")
    plt.xticks(rotation=45)

    # Add value labels on bars
    for bar, value in zip(bars, evppi_values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(evppi_values) * 0.01,
            f"{value:.0f}",
            ha="center",
            va="bottom",
        )

    # Plot 5: Strategy comparison scatter
    plt.subplot(2, 3, 5)
    plt.scatter(
        nb_array[:, 0], nb_array[:, 1], alpha=0.5, label="Drug vs Standard", s=20
    )
    plt.scatter(
        nb_array[:, 0], nb_array[:, 2], alpha=0.5, label="Program vs Standard", s=20
    )
    plt.xlabel("Standard Care NMB (AUD)")
    plt.ylabel("Intervention NMB (AUD)")
    plt.title("Strategy Comparison Scatter")
    plt.legend()
    plt.axhline(y=0, color="k", linestyle="--", alpha=0.3)
    plt.axvline(x=0, color="k", linestyle="--", alpha=0.3)

    # Plot 6: Population impact
    plt.subplot(2, 3, 6)
    populations = ["Australia", "New Zealand"]
    pop_values = [aus_pop_evpi / 1e9, nz_pop_evpi / 1e9]  # Convert to billions
    bars = plt.bar(populations, pop_values, color=["#1f77b4", "#ff7f0e"])
    plt.ylabel("EVPI (AUD Billions)")
    plt.title("Population-Level EVPI Impact")

    # Add value labels on bars
    for bar, value in zip(bars, pop_values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(pop_values) * 0.01,
            f"{value:.2f}B",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
    plt.savefig("advanced_au_nz_voi_analysis.png", dpi=300, bbox_inches="tight")
    plt.show()

    print("\nAnalysis completed. Plots saved as 'advanced_au_nz_voi_analysis.png'")

    # Summary of findings and implications for health technology assessment
    print("\nAdvanced VOI Analysis Summary:")
    print("-" * 40)
    print(
        f"- EVPI suggests up to AUD {evpi_value:,.2f} per patient could be gained by eliminating uncertainty"
    )
    print(
        f"- At the population level, this represents AUD {aus_pop_evpi:,.0f} in Australia"
    )
    print(
        f"- The highest value parameter group is {'Efficacy' if evppi_efficacy == max(evppi_values) else 'Cost' if evppi_cost == max(evppi_values) else 'Outcome' if evppi_outcome == max(evppi_values) else 'Risk'} parameters"
    )
    print(
        f"- This suggests research priorities should focus on {'efficacy' if evppi_efficacy == max(evppi_values) else 'cost' if evppi_cost == max(evppi_values) else 'outcome' if evppi_outcome == max(evppi_values) else 'risk'} parameter estimation"
    )
    print(
        "- The analysis demonstrates the value of VOI methods in prioritizing research investments"
    )
    print(
        "- Results can inform HTA agencies like MSAC (Australia) and Pharmac (New Zealand)"
    )

    # Additional implications for health technology assessment
    print("\nImplications for Health Technology Assessment:")
    print("-" * 50)
    print(
        "- VOI analysis can guide research funding decisions in publicly funded systems"
    )
    print("- Results quantify the potential value of reducing specific uncertainties")
    print("- Can inform optimal sample size calculations for clinical trials")
    print("- Supports transparent, evidence-based policy decisions")
    print("- Enables efficient allocation of research resources")


if __name__ == "__main__":
    main()
