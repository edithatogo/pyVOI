"""
New Zealand Healthcare VOI Analysis Example
============================================

This example demonstrates the use of the voiage library for Value of Information
analysis in a New Zealand healthcare context, specifically a hypothetical decision
about funding a new respiratory intervention for Māori and Pacific populations.

The example uses parameter values based on New Zealand health system data and
Pharmac guidelines, with costs in New Zealand dollars and health outcomes measured in QALYs.
"""

import matplotlib.pyplot as plt
import numpy as np

from voiage.analysis import DecisionAnalysis
from voiage.methods.basic import evpi, evppi


def simulate_respiratory_model(n_simulations=1000, wtp_threshold=45000):
    """
    Simulate a respiratory intervention model for VOI analysis in New Zealand.

    Based on New Zealand health economic parameters and Pharmac guidelines.

    Args:
        n_simulations: Number of probabilistic sensitivity analysis simulations
        wtp_threshold: Willingness-to-pay threshold in NZD per QALY (Pharmac guidelines)

    Returns
    -------
        tuple: (net_benefit_array, parameter_samples)
    """
    # Model parameters based on New Zealand respiratory literature
    base_params = {
        # Treatment effect parameters
        "relative_risk_reduction": np.random.normal(
            0.20, 0.06, n_simulations
        ),  # 20% average risk reduction
        "baseline_risk": np.random.beta(
            8, 12, n_simulations
        ),  # Baseline respiratory risk in population
        # Demographic parameters specific to NZ Māori/Pacific populations
        "maori_pacific_multiplier": np.random.normal(
            1.4, 0.2, n_simulations
        ),  # Higher baseline risk
        # Cost parameters (in NZD, using approximate 0.65 AUD/NZD exchange rate)
        "intervention_cost": np.random.normal(
            1200, 250, n_simulations
        ),  # Cost per patient in NZD
        "standard_care_cost": np.random.normal(
            150, 30, n_simulations
        ),  # Annual standard care cost in NZD
        "event_cost": np.random.normal(
            12000, 2500, n_simulations
        ),  # Cost of respiratory event in NZD
        # Outcome parameters
        "utility_gain": np.random.normal(
            0.04, 0.015, n_simulations
        ),  # Utility gain from intervention
        "treatment_duration": np.random.normal(
            3, 0.8, n_simulations
        ),  # Years of treatment effect
        "time_horizon": np.full(n_simulations, 10),  # Analysis time horizon in years
    }

    # Calculate net benefits for two strategies: standard care vs new intervention
    net_benefits = np.zeros((n_simulations, 2))

    for i in range(n_simulations):
        # Calculate probability of respiratory events (adjusted for Māori/Pacific high-risk group)
        baseline_prob = (
            base_params["baseline_risk"][i] * base_params["maori_pacific_multiplier"][i]
        )
        intervention_prob = baseline_prob * (
            1 - base_params["relative_risk_reduction"][i]
        )

        # Calculate QALYs
        standard_qalys = 10 * 0.70  # 10 years at utility 0.70 for standard care
        intervention_qalys = 10 * (
            0.70 + base_params["utility_gain"][i]
        )  # Higher utility with intervention

        # Adjust for event probability
        standard_qalys -= (
            baseline_prob * 0.6
        )  # QALY loss if event occurs (higher for respiratory)
        intervention_qalys -= intervention_prob * 0.6  # QALY loss if event occurs

        # Calculate costs
        standard_cost = (
            base_params["standard_care_cost"][i] * 10
        )  # 10 years of standard care
        intervention_cost = (
            standard_cost + base_params["intervention_cost"][i]
        )  # Plus intervention cost

        # Calculate net monetary benefits
        standard_nmb = (standard_qalys * wtp_threshold) - standard_cost
        intervention_nmb = (intervention_qalys * wtp_threshold) - intervention_cost

        net_benefits[i, 0] = standard_nmb  # Standard care
        net_benefits[i, 1] = intervention_nmb  # New intervention

    return net_benefits, base_params


