# Specification: Logging privacy and bounded delivery

## Scope and authority

Baseline: `1207cef979311d1f39b3e41c32e165907303dec2`. Follow root AGENTS.md and the parent programme repository boundaries. This track owns only the named Voiage slice; it authorizes no sibling changes or external operations.

## Required context

- `voiage/logging.py`
- `tests/test_logging_contract.py`
- `voiage/assurance_policy.py`

## Acceptance criteria

### AC1: Privacy

Define event field allowlists and deployment-owned retention/redaction policy.

Acceptance: Raw patient records, parameter draws, credentials and sensitive filesystem paths are excluded by default; no universal retention period is invented.

### AC2: Adversarial

Write nested secret, exception, object-formatting, Unicode and forged-correlation tests before extending sanitization.

Acceptance: All secret sentinels are absent from emitted records; untrusted fields cannot impersonate trusted correlation fields.

### AC3: Queue

Specify bounded queue capacity, severity-aware drop behavior and low-cardinality loss counters before implementing an optional queue.

Acceptance: A full queue has deterministic bounded behavior; numerical execution does not wait indefinitely; audit evidence is never silently dropped through this queue.

### AC4: Failure

Inject disk-full, failed writer, recursive logging and stalled sink behavior.

Acceptance: Logging failures do not mask the original calculation error or deadlock computation; loss is observable without recursive failure.

### AC5: Shutdown

Test cancellation, flush timeout and process shutdown ownership.

Acceptance: Applications control shutdown; bounded flushing reports incomplete delivery; hosts are not terminated and retention stays deployment-owned.

## Non-functional and external boundaries

Rust-first dependencies; no silent numerical fallback, global logging initialization, API-policy change, tolerance inflation or golden-fixture rewrite. Preserve current version synchronization and declared public compatibility. Applications own telemetry sinks and retention. No cloud account, paid runner, publication, registry submission or release is included.

## Verification

Freeze exact test commands in the first task of each phase before implementation. Existing context files above are starting points, not unrestricted write permission. Add meaningful negative tests before code; test collection of zero is failure. Final candidate uses `tox run-parallel -p 2` under AGENTS.md and affected native gates, including `cargo test --manifest-path rust/Cargo.toml --workspace --all-features --locked` for Rust changes. Required hosted checks apply to the delivered PR revision.
