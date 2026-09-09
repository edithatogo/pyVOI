//! Durable identity and resume contracts for bounded executions.

use serde::{Deserialize, Deserializer, Serialize};
use std::fmt;
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, Mutex};

/// Immutable identities that must match before a checkpoint can be resumed.
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct CheckpointIdentity {
    /// Identity of the model and its input data.
    pub model_input: String,
    /// Identity of the random-number stream or deterministic seed.
    pub rng: String,
    /// Identity of the algorithm and its configuration.
    pub algorithm: String,
}

#[derive(Deserialize)]
struct CheckpointIdentityWire {
    model_input: String,
    rng: String,
    algorithm: String,
}

impl<'de> Deserialize<'de> for CheckpointIdentity {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let wire = CheckpointIdentityWire::deserialize(deserializer)?;
        Self::new(wire.model_input, wire.rng, wire.algorithm).map_err(serde::de::Error::custom)
    }
}

impl CheckpointIdentity {
    /// Construct an identity, rejecting empty components.
    ///
    /// # Errors
    ///
    /// Returns [`CheckpointError::EmptyIdentity`] when any component is empty.
    pub fn new(
        model_input: impl Into<String>,
        rng: impl Into<String>,
        algorithm: impl Into<String>,
    ) -> Result<Self, CheckpointError> {
        let identity = Self {
            model_input: model_input.into(),
            rng: rng.into(),
            algorithm: algorithm.into(),
        };
        if identity.model_input.is_empty()
            || identity.rng.is_empty()
            || identity.algorithm.is_empty()
        {
            return Err(CheckpointError::EmptyIdentity);
        }
        Ok(identity)
    }
}

/// A finite evaluation budget with atomic batch reservations.
#[derive(Clone, Debug)]
pub struct ExecutionBudget {
    /// Maximum model evaluations permitted for the complete execution.
    pub max_evaluations: u64,
    remaining: Arc<AtomicU64>,
}

/// Cooperative cancellation flag checked at batch boundaries.
#[derive(Clone, Debug, Default)]
pub struct CancellationToken {
    cancelled: Arc<AtomicBool>,
    admission: Arc<Mutex<()>>,
}

impl CancellationToken {
    /// Create a token in the non-cancelled state.
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    /// Request cancellation; callers observe it before admitting the next batch.
    pub fn cancel(&self) {
        let _guard = self
            .admission
            .lock()
            .unwrap_or_else(std::sync::PoisonError::into_inner);
        self.cancelled.store(true, Ordering::Release);
    }

    /// Whether cancellation has been requested.
    #[must_use]
    pub fn is_cancelled(&self) -> bool {
        self.cancelled.load(Ordering::Acquire)
    }

    /// Reserve a batch only when cancellation has not been requested.
    ///
    /// # Errors
    ///
    /// Returns [`CheckpointError::Cancelled`] when cancellation was requested
    /// before the batch could be admitted.
    pub fn reserve_batch(
        &self,
        budget: &ExecutionBudget,
        batch_size: u64,
    ) -> Result<bool, CheckpointError> {
        let _guard = self
            .admission
            .lock()
            .unwrap_or_else(std::sync::PoisonError::into_inner);
        if self.is_cancelled() {
            return Err(CheckpointError::Cancelled);
        }
        Ok(budget.try_reserve(batch_size))
    }
}

/// Explicit lifecycle state for a bounded VOI computation.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ExecutionState {
    /// Work is still allowed to consume budget.
    Running,
    /// The computation completed with a valid result.
    Complete,
    /// A valid checkpoint exists, but the computation did not finish.
    Partial,
    /// Cooperative cancellation stopped work at a batch boundary.
    Cancelled,
    /// The computation failed and cannot be resumed from this state.
    Failed,
}

impl ExecutionState {
    /// Whether this state cannot consume another batch without an explicit resume.
    #[must_use]
    pub const fn is_terminal(&self) -> bool {
        !matches!(self, Self::Running)
    }

