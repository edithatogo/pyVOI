# Implementation plan: VOP-to-VOI version and logging pilot

The implementation is present in merged PR #1120 (`348db4d3e51a82b6fc6a252ef4bdabdf99db8564`). Use [START_HERE.md](./START_HERE.md) and the exact phase commands/file reservations in [implementation-packet.json](./implementation-packet.json) for acceptance review. Prerequisite: logging_privacy_resilience_20260907 is accepted in PR #1152. Follow the [orchestration plan](../agent_safe_engineering_20260907/orchestration.md). Final acceptance remains open until the full local/native gate is recorded.

## Phase 1: Pin

- [x] T1.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC1; split if scope exceeds one behavioral change.
- [x] T1.2 — Select one existing VOP export contract and exact producer/consumer revisions; identify any producer change as a separate upstream handoff. (AC1).
- [x] T1.3 — Validate: Existing contracts are reused; no upstream task is assumed accepted or implemented. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC1).

## Phase 2: Negative

- [x] T2.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC2; split if scope exceeds one behavioral change.
- [x] T2.2 — Create wrong-unit, wrong-weight, unknown-version and malformed-correlation cases. (AC2).
- [x] T2.3 — Validate: Invalid inputs are rejected before model evaluation with stable diagnostics. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC2).

## Phase 3: Consumer

- [x] T3.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC3; split if scope exceeds one behavioral change.
- [x] T3.2 — Implement only the missing consumer slice and run it from an installed artifact outside the source tree. (AC3).
- [x] T3.3 — Validate: The reference result, version identities and cross-boundary correlation agree on the qualified installed combination. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC3).

## Phase 4: Replacement

- [x] T4.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC4; split if scope exceeds one behavioral change.
- [x] T4.2 — Test two small providers with deliberately different APIs against the same semantic input contract. (AC4).
- [x] T4.3 — Validate: Both yield the expected VOI result without requiring third-party API/ABI equivalence. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC4).

## Phase 5: Replay

- [x] T5.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC5; split if scope exceeds one behavioral change.
- [x] T5.2 — Reproduce the complete export-to-result workflow and publish a local redacted validation packet. (AC5).
- [x] T5.3 — Validate: Packet records hashes, versions, expected results and limitations; synthetic data are labelled and no hosted publication is implied. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC5).

## Final acceptance

- [x] CLOSE.1 — Review every AC, run final required local/native gates and record exact source/environment evidence; reuse only eligible unchanged evidence.
- [x] CLOSE.2 — Reconcile plan, metadata, registry and append-only evidence; require satisfied upstream contracts and applicable hosted evidence before completion. Do not infer release or scientific acceptance.
