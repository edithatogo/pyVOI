# Security and registry evidence packet — 2026-09-06

This packet is repository evidence for maintainer review. It does not submit a questionnaire, create an RRID, deposit to Zenodo, activate OSC, or claim acceptance. The maintainer is the sole human decision-maker; repository opinions are supplied by the role-separated agent panel. Destination curators and service operators remain external authorities.

## Security snapshot

Live GitHub API observations on 2026-09-06:

| Surface | Result | Disposition |
| --- | --- | --- |
| Dependabot | 2 open alerts, both high severity, for `nltk` model-artifact APIs bypassing path restrictions (alerts 74 and 75) | Existing bounded disposition is recorded in `conductor/tracks/remaining_backlog_delivery_20260831/nltk-residual-advisory-20260902.json`; no patched upstream release exists, so retain the pin and monitor for the first patched release |
| Dependabot | Earlier alerts 1–73 are fixed | Preserve the alert history; do not infer that the two open alerts are fixed |
| Code scanning | Open alerts include `py/import-and-import-from`, `py/empty-except`, `py/polluting-import`, `py/mixed-returns`, `py/ineffectual-statement` | Agent panel may triage and propose patches; each alert needs a current SARIF disposition and maintainer decision |
| Secret scanning | No alert records returned by the live API | This is an observation at packet time, not a perpetual guarantee |
| OpenSSF Scorecard | Existing issue #620 records 8.2/10 hosted evidence and 10/10 is not required under the sole-maintainer policy when it depends on other humans or organisations | Retain the actual score and actionable controls; no synthetic contributors, approvals, releases, or metric gaming |

The packet does not close #620 or #1045 while high-severity Dependabot alerts, open code-scanning findings, or maintainer questionnaire decisions remain unresolved.

## OpenSSF Best Practices questionnaire preparation

Project ID: [13835](https://www.bestpractices.dev/en/projects/13835). The following evidence pointers are ready for the maintainer's criterion-by-criterion inspection:

- project identity and homepage: `README.md`, `pyproject.toml`, `CITATION.cff`, and the public documentation site;
- licence: `LICENSE`, SPDX `Apache-2.0` metadata in `pyproject.toml`, `CITATION.cff`, and `codemeta.json`;
- source and contribution process: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue forms, and pull request template;
- vulnerability reporting: `SECURITY.md` and the CodeQL, gitleaks, dependency review, SBOM, and Scorecard workflows;
- quality and reproducibility: `tox.ini`, `tests/`, lockfiles, signed commits, release receipts, and `.github/workflows/`;
- release provenance: GitHub release `v2.2.0` assets include `voiage-2.2.0.intoto.jsonl`, `SHA256SUMS`, SBOM, manifest, wheel, and sdist;
- project governance: `AGENTS.md`, `conductor/single-maintainer-review-policy.md`, and `conductor/panel-gate-policy.json`.

The maintainer still needs to inspect the live questionnaire, mark each criterion as supported or not applicable, and submit or save the response in the authenticated account. An agent panel and this packet cannot provide personal attestations. The repository policy does not require recruiting additional humans; any criterion that intrinsically requires external contributors, reviewers, or an awarded badge remains an external constraint and must be recorded honestly.

## SciCrunch/RRID

`docs/release/scicrunch-rrid-registration.json` records a submitted 2026-07-27 suggestion for `voiage`, based on v2.0.0, with curation pending and no confirmation ID or RRID. No duplicate submission is warranted. Issue #298 remains open until a curator-issued `RRID:SCR_######` and resolving URL are observed and verified.

## Current-release archival metadata

`docs/release/zenodo-v2.2.0-metadata-draft.json` is a local, unpublished metadata draft for the signed GitHub release `v2.2.0`. It deliberately contains no DOI, deposition ID, access token, or publication claim. The release assets and `release-manifest.json` are the source evidence. The maintainer must choose whether a distinct archival deposition is needed, then perform any authenticated deposit and verify the DOI before adding it to citation metadata. Issue #1026 remains open until that authoritative receipt exists.

## OSC and issue disposition

OSC remains deferred because the current repository is personal and does not meet the documented organisation/shared-ownership eligibility boundary. No account, fiscal host, sponsorship link, or payment path is claimed. This packet supports issue #1026's documented deferral and does not create a new application.

## Maintainer inputs required

1. Let the agent panel triage open code-scanning alerts and apply routine safe fixes or concrete false-positive dispositions; retain the exact alert evidence.
2. Complete or save the OpenSSF questionnaire responses in the authenticated project account, recording unsupported or externally gated criteria accurately.
3. Decide whether Zenodo deposition adds a distinct archival purpose; if yes, perform the authenticated deposit and retain the DOI receipt.
4. Verify SciCrunch curation status later; do not resubmit without evidence that the existing suggestion was rejected or withdrawn.

## Live OpenSSF questionnaire readback

The live Project 13835 JSON endpoint was checked at packet time: `updated_at=2026-07-27T08:06:09.125Z`, `name=null`, `description=null`, and `license=null`. All ordinary criterion fields returned `?`; `achieve_passing_status` and `achieve_silver_status` returned `Unmet`; `OSPS-BR-01.02_status` returned `0`. This means the public project is not a Passing questionnaire record. The repository evidence pointers above are a preparation map, not answers submitted to the service.

The maintainer's next questionnaire pass should fill, at minimum, the public identity, licensing, documentation, contribution, vulnerability-reporting, build/test, CI, dependency, release, governance, and OpenSSF practice criteria from the named files. Criteria requiring independent contributors, two-person review, or external awards should be recorded as unsupported under the sole-maintainer policy rather than answered with synthetic evidence.

## Current code-scanning triage boundary

The live code-scanning API returned open findings across `py/empty-except`, `py/import-and-import-from`, `py/ineffectual-statement`, `py/mixed-returns`, `py/polluting-import`, `py/multiple-definition`, and `pythagorean` rules (the API is paginated; counts must be recomputed against a single captured response before closure). These are actionable repository findings, not badge evidence. The agent panel should group them by file and exact alert number, then remediate or document a narrow false-positive disposition with a maintainer decision. This packet intentionally does not close them based on a rule-name summary.

## Public RRID discovery check

Public web queries restricted to scicrunch.org and rrid.site for voiage on
6 September returned no results. This is negative search evidence only; it
does not establish rejection, absence from the registry or current private
curation status. Retain the existing request and do not submit a duplicate.
