# Implementation plan: Version identities and compatibility policy

Implementation completed in PR #1117. Use [START_HERE.md](./START_HERE.md) and the exact phase commands/file reservations in [implementation-packet.json](./implementation-packet.json). Prerequisites: execution_packet_guard_20260907. Follow the [orchestration plan](../agent_safe_engineering_20260907/orchestration.md).

## Phase 1: Inventory

- [x] T1.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC1; split if scope exceeds one behavioral change.
- [x] T1.2 — Map existing package, public API, C ABI, schema, algorithm, RNG and checkpoint identities and their authoritative files. (AC1).
- [x] T1.3 — Validate: Each identity has one owner, increment rule and declared consumers; independent identities are not conflated. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC1).

## Phase 2: Policy

- [x] T2.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC2; split if scope exceeds one behavioral change.
- [x] T2.2 — Specify compatible versus breaking changes, supported read/write windows and deprecation decisions. (AC2).
- [x] T2.3 — Validate: Examples cover additive fields, changed units, renamed fields, numerical fixes and RNG changes; no silent version bump. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC2).

## Phase 3: Fixtures

- [x] T3.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC3; split if scope exceeds one behavioral change.
- [x] T3.2 — Create old-reader/new-writer and new-reader/old-writer fixtures for one existing serialized VOI contract. (AC3).
- [x] T3.3 — Validate: Supported combinations pass; unsupported major versions and missing required fields fail explicitly. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC3).

## Phase 4: Identity

- [x] T4.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC4; split if scope exceeds one behavioral change.
- [x] T4.2 — Implement the smallest version-envelope/validation change using Rust-owned semantics and thin bindings. (AC4).
- [x] T4.3 — Validate: Package synchronization still passes and provider APIs do not leak into public identities. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC4).

## Phase 5: Migration

- [x] T5.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC5; split if scope exceeds one behavioral change.
- [x] T5.2 — Test a single explicit migration and replay invalidation before enabling it. (AC5).
- [x] T5.3 — Validate: Original artifacts remain immutable; changed algorithm/RNG/input identities invalidate incompatible checkpoints; migration records both identities. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC5).

## Final acceptance

- [x] CLOSE.1 — Review every AC, run final required local/native gates and record exact source/environment evidence; reuse only eligible unchanged evidence.
- [x] CLOSE.2 — Reconcile plan, metadata, registry and append-only evidence; require satisfied upstream contracts and applicable hosted evidence before completion. Do not infer release or scientific acceptance.
