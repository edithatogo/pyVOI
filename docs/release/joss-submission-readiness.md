# JOSS submission readiness

## Current boundary

Version 2.2.0 is public on PyPI, TestPyPI and GitHub. Its signed tag resolves
to `7af563c8cb373057d30662650b3f332f39e05b83`; the immutable publication receipt
is in the active v2.2 release-and-venue track. No JOSS, pyOpenSci or rOpenSci
submission is claimed. Repository checks do not establish venue acceptance.

The canonical preprint remains `paper/main.tex`; `paper.md` is the JOSS
adaptation. Both now distinguish the published version from historical
worked-example and archive records. The new manuscript requires fresh source
audits, PDF evidence and maintainer review; any JOSS editorial requirements remain external destination constraints. Older hosted PDFs remain historical,
not current-version approval.

The arXiv account was last observed on 26 July 2026: draft `7870358` was
incomplete and had an expiry of 9 August. That observation is not a live
account check or a permanent arXiv identifier. On 31 August the maintainer replaced the earlier arXiv-first sequence with
journal-first following reported case-specific advice. ArXiv is deferred until
journal submission and a later authorized action; no category or licence is chosen.

## Current evidence

| Requirement | Evidence and boundary |
| --- | --- |
| Open software and sustained development | Apache-2.0, public history since July 2025, issues, PRs, releases, tests, CI, documentation and contribution guidance |
| Research use | The historical same-author VOP record used release 2.0.0. A separate automated 2.2.0 replay reproduced its 500-row CSV and EVPI through two supported environments; this is not additional human use or independent adoption |
| Current software release | Signed v2.2.0, exact distribution digests, provenance, SBOM and clean installations are bound in the publication receipt |
| Permanent archive | The cited Software Heritage snapshot preserves v2.0.0, not v2.2.0. A new snapshot and DOI-bearing reviewed-version archive remain unconfirmed |
| Scientific and numerical evidence | Retained synthetic worked-example outputs match clean regeneration; reference tests do not establish empirical validation in every target domain |
| Non-author engagement | Issue #471 still has only author comments when checked on 30 August; automated accounts and AI-agent runs do not satisfy this evidence class |
| AI disclosure | Current assistance is disclosed and the maintainer confirmed review and understanding on 31 August; subsequent changes require review against the submitted packet |
| Funding and competing interests | No external funding and no competing interests were confirmed by the author on 24 July 2026; no new declaration is inferred |
| Paper and citation review | SourceRight and Authentext are structural/editorial checks; final claim/source checking and human approval remain required |
| Submission and editorial outcome | Not started; partner eligibility, screening, acceptance and DOI assignment remain external |

The research-use record and replay are in
`paper/joss-developer-research-use.json` and
`paper/research-use/v2.2.0/`. Exact current manuscript tool results and PDF
identities belong in `paper/joss-editorial-assurance.json` and
`paper/joss-readiness-manifest.json`.

## Reviewer installation surfaces

| Surface | Installation and scope |
| --- | --- |
| Python | A fresh `python -m pip install voiage==2.2.0` installs the primary review surface; verify outside the source checkout |
| R | Build `r-package/voiageR` as an R source archive. Native EVPI and ENBS compile the bundled dependency-free Rust kernel offline; no ambient shared voiage library is required. EVPPI and EVSI remain optional Python-backed paths |
| Julia | Build the main `voiage-ffi` library and supply it through `VOIAGE_FFI_LIBRARY`, then instantiate and test `bindings/julia`. Native EVPI and signed ENBS are supported; this is not a claim of completed JLL or General registration |
| Rust | The workspace and cross-language reference fixtures provide implementation evidence; registry publication and installation outcomes are recorded separately |

R and Julia expose scalar calculations, not the full Python decision-record
interface. R uses a separate bundled Rust implementation checked against shared
fixtures; the project does not claim one physical kernel is used by every binding.

## Selected submission route

The selected route is **pyOpenSci review first, followed by a JOSS partner
fast-track request** if pyOpenSci accepts the package and JOSS confirms scope.
The maintainer has authorized that route and autonomous repository delivery;
a separate maintainer instruction is not needed merely to reselect it.
The maintainer separately confirmed personal declarations on 31 August. This
does not permit AI-drafted JOSS conversations with editors and reviewers.

Finish all repository repairs and current maintainer review; any JOSS editorial requirements remain external destination constraints before any submission.
Earlier pyOpenSci requests #271 and #272 are now withdrawn, with no other
open author request observed. Survey completion and actual human-written
submission text remain pending; editorial screening is external. Preserve
the genuine engagement prerequisite. The decision and withdrawal receipts
are in the active v2.2 Conductor track; arXiv is no longer a pre-JOSS gate. After pyOpenSci acceptance, retain the review issue and accepted
revision before requesting eligible JOSS partner handling.

The standalone R package remains an eventual rOpenSci target. Reviews must not
run concurrently with pyOpenSci or JOSS unless the relevant editors expressly
permit that arrangement. Scope and monorepository suitability are questions for
the rOpenSci editor, not locally decidable acceptance criteria.

Current primary guidance:
[pyOpenSci policies](https://www.pyopensci.org/software-peer-review/our-process/policies.html),
[JOSS submission requirements](https://joss.readthedocs.io/en/latest/submitting.html),
[JOSS paper format](https://joss.readthedocs.io/en/latest/paper.html), and
[rOpenSci author guide](https://devguide.ropensci.org/softwarereview_author.html).

## Validation

Run `uv run python scripts/validate_joss.py` and the full tox gate.
The hosted JOSS workflow builds and retains an Open Journals PDF without
submitting it. Use `scripts/validate_joss.py --submission` only to inspect the
remaining submission gates; it must remain blocked while required human and
external evidence is missing.
