# Repository boundaries and integration order

Decision date: 2026-09-07. This refines the local planning contract following the
owner's request for focused repositories and future Rust-first replacements.
It creates no sibling repositories, tracks, issues or runtime dependencies.

## Placement rule

`voiage` owns the value of information calculation: decision/utility inputs,
VOI estimators, estimator diagnostics, VOI-specific job control, result contracts
and thin supported bindings. It consumes model outcomes and evidence; it does
not become a general simulation, statistics, data acquisition, ontology,
publication, dashboard hosting or agent-management platform.

Every implementation packet must name exactly one delivery repository, one
capability owner, one adapter owner, and explicit excluded responsibilities.
One PR changes one repository and one behavioral slice. A shared owner may
maintain multiple cohesive crates; a crate does not automatically need its own
repository. Do not create a new repository for every feature or adapter.

Use the existing owner first. Extract a component only when it has a coherent
independent purpose, demonstrated second consumer, independent release/security
needs and a named maintenance owner. If ownership is unclear, freeze a small
interface proposal and defer implementation; do not absorb the feature into
`voiage` as a shortcut. No new catch-all integration repository is proposed.

## Candidate ownership and admission

The linked [GitHub receipt](./github-integration-review.json) records source
blob identities and read ranges. README statements describe candidate scope,
not verified runtime maturity. Validate current source, license, installed
behavior and export semantics before admitting any dependency.

