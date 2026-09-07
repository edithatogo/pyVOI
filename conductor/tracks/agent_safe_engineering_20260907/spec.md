# Specification

## Authority and scope

Baseline: `1207cef979311d1f39b3e41c32e165907303dec2`. Read AGENTS.md, active workflows, tests and the integrated roadmap at `docs/reviews/roadmaps/voi-methods-expansion.md`. Executable contracts take precedence over historical descriptions. Existing backlog and venue tracks retain their owners and external gates.

This track adds engineering acceptance criteria to the earlier V01–V12/F01–F08 roadmap. It does not authorize implementing all twenty method packages. G01 is the prerequisite for machine-enforced packet readiness; until it lands, an integrator performs the same checks explicitly. No claim of automated enforcement is made now.

## Repository ownership and successor policy

[Repository boundaries](./repository-boundaries.md) is normative for this track.
Each slice stays in one repository. The earlier twenty packages are allocated
between VOI responsibilities and external capability owners. Producer integrations
require semantic/interchange conformance, not default third-party API/ABI parity.
Existing Voiage promises retain their explicit compatibility requirements.

## Acceptance criteria

### G01: Execution packets and drift enforcement

First inspect conductor-next for reusable generic enforcement; keep a Voiage
policy/profile here and propose missing generic functionality upstream. Build a
bounded read-only packet validator that rejects missing prerequisites, unknown task IDs, dependency cycles, unsafe paths, stale input hashes, unsupported evidence states and writes outside the selected task scope. Hook it into the existing harness only after negative tests pass.

**G01-AC:** Mutate one valid packet at a time: cycle, ../ traversal, symlink escape, missing prerequisite evidence, changed baseline hash, unknown field, and out-of-scope changed file must each exit nonzero; a valid read-only audit exits zero. Include staged, unstaged and untracked paths. A packet never grants shell or publication permission.

Boundary: A local scope checker can detect drift but cannot prove scientific correctness or sandbox an agent.

### G02: Rust dependency and feature qualification

Inventory default, no-default, each supported feature and documented combinations per crate and target; qualify MSRV separately from latest Rust tooling. Record dependency size, compile time, native/non-native transitive boundaries and exact exclusions. Extend existing checks without silently raising Rust 1.85.

**G02-AC:** A deliberately unavailable optional backend must leave the minimal supported build usable; an MSRV-incompatible candidate must fail its qualification lane. The matrix must name unsupported combinations and verify locked resolution. Native alternatives precede any non-Rust dependency proposal.

Boundary: Registry freshness is not compatibility. Tooling MSRV and library MSRV are distinct; no preview promotion from one passing platform.

### G03: Voiage compatibility and replaceable providers

Apply compatibility checks to Voiage's own promised surfaces, not all external
providers. Qualify cargo-semver-checks against an explicit release revision and supported feature/target matrix. Keep compiled C ABI and installed Python/R/Julia witnesses because Rust API checks do not establish foreign ABI or wire compatibility.

**G03-AC:** Removing a public Rust item fails the API check; changing an exported C signature fails a compiled consumer; additive compatible API passes. Pin baseline/toolchain and retain a bounded documented suppression only with a regression witness. Do not regenerate old fixtures from the candidate. Two toy providers with
different APIs must translate to the same semantic contract and reference VOI
result; wrong units or weights must be rejected.

Boundary: A new release/version decision and deliberate breaking change require maintainer disposition, not automatic version bumping.

### G04: CI cost and failure reproducibility

Measure durations and overlapping inventories first. Propose shared immutable build/coverage artifacts only when source, interpreter, lock, features and coverage settings match. Add nextest resource groups and replay evaluation to the existing preview lane. Keep required job names and fail-closed aggregate results.

**G04-AC:** Artifact from another source head, lock or interpreter is rejected. Failed subprocess, cancelled shard and missing coverage artifact cannot produce green aggregation. Cold/warm timing and exact test counts establish any claimed saving; retries retain first failure and flaky status.

