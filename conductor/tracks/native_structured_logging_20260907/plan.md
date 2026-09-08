# Implementation plan: Minimal Rust structured logging

Implementation and verification are complete. Use [START_HERE.md](./START_HERE.md) and the exact phase commands/file reservations in [implementation-packet.json](./implementation-packet.json). Prerequisites: version_identity_contracts_20260907. Follow the [orchestration plan](../agent_safe_engineering_20260907/orchestration.md).

## Phase 1: Events

Status: complete.

- [ ] T1.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC1; split if scope exceeds one behavioral change.
- [ ] T1.2 — Freeze the minimal versioned event fields, severity policy and run/analysis/trace correlation mapping. (AC1).
- [ ] T1.3 — Validate: Scientific results, audit evidence and operational logs have distinct contracts; diagnostics remain available with logging disabled. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC1).

## Phase 2: Dependency

Status: complete.

- [ ] T2.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC2; split if scope exceeds one behavioral change.
- [ ] T2.2 — Qualify tracing with minimal features and the supported MSRV; record compile-time and disabled-path costs. (AC2).
- [ ] T2.3 — Validate: No exporter, network client or mandatory async runtime enters the numerical core. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC2).

## Phase 3: Ownership

Status: complete.

- [ ] T3.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC3; split if scope exceeds one behavioral change.
- [ ] T3.2 — Test host-installed subscriber coexistence before implementing application-owned configuration. (AC3).
- [ ] T3.3 — Validate: Importing/calling the library never installs a global subscriber or replaces host handlers; repeated setup does not duplicate events. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC3).

## Phase 4: Bridge

Status: complete.

- [ ] T4.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC4; split if scope exceeds one behavioral change.
- [ ] T4.2 — Implement and test one Python-to-Rust correlation path and context isolation across parallel calls. (AC4).
- [ ] T4.3 — Validate: Two concurrent runs do not exchange IDs; nested spans preserve parentage; absent tracing remains valid. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC4).

## Phase 5: Numerics

Status: pending.

- [ ] T5.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC5; split if scope exceeds one behavioral change.
- [ ] T5.2 — Compare logging disabled/enabled for a deterministic reference kernel and benchmark the boundary. (AC5).
- [ ] T5.3 — Validate: Results and deterministic hashes agree; timestamps/trace IDs never enter calculation identities; the reviewed overhead budget passes. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC5).

## Final acceptance

- [ ] CLOSE.1 — Review every AC, run final required local/native gates and record exact source/environment evidence; reuse only eligible unchanged evidence.
- [ ] CLOSE.2 — Reconcile plan, metadata, registry and append-only evidence; require satisfied upstream contracts and applicable hosted evidence before completion. Do not infer release or scientific acceptance.