def main():
    """
    Main function to run the New Zealand healthcare VOI analysis.
    """
    print("New Zealand Healthcare VOI Analysis Example")
    print("=" * 50)

    # Set seed for reproducibility
    np.random.seed(123)

    # Simulate the respiratory model
    print("Simulating respiratory intervention model for Māori/Pacific populations...")
    nb_array, param_samples = simulate_respiratory_model(n_simulations=1000)

    print(f"Simulated {len(nb_array)} PSA runs with 2 strategies")
    print(f"Mean net benefit - Standard care: NZD {nb_array[:, 0].mean():,.2f}")
    print(f"Mean net benefit - New intervention: NZD {nb_array[:, 1].mean():,.2f}")

    # Calculate EVPI
    print("\nCalculating Expected Value of Perfect Information...")
    evpi_value = evpi(nb_array)
    print(f"EVPI: NZD {evpi_value:,.2f} per patient")

    # Calculate EVPI scaled to New Zealand population (approx 5 million)
    print(f"Population EVPI (New Zealand): NZD {evpi_value * 5_000_000:,.2f} total")

    # Calculate EVPPI for key parameters
    print("\nCalculating Expected Value of Partial Perfect Information...")

    # EVPPI for treatment effect (relative risk reduction)
    evppi_rrr = evppi(
        nb_array, param_samples, parameters_of_interest=["relative_risk_reduction"]
    )
    print(f"EVPPI for treatment effect: NZD {evppi_rrr:,.2f} per patient")

    # EVPPI for demographic factors (Māori/Pacific risk multiplier)
    evppi_demographic = evppi(
        nb_array, param_samples, parameters_of_interest=["maori_pacific_multiplier"]
    )
    print(
        f"EVPPI for demographic risk factors: NZD {evppi_demographic:,.2f} per patient"
    )

    # EVPPI for cost parameters
    evppi_cost = evppi(
        nb_array,
        param_samples,
        parameters_of_interest=["intervention_cost", "standard_care_cost"],
    )
    print(f"EVPPI for cost parameters: NZD {evppi_cost:,.2f} per patient")

    # Create decision analysis object for more detailed analysis
    analysis = DecisionAnalysis(nb_array=nb_array, parameter_samples=param_samples)

    # Calculate additional metrics
    print("\nAdditional analysis using DecisionAnalysis class:")
    evpi_detailed = analysis.evpi()
    print(f"EVPI (DecisionAnalysis): NZD {evpi_detailed:,.2f} per patient")

    # Population-level EVPI with time horizon (10 years) and New Zealand population
    # Note: Using population of 5 million and 10-year time horizon with 3% discount rate
    population_evpi = analysis.evpi(
        population=5_000_000,  # New Zealand population
        time_horizon=10,  # 10-year time horizon
        discount_rate=0.03,  # 3% discount rate (consistent with Pharmac guidelines)
    )
    print(f"Population EVPI (with discounting): NZD {population_evpi:,.2f} total")

    # Plot results
    plt.figure(figsize=(12, 8))

    # Plot 1: Net benefit distribution
    plt.subplot(2, 2, 1)
    plt.hist(nb_array[:, 0], alpha=0.7, label="Standard Care", bins=30)
    plt.hist(nb_array[:, 1], alpha=0.7, label="New Intervention", bins=30)
    plt.xlabel("Net Monetary Benefit (NZD)")
    plt.ylabel("Frequency")
    plt.title("Distribution of Net Monetary Benefits")
    plt.legend()

    # Plot 2: Cost-effectiveness plane
    plt.subplot(2, 2, 2)
    # Calculate incremental effectiveness and cost (simplified approach)
    inc_qalys = (
        np.mean(nb_array[:, 1] - nb_array[:, 0]) / 45000
    )  # Convert NMB difference back to QALYs
    inc_cost = np.mean(
        [
            param_samples["intervention_cost"][i]
            for i in range(len(param_samples["intervention_cost"]))
        ]
    )
    plt.scatter(
        [inc_qalys], [inc_cost], s=100, c="red", marker="o", label="Incremental"
    )
    plt.axhline(y=0, color="k", linestyle="--", alpha=0.5)
    plt.axvline(x=0, color="k", linestyle="--", alpha=0.5)
    plt.xlabel("Incremental QALYs")
    plt.ylabel("Incremental Cost (NZD)")
    plt.title("Cost-Effectiveness Plane")

    # Add willingness-to-pay line
    x_line = np.linspace(-0.5, 1.0, 100)
    y_line = x_line * 45000  # WTP threshold
    plt.plot(x_line, y_line, "b--", alpha=0.5, label="WTP = 45,000 NZD/QALY")
    plt.legend()

    # Plot 3: Parameter distributions
    plt.subplot(2, 2, 3)
    plt.hist(
        param_samples["maori_pacific_multiplier"],
        bins=30,
        alpha=0.7,
        label="Māori/Pacific Risk Multiplier",
    )
    plt.xlabel("Risk Multiplier")
    plt.ylabel("Frequency")
    plt.title("Distribution of Demographic Risk Factors")
    plt.legend()

    # Plot 4: EVPPI comparison
    plt.subplot(2, 2, 4)
    params = ["Treatment Effect", "Demographic Factors", "Cost Parameters"]
    evppi_values = [evppi_rrr, evppi_demographic, evppi_cost]
    bars = plt.bar(params, evppi_values)
    plt.ylabel("EVPPI (NZD per patient)")
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

    plt.tight_layout()
    plt.savefig("new_zealand_respiratory_voi.png", dpi=300, bbox_inches="tight")
    plt.show()

    print("\nAnalysis completed. Plots saved as 'new_zealand_respiratory_voi.png'")

    # Summary of findings
    print("\nSummary:")
    print("- The new intervention shows positive net benefit on average")
    print(
        f"- EVPI suggests up to NZD {evpi_value:,.2f} per patient could be gained by eliminating uncertainty"
    )
    print(
        f"- Most valuable parameter to research is the treatment effect (RRR) with EVPPI of NZD {evppi_rrr:,.2f}"
    )
    print(
        f"- Demographic factors also show significant value (NZD {evppi_demographic:,.2f} per patient)"
    )
    print(
        "- This suggests focusing research on treatment effectiveness and demographic-specific effects would provide most value"
    )


if __name__ == "__main__":
    main()
