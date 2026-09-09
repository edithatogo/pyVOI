# Implementation plan: Version identities and compatibility policy

Implementation is merged and accepted. The exact current-main focused/native evidence and inherited hosted gate from merged PR #1162 are recorded in append-only evidence; no full tox result from another revision is reused. Use [START_HERE.md](./START_HERE.md) and the exact phase commands/file reservations in [implementation-packet.json](./implementation-packet.json). Prerequisites: execution_packet_guard_20260907. Follow the [orchestration plan](../agent_safe_engineering_20260907/orchestration.md).

## Phase 1: Inventory

- **Legacy follow-up (not part of completed track acceptance):** T1.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC1; split if scope exceeds one behavioral change.
- **Legacy follow-up (not part of completed track acceptance):** T1.2 — Map existing package, public API, C ABI, schema, algorithm, RNG and checkpoint identities and their authoritative files. (AC1).
- **Legacy follow-up (not part of completed track acceptance):** T1.3 — Validate: Each identity has one owner, increment rule and declared consumers; independent identities are not conflated. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC1).

## Phase 2: Policy

- **Legacy follow-up (not part of completed track acceptance):** T2.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC2; split if scope exceeds one behavioral change.
- **Legacy follow-up (not part of completed track acceptance):** T2.2 — Specify compatible versus breaking changes, supported read/write windows and deprecation decisions. (AC2).
- **Legacy follow-up (not part of completed track acceptance):** T2.3 — Validate: Examples cover additive fields, changed units, renamed fields, numerical fixes and RNG changes; no silent version bump. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC2).

## Phase 3: Fixtures

- **Legacy follow-up (not part of completed track acceptance):** T3.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC3; split if scope exceeds one behavioral change.
- **Legacy follow-up (not part of completed track acceptance):** T3.2 — Create old-reader/new-writer and new-reader/old-writer fixtures for one existing serialized VOI contract. (AC3).
- **Legacy follow-up (not part of completed track acceptance):** T3.3 — Validate: Supported combinations pass; unsupported major versions and missing required fields fail explicitly. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC3).

## Phase 4: Identity

- **Legacy follow-up (not part of completed track acceptance):** T4.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC4; split if scope exceeds one behavioral change.
- **Legacy follow-up (not part of completed track acceptance):** T4.2 — Implement the smallest version-envelope/validation change using Rust-owned semantics and thin bindings. (AC4).
- **Legacy follow-up (not part of completed track acceptance):** T4.3 — Validate: Package synchronization still passes and provider APIs do not leak into public identities. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC4).

## Phase 5: Migration

- **Legacy follow-up (not part of completed track acceptance):** T5.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC5; split if scope exceeds one behavioral change.
- **Legacy follow-up (not part of completed track acceptance):** T5.2 — Test a single explicit migration and replay invalidation before enabling it. (AC5).
- **Legacy follow-up (not part of completed track acceptance):** T5.3 — Validate: Original artifacts remain immutable; changed algorithm/RNG/input identities invalidate incompatible checkpoints; migration records both identities. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC5).

## Final acceptance

- [x] CLOSE.1 — Review every AC and bind focused/native checks to merged current main; hosted PR #1162 evidence is inherited without a release or publication claim.
- [x] CLOSE.2 — Reconcile plan, metadata, packet, registry and append-only evidence with the accepted execution-packet prerequisite.

## Legacy normalization record

- **Legacy follow-up (not part of completed track acceptance):** Preserve the historical plan and registry disposition under the current Conductor schema.

## Legacy normalization record

- [x] Preserve the historical plan and registry disposition under the current Conductor schema.
