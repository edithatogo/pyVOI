# Single-maintainer review policy

`voiage` is maintained by one repository owner. Any repository-owned request
for independent scientific, implementation, parity, or release review is
fulfilled by a role-separated panel of advisory subagents coordinated by an
orchestrator. The panel produces structured reports, disagreement registers,
limitations, and evidence hashes; it does not provide independent human
approval or replace the maintainer's accountable decision.

The policy covers every repository-owned review gate: scientific validity,
maturity promotion, cross-language parity, hosted exact-head assurance,
release, publication/registry preparation, and GitHub issue/project closure.
The repository owner may act as accountable scientist, maintainer, and release
approver after considering the panel evidence. The owner decision must name the
candidate, scope, maturity, conditions, dissent, and downstream boundaries; it
must not be represented as independent review.
External venues, other repositories, and destination-specific controls retain their
service requirements. Those requirements are tracked as destination constraints,
not as requests for additional human participation in this repository. Only the
repository owner may make or attest to a human decision, submission, release, or
issue closure.

A gate remains pending when the panel identifies unresolved findings, the exact
candidate changes, parity is incomplete, or an external receipt is absent.


## Sampling-acquisition-harm H8 boundary

For #850/#853/#876, the current M32 requirements in `requirements.md` require
five separately authored agent-role reports: estimand/domain, estimator
assurance, cross-language API, governance/publication, and domain/ethics safety.
The reviewing agents must be distinct from the candidate author/remediator and
the separate non-deciding orchestrator. Multiple lenses written by one agent
are preparation, not a completed panel. Shared-model limitations and conflicts
must be disclosed; the panel must not be described as independent human review.

A new candidate-bound packet must retain the exact commit/tree, report and
source digests, source rights/drift/applicability assessments, all nineteen
finding dispositions and dissent, separate synthesis, and one sole-maintainer
scientific/domain/product decision. Critical/High findings cannot disappear
through a change of governance wording. An exclusion disposition must preserve
narrower non-authorizing research and distinguish excluded-runtime blockers
from accepted limitations; it does not validate a future estimator.

The previous two-human commissioning route is retained solely to validate its
historical evidence. In `voiage/sampling_harm_human_commissioning.py`,
`PREFLIGHT_PATH` and `DECISION_PATH` select the dated 20260803 artifacts;
`validate_sampling_harm_human_commissioning` enforces nineteen pending findings,
unassigned reviewers and false authority flags, then returns `ready=False`.
`load_and_validate_sampling_harm_candidate_decision` calls that historical loader
and validates only the old option-selection receipt, also returning `ready=False`.
The direct callers are these historical loaders and
`tests/test_sampling_harm_human_commissioning.py`; they do not accept current
panel completion or authorize H8 disposition. Preserve those artifacts, schemas,
validators and tests unchanged rather than retrofit new identities into them.

No current executable H8 acceptance route exists. The replacement packet needs
its own fail-closed validation before H8-D through H8-H can advance. General
policy, advisory reports, an old validator pass, or the broader frontier's
experimental acceptance status cannot substitute for that work. Until then,
these H8 gates remain pending and runtime, study, promotion and issue-closure
authority remain false. No additional human recruitment is required.
