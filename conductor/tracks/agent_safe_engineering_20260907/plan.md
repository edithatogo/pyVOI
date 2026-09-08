# Plan: Agent-safe engineering improvements

G01 is complete from the accepted execution-packet child track; G02-G08 remain pending. Repository allocation precedes implementation;
[repository-boundaries.md](./repository-boundaries.md) orders the separate
integration pilots and defines the external capabilities excluded from this repo. Follow [worker-guide.md](./worker-guide.md). A package is not an atomic implementation task: finish its bounded design packet before implementation.

## G01: Execution packets and drift enforcement

Implementation authority is delegated to [execution_packet_guard](../execution_packet_guard_20260907/index.md).
The following parent tasks are tracking summaries only; do not execute duplicate work.

Prerequisites: none; planning preflight is ready.

- [x] G01.1 — Confirm repository allocations and exclusions in repository-boundaries.md, inspect conductor-next reuse, and freeze the Voiage-specific validator profile; read the packet inputs; verify the observed gap against HEAD, identify one bounded change and freeze the exact files, baseline hashes, acceptance fixture and toolchain. Record existing behavior and intended failure (G01-AC).
- [x] G01.2 — Write and run the negative/analytic witness first; implement the frozen slice only after prerequisites and integrator review are recorded. Run `python -m pytest tests/test_execution_packets.py tests/test_repo_harness.py -q` plus affected checks (G01-AC).
- [x] G01.3 — Review the diff against the packet; run required final gates, bind evidence to source and environment, and update plan/metadata only for proven completion (G01-AC).

## G02: Rust dependency and feature qualification

Prerequisites: G01. The bounded qualification matrix is frozen in [dependency-feature-matrix.json](./dependency-feature-matrix.json); runtime/dependency promotion remains pending.

- [x] G02.1 — Read the packet inputs; verify the observed gap against HEAD, identify one bounded change and freeze the exact files, baseline hashes, acceptance fixture and toolchain. Record existing behavior and intended failure (G02-AC).
- [x] G02.2 — Write and run the negative/analytic witness first; implement the frozen slice only after prerequisites and integrator review are recorded. Run `python -m pytest tests/test_dependency_promotion_policy.py tests/test_dependency_frontier_script.py -q` plus affected checks (G02-AC).
- [x] G02.3 — Review the diff against the packet; run required final gates, bind evidence to source and environment, and update plan/metadata only for proven completion (G02-AC).

## G03: Voiage compatibility and replaceable providers

Version identity/evolution implementation follows [version_identity_contracts](../version_identity_contracts_20260907/index.md).
Use [orchestration.md](./orchestration.md) to exclude transferred logging/pilot work from G06–G08.

Prerequisites: G01.

- [ ] G03.1 — Read the packet inputs; verify the observed gap against HEAD, identify one bounded change and freeze the exact files, baseline hashes, acceptance fixture and toolchain. Record existing behavior and intended failure (G03-AC).
- [ ] G03.2 — Write and run the negative/analytic witness first; implement the frozen slice only after prerequisites and integrator review are recorded. Run `python -m pytest tests/test_consumer_matrix.py tests/test_ffi_sanitizer_contract.py -q` plus affected checks (G03-AC).
- [ ] G03.3 — Review the diff against the packet; run required final gates, bind evidence to source and environment, and update plan/metadata only for proven completion (G03-AC).

## G04: CI cost and failure reproducibility

Prerequisites: G01.

- [ ] G04.1 — Read the packet inputs; verify the observed gap against HEAD, identify one bounded change and freeze the exact files, baseline hashes, acceptance fixture and toolchain. Record existing behavior and intended failure (G04-AC).
- [ ] G04.2 — Write and run the negative/analytic witness first; implement the frozen slice only after prerequisites and integrator review are recorded. Run `python -m pytest tests/test_exact_head_workflows.py tests/test_repo_harness.py -q` plus affected checks (G04-AC).
- [ ] G04.3 — Review the diff against the packet; run required final gates, bind evidence to source and environment, and update plan/metadata only for proven completion (G04-AC).

## G05: Numerical adversarial assurance

Prerequisites: G01.

- [ ] G05.1 — Read the packet inputs; verify the observed gap against HEAD, identify one bounded change and freeze the exact files, baseline hashes, acceptance fixture and toolchain. Record existing behavior and intended failure (G05-AC).
- [ ] G05.2 — Write and run the negative/analytic witness first; implement the frozen slice only after prerequisites and integrator review are recorded. Run `cargo test --manifest-path rust/Cargo.toml --locked -p voiage-numerics` plus affected checks (G05-AC).
- [ ] G05.3 — Review the diff against the packet; run required final gates, bind evidence to source and environment, and update plan/metadata only for proven completion (G05-AC).

## G06: Bounded jobs and recoverable computation

Prerequisites: G01.

- [ ] G06.1 — Read the packet inputs; verify the observed gap against HEAD, identify one bounded change and freeze the exact files, baseline hashes, acceptance fixture and toolchain. Record existing behavior and intended failure (G06-AC).
- [ ] G06.2 — Write and run the negative/analytic witness first; implement the frozen slice only after prerequisites and integrator review are recorded. Run `cargo test --manifest-path rust/Cargo.toml --locked -p voiage-domain -p voiage-diagnostics -p voiage-numerics` plus affected checks (G06-AC).
- [ ] G06.3 — Review the diff against the packet; run required final gates, bind evidence to source and environment, and update plan/metadata only for proven completion (G06-AC).

## G07: Capability discovery and reproducible user reports

Prerequisites: G01, G03.

- [ ] G07.1 — Use the ordered integration pilots in repository-boundaries.md to select at most one producer contract; read the packet inputs; verify the observed gap against HEAD, identify one bounded change and freeze the exact files, baseline hashes, acceptance fixture and toolchain. Record existing behavior and intended failure (G07-AC).
- [ ] G07.2 — Write and run the negative/analytic witness first; implement the frozen slice only after prerequisites and integrator review are recorded. Run `python -m pytest tests/test_consumer_matrix.py tests/test_astro_docs_contract.py -q` plus affected checks (G07-AC).
- [ ] G07.3 — Review the diff against the packet; run required final gates, bind evidence to source and environment, and update plan/metadata only for proven completion (G07-AC).

## G08: Automation and release evidence lifecycle

Prerequisites: G01, G02, G04.

- [ ] G08.1 — Read the packet inputs; verify the observed gap against HEAD, identify one bounded change and freeze the exact files, baseline hashes, acceptance fixture and toolchain. Record existing behavior and intended failure (G08-AC).
- [ ] G08.2 — Write and run the negative/analytic witness first; implement the frozen slice only after prerequisites and integrator review are recorded. Run `python -m pytest tests/test_dependency_delivery_controls.py tests/test_python_release_workflow.py tests/test_rust_release_workflow.py -q` plus affected checks (G08-AC).
- [ ] G08.3 — Review the diff against the packet; run required final gates, bind evidence to source and environment, and update plan/metadata only for proven completion (G08-AC).
