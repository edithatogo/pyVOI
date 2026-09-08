"""Tests for configuration objects in Value of Information analysis."""

import pytest

from voiage.config_objects import (
    EnvironmentalConfig,
    FinancialConfig,
    HealthcareConfig,
    MetamodelConfig,
    OptimizationConfig,
    ParallelConfig,
    StreamingConfig,
    VOIAnalysisConfig,
    create_default_config,
    create_environmental_config,
    create_financial_config,
    create_healthcare_config,
    create_metamodel_config,
    create_optimization_config,
    create_parallel_config,
    create_streaming_config,
)


def test_voi_analysis_config() -> None:
    """Test VOIAnalysisConfig."""
    # Test default configuration
    config = VOIAnalysisConfig()
    assert config.population is None
    assert config.time_horizon is None
    assert config.discount_rate is None
    assert config.chunk_size is None
    assert config.use_jit is False
    assert config.backend == "numpy"
    assert config.enable_caching is False
    assert config.streaming_window_size is None
    assert config.n_regression_samples is None
    assert config.n_simulations == 1000

    # Test custom configuration
    config = VOIAnalysisConfig(
        population=100000,
        time_horizon=10,
        discount_rate=0.03,
        chunk_size=1000,
        use_jit=True,
        backend="jax",
        enable_caching=True,
        streaming_window_size=5000,
        n_regression_samples=5000,
        n_simulations=2000,
    )

    assert config.population == 100000
    assert config.time_horizon == 10
    assert config.discount_rate == 0.03
    assert config.chunk_size == 1000
    assert config.use_jit is True
    assert config.backend == "jax"
    assert config.enable_caching is True
    assert config.streaming_window_size == 5000
    assert config.n_regression_samples == 5000
    assert config.n_simulations == 2000

    # Test to_dict method
    config_dict = config.to_dict()
    assert isinstance(config_dict, dict)
    assert config_dict["population"] == 100000
    assert config_dict["time_horizon"] == 10
    assert config_dict["discount_rate"] == 0.03
    assert config_dict["chunk_size"] == 1000
    assert config_dict["use_jit"] is True
    assert config_dict["backend"] == "jax"
    assert config_dict["enable_caching"] is True
    assert config_dict["streaming_window_size"] == 5000
    assert config_dict["n_regression_samples"] == 5000
    assert config_dict["regression_model"] is None
    assert config_dict["n_simulations"] == 2000

    # Test to_dict method on default config
    default_config = VOIAnalysisConfig()
    default_dict = default_config.to_dict()
    assert default_dict["population"] is None
    assert default_dict["time_horizon"] is None
    assert default_dict["discount_rate"] is None
    assert default_dict["chunk_size"] is None
    assert default_dict["use_jit"] is False
    assert default_dict["backend"] == "numpy"
    assert default_dict["enable_caching"] is False
    assert default_dict["streaming_window_size"] is None
    assert default_dict["n_regression_samples"] is None
    assert default_dict["regression_model"] is None
    assert default_dict["n_simulations"] == 1000


def test_streaming_config() -> None:
    """Test StreamingConfig."""
    # Test default configuration
    config = StreamingConfig()
    assert config.window_size == 1000
    assert config.update_frequency == 100
    assert config.buffer_size is None

    # Test custom configuration
    config = StreamingConfig(window_size=2000, update_frequency=50, buffer_size=10000)

    assert config.window_size == 2000
    assert config.update_frequency == 50
    assert config.buffer_size == 10000

    # Test validation
    with pytest.raises(ValueError):
        StreamingConfig(window_size=-1)

    with pytest.raises(ValueError):
        StreamingConfig(update_frequency=0)

    with pytest.raises(ValueError):
        StreamingConfig(buffer_size=-1)


def test_metamodel_config() -> None:
    """Test MetamodelConfig."""
    # Test default configuration
    config = MetamodelConfig()
    assert config.method == "gam"
    assert config.n_samples == 10000
    assert config.n_folds == 5

    # Test custom configuration
    config = MetamodelConfig(
        method="gp",
        n_samples=5000,
        n_folds=10,
        gp_length_scale=2.0,
        gp_noise_level=0.05,
    )

    assert config.method == "gp"
    assert config.n_samples == 5000
    assert config.n_folds == 10
    assert config.gp_length_scale == 2.0
    assert config.gp_noise_level == 0.05

    # Test validation
    with pytest.raises(ValueError):
        MetamodelConfig(method="invalid_method")


def test_optimization_config() -> None:
    """Test OptimizationConfig."""
    # Test default configuration
    config = OptimizationConfig()
    assert config.algorithm == "grid"
    assert config.n_iterations == 100
    assert config.n_initial_points == 10

    # Test custom configuration
    config = OptimizationConfig(
        algorithm="bayesian",
        n_iterations=200,
        n_initial_points=20,
        acquisition_function="ucb",
        kappa=3.0,
    )

    assert config.algorithm == "bayesian"
    assert config.n_iterations == 200
    assert config.n_initial_points == 20
    assert config.acquisition_function == "ucb"
    assert config.kappa == 3.0

    # Test validation
    with pytest.raises(ValueError):
        OptimizationConfig(algorithm="invalid_algorithm")

    with pytest.raises(ValueError):
        OptimizationConfig(acquisition_function="invalid_function")


