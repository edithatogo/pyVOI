# Track: Remaining Backlog Delivery

- [Specification](./spec.md)
- [Implementation Plan](./plan.md)
- [Metadata](./metadata.json)
- [Evidence](./evidence.jsonl)
- [Baseline and recovery receipt](./baseline-and-recovery-20260831.json)
- [Remaining issue register](./remaining-issue-register-20260831.md)
- [Issue reconciliation receipt](./issue-reconciliation-20260831.json)
- [Interruption recovery receipt](./interruption-recovery-20260831.json)
- [Torch advisory triage](./torch-advisory-triage-20260831.json)
- [Local validation continuation](./local-validation-20260831.json)
- [Post-repair independent review](./post-repair-review-20260831.json)
- [Preparation review](./preparation-review-20260831.md)
- [Observed Codecov delivery](./codecov-observation-20260831.json)
- [Full R check with manuals](./r-manual-check-20260901.json)
- [Current R check receipt](./r-strict-check-20260831.json)
- [GitHub issue #1053](https://github.com/edithatogo/voiage/issues/1053)
- [Related roadmap #296](https://github.com/edithatogo/voiage/issues/296)

Status: in progress. Technical repairs are proceeding in isolated worktrees.
The verified recovery archive permits retirement of obsolete branch refs.
No scientific, venue, registry or human-action outcome is inferred from local
validation or protected PR delivery.

- [Delivery checkpoint (2026-09-01)](./delivery-checkpoint-20260901.md)
- [Delivery and cleanup observations (2026-09-01)](./delivery-checkpoint-20260901.json)
- [Pending pre-closeout receipt (2026-09-03)](./pre-closeout-20260903.json)

The pre-closeout receipt binds merged PRs #1087 and #1088, closed repository issues
#1024, #614, and #615, and the post-merge inventory. It remains fail-closed on
an exact native Spack receipt placeholder. Issue #1025 and all remaining human,
scientific, registry, identifier, and venue outcomes stay pending. The sole
unique cleanup branch was retired only after its exact commit and tree were
preserved under a nonbranch recovery ref and a checksum-bound complete-history
bundle. A separately checksum-bound restore record confirms that a mirror clone
resolved the exact commit and tree and passed full strict object verification.
It cannot prove its own post-merge inventory: a separate, auditable
post-closeout receipt is required after this change merges and its delivery
branch and worktree are pruned, before issue #1053 may close.
The durable ref manifest excludes rotating `refs/codex/turn-diffs/*` app state,
labels that namespace transient, and separately binds every ordered stash
reflog entry by object ID, selector, and subject.

- [Prepared continuation handoff](./implementation-handoff.md)