    /// Transition to another state, rejecting completion from a partial/cancelled state.
    ///
    /// # Errors
    ///
    /// Returns [`CheckpointError::InvalidStateTransition`] for an unsupported transition.
    pub fn transition(&mut self, next: Self) -> Result<(), CheckpointError> {
        let allowed = matches!(
            (self.clone(), next.clone()),
            (
                Self::Running,
                Self::Complete | Self::Partial | Self::Cancelled | Self::Failed
            ) | (Self::Partial | Self::Cancelled, Self::Running)
        );
        if allowed {
            *self = next;
            Ok(())
        } else {
            Err(CheckpointError::InvalidStateTransition)
        }
    }
}

impl ExecutionBudget {
    /// Construct a budget. Zero is valid and permits no evaluations.
    #[must_use]
    pub fn new(max_evaluations: u64) -> Self {
        Self {
            max_evaluations,
            remaining: Arc::new(AtomicU64::new(max_evaluations)),
        }
    }

    /// Return whether a batch can execute without exceeding the budget.
    #[must_use]
    pub fn allows(&self, completed_evaluations: u64, batch_size: u64) -> bool {
        completed_evaluations
            .checked_add(batch_size)
            .is_some_and(|total| total <= self.max_evaluations)
            && self.remaining.load(Ordering::Acquire) >= batch_size
    }

    /// Atomically reserve a complete batch, preventing concurrent over-admission.
    #[must_use]
    pub fn try_reserve(&self, batch_size: u64) -> bool {
        let mut current = self.remaining.load(Ordering::Acquire);
        loop {
            if current < batch_size {
                return false;
            }
            match self.remaining.compare_exchange_weak(
                current,
                current - batch_size,
                Ordering::AcqRel,
                Ordering::Acquire,
            ) {
                Ok(_) => return true,
                Err(observed) => current = observed,
            }
        }
    }

    /// Return the unreserved evaluation count.
    #[must_use]
    pub fn remaining(&self) -> u64 {
        self.remaining.load(Ordering::Acquire)
    }
}

/// A serializable, last-valid checkpoint at a batch boundary.
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ExecutionCheckpoint {
    /// Identities required for safe resume.
    pub identity: CheckpointIdentity,
    /// Number of fully committed batches.
    pub completed_batches: u64,
    /// Number of model evaluations committed in those batches.
    pub evaluations: u64,
    /// Digest of the committed partial result payload.
    pub payload_digest: String,
    /// Contract governing deterministic replay of the committed result.
    #[serde(default)]
    pub replay: ReplayContract,
}

/// CPU replay tolerance and reduction-order contract persisted with a checkpoint.
#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct ReplayContract {
    /// Non-negative absolute tolerance represented by its IEEE-754 bits.
    pub cpu_tolerance_bits: u64,
    /// Named reduction order required for deterministic replay.
    pub reduction_order: String,
}

impl Default for ReplayContract {
    fn default() -> Self {
        Self::new(1e-12, "stable_serial").expect("default replay contract is valid")
    }
}

impl ReplayContract {
    /// Construct a replay contract with a finite non-negative CPU tolerance.
    ///
    /// # Errors
    ///
    /// Returns [`CheckpointError::InvalidReplayContract`] for non-finite,
    /// negative, or empty values.
    pub fn new(
        cpu_tolerance: f64,
        reduction_order: impl Into<String>,
    ) -> Result<Self, CheckpointError> {
        let reduction_order = reduction_order.into();
        if !cpu_tolerance.is_finite() || cpu_tolerance < 0.0 || reduction_order.is_empty() {
            return Err(CheckpointError::InvalidReplayContract);
        }
        Ok(Self {
            cpu_tolerance_bits: cpu_tolerance.to_bits(),
            reduction_order,
        })
    }

    /// Return the declared CPU tolerance.
    #[must_use]
    pub fn cpu_tolerance(&self) -> f64 {
        f64::from_bits(self.cpu_tolerance_bits)
    }

    /// Check two replay values against the declared absolute CPU tolerance.
    #[must_use]
    pub fn matches(&self, expected: f64, observed: f64) -> bool {
        expected.is_finite()
            && observed.is_finite()
            && (expected - observed).abs() <= self.cpu_tolerance()
    }
}

