//! Optional trace-export boundary, intentionally inert until an application opts in.

/// Explicit opt-in configuration for a future OpenTelemetry bridge.
#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct TraceExportConfig {
    /// Whether an application explicitly enabled export.
    enabled: bool,
    /// Maximum number of export retries before giving up.
    max_retries: u8,
}

impl TraceExportConfig {
    /// Reject unbounded retry policies and preserve feature-off operation.
    ///
    /// # Errors
    ///
    /// Returns an error when the retry budget exceeds three attempts.
    pub fn new(enabled: bool, max_retries: u8) -> Result<Self, &'static str> {
        if max_retries > 3 {
            return Err("max_retries must be <= 3");
        }
        Ok(Self {
            enabled,
            max_retries,
        })
    }

    /// Returns whether export was explicitly enabled.
    #[must_use]
    pub const fn enabled(&self) -> bool {
        self.enabled
    }

    /// Returns the bounded retry budget.
    #[must_use]
    pub const fn max_retries(&self) -> u8 {
        self.max_retries
    }
}
