# Evidence and further recommendations

Review date: 2026-09-07; source baseline `1207cef9`. These are bounded findings from the inspected files, not a claim of an exhaustive absence scan.

| Package | Existing evidence and gap | Recommendation |
| --- | --- | --- |
| G01 | The existing harness checks repository conventions but does not yet enforce these task packets or dependency readiness. | Execution packets and drift enforcement |
| G02 | Cargo-deny and preview qualification already exist; all-features success alone does not establish minimal or separately enabled feature support. | Rust dependency and feature qualification |
| G03 | Installed consumer and sanitizer contracts exist; a dedicated Rust public-API comparison was not found in the inspected workflows. | API and ABI compatibility witnesses |
| G04 | CI and Operational Assurance both collect full Python coverage; nextest/sccache is already an observation lane. Duplication may be intentional and must be measured. | CI cost and failure reproducibility |
| G05 | EVPI/ENBS/sample-matrix fuzzing and Miri already run; extend their case coverage instead of adding duplicate workflows. | Numerical adversarial assurance |
| G06 | The integrated roadmap proposes restartable execution; cancellation, resource limits and partial-result semantics need explicit acceptance witnesses before implementation. | Bounded jobs and recoverable computation |
| G07 | Capability registries and consumer checks exist; user-facing discovery must reflect the installed artifact and bounded method maturity rather than narrative feature lists. | Capability discovery and reproducible user reports |
| G08 | Renovate, SBOMs and release assurance already exist. Improve evidence consumption, expiry and recovery instead of creating a second update bot. | Automation and release evidence lifecycle |

## Current primary sources

These sources establish tool capabilities, not compatibility with this repository. Qualify pinned candidates before adoption.

- [Cargo feature semantics](https://doc.rust-lang.org/cargo/reference/features.html): supports the feature-matrix investigation (G02).
- [cargo-semver-checks upstream](https://github.com/obi1kenobi/cargo-semver-checks): Rust API comparisons use explicit baselines; tool/rustdoc compatibility needs qualification (G03).
- [nextest resource groups](https://nexte.st/docs/configuration/test-groups/) and [run replay](https://nexte.st/docs/features/record-replay-rerun/): extend the existing observation lane with bounded resources and reproducible failure investigation (G04).
- [GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations): investigate verification at artifact consumption, in addition to existing generation (G08).

## Earlier roadmap handoffs

| Earlier package | This track supplies | Activation boundary |
| --- | --- | --- |
| V01, V02, F01 | G01 packet/claim discipline; G05 independent witnesses | Refine semantic and scientific contracts first |
| V03–V08, F02, F05 | G05 numerical assurance; G06 job-state contracts | Method-specific algorithm and tolerance review still required |
| V09–V11, F03, F07 | Bounded research packets and explicit unsupported states | Research feasibility does not grant stable promotion |
| V12, F08 | G03 installed-consumer compatibility; G07 discovery | Each binding/producer needs actual acceptance evidence |
| F04 | G02 feature/MSRV and G04 measured CI qualification | No dependency upgrades from registry snapshots alone |
| F06 | G05 witnesses and G07 provenance | Economic assumptions and joint evidence remain method-owned |

## Owner-library review and scope refinement

The [repository allocation](./repository-boundaries.md) refines this assessment
using live GitHub inspection. It distinguishes existing integrations, planned
fixtures, candidate producers, and deferred capabilities. It narrows G01 to a
local policy/profile, G03 to explicit compatibility promises, and G06 to VOI-job
lifecycle control. No generic engine or sibling implementation is authorized.
