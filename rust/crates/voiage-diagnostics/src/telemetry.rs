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

#[cfg(test)]
mod tests {
    use super::{emit, Correlation};
    use std::hint::black_box;
    use std::sync::{
        atomic::{AtomicUsize, Ordering},
        Arc, Mutex,
    };
    use std::time::{Duration, Instant};
    use tracing::span::{Attributes, Id, Record};
    use tracing::{Event, Metadata, Subscriber};

    const SAMPLES: usize = 2_048;
    const MAX_OVERHEAD_RATIO: f64 = 25.0;
    static TEST_LOCK: Mutex<()> = Mutex::new(());

    #[derive(Debug, Clone)]
    struct EnabledSubscriber {
        events: Arc<AtomicUsize>,
    }

    impl Subscriber for EnabledSubscriber {
        fn enabled(&self, _metadata: &Metadata<'_>) -> bool {
            true
        }

        fn new_span(&self, _span: &Attributes<'_>) -> Id {
            Id::from_u64(1)
        }

        fn record(&self, _span: &Id, _values: &Record<'_>) {}

        fn record_follows_from(&self, _span: &Id, _follows: &Id) {}

        fn event(&self, _event: &Event<'_>) {
            self.events.fetch_add(1, Ordering::Relaxed);
        }

        fn enter(&self, _span: &Id) {}

        fn exit(&self, _span: &Id) {}
    }

    fn reference_kernel() -> u64 {
        (0..64_u64).fold(0x9e37_79b9_7f4a_7c15, |state, value| {
            state
                .rotate_left(7)
                .wrapping_mul(0x1000_0000_01b3)
                .wrapping_add(value ^ 0xa5a5_a5a5_a5a5_a5a5)
        })
    }

    fn digest(value: u64) -> u64 {
        value.wrapping_mul(0x9e37_79b9_7f4a_7c15).rotate_left(17) ^ 0x243f_6a88_85a3_08d3
    }

    fn accumulate(value: u64, sample: usize) -> u64 {
        value
            .wrapping_add(black_box(reference_kernel()).rotate_left((sample % 64) as u32))
            .wrapping_add(sample as u64 ^ 0xd6e8_feb8_6659_fd93)
    }

    fn measure_disabled(correlation: &Correlation) -> (u64, Duration) {
        let start = Instant::now();
        let mut value = 0_u64;
        for sample in 0..SAMPLES {
            value = accumulate(value, sample);
            emit(correlation, "deterministic-reference-kernel");
        }
        (digest(value), start.elapsed())
    }

    fn measure_enabled(correlation: &Correlation) -> (u64, Duration) {
        let start = Instant::now();
        let mut value = 0_u64;
        for sample in 0..SAMPLES {
            value = accumulate(value, sample);
            emit(correlation, "deterministic-reference-kernel");
        }
        (digest(value), start.elapsed())
    }

    #[test]
    fn logging_does_not_change_reference_kernel_identity() {
        let _guard = TEST_LOCK.lock().expect("telemetry test lock");
        let correlation = Correlation::new("run-fixed", "analysis-fixed");
        let (disabled_hash, _) = measure_disabled(&correlation);
        let events = Arc::new(AtomicUsize::new(0));
        let subscriber = EnabledSubscriber {
            events: Arc::clone(&events),
        };
        let (enabled_hash, _) =
            tracing::subscriber::with_default(subscriber, || measure_enabled(&correlation));
        assert_eq!(disabled_hash, enabled_hash);
        assert_eq!(events.load(Ordering::Relaxed), SAMPLES);
    }

    #[test]
    fn enabled_logging_stays_within_reviewed_overhead_budget() {
        let _guard = TEST_LOCK.lock().expect("telemetry test lock");
        let correlation = Correlation::new("run-fixed", "analysis-fixed");
        let (_, disabled) = measure_disabled(&correlation);
        let events = Arc::new(AtomicUsize::new(0));
        let subscriber = EnabledSubscriber {
            events: Arc::clone(&events),
        };
        let (_, enabled) =
            tracing::subscriber::with_default(subscriber, || measure_enabled(&correlation));
        assert_eq!(events.load(Ordering::Relaxed), SAMPLES);
        let disabled_ns = disabled.as_nanos().max(1) as f64;
        let enabled_ns = enabled.as_nanos() as f64;
        assert!(
            enabled_ns / disabled_ns <= MAX_OVERHEAD_RATIO,
            "enabled logging overhead exceeded {:.1}x budget: disabled={disabled:?}, enabled={enabled:?}",
            MAX_OVERHEAD_RATIO
        );
    }
}
