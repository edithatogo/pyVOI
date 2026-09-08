# Implementation handoff: Version identities and compatibility policy

Completed in PR #1117; current eligibility: **closed**.

1. Read spec.md, plan.md, implementation-packet.json and the shared orchestration.
2. Use a clean, isolated worktree from the accepted planning commit. Compare the
   packet input hashes with its current files; changed inputs require review.
3. Confirm prerequisite tracks have source-bound acceptance evidence. Reading a
   packet or a green schema check does not satisfy a prerequisite.
4. Run existing baseline checks: `python -m pytest tests/test_version_sync.py -q`.
5. Start T1.1. Reserved paths include proposed new files; do not claim they exist.
   Author the specified acceptance tests before implementing behavior.
6. Use `python -m pytest tests/test_version_identity_contracts.py tests/test_version_sync.py -q` for focused verification. Run native checks for Rust changes and
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
