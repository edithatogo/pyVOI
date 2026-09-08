# Implementation handoff: VOP-to-VOI version and logging pilot

Implementation exists in merged PR #1120 at commit `348db4d3e51a82b6fc6a252ef4bdabdf99db8564`; current eligibility: **acceptance review pending**.

1. Read spec.md, plan.md, implementation-packet.json and the shared orchestration.
2. Use a clean, isolated worktree from the accepted planning commit. Compare the
   packet input hashes with its current files; changed inputs require review.
3. Confirm prerequisite tracks have source-bound acceptance evidence. The
   logging/privacy prerequisite is evidenced by merged PR #1119 at
   `3e33feafd68d718142b083de12d697e2ec5f42e5`; a packet or green schema check
   alone does not satisfy a prerequisite.
4. Run existing baseline checks: `python -m pytest tests/test_consumer_matrix.py tests/test_vop_research_handoff.py -q`.
5. Review the merged implementation against each AC before any further change.
   Do not duplicate the implementation or claim final completion from the merged
   PR alone; final local/native and track evidence remain required.
6. Use `python -m pytest tests/test_vop_logging_version_pilot.py tests/test_consumer_matrix.py tests/test_vop_research_handoff.py -q` for focused verification. Run native checks for Rust changes and
   the final local gate required by AGENTS.md. Record actual commands/results.

Each phase in implementation-packet.json states the behavior, observable result,
exact test command and ordered task IDs. Shared dependency/workflow files are
integrator-only. No package upgrade is implicit; follow isolated dependency
frontier preflight before runtime/dependency work. Dependencies remain unchosen
until their existing qualification task supplies a compatible pinned graph.

The first task is bounded contract/design work. It must produce the exact
negative-test witness before code. No scientific assumptions or ABI policy may
be invented by the worker. Preserve runtime-neutral interchange and independent
provider APIs as specified in repository-boundaries.md.