#[derive(Deserialize)]
struct ExecutionCheckpointWire {
    identity: CheckpointIdentity,
    completed_batches: u64,
    evaluations: u64,
    payload_digest: String,
    #[serde(default)]
    replay: ReplayContract,
}

impl<'de> Deserialize<'de> for ExecutionCheckpoint {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let wire = ExecutionCheckpointWire::deserialize(deserializer)?;
        let mut checkpoint = Self::new(
            wire.identity,
            wire.completed_batches,
            wire.evaluations,
            wire.payload_digest,
        )
        .map_err(serde::de::Error::custom)?;
        checkpoint.replay = wire.replay;
        if !checkpoint.replay.cpu_tolerance().is_finite()
            || checkpoint.replay.cpu_tolerance() < 0.0
            || checkpoint.replay.reduction_order.is_empty()
        {
            return Err(serde::de::Error::custom(
                CheckpointError::InvalidReplayContract,
            ));
        }
        Ok(checkpoint)
    }
}

impl ExecutionCheckpoint {
    /// Construct a checkpoint with a non-empty payload digest.
    ///
    /// # Errors
    ///
    /// Returns [`CheckpointError::EmptyPayloadDigest`] when the digest is empty.
    pub fn new(
        identity: CheckpointIdentity,
        completed_batches: u64,
        evaluations: u64,
        payload_digest: impl Into<String>,
    ) -> Result<Self, CheckpointError> {
        let payload_digest = payload_digest.into();
        if payload_digest.is_empty() {
            return Err(CheckpointError::EmptyPayloadDigest);
        }
        Ok(Self {
            identity,
            completed_batches,
            evaluations,
            payload_digest,
            replay: ReplayContract::default(),
        })
    }

    /// Attach an explicit deterministic replay contract.
    ///
    /// # Errors
    ///
    /// Returns [`CheckpointError::InvalidReplayContract`] when the metadata
    /// is not finite and non-negative.
    pub fn with_replay(mut self, replay: ReplayContract) -> Result<Self, CheckpointError> {
        if !replay.cpu_tolerance().is_finite()
            || replay.cpu_tolerance() < 0.0
            || replay.reduction_order.is_empty()
        {
            return Err(CheckpointError::InvalidReplayContract);
        }
        self.replay = replay;
        Ok(self)
    }

    /// Return whether the next complete batch fits the supplied budget.
    #[must_use]
    pub fn next_batch_allowed(&self, budget: &ExecutionBudget, batch_size: u64) -> bool {
        self.evaluations.checked_add(batch_size).is_some() && budget.try_reserve(batch_size)
    }

    /// Reject resume when model, RNG, or algorithm identity changed.
    ///
    /// # Errors
    ///
    /// Returns [`CheckpointError::IdentityMismatch`] when the identities differ.
    pub fn ensure_compatible(&self, identity: &CheckpointIdentity) -> Result<(), CheckpointError> {
        if &self.identity == identity {
            Ok(())
        } else {
            Err(CheckpointError::IdentityMismatch)
        }
    }
}

/// A file-backed checkpoint store that replaces a checkpoint atomically.
#[derive(Clone, Debug)]
pub struct CheckpointStore {
    path: PathBuf,
}

impl CheckpointStore {
    /// Create a store for a checkpoint path.
    #[must_use]
    pub fn new(path: impl Into<PathBuf>) -> Self {
        Self { path: path.into() }
    }

