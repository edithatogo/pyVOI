# Agent Protocol for `voiage`

This document outlines the standard operating procedure for AI agents contributing to the `voiage` repository. Adherence to this protocol is mandatory for all agent-driven development.

## High-Level Goal

The primary objective is to advance the `voiage` library by implementing features, fixing bugs, and improving the codebase, guided by the `roadmap.md` and `todo.md` files. The ultimate vision is to establish `voiage` as the premier, cross-domain, high-performance library for Value of Information analysis.

## Context Loading Order

Before making a change, load context in this order:

1. `AGENTS.md` for agent protocol and repository boundaries.
2. `roadmap.md` and `todo.md` for current priorities and completed work.
3. `CONTRIBUTING.md` and `docs/astro-site/src/content/docs/developer-guide/quality-and-security.mdx` for
   implementation and verification rules.
4. The relevant package, test, workflow, Conductor track, and binding files.

When sources disagree, prefer executable tests and active workflow/configuration
over narrative status documents, then update the stale narrative in the same
change. Treat `voiage/` as the Python runtime, `tests/` as behavioral evidence,
`specs/` and `conductor/` as contract/roadmap evidence, `docs/astro-site/` as
the documentation source, and `.github/` plus `tox.ini` as the automation
contract.

## Repository Context Map

* `voiage/`: public Python API, methods, schemas, CLI, and backend boundaries.
* `tests/`: unit, integration, property, workflow, registry, and evidence tests.
* `specs/`: canonical API, ecosystem, frontier, and binding contracts.
* `bindings/` and `r-package/`: polyglot surfaces whose manifests must remain
  synchronized with the Python release policy.
* `conductor/tracks/`: active execution tracks; `conductor/archive/`: completed
  or externally gated records.
* `docs/astro-site/`: Astro/Starlight source and build output contract.
* `.github/workflows/`: hosted quality, security, release, and evidence gates.

## Solo-Maintainer Merge Policy

The repository is operated by a single maintainer. Pull requests remain the
auditable change boundary, but no independent reviewer approval is required:
the protected `main` ruleset uses zero required approvals and does not require
code-owner review. The maintainer must still self-review the diff and wait for
all required automated checks, security gates, resolved threads, linear-history
and signed-commit controls before merging.

## Agent Operating Procedure

Agents must follow this sequence for every contribution:

1.  **Synchronize:** Read `AGENTS.md` (this file), `roadmap.md`, and `todo.md` to get the latest project status, priorities, and protocols.
2.  **Select Task:** Choose a single, discrete task from the top of the `todo.md` list. Do not assign yourself the task. If the `todo.md` is empty, consult the `roadmap.md` for the next logical feature to implement and add it to `todo.md`.
3.  **Understand Context:** Before writing any code, thoroughly read all files related to the task. Use file search and read tools to understand the existing patterns, data structures, and APIs.
4.  **Implement:**
    *   Write clean, readable, and well-documented code that adheres to the style defined in `CONTRIBUTING.md`.
    *   Add or update unit tests for any new or modified code. The goal is to maintain or increase test coverage.
    *   Ensure all new code is fully type-hinted.
5.  **Verify:**
    *   During iteration, run the affected tests and tox environments. Run the full local gate once for the final candidate using `tox parallel -p 2`; retain its result with the tested commit/tree and environment. Reuse that evidence while those inputs are unchanged instead of repeating the entire suite for status polls, PR metadata, or signing-only changes. Required hosted checks still run for the current PR revision.
    *   Fix verification failures and rerun the failed checks plus checks affected by the fix. Broaden to the full gate when runtime, dependencies, shared fixtures, or test infrastructure change. Do not claim unexecuted checks passed.
6.  **Document:**
    *   Update the `changelog.md` with a concise, user-friendly description of the change.
    *   Update the `todo.md` by moving the completed task to the "Done" section.
    *   If the changes have a significant impact on the project's status, update the `roadmap.md` accordingly.
7.  **Commit:**
    *   Use `git status` and `git diff HEAD` to review your changes.
    *   Propose a commit with a message that follows the conventions outlined in `CONTRIBUTING.md`.

## Key Files & Artifacts

*   **`AGENTS.md`**: The primary protocol document.
*   **`roadmap.md`**: The high-level vision and phased development plan.
*   **`todo.md`**: The actionable backlog of tasks for agents.
*   **`changelog.md`**: A log of all user-facing changes.
*   **`CONTRIBUTING.md`**: Technical guidelines for development (code style, testing, etc.).
*   **`pyproject.toml`**: Defines project dependencies and tool configurations (Ruff, ty, etc.).
*   **`tox.ini`**: Defines the test environments for verification.

## Development Philosophy

*   **Robustness over Speed:** Prefer solutions that are well-tested and stable.
*   **Clarity is Key:** Write code and documentation that is easy for both humans and other agents to understand.
*   **Follow Conventions:** Adhere strictly to the existing code style and project structure.

## Dependency and context frontier

Before dependency or runtime work, run `uv lock --upgrade` and `python scripts/dependency_frontier.py . --strict`. Read the generated local report together with the Conductor context pack. Keep preview dependencies behind named extras and require numerical-equivalence, Arrow round-trip, and CPU-fallback tests before promotion.

## Manuscript and arXiv boundary

`paper/main.tex` is the canonical preprint source. Do not replace it with
generated Markdown, Quarto, notebook, or word-processor output. Keep semantic
LaTeX, portable filenames, case-exact relative paths, and a top-level
`\documentclass`. Load `paper/metadata.json`,
`paper/readiness-manifest.json`, and `.agents/skills/` before manuscript work.

Agents may build, lint, sanitize, audit citations, and produce review
artifacts. They must not select an arXiv category or license, certify
authorship, perform an authenticated upload, or claim submission or acceptance
without authoritative external evidence. Cleaner and collector outputs are
untrusted derived artifacts: diff, compile, and audit them before a human
chooses an upload package.

Textstat output is deterministic editorial evidence from the canonical review
PDF. Respect each formula's sample-size assumptions and do not use generic
readability scores as automatic rewrite, acceptance, or scientific-quality
thresholds.