def test_create_optimization_config() -> None:
    """Test create_optimization_config factory function."""
    # Test default
    config = create_optimization_config()
    assert isinstance(config, OptimizationConfig)
    assert config.algorithm == "grid"

    # Test custom valid algorithm
    config = create_optimization_config(algorithm="bayesian")
    assert isinstance(config, OptimizationConfig)
    assert config.algorithm == "bayesian"

    # Test validation
    with pytest.raises(ValueError):
        create_optimization_config(algorithm="invalid_algorithm")


def test_healthcare_config() -> None:
    """Test HealthcareConfig."""
    # Test default configuration
    config = HealthcareConfig()
    assert config.qaly_discount_rate == 0.03
    assert config.cost_discount_rate == 0.03
    assert config.cycle_length == 1.0
    assert config.max_cycles == 50

    # Test custom configuration
    config = HealthcareConfig(
        qaly_discount_rate=0.05,
        cost_discount_rate=0.04,
        cycle_length=0.5,
        max_cycles=100,
        markov_cohort_size=5000,
        markov_start_age=30.0,
    )

    assert config.qaly_discount_rate == 0.05
    assert config.cost_discount_rate == 0.04
    assert config.cycle_length == 0.5
    assert config.max_cycles == 100
    assert config.markov_cohort_size == 5000
    assert config.markov_start_age == 30.0

    # Test validation
    with pytest.raises(ValueError):
        HealthcareConfig(qaly_discount_rate=1.5)

    with pytest.raises(ValueError):
        HealthcareConfig(cost_discount_rate=-0.1)

    with pytest.raises(ValueError):
        HealthcareConfig(cycle_length=-1)

    with pytest.raises(ValueError):
        HealthcareConfig(max_cycles=0)

    with pytest.raises(ValueError):
        HealthcareConfig(markov_cohort_size=0)

    with pytest.raises(ValueError):
        HealthcareConfig(markov_start_age=-1)


def test_environmental_config() -> None:
    """Test EnvironmentalConfig."""
    # Test default configuration
    config = EnvironmentalConfig()
    assert config.carbon_intensity == 0.5
    assert config.energy_consumption == 10000
    assert config.water_intensity == 0.1

    # Test custom configuration
    config = EnvironmentalConfig(
        carbon_intensity=0.3,
        energy_consumption=5000,
        water_intensity=0.05,
        water_cost=0.003,
        biodiversity_impact_factor=0.02,
        social_cost_of_carbon=75,
        ecosystem_service_value=150,
    )

    assert config.carbon_intensity == 0.3
    assert config.energy_consumption == 5000
    assert config.water_intensity == 0.05
    assert config.water_cost == 0.003
    assert config.biodiversity_impact_factor == 0.02
    assert config.social_cost_of_carbon == 75
    assert config.ecosystem_service_value == 150

    # Test validation
    with pytest.raises(ValueError):
        EnvironmentalConfig(carbon_intensity=-1)

    with pytest.raises(ValueError):
        EnvironmentalConfig(energy_consumption=-1)

    with pytest.raises(ValueError):
        EnvironmentalConfig(water_intensity=-1)

    with pytest.raises(ValueError):
        EnvironmentalConfig(water_cost=-1)

    with pytest.raises(ValueError):
        EnvironmentalConfig(biodiversity_impact_factor=-1)

    with pytest.raises(ValueError):
        EnvironmentalConfig(social_cost_of_carbon=-1)

    with pytest.raises(ValueError):
        EnvironmentalConfig(ecosystem_service_value=-1)


def test_financial_config() -> None:
    """Test FinancialConfig."""
    # Test default configuration
    config = FinancialConfig()
    assert config.var_confidence_level == 0.95
    assert config.cvar_confidence_level == 0.95
    assert config.sharpe_ratio_risk_free_rate == 0.0001
    assert config.mc_n_simulations == 10000

    # Test custom configuration
    config = FinancialConfig(
        var_confidence_level=0.99,
        cvar_confidence_level=0.99,
        sharpe_ratio_risk_free_rate=0.0002,
        mc_n_simulations=20000,
        mc_time_horizon=504,
        stress_test_scenarios=[
            "market_crash",
            "interest_rate_shock",
            "currency_crisis",
        ],
    )

    assert config.var_confidence_level == 0.99
    assert config.cvar_confidence_level == 0.99
    assert config.sharpe_ratio_risk_free_rate == 0.0002
    assert config.mc_n_simulations == 20000
    assert config.mc_time_horizon == 504
    assert len(config.stress_test_scenarios) == 3

    # Test validation
    with pytest.raises(ValueError):
        FinancialConfig(var_confidence_level=1.5)

    with pytest.raises(ValueError):
        FinancialConfig(cvar_confidence_level=0)

    with pytest.raises(ValueError):
        FinancialConfig(mc_n_simulations=0)

    with pytest.raises(ValueError):
        FinancialConfig(mc_time_horizon=0)


