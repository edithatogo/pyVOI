# Specification: Minimal Rust structured logging

## Scope and authority

Baseline: `1207cef979311d1f39b3e41c32e165907303dec2`. Follow root AGENTS.md and the parent programme repository boundaries. This track owns only the named Voiage slice; it authorizes no sibling changes or external operations.

## Required context

- `voiage/logging.py`
- `tests/test_logging_contract.py`
- `rust/crates/voiage-diagnostics/Cargo.toml`
- `rust/crates/voiage-python/Cargo.toml`

## Acceptance criteria

### AC1: Events

Freeze the minimal versioned event fields, severity policy and run/analysis/trace correlation mapping.

Acceptance: Scientific results, audit evidence and operational logs have distinct contracts; diagnostics remain available with logging disabled.

### AC2: Dependency

Qualify tracing with minimal features and the supported MSRV; record compile-time and disabled-path costs.

Acceptance: No exporter, network client or mandatory async runtime enters the numerical core.

### AC3: Ownership

Test host-installed subscriber coexistence before implementing application-owned configuration.

Acceptance: Importing/calling the library never installs a global subscriber or replaces host handlers; repeated setup does not duplicate events.

### AC4: Bridge

Implement and test one Python-to-Rust correlation path and context isolation across parallel calls.

Acceptance: Two concurrent runs do not exchange IDs; nested spans preserve parentage; absent tracing remains valid.

### AC5: Numerics

Compare logging disabled/enabled for a deterministic reference kernel and benchmark the boundary.

Acceptance: Results and deterministic hashes agree; timestamps/trace IDs never enter calculation identities; the reviewed overhead budget passes.

## Non-functional and external boundaries

Rust-first dependencies; no silent numerical fallback, global logging initialization, API-policy change, tolerance inflation or golden-fixture rewrite. Preserve current version synchronization and declared public compatibility. Applications own telemetry sinks and retention. No cloud account, paid runner, publication, registry submission or release is included.

## Verification

Freeze exact test commands in the first task of each phase before implementation. Existing context files above are starting points, not unrestricted write permission. Add meaningful negative tests before code; test collection of zero is failure. Final candidate uses `tox run-parallel -p 2` under AGENTS.md and affected native gates, including `cargo test --manifest-path rust/Cargo.toml --workspace --all-features --locked` for Rust changes. Required hosted checks apply to the delivered PR revision.
