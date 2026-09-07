//! Structured diagnostics and error contracts for voiage.

#![forbid(unsafe_code)]

use std::collections::BTreeMap;

mod contracts;
mod domain_mapping;
#[cfg(feature = "otel")]
pub mod otel_export;
pub mod telemetry;

pub use contracts::{
    ApproximationStatus, DiagnosticStatus, Diagnostics, MethodMaturity, MethodMetadata,
    WarningRecord, WarningSeverity,
};

/// Identifies this crate while structured diagnostics are introduced.
pub const CRATE_NAME: &str = "voiage-diagnostics";

/// Stable language-neutral error categories used by binding adapters.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum ErrorCategory {
    /// Invalid values or unsupported input combinations.
    Input,
    /// Incompatible vector, matrix, or tensor dimensions.
    DimensionMismatch,
    /// A requested execution backend is not available.
    BackendUnavailable,
    /// A numerical method could not produce a valid result.
    Numerical,
    /// Encoding or decoding failed.
    Serialization,
}

/// Stable machine-readable error codes.
///
/// Binding implementations must dispatch on these codes rather than on the
/// human-readable error message.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum ErrorCode {
    /// An input failed validation.
    InvalidInput,
    /// Input dimensions are incompatible.
    DimensionMismatch,
    /// The requested backend is not available.
    BackendUnavailable,
    /// A numerical computation failed.
    NumericalFailure,
    /// Serialization or deserialization failed.
    SerializationFailure,
}

impl ErrorCode {
    /// Returns the stable snake-case identifier.
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::InvalidInput => "invalid_input",
            Self::DimensionMismatch => "dimension_mismatch",
            Self::BackendUnavailable => "backend_unavailable",
            Self::NumericalFailure => "numerical_failure",
            Self::SerializationFailure => "serialization_failure",
        }
    }

    /// Returns the binding-level category for this code.
    #[must_use]
    pub const fn category(self) -> ErrorCategory {
        match self {
            Self::InvalidInput => ErrorCategory::Input,
            Self::DimensionMismatch => ErrorCategory::DimensionMismatch,
            Self::BackendUnavailable => ErrorCategory::BackendUnavailable,
            Self::NumericalFailure => ErrorCategory::Numerical,
            Self::SerializationFailure => ErrorCategory::Serialization,
        }
    }

    /// Returns the reserved deterministic ABI status for this code.
    ///
    /// This mapping reserves status values for a future FFI adapter; it does
    /// not define or export a C ABI.
    #[must_use]
    pub const fn abi_status(self) -> AbiStatus {
        match self {
            Self::InvalidInput => AbiStatus::Input,
            Self::DimensionMismatch => AbiStatus::DimensionMismatch,
            Self::BackendUnavailable => AbiStatus::BackendUnavailable,
            Self::NumericalFailure => AbiStatus::Numerical,
            Self::SerializationFailure => AbiStatus::Serialization,
        }
    }
}

/// Reserved status values for deterministic translation by a future ABI.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
#[repr(u32)]
pub enum AbiStatus {
    /// Successful operation.
    Success = 0,
    /// Invalid input.
    Input = 10,
    /// Incompatible dimensions.
    DimensionMismatch = 11,
    /// Requested backend unavailable.
    BackendUnavailable = 20,
    /// Numerical failure.
    Numerical = 30,
    /// Serialization failure.
    Serialization = 40,
    /// Reserved catch-all for unexpected internal failures.
    Internal = 255,
}

impl AbiStatus {
    /// Returns the stable numeric status value.
    #[must_use]
    pub const fn as_u32(self) -> u32 {
        self as u32
    }
}

/// Optional structured context attached to an error record.
#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct ErrorDetails {
    field: Option<String>,
    expected_dimensions: Option<Vec<usize>>,
    actual_dimensions: Option<Vec<usize>>,
    backend: Option<String>,
    context: BTreeMap<String, String>,
}

impl ErrorDetails {
    /// Creates empty structured details.
    #[must_use]
    pub const fn new() -> Self {
        Self {
            field: None,
            expected_dimensions: None,
            actual_dimensions: None,
            backend: None,
            context: BTreeMap::new(),
        }
    }

    /// Sets the affected field or path.
    #[must_use]
    pub fn with_field(mut self, field: impl Into<String>) -> Self {
        self.field = Some(field.into());
        self
    }

    /// Sets the expected dimensions.
    #[must_use]
    pub fn with_expected_dimensions(mut self, dimensions: impl IntoIterator<Item = usize>) -> Self {
        self.expected_dimensions = Some(dimensions.into_iter().collect());
        self
    }

    /// Sets the observed dimensions.
    #[must_use]
    pub fn with_actual_dimensions(mut self, dimensions: impl IntoIterator<Item = usize>) -> Self {
        self.actual_dimensions = Some(dimensions.into_iter().collect());
        self
    }

    /// Sets the requested backend identifier.
    #[must_use]
    pub fn with_backend(mut self, backend: impl Into<String>) -> Self {
        self.backend = Some(backend.into());
        self
    }

    /// Adds deterministic machine-readable context.
    #[must_use]
    pub fn with_context(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        self.context.insert(key.into(), value.into());
        self
    }

    /// Returns the affected field or path.
    #[must_use]
    pub fn field(&self) -> Option<&str> {
        self.field.as_deref()
    }

