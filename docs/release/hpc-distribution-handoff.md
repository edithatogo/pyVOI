# HPC distribution handoff for voiage 2.2.0

Status: local recipe candidates; no upstream submission or HPC installation.

The recipes use the published PyPI source distribution, not a GitHub-generated
archive. Its SHA-256 is
`e4edfd41011891a94cbc2b144ff1d20340fcc32481e7a2b24157494b7490a16b`.
The source contains the release identity used by the Rust build backend. Rust
1.85 or newer and Maturin 1.9 through 1.x are build requirements. Optional JAX
and other accelerators are not enabled by these CPU recipes.

## Spack packet

Candidate: `packaging/spack/package.py`, package name `py-voiage`.

Proposed title: `py-voiage: add version 2.2.0`.

Proposed body:

> Add the Apache-2.0 voiage Python package with its required Rust extension.
> Build from the checksum-pinned upstream source distribution. Declare the
> Python 3.12–3.14 range, build dependencies, and all twelve runtime dependency
> constraints, including JSON Schema. Use the tested modern Typer/Click pair
> rather than permitting an old Typer with new Click. Check both the Python and
> native imports.

Issue #1025 named `spack/spack`. Current Spack lists its built-in package
repository as [spack/spack-packages](https://github.com/spack/spack-packages);
confirm its contribution layout and supported package API with maintainers
before opening the recipe PR. Do not submit this packet automatically.

Run `bash scripts/validate_hpc_recipes.sh --spec` to resolve the recipe against
an installed Spack catalogue. Missing package versions are upstream catalogue
work, not permission to lower voiage's dependency requirements. A concrete
spec is not a successful build. Run the explicit `--build` mode only on a
prepared build host, with retained logs and approval for its resource use.
Cargo dependencies are downloaded according to the shipped Cargo.lock unless
the site prepares a Cargo vendor cache. No offline build is claimed.

## EasyBuild packet

Candidates:

- `packaging/easybuild/voiage-2.2.0-foss-2023a.eb`
- `packaging/easybuild/voiage-2.2.0-foss-2024a.eb`

Proposed title: `voiage 2.2.0: foss 2023a and 2024a candidates`.

Proposed body:

> Add checksum-pinned voiage source builds with Python and native-extension
> sanity checks. Disable pip dependency downloads and require a consistent
> site-provided dependency stack. Both requested foss toolchain variants are
> included; each needs matching dependency easyconfigs before acceptance.

Target: [easybuilders/easybuild-easyconfigs](https://github.com/easybuilders/easybuild-easyconfigs).
No upstream PR has been opened.

These are **backport candidates**, not a claim that the upstream robot search
path already contains their dependency graph. Python 3.12 and modern NumPy,
SciPy, Arrow, Polars, Pydantic and JSON Schema must be provided consistently
for each compiler toolchain. The older recipe's scikit-learn 1.5, Arrow 16 and
Pydantic 2.7 did not meet the source requirements. The new recipes name versions
that satisfy those requirements, and intentionally fail rather than download
an uncontrolled replacement stack with pip. Site or upstream dependency
recipes and actual Linux builds remain required. Do not mix compiled modules
from different foss generations to bypass this requirement.

## Evidence and remaining work

The portable [validation receipt](hpc-validation-20260831.json) records source,
wheel and recipe hashes, the tested runtime versions, and the failed pinned
solver audit. Its explicit host scope excludes HPC builds and module loading.

`bash scripts/validate_hpc_recipes.sh --syntax` parses the three current recipe
files. The `--spec` mode additionally runs Spack concretization, EasyBuild style
checks and robot dry runs; it fails if required tools or dependency recipes
are unavailable. The validator supplies all checked-in generation overlays to
EasyBuild. Set `HPC_EASYBUILD_CATALOGUE_PATH` when the host catalogue is not at
EasyBuild's standard location. The `--build` mode additionally performs the
package builds.
None of these steps is silently treated as another step.

`python scripts/hpc_package_smoke.py --output /absolute/path/smoke.json` downloads
and verifies the pinned source, builds its Rust wheel, installs it into a fresh
Python 3.12 environment outside the checkout with the twelve exact runtime
versions in the EasyBuild candidates, runs dependency consistency and
CLI checks, checks native runtime provenance, evaluates a known EVPI example,
and round-trips an Arrow table. It records failures as failures. This is local
source-wheel evidence on the recorded host. It does not build the dependency
modules with foss, and is not Spack, EasyBuild, scheduler,
MPI, accelerator or cluster module-load evidence.

Before upstream review, retain successful concrete dependency graphs, real
Spack and both EasyBuild build logs, their installed smoke results and a real
module-load transcript. Then a maintainer may choose the reviewed upstream
packets. Upstream merge and package index visibility remain later outcomes.

### Historical catalogue-only audit on 31 August 2026

Spack 1.2.2 loaded the recipe, fetched its built-in catalogue and attempted
concretization, which failed. Its available typing-extensions 4.15.0,
Pydantic 2.12.5, PyArrow 19.0.1, Polars 1.29.0 and Click 8.1.8 did not satisfy
the release's minimum versions. The catalogue also lacks the tested Typer
0.27.2 and Click 8.5.0 combination selected by these recipes, and its older
Typer dependency constraints cap Click at 8.1.8. This is a concrete dependency
catalogue blocker in the standalone recipe path. The local overlay follow-up
below addresses those versions without lowering release constraints.

EasyBuild 4.9.4 parsed both candidate files successfully. That parser result
does not establish robot resolution, a foss build, or module loading. This
host has no initialized Environment Modules or Lmod command, and the matching
backport dependency stacks have not been installed.

For a repeatable solver audit, set `HPC_SPACK_CATALOG_COMMIT` to the reviewed
catalogue commit and `HPC_VALIDATION_WORK_DIR` to a new directory. The validator
refuses to overwrite an evidence directory and retains the catalogue there.
The repeated audit pins `d4f7c711a6a42f1c4d551c8fd10fce9a11340a81` from the
`releases/v2026.06` catalogue.

The audit identified a local overlay as the next step, requiring more than five
version declarations. Pydantic 2.13.4 requires pydantic-core 2.46.4, and Polars
1.42.1 requires the separate polars-runtime-32 package at the same version.
Arrow needs matching C++ and Python builds, and modern Typer needs its current
transitive dependencies. Each source digest, build backend, Rust/compiler
requirement and version constraint needed checking before concretization and
native build tests. The following overlay provides the source and solver
evidence; upstream packets remain unsubmitted pending the remaining work.

### Local overlay follow-up

The repository now supplies `packaging/spack-overlay/` against that pinned
catalogue. It adds the missing Python versions, the split Polars runtime,
matched Arrow 25 C++ source, and audited build dependencies. PyArrow requests
the CSV, dataset, filesystem and Parquet features used by voiage's ingestion
and interchange modules. The retained catalogue-only failure above remains
historical evidence; it is not the current overlay result.

The overlay's `solver-receipt.json` and complete `solver-logs/` record three
successful individual graphs: Typer, Pydantic and PyArrow. The dated compiler follow-up now resolves the complete voiage graph on
macOS arm64 with distinct stable Rust 1.96.0 and exact `nightly-2026-04-01`
nodes. Its beta stage0 and source archive are checksum-bound; only Rust,
rust-bootstrap, Maturin and setuptools-rust permit two build-tool instances. The Python 3.13 LibCST path also
needs a separate pyyaml-ft recipe. None of these graph results proves a build.

Use the isolated configuration, cache and bootstrap commands in the
[overlay guide](../../packaging/spack-overlay/README.md) to reproduce that
audit. The `validate_hpc_recipes.sh --spec` command now loads the overlay before the
root recipe; its output should therefore be interpreted with the versioned
provider recipes and pinned catalogue together. Actual
Linux builds, Arrow round trips from the installed Spack package, and module
loading remain required before submission or completion of issue #1025.
