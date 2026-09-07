# Specification: Execution packet readiness and drift controls

## Scope and authority

Baseline: `1207cef979311d1f39b3e41c32e165907303dec2`. Follow root AGENTS.md and the parent programme repository boundaries. This track owns only the named Voiage slice; it authorizes no sibling changes or external operations.

## Required context

- `scripts/repo_harness.py`
- `tests/test_repo_harness.py`
- `conductor/tracks/agent_safe_engineering_20260907/packets.json`

## Acceptance criteria

### AC1: Ownership

Confirm capability allocation and conductor-next reuse; freeze the local policy/profile and exact file allowlist.

Acceptance: A generic agent engine is not introduced into Voiage; every task has one repository and owner.

### AC2: Schema

Write negative tests for missing fields, unknown task IDs, duplicate IDs and dependency cycles before implementing packet validation.

Acceptance: Invalid packets exit nonzero; the valid fixture passes; no shell command is executed by validation.

### AC3: Scope

Test absolute paths, traversal, symlink escape and staged/unstaged/untracked out-of-scope changes before adding path checks.

Acceptance: Each escape is rejected without changing any file.

### AC4: Readiness

Test stale baseline hashes, missing prerequisite evidence and unsupported result states before adding readiness checks.

Acceptance: A pending or failed prerequisite cannot authorize implementation.

### AC5: Harness

Integrate the bounded checker into the existing harness and test a realistic worker handoff.

Acceptance: An intentionally drifted handoff fails; a valid handoff retains its source and environment identity.

## Non-functional and external boundaries

Rust-first dependencies; no silent numerical fallback, global logging initialization, API-policy change, tolerance inflation or golden-fixture rewrite. Preserve current version synchronization and declared public compatibility. Applications own telemetry sinks and retention. No cloud account, paid runner, publication, registry submission or release is included.

## Verification

Freeze exact test commands in the first task of each phase before implementation. Existing context files above are starting points, not unrestricted write permission. Add meaningful negative tests before code; test collection of zero is failure. Final candidate uses `tox run-parallel -p 2` under AGENTS.md and affected native gates, including `cargo test --manifest-path rust/Cargo.toml --workspace --all-features --locked` for Rust changes. Required hosted checks apply to the delivered PR revision.
