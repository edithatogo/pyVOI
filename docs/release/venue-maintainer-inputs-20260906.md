# Venue execution handoff — 6 September 2026

Related issues: #1037, #471, #312 and #296. This is internal agent-authored
preparation, not author-written review communication or a submission receipt.

## Decisions already recorded

Retain voiage 2.2.0, pyOpenSci first, the eligible JOSS partner route next,
and arXiv after journal submission. The personal declarations and withdrawal
of the earlier pyOpenSci requests remain recorded in the active release track.
Do not request these decisions again. Repository assessments use agents and
the sole maintainer; destination editorial outcomes remain external facts.

## Actual survey requirements

Read-only inspection of the public [pre-review survey](https://forms.gle/F9mou7S3jhe8DMJ16)
on 6 September identified an eight-page form. No answers were entered or sent.
Its first page requires an email address. The embedded form definition marks
first and last names, package name, repository URL and maintainer names as
required on their applicable pages. The maintainer section introduction calls
its questions optional, but three package fields have required flags; follow
the actual field validation rather than that introductory sentence.

Repository facts ready for entry:

| Field | Established value |
| --- | --- |
| Contribution role | Package maintainer |
| Package | voiage |
| Repository | https://github.com/edithatogo/voiage |
| Maintainer list | Sole maintainer; the form permits “just me” |
| GitHub username | edithatogo |
| Documentation tooling | Astro/Starlight |

The maintainer should enter the preferred contact email and name directly in
the private form. Professional background, support preferences, AI experience
and demographic questions are optional in the observed definition. Do not
infer demographic answers or commit private responses to Git. Google sign-in
is offered for saving progress but the form states it is not required.

## Submission text

Use `docs/release/pyopensci-submission-draft.md` only as a factual reference.
The remaining writing is the maintainer's own account of the package purpose,
research use, key design choices, relation to existing tools and AI assistance.
Do not convert an approval of the staging draft into a claim of human authorship.
The [current pyOpenSci policy](https://www.pyopensci.org/software-peer-review/our-process/policies.html)
was rechecked on 6 September: it calls for meaningful human oversight and
prefers human-written review communication, allowing translation and grammar
assistance. This handoff does not post generated communication to the venue.

## Research evidence ready for review

`research-use-decimal-review-20260906.json` independently recomputes the retained
500-row CSV using standard-library Decimal arithmetic at 50-digit precision.
Vaccination has the larger net benefit in all 500 supplied draws; therefore
the scenario's EVPI is exactly zero under this calculation. This corroborates
the retained numerical result without rerunning an unchanged installation or
claiming new human use. The smallest sampled incremental net benefit is
344,525,082.1243995 NZD per model cohort. This is a scenario property, not a
clinical recommendation, real-world effectiveness estimate or general claim
that further research has no value.

The original wheel-verification receipt and separate-environment limitations
remain in `paper/research-use/v2.2.0/README.md`. An agent arithmetic review cannot
establish non-author human adoption or guarantee JOSS eligibility.

## Deferred actions

Once the private survey and author-written body exist, retain an actual
pyOpenSci submission receipt. Pursue the selected JOSS route only with its
eligibility evidence. Do not reopen the historical arXiv upload now or select
a category or licence on the author's behalf. Bring those choices with the
final journal-first package. rOpenSci remains sequenced to avoid concurrent
review. No venue acceptance, DOI or arXiv announcement is established here.