    /// Persist a checkpoint through a same-directory temporary file and rename.
    ///
    /// The previous valid file remains in place if any write step fails before
    /// the final rename.
    ///
    /// # Errors
    ///
    /// Returns [`CheckpointError::PersistenceFailure`] when the file cannot be
    /// written, or [`CheckpointError::InvalidCheckpointEncoding`] when it
    /// cannot be encoded.
    pub fn save(&self, checkpoint: &ExecutionCheckpoint) -> Result<(), CheckpointError> {
        let bytes = serde_json::to_vec(checkpoint)
            .map_err(|_| CheckpointError::InvalidCheckpointEncoding)?;
        let parent = self
            .path
            .parent()
            .filter(|path| !path.as_os_str().is_empty())
            .unwrap_or_else(|| Path::new("."));
        let temporary = temporary_path(&self.path)?;
        let result = (|| {
            let mut file = OpenOptions::new()
                .create_new(true)
                .write(true)
                .open(&temporary)
                .map_err(|_| CheckpointError::PersistenceFailure)?;
            file.write_all(&bytes)
                .and_then(|()| file.sync_all())
                .map_err(|_| CheckpointError::PersistenceFailure)?;
            fs::rename(&temporary, &self.path).map_err(|_| CheckpointError::PersistenceFailure)?;
            sync_parent_directory(parent)
        })();
        if result.is_err() {
            let _ = fs::remove_file(&temporary);
        }
        result
    }

    /// Load and validate the latest complete checkpoint.
    ///
    /// # Errors
    ///
    /// Returns [`CheckpointError::PersistenceFailure`] when the file cannot
    /// be read, or [`CheckpointError::InvalidCheckpointEncoding`] when its
    /// contents are malformed or violate checkpoint invariants.
    pub fn load(&self) -> Result<ExecutionCheckpoint, CheckpointError> {
        let mut file = File::open(&self.path).map_err(|_| CheckpointError::PersistenceFailure)?;
        let mut bytes = Vec::new();
        file.read_to_end(&mut bytes)
            .map_err(|_| CheckpointError::PersistenceFailure)?;
        serde_json::from_slice(&bytes).map_err(|_| CheckpointError::InvalidCheckpointEncoding)
    }
}

static TEMPORARY_FILE_SEQUENCE: AtomicU64 = AtomicU64::new(0);

fn temporary_path(destination: &Path) -> Result<PathBuf, CheckpointError> {
    let parent = destination
        .parent()
        .filter(|path| !path.as_os_str().is_empty())
        .unwrap_or_else(|| Path::new("."));
    let name = destination
        .file_name()
        .ok_or(CheckpointError::PersistenceFailure)?;
    for _ in 0..128 {
        let sequence = TEMPORARY_FILE_SEQUENCE.fetch_add(1, Ordering::Relaxed);
        let temporary_name = format!(
            ".{}.tmp.{}.{}",
            name.to_string_lossy(),
            std::process::id(),
            sequence
        );
        let candidate = parent.join(temporary_name);
        if !candidate.exists() {
            return Ok(candidate);
        }
    }
    Err(CheckpointError::PersistenceFailure)
}

#[cfg(unix)]
fn sync_parent_directory(parent: &Path) -> Result<(), CheckpointError> {
    File::open(parent)
        .and_then(|directory| directory.sync_all())
        .map_err(|_| CheckpointError::PersistenceFailure)
}

#[cfg(not(unix))]
fn sync_parent_directory(_parent: &Path) -> Result<(), CheckpointError> {
    // Windows does not provide a portable directory-handle fsync operation.
    // The file is flushed before rename; the rename remains the commit point.
    Ok(())
}

/// Fail-closed checkpoint construction or resume error.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CheckpointError {
    /// One identity component was empty.
    EmptyIdentity,
    /// The persisted result payload has no digest.
    EmptyPayloadDigest,
    /// Resume identities do not match the checkpoint.
    IdentityMismatch,
    /// The requested lifecycle transition is not permitted.
    InvalidStateTransition,
    /// Cooperative cancellation was observed at a batch boundary.
    Cancelled,
    /// Checkpoint bytes could not be durably persisted or read.
    PersistenceFailure,
    /// Checkpoint bytes were malformed or violated serialization invariants.
    InvalidCheckpointEncoding,
    /// Replay tolerance or reduction-order metadata is invalid.
    InvalidReplayContract,
}

