# Contributing to `voiage`

We welcome contributions from the community, whether from humans or AI agents. To ensure a smooth and effective development process, please adhere to the following guidelines.

## Getting Started

### Prerequisites

*   Python 3.12-3.14
*   [Rust](https://www.rust-lang.org/tools/install) 1.85 or later for source builds
*   [uv](https://docs.astral.sh/uv/) for locked environments and builds
*   [pre-commit](https://pre-commit.com/#installation) for automated checks

### Setting Up the Development Environment

1.  **Fork and Clone:**
    *   Fork the repository on GitHub.
    *   Clone your fork locally:
        ```bash
        git clone https://github.com/YOUR_USERNAME/voiage.git
        cd voiage
        ```

2.  **Install Dependencies:**
    ```bash
    uv sync --extra dev --extra ci
    ```

3.  **Install Pre-commit Hooks:**
    *   This will install the hooks defined in `.pre-commit-config.yaml`, which automatically run checks before each commit.
        ```bash
        pre-commit install
        ```

## Development Workflow

This is currently a solo-maintainer repository. Pull requests are retained for
traceability and automated quality gates, but an additional human approval is
not required. The maintainer is the sole human decision-maker and self-reviews after considering the agent-panel opinions every diff and merge only after
the required CI, security, coverage, documentation, and contract checks pass.

1.  **Create a Branch:**
    *   Create a new branch for your feature or bugfix:
        ```bash
        git checkout -b feature/my-new-feature
        ```

2.  **Write Code:**
    *   Make your changes, following the code style guidelines below.
    *   Ensure new code is well-tested and fully type-hinted.

3.  **Verify Changes:**
    *   Run the full suite of tests, linting, and type checks using `tox`. This is the same check that runs in our CI pipeline.
        ```bash
        tox
        ```
    *   Fix any errors reported by `tox` before proceeding.
    *   Run the repository-owned security and workflow harness directly when
        changing CI or release automation:
        ```bash
        uv run python scripts/repo_harness.py
        ```
    *   Frontier contract changes should also pass the dedicated registry check:
        ```bash
        tox -e frontier-contract
        ```
    *   `tox is the required local CI authority`, together with the repository
        harness. `nox is an optional developer interface` that mirrors
        selected core sessions but is not a second required gate:
        ```bash
        uv run nox
        ```

4.  **Commit Changes:**
    *   Stage your changes (`git add .`).
    *   Commit them with a descriptive message. The pre-commit hooks will run automatically.
        ```bash
        git commit -m "feat: Add my new feature"
        ```

5.  **Push and Open a Pull Request:**
    *   Push your branch to your fork and open a pull request against the `main` branch of the original repository.

For a more detailed walkthrough of the Conductor workflow, docs structure, and
testing expectations, see the [How to contribute guide](https://edithatogo.github.io/voiage/developer-guide/how-to-contribute/).
For the repository security model and hosted GitHub gates, see
the [quality and security guidance](https://edithatogo.github.io/voiage/developer-guide/quality-and-security/).

For help requests, support questions, and security reporting, see
[`SUPPORT.md`](SUPPORT.md), [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md), and
[`SECURITY.md`](SECURITY.md).

## Code Style and Conventions

### Formatting and Linting

*   We use **Ruff** for formatting, linting, and security-rule checks to ensure a consistent code style.
*   The configuration is defined in `pyproject.toml`.
*   The pre-commit hooks will automatically format your code. You can also run it manually:
    ```bash
    ruff format .
    ruff check --fix .
    ```
*   We use **Vale** to lint prose in Markdown and reStructuredText docs. Run it
    from the repository root with:
    ```bash
    uv run bash scripts/vale_prose.sh
    ```

### Type Hinting

*   All new functions and methods must include type hints.
*   We use **ty** for static type analysis. The pre-commit hook will run `ty check` on your changes.

### Testing

*   We use **pytest** for testing.
*   All new features must be accompanied by tests.
*   All bug fixes should include a regression test.
*   Run tests using `tox` or directly with `pytest`:
    ```bash
    pytest
    ```

### R Package Documentation

*   The R package keeps its narrative docs deterministic and non-interactive.
*   From `r-package/voiageR`, build the PDF manual with:
    ```bash
    Rscript tools/build-manual.R . build/voiageR-manual.pdf
    ```
*   The vignette is source-controlled under `r-package/voiageR/vignettes/`
    and should remain runnable without interactive prompts or live notebook
    state.
*   Before release, verify the package metadata and reference docs with:
    ```bash
    R CMD build .
    R CMD check --as-cran --no-manual voiageR_<version>.tar.gz
    ```
    Replace `<version>` with the tarball version produced by your local build.

### Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. This helps in automating changelog generation and makes the commit history more readable.

Each commit message should be in the format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

*   **Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `build`, `ci`.
*   **Example:**
    ```
    feat(analysis): Add EVSI regression method
    ```
    ```
    fix: Correct population scaling in EVPI calculation
    ```

## Documentation

*   Public functions and classes should have docstrings following the **NumPy docstring convention**.
*   The project's documentation site is in `docs/astro-site/` and is built with Astro and Starlight.
*   The R package documentation track ships a narrative vignette at
    `r-package/voiageR/vignettes/voiageR-getting-started.Rmd` and a
    deterministic PDF manual helper at `r-package/voiageR/tools/build-manual.R`.
    From the package root, you can verify both with:
    ```bash
    Rscript tools/build-manual.R . "$RUNNER_TEMP/voiageR-manual.pdf"
    Rscript -e 'rmarkdown::render("vignettes/voiageR-getting-started.Rmd", output_format = "html_vignette", quiet = TRUE)'
    ```
### Prose linting

Documentation prose is checked with [Vale](https://vale.sh/) using the repository
rules in `.vale/`. Install Vale locally, then run `uv run task vale` (or
`tox -e vale`) before submitting documentation changes. GitHub Actions runs the
same wrapper in the `Vale Prose Lint` job.