def test_parallel_config() -> None:
    """Test ParallelConfig."""
    # Test default configuration
    config = ParallelConfig()
    assert config.n_workers is None
    assert config.use_processes is True
    assert config.max_workers is None

    # Test custom configuration
    config = ParallelConfig(
        n_workers=4,
        use_processes=False,
        max_workers=8,
        memory_limit_mb=8192,
        chunk_size=1000,
    )

    assert config.n_workers == 4
    assert config.use_processes is False
    assert config.max_workers == 8
    assert config.memory_limit_mb == 8192
    assert config.chunk_size == 1000

    # Test validation
    with pytest.raises(ValueError):
        ParallelConfig(n_workers=-1)

    with pytest.raises(ValueError):
        ParallelConfig(max_workers=0)

    with pytest.raises(ValueError):
        ParallelConfig(memory_limit_mb=0)

    with pytest.raises(ValueError):
        ParallelConfig(chunk_size=0)


def test_create_default_config() -> None:
    """Test create_default_config factory function."""
    config = create_default_config()
    assert isinstance(config, VOIAnalysisConfig)

    # Check default values
    assert config.population is None
    assert config.time_horizon is None
    assert config.discount_rate is None
    assert config.chunk_size is None
    assert config.use_jit is False
    assert config.backend == "numpy"
    assert config.enable_caching is False
    assert config.streaming_window_size is None
    assert config.n_regression_samples is None
    assert config.regression_model is None
    assert config.n_simulations == 1000


def test_create_environmental_config() -> None:
    """Test create_environmental_config factory function."""
    config = create_environmental_config()
    assert isinstance(config, EnvironmentalConfig)
    # Check default properties
    assert config.carbon_intensity == 0.5
    assert config.energy_consumption == 10000
    assert config.water_intensity == 0.1
    assert config.water_cost == 0.002
    assert config.biodiversity_impact_factor == 0.01
    assert config.social_cost_of_carbon == 50


def test_create_healthcare_config() -> None:
    """Test create_healthcare_config factory function."""
    config = create_healthcare_config()
    assert isinstance(config, HealthcareConfig)
    assert config.qaly_discount_rate == 0.03
    assert config.cost_discount_rate == 0.03
    assert config.cycle_length == 1.0
    assert config.max_cycles == 50
    assert config.markov_cohort_size == 10000
    assert config.markov_start_age == 25.0


def test_create_parallel_config() -> None:
    """Test create_parallel_config factory function."""
    config = create_parallel_config()
    assert isinstance(config, ParallelConfig)
    assert config.n_workers is None
    assert config.use_processes is True
    assert config.max_workers is None
    assert config.memory_limit_mb is None
    assert config.chunk_size is None


def test_create_financial_config() -> None:
    """Test create_financial_config factory function."""
    config = create_financial_config()
    assert isinstance(config, FinancialConfig)
    assert config.var_confidence_level == 0.95
    assert config.cvar_confidence_level == 0.95
    assert config.sharpe_ratio_risk_free_rate == 0.0001
    assert config.mc_n_simulations == 10000
    assert config.mc_time_horizon == 252
    assert config.stress_test_scenarios == ["market_crash", "interest_rate_shock"]


def test_factory_functions() -> None:
    """Test factory functions."""
    # Test create_default_config
    config = create_default_config()
    assert isinstance(config, VOIAnalysisConfig)

    # Test create_environmental_config
    config = create_environmental_config()
    assert isinstance(config, EnvironmentalConfig)

    # Test create_financial_config
    config = create_financial_config()
    assert isinstance(config, FinancialConfig)

    # Test create_parallel_config
    config = create_parallel_config()
    assert isinstance(config, ParallelConfig)

    # Test create_streaming_config
    config = create_streaming_config()
    assert isinstance(config, StreamingConfig)

    # Test create_metamodel_config
    config = create_metamodel_config()
    assert isinstance(config, MetamodelConfig)
    assert config.method == "gam"

    config = create_metamodel_config(method="gp")
    assert isinstance(config, MetamodelConfig)
    assert config.method == "gp"


def test_create_streaming_config() -> None:
    """Test create_streaming_config factory function."""
    config = create_streaming_config()
    assert isinstance(config, StreamingConfig)

    # Check default values are set correctly
    assert config.window_size == 1000
    assert config.update_frequency == 100
    assert config.buffer_size is None


if __name__ == "__main__":
    test_create_default_config()
    test_voi_analysis_config()
    test_streaming_config()
    test_metamodel_config()
    test_optimization_config()
    test_healthcare_config()
    test_environmental_config()
    test_financial_config()
    test_parallel_config()
    test_create_healthcare_config()
    test_create_parallel_config()
    test_create_financial_config()
    test_factory_functions()
    test_create_optimization_config()
    test_create_streaming_config()
    print("All configuration objects tests passed!")
