# Implementation plan: Execution packet readiness and drift controls

Implementation is merged; final local acceptance reconciliation remains pending. Use [START_HERE.md](./START_HERE.md) and the exact phase commands/file reservations in [implementation-packet.json](./implementation-packet.json). Prerequisites: none. Follow the [orchestration plan](../agent_safe_engineering_20260907/orchestration.md).

## Phase 1: Ownership

- [x] T1.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC1; split if scope exceeds one behavioral change.
- [x] T1.2 — Confirm capability allocation and conductor-next reuse; freeze the local policy/profile and exact file allowlist. (AC1).
- [x] T1.3 — Validate: A generic agent engine is not introduced into Voiage; every task has one repository and owner. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC1).

## Phase 2: Schema

- [x] T2.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC2; split if scope exceeds one behavioral change.
- [x] T2.2 — Write negative tests for missing fields, unknown task IDs, duplicate IDs and dependency cycles before implementing packet validation. (AC2).
- [x] T2.3 — Validate: Invalid packets exit nonzero; the valid fixture passes; no shell command is executed by validation. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC2).

## Phase 3: Scope

- [x] T3.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC3; split if scope exceeds one behavioral change.
- [x] T3.2 — Test absolute paths, traversal, symlink escape and staged/unstaged/untracked out-of-scope changes before adding path checks. (AC3).
- [x] T3.3 — Validate: Each escape is rejected without changing any file. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC3).

## Phase 4: Readiness

- [x] T4.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC4; split if scope exceeds one behavioral change.
- [x] T4.2 — Test stale baseline hashes, missing prerequisite evidence and unsupported result states before adding readiness checks. (AC4).
- [x] T4.3 — Validate: A pending or failed prerequisite cannot authorize implementation. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC4).

## Phase 5: Harness

- [x] T5.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC5; split if scope exceeds one behavioral change.
- [x] T5.2 — Integrate the bounded checker into the existing harness and test a realistic worker handoff. (AC5).
- [x] T5.3 — Validate: An intentionally drifted handoff fails; a valid handoff retains its source and environment identity. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC5).

## Final acceptance

- [x] CLOSE.1 — Review every AC, run final required local/native gates and record exact source/environment evidence; reuse only eligible unchanged evidence.
- [x] CLOSE.2 — Reconcile plan, metadata, registry and append-only evidence; require satisfied upstream contracts and applicable hosted evidence before completion. Do not infer release or scientific acceptance.


Closeout note: T1.1–T5.3 are evidenced by merged PRs #1109 and #1129 and the focused 25-test local run recorded in evidence.jsonl. CLOSE.1 and CLOSE.2 are accepted against the exact source-bound local/native and hosted evidence recorded in the final evidence record. This acceptance does not infer release or scientific acceptance.
