# Worker guide

## Start here

Read the root AGENTS.md, this track's spec.md, plan.md, packets.json and the
selected packet's read_first files. Commands run from the repository root.
Use the existing project environment; do not install an arbitrary latest tool.
A missing file, command or fixture is a preflight finding, not permission to
invent an alternative. Report its exact path and resolve it before implementation.

Select one pending `.1` task whose prerequisites are satisfied. Record your
branch, worktree, current source revision and owner in the task handoff. Never
infer exclusive ownership from a directory name. Preserve existing dirty files.
Do not start another task because the first one is blocked.

## Turn a package into a safe implementation slice

The packet's candidate_write_scope is an investigation boundary, not a blanket
write permission. Before `.2`, name at most five exact implementation files and
one behavioral outcome. If the slice needs more files, split it into separately
reviewed substeps. Add the new checkboxes to plan.md and retain acceptance IDs.
Never use an entire source directory as the final write allowlist.

Record baseline SHA-256 values for the read/write inputs, selected test fixture,
expected red failure, expected green result, exact command arguments and tool
versions. Pin upstream prerequisite evidence. Distinguish test tooling failures
from the intended behavioral red failure. A zero-test collection is not success.

An integrator reviews shared schemas, public API, numerical assumptions,
lockfiles and workflow changes. A worker may implement a frozen decision, but
must not infer a scientific estimand, raise MSRV, change compatibility policy or
relax an acceptance threshold. G01's validator will check structural readiness;
its success will not replace this semantic review.

## Parallel schedule

G01 preflight comes first. G02, G03, G04, G05 and G06 can investigate independently
while G01 is prepared, but their implementation waits for G01 and an exact packet.
G07 implementation follows G03; G08 follows G02 and G04. Within each package,
`.1` precedes `.2` and `.2` precedes `.3`.

The integrator owns shared files: AGENTS.md, conductor/workflow.md, registry,
root roadmap/task list, public schemas, lockfiles and required workflow names.
G03 and G07 both touch consumer checks; G04 and G08 both touch automation. Their
exact file reservations must be disjoint or those edits run sequentially.
G05 and G06 kernel changes also serialize when they share a source file.

Use separate worktrees and caches; initially allow at most two implementation
workers and one integrator. Lower concurrency if memory or review capacity is
insufficient. No concurrent tox processes may write the same environment.
No automatic takeover, branch cleanup or shared-file rewrite is allowed.

## Validation and evidence

For runtime/dependency work follow AGENTS.md's frontier preflight in the isolated
checkout. Keep unrelated lock refreshes separate from the functional patch;
resolve an incompatible candidate before proceeding. Use the existing locked
native commands, for example `cargo test --manifest-path rust/Cargo.toml --locked`.
Run the selected packet's focused checks and applicable formatting/type checks.

Run `tox run-parallel -p 2` for the final candidate under AGENTS.md. Reuse eligible
unchanged evidence with its exact input binding. A failed check requires the
failed and affected checks again; runtime/dependency/shared-test changes require
the broader gate. Never substitute this packet for required hosted checks.

At every handoff record: task ID; acceptance ID; source SHA/tree; changed files;
command; environment/toolchain; exit status; test count; artifact digest; unresolved
risk; next allowed action. Keep secret values and patient data out of evidence.
Append evidence with the configured Conductor helper; never invent ledger hashes.
No completed checkbox without actual verification and the required commit record.

## Stop conditions

Stop dependent implementation if input hashes drift, scope expands, a prerequisite
is missing, the oracle is ambiguous, an API break is discovered, or two attempted
fixes leave the same failure unresolved. Preserve the diff and record a minimal
reproducer and exact next decision. Independent preflight may continue.

Never alter golden/reference bytes, drop failing tests, increase error tolerances,
turn errors into warnings, label a partial job complete, or promote an experimental
backend to force a passing result. New tests must be capable of rejecting a
plausible wrong implementation, not merely repeat its formula.

Rollback means reverting the owned change through the repository workflow.
Do not reset shared work, delete history, rewrite release artifacts, deploy,
publish or close an external gate. Track creation authorizes none of those actions.

## Structural packet check

Use the installed jsonschema Python API from the project environment:

```bash
python - <<'PYTHON'
import json
from pathlib import Path
from jsonschema import Draft202012Validator
root = Path("conductor/tracks/agent_safe_engineering_20260907")
schema = json.loads((root / "packet-schema.json").read_text())
Draft202012Validator.check_schema(schema)
Draft202012Validator(schema).validate(json.loads((root / "packets.json").read_text()))
PYTHON
```

This checks fields and types; it does not check dependency readiness, exact path
ownership or baseline hashes. Those checks remain explicit integrator duties
until G01 implements them.
G01 should reuse this schema and add semantic checks, not create another packet
format. Freeze the schema change together with its validator tests.

## Repository admission

Read [repository-boundaries.md](./repository-boundaries.md) before any scope
refinement. One slice has one delivery repository. Generic inference, game
solving, simulation, source acquisition and shared automation stay with their
owners. Future Rust-first providers may have distinct APIs/ABIs; validate the
chosen scientific and interchange contract. Existing Voiage compatibility
promises remain in force. Do not edit a sibling repository from this track.
