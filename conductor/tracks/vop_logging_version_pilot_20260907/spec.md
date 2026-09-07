# Specification: VOP-to-VOI version and logging pilot

## Scope and authority

Baseline: `1207cef979311d1f39b3e41c32e165907303dec2`. Follow root AGENTS.md and the parent programme repository boundaries. This track owns only the named Voiage slice; it authorizes no sibling changes or external operations.

## Required context

- `specs/integration/vop-voiage/bundles/UPSTREAM.json`
- `tests/test_logging_contract.py`
- `tests/test_consumer_matrix.py`
- `voiage/logging.py`

## Acceptance criteria

### AC1: Pin

Select one existing VOP export contract and exact producer/consumer revisions; identify any producer change as a separate upstream handoff.

Acceptance: Existing contracts are reused; no upstream task is assumed accepted or implemented.

### AC2: Negative

Create wrong-unit, wrong-weight, unknown-version and malformed-correlation cases.

Acceptance: Invalid inputs are rejected before model evaluation with stable diagnostics.

### AC3: Consumer

Implement only the missing consumer slice and run it from an installed artifact outside the source tree.

Acceptance: The reference result, version identities and cross-boundary correlation agree on the qualified installed combination.

### AC4: Replacement

Test two small providers with deliberately different APIs against the same semantic input contract.

Acceptance: Both yield the expected VOI result without requiring third-party API/ABI equivalence.

### AC5: Replay

Reproduce the complete export-to-result workflow and publish a local redacted validation packet.

Acceptance: Packet records hashes, versions, expected results and limitations; synthetic data are labelled and no hosted publication is implied.

## Non-functional and external boundaries

Rust-first dependencies; no silent numerical fallback, global logging initialization, API-policy change, tolerance inflation or golden-fixture rewrite. Preserve current version synchronization and declared public compatibility. Applications own telemetry sinks and retention. No cloud account, paid runner, publication, registry submission or release is included.

## Verification

Freeze exact test commands in the first task of each phase before implementation. Existing context files above are starting points, not unrestricted write permission. Add meaningful negative tests before code; test collection of zero is failure. Final candidate uses `tox run-parallel -p 2` under AGENTS.md and affected native gates, including `cargo test --manifest-path rust/Cargo.toml --workspace --all-features --locked` for Rust changes. Required hosted checks apply to the delivered PR revision.
