# Specification: Version identities and compatibility policy

## Scope and authority

Baseline: `1207cef979311d1f39b3e41c32e165907303dec2`. Follow root AGENTS.md and the parent programme repository boundaries. This track owns only the named Voiage slice; it authorizes no sibling changes or external operations.

## Required context

- `voiage/versioning.py`
- `scripts/validate_version_sync.py`
- `tests/test_version_sync.py`
- `rust/Cargo.toml`

## Acceptance criteria

### AC1: Inventory

Map existing package, public API, C ABI, schema, algorithm, RNG and checkpoint identities and their authoritative files.

Acceptance: Each identity has one owner, increment rule and declared consumers; independent identities are not conflated.

### AC2: Policy

Specify compatible versus breaking changes, supported read/write windows and deprecation decisions.

Acceptance: Examples cover additive fields, changed units, renamed fields, numerical fixes and RNG changes; no silent version bump.

### AC3: Fixtures

Create old-reader/new-writer and new-reader/old-writer fixtures for one existing serialized VOI contract.

Acceptance: Supported combinations pass; unsupported major versions and missing required fields fail explicitly.

### AC4: Identity

Implement the smallest version-envelope/validation change using Rust-owned semantics and thin bindings.

Acceptance: Package synchronization still passes and provider APIs do not leak into public identities.

### AC5: Migration

Test a single explicit migration and replay invalidation before enabling it.

Acceptance: Original artifacts remain immutable; changed algorithm/RNG/input identities invalidate incompatible checkpoints; migration records both identities.

## Non-functional and external boundaries

Rust-first dependencies; no silent numerical fallback, global logging initialization, API-policy change, tolerance inflation or golden-fixture rewrite. Preserve current version synchronization and declared public compatibility. Applications own telemetry sinks and retention. No cloud account, paid runner, publication, registry submission or release is included.

## Verification

Freeze exact test commands in the first task of each phase before implementation. Existing context files above are starting points, not unrestricted write permission. Add meaningful negative tests before code; test collection of zero is failure. Final candidate uses `tox run-parallel -p 2` under AGENTS.md and affected native gates, including `cargo test --manifest-path rust/Cargo.toml --workspace --all-features --locked` for Rust changes. Required hosted checks apply to the delivered PR revision.
