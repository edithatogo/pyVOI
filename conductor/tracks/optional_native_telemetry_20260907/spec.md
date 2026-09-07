# Specification: Optional native telemetry qualification

## Scope and authority

Baseline: `1207cef979311d1f39b3e41c32e165907303dec2`. Follow root AGENTS.md and the parent programme repository boundaries. This track owns only the named Voiage slice; it authorizes no sibling changes or external operations.

## Required context

- `rust/Cargo.toml`
- `rust/crates/voiage-diagnostics/Cargo.toml`
- `tests/test_dependency_promotion_policy.py`

## Acceptance criteria

### AC1: Need

Use pilot measurements to select one concrete telemetry use case and acceptance budget; record defer if no need is demonstrated.

Acceptance: No exporter or dashboard is added solely for novelty; deferral is explicit and not feature completion.

### AC2: Qualify

Qualify a pinned Rust OpenTelemetry SDK/bridge/exporter combination with minimal feature and MSRV tests.

Acceptance: Signals and semantic-convention versions are recorded; base installation has no exporter requirement.

### AC3: Signal

Add one optional trace export path before metrics/log export; verify context propagation with a local test collector.

Acceptance: Correct parentage and attributes arrive; network export requires application opt-in.

### AC4: Limits

Test sampling, label-cardinality limits, bounded retries, collector outage and shutdown.

Acceptance: No run IDs or arbitrary parameter values become metric labels; unavailable collectors cannot block numerical work indefinitely.

### AC5: Consumer

Verify feature-off, feature-on and incompatible-toolchain lanes plus numerical equivalence.

Acceptance: Supported CPU baseline remains usable; unsupported combinations fail explicitly; dashboard/collector hosting stays outside this repository.

## Non-functional and external boundaries

Rust-first dependencies; no silent numerical fallback, global logging initialization, API-policy change, tolerance inflation or golden-fixture rewrite. Preserve current version synchronization and declared public compatibility. Applications own telemetry sinks and retention. No cloud account, paid runner, publication, registry submission or release is included.

## Verification

Freeze exact test commands in the first task of each phase before implementation. Existing context files above are starting points, not unrestricted write permission. Add meaningful negative tests before code; test collection of zero is failure. Final candidate uses `tox run-parallel -p 2` under AGENTS.md and affected native gates, including `cargo test --manifest-path rust/Cargo.toml --workspace --all-features --locked` for Rust changes. Required hosted checks apply to the delivered PR revision.
