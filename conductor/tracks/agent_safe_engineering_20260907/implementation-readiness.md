# Active-track implementation readiness

Preparation date: 2026-09-07. All nine active tracks have an entry handoff.
Prepared means a worker can execute the next eligible step without choosing its
scope from scratch. It does not mean prerequisites or external gates passed.
Implementation checkboxes remain unchanged.

| Track | Start state | First action |
| --- | --- | --- |
| execution_packet_guard_20260907 | Ready for bounded preflight | START_HERE.md, T1.1 ownership/profile witness |
| version_identity_contracts_20260907 | Completed in PR #1117 | Downstream native logging may consume the accepted identity contract |
| native_structured_logging_20260907 | Waiting for version contracts | Prepare event/correlation inventory; then T1.1 |
| logging_privacy_resilience_20260907 | Waiting for native event contract | Prepare adversarial cases without shared-file edits |
| vop_logging_version_pilot_20260907 | Waiting for logging/privacy acceptance | Inspect existing producer export and pin candidates |
| optional_native_telemetry_20260907 | Waiting for pilot and demonstrated need | Read-only dependency/use-case evaluation only |
| agent_safe_engineering_20260907 | Parent coordination; residual G02–G08 design packets | START_HERE.md; never duplicate delegated child slices |
| remaining_backlog_delivery_20260831 | Evidence reconciliation first | implementation-handoff.md; resolve closed #1053 versus incomplete plan |
| v2_2_release_and_venue_submissions_20260830 | External R14 prerequisites | implementation-handoff.md; retain survey/text and editorial gates |

## Planning defaults workers may rely on

- Package release authority remains Cargo; wire, event, algorithm, RNG and
  checkpoint identities are separate explicit fields, not derived implicitly
  from the package number. Existing synchronization policy is preserved.
- Version evolution starts with one existing contract. Preserve immutable old
  fixtures. Reject unknown incompatible major versions. Do not silently infer
  currencies, weights, units, RNG or algorithm defaults during migration.
- Native instrumentation uses application-owned subscribers and optional
  structured events. Never initialize global logging on import/library entry.
- No exporter/network runtime enters the minimal numerical dependency graph.
  Disabled logging must preserve results and deterministic hashes.
- Redaction occurs before sink serialization; allowlisted event attributes are
  the default. Retention and sink credentials belong to the application.
- Queue and overhead limits require a measured, recorded numeric budget before
  implementation. Do not pretend an arbitrary unmeasured threshold is accepted.
- Scientific result diagnostics and durable audit records are not sampled logs.
- Every new Rust provider may have its own API; adapters uphold only named
  interchange/semantic contracts and Voiage's existing public promises.

## Orchestration and handoff

Use orchestration.md for the dependency chain and ownership rules. The six
child implementation-packet.json files reserve exact implementation paths,
record existing input hashes, identify proposed new files and enumerate phase
commands/expected results. Check hashes after rebasing; regenerate a packet
only after reviewing the changed inputs. A hash match establishes input identity,
not scientific approval or test success.

The parent G packages deliberately start with design/measurement artifacts.
Algorithm choices, dependency qualification and numerical thresholds are actual
work items; they cannot be manufactured during planning. Until those steps pass,
a weaker worker is restricted to the explicitly bounded preflight artifact.

One clean worktree per worker, two implementation workers maximum initially,
one integration pilot, and one integrator for shared files. No parallel edits
to the same source, lock, schema or workflow. Merge prerequisites first and
revalidate dependent source hashes. Missing native runners or human artifacts
block only their tracks; independent preflight can continue.

The planning changes remain local until delivered through the repository PR
workflow. Latest observed main is b58a43ca (a PostCSS update after baseline
1207cef9). Before implementation, integrate the accepted planning revision with
current main and rerun the affected checks. Do not overwrite the original dirty
checkout or assume this worktree is main.