    /// Returns the expected dimensions.
    #[must_use]
    pub fn expected_dimensions(&self) -> Option<&[usize]> {
        self.expected_dimensions.as_deref()
    }

    /// Returns the observed dimensions.
    #[must_use]
    pub fn actual_dimensions(&self) -> Option<&[usize]> {
        self.actual_dimensions.as_deref()
    }

    /// Returns the requested backend identifier.
    #[must_use]
    pub fn backend(&self) -> Option<&str> {
        self.backend.as_deref()
    }

    /// Returns a context value by key.
    #[must_use]
    pub fn context(&self, key: &str) -> Option<&str> {
        self.context.get(key).map(String::as_str)
    }
}

/// A stable error identity plus safe human-readable and structured context.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ErrorRecord {
    code: ErrorCode,
    message: String,
    details: Option<ErrorDetails>,
}

impl ErrorRecord {
    /// Creates an error record without structured details.
    #[must_use]
    pub fn new(code: ErrorCode, message: impl Into<String>) -> Self {
        Self {
            code,
            message: message.into(),
            details: None,
        }
    }

    /// Attaches structured details.
    #[must_use]
    pub fn with_details(mut self, details: ErrorDetails) -> Self {
        self.details = Some(details);
        self
    }

    /// Returns the stable machine-readable code.
    #[must_use]
    pub const fn code(&self) -> ErrorCode {
        self.code
    }

    /// Returns the binding-level error category.
    #[must_use]
    pub const fn category(&self) -> ErrorCategory {
        self.code.category()
    }

    /// Returns the reserved deterministic ABI status.
    #[must_use]
    pub const fn abi_status(&self) -> AbiStatus {
        self.code.abi_status()
    }

    /// Returns the safe human-readable message.
    #[must_use]
    pub fn message(&self) -> &str {
        &self.message
    }

    /// Returns optional structured details.
    #[must_use]
    pub const fn details(&self) -> Option<&ErrorDetails> {
        self.details.as_ref()
    }
}

#[cfg(test)]
mod tests {
    use super::{AbiStatus, ErrorCategory, ErrorCode, ErrorDetails, ErrorRecord};

    #[test]
    fn stable_codes_map_to_python_categories_and_reserved_abi_statuses() {
        let cases = [
            (
                ErrorCode::InvalidInput,
                ErrorCategory::Input,
                AbiStatus::Input,
            ),
            (
                ErrorCode::DimensionMismatch,
                ErrorCategory::DimensionMismatch,
                AbiStatus::DimensionMismatch,
            ),
            (
                ErrorCode::BackendUnavailable,
                ErrorCategory::BackendUnavailable,
                AbiStatus::BackendUnavailable,
            ),
            (
                ErrorCode::NumericalFailure,
                ErrorCategory::Numerical,
                AbiStatus::Numerical,
            ),
            (
                ErrorCode::SerializationFailure,
                ErrorCategory::Serialization,
                AbiStatus::Serialization,
            ),
        ];

        for (code, category, status) in cases {
            assert_eq!(code.category(), category);
            assert_eq!(code.abi_status(), status);
            assert!(!code.as_str().is_empty());
            assert_ne!(status.as_u32(), 0);
        }
    }

    #[test]
    fn structured_details_preserve_machine_readable_context() {
        let details = ErrorDetails::new()
            .with_field("net_benefit")
            .with_expected_dimensions([100, 3])
            .with_actual_dimensions([100, 2])
            .with_backend("gpu")
            .with_context("operation", "evsi");
        let error = ErrorRecord::new(
            ErrorCode::DimensionMismatch,
            "strategy dimensions do not match",
        )
        .with_details(details);

        assert_eq!(error.category(), ErrorCategory::DimensionMismatch);
        assert_eq!(error.code().as_str(), "dimension_mismatch");
        assert_eq!(error.message(), "strategy dimensions do not match");
        assert_eq!(
            error.details().and_then(ErrorDetails::field),
            Some("net_benefit")
        );
        assert_eq!(
            error.details().and_then(ErrorDetails::expected_dimensions),
            Some(&[100, 3][..])
        );
        assert_eq!(
            error.details().and_then(ErrorDetails::actual_dimensions),
            Some(&[100, 2][..])
        );
        assert_eq!(error.details().and_then(ErrorDetails::backend), Some("gpu"));
        assert_eq!(
            error
                .details()
                .and_then(|details| details.context("operation")),
            Some("evsi")
        );
    }

    #[test]
    fn error_identity_does_not_depend_on_display_message() {
        let first = ErrorRecord::new(ErrorCode::InvalidInput, "first wording");
        let second = ErrorRecord::new(ErrorCode::InvalidInput, "revised wording");

        assert_eq!(first.code(), second.code());
        assert_eq!(first.category(), second.category());
        assert_eq!(first.abi_status(), second.abi_status());
        assert_ne!(first.message(), second.message());
    }

    #[test]
    fn abi_status_values_are_stable_and_reserve_success() {
        assert_eq!(AbiStatus::Success.as_u32(), 0);
        assert_eq!(AbiStatus::Input.as_u32(), 10);
        assert_eq!(AbiStatus::DimensionMismatch.as_u32(), 11);
        assert_eq!(AbiStatus::BackendUnavailable.as_u32(), 20);
        assert_eq!(AbiStatus::Numerical.as_u32(), 30);
        assert_eq!(AbiStatus::Serialization.as_u32(), 40);
        assert_eq!(AbiStatus::Internal.as_u32(), 255);
    }
}