impl fmt::Display for CheckpointError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::EmptyIdentity => "checkpoint identity components must not be empty",
            Self::EmptyPayloadDigest => "checkpoint payload digest must not be empty",
            Self::IdentityMismatch => "checkpoint identity does not match the requested resume",
            Self::InvalidStateTransition => "execution state transition is not permitted",
            Self::Cancelled => "execution was cancelled before batch admission",
            Self::PersistenceFailure => "checkpoint persistence failed",
            Self::InvalidCheckpointEncoding => "checkpoint encoding is invalid",
            Self::InvalidReplayContract => "replay contract is invalid",
        })
    }
}

impl std::error::Error for CheckpointError {}

#[cfg(test)]
mod tests {
    use super::*;

    fn identity() -> CheckpointIdentity {
        CheckpointIdentity::new("model-v1", "seed-7", "evsi-v2").unwrap()
    }

    #[test]
    fn lifecycle_rejects_completion_after_cancellation_until_resume() {
        let mut cancelled = ExecutionState::Running;
        cancelled
            .transition(ExecutionState::Cancelled)
            .expect("cancellation is valid");
        assert!(cancelled.is_terminal());
        assert_eq!(
            cancelled.transition(ExecutionState::Complete),
            Err(CheckpointError::InvalidStateTransition)
        );
        cancelled
            .transition(ExecutionState::Running)
            .expect("cancelled work can resume");
        cancelled
            .transition(ExecutionState::Complete)
            .expect("resumed work can complete");
    }

    #[test]
    fn cancellation_is_checked_before_batch_admission() {
        let budget = ExecutionBudget::new(4);
        let token = CancellationToken::new();
        assert!(token.reserve_batch(&budget, 2).unwrap());
        assert_eq!(budget.remaining(), 2);
        token.cancel();
        assert_eq!(
            token.reserve_batch(&budget, 1),
            Err(CheckpointError::Cancelled)
        );
        assert_eq!(budget.remaining(), 2);
    }

    #[test]
    fn zero_budget_performs_no_evaluations_and_batches_are_atomic() {
        let checkpoint = ExecutionCheckpoint::new(identity(), 0, 0, "sha256:empty").unwrap();
        assert!(!checkpoint.next_batch_allowed(&ExecutionBudget::new(0), 1));
        assert!(checkpoint.next_batch_allowed(&ExecutionBudget::new(2), 2));
        assert!(!checkpoint.next_batch_allowed(&ExecutionBudget::new(2), 3));
    }

    #[test]
    fn resume_requires_all_execution_identities_to_match() {
        let checkpoint = ExecutionCheckpoint::new(identity(), 3, 30, "sha256:abc").unwrap();
        assert!(checkpoint.ensure_compatible(&identity()).is_ok());
        let changed = CheckpointIdentity::new("model-v1", "seed-8", "evsi-v2").unwrap();
        assert_eq!(
            checkpoint.ensure_compatible(&changed),
            Err(CheckpointError::IdentityMismatch)
        );
    }

    #[test]
    fn deterministic_replay_witness_is_bound_to_cpu_tolerance() {
        let replay = ReplayContract::new(1e-10, "stable_serial").unwrap();
        assert!(replay.matches(1.0, 1.0 + 5e-11));
        assert!(!replay.matches(1.0, 1.0 + 2e-10));
        assert_eq!(replay.reduction_order, "stable_serial");
        let checkpoint = ExecutionCheckpoint::new(identity(), 1, 10, "sha256:replay")
            .unwrap()
            .with_replay(replay.clone())
            .unwrap();
        let encoded = serde_json::to_string(&checkpoint).unwrap();
        let decoded: ExecutionCheckpoint = serde_json::from_str(&encoded).unwrap();
        assert_eq!(decoded.replay, replay);
        assert!(decoded.replay.matches(0.25, 0.25 + 1e-11));
    }

    #[test]
    fn replay_contract_rejects_nonfinite_or_negative_tolerances() {
        assert_eq!(
            ReplayContract::new(f64::NAN, "stable_serial"),
            Err(CheckpointError::InvalidReplayContract)
        );
        assert_eq!(
            ReplayContract::new(-1.0, "stable_serial"),
            Err(CheckpointError::InvalidReplayContract)
        );
        assert_eq!(
            ReplayContract::new(1e-12, ""),
            Err(CheckpointError::InvalidReplayContract)
        );
    }