| Capability | Proposed or established home | Voiage boundary and first action | Admission order |
| --- | --- | --- | --- |
| VOI kernels and uncertainty decisions | `voiage` | Own the calculation and minimal input/result contract | Core first |
| General spline fitting/replay | [mars](https://github.com/edithatogo/mars) | Reuse optional surrogate artifacts; do not implement a second MARS trainer | Pilot 2 |
| Diffusion/adoption models | [innovate](https://github.com/edithatogo/innovate) | Consume adoption uncertainty with times/units; fitting remains producer-owned | After first model handoff |
| Deterministic simulation time/events/DES/ABM | [kairos](https://github.com/edithatogo/kairos) | Model outputs or optional model callback; never a second scheduler in VOI | Later native pilot |
| General game solving | Rust incubator in [new-drug-reimbursement-game](https://github.com/edithatogo/new-drug-reimbursement-game) | Application consumes VOI; general solver remains outside VOI, extraction decision stays with owner | Later application pilot |
| Game-theory semantics | [UOGTO](https://github.com/edithatogo/UOGTO) | Optional semantic identifiers, not an RDF engine inside numerical kernels | With game pilot |
| CEA/DCEA models and decision context | [vop_poc_nz](https://github.com/edithatogo/vop_poc_nz) | Extend existing `specs/integration/vop-voiage` contracts; no parallel DCEA application | Pilot 1 |
| Disease/population microsimulation | [lifecourse](https://github.com/edithatogo/lifecourse) | Producer-side PSA export; retain dependence, weights, costs and QALYs | After Pilot 1 |
| Genetic insurance policy models | [ginsim](https://github.com/edithatogo/ginsim) | Consumer/use-case benchmark only; policy equilibria remain external | Deferred application |
| Funding formulas | [mchs](https://github.com/edithatogo/mchs) | Cost/funding output with calculator/year provenance; no NWAU formulas in VOI | Deferred costing input |
| Burden evidence | [rareburden-commons](https://github.com/edithatogo/rareburden-commons) | Governed aggregate uncertainty exports; synthetic status retained | Deferred evidence pilot |
| Tariff/reimbursement evidence | [reimbursement-atlas](https://github.com/edithatogo/reimbursement-atlas) | Reviewed derived inputs; tariffs are not automatically costs or utilities | Deferred evidence pilot |
| Medicine terminology/regulatory/funding records | [global-medicines-atlas](https://github.com/edithatogo/global-medicines-atlas) | Separate governed enrichment step, not a base dependency | Deferred evidence pilot |
| Spatial/public-data provenance | [riopa-infrastructure](https://github.com/edithatogo/riopa-infrastructure) | Optional research-object references; no second spatial archive | Deferred evidence pilot |
| Generic agent packet/lease engine | [conductor-next](https://github.com/edithatogo/conductor-next) | G01 keeps VOI policy/profile here; investigate generic enforcement upstream | Preflight now |
| Estate CI/security policy | [repository-standards](https://github.com/edithatogo/repository-standards) | G04/G08 consume bounded profiles with local numerical gates | Preflight now |
| Dependency update policy | [renovate-config](https://github.com/edithatogo/renovate-config) | Already extended locally; no second dependency-update bot | Maintain existing |
| Polyglot documentation | [astro-polyglot](https://github.com/edithatogo/astro-polyglot) | Already a local gitlink; extraction/rendering stays upstream | Maintain existing |
| Citation evidence | [sourceright](https://github.com/edithatogo/sourceright) | Already a local gitlink; development/report tooling only | Maintain existing |
| Research diagrams/checklists | [standardflow](https://github.com/edithatogo/standardflow) | Optional exported report consumer; no renderer inside VOI core | Defer |

`NwauCore.jl` and `NationalWeightedActivityUnitWrapper.jl` describe themselves as
thin MCHS CLI wrappers, not independent numerical cores. Do not add both as
providers or mistake their names for separate formula authorities. Archived
source projects are historical references, not new acquisition dependencies.
Unrelated publishing, legal-corpus and application repositories are outside this
numerical integration plan. Private repository details are not copied here.

## Source findings that affect the order

- Existing `specs/ecosystem/fixtures/manifest.json` already reserves `mars`,
  `innovate` and `lifecourse`, but labels all three fixtures planned. Extend
  that ownership; do not call it installed interoperability.
- `mars/rust-runtime/Cargo.toml` describes portable replay and has unconditional
  PyO3. First qualify producer-export/replay fixtures. Do not assume Rust training
  is implemented or import a Python-linked crate into the minimal core. A future
  producer-side feature split requires its own accepted change.
- `innovate/docs/architecture_principles.md` retains Python-reference semantics
  while describing a Rust trajectory. This plan does not rewrite that producer's
  compatibility policy. A future separately designed Rust successor is allowed
  through a new adapter and declared semantic differences.
- The reimbursement game's `ecosystem.lock.toml` and README already assign
  simulation to Kairos, semantics to UOGTO, and VOI to Voiage. Retain that directed
  ownership. Its pinned Voiage revision is historical; requalify against an exact
  release/commit before making a new compatibility claim.
- Kairos lists an active pre-release project and many optional crates. Select
  the minimal qualified capability rather than importing the whole workspace.
- Atlas and RareBurden READMEs explicitly bound evidence maturity. Repository
  availability is not permission to treat estimates or sources as qualified data.

## Compatibility policy for Rust-first successors

There are four separate promises. Record which ones an integration actually makes:

1. **Scientific semantics:** estimand, units, joint uncertainty, timing, missing
   data and decision conventions. Test these with independent reference cases.
2. **Interchange:** a named version of an input/output contract. An adapter may
   translate to it without matching either library's public programming API.
3. **Public API:** required only for a deliberately supported adapter/API surface,
   including Voiage's existing public releases within its version policy.
4. **ABI:** required only for an explicitly supported binary boundary, such as
   Voiage's versioned C ABI. Rust-to-Rust crates do not imply a stable Rust ABI.

A Rust-first successor may use idiomatic types, ownership, errors and concurrency,
remove legacy concepts and expose a different API. It need not clone Python/R
classes, function names, signatures, serialization internals or binary layout.
Do not force py-earth, scikit-learn, BCEA, dampack, heemod or other third-party
API equivalence into a new core by default. A temporary compatibility facade is
optional, separately owned, versioned and removable with a migration policy.

Represent the provider behind a narrow port or versioned artifact. Do not expose
its object types in Voiage's public contract. Prefer portable data exchange for
initial integration; choose Rust traits for source-level composition only after
feature/MSRV qualification. Use C ABI only for a demonstrated binary consumer.
No universal intermediate representation or new schema framework is needed for
the first pilot; reuse the existing compatible VOI contract where sufficient.

A replacement test must use two deliberately different toy provider APIs that
produce semantically equivalent inputs; both must yield the reference VOI result
through their adapters. A provider with different weighting, units or estimand
must fail validation or report the difference explicitly. Numerical agreement is
not assumed across different methods; declare tolerances and scope in advance.
Maintain existing promised contracts until an explicit versioned migration lands.

## Ordered delivery with small repository scope

| Order | Deliverable | Owner / writes | Exit criterion |
| --- | --- | --- | --- |
| 0 | Confirm this capability map and exclusions in G01.1 | Voiage planning only | Every slice has one home and no ownership cycle |
| 1 | Refine VOI packet validator profile and upstream-tool gap | Voiage G01; upstream proposal only | No generic Conductor engine duplicated locally |
| 2 | Freeze minimal producer/result semantics and existing VOP baseline | Voiage contracts; separate producer acceptance | One reference result, wrong-unit/weight/schema cases rejected |
| 3 | Pilot 1: one VOP-to-VOI workflow | One consumer adapter PR, separate producer PR if needed | Producer export and installed VOI consumer pass exact revisions |
| 4 | Pilot 2: one MARS artifact/replay workflow | MARS owns training/replay; Voiage owns VOI use | Held-out/reference error assessed; no unconditional Python in base |
| 5 | Choose one next integration from diffusion or microsimulation | Existing producer home | Reuse the same port without widening core scope |
| 6 | Evaluate Kairos/game/evidence applications individually | Respective owner repositories | Independent maturity and rights gates satisfied |

G02–G05 engineering investigations can run alongside steps 0–2 under disjoint
file reservations. G06 owns the lifecycle of a VOI calculation, not simulation
time/events. Do not make the first integration wait for a complete generic game
runtime, distributed simulator, inference framework or public-data platform.
Initially allow one integration pilot in flight and at most two implementation
workers overall. Freeze/merge the producer's export first, then its consumer;
a second repo's PR has its own tests, authorization and source binding.
An unavailable producer blocks only its adapter, never base installation.

For every candidate record one disposition: reuse now, qualify adapter,
producer-side improvement, future Rust successor, defer, or exclude. Record
which repository implements it and who accepts handoff. These are proposed
allocations; no upstream owner has accepted a task merely because it appears here.

## Allocation of the earlier twenty packages

This allocation narrows the programme, rather than treating every roadmap item
as a feature to add to the Voiage repository.

| Packages | Voiage-owned slice | Keep outside Voiage |
| --- | --- | --- |
| V01–V02 | VOI capability census and estimator assurance | Generic research/agent governance engine |
| V03–V04 | EVSI regression, moment and importance estimators | General MARS/ML training and inference libraries |
| V05 | Study-likelihood interface and small analytic reference models | Complete clinical-trial or disease-model platform |
| V06 | ENBS/research-design objective and bounded study decision logic | General economic modelling or optimization framework |
| V07 | Multilevel/unbiased VOI estimator implementation | General-purpose distributed computation system |
| V08 | VOI semantics for supported realistic-data variants | Data cleaning, causal inference and missing-data modelling platforms |
| V09 | VOI decision objective and acquisition boundary | General Bayesian experimental-design/SBI engine; select an owner later |
| V10 | Explicitly accepted VOI variants and diagnostic contracts | Broad application catalogue, simulation or policy dashboard |
| V11 | Information value inputs/results for strategic decisions | General game solvers; use the existing game-runtime incubator |
| V12 | Voiage's own thin bindings and installed conformance | Bindings for every upstream library |
| F01 | Minimal VOI sample, unit, weight and result contracts | Universal evidence graph or ontology framework |
| F02 | Posterior sample/diagnostic consumption | MCMC, HMC, VI, SBI inference engines; owner unresolved and deferred |
| F03 | VOI objective adapter | General acquisition/optimization framework; no new repo assumed |
| F04 | VOI feature/MSRV, allocation and numerical backend qualification | Reimplementation of Arrow, tensor or GPU libraries |
| F05 | Bounded VOI calculation cancellation/checkpoints | DES/ABM scheduling, cloud/HPC platform and generic workflow engine |
| F06 | Economic outcome and uncertainty interchange | NMA/survival/costing/evidence-synthesis engines; qualify producers |
| F07 | Public-health VOI examples and input/output contracts | Disease simulation, source harvesting and data lake operations |
| F08 | Voiage producer/consumer port and minimal report | Shared docs engines, publication clients and broad integration platform |
