//! Optional trace-export boundary, intentionally inert until an application opts in.

/// Explicit opt-in configuration for a future OpenTelemetry bridge.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TraceExportConfig {
    /// Whether an application explicitly enabled export.
    pub enabled: bool,
    /// Maximum number of export retries before giving up.
    pub max_retries: u8,
}

impl Default for TraceExportConfig {
    fn default() -> Self {
        Self {
            enabled: false,
            max_retries: 0,
        }
    }
}

impl TraceExportConfig {
    /// Reject unbounded retry policies and preserve feature-off operation.
    pub fn new(enabled: bool, max_retries: u8) -> Result<Self, &'static str> {
        if max_retries > 3 {
            return Err("max_retries must be <= 3");
        }
        Ok(Self {
            enabled,
            max_retries,
        })
    }
}
