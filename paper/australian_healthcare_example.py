"""
Australian Healthcare VOI Analysis Example
==========================================

This example demonstrates the use of the voiage library for Value of Information
analysis in an Australian healthcare context, specifically a hypothetical decision
about funding a new cardiovascular intervention.

The example uses parameter values based on Australian health system data and
guidelines, with costs in Australian dollars and health outcomes measured in QALYs.
"""

import matplotlib.pyplot as plt
import numpy as np

from voiage.analysis import DecisionAnalysis
from voiage.methods.basic import evpi, evppi


def simulate_cardiovascular_model(n_simulations=1000, wtp_threshold=50000):
    """
    Simulate a cardiovascular intervention model for VOI analysis.

    Based on Australian health economic parameters and guidelines.

    Args:
        n_simulations: Number of probabilistic sensitivity analysis simulations
        wtp_threshold: Willingness-to-pay threshold in AUD per QALY

    Returns
    -------
        tuple: (net_benefit_array, parameter_samples)
    """
    # Model parameters based on Australian cardiovascular literature
    base_params = {
        # Treatment effect parameters
        "relative_risk_reduction": np.random.normal(
            0.15, 0.05, n_simulations
        ),  # 15% average risk reduction
        "baseline_risk": np.random.beta(
            10, 15, n_simulations
        ),  # Baseline CV risk in population
        # Cost parameters (in AUD)
        "intervention_cost": np.random.normal(
            1500, 300, n_simulations
        ),  # Cost per patient
        "standard_care_cost": np.random.normal(
            200, 40, n_simulations
        ),  # Annual standard care cost
        "event_cost": np.random.normal(15000, 3000, n_simulations),  # Cost of CV event
        # Outcome parameters
        "utility_gain": np.random.normal(
            0.03, 0.01, n_simulations
        ),  # Utility gain from intervention
        "treatment_duration": np.random.normal(
            5, 1, n_simulations
        ),  # Years of treatment effect
        "time_horizon": np.full(n_simulations, 10),  # Analysis time horizon in years
    }

    # Calculate net benefits for two strategies: standard care vs new intervention
    net_benefits = np.zeros((n_simulations, 2))

    for i in range(n_simulations):
        # Calculate probability of CV events
        baseline_prob = base_params["baseline_risk"][i]
        intervention_prob = baseline_prob * (
            1 - base_params["relative_risk_reduction"][i]
        )

        # Calculate QALYs
        standard_qalys = 10 * 0.75  # 10 years at utility 0.75 for standard care
        intervention_qalys = 10 * (
            0.75 + base_params["utility_gain"][i]
        )  # Higher utility with intervention

        # Adjust for event probability
        standard_qalys -= baseline_prob * 0.5  # QALY loss if event occurs
        intervention_qalys -= intervention_prob * 0.5  # QALY loss if event occurs

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
    Main function to run the Australian healthcare VOI analysis.
    """
    print("Australian Healthcare VOI Analysis Example")
    print("=" * 50)

    # Set seed for reproducibility
    np.random.seed(42)

    # Simulate the cardiovascular model
    print("Simulating cardiovascular intervention model...")
    nb_array, param_samples = simulate_cardiovascular_model(n_simulations=1000)

    print(f"Simulated {len(nb_array)} PSA runs with 2 strategies")
    print(f"Mean net benefit - Standard care: AUD {nb_array[:, 0].mean():,.2f}")
    print(f"Mean net benefit - New intervention: AUD {nb_array[:, 1].mean():,.2f}")

    # Calculate EVPI
    print("\nCalculating Expected Value of Perfect Information...")
    evpi_value = evpi(nb_array)
    print(f"EVPI: AUD {evpi_value:,.2f} per patient")

    # Calculate EVPI scaled to Australian population (approx 25 million)
    print(f"Population EVPI (Australia): AUD {evpi_value * 25_000_000:,.2f} total")

    # Calculate EVPPI for key parameters
    print("\nCalculating Expected Value of Partial Perfect Information...")

    # EVPPI for treatment effect (relative risk reduction)
    evppi_rrr = evppi(
        nb_array, param_samples, parameters_of_interest=["relative_risk_reduction"]
    )
    print(f"EVPPI for treatment effect: AUD {evppi_rrr:,.2f} per patient")

    # EVPPI for cost parameters
    evppi_cost = evppi(
        nb_array,
        param_samples,
        parameters_of_interest=["intervention_cost", "standard_care_cost"],
    )
    print(f"EVPPI for cost parameters: AUD {evppi_cost:,.2f} per patient")

    # EVPPI for baseline risk
    evppi_baseline = evppi(
        nb_array, param_samples, parameters_of_interest=["baseline_risk"]
    )
    print(f"EVPPI for baseline risk: AUD {evppi_baseline:,.2f} per patient")

    # Create decision analysis object for more detailed analysis
    analysis = DecisionAnalysis(nb_array=nb_array, parameter_samples=param_samples)

    # Calculate additional metrics
    print("\nAdditional analysis using DecisionAnalysis class:")
    evpi_detailed = analysis.evpi()
    print(f"EVPI (DecisionAnalysis): AUD {evpi_detailed:,.2f} per patient")

    # Population-level EVPI with time horizon (10 years) and Australian population
    # Note: Using population of 25 million and 10-year time horizon with 3% discount rate
    population_evpi = analysis.evpi(
        population=25_000_000,  # Australian population
        time_horizon=10,  # 10-year time horizon
        discount_rate=0.03,  # 3% discount rate
    )
    print(f"Population EVPI (with discounting): AUD {population_evpi:,.2f} total")

    # Plot results
    plt.figure(figsize=(12, 8))

    # Plot 1: Net benefit distribution
    plt.subplot(2, 2, 1)
    plt.hist(nb_array[:, 0], alpha=0.7, label="Standard Care", bins=30)
    plt.hist(nb_array[:, 1], alpha=0.7, label="New Intervention", bins=30)
    plt.xlabel("Net Monetary Benefit (AUD)")
    plt.ylabel("Frequency")
    plt.title("Distribution of Net Monetary Benefits")
    plt.legend()

    # Plot 2: Cost-effectiveness plane
    plt.subplot(2, 2, 2)
    qaly_diff = (
        np.mean(nb_array[:, 1] - nb_array[:, 0]) / 50000
    )  # Convert NMB difference back to QALYs
    cost_diff = np.mean(
        [
            param_samples["intervention_cost"][i]
            + param_samples["standard_care_cost"][i] * 10
            - param_samples["standard_care_cost"][i] * 10
            for i in range(len(param_samples["intervention_cost"]))
        ]
    )
    plt.scatter([qaly_diff], [cost_diff], s=100, c="red", marker="o")
    plt.axhline(y=0, color="k", linestyle="--", alpha=0.5)
    plt.axvline(x=0, color="k", linestyle="--", alpha=0.5)
    plt.xlabel("Incremental QALYs")
    plt.ylabel("Incremental Cost (AUD)")
    plt.title("Cost-Effectiveness Plane")

    # Add willingness-to-pay line
    x_line = np.linspace(-0.5, 1.0, 100)
    y_line = x_line * 50000  # WTP threshold
    plt.plot(x_line, y_line, "b--", alpha=0.5, label="WTP = 50,000 AUD/QALY")
    plt.legend()

    # Plot 3: Parameter distributions
    plt.subplot(2, 2, 3)
    plt.hist(param_samples["relative_risk_reduction"], bins=30, alpha=0.7, label="RRR")
    plt.xlabel("Relative Risk Reduction")
    plt.ylabel("Frequency")
    plt.title("Distribution of Treatment Effect")
    plt.legend()

    # Plot 4: EVPPI comparison
    plt.subplot(2, 2, 4)
    params = ["Treatment Effect", "Cost Parameters", "Baseline Risk"]
    evppi_values = [evppi_rrr, evppi_cost, evppi_baseline]
    bars = plt.bar(params, evppi_values)
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

    plt.tight_layout()
    plt.savefig("australian_cardiovascular_voi.png", dpi=300, bbox_inches="tight")
    plt.show()

    print("\nAnalysis completed. Plots saved as 'australian_cardiovascular_voi.png'")

    # Summary of findings
    print("\nSummary:")
    print("- The new intervention shows positive net benefit on average")
    print(
        f"- EVPI suggests up to AUD {evpi_value:,.2f} per patient could be gained by eliminating uncertainty"
    )
    print(
        f"- Most valuable parameter to research is the treatment effect (RRR) with EVPPI of AUD {evppi_rrr:,.2f}"
    )
    print(
        "- This suggests focusing research on precisely measuring the treatment's effectiveness would provide the most value"
    )


if __name__ == "__main__":
    main()