    #[test]
    fn deserialization_revalidates_persisted_identity_and_digest() {
        let invalid = r#"{"identity":{"model_input":"","rng":"seed","algorithm":"evsi"},"completed_batches":1,"evaluations":1,"payload_digest":"sha256:x"}"#;
        assert!(serde_json::from_str::<ExecutionCheckpoint>(invalid).is_err());
        let invalid_digest = r#"{"identity":{"model_input":"model","rng":"seed","algorithm":"evsi"},"completed_batches":1,"evaluations":1,"payload_digest":""}"#;
        assert!(serde_json::from_str::<ExecutionCheckpoint>(invalid_digest).is_err());
    }

    #[test]
    fn empty_identity_and_digest_fail_closed() {
        assert_eq!(
            CheckpointIdentity::new("", "seed", "algorithm"),
            Err(CheckpointError::EmptyIdentity)
        );
        assert_eq!(
            ExecutionCheckpoint::new(identity(), 0, 0, ""),
            Err(CheckpointError::EmptyPayloadDigest)
        );
    }

    #[test]
    fn atomic_store_round_trip_preserves_checkpoint_identity() {
        let path = std::env::temp_dir().join(format!(
            "voiage-checkpoint-{}-{}.json",
            std::process::id(),
            "round-trip"
        ));
        let _ = std::fs::remove_file(&path);
        let store = CheckpointStore::new(&path);
        let checkpoint = ExecutionCheckpoint::new(identity(), 4, 40, "sha256:stable").unwrap();
        store.save(&checkpoint).unwrap();
        let loaded = store.load().unwrap();
        assert_eq!(loaded, checkpoint);
        loaded.ensure_compatible(&identity()).unwrap();
        let changed = CheckpointIdentity::new("model-v2", "seed-7", "evsi-v2").unwrap();
        assert_eq!(
            loaded.ensure_compatible(&changed),
            Err(CheckpointError::IdentityMismatch)
        );
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn stale_temporary_file_does_not_block_future_saves() {
        let path = std::env::temp_dir().join(format!(
            "voiage-checkpoint-{}-{}.json",
            std::process::id(),
            "failure"
        ));
        let temporary = path.with_extension("tmp");
        let _ = std::fs::remove_file(&path);
        let _ = std::fs::remove_file(&temporary);
        let store = CheckpointStore::new(&path);
        let checkpoint = ExecutionCheckpoint::new(identity(), 2, 20, "sha256:last-valid").unwrap();
        store.save(&checkpoint).unwrap();
        std::fs::write(&temporary, b"interrupted").unwrap();
        let replacement = ExecutionCheckpoint::new(identity(), 3, 30, "sha256:new").unwrap();
        store.save(&replacement).unwrap();
        assert_eq!(store.load().unwrap(), replacement);
        let _ = std::fs::remove_file(path);
        let _ = std::fs::remove_file(temporary);
    }

    #[test]
    fn destination_with_tmp_suffix_gets_distinct_temporary_path() {
        let path = std::env::temp_dir().join(format!(
            "voiage-checkpoint-{}-{}.tmp",
            std::process::id(),
            "suffix"
        ));
        let store = CheckpointStore::new(&path);
        let checkpoint = ExecutionCheckpoint::new(identity(), 1, 10, "sha256:suffix").unwrap();
        store.save(&checkpoint).unwrap();
        assert_eq!(store.load().unwrap(), checkpoint);
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn bare_relative_path_uses_current_directory_as_parent() {
        let path = PathBuf::from(format!(
            "voiage-checkpoint-{}-bare.json",
            std::process::id()
        ));
        let store = CheckpointStore::new(&path);
        let checkpoint = ExecutionCheckpoint::new(identity(), 1, 10, "sha256:bare").unwrap();
        store.save(&checkpoint).unwrap();
        assert_eq!(store.load().unwrap(), checkpoint);
        let _ = std::fs::remove_file(path);
    }
}
