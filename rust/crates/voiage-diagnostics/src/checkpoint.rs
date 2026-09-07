//! Durable identity and resume contracts for bounded executions.

use serde::{Deserialize, Serialize};
use std::fmt;

/// Immutable identities that must match before a checkpoint can be resumed.
#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct CheckpointIdentity {
    /// Identity of the model and its input data.
    pub model_input: String,
    /// Identity of the random-number stream or deterministic seed.
    pub rng: String,
    /// Identity of the algorithm and its configuration.
    pub algorithm: String,
}

impl CheckpointIdentity {
    /// Construct an identity, rejecting empty components.
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

/// A serializable, last-valid checkpoint at a batch boundary.
#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
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

impl ExecutionCheckpoint {
    /// Construct a checkpoint with a non-empty payload digest.
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

    /// Reject resume when model, RNG, or algorithm identity changed.
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
