//! Durable identity and resume contracts for bounded executions.

use serde::{Deserialize, Deserializer, Serialize};
use std::fmt;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;

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
}

#[derive(Deserialize)]
struct ExecutionCheckpointWire {
    identity: CheckpointIdentity,
    completed_batches: u64,
    evaluations: u64,
    payload_digest: String,
}

impl<'de> Deserialize<'de> for ExecutionCheckpoint {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let wire = ExecutionCheckpointWire::deserialize(deserializer)?;
        Self::new(
            wire.identity,
            wire.completed_batches,
            wire.evaluations,
            wire.payload_digest,
        )
        .map_err(serde::de::Error::custom)
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
        })
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

/// Fail-closed checkpoint construction or resume error.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CheckpointError {
    /// One identity component was empty.
    EmptyIdentity,
    /// The persisted result payload has no digest.
    EmptyPayloadDigest,
    /// Resume identities do not match the checkpoint.
    IdentityMismatch,
}

impl fmt::Display for CheckpointError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::EmptyIdentity => "checkpoint identity components must not be empty",
            Self::EmptyPayloadDigest => "checkpoint payload digest must not be empty",
            Self::IdentityMismatch => "checkpoint identity does not match the requested resume",
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
}
