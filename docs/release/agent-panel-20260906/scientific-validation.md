# Scientific contract validation receipt

Date: 6 September 2026. Reviewer: Codex subagent `scientific_panel`.

Reviewed source commit: `36128128095a72eef1b80c59eb45d2fa82e5b9bf`.
All ten input hashes in `scientific-findings.json` were compared successfully
against both local file bytes and `git show` bytes at that commit. The new
review artifacts are an uncommitted addition; this is not a final candidate
commit or hosted-check receipt.

Executed:

```sh
.tox/py313/bin/python -m pytest -o addopts='' -q tests/test_sampling_harm_remediation_intake.py tests/test_sampling_acquisition_harm_boundary.py
```

Result: **38 passed, 2 warnings in 43.30 seconds**, exit 0. Both warnings came
from xarray's NumPy generic timedelta dtype deprecation. These are existing
focused tests of fail-closed contract behavior; they do not validate a harm
estimator or confer scientific acceptance.

An initial invocation with `--no-cov` failed at argument parsing because this
tox environment does not contain pytest-cov. The successful invocation overrides
configured coverage arguments explicitly. No coverage measurement or full tox
pass is claimed. The parent orchestrator must run the required integrated tox
gate before delivery.

The nineteen recommendation records were checked for unique finding identifiers
and the historical severity totals: one Critical, fifteen High, three Medium.