Boundary: Do not weaken required checks, coverage thresholds or security controls to reduce duration. Hosted ruleset changes are separate from workflow implementation.

### G05: Numerical adversarial assurance

Select one missing numerical family per PR. Add independent analytic or high-precision reference cases, extreme scales, ties, non-finite inputs and weighted/dependent samples where supported. Persist minimized fuzz failures and test unsafe ownership paths with the existing tools.

**G05-AC:** For risk-neutral EVPI, a constant added to every action for each sample leaves EVPI unchanged; a positive utility scaling scales EVPI. Analytic references and declared floating-point tolerances test accuracy. Error estimates, RNG changes and unstable reductions must not be hidden by clamping or tolerance inflation.

Boundary: Properties are conditional on the estimand and assumptions. A shared implementation on both sides is not an independent oracle.

### G06: Bounded jobs and recoverable computation

Keep general time/event simulation in Kairos; design a VOI-job-specific
Rust-owned execution state machine with evaluation/memory budgets, cooperative cancellation and distinct complete/partial/failed states. Define resume identity and checkpoint atomicity before adding one bounded kernel integration; thin bindings translate states without numerical policy.

**G06-AC:** Budget zero performs zero model evaluations; cancellation at a defined batch boundary cannot yield a complete result. Interrupted write retains the last valid checkpoint. Resume rejects changed model/input/RNG/algorithm identities. Deterministic replay matches the declared CPU tolerance.

Boundary: No hard memory guarantee for external callbacks; report cooperative limits honestly. Structural contracts require integrator review before broad kernel edits.

### G07: Capability discovery and reproducible user reports

Specify a stable JSON capability/diagnostic report including installed backend, supported estimator/shape, error code, algorithm identity and provenance. Reuse existing registries and add a CLI dry-run/validation path after checking existing command behavior. Include a small complete source-to-report example and accessible plots.

**G07-AC:** Missing optional module, unsupported method/shape and stale schema return structured actionable errors. Dry run performs no model evaluation. Installed-wheel report agrees with actual dispatch. Default reports omit paths, credentials and patient-level data; explicit inclusion is documented.

Boundary: A diagnostic report is not an attestation of scientific suitability; retain experimental labels and avoid silently downloading models.

### G08: Automation and release evidence lifecycle

Inventory automation owners/triggers/secrets/retention and stale exceptions. Design dependency-group canaries with minimal and installed-consumer checks, expiring advisory dispositions, and verification of artifact provenance before reuse. Rehearse a failed partial polyglot release locally with immutable artifacts and idempotent recovery.

**G08-AC:** Wrong artifact digest or signer identity, expired exception, missing platform receipt and partially published release remain distinct failed/pending states. Canaries do not automatically promote scientific features or mutate historical release bytes. A replay cannot publish a different artifact under an existing version.

Boundary: No release, registry submission, credentials change or paid runner is authorized by these planning records. Publishing remains a separate accountable action.

## Non-functional requirements

Rust owns stable numerics and execution semantics. Prefer Rust dependencies and existing tools; justify every non-Rust runtime addition. Stable CPU behavior, bounded resources, portable artifacts and installed-consumer compatibility are required. No blanket refactors, automatic baseline regeneration, expanded tolerance, reduced tests or security exceptions to get green checks.

## Out of scope and external boundaries

No runtime features are implemented by initializing this track. No GitHub issues, release, submissions, paid infrastructure, research acceptance or publication are created. No existing unfinished track is closed or silently superseded. A maintainer resolves scientific assumptions and public compatibility decisions before a worker writes dependent code.

## Detailed logging/versioning execution authority

The six tracks linked in [orchestration.md](./orchestration.md) own the transferred
execution-guard, versioning, logging, privacy, pilot and optional-telemetry slices.
Parent acceptance criteria remain requirements; implementation is recorded only
in the owning child track. No duplicate implementation is authorized.
