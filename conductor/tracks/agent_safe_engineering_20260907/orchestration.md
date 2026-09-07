# Logging and versioning delivery orchestration

All six tracks are new and unimplemented. The owner requested planning, not
automatic execution of this queue. Root AGENTS.md governs actual implementation
and verification. Existing active backlog/venue tracks retain their ownership.

## Canonical sequence

| Order | Track | Prerequisite | Owns |
| --- | --- | --- | --- |
| 1 | [Execution guard](../execution_packet_guard_20260907/index.md) | Ownership preflight | Voiage packet profile and bounded drift checks |
| 2 | [Version identities](../version_identity_contracts_20260907/index.md) | Execution guard accepted | Version policy, compatibility matrix and one migration |
| 3 | [Native logging](../native_structured_logging_20260907/index.md) | Version identities accepted | Minimal Rust events and host-owned correlation |
| 4 | [Privacy and resilience](../logging_privacy_resilience_20260907/index.md) | Native logging accepted | Privacy tests, bounded delivery and failure behavior |
| 5 | [VOP pilot](../vop_logging_version_pilot_20260907/index.md) | Privacy and resilience accepted | One installed producer-to-consumer workflow |
| 6 | [Optional telemetry](../optional_native_telemetry_20260907/index.md) | Pilot accepted and need demonstrated | One optional native exporter qualification |

Acceptance requires recorded upstream AC results, exact source revision and
contract hashes, not just an archived directory or completed checkbox. If no
telemetry need is demonstrated, record deferred status separately; do not mark
an unimplemented exporter complete. No dashboard or collector service is built
inside Voiage.

## Parallel investigations and integration barriers

Before implementation, source inventory, privacy adversarial-case design and
producer-export inspection may proceed in parallel in read-only mode. After
the version contract freezes, native logging implementation may run alongside
privacy-test preparation in separate worktrees. Privacy implementation waits
for the accepted event contract. The pilot may prepare fixtures early, but
installed-consumer qualification waits for accepted logging/privacy behavior.
Exporter research is independent; exporter implementation is last.

Maximum initial work in progress: two implementation workers plus one
integrator; only one integration pilot. The integrator serializes all edits to
Cargo/uv lockfiles, shared schemas, version manifests, root governance files
and required CI names. Logging and privacy workers both target voiage/logging.py
and native diagnostics; they must not edit those files simultaneously.
Every task reserves exact paths before changing code. Separate worktrees and
target/tox directories are mandatory; no shared mutable caches during testing.

Merge the upstream contract first, then rebase dependent work and revalidate
its recorded hashes. A changed event/version contract reopens affected packet
readiness and tests. No bulk merge or silent acceptance of stale fixtures.
Unavailable external providers block their adapter only, not base VOI work.

## Scope transfer from the engineering programme

These tracks are authoritative for their listed slices:

- G01 execution guard implementation moves to execution_packet_guard_20260907.
  The parent keeps repository allocation and upstream reuse decisions.
- G03 version-identity/evolution details move to version_identity_contracts_20260907.
  Broader public API/ABI witness work remains G03 and must reuse these identities.
- G06 retains general VOI job/checkpoint state; logging shutdown and telemetry
  transport live in the logging tracks. No second simulation scheduler is added.
- G07 logging/correlation and the first VOP integration pilot use these tracks.
  Broader capability discovery remains G07.
- G08 retains release recovery/automation; version policy and telemetry failure
  evidence are consumed from these tracks rather than reimplemented.

Parent packet IDs remain navigation references, not parallel authorization to
implement these transferred slices. Any overlap is resolved by this ownership
map before implementation. New task files name references and anticipated tests;
workers must freeze actual commands and exact files before code, as required
by the shared worker guide. Planning does not claim runnable new tests already exist.

## Per-phase acceptance and handoff

Each phase has three pending steps: freeze its bounded packet, implement after
an intended behavioral red test, and validate/review. The final two steps
reconcile all ACs and completion evidence. Changes requiring more than five
implementation files must be split into additional reviewed task checkboxes.
The integrator handles shared policy changes separately.

Handoffs include track/task/AC ID, repository, source SHA/tree, contract hashes,
owner, exact files, toolchain, commands, exit status, count, result digest,
unresolved risks and next eligible task. Use the configured evidence helper;
do not manufacture hash-chain records. Stop after two unresolved attempts at
the same failure; retain the reproducer and diff. Never change a fixture,
version policy, error tolerance or coverage threshold to conceal failure.
