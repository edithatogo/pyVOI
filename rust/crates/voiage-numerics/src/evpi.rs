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
    let mut strategy_totals = vec![0.0; strategy_count];
    let mut perfect_information_total = 0.0;

    for row in net_benefit.rows() {
        let mut row_maximum = f64::NEG_INFINITY;
        for (strategy_index, value) in row.iter().copied().enumerate() {
            strategy_totals[strategy_index] += value;
            row_maximum = row_maximum.max(value);
        }
        perfect_information_total += row_maximum;
    }

    let divisor = f64::from(u32::try_from(sample_count).map_err(|_| {
        NumericalInputError::invalid(
            "net_benefit",
            "sample count exceeds the supported numerical range",
        )
    })?);
    let perfect_information_mean = perfect_information_total / divisor;
    let current_information_mean = strategy_totals
        .into_iter()
        .map(|total| total / divisor)
        .fold(f64::NEG_INFINITY, f64::max);

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
        assert!((evpi(&shifted).expect("shifted") - baseline).abs() < 1.0e-12);
        assert!((evpi(&scaled).expect("scaled") - 2.0 * baseline).abs() < 1.0e-12);
    }

    #[test]
    fn matrix_contract_rejects_non_finite_inputs_before_evaluation() {
        assert!(SampleMatrix::try_from(vec![vec![1.0, f64::NAN]]).is_err());
        assert!(SampleMatrix::try_from(vec![vec![1.0, f64::INFINITY]]).is_err());
    }
}
