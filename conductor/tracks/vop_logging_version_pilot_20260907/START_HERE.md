# Implementation handoff: VOP-to-VOI version and logging pilot

Implementation and all phase acceptance exist in merged PRs #1120, #1153, #1154, #1155, #1156, and #1157; current eligibility: **repository-owned acceptance complete; external release/publication gates excluded**.

1. Read spec.md, plan.md, implementation-packet.json and the shared orchestration.
2. Use a clean, isolated worktree from the accepted planning commit. Compare the
   packet input hashes with its current files; changed inputs require review.
3. Confirm the logging/privacy prerequisite has source-bound acceptance evidence.
   The prerequisite is accepted in PR #1152 at merge commit
   `25dfcdf4f42f86301bf3ab07e659f4641a8bbb93`.
4. Run existing baseline checks: `python -m pytest tests/test_consumer_matrix.py tests/test_vop_research_handoff.py -q`.
5. Review the merged implementation against each AC before any further change.
   Do not duplicate the implementation or claim final completion from the merged
   PR alone; final local/native and track evidence remain required.
6. Historical focused and final local/native results are recorded in evidence.jsonl against their exact source trees. Re-run gates only for a new runtime candidate; this closeout changes Conductor state only.

Each phase in implementation-packet.json states the behavior, observable result,
exact test command and ordered task IDs. Shared dependency/workflow files are
integrator-only. No package upgrade is implicit; follow isolated dependency
frontier preflight before runtime/dependency work. Dependencies remain unchosen
until their existing qualification task supplies a compatible pinned graph.

The first task is bounded contract/design work. It must produce the exact
negative-test witness before code. No scientific assumptions or ABI policy may
be invented by the worker. Preserve runtime-neutral interchange and independent
provider APIs as specified in repository-boundaries.md.
