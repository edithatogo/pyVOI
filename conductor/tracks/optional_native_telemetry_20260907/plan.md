# Implementation plan: Optional native telemetry qualification

All tasks are pending. Use [START_HERE.md](./START_HERE.md) and the exact phase commands/file reservations in [implementation-packet.json](./implementation-packet.json). Prerequisites: vop_logging_version_pilot_20260907. Follow the [orchestration plan](../agent_safe_engineering_20260907/orchestration.md).

## Phase 1: Need

- [ ] T1.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC1; split if scope exceeds one behavioral change.
- [ ] T1.2 — Use pilot measurements to select one concrete telemetry use case and acceptance budget; record defer if no need is demonstrated. (AC1).
- [ ] T1.3 — Validate: No exporter or dashboard is added solely for novelty; deferral is explicit and not feature completion. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC1).

## Phase 2: Qualify

- [ ] T2.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC2; split if scope exceeds one behavioral change.
- [ ] T2.2 — Qualify a pinned Rust OpenTelemetry SDK/bridge/exporter combination with minimal feature and MSRV tests. (AC2).
- [ ] T2.3 — Validate: Signals and semantic-convention versions are recorded; base installation has no exporter requirement. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC2).

## Phase 3: Signal

- [ ] T3.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC3; split if scope exceeds one behavioral change.
- [ ] T3.2 — Add one optional trace export path before metrics/log export; verify context propagation with a local test collector. (AC3).
- [ ] T3.3 — Validate: Correct parentage and attributes arrive; network export requires application opt-in. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC3).

## Phase 4: Limits

- [ ] T4.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC4; split if scope exceeds one behavioral change.
- [ ] T4.2 — Test sampling, label-cardinality limits, bounded retries, collector outage and shutdown. (AC4).
- [ ] T4.3 — Validate: No run IDs or arbitrary parameter values become metric labels; unavailable collectors cannot block numerical work indefinitely. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC4).

## Phase 5: Consumer

- [ ] T5.1 — Freeze exact input hashes, at most five implementation paths, expected red/green result and command for AC5; split if scope exceeds one behavioral change.
- [ ] T5.2 — Verify feature-off, feature-on and incompatible-toolchain lanes plus numerical equivalence. (AC5).
- [ ] T5.3 — Validate: Supported CPU baseline remains usable; unsupported combinations fail explicitly; dashboard/collector hosting stays outside this repository. Record source, environment, command, exit status, test count and artifact digest; review diff and stop on unresolved failure (AC5).

## Final acceptance

- [ ] CLOSE.1 — Review every AC, run final required local/native gates and record exact source/environment evidence; reuse only eligible unchanged evidence.
- [ ] CLOSE.2 — Reconcile plan, metadata, registry and append-only evidence; require satisfied upstream contracts and applicable hosted evidence before completion. Do not infer release or scientific acceptance.
