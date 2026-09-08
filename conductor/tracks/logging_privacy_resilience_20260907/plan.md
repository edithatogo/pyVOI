# Implementation plan: Logging privacy and bounded delivery

Implementation exists in merged PR #1119. The native structured logging prerequisite is accepted in merged PR #1148 (a7fe6304), and the exact current-main local/native gates are recorded below. This closeout candidate still requires its own hosted checks and merge. Use [START_HERE.md](./START_HERE.md) and the exact phase commands/file reservations in [implementation-packet.json](./implementation-packet.json). Prerequisite native_structured_logging_20260907 is accepted in merged PR #1148; PR #1139 remains historical implementation evidence. Follow the [orchestration plan](../agent_safe_engineering_20260907/orchestration.md).

## Phase 1: Privacy

- [x] T1.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC1; split if scope exceeds one behavioral change.
- [x] T1.2 — Define event field allowlists and deployment-owned retention/redaction policy. (AC1).
- [x] T1.3 — Validate: Raw patient records, parameter draws, credentials and sensitive filesystem paths are excluded by default; no universal retention period is invented. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC1).

## Phase 2: Adversarial

- [x] T2.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC2; split if scope exceeds one behavioral change.
- [x] T2.2 — Write nested secret, exception, object-formatting, Unicode and forged-correlation tests before extending sanitization. (AC2).
- [x] T2.3 — Validate: All secret sentinels are absent from emitted records; untrusted fields cannot impersonate trusted correlation fields. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC2).

## Phase 3: Queue

- [x] T3.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC3; split if scope exceeds one behavioral change.
- [x] T3.2 — Specify bounded queue capacity, severity-aware drop behavior and low-cardinality loss counters before implementing an optional queue. (AC3).
- [x] T3.3 — Validate: A full queue has deterministic bounded behavior; numerical execution does not wait indefinitely; audit evidence is never silently dropped through this queue. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC3).

## Phase 4: Failure

- [x] T4.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC4; split if scope exceeds one behavioral change.
- [x] T4.2 — Inject disk-full, failed writer, recursive logging and stalled sink behavior. (AC4).
- [x] T4.3 — Validate: Logging failures do not mask the original calculation error or deadlock computation; loss is observable without recursive failure. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC4).

## Phase 5: Shutdown

- [x] T5.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC5; split if scope exceeds one behavioral change.
- [x] T5.2 — Test cancellation, flush timeout and process shutdown ownership. (AC5).
- [x] T5.3 — Validate: Applications control shutdown; bounded flushing reports incomplete delivery; hosts are not terminated and retention stays deployment-owned. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC5).

## Final acceptance

- [x] CLOSE.1 — Review every AC, run final required local/native gates and record exact source/environment evidence; reuse only eligible unchanged evidence.
  - Source-bound prerequisite evidence: native structured logging merged PR #1148 (`a7fe6304`).
  - Privacy implementation evidence: merged PR #1119 (`3e33feaf`).
  - Focused closeout validation: 45 tests passed under tox-managed Python 3.14; exact command and environment are recorded in `evidence.jsonl`.
  - Candidate-tree full gate passed on `741388ac46f0421e886422c573dea2f119e773fe` (tree `c72c117673549541c5d3cd55438b9cd53d200682`): all 15 tox environments passed; log digest is recorded in `evidence.jsonl`.
  - Hosted checks and merge for this closeout PR remain pending.
- [x] CLOSE.2 — Reconcile plan, metadata, registry and append-only evidence; require satisfied upstream contracts and applicable hosted evidence before completion. Do not infer release or scientific acceptance.
  - Registry normalization and baseline validation are included in the candidate validation; hosted acceptance remains an explicit final boundary.
