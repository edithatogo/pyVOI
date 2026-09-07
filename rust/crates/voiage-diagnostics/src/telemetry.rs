//! Application-owned, optional structured diagnostic events.

use std::fmt;

/// Stable fields attached to a diagnostic event.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Correlation {
    /// Run identifier supplied by the host application.
    pub run_id: String,
    /// Analysis identifier supplied by the host application.
    pub analysis_id: String,
}

impl Correlation {
    /// Construct correlation without installing a global subscriber.
    #[must_use]
    pub fn new(run_id: impl Into<String>, analysis_id: impl Into<String>) -> Self {
        Self {
            run_id: run_id.into(),
            analysis_id: analysis_id.into(),
        }
    }
}

impl fmt::Display for Correlation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "run_id={} analysis_id={}", self.run_id, self.analysis_id)
    }
}

/// Emit a diagnostic event to the host-installed tracing subscriber, if any.
pub fn emit(correlation: &Correlation, message: &str) {
    tracing::info!(run_id = %correlation.run_id, analysis_id = %correlation.analysis_id, event = "voiage.diagnostic", message);
}
