use voiage_domain::SampleMatrix;

use crate::NumericalInputError;

/// Computes expected value of perfect information from `[sample][strategy]`
/// net-benefit values.
///
/// # Errors
///
/// The matrix is validated by [`SampleMatrix`]. This result-bearing signature
/// preserves a uniform numerical-kernel boundary for future checked failures.
pub fn evpi(net_benefit: &SampleMatrix) -> Result<f64, NumericalInputError> {
    let [sample_count, strategy_count] = net_benefit.shape();
    let divisor = f64::from(u32::try_from(sample_count).map_err(|_| {
        NumericalInputError::invalid(
            "net_benefit",
            "sample count exceeds the supported numerical range",
        )
    })?);
    let mut strategy_means = vec![0.0; strategy_count];
    let mut perfect_information_mean = 0.0;

    for row in net_benefit.rows() {
        let mut row_maximum = f64::NEG_INFINITY;
        for (strategy_index, value) in row.iter().copied().enumerate() {
            strategy_means[strategy_index] += value / divisor;
            row_maximum = row_maximum.max(value);
        }
        perfect_information_mean += row_maximum / divisor;
    }

    let current_information_mean = strategy_means.into_iter().fold(f64::NEG_INFINITY, f64::max);

    Ok((perfect_information_mean - current_information_mean).max(0.0))
}

#[cfg(test)]
mod tests {
    use super::evpi;
    use voiage_domain::SampleMatrix;

    fn matrix(values: Vec<Vec<f64>>) -> SampleMatrix {
        values.try_into().expect("valid matrix")
    }

    #[test]
    fn affine_invariance_holds_for_constant_shift_and_positive_scaling() {
        let base = matrix(vec![vec![1.0, 3.0], vec![4.0, 2.0], vec![5.0, 6.0]]);
        let shifted = matrix(vec![vec![11.0, 13.0], vec![14.0, 12.0], vec![15.0, 16.0]]);
        let scaled = matrix(vec![vec![2.0, 6.0], vec![8.0, 4.0], vec![10.0, 12.0]]);
        let baseline = evpi(&base).expect("baseline");
        assert!(
            (evpi(&shifted).expect("shifted") - baseline).abs() < 1.0e-12 * baseline.max(1.0),
            "baseline={baseline:?} shifted={:?}",
            evpi(&shifted)
        );
        assert!(
            (evpi(&scaled).expect("scaled") - 2.0 * baseline).abs() < 1.0e-12 * baseline.max(1.0)
        );
    }

    #[test]
    fn matrix_contract_rejects_non_finite_inputs_before_evaluation() {
        assert!(SampleMatrix::try_from(vec![vec![1.0, f64::NAN]]).is_err());
        assert!(SampleMatrix::try_from(vec![vec![1.0, f64::INFINITY]]).is_err());
    }

    #[test]
    fn extreme_finite_scale_preserves_the_analytic_evpi() {
        let scale = 0.75 * f64::MAX;
        let values = matrix(vec![vec![scale, 0.0], [0.5 * scale, scale].to_vec()]);
        let expected = 0.25 * scale;
        let actual = evpi(&values).expect("finite extreme-scale result");
        assert!(
            (actual - expected).abs() / expected < 1.0e-12,
            "actual={actual:?} expected={expected:?}"
        );
    }
}
